import unittest
from phase_policy import source_bound_data, source_data_deny, associated_pass, pass_denies, legacy_fence, maximum, timed
from policy_model import decision

FUNCTION='arn:aws:lambda:us-east-1:111111111111:function:jel-v6-sandbox-test-v6'
TABLE='arn:aws:dynamodb:us-east-1:111111111111:table/jel-v6-jel-v6-sandbox-test-events'
ROLE='arn:aws:iam::111111111111:role/jel-v6/jel-v6-sandbox-test-v6-execution'
API='arn:aws:apigateway:us-east-1::/apis/syntheticapi'

class AuthorityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.data=[source_bound_data(TABLE,FUNCTION),source_data_deny(FUNCTION)]
        self.passing=[associated_pass(ROLE,FUNCTION),*pass_denies(ROLE,FUNCTION)]
        self.good={'lambda:SourceFunctionArn':FUNCTION}
        self.assoc={'iam:PassedToService':'lambda.amazonaws.com','iam:AssociatedResourceArn':FUNCTION}
    def test_intended_function_get_put(self):
        for a in ['dynamodb:GetItem','dynamodb:PutItem']:
            self.assertEqual('allowed',decision(self.data,a,TABLE,self.good))
    def test_alternate_lambda_same_role(self):
        for a in ['dynamodb:GetItem','dynamodb:PutItem']:
            self.assertEqual('explicitDeny',decision(self.data,a,TABLE,{'lambda:SourceFunctionArn':FUNCTION+'other'},identity_allow=True))
    def test_direct_credentials_missing_source(self):
        self.assertEqual('explicitDeny',decision(self.data,'dynamodb:GetItem',TABLE,{},identity_allow=True))
    def test_qualified_source_is_not_unqualified(self):
        for suffix in [':sandbox',':1',':$LATEST']:
            self.assertEqual('explicitDeny',decision(self.data,'dynamodb:GetItem',TABLE,{'lambda:SourceFunctionArn':FUNCTION+suffix},identity_allow=True))
    def test_other_table_not_granted(self):
        self.assertEqual('implicitDeny',decision(self.data,'dynamodb:GetItem',TABLE+'other',self.good))
    def test_correct_pass(self):
        self.assertEqual('allowed',decision(self.passing,'iam:PassRole',ROLE,self.assoc))
    def test_wrong_pass_service(self):
        for service in ['ec2.amazonaws.com','cloudformation.amazonaws.com','']:
            self.assertEqual('explicitDeny',decision(self.passing,'iam:PassRole',ROLE,{**self.assoc,'iam:PassedToService':service},identity_allow=True))
    def test_wrong_or_qualified_association(self):
        for fn in [FUNCTION+'other',FUNCTION+':sandbox',FUNCTION+':1']:
            self.assertEqual('explicitDeny',decision(self.passing,'iam:PassRole',ROLE,{**self.assoc,'iam:AssociatedResourceArn':fn},identity_allow=True))
    def test_missing_pass_context(self):
        for c in [{},{'iam:PassedToService':'lambda.amazonaws.com'},{'iam:AssociatedResourceArn':FUNCTION}]:
            self.assertEqual('explicitDeny',decision(self.passing,'iam:PassRole',ROLE,c,identity_allow=True))
    def test_other_role_not_granted(self):
        self.assertEqual('implicitDeny',decision(self.passing,'iam:PassRole',ROLE+'other',self.assoc))
    def test_policy_mutation_cannot_bypass_source_boundary(self):
        self.assertEqual('explicitDeny',decision([source_data_deny(FUNCTION)],'dynamodb:PutItem',TABLE,{},identity_allow=True))
    def test_logging_not_subject_to_ddb_deny(self):
        self.assertEqual('allowed',decision([source_data_deny(FUNCTION)],'logs:PutLogEvents','synthetic-log',{},identity_allow=True))
    def test_intended_credentials_context_not_code_attestation(self):
        # A stolen intended-function context is deliberately NOT claimed blocked.
        self.assertEqual('allowed',decision(self.data,'dynamodb:GetItem',TABLE,self.good))
    def test_legacy_fence_gateway_and_role_reuse(self):
        p=legacy_fence(function=FUNCTION,table=TABLE,roles=[ROLE],boundaries=['synthetic-boundary'],api=API,bucket='arn:aws:s3:::synthetic',stacks=['synthetic-stack'])['Statement']
        for action,res in [('apigateway:PATCH',API+'/routes/r'),('apigateway:DELETE',API),('apigateway:POST',API+'/integrations'),('iam:PassRole',ROLE),('sts:AssumeRole',ROLE),('iam:PutRolePolicy',ROLE),('lambda:UpdateFunctionConfiguration',FUNCTION),('lambda:PutResourcePolicy',FUNCTION)]:
            self.assertEqual('explicitDeny',decision(p,action,res,{},identity_allow=True))
        self.assertEqual('allowed',decision(p,'apigateway:PATCH',API.replace('syntheticapi','legacyapi')+'/routes/r',{},identity_allow=True))
    def test_unknown_api_cannot_render_fence(self):
        for api in ['',API+'*',API.rsplit('/',1)[0]+'/']:
            with self.assertRaises(ValueError):legacy_fence(function=FUNCTION,table=TABLE,roles=[ROLE],boundaries=[],api=api,bucket='b',stacks=[])
    def test_expired_authority_denied_with_session_allow(self):
        p=timed(maximum([{'Effect':'Allow','Action':'s3:PutObject','Resource':'synthetic-object'}]),'2026-01-01T00:00:00Z','2026-01-01T01:00:00Z')['Statement']
        for now in ['2025-12-31T23:59:59Z','2026-01-01T01:00:00Z','2026-02-01T00:00:00Z']:
            self.assertEqual('explicitDeny',decision(p,'s3:PutObject','synthetic-object',{'aws:CurrentTime':now},identity_allow=True))
        self.assertEqual('allowed',decision(p,'s3:PutObject','synthetic-object',{'aws:CurrentTime':'2026-01-01T00:30:00Z'}))
        self.assertEqual('explicitDeny',decision(p,'s3:PutObject','synthetic-object',{},identity_allow=True))
    def test_long_or_unzoned_window_rejected(self):
        for a,b in [('2026-01-01T00:00:00Z','2026-01-02T00:00:00Z'),('2026-01-01T00:00:00','2026-01-01T01:00:00')]:
            with self.assertRaises(ValueError):timed(maximum([]),a,b)

class TopologyTests(unittest.TestCase):
    def setUp(self):
        from authority_topology import topology
        self.c={'account':'111111111111','region':'us-east-1','namespace':'synthetic',
            'stacks':{'bootstrap':'jel-v6-bootstrap-test','authority':'jel-v6-authority-test','runtime':'jel-v6-sandbox-test','ingress':'jel-v6-ingress-test'},
            'trusted_operator':'arn:aws:iam::111111111111:role/jel-v6-approved/external-federated',
            'starts_at':'2026-01-01T00:00:00Z','expires_at':'2026-01-01T01:00:00Z'}
        self.t=topology(self.c);self.ctx={'aws:CurrentTime':'2026-01-01T00:30:00Z'}
    def test_nonroot_explicit_trust(self):
        from authority_topology import topology
        for actor in ['arn:aws:iam::111111111111:root','arn:aws:iam::111111111111:user/us-os-gateway','arn:aws:iam::222222222222:role/jel-v6-approved/operator']:
            with self.assertRaises(ValueError):topology({**self.c,'trusted_operator':actor})
    def test_runtime_operator_cannot_activate_or_change_bootstrap(self):
        p=self.t['roles']['runtime-operator']['maximum_boundary']['Statement']
        for stack in ['jel-v6-ingress-test','jel-v6-bootstrap-test','jel-v6-authority-test']:
            self.assertEqual('explicitDeny',decision(p,'cloudformation:UpdateStack',f'arn:aws:cloudformation:us-east-1:111111111111:stack/{stack}/id',self.ctx,identity_allow=True))
    def test_recovery_cannot_become_admin(self):
        for name in ['recovery-operator','emergency-operator']:
            p=self.t['roles'][name]['maximum_boundary']['Statement']
            for action in ['iam:PutRolePolicy','iam:CreatePolicyVersion','sts:AssumeRole','lambda:InvokeFunction']:
                self.assertEqual('explicitDeny',decision(p,action,ROLE,self.ctx,identity_allow=True))
    def test_publisher_cannot_deploy_or_change_policy(self):
        p=self.t['roles']['publisher-operator']['maximum_boundary']['Statement']
        for action in ['cloudformation:CreateStack','iam:PassRole','s3:PutBucketPolicy']:
            self.assertEqual('explicitDeny',decision(p,action,'anything',self.ctx,identity_allow=True))
    def test_bootstrap_cannot_leave_inert_state(self):
        p=self.t['roles']['bootstrap-service']['maximum_boundary']['Statement']
        for action,res in [('apigateway:POST',API+'/stages'),('iam:CreateRole',ROLE),('lambda:CreateFunction',FUNCTION),('dynamodb:PutItem',TABLE)]:
            self.assertEqual('explicitDeny',decision(p,action,res,self.ctx,identity_allow=True))
    def test_bootstrap_expired_even_if_grant_left_attached(self):
        p=self.t['roles']['bootstrap-service']['maximum_boundary']['Statement']
        self.assertEqual('explicitDeny',decision(p,'apigateway:POST','arn:aws:apigateway:us-east-1::/apis',{'aws:CurrentTime':'2026-01-01T01:00:00Z'},identity_allow=True))
    def test_operator_requires_exact_service_role(self):
        p=self.t['roles']['runtime-operator']['maximum_boundary']['Statement']
        stack='arn:aws:cloudformation:us-east-1:111111111111:stack/jel-v6-sandbox-test/id'
        role=self.t['service_role_arns']['runtime']
        self.assertEqual('allowed',decision(p,'cloudformation:CreateStack',stack,{**self.ctx,'cloudformation:RoleArn':role}))
        self.assertEqual('explicitDeny',decision(p,'cloudformation:CreateStack',stack,self.ctx,identity_allow=True))
    def test_no_authorization_from_rendered_roles(self):
        self.assertFalse(self.t['deployment_authorized']);self.assertFalse(self.t['live_gates_closed'])
        self.assertFalse(self.t['installation_prerequisite']['normal_root_use'])
