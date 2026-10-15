import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import theme_release as mirrors
import theme_publication as themes
from bot import digest, Rejected, require


class Api:
    def __init__(self):
        self.release = None; self.content = {}; self.downloads = []; self.verified = []; self.published = False
    def json(self, path, method='GET', data=None):
        if '/releases/tags/' in path:
            if self.release is None: raise Rejected('OriginHttp404')
        elif method == 'POST':
            self.release = dict(data, id=3, assets=[])
        elif method == 'PATCH':
            self.release.update(data); self.published = True
        return copy.deepcopy(self.release)
    def upload(self, command, **kwargs):
        assert '--clobber' not in command
        path = Path(command[4]); raw = path.read_bytes()
        self.content[path.name] = raw
        self.release['assets'].append(dict(id=len(self.content)+10, name=path.name, size=len(raw), state='uploaded', digest='sha256:'+digest(raw)))
        class Result: returncode=0
        return Result()
    def download(self, artifact, target):
        raw=self.content[artifact['assetName']]
        require(len(raw)==artifact['sizeBytes'] and digest(raw)==artifact['sha256'], 'PayloadDigestMismatch')
        target.write_bytes(raw); self.downloads.append(artifact)
    def verify_origin(self, artifact): self.verified.append(artifact)


class MirrorTests(unittest.TestCase):
    def test_mirrors_verified_before_publication_and_retry_without_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=b'catalog'; data=b'actual reviewed ZIP'; name='theme-'+digest(data)+'.zip'
            path=Path(tmp)/name; path.write_bytes(data); api=Api()
            with patch.object(mirrors.subprocess,'run',side_effect=api.upload) as upload:
                artifact=mirrors.release_assets(api,'a'*40,raw,{name:path})
                self.assertEqual(upload.call_count,2)
                self.assertEqual(set(api.content),{'catalog.json',name})
                self.assertEqual({a['sha256'] for a in api.downloads},{digest(raw),digest(data)})
                self.assertEqual(artifact['assetName'],'catalog.json'); self.assertFalse(api.release['draft'])
                upload.reset_mock(); mirrors.release_assets(api,'a'*40,raw,{name:path}); upload.assert_not_called()
                # A final release may never be repaired in place when a mirror is missing.
                api.release['assets']=[a for a in api.release['assets'] if a['name']=='catalog.json']
                with self.assertRaisesRegex(Rejected,'PublicationAssetMissing'):
                    mirrors.release_assets(api,'a'*40,raw,{name:path})
                upload.assert_not_called()
    def test_content_address_prevents_upload_of_substituted_local_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/('theme-'+digest(b'approved')+'.zip');path.write_bytes(b'changed')
            with self.assertRaisesRegex(Rejected,'ThemeMirrorDigestMismatch'):
                mirrors.release_assets(Api(),'a'*40,b'catalog',{path.name:path})
    def test_preexisting_release_asset_body_reverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw=b'catalog'; data=b'approved';name='theme-'+digest(data)+'.zip';path=Path(tmp)/name;path.write_bytes(data);api=Api()
            with patch.object(mirrors.subprocess,'run',side_effect=api.upload):
                mirrors.release_assets(api,'a'*40,raw,{name:path})
                api.content[name]=b'replaced'
                with self.assertRaisesRegex(Rejected,'PayloadDigestMismatch'):
                    mirrors.release_assets(api,'a'*40,raw,{name:path})
    def test_approved_third_party_origins_are_retained_and_identical_payloads_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=b'reviewed ZIP';sha=digest(raw)
            rows=[dict(id='third.theme.'+str(i),state='active',manifest=dict(version='1.0.0'),artifact=dict(repository='independent-'+str(i)+'/theme',ownerId=str(700+i),sha256=sha)) for i in range(2)]
            class Origin:
                def __init__(self): self.seen=[]
                def verify_origin(self,artifact,data_only=False): self.seen.append((artifact,data_only))
                def download(self,artifact,path): path.write_bytes(raw)
            api=Origin()
            with patch.object(themes,'validate') as validate:
                payloads=themes.revalidate(api,themes.encode(dict(packages=rows)),'validator',root)
            self.assertEqual(len(payloads),1);self.assertEqual(validate.call_count,2)
            self.assertEqual([a['repository'] for a,_ in api.seen],[r['artifact']['repository'] for r in rows]);self.assertTrue(all(data_only for _,data_only in api.seen))
            self.assertEqual(next(iter(payloads.values())).read_bytes(),raw)
            self.assertEqual(rows[0]['artifact']['ownerId'],'700')

if __name__=='__main__':unittest.main()
