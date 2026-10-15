import os
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publication_gate as gate
from bot import INDEX, Rejected

ENV = dict(GITHUB_REPOSITORY=INDEX, GITHUB_REF='refs/heads/main', GITHUB_EVENT_NAME='workflow_run')


class PublicationGateTests(unittest.TestCase):
    def source(self, result):
        with patch.dict(os.environ, ENV, clear=True), patch.object(gate.labels, 'payload', return_value={
                'workflow_run': {'display_title': gate.updates.TITLE}}), patch.object(gate.updates, 'upstream', return_value=result) as proof:
            api = Mock()
            self.assertEqual(gate.needed(api), result is not None)
            proof.assert_called_once_with(api)
            api.json.assert_not_called()

    def test_no_updates_skips_heavy_jobs(self): self.source(None)
    def test_admitted_source_proceeds(self): self.source('123')

    def test_bad_source_proof_cannot_become_noop_success(self):
        with patch.dict(os.environ, ENV, clear=True), patch.object(gate.labels, 'payload', return_value={
                'workflow_run': {'display_title': gate.updates.TITLE}}), patch.object(gate.updates, 'upstream', side_effect=Rejected('PublicationTriggerRejected')):
            with self.assertRaises(Rejected): gate.needed(Mock())

    def test_label_needs_real_admit_job(self):
        for jobs, accepted in [([{'name': 'admit', 'conclusion': 'success'}], True),
                               ([{'name': 'admit', 'conclusion': 'skipped'}], False), ([], False)]:
            with patch.dict(os.environ, ENV, clear=True), patch.object(gate.labels, 'payload', return_value={
                    'workflow_run': {'display_title': 'Label admission #42'}}), patch.object(gate.labels, 'upstream', return_value='123') as proof:
                api = Mock(); api.json.return_value = {'jobs': jobs}
                if accepted: self.assertTrue(gate.needed(api))
                else:
                    with self.assertRaises(Rejected): gate.needed(api)
                proof.assert_called_once_with(api)

    def test_manual_entry_retains_publisher_checks(self):
        with patch.dict(os.environ, dict(ENV, GITHUB_EVENT_NAME='workflow_dispatch'), clear=True):
            api = Mock(); self.assertTrue(gate.needed(api)); api.json.assert_not_called()

    def test_wrong_repository_ref_or_trigger_rejected(self):
        for value in [dict(GITHUB_REPOSITORY='other/repo'), dict(GITHUB_REF='refs/heads/other'), dict(GITHUB_EVENT_NAME='push')]:
            with patch.dict(os.environ, dict(ENV, **value), clear=True):
                with self.assertRaises(Rejected): gate.needed(Mock())


if __name__ == '__main__': unittest.main()
