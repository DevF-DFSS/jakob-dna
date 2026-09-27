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
        for action,res in [('apigateway:PATCH',API+'/routes/r'),('apigateway:DELETE',API),('apigateway:POST',API+'/integrations'),('iam:PassRole',ROLE),('iam:PutRolePolicy',ROLE),('lambda:UpdateFunctionConfiguration',FUNCTION),('lambda:PutResourcePolicy',FUNCTION)]:
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
