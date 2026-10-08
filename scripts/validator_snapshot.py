#!/usr/bin/env python3
"""Check a pinned validator snapshot; refresh only from an explicit trusted source tree."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PREFIXES = ('Common/Utils/Framework/ManagedExtensions/', 'Extensions/PluginStore/Client/')
ORIGIN_REPOSITORIES = {'client': 'HunYuan2333/Phinix-Rework', 'common': 'HunYuan2333/Phinix-Rework-Common'}
ORIGIN_PREFIXES = {'client': (SOURCE_PREFIXES[1],), 'common': (SOURCE_PREFIXES[0],)}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('SnapshotDuplicateField')
        result[key] = value
    return result


def bounded(path):
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('SnapshotFileLimit')
    return path.read_bytes()


def path_in(root, relative, prefixes):
    if not isinstance(relative, str) or '\\' in relative:
        raise ValueError('SnapshotPathRejected')
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != relative or not relative.startswith(prefixes) or path.suffix != '.cs':
        raise ValueError('SnapshotPathRejected')
    full = root / relative
    current = full
    while current != root:
        if current.is_symlink():
            raise ValueError('SnapshotLinkRejected')
        current = current.parent
    return full


def inspect(root, source_root=None, source_roots=None):
    root = Path(root).resolve()
    manifest_path = root / 'Validator/production-provenance.json'
    if manifest_path.is_symlink():
        raise ValueError('SnapshotLinkRejected')
    manifest = json.loads(bounded(manifest_path), object_pairs_hook=unique)
    if manifest.get('schemaVersion') not in (1, 2) or not isinstance(manifest.get('files'), list) or not 1 <= len(manifest['files']) <= 64:
        raise ValueError('SnapshotManifestRejected')
    split = manifest['schemaVersion'] == 2
    if split:
        validate_origins(manifest.get('origins'))
        if source_root is not None:
            raise ValueError('SnapshotSplitRootsRequired')
        if source_roots is not None:
            validate_checkouts(source_roots, manifest['origins'])
    elif source_roots is not None:
        raise ValueError('SnapshotMigrationRequired')
    sources, snapshots, content = set(), set(), []
    for record in manifest['files']:
        if set(record) != ({'origin', 'source', 'snapshot', 'sha256'} if split else {'source', 'snapshot', 'sha256'}):
            raise ValueError('SnapshotRecordRejected')
        source, snapshot = record['source'], record['snapshot']
        role = record.get('origin')
        if split and role not in ORIGIN_REPOSITORIES:
            raise ValueError('SnapshotOriginRejected')
        if not isinstance(record['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', record['sha256']):
            raise ValueError('SnapshotDigestRejected')
        target = path_in(root, snapshot, ('Validator/Production/',))
        # Validate source paths even when the standalone index has no main source checkout.
        origin = path_in(Path(source_roots[role]).resolve() if split and source_roots else Path(source_root).resolve() if source_root else root, source, ORIGIN_PREFIXES[role] if split else SOURCE_PREFIXES)
        if source in sources or snapshot in snapshots:
            raise ValueError('SnapshotDuplicateFile')
        sources.add(source); snapshots.add(snapshot)
        frozen = bounded(target)
        if hashlib.sha256(frozen).hexdigest() != record['sha256']:
            raise ValueError('SnapshotDigestMismatch: ' + snapshot)
        if split and source_roots is not None:
            content.append((record, target, committed_source(Path(source_roots[role]).resolve(), manifest['origins'][role]['commit'], source)))
        elif source_root:
            content.append((record, target, bounded(origin)))
    actual = {p.relative_to(root).as_posix() for p in (root / 'Validator/Production').rglob('*.cs')}
    if actual != snapshots:
        raise ValueError('SnapshotFileSetMismatch')
    return manifest, manifest_path, content


def check(root, source_root=None, source_roots=None):
    manifest, _, content = inspect(root, source_root, source_roots)
    for record, _, raw in content:
        if hashlib.sha256(raw).hexdigest() != record['sha256']:
            raise ValueError('SnapshotSourceChanged: ' + record['source'])
    return len(manifest['files'])


def atomic(path, raw):
    descriptor, name = tempfile.mkstemp(prefix='.snapshot-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def refresh(root, source_root):
    # Read and validate the complete source set before replacing any frozen file.
    manifest, path, content = inspect(root, source_root)
    for record, target, raw in content:
        atomic(target, raw)
        record['sha256'] = hashlib.sha256(raw).hexdigest()
    atomic(path, (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    return check(root, source_root)


def git(root, *arguments):
    result = subprocess.run(['git', '-C', str(root), *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError('SnapshotGitSourceRejected')
    return result.stdout


def validate_origins(origins):
    if not isinstance(origins, dict) or set(origins) != set(ORIGIN_REPOSITORIES):
        raise ValueError('SnapshotOriginsRejected')
    for role, origin in origins.items():
        if not isinstance(origin, dict) or set(origin) != {'repository', 'commit'} or origin['repository'] != ORIGIN_REPOSITORIES[role]:
            raise ValueError('SnapshotOriginRejected')
        if not isinstance(origin['commit'], str) or not re.fullmatch('[0-9a-f]{40}', origin['commit']):
            raise ValueError('SnapshotCommitRejected')


def validate_checkouts(roots, origins):
    if set(roots) != set(ORIGIN_REPOSITORIES):
        raise ValueError('SnapshotSplitRootsRequired')
    for role, location in roots.items():
        root = Path(location).resolve()
        if git(root, 'rev-parse', 'HEAD').decode().strip() != origins[role]['commit']:
            raise ValueError('SnapshotCommitMismatch: ' + role)
        url = git(root, 'remote', 'get-url', 'origin').decode().strip()
        expected = 'https://github.com/' + origins[role]['repository']
        if url.rstrip('/').removesuffix('.git').lower() != expected.lower():
            raise ValueError('SnapshotRepositoryMismatch: ' + role)
    link = git(roots['client'], 'ls-tree', origins['client']['commit'], 'Dependencies/Phinix.Common').decode().strip()
    if link != '160000 commit ' + origins['common']['commit'] + '\tDependencies/Phinix.Common':
        raise ValueError('SnapshotSharedPinMismatch')


def committed_source(root, commit, source):
    file = path_in(root, source, SOURCE_PREFIXES)
    raw = git(root, 'show', commit + ':' + source)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError('SnapshotFileLimit')
    if bounded(file) != raw:
        raise ValueError('SnapshotSourceDirty: ' + source)
    return raw


def refresh_split(root, roots, origins=None):
    # Freeze only bytes from explicit, matching trusted client/common commits.
    manifest, path, _ = inspect(root)
    if origins is None:
        if manifest['schemaVersion'] != 2:
            raise ValueError('SnapshotOriginsRequired')
        origins = manifest['origins']
    validate_origins(origins)
    validate_checkouts(roots, origins)
    content = []
    for record in manifest['files']:
        role = 'common' if record['source'].startswith(SOURCE_PREFIXES[0]) else 'client'
        path_in(Path(roots[role]).resolve(), record['source'], ORIGIN_PREFIXES[role])
        raw = committed_source(Path(roots[role]).resolve(), origins[role]['commit'], record['source'])
        content.append((record, path_in(Path(root).resolve(), record['snapshot'], ('Validator/Production/',)), role, raw))
    # Validation of every input completes before any frozen file is replaced.
    for record, target, role, raw in content:
        atomic(target, raw)
        record['origin'] = role
        record['sha256'] = hashlib.sha256(raw).hexdigest()
    manifest['schemaVersion'] = 2
    manifest.pop('originRepository', None)
    manifest['origins'] = origins
    atomic(path, (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    return check(root, source_roots=roots)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'refresh'))
    parser.add_argument('--source-root', type=Path, help='Legacy schema-1 monorepo input only')
    parser.add_argument('--client-root', type=Path)
    parser.add_argument('--common-root', type=Path)
    parser.add_argument('--client-commit')
    parser.add_argument('--common-commit')
    args = parser.parse_args()
    split = args.client_root is not None or args.common_root is not None
    pins = args.client_commit is not None or args.common_commit is not None
    if split and (args.client_root is None or args.common_root is None or args.source_root is not None):
        parser.error('supply both --client-root and --common-root, without --source-root')
    if pins and (not split or args.action != 'refresh' or not args.client_commit or not args.common_commit):
        parser.error('explicit commits require split refresh and both commit arguments')
    if args.action == 'refresh' and args.source_root is None and not split:
        parser.error('refresh requires explicit trusted source roots; candidate code is never a source tree')
    roots = {'client': args.client_root, 'common': args.common_root} if split else None
    origins = {role: {'repository': repository, 'commit': getattr(args, role + '_commit')}
               for role, repository in ORIGIN_REPOSITORIES.items()} if pins else None
    try:
        if args.action == 'refresh':
            count = refresh_split(ROOT, roots, origins) if split else refresh(ROOT, args.source_root)
        else:
            count = check(ROOT, args.source_root, roots)
        print(json.dumps({'event': 'validator.snapshot_checked', 'files': count, 'sourceCompared': args.source_root is not None or split}))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
