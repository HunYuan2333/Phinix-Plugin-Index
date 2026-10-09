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
        self.assertLess(text.index('Reject a superseded queued snapshot'),text.index('actions/setup-dotnet@'))
        self.assertIn('"$current" != "$GITHUB_SHA"',text)
        self.assertNotIn('export GITHUB_SHA=',text)
        self.assertIn("cron: '17 * * * *'",text)

if __name__=='__main__':unittest.main()
