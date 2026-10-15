import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import theme_publication as themes
VALIDATOR = ROOT/'Validator/bin/Release/net10.0/Validator.dll'
FIXTURE = json.loads((ROOT/'tests/fixtures/theme-submission.json').read_text())


class ThemePublicationTests(unittest.TestCase):
    def draft(self, record, extra=None):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); folder=root/'themes/packages'; folder.mkdir(parents=True)
            (folder/'sample.json').write_text(json.dumps(record))
            if extra: (folder/'second.json').write_text(json.dumps(extra))
            return json.loads(themes.build(root,'a'*40,VALIDATOR))

    def test_separate_feed_uses_real_theme_reader(self):
        value=self.draft(FIXTURE)
        self.assertEqual((value['schemaVersion'],value['sourceId']),(4,'phinix.themes'))
        self.assertEqual(value['packages'][0]['manifest']['management'],'phinix-theme')

    def test_empty_feed_has_its_own_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=json.loads(themes.build(Path(tmp),'a'*40,VALIDATOR))
        self.assertEqual(value['packages'],[])

    def test_duplicate_and_bad_manifests_are_rejected(self):
        with self.assertRaises(ValueError): self.draft(FIXTURE,FIXTURE)
        for change in [lambda p:p.update(management='phinix-dll'),lambda p:p['artifact'].update(payloadKind='managed-dll-zip'),
                       lambda p:p['manifest'].update(assemblies=[]),lambda p:p['manifest']['themes'][0].update(path='Themes/../bad.xml'),
                       lambda p:p['manifest']['themes'][0].update(path='Themes/CON.xml'),lambda p:p.update(id='other.theme'),
                       lambda p:p['artifact'].update(sizeBytes=8*1024*1024+1),lambda p:p['artifact'].update(tag='v9.0.0')]:
            candidate=copy.deepcopy(FIXTURE); change(candidate['package'])
            with self.subTest(candidate=candidate),self.assertRaises(ValueError): self.draft(candidate)

    def test_continuity_preserves_versions_and_allows_only_state_changes(self):
        old={'packages':[FIXTURE['package']]}; new=copy.deepcopy(old)
        new['packages'][0]['state']='withdrawn'; themes.continuity(old,new)
        new['packages'][0]['summary']='changed'
        with self.assertRaisesRegex(themes.Rejected,'ThemePublishedVersionChanged'): themes.continuity(old,new)
        with self.assertRaisesRegex(themes.Rejected,'ThemePublishedVersionRemoved'): themes.continuity(old,{'packages':[]})

    def test_cannot_publish_from_push_pr_or_other_branch(self):
        class Api:
            def json(self,*args): raise AssertionError('must reject before remote access')
        for event,ref in [('push','refs/heads/main'),('pull_request','refs/heads/main'),('workflow_dispatch','refs/heads/themes')]:
            with patch.dict(os.environ,dict(GITHUB_REPOSITORY=themes.INDEX,GITHUB_EVENT_NAME=event,GITHUB_REF=ref,GITHUB_RUN_ATTEMPT='1')):
                with self.assertRaisesRegex(themes.Rejected,'ThemePublicationContextRejected'): themes.publish(None,Api())

    def test_pointer_envelope_is_independent(self):
        raw=themes.encode({'schemaVersion':4,'sourceId':themes.SOURCE,'snapshotId':'a'*40,'packages':[]})
        artifact=dict(repository=themes.INDEX,repositoryId='1',ownerId='2',releaseId='3',assetId='4',assetName='catalog.json')
        published,stable=themes.envelopes('a'*40,raw,artifact);p=json.loads(published);s=json.loads(stable)
        self.assertEqual(s['catalogSchemaVersion'],4);self.assertEqual(s['publishedSha256'],themes.digest(published))
        self.assertEqual(p['sourceId'],'phinix.themes')

if __name__=='__main__':unittest.main()
