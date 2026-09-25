"""Offline audit-evidence checks; no SDK imports or network calls."""
import ast
import re
import json
from pathlib import Path
import unittest
from compare import compare

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'evidence.json').read_text())
ALLOWED = {
 'sts': {'GetCallerIdentity'}, 'ec2': {'DescribeRegions'},
 'lambda': {'ListFunctions','GetFunctionConfiguration','ListAliases','ListVersionsByFunction','GetPolicy','ListFunctionUrlConfigs','GetAccountSettings'},
 'dynamodb': {'ListTables','DescribeTable'},
 'apigatewayv2': {'GetApis','GetRoutes','GetIntegrations','GetStages','GetAuthorizers'},
 'cognito-idp': {'ListUserPools'},
 'iam': {'ListRoles','GetRole','ListAttachedRolePolicies','ListRolePolicies','GetRolePolicy','GetPolicy','GetPolicyVersion','ListOpenIDConnectProviders','GetOpenIDConnectProvider','SimulatePrincipalPolicy'},
 'organizations': {'DescribeOrganization','ListPoliciesForTarget','ListParents'},
 's3': {'ListBuckets','GetBucketLocation','GetBucketVersioning'},
 'service-quotas': {'ListServiceQuotas'}, 'cloudformation': {'ListStacks'},
 'logs': {'DescribeLogGroups'}, 'cloudwatch': {'DescribeAlarms'},
}

class EvidenceTests(unittest.TestCase):
    def test_executed_operation_allowlist(self):
        calls = [c for b in DATA.values() for c in b['api_calls']]
        self.assertEqual(180,len(calls))
        for c in calls:
            self.assertIn(c['operation'],ALLOWED[c['service']])
        failed = [c for c in calls if c['status'] != 'success']
        self.assertEqual(3,len(failed))
        self.assertTrue(all('AWSOrganizationsNotInUseException' in c['error'] for c in failed))

    def test_no_environment_values_or_code_urls(self):
        def walk(x):
            if isinstance(x,dict):
                for k,v in x.items():
                    self.assertNotIn(k,{'Variables','AccessKeyId','SecretAccessKey','SessionToken','ClientSecret','SecretString','SecretBinary','CodeLocation'})
                    walk(v)
            elif isinstance(x,list):
                for v in x: walk(v)
        walk(DATA)

    def test_discovery_has_no_silent_failures(self):
        d = DATA['batch1']['snapshot']
        self.assertEqual(17,len(d['regions']))
        self.assertEqual(set(d['regions']),{r['region'] for r in d['inventory']})
        for r in d['inventory']:
            self.assertFalse(r['errors'])
        for r in DATA['batch2']['snapshot']['regions']:
            self.assertFalse(r['errors'])

    def test_ancestry_is_not_pr_number_order(self):
        prs = {r['number']:r for r in json.loads((ROOT/'lineage.json').read_text())}
        for i in [3,4,5,6]:
            self.assertEqual([prs[2]['head']],prs[i]['commits'][0]['parents'])
        for i in [7,8,9]:
            self.assertEqual([prs[i-1]['head']],prs[i]['commits'][0]['parents'])
        self.assertEqual('f7acf43f1f4a87fbbcda068a94a5037427750b24',prs[9]['head'])
        self.assertTrue(all(not p['merged'] for p in prs.values()))

    def test_simulation_not_data_api(self):
        for r in DATA['batch5']['snapshot']['results']:
            self.assertIn('jel-v6-sandbox-20260925',r['resource'])
            results=r['simulation']['EvaluationResults']
            if 'dynamodb:GetItem' in r['actions']:
                self.assertTrue(all(v['EvalDecision']=='allowed' for v in results))

    def test_delta_snapshot(self):
        rows=json.loads((ROOT/'delta.json').read_text())
        self.assertEqual(22,len(rows))
        self.assertTrue(all(r['delta']=='unchanged' for r in rows))
        self.assertEqual(4,len([r for r in rows if r['kind']=='table']))

    def test_compare_detects_drift_and_missing_observation(self):
        old={'details':{'regions':[{'region':'test','functions':[],'tables':[{'TableName':'t','KeySchema':[],'AttributeDefinitions':[],'TableStatus':'ACTIVE'}],'apis':[]}]}}
        new={'batch2':{'snapshot':{'regions':[{'region':'test','functions':[],'tables':[{'TableName':'t','KeySchema':[],'AttributeDefinitions':[],'TableStatus':'UPDATING'}],'apis':[]}]}}}
        self.assertEqual('changed',compare(old,new)[0]['delta'])
        new['batch2']['snapshot']['regions']=[]
        self.assertEqual('🐈📦 UNRESOLVED',compare(old,new)[0]['delta'])

    def test_no_credentials_or_presigned_urls(self):
        for path in ROOT.rglob('*'):
            if not path.is_file() or '__pycache__' in str(path) or path.name == 'test_evidence.py':
                continue
            value = path.read_text()
            self.assertIsNone(re.search(r'(?:AKIA|ASIA)[A-Z0-9]{16}', value), str(path))
            self.assertIsNone(re.search(r'(?i)(?:x-amz-signature|x-amz-credential|x-amz-security-token|AWSAccessKeyId)=', value), str(path))
            self.assertNotIn('-----BEGIN PRIVATE KEY-----', value)

    def test_scripts_parse_without_executing(self):
        for path in (ROOT/'scripts').glob('*.py'):
            ast.parse(path.read_text())

if __name__=='__main__': unittest.main()
