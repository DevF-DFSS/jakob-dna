from copy import deepcopy
import unittest
from authorization_gate import digest
from phase_plan import evaluate

NOW='2026-01-01T00:30:00Z'


def fixture(phase='RUNTIME'):
    from phase_plan import PHASES,EVIDENCE
    mode=PHASES[phase][2]
    c={'account':'111111111111','region':'us-east-1','source_commit':'a'*40,'parent_commit':'b'*40,
       'templates':{k:'c'*64 for k in ['bootstrap','authority','runtime','ingress']},
       'parameters_sha256':{k:'9'*64 for k in ['bootstrap','authority','runtime','ingress']},
       'bindings_sha256':'d'*64,'artifact_sha256':'e'*64,'capability_sha256':'f'*64,'capability_mode':mode,
       's3':{'bucket':'jel-v6-111111111111-us-east-1-synthetic','key':'releases/'+'e'*64+'.zip','version':'version1'},
       'stacks':{'bootstrap':'jel-v6-bootstrap-test','authority':'jel-v6-authority-test','runtime':'jel-v6-sandbox-test','ingress':'jel-v6-ingress-test'},
       'roles':{k:'arn:aws:iam::111111111111:role/jel-v6-approved/'+k for k in ['operator','recovery','bootstrap_service','runtime_service','ingress_service','publisher']},
       'api_id':'synthetic','provider_profile_sha256':'1'*64 if phase in ['TEST_INGRESS','SANDBOX','PUBLISH_TEST','PUBLISH_SANDBOX'] else None}
    if phase in ['BOOTSTRAP','AUTHORITY'] or phase.startswith('PUBLISH_'):c['s3']['version']='NOT_PUBLISHED'
    if phase=='BOOTSTRAP':c['api_id']=None
    prior,mutation,_,stack=PHASES[phase]
    p={'schema_version':'jel-v6-phase-plan/1','phase':phase,'context':deepcopy(c),
       'previous':{'state':prior,'result':'COMPLETE','receipt_sha256':None if phase=='BOOTSTRAP' else '2'*64},
       'mutation_class':mutation,'resources':['arn:aws:cloudformation:us-east-1:111111111111:stack/'+c['stacks'].get(stack,'UNUSED')+'/*'],
       'starts_at':'2026-01-01T00:00:00Z','expires_at':'2026-01-01T01:00:00Z',
       'stop_conditions':['any_failed_or_unknown_gate','any_partial_create','any_unexpected_resource','window_expired'],
       'rollback':{'strategy':'QUARANTINE_THEN_SEPARATE_RECOVERY_AUTHORIZATION','operator_arn':c['roles']['recovery'],'procedure_sha256':'3'*64},
       'blockers':[],'evidence':[]}
    if stack=='artifact':p['resources']=['arn:aws:s3:::'+c['s3']['bucket']+'/'+c['s3']['key']]
    if phase=='TEST_INGRESS':p['resources'].append('arn:aws:cloudformation:us-east-1:111111111111:stack/'+c['stacks']['runtime']+'/*')
    op=digest({k:v for k,v in p.items() if k!='evidence'})
    kinds=dict(EVIDENCE)
    if phase in ('SANDBOX','PUBLISH_SANDBOX'):kinds['sandbox_observations']='OBSERVED_LIVE_BEHAVIOR'
    p['evidence']=[{'kind':k,'class':v,'source':'synthetic-test-only','observed_at':NOW,'operation_sha256':op,'result':'PASS','authorization_coordinate':'synthetic-approval' if k=='human' else None} for k,v in kinds.items()]
    return p,c,{'2'*64}|{digest(e) for e in p['evidence']}


class PhasePlanTests(unittest.TestCase):
    def setUp(self):self.p,self.c,self.verified=fixture()
    def result(self):return evaluate(self.p,self.c,now=NOW,verified_digests=self.verified)
    def denied(self):self.assertEqual(self.result()['status'],'BLOCKED');self.assertFalse(self.result()['deployment_authorized'])
    def test_synthetic_complete_never_authorizes(self):
        from phase_plan import PHASES
        for phase in PHASES:
            p,c,v=fixture(phase);r=evaluate(p,c,now=NOW,verified_digests=v)
            self.assertEqual(r['status'],'COMPLETE',r);self.assertFalse(r['deployment_authorized'])
    def test_human_string_not_authenticated(self):
        self.assertEqual(evaluate(self.p,self.c,now=NOW)['status'],'BLOCKED')
    def test_phase_skip(self):self.p['previous']['state']='NONE';self.denied()
    def test_partial_create_requires_quarantine(self):self.p['previous']['result']='PARTIAL';self.denied()
    def test_wrong_account_and_region(self):
        for k,v in [('account','222222222222'),('region','eu-west-1')]:
            p,c,verified=fixture();p['context'][k]=v
            self.assertEqual(evaluate(p,c,now=NOW,verified_digests=verified)['status'],'BLOCKED')
    def test_wrong_source_parent_and_hashes(self):
        for k in ['source_commit','parent_commit','artifact_sha256','bindings_sha256','capability_sha256']:
            p,c,v=fixture();p['context'][k]='0'*len(c[k]);self.assertEqual(evaluate(p,c,now=NOW,verified_digests=v)['status'],'BLOCKED')
    def test_wrong_template_hash(self):self.p['context']['templates']['ingress']='0'*64;self.denied()
    def test_wrong_s3_version(self):self.p['context']['s3']['version']='changed';self.denied()
    def test_wrong_mutation_scope(self):self.p['resources']=['*'];self.denied()
    def test_stale_evidence(self):self.p['evidence'][0]['observed_at']='2025-12-31T23:59:59Z';self.denied()
    def test_expired_window(self):self.p['expires_at']=NOW;self.denied()
    def test_wrong_evidence_class(self):self.p['evidence'][0]['class']='LOCAL_TEST';self.denied()
    def test_historical_receipt_cannot_transfer(self):self.p['previous']['receipt_sha256']='4'*64;self.denied()
    def test_unresolved_blockers(self):self.p['blockers']=['IAM_UNPROVEN'];self.denied()
    def test_missing_recovery_plan(self):self.p['rollback']['procedure_sha256']=None;self.denied()
    def test_ingress_needs_separate_operation(self):self.p['phase']='TEST_INGRESS';self.denied()
    def test_sandbox_requires_observed_tests(self):
        p,c,v=fixture('SANDBOX');p['evidence']=[e for e in p['evidence'] if e['kind']!='sandbox_observations']
        self.assertEqual(evaluate(p,c,now=NOW,verified_digests=v)['status'],'BLOCKED')
    def test_invalid_expected_context(self):
        for v in [None,{}, {'account':'root'}]:self.assertEqual(evaluate(self.p,v,now=NOW)['status'],'BLOCKED')
    def test_unknown_fields_and_approval_cannot_open(self):self.p['deployment_authorized']=True;self.denied()

    def test_wrong_parameter_set_hash(self):
        self.p['context']['parameters_sha256']['authority']='0'*64;self.denied()
    def test_publication_requires_new_receipt_before_runtime(self):
        self.p['previous']['state']='AUTHORITY';self.denied()
