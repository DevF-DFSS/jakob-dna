import unittest
from compare_inventory import compare

class InventoryTests(unittest.TestCase):
    expected=[{'service':'lambda','name':'test','region':'us-east-1'}]
    def test_missing_is_unresolved(self):
        self.assertIn('UNRESOLVED',compare(self.expected,{'resources':[]})[0]['status'])
    def test_name_without_provenance_is_unresolved(self):
        self.assertIn('UNRESOLVED',compare(self.expected,{'resources':[{'service':'lambda','name':'test','region':'us-east-1'}]})[0]['status'])
    def test_other_region_is_unresolved(self):
        row={'service':'lambda','name':'test','region':'us-east-2','account':'synthetic','observed_at':'2026-09-24T00:00:00Z','evidence_ref':'synthetic'}
        self.assertIn('UNRESOLVED',compare(self.expected,{'resources':[row]})[0]['status'])
    def test_scoped_evidence_matches(self):
        row={'service':'lambda','name':'test','region':'us-east-1','account':'synthetic','observed_at':'2026-09-24T00:00:00Z','evidence_ref':'synthetic'}
        self.assertEqual(compare(self.expected,{'resources':[row]})[0]['status'],'OBSERVED_IN_SUPPLIED_INVENTORY')

if __name__=='__main__':
    unittest.main()
