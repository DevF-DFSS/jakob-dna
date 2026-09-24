"""Deliberately narrow offline allowlist; not IAM evaluation or cfn-lint."""
import json


def check(t):
    r = t['Resources']
    allowed = {'DynamoDB::Table','Logs::LogGroup','IAM::Role','ApiGatewayV2::Api','ApiGatewayV2::Authorizer',
               'Lambda::Function','Lambda::Version','Lambda::Alias','ApiGatewayV2::Integration','ApiGatewayV2::Route',
               'ApiGatewayV2::Deployment','ApiGatewayV2::Stage','Lambda::Permission','CloudWatch::Alarm'}
    assert all(x['Type'].removeprefix('AWS::') in allowed for x in r.values())
    text = json.dumps(t)
    for forbidden in ['DFSS-ColdStart','us-os-brain','DFSS_SessionState','jakob-memory-store','jakob-identity-profiles',
                      'us-os-memory','GEMINI_API_KEY','SECRET_HANDSHAKE_TOKEN','AWS::Lambda::Url','ManagedPolicyArns','ImportValue']:
        assert forbidden not in text, forbidden
    routes = [x['Properties'] for x in r.values() if x['Type']=='AWS::ApiGatewayV2::Route']
    assert {x['RouteKey'] for x in routes} == {'POST /v6/events','GET /v6/senders/{sender}/events/{event_id}'}
    assert len(routes)==2
    for route in routes:
        assert route['AuthorizationType']=='JWT' and route['AuthorizerId']=={'Ref':'Authorizer'}
        assert route['AuthorizationScopes']==['jel-v6/write' if route['RouteKey'].startswith('POST') else 'jel-v6/read']
        assert route['Target']=={'Fn::Sub':'integrations/${Integration}'}
    assert r['Stage']['Properties']['StageName']=='sandbox'
    assert r['Stage']['Properties']['AutoDeploy'] is False
    assert r['Stage']['Properties']['DeploymentId']=={'Ref':'CandidateDeployment'}
    assert r['Integration']['Properties']['IntegrationUri']=={'Ref':'Alias'}
    assert r['Integration']['Properties']['PayloadFormatVersion']=='2.0'
    assert r['Function']['Properties']['Role']=={'Fn::GetAtt':['ExecutionRole','Arn']}
    assert r['Function']['Properties']['Handler']=='aws_v6.host.handler'
    assert r['Function']['Properties']['Runtime']=='python3.13'
    assert r['Function']['Properties']['Environment']['Variables']=={
        'V6_TABLE_NAME':{'Ref':'Events'},'EXPECTED_API_ID':{'Ref':'Api'},'EXPECTED_STAGE':'sandbox',
        'EXPECTED_ISSUER':{'Ref':'JwtIssuer'},'EXPECTED_AUDIENCE':{'Ref':'JwtAudience'},'EXPECTED_REGION':{'Ref':'AWS::Region'}}
    assert set(t['Parameters'])=={'JwtIssuer','JwtAudience','ArtifactBucket','ArtifactKey','ArtifactVersion','ArtifactCodeSha256'}
    assert all('Default' not in p for p in t['Parameters'].values())
    assert r['Authorizer']['Properties']['JwtConfiguration']=={'Issuer':{'Ref':'JwtIssuer'},'Audience':[{'Ref':'JwtAudience'}]}
    assert r['Authorizer']['Properties']['IdentitySource']==['$request.header.Authorization']
    assert r['Alias']['Properties']['FunctionVersion']=={'Fn::GetAtt':['CandidateVersion','Version']}
    assert r['CandidateVersion']['Properties']['CodeSha256']=={'Ref':'ArtifactCodeSha256'}
    assert r['ExecutionRole']['Properties']['AssumeRolePolicyDocument']['Statement']==[
        {'Effect':'Allow','Principal':{'Service':'lambda.amazonaws.com'},'Action':'sts:AssumeRole'}]
    statements = r['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement']
    assert len(r['ExecutionRole']['Properties']['Policies'])==1 and len(statements)==2
    assert statements[0]=={'Effect':'Allow','Action':['dynamodb:PutItem','dynamodb:GetItem'],'Resource':{'Fn::GetAtt':['Events','Arn']}}
    assert statements[1]=={'Effect':'Allow','Action':['logs:CreateLogStream','logs:PutLogEvents'],
        'Resource':{'Fn::Sub':'arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}-v6:log-stream:*'}}
    permissions = [x['Properties'] for x in r.values() if x['Type']=='AWS::Lambda::Permission']
    assert len(permissions)==2
    suffixes = {'POST/v6/events','GET/v6/senders/*/events/*'}
    for permission in permissions:
        assert set(permission)=={'Action','FunctionName','Principal','SourceAccount','SourceArn'}
        assert permission['Action']=='lambda:InvokeFunction' and permission['FunctionName']=={'Ref':'Alias'}
        assert permission['Principal']=='apigateway.amazonaws.com' and permission['SourceAccount']=={'Ref':'AWS::AccountId'}
        prefix='arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${Api}/sandbox/'
        source=permission['SourceArn']['Fn::Sub']
        assert source.startswith(prefix) and source[len(prefix):] in suffixes
        suffixes.remove(source[len(prefix):])
    assert not suffixes
    assert r['Events']['DeletionPolicy']==r['Events']['UpdateReplacePolicy']=='Retain'
    assert r['Events']['Properties']['KeySchema']==[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}]
    # No additional resource with a second policy or invocation grant may bypass the checks.
    assert set(r)=={'Events','FunctionLogs','ExecutionRole','Api','Authorizer','Function','CandidateVersion','Alias',
                   'Integration','PostRoute','GetRoute','CandidateDeployment','Stage','PostPermission','GetPermission','ErrorsAlarm','ThrottleAlarm'}
    return True
