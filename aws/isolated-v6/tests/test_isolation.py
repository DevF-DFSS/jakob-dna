import copy
import json
from pathlib import Path
import re
import unittest
from make_template import template
from isolation_policy import bootstrap, LAMBDA_RESOURCE_ACTIONS
from isolation_security import check_isolation, check_bootstrap
from policy_model import decision
from security import check

ROOT=Path(__file__).resolve().parents[1]
ACCOUNT='111111111111'
REGION='us-east-1'
STACK='jel-v6-sandbox-synthetic'
FUNCTION=f'arn:aws:lambda:{REGION}:{ACCOUNT}:function:{STACK}-v6'
TABLE=f'arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/jel-v6-{STACK}-events'
ROLE=f'arn:aws:iam::{ACCOUNT}:role/jel-v6/{STACK}-v6-execution'
RECOVERY=f'arn:aws:iam::{ACCOUNT}:role/jel-v6-approved/recovery'
DEPLOY=f'arn:aws:iam::{ACCOUNT}:role/synthetic-deploy'
PUBLISHER=f'arn:aws:iam::{ACCOUNT}:role/synthetic-publisher'
BUCKET='arn:aws:s3:::synthetic-new-v6'
BOUNDARY=f'arn:aws:iam::{ACCOUNT}:policy/synthetic-runtime-boundary'
LEGACY=[f'arn:aws:iam::{ACCOUNT}:'+p for p in ['user/us-os-gateway','user/nested/us-os-gateway',
 'role/service-role/DFSS-ColdStart-role-io8kh35x','role/service-role/us-os-brain-role-c7v6jeb1','role/JakobLambdaExecutionRole']]


def resolve(x):
    mapping={'AWS::Partition':'aws','AWS::Region':REGION,'AWS::AccountId':ACCOUNT,'AWS::StackName':STACK,
        'RuntimeStackName':STACK,'BootstrapStackName':'jel-v6-bootstrap-synthetic','Function.Arn':FUNCTION,
        'Function':STACK+'-v6','Alias':FUNCTION+':sandbox','SandboxApi':'syntheticapi','ApprovedRecoveryRoleArn':RECOVERY,
        'Artifacts.Arn':BUCKET,'Artifacts':'synthetic-new-v6','DeploymentRole.Arn':DEPLOY,'PublisherRole.Arn':PUBLISHER,'RuntimeBoundary':BOUNDARY}
    if isinstance(x,list):return [resolve(v) for v in x]
    if not isinstance(x,dict):return x
    if 'Ref' in x:return mapping[x['Ref']]
    if 'Fn::GetAtt' in x:return mapping['.'.join(x['Fn::GetAtt'])]
    if 'Fn::ImportValue' in x:
        name=resolve(x['Fn::ImportValue'])
        return {'jel-v6-bootstrap-synthetic-ApiId':'syntheticapi','jel-v6-bootstrap-synthetic-ArtifactBucket':'synthetic-new-v6',
                'jel-v6-bootstrap-synthetic-RuntimeBoundaryArn':BOUNDARY}[name]
    if 'Fn::Sub' in x:
        v=x['Fn::Sub'];text=v[0] if isinstance(v,list) else v
        replacements={**mapping,**({k:resolve(vv) for k,vv in v[1].items()} if isinstance(v,list) else {})}
        return re.sub(r'\$\{([^}]+)\}',lambda m:replacements[m[1]],text)
    return {k:resolve(v) for k,v in x.items()}


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.t=template();self.b=bootstrap();self.r=self.t['Resources'];self.br=self.b['Resources']
        self.lp=resolve(self.r['FunctionResourcePolicy']['Properties']['PolicyDocument']['Statement'])
        self.dp=resolve(self.r['Events']['Properties']['ResourcePolicy']['PolicyDocument']['Statement'])
        self.sp=resolve(self.br['ArtifactPolicy']['Properties']['PolicyDocument']['Statement'])
    def test_generated_bootstrap_matches(self):
        self.assertEqual(self.b,json.loads((ROOT/'infra/bootstrap.json').read_text()));self.assertTrue(check_bootstrap(self.b))
    def test_only_full_lambda_policy(self):
        types=[v['Type'] for v in self.r.values()]
        self.assertNotIn('AWS::Lambda::Permission',types);self.assertEqual(1,types.count('AWS::Lambda::ResourcePolicy'))
    def test_exact_gateway_routes(self):
        for path in ['POST/v6/events','GET/v6/senders/sender/events/id']:
            ctx={'aws:PrincipalServiceName':'apigateway.amazonaws.com','aws:SourceAccount':ACCOUNT,
                 'aws:SourceArn':f'arn:aws:execute-api:{REGION}:{ACCOUNT}:syntheticapi/sandbox/'+path}
            self.assertEqual('allowed',decision(self.lp,'lambda:InvokeFunction',FUNCTION+':sandbox',ctx))
            self.assertEqual('implicitDeny',decision(self.lp,'lambda:InvokeFunction',FUNCTION+':1',ctx))
    def test_wrong_gateway_account_api_stage_method_path(self):
        good={'aws:PrincipalServiceName':'apigateway.amazonaws.com','aws:SourceAccount':ACCOUNT,
              'aws:SourceArn':f'arn:aws:execute-api:{REGION}:{ACCOUNT}:syntheticapi/sandbox/POST/v6/events'}
        for key,v in [('aws:SourceAccount','222222222222'),('aws:SourceArn',good['aws:SourceArn'].replace('syntheticapi','legacyapi')),
                      ('aws:SourceArn',good['aws:SourceArn'].replace('sandbox','prod')),('aws:SourceArn',good['aws:SourceArn'].replace('POST','DELETE')),
                      ('aws:SourceArn',good['aws:SourceArn']+'/other')]:
            ctx={**good,key:v};self.assertEqual('explicitDeny',decision(self.lp,'lambda:InvokeFunction',FUNCTION+':sandbox',ctx,identity_allow=True))
    def test_legacy_lambda_denied_despite_identity_allow(self):
        for principal in LEGACY:
            for resource in [FUNCTION,FUNCTION+':sandbox',FUNCTION+':1']:
                for action in LAMBDA_RESOURCE_ACTIONS:
                    with self.subTest(principal=principal,action=action):
                        self.assertEqual('explicitDeny',decision(self.lp,action,resource,{'aws:PrincipalArn':principal},identity_allow=True))
    def test_all_direct_invocation_denied(self):
        for principal in [ROLE,DEPLOY,RECOVERY,LEGACY[0]]:
            self.assertEqual('explicitDeny',decision(self.lp,'lambda:InvokeFunction',FUNCTION+':sandbox',{'aws:PrincipalArn':principal},identity_allow=True))
    def test_deployment_recovery_management_not_denied(self):
        for principal in [DEPLOY,RECOVERY]:
            for action in ['lambda:UpdateFunctionCode','lambda:PutResourcePolicy','lambda:DeleteFunction']:
                self.assertEqual('allowed',decision(self.lp,action,FUNCTION,{'aws:PrincipalArn':principal},identity_allow=True))
            self.assertEqual('allowed',decision(self.dp,'dynamodb:UpdateTable',TABLE,{'aws:PrincipalArn':principal},identity_allow=True))
    def test_legacy_table_and_index_denied(self):
        for principal in LEGACY:
            for resource in [TABLE,TABLE+'/index/test']:
                for action in ['dynamodb:GetItem','dynamodb:PutItem','dynamodb:Query','dynamodb:DeleteTable']:
                    self.assertEqual('explicitDeny',decision(self.dp,action,resource,{'aws:PrincipalArn':principal},identity_allow=True))
    def test_runtime_get_put_not_denied(self):
        for action in ['dynamodb:GetItem','dynamodb:PutItem']:
            self.assertEqual('allowed',decision(self.dp,action,TABLE,{'aws:PrincipalArn':ROLE},identity_allow=True))
    def test_runtime_boundary_denies_legacy_even_with_session_allow(self):
        policy=resolve(self.br['RuntimeBoundary']['Properties']['PolicyDocument']['Statement'])
        for resource,action in [(f'arn:aws:dynamodb:{REGION}:{ACCOUNT}:table/'+n,'dynamodb:GetItem') for n in
             ['DFSS_SessionState','jakob-memory-store','jakob-identity-profiles','us-os-memory']]+[(FUNCTION.replace(STACK+'-v6',n),'lambda:InvokeFunction') for n in ['DFSS-ColdStart','us-os-brain']]+[('arn:aws:s3:::jakob-asset-store/x','s3:GetObject')]:
            self.assertEqual('explicitDeny',decision(policy,action,resource,{},identity_allow=True))
        for action in ['dynamodb:PutItem','dynamodb:GetItem']:self.assertEqual('allowed',decision(policy,action,TABLE,{}))
        self.assertEqual('explicitDeny',decision(policy,'dynamodb:DeleteItem',TABLE,{},identity_allow=True))
    def test_deployer_cannot_rewrite_boundaries_or_legacy(self):
        policy=resolve(self.br['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        for action,res in [('iam:CreatePolicyVersion',BOUNDARY),('iam:DeleteRolePermissionsBoundary',ROLE),
                           ('lambda:UpdateFunctionCode',FUNCTION.replace(STACK+'-v6','us-os-brain')),
                           ('apigateway:PATCH',f'arn:aws:apigateway:{REGION}::/apis/kirmld16gb/routes/x')]:
            self.assertNotEqual('allowed',decision(policy,action,res,{}))
        self.assertEqual('allowed',decision(policy,'iam:CreateRole',ROLE,{'iam:PermissionsBoundary':BOUNDARY}))
        self.assertEqual('explicitDeny',decision(policy,'iam:CreateRole',ROLE,{'iam:PermissionsBoundary':'other'},identity_allow=True))
    def test_artifacts_private_versioned_and_retained(self):
        p=self.br['Artifacts']['Properties'];self.assertNotIn('BucketName',p)
        self.assertTrue(all(p['PublicAccessBlockConfiguration'].values()));self.assertEqual('Enabled',p['VersioningConfiguration']['Status'])
        self.assertEqual('Retain',self.br['ArtifactPolicy']['DeletionPolicy'])
    def test_bucket_legacy_denied_and_recovery_not_locked_out(self):
        for principal in LEGACY+[ROLE]:
            self.assertEqual('explicitDeny',decision(self.sp,'s3:GetObject',BUCKET+'/x',{'aws:PrincipalArn':principal},identity_allow=True))
        for principal in [DEPLOY,PUBLISHER,RECOVERY]:
            self.assertEqual('allowed',decision(self.sp,'s3:GetObjectVersion',BUCKET+'/x',{'aws:PrincipalArn':principal,'aws:SecureTransport':'true'},identity_allow=True))
        self.assertEqual('allowed',decision(self.sp,'s3:PutBucketPolicy',BUCKET,{'aws:PrincipalArn':RECOVERY,'aws:SecureTransport':'true'},identity_allow=True))
    def test_missing_principal_and_non_tls_denied(self):
        self.assertEqual('explicitDeny',decision(self.sp,'s3:GetObject',BUCKET+'/x',{},identity_allow=True))
        self.assertEqual('explicitDeny',decision(self.sp,'s3:GetObject',BUCKET+'/x',{'aws:PrincipalArn':RECOVERY,'aws:SecureTransport':'false','aws:PrincipalIsAWSService':'false'},identity_allow=True))
    def test_no_notprincipal_or_legacy_resource_ownership(self):
        self.assertNotIn('NotPrincipal',json.dumps([self.t,self.b]))
        self.assertNotIn('AWS::IAM::User',[v['Type'] for v in self.br.values()])
        for name in ['DFSS-ColdStart','us-os-brain','JakobLambdaExecutionRole']:
            self.assertNotIn(name,json.dumps([r['Properties'].get('RoleName') for r in self.br.values()]))
    def test_denies_are_not_interchangeable_with_allows(self):
        t=copy.deepcopy(self.t);t['Resources']['Events']['Properties']['ResourcePolicy']['PolicyDocument']['Statement'][0]['Effect']='Allow'
        with self.assertRaises(AssertionError):check(t)
    def test_missing_legacy_principal_rejected(self):
        t=copy.deepcopy(self.t);t['Resources']['FunctionResourcePolicy']['Properties']['PolicyDocument']['Statement'][0]['Condition']['ArnLike']['aws:PrincipalArn'].pop()
        with self.assertRaises(AssertionError):check(t)
    def test_extra_permission_mechanism_rejected(self):
        t=copy.deepcopy(self.t);t['Resources']['Bad']={'Type':'AWS::Lambda::Permission','Properties':{}}
        with self.assertRaises(AssertionError):check(t)

    def test_unsupported_lambda_actions_are_not_claimed_protected(self):
        for action in ['lambda:UpdateFunctionConfiguration','lambda:PutResourcePolicy','lambda:DeleteResourcePolicy','lambda:AddPermission','lambda:RemovePermission']:
            self.assertNotIn(action,self.lp[0]['Action'])
            self.assertEqual('allowed',decision(self.lp,action,FUNCTION,{'aws:PrincipalArn':LEGACY[0]},identity_allow=True))
    def test_boundary_cannot_be_bypassed_with_session_allow(self):
        p=resolve(self.br['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        for action,res,ctx in [('iam:DeleteRolePermissionsBoundary',ROLE,{}),('iam:PutRolePermissionsBoundary',ROLE,{}),('iam:PassRole',ROLE,{'iam:PassedToService':'ec2.amazonaws.com'}),('iam:CreateRole',ROLE,{})]:
            self.assertEqual('explicitDeny',decision(p,action,res,ctx,identity_allow=True))
    def test_gateway_deny_tampering_rejected(self):
        for i in range(1,4):
            for key,value in [('Effect','Allow'),('Resource','*'),('Action','lambda:GetFunction')]:
                t=copy.deepcopy(self.t);t['Resources']['FunctionResourcePolicy']['Properties']['PolicyDocument']['Statement'][i][key]=value
                with self.assertRaises(AssertionError):check(t)
    def test_bootstrap_requires_independent_same_account_recovery(self):
        p=self.b['Parameters']['ApprovedRecoveryRoleArn'];self.assertNotIn('Default',p)
        for legacy in LEGACY:self.assertIsNone(re.fullmatch(p['AllowedPattern'],legacy))
        self.assertIsNotNone(re.fullmatch(p['AllowedPattern'],RECOVERY))
        self.assertIn('SameAccountRecovery',self.b['Rules'])
        self.assertEqual({'Version':'2012-10-17','Statement':[{'Effect':'Allow','Principal':{'Service':'cloudformation.amazonaws.com'},'Action':'sts:AssumeRole'}]},self.br['DeploymentRole']['Properties']['AssumeRolePolicyDocument'])

    def test_managed_policy_size_at_maximum_candidate_names(self):
        # IAM managed policy limit excludes whitespace. Account/region are synthetic.
        for name in ['RuntimeBoundary','DeploymentBoundary','PublisherBoundary']:
            raw=json.dumps(resolve(self.br[name]['Properties']['PolicyDocument']),separators=(',',':'))
            raw=raw.replace(REGION,'ap-southeast-7').replace(STACK,'jel-v6-sandbox-'+'x'*24).replace(BOUNDARY,'arn:aws:iam::111111111111:policy/jel-v6-sandbox-'+'x'*24+'-runtime-boundary').replace(BUCKET,'arn:aws:s3:::'+'x'*63)
            self.assertLessEqual(len(raw),6144,name)
    def test_deployment_and_publisher_required_paths(self):
        d=resolve(self.br['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        for action,res,ctx in [('lambda:PutResourcePolicy',FUNCTION,{}),('lambda:AddPermission',FUNCTION,{}),('lambda:RemovePermission',FUNCTION,{}),('s3:GetObjectVersion',BUCKET+'/candidate.zip',{}),('iam:PassRole',ROLE,{'iam:PassedToService':'lambda.amazonaws.com'})]:
            self.assertEqual('allowed',decision(d,action,res,ctx))
        p=resolve(self.br['PublisherBoundary']['Properties']['PolicyDocument']['Statement'])
        self.assertEqual('allowed',decision(p,'s3:PutObject',BUCKET+'/candidate.zip',{}))
        for action in ['s3:PutBucketPolicy','s3:DeleteObject','iam:PassRole']:
            self.assertEqual('explicitDeny',decision(p,action,BUCKET,{},identity_allow=True))
