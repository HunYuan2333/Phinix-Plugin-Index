import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validator_snapshot', ROOT / 'scripts/validator_snapshot.py')
snapshot = importlib.util.module_from_spec(spec); spec.loader.exec_module(snapshot)


class ValidatorSnapshotTests(unittest.TestCase):
    def fixture(self, temporary):
        root, source = Path(temporary) / 'index', Path(temporary) / 'main'
        target = root / 'Validator/Production/Test.cs'; target.parent.mkdir(parents=True)
        origin = source / 'Extensions/PluginStore/Client/Test.cs'; origin.parent.mkdir(parents=True)
        target.write_bytes(b'old'); origin.write_bytes(b'old')
        manifest = {'schemaVersion': 1, 'files': [{'source': origin.relative_to(source).as_posix(),
                    'snapshot': target.relative_to(root).as_posix(), 'sha256': snapshot.hashlib.sha256(b'old').hexdigest()}]}
        (root / 'Validator/production-provenance.json').write_text(json.dumps(manifest))
        return root, source, target, origin

    def test_checked_in_snapshot_integrity(self):
        self.assertGreater(snapshot.check(ROOT), 0)

    def test_main_source_consistency_when_source_checkout_is_available(self):
        source = next((parent for parent in ROOT.parents if (parent / 'Common/Utils/Utils.csproj').is_file()), None)
        if source is None:
            self.skipTest('Standalone index has no main source checkout; integrity is checked separately')
        self.assertGreater(snapshot.check(ROOT, source), 0)

    def test_source_drift_is_detected_and_explicit_refresh_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, target, origin = self.fixture(temporary)
            origin.write_bytes(b'new')
            with self.assertRaisesRegex(ValueError, 'SnapshotSourceChanged'):
                snapshot.check(root, source)
            self.assertEqual(snapshot.refresh(root, source), 1)
            self.assertEqual(target.read_bytes(), b'new')
            self.assertEqual(snapshot.refresh(root, source), 1)

    def test_modified_or_undeclared_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, target, origin = self.fixture(temporary)
            target.write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'SnapshotDigestMismatch'):
                snapshot.refresh(root, source)
            target.write_bytes(b'old'); (target.parent / 'Unexpected.cs').write_bytes(b'new')
            with self.assertRaisesRegex(ValueError, 'SnapshotFileSetMismatch'):
                snapshot.check(root)

    def test_path_escape_and_source_link_fail_before_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, target, origin = self.fixture(temporary)
            origin.unlink(); origin.symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'SnapshotLinkRejected'):
                snapshot.refresh(root, source)
            self.assertEqual(target.read_bytes(), b'old')
            path = root / 'Validator/production-provenance.json'; manifest = json.loads(path.read_text())
            manifest['files'][0]['source'] = 'Extensions/PluginStore/Client/../../../secret.cs'
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'SnapshotPathRejected'):
                snapshot.check(root)

    def test_missing_later_source_does_not_partially_refresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, source, target, origin = self.fixture(temporary)
            extra = target.parent / 'Missing.cs'; extra.write_bytes(b'old')
            path = root / 'Validator/production-provenance.json'; manifest = json.loads(path.read_text())
            manifest['files'].append({'source': 'Extensions/PluginStore/Client/Missing.cs',
                                     'snapshot': extra.relative_to(root).as_posix(), 'sha256': snapshot.hashlib.sha256(b'old').hexdigest()})
            path.write_text(json.dumps(manifest)); origin.write_bytes(b'new')
            with self.assertRaises(FileNotFoundError):
                snapshot.refresh(root, source)
            self.assertEqual(target.read_bytes(), b'old')


class SplitValidatorSnapshotTests(unittest.TestCase):
    def fixture(self, temporary):
        import subprocess
        parent = Path(temporary)
        index = parent / 'index'
        roots = {'client': parent / 'client', 'common': parent / 'common'}
        records = []
        origins = {}
        for role in ['common', 'client']:
            root = roots[role]; root.mkdir()
            def run(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()
            run('init', '-q'); run('config', 'user.name', 'Snapshot Test'); run('config', 'user.email', 'snapshot@example.invalid')
            run('remote', 'add', 'origin', 'https://github.com/' + snapshot.ORIGIN_REPOSITORIES[role] + '.git')
            source = snapshot.ORIGIN_PREFIXES[role][0] + 'Test.cs'
            path = root / source; path.parent.mkdir(parents=True); path.write_bytes(role.encode())
            run('add', '.')
            if role == 'client':
                run('update-index', '--add', '--cacheinfo', '160000,' + origins['common']['commit'] + ',Dependencies/Phinix.Common')
            run('commit', '-qm', 'trusted fixture')
            origins[role] = {'repository': snapshot.ORIGIN_REPOSITORIES[role], 'commit': run('rev-parse', 'HEAD')}
            target = index / ('Validator/Production/' + role + '.cs'); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b'old')
            records.append({'source': source, 'snapshot': target.relative_to(index).as_posix(), 'sha256': snapshot.hashlib.sha256(b'old').hexdigest()})
        manifest = index / 'Validator/production-provenance.json'
        manifest.write_text(json.dumps({'schemaVersion': 1, 'files': records}))
        return index, roots, origins, manifest

    def test_split_migration_and_repeated_refresh(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            self.assertEqual(snapshot.refresh_split(index, roots, origins), 2)
            self.assertEqual(snapshot.refresh_split(index, roots), 2)
            self.assertEqual(snapshot.check(index), 2)
            self.assertEqual(snapshot.check(index, source_roots=roots), 2)
            self.assertEqual(json.loads(manifest.read_text())['origins'], origins)
            with self.assertRaisesRegex(ValueError, 'SnapshotSplitRootsRequired'):
                snapshot.check(index, roots['client'])

    def test_dirty_source_rejected_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            path = roots['client'] / (snapshot.ORIGIN_PREFIXES['client'][0] + 'Test.cs'); path.write_bytes(b'candidate')
            before = manifest.read_bytes()
            with self.assertRaisesRegex(ValueError, 'SnapshotSourceDirty'):
                snapshot.refresh_split(index, roots, origins)
            self.assertEqual(manifest.read_bytes(), before)
            self.assertEqual((index / 'Validator/Production/common.cs').read_bytes(), b'old')

    def test_wrong_commit_and_missing_roots_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            with self.assertRaisesRegex(ValueError, 'SnapshotSplitRootsRequired'):
                snapshot.refresh_split(index, {'client': roots['client']}, origins)
            origins['client']['commit'] = 'a' * 40
            with self.assertRaisesRegex(ValueError, 'SnapshotCommitMismatch'):
                snapshot.refresh_split(index, roots, origins)

    def test_wrong_remote_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            snapshot.git(roots['common'], 'remote', 'set-url', 'origin', 'https://example.invalid/candidate.git')
            with self.assertRaisesRegex(ValueError, 'SnapshotRepositoryMismatch'):
                snapshot.refresh_split(index, roots, origins)

    def test_shared_gitlink_must_match_pinned_common(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            snapshot.git(roots['common'], '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-qm', 'new shared')
            origins['common']['commit'] = snapshot.git(roots['common'], 'rev-parse', 'HEAD').decode().strip()
            with self.assertRaisesRegex(ValueError, 'SnapshotSharedPinMismatch'):
                snapshot.refresh_split(index, roots, origins)

    def test_record_cannot_cross_repository_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            snapshot.refresh_split(index, roots, origins)
            value = json.loads(manifest.read_text()); value['files'][0]['origin'] = 'client'; manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'SnapshotPathRejected'):
                snapshot.check(index)

    def test_invalid_provenance_rejected_without_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            index, roots, origins, manifest = self.fixture(temporary)
            snapshot.refresh_split(index, roots, origins)
            value = json.loads(manifest.read_text()); value['origins']['common']['commit'] = 'dev'; manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'SnapshotCommitRejected'):
                snapshot.check(index)
