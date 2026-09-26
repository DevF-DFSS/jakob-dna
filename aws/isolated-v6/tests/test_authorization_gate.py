import copy
import json
from pathlib import Path
import unittest
from authorization_gate import evaluate,digest,KINDS

NOW='2026-09-25T12:00:00Z'
C={'account_id':'111111111111','region':'us-east-1','operator_arn':'arn:aws:iam::111111111111:role/jel-v6-approved/operator','recovery_arn':'arn:aws:iam::111111111111:role/jel-v6-approved/recovery','candidate_commit':'a'*40,**{k:'b'*64 for k in ['artifact_sha256','template_sha256','bootstrap_sha256','binding_sha256']}}

class AuthorizationGateTests(unittest.TestCase):
    def setUp(self):
        self.r={'schema_version':'jel-v6-authorization/1','context':copy.deepcopy(C),'blockers':[],'evidence':[
            {'kind':k,'source':'synthetic-independent-verifier','mode':mode,'observed_at':NOW,'context':copy.deepcopy(C),'result':'PASS','approval':{'by':'DevF','decision':'AUTHORIZE_SANDBOX','review_reference':'synthetic-only'} if k=='devf_authorization' else None} for k,mode in KINDS.items()]}
    def run_gate(self,verify=True):return evaluate(self.r,C,now=NOW,verified_digests={digest(e) for e in self.r['evidence']} if verify else set())
    def denied(self):
        r=self.run_gate();self.assertNotEqual('COMPLETE',r['status']);self.assertFalse(r['deployment_authorized'])
    def test_synthetic_complete_never_authorizes_execution(self):
        r=self.run_gate();self.assertEqual('COMPLETE',r['status']);self.assertFalse(r['deployment_authorized'])
    def test_each_missing_kind_is_unknown(self):
        original=copy.deepcopy(self.r)
        for k in KINDS:
            self.r=copy.deepcopy(original);self.r['evidence']=[e for e in self.r['evidence'] if e['kind']!=k]
            with self.subTest(kind=k):self.assertEqual('UNKNOWN',self.run_gate()['status'])
    def test_stale_future_and_malformed_times(self):
        for t in ['2026-09-24T11:59:59Z','2026-09-25T12:00:01Z','yesterday','2026-09-25T12:00:00']:
            self.r['evidence'][0]['observed_at']=t;self.denied()
    def test_freshness_boundary(self):
        self.r['evidence'][0]['observed_at']='2026-09-24T12:00:00Z';self.assertEqual('COMPLETE',self.run_gate()['status'])
    def test_wrong_account_region_commit_operator_and_artifacts(self):
        for key in C:
            r=copy.deepcopy(self.r);self.r['evidence'][0]['context'][key]='wrong'
            with self.subTest(key=key):self.denied()
            self.r=r
    def test_record_context_mismatch(self):self.r['context']['region']='us-east-2';self.denied()
    def test_historical_tests_cannot_be_current(self):
        for e in self.r['evidence']:
            if e['kind']=='offline_validation':e['mode']='HISTORICAL'
        self.denied()
    def test_blockers_fail_closed(self):self.r['blockers']=['unresolved IAM'];self.denied()
    def test_missing_explicit_approval(self):self.r['evidence'][-1]['approval']=None;self.denied()
    def test_unverified_claims_are_unknown(self):self.assertEqual('UNKNOWN',self.run_gate(False)['status'])
    def test_tampered_previously_verified_evidence(self):
        verified={digest(e) for e in self.r['evidence']};self.r['evidence'][0]['source']='forged'
        self.assertEqual('UNKNOWN',evaluate(self.r,C,now=NOW,verified_digests=verified)['status'])
    def test_contradictory_duplicate_evidence(self):self.r['evidence'].append(copy.deepcopy(self.r['evidence'][0]));self.denied()
    def test_failed_evidence(self):self.r['evidence'][0]['result']='FAIL';self.denied()
    def test_root_operator_rejected(self):
        c=copy.deepcopy(C);c['operator_arn']='arn:aws:iam::111111111111:root'
        self.assertEqual('BLOCKED',evaluate(self.r,c,now=NOW)['status'])
    def test_recovery_wrong_path_or_account_rejected(self):
        for arn in ['arn:aws:iam::111111111111:role/legacy','arn:aws:iam::222222222222:role/jel-v6-approved/recovery']:
            c=copy.deepcopy(C);c['recovery_arn']=arn;self.assertEqual('BLOCKED',evaluate(self.r,c,now=NOW)['status'])
    def test_malformed_inputs_and_unknown_fields(self):
        for r in [None,{},dict(self.r,bypass=True),dict(self.r,blockers=None)]:
            self.assertEqual('BLOCKED',evaluate(r,C,now=NOW)['status'])
    def test_real_record_remains_blocked(self):
        p=Path(__file__).resolve().parents[1]/'release/authorization/current.json'
        self.assertEqual('BLOCKED',evaluate(json.loads(p.read_text()),C,now=NOW)['status'])
    def test_recovery_design_is_unconfigured_and_not_admin(self):
        p=Path(__file__).resolve().parents[1]/'release/authorization/recovery-operator.json'
        r=json.loads(p.read_text());self.assertIsNone(r['trusted_federated_principal']);self.assertFalse(r['deployment_authorized'])
        statements=r['normal_policy_template']['Statement']
        allows=[s for s in statements if s['Effect']=='Allow']
        self.assertTrue(all(s['Resource']!='*' for s in allows))
        actions=[a for s in allows for a in (s['Action'] if isinstance(s['Action'],list) else [s['Action']])]
        self.assertEqual({'cloudformation:DescribeStacks','cloudformation:DescribeStackEvents','cloudformation:DescribeStackResources','cloudformation:GetTemplate','cloudformation:UpdateStack','cloudformation:ContinueUpdateRollback','iam:PassRole'},set(actions))
        passrole=next(s for s in allows if s['Action']=='iam:PassRole')
        self.assertEqual('${DeploymentRoleArn}',passrole['Resource'])
        self.assertEqual({'StringEquals':{'iam:PassedToService':'cloudformation.amazonaws.com'}},passrole['Condition'])
