from copy import deepcopy
import json
from pathlib import Path
import re
import unittest
from phase_templates import templates,source_revision
from phase_security import check_documents,check_phases
from policy_model import decision

ROOT=Path(__file__).resolve().parents[1]


def resolved(v):
    variables={'AWS::Partition':'aws','AWS::Region':'us-east-1','AWS::AccountId':'111111111111',
               'RuntimeStackName':'jel-v6-sandbox-test','AWS::StackName':'jel-v6-sandbox-test',
               'BootstrapStackName':'jel-v6-bootstrap-test','ServiceAuthorityExpiresAt':'2026-01-01T01:00:00Z'}
    if isinstance(v,dict):
        if 'Fn::ImportValue' in v:return 'syntheticapi'
        if 'Ref' in v:return variables.get(v['Ref'],'arn:aws:iam::111111111111:policy/synthetic-boundary')
        if 'Fn::Sub' in v:
            sub=v['Fn::Sub'];text=sub[0] if isinstance(sub,list) else sub
            values={**variables,**({k:resolved(x) for k,x in sub[1].items()} if isinstance(sub,list) else {})}
            return re.sub(r'\$\{([^}]+)\}',lambda m:values.get(m[1],m[1]),text)
        return {k:resolved(x) for k,x in v.items()}
    if isinstance(v,list):return [resolved(x) for x in v]
    return v


class PhaseTemplateTests(unittest.TestCase):
    def setUp(self):self.d=templates(source_revision(ROOT))
    def test_generated_bundle_matches_checked_sources(self):self.assertTrue(check_phases(ROOT)['passed'])
    def test_inert_bootstrap_and_no_quick_create(self):
        self.d['bootstrap']['Resources']['SandboxApi']['Properties']['Target']='synthetic-lambda'
        with self.assertRaises(AssertionError):check_documents(self.d)
    def test_runtime_has_no_ingress(self):
        self.d['runtime']['Resources']['Stage']=self.d['ingress']['Resources']['Stage']
        with self.assertRaises(AssertionError):check_documents(self.d)
    def test_resource_policy_only(self):
        self.d['runtime']['Resources']['Extra']={'Type':'AWS::Lambda::Permission'}
        with self.assertRaises(AssertionError):check_documents(self.d)
    def test_source_condition_cannot_disappear(self):
        del self.d['runtime']['Resources']['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'][0]['Condition']
        with self.assertRaises((AssertionError,KeyError)):check_documents(self.d)
    def test_route_auth_cannot_be_disabled(self):
        self.d['ingress']['Resources']['PostRoute']['Properties']['AuthorizationType']='NONE'
        with self.assertRaises(AssertionError):check_documents(self.d)
    def test_deployer_cannot_manage_api_or_bootstrap_boundaries(self):
        p=resolved(self.d['authority']['Resources']['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        for action,resource in [('apigateway:POST','arn:aws:apigateway:us-east-1::/apis/syntheticapi/stages'),('iam:CreatePolicyVersion','arn:aws:iam::111111111111:policy/synthetic-boundary'),('lambda:InvokeFunction','arn:aws:lambda:us-east-1:111111111111:function:jel-v6-sandbox-test-v6')]:
            self.assertEqual(decision(p,action,resource,{'aws:CurrentTime':'2026-01-01T00:30:00Z'},identity_allow=True),'explicitDeny')
    def test_actual_source_boundary_blocks_alternate_and_absent(self):
        p=resolved(self.d['authority']['Resources']['RuntimeBoundary']['Properties']['PolicyDocument']['Statement'])
        table='arn:aws:dynamodb:us-east-1:111111111111:table/jel-v6-jel-v6-sandbox-test-events'
        fn='arn:aws:lambda:us-east-1:111111111111:function:jel-v6-sandbox-test-v6'
        for source in [None,fn+'other',fn+':1']:
            self.assertEqual(decision(p,'dynamodb:PutItem',table,{'lambda:SourceFunctionArn':source},identity_allow=True),'explicitDeny')
        self.assertEqual(decision(p,'dynamodb:PutItem',table,{'lambda:SourceFunctionArn':fn}),'allowed')
    def test_actual_passrole_requires_exact_context(self):
        p=resolved(self.d['authority']['Resources']['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        role='arn:aws:iam::111111111111:role/jel-v6/jel-v6-sandbox-test-v6-execution'
        c={'aws:CurrentTime':'2026-01-01T00:30:00Z','iam:PassedToService':'lambda.amazonaws.com','iam:AssociatedResourceArn':'arn:aws:lambda:us-east-1:111111111111:function:jel-v6-sandbox-test-v6'}
        self.assertEqual(decision(p,'iam:PassRole',role,c),'allowed')
        c['iam:AssociatedResourceArn']+='other';self.assertEqual(decision(p,'iam:PassRole',role,c,identity_allow=True),'explicitDeny')
    def test_service_role_expires_even_with_extra_allow(self):
        p=resolved(self.d['authority']['Resources']['DeploymentBoundary']['Properties']['PolicyDocument']['Statement'])
        self.assertEqual(decision(p,'lambda:UpdateFunctionCode','anything',{'aws:CurrentTime':'2026-01-01T01:00:00Z'},identity_allow=True),'explicitDeny')
    def test_dependency_order_has_no_backward_import(self):
        for phase,forbidden in [('bootstrap',['AuthorityStackName','Fn::ImportValue']),('authority',['Fn::GetAtt": ["Function']),('runtime',['IngressStackName'])]:
            for word in forbidden:self.assertNotIn(word,json.dumps(self.d[phase]))
    def test_revision_changes_immutable_version_and_deployment(self):
        other=templates('1'*64)
        for phase,kind in [('runtime','AWS::Lambda::Version'),('ingress','AWS::ApiGatewayV2::Deployment')]:
            ids=lambda d:{k for k,v in d[phase]['Resources'].items() if v['Type']==kind}
            self.assertNotEqual(ids(self.d),ids(other))
    def test_data_and_artifact_retention_survives_split(self):
        for phase,name in [('bootstrap','Artifacts'),('bootstrap','ArtifactPolicy'),('runtime','Events')]:
            self.assertEqual(self.d[phase]['Resources'][name]['DeletionPolicy'],'Retain')
    def test_actual_ingress_role_cannot_mutate_lambda_or_api_root(self):
        p=resolved(self.d['authority']['Resources']['IngressBoundary']['Properties']['PolicyDocument']['Statement'])
        for action,resource in [('lambda:UpdateFunctionCode','x'),('apigateway:DELETE','arn:aws:apigateway:us-east-1::/apis/syntheticapi')]:
            self.assertEqual(decision(p,action,resource,{'aws:CurrentTime':'2026-01-01T00:30:00Z'},identity_allow=True),'explicitDeny')
