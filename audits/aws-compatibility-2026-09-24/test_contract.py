import unittest
from check_contract import *

class ContractChecks(unittest.TestCase):
    def table(self, hash_name="userId", range_type="N"):
        return {"KeySchema": [{"AttributeName":hash_name,"KeyType":"HASH"},
                             {"AttributeName":"timestamp","KeyType":"RANGE"}],
                "AttributeDefinitions":[{"AttributeName":hash_name,"AttributeType":"S"},
                                        {"AttributeName":"timestamp","AttributeType":range_type}]}
    def test_matching_table(self):
        self.assertEqual(table_status(self.table()), COMPATIBLE)
    def test_index_cannot_replace_primary_key(self):
        t=self.table("memoryId")
        t["AttributeDefinitions"].append({"AttributeName":"userId","AttributeType":"S"})
        t["GlobalSecondaryIndexes"]=[{"IndexName":"userId-index"}]
        self.assertEqual(table_status(t), MIGRATE)
    def test_string_timestamp_incompatible(self):
        self.assertEqual(table_status(self.table(range_type="S")), MIGRATE)
    def test_missing_schema_unknown(self):
        self.assertEqual(table_status({}), UNRESOLVED)
    def test_missing_table_name(self):
        self.assertEqual(function_status({"Runtime":"python3.12","Handler":"lambda_function.lambda_handler","table_name_present":False}), MIGRATE)
    def test_node_runtime_migration(self):
        self.assertEqual(function_status({"Runtime":"nodejs24.x"}), MIGRATE)
    def test_none_authorization_blocks_candidate(self):
        self.assertEqual(route_status({"AuthorizationType":"NONE"}), BLOCKED)
    def test_authorizer_presence_does_not_prove_security(self):
        self.assertEqual(route_status({"AuthorizationType":"JWT"}), UNRESOLVED)
    def test_absent_evidence_is_not_compatible(self):
        self.assertEqual(route_status({}), UNRESOLVED)
        self.assertEqual(function_status({}), UNRESOLVED)

if __name__ == "__main__":
    unittest.main()
