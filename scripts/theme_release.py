"""Publish byte-identical, content-addressed theme mirrors with their catalog."""
from pathlib import Path
import re
import subprocess
import tempfile
from bot import INDEX, Rejected, require, digest
from admission import PREFIX, REPOSITORY_ID, OWNER_ID


def release_assets(api, snapshot, raw, payloads):
    tag = 'theme-catalog-v4-' + snapshot
    require(re.fullmatch(r'[0-9a-f]{40}', snapshot) is not None, 'InvalidSnapshot')
    require(len(payloads) <= 256, 'CollectionLimit')
    documents = {'catalog.json': (len(raw), digest(raw), None)}
    for name, path in payloads.items():
        require(re.fullmatch(r'theme-[0-9a-f]{64}\.zip', name) is not None, 'ThemeMirrorNameRejected')
        require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= 8 * 1024 * 1024, 'ThemeMirrorPayloadRejected')
        content_hash = digest(path.read_bytes())
        require(name == 'theme-' + content_hash + '.zip', 'ThemeMirrorDigestMismatch')
        documents[name] = (path.stat().st_size, content_hash, path)
    try:
        release = api.json(PREFIX + '/releases/tags/' + tag)
    except Rejected as ex:
        if str(ex) != 'OriginHttp404': raise
        release = api.json(PREFIX + '/releases', 'POST', dict(tag_name=tag, target_commitish=snapshot,
            name=tag, draft=True, prerelease=False,
            body='Reviewed theme catalog and byte-identical public theme mirrors. Input: ' + snapshot + '. Catalog SHA256: ' + digest(raw)))
    require(release.get('tag_name') == tag and release.get('prerelease') is False and
            (not release.get('draft') or release.get('target_commitish') == snapshot), 'PublicationReleaseConflict')

    def assets_of(value):
        assets = value.get('assets', [])
        require(type(assets) is list and len(assets) <= len(documents), 'PublicationAssetConflict')
        result = {}
        for asset in assets:
            name = asset.get('name')
            require(name in documents and name not in result, 'PublicationAssetConflict')
            length, sha, _ = documents[name]
            require(asset.get('state') == 'uploaded' and type(asset.get('size')) is int and asset['size'] == length and
                    asset.get('digest') in (None, 'sha256:' + sha), 'PublicationAssetConflict')
            result[name] = asset
        return result

    assets = assets_of(release)
    with tempfile.TemporaryDirectory() as temporary:
        catalog = Path(temporary) / 'catalog.json'; catalog.write_bytes(raw)
        for name, (length, sha, path) in documents.items():
            if name in assets: continue
            require(release.get('draft') is True, 'PublicationAssetMissing')
            result = subprocess.run(['gh', 'release', 'upload', tag, str(path or catalog), '--repo', INDEX], capture_output=True, timeout=120)
            require(result.returncode == 0, 'PublicationUploadFailed')
        release = api.json(PREFIX + '/releases/' + str(release['id'])); assets = assets_of(release)
        require(set(assets) == set(documents), 'PublicationAssetMissing')
        # Check actual stored bytes, including preexisting assets, before exposing a pointer.
        for name, (length, sha, _) in documents.items():
            asset = assets[name]
            identity = dict(repository=INDEX, repositoryId=REPOSITORY_ID, ownerId=OWNER_ID, sourceCommit=snapshot,
                tag=tag, releaseId=str(release['id']), assetId=str(asset['id']), assetName=name, sha256=sha, sizeBytes=length)
            api.download(identity, Path(temporary) / 'verify.bin')
    if release['draft']:
        api.json(PREFIX + '/releases/' + str(release['id']), 'PATCH', dict(draft=False))
    catalog_asset = assets['catalog.json']
    artifact = dict(repository=INDEX, repositoryId=REPOSITORY_ID, ownerId=OWNER_ID, sourceCommit=snapshot,
        tag=tag, releaseId=str(release['id']), assetId=str(catalog_asset['id']), assetName='catalog.json', sha256=digest(raw), sizeBytes=len(raw))
    api.verify_origin(artifact)
    return artifact
