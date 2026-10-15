"""Protect the shared writer queue and strict stale-event guard."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WriterQueueTests(unittest.TestCase):
    def test_every_metadata_writer_preserves_pending_runs(self):
        for name in ('plugin-admission.yml','plugin-label-admission.yml','plugin-source-updates.yml','plugin-publish.yml'):
            with self.subTest(workflow=name):
                text=(ROOT/'.github/workflows'/name).read_text()
                self.assertIn('concurrency:\n  group: index-metadata\n  queue: max\n  cancel-in-progress: false\n',text)
    def test_source_guard_runs_before_build_without_rebinding_event_sha(self):
        text=(ROOT/'.github/workflows/plugin-source-updates.yml').read_text()
        self.assertLess(text.index('Reject a superseded queued snapshot'),text.index('uses: ./.github/actions/prepare-validator'))
        self.assertIn('"$current" != "$GITHUB_SHA"',text)
        self.assertNotIn('export GITHUB_SHA=',text)
        self.assertIn("cron: '17 * * * *'",text)

    def test_publication_gate_precedes_build_and_noop_skips_feedback(self):
        text=(ROOT/'.github/workflows/plugin-publish.yml').read_text()
        self.assertLess(text.index('run: python3 scripts/publication_gate.py'),text.index('uses: ./.github/actions/prepare-validator'))
        self.assertIn("needs: gate\n    if: needs.gate.outputs.needed == 'true'",text)
        self.assertEqual(text.count("always() && needs.gate.outputs.needed == 'true'"),2)

    def test_validator_preparation_is_shared_without_widening_writer_permissions(self):
        action=(ROOT/'.github/actions/prepare-validator/action.yml').read_text()
        self.assertIn('dotnet build Validator/Validator.csproj',action)
        self.assertIn('python3 -m unittest discover -s tests -v',action)
        self.assertNotIn('GH_TOKEN',action)
        for path in (ROOT/'.github/workflows').glob('plugin-*.yml'):
            self.assertIn('uses: ./.github/actions/prepare-validator',path.read_text())

if __name__=='__main__':unittest.main()
