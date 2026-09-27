"""Structural phase assertions; not effective IAM or approval verification."""
import json
from phase_templates import templates, source_revision


def check_phases(candidate):
    docs={k:json.loads((candidate/'infra/phases'/f'{k}.json').read_text()) for k in ['bootstrap','authority','runtime','ingress']}
    check_documents(docs)
    assert docs==templates(source_revision(candidate)), 'generated_phase_templates_drift'
    return {'passed':True,'deployment_authorized':False,'composition':'infra/phases','limits':'LOCAL_STATIC_ANALYSIS only'}


def check_documents(d):
    b,a,r,i=(d[k]['Resources'] for k in ['bootstrap','authority','runtime','ingress'])
    assert set(b)=={'SandboxApi','Artifacts','ArtifactPolicy'}
    assert set(b['SandboxApi']['Properties'])=={'Name','ProtocolType'} # No Quick Create Target/RouteKey.
    assert b['SandboxApi']['Properties']['ProtocolType']=='HTTP'
    assert b['Artifacts']['DeletionPolicy']==b['Artifacts']['UpdateReplacePolicy']=='Retain'
    assert b['Artifacts']['Properties']['VersioningConfiguration']=={'Status':'Enabled'}
    assert all(b['Artifacts']['Properties']['PublicAccessBlockConfiguration'].values())
    assert all(v['Type'] in ['AWS::IAM::ManagedPolicy','AWS::IAM::Role'] for v in a.values())
    assert not any(v['Type'].startswith('AWS::ApiGateway') for v in r.values())
    assert all(v['Type'].startswith('AWS::ApiGatewayV2::') for v in i.values())
    assert all(v['Type']!='AWS::Lambda::Permission' and v['Type']!='AWS::Lambda::Url' for t in d.values() for v in t['Resources'].values())
    assert sum(v['Type']=='AWS::Lambda::ResourcePolicy' for t in d.values() for v in t['Resources'].values())==1
    assert r['Function']['Properties']['Handler']=='aws_v6.phase_host.handler'
    assert 'ReservedConcurrentExecutions' not in r['Function']['Properties']
    assert r['Events']['DeletionPolicy']==r['Events']['UpdateReplacePolicy']=='Retain'
    data=r['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'][0]
    assert set(data['Action'])=={'dynamodb:GetItem','dynamodb:PutItem'}
    assert data['Condition']=={'ArnEquals':{'lambda:SourceFunctionArn':{'Fn::Sub':'arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${AWS::StackName}-v6'}}}
    maximum=a['RuntimeBoundary']['Properties']['PolicyDocument']['Statement']
    assert any(s.get('Condition',{}).get('ArnNotEquals',{}).get('lambda:SourceFunctionArn') for s in maximum if s['Effect']=='Deny')
    deploy=a['DeploymentRole']['Properties']['Policies'][0]['PolicyDocument']['Statement']
    assert 'apigateway:' not in json.dumps(deploy)
    passing=[s for s in deploy if s['Action']=='iam:PassRole'];assert len(passing)==1
    assert passing[0]['Condition']['StringEquals']=={'iam:PassedToService':'lambda.amazonaws.com'}
    assert passing[0]['Condition']['ArnEquals']['iam:AssociatedResourceArn']=={'Fn::Sub':'arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${RuntimeStackName}-v6'}
    routes=[v['Properties'] for v in i.values() if v['Type']=='AWS::ApiGatewayV2::Route']
    assert {p['RouteKey'] for p in routes}=={'POST /v6/events','GET /v6/senders/{sender}/events/{event_id}'}
    for p in routes:
        assert p['AuthorizationType']=='JWT'
        assert p['AuthorizationScopes']==['jel-v6/write' if p['RouteKey'].startswith('POST') else 'jel-v6/read']
    stage=i['Stage']['Properties']
    assert stage['StageName']=='sandbox' and stage['AutoDeploy'] is False
    assert stage['DefaultRouteSettings']=={'ThrottlingBurstLimit':2,'ThrottlingRateLimit':1}
    assert 'Fn::ImportValue' in i['Integration']['Properties']['IntegrationUri']
    for name in ['DeploymentBoundary','IngressBoundary','PublisherBoundary']:
        assert any('DateGreaterThanEquals' in s.get('Condition',{}) for s in a[name]['Properties']['PolicyDocument']['Statement'] if s['Effect']=='Deny')
    # No operational signals silently removed by splitting the HTTP API resources.
    assert {'RejectedMetric','UnavailableMetric','RejectedAlarm','UnavailableAlarm','Gateway4xxAlarm','ErrorsAlarm','ThrottleAlarm'}<=set(r)
    def allow_text(v):
        if isinstance(v,dict):return {} if v.get('Effect')=='Deny' else {k:allow_text(x) for k,x in v.items()}
        if isinstance(v,list):return [allow_text(x) for x in v]
        return v
    text=json.dumps(allow_text(d))
    for legacy in ['DFSS-ColdStart','us-os-brain','JakobLambdaExecutionRole','us-os-gateway','kirmld16gb','qjiuor3yak','p9qtqpd8mc']:
        assert legacy not in text
