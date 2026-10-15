#!/usr/bin/env python3
"""Maintainer-dispatched data theme feed; never writes the plugin pointer."""
import argparse
import base64
import os
from pathlib import Path
import re
import tempfile
from bot import INDEX, GitHub, Rejected, require, strict_json, encode, digest
from admission import PREFIX, REPOSITORY_ID, OWNER_ID, maintainer, index, commit
from catalog import read, validate
from publisher import release_asset

SOURCE, BRANCH = 'phinix.themes', 'themes'


def build(root, snapshot, validator):
    require(re.fullmatch(r'[0-9a-f]{40}', snapshot) is not None, 'InvalidSnapshot')
    directory = root / 'themes/packages'
    require(not directory.is_symlink(), 'InputPathRejected')
    records = []
    if directory.exists():
        require(directory.is_dir(), 'InputPathRejected')
        for path in sorted(directory.iterdir()):
            require(path.is_file() and not path.is_symlink() and path.suffix == '.json', 'InputPathRejected')
            candidate = read(path)
            require(type(candidate) is dict and set(candidate) == {'schemaVersion', 'package'} and type(candidate['schemaVersion']) is int and candidate['schemaVersion'] == 1, 'SubmissionEnvelope')
            records.append(candidate['package'])
    require(len(records) <= 256, 'CollectionLimit')
    raw = encode(dict(schemaVersion=4, sourceId=SOURCE, snapshotId=snapshot, packages=records))
    with tempfile.TemporaryDirectory() as temporary:
        catalog = Path(temporary) / 'catalog.json'; catalog.write_bytes(raw)
        validate(validator, ['theme-catalog', SOURCE, str(catalog)])
    return raw


def revalidate(api, raw, validator):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary); catalog = root / 'catalog.json'; catalog.write_bytes(raw)
        for p in strict_json(raw)['packages']:
            if p['state'] != 'active': continue
            api.verify_origin(p['artifact'], data_only=True)
            archive = root / 'candidate.zip'; api.download(p['artifact'], archive)
            validate(validator, ['theme-payload', SOURCE, str(catalog), str(archive), p['id'], p['manifest']['version'], str(root / 'report.json')])


def envelopes(snapshot, raw, artifact):
    shared = dict(schemaVersion=1, sourceId=SOURCE, snapshotId=snapshot, catalogSchemaVersion=4, catalogSha256=digest(raw), catalogSizeBytes=len(raw))
    published = encode(dict(shared, **{key: artifact[key] for key in ('repository', 'repositoryId', 'ownerId', 'releaseId', 'assetId', 'assetName')}))
    return published, encode(dict(shared, publishedSha256=digest(published), publishedSizeBytes=len(published)))


def continuity(previous, current):
    old_rows = {(p['id'], p['manifest']['version']): p for p in previous['packages']}
    new_rows = {(p['id'], p['manifest']['version']): p for p in current['packages']}
    for key, p in old_rows.items():
        require(key in new_rows, 'ThemePublishedVersionRemoved')
        changed = dict(new_rows[key]); changed['state'] = p['state']
        require(changed == p, 'ThemePublishedVersionChanged')


def publish(args, api):
    require(os.environ.get('GITHUB_REPOSITORY') == INDEX and os.environ.get('GITHUB_REF') == 'refs/heads/main' and os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'ThemePublicationContextRejected')
    snapshot = os.environ.get('GITHUB_SHA', ''); actor = os.environ.get('GITHUB_TRIGGERING_ACTOR')
    actor_id = maintainer(api, actor); require(index(api) == snapshot, 'TrustedHeadChanged')
    raw = build(args.root, snapshot, args.validator); revalidate(api, raw, args.validator)
    path = PREFIX + '/git/ref/heads/' + BRANCH
    try:
        parent = api.json(path)['object']['sha']; exists = True
    except Rejected as ex:
        if str(ex) != 'OriginHttp404': raise
        parent = snapshot; exists = False
    if exists:
        old_file = api.json(PREFIX + '/contents/stable.json?ref=' + parent)
        old = strict_json(base64.b64decode(old_file['content']))
        require(old.get('sourceId') == SOURCE and old.get('catalogSchemaVersion') == 4, 'ThemeBranchConflict')
        old_file = api.json(PREFIX + '/contents/published/' + old['snapshotId'] + '.json?ref=' + parent)
        published_raw = base64.b64decode(old_file['content'])
        require(digest(published_raw) == old['publishedSha256'] and len(published_raw) == old['publishedSizeBytes'], 'PublicationDescriptorMismatch')
        old_p = strict_json(published_raw)
        require(old_p.get('repository') == INDEX and old_p.get('repositoryId') == REPOSITORY_ID and old_p.get('ownerId') == OWNER_ID and all(old_p.get(k) == old.get(k) for k in ('sourceId','snapshotId','catalogSchemaVersion','catalogSha256','catalogSizeBytes')), 'ThemeBranchConflict')
        old_asset = dict(repository=INDEX, repositoryId=REPOSITORY_ID, ownerId=OWNER_ID, releaseId=old_p['releaseId'], assetId=old_p['assetId'], assetName='catalog.json', sizeBytes=old['catalogSizeBytes'], sha256=old['catalogSha256'])
        with tempfile.TemporaryDirectory() as temporary:
            prior = Path(temporary) / 'catalog.json'; api.download(old_asset, prior)
            previous = strict_json(prior.read_bytes())
            require(previous.get('sourceId') == SOURCE and previous.get('schemaVersion') == 4, 'ThemeBranchConflict')
            continuity(previous, strict_json(raw))
    require(index(api) == snapshot and maintainer(api, actor, actor_id) == actor_id, 'TrustedHeadChanged')
    if args.check_only:
        print('Theme publication check passed; no remote writes.'); return
    artifact = release_asset(api, snapshot, raw, catalog_schema=4)
    published, stable = envelopes(snapshot, raw, artifact)
    require(index(api) == snapshot, 'TrustedHeadChanged')
    receipt = encode(dict(schemaVersion=1, sourceId=SOURCE, inputCommit=snapshot, actor=actor, actorId=actor_id, runId=os.environ['GITHUB_RUN_ID'], catalogSha256=digest(raw)))
    head = commit(api, parent, {'published/' + snapshot + '.json': published, 'stable.json': stable, 'theme-approval-receipts/' + snapshot + '.json': receipt}, 'Publish theme catalog v4 ' + snapshot)
    if exists: api.json(PREFIX + '/git/refs/heads/' + BRANCH, 'PATCH', dict(sha=head, force=False))
    else: api.json(PREFIX + '/git/refs', 'POST', dict(ref='refs/heads/' + BRANCH, sha=head))
    print('Published separate theme feed ' + digest(raw))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--validator', type=Path, required=True)
    parser.add_argument('--snapshot'); parser.add_argument('--output', type=Path)
    parser.add_argument('--check-only', action='store_true'); args = parser.parse_args()
    try:
        if args.output:
            require(args.snapshot is not None and not args.output.exists(), 'FreshOutputRequired')
            raw = build(args.root, args.snapshot, args.validator)
            with args.output.open('xb') as handle: handle.write(raw)
        else: publish(args, GitHub(max_calls=2048, timeout=1800))
    except (Rejected, ValueError, KeyError, TypeError, OSError) as ex: parser.exit(1, str(ex) + '\n')


if __name__ == '__main__': main()
