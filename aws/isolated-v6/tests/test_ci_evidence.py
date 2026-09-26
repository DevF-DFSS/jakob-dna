import json
from pathlib import Path
import unittest
from unittest.mock import patch
from ci_evidence import decision

class CIEvidenceTests(unittest.TestCase):
    def setUp(self):self.w=json.loads((Path(__file__).resolve().parents[3]/'.github/workflows/v6-evidence.yml').read_text())
    def test_read_only_standard_runner(self):
        self.assertEqual({'contents':'read'},self.w['permissions']);self.assertEqual('ubuntu-24.04',self.w['jobs']['offline']['runs-on'])
        self.assertEqual({'pull_request','workflow_dispatch'},set(self.w['on']))
        self.assertNotIn('secrets.',json.dumps(self.w));self.assertNotIn('id-token',json.dumps(self.w))
    def test_pinned_actions_and_no_persisted_git_credentials(self):
        steps=self.w['jobs']['offline']['steps']
        for s in steps:
            if 'uses' in s:self.assertRegex(s['uses'],r'^[\w/-]+@[0-9a-f]{40}$')
        self.assertFalse(steps[0]['with']['persist-credentials'])
    def test_lint_failure_is_failure(self):
        self.assertFalse(decision({'suite':0,'lint':1},True)['passed'])
    def test_build_difference_is_failure(self):self.assertFalse(decision({'suite':0},False)['passed'])
    def test_execution_sources_never_authorize(self):
        for value,source in [('true','GITHUB_CI_EXECUTION'),('false','LOCAL_EXECUTION')]:
            with patch.dict('os.environ',{'GITHUB_ACTIONS':value}):
                r=decision({'suite':0},True);self.assertTrue(r['passed']);self.assertEqual(source,r['evidence_class']);self.assertFalse(r['deployment_authorized'])
    def test_linux_hash_lock_preserves_all_validation_versions(self):
        root=Path(__file__).resolve().parents[1]
        original=(root/'validation-toolchain.lock').read_text().splitlines()
        locked=(root/'release/ci/linux-toolchain.lock').read_text().splitlines()
        self.assertEqual(original,[line.split(' --hash=')[0] for line in locked])
        for line in locked:self.assertRegex(line,r' --hash=sha256:[0-9a-f]{64}$')
