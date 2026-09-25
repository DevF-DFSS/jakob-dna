"""Deliberately narrow offline allowlist; not IAM evaluation or cfn-lint."""
import json
from isolation_policy import imported
from isolation_security import check_isolation


def check(t):
    check_isolation(t)
    r = t['Resources']
    allowed = {'DynamoDB::Table','Logs::LogGroup','Logs::MetricFilter','IAM::Role','ApiGatewayV2::Api','ApiGatewayV2::Authorizer',
               'Lambda::Function','Lambda::Version','Lambda::Alias','ApiGatewayV2::Integration','ApiGatewayV2::Route',
               'ApiGatewayV2::Deployment','ApiGatewayV2::Stage','Lambda::ResourcePolicy','IAM::ManagedPolicy','CloudWatch::Alarm'}
    assert all(x['Type'].removeprefix('AWS::') in allowed for x in r.values())
    def without_denies(x):
        if isinstance(x,dict):
            if x.get('Effect')=='Deny':return {}
            return {k:without_denies(v) for k,v in x.items()}
        if isinstance(x,list):return [without_denies(v) for v in x]
        return x
    text = json.dumps(without_denies(t))
    for forbidden in ['DFSS-ColdStart','us-os-brain','DFSS_SessionState','jakob-memory-store','jakob-identity-profiles',
                      'us-os-memory','kirmld16gb','qjiuor3yak','p9qtqpd8mc','JakobLambdaExecutionRole','GEMINI_API_KEY','SECRET_HANDSHAKE_TOKEN','AWS::Lambda::Url','ManagedPolicyArns']:
        assert forbidden not in text, forbidden
    routes = [x['Properties'] for x in r.values() if x['Type']=='AWS::ApiGatewayV2::Route']
    assert {x['RouteKey'] for x in routes} == {'POST /v6/events','GET /v6/senders/{sender}/events/{event_id}'}
    assert len(routes)==2
    for route in routes:
        assert route['AuthorizationType']=='JWT' and route['AuthorizerId']=={'Ref':'Authorizer'}
        assert route['AuthorizationScopes']==['jel-v6/write' if route['RouteKey'].startswith('POST') else 'jel-v6/read']
        assert route['Target']=={'Fn::Sub':'integrations/${Integration}'}
    assert 'ReservedConcurrentExecutions' not in r['Function']['Properties']
    assert r['Stage']['Properties']['DefaultRouteSettings']=={'ThrottlingBurstLimit':2,'ThrottlingRateLimit':1}
    assert 'RouteSettings' not in r['Stage']['Properties']
    assert r['Stage']['Properties']['StageName']=='sandbox'
    assert r['Stage']['Properties']['AutoDeploy'] is False
    assert r['Stage']['Properties']['DeploymentId']=={'Ref':'CandidateDeployment'}
    assert r['Integration']['Properties']['IntegrationUri']=={'Ref':'Alias'}
    assert r['Integration']['Properties']['PayloadFormatVersion']=='2.0'
    assert r['Function']['Properties']['Role']=={'Fn::GetAtt':['ExecutionRole','Arn']}
    assert r['Function']['Properties']['Handler']=='aws_v6.activation.handler'
    assert r['Function']['Properties']['Runtime']=='python3.13'
    assert r['Function']['Properties']['Environment']['Variables']=={
        'V6_TABLE_NAME':{'Ref':'Events'},'EXPECTED_API_ID':imported('ApiId'),'EXPECTED_STAGE':'sandbox',
        'EXPECTED_ISSUER':{'Ref':'JwtIssuer'},'EXPECTED_AUDIENCE':{'Ref':'JwtAudience'},'EXPECTED_REGION':{'Ref':'AWS::Region'},
        'EXPECTED_CLIENT_IDS':{'Ref':'ClientIdsJson'},'BINDINGS_VERSION':{'Ref':'BindingsVersion'},
        'BINDINGS_SHA256':{'Ref':'BindingsSha256'},
        'EXPECTED_ALIAS_ARN':{'Fn::Sub':'arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${AWS::StackName}-v6:sandbox'}}
    assert set(t['Parameters'])=={'ClientIdsJson','BindingsVersion','BindingsSha256','JwtIssuer','JwtAudience','BootstrapStackName','ArtifactKey','ArtifactVersion','ArtifactCodeSha256'}
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
    assert r['Events']['DeletionPolicy']==r['Events']['UpdateReplacePolicy']=='Retain'
    assert r['Events']['Properties']['KeySchema']==[{'AttributeName':'PK','KeyType':'HASH'},{'AttributeName':'SK','KeyType':'RANGE'}]
    # No additional resource with a second policy or invocation grant may bypass the checks.
    assert set(r)=={'Events','FunctionLogs','ExecutionRole','FunctionResourcePolicy','Authorizer','Function','CandidateVersion','Alias',
                   'Integration','PostRoute','GetRoute','CandidateDeployment','Stage','ErrorsAlarm','ThrottleAlarm','RejectedMetric','UnavailableMetric','RejectedAlarm','UnavailableAlarm','Gateway4xxAlarm'}
    for outcome in ['rejected','unavailable']:
        name=outcome.title()
        assert r[name+'Metric']['Properties']=={
            'LogGroupName':{'Ref':'FunctionLogs'},
            'FilterPattern':'{ $.kind = "v6_outcome" && $.outcome = "'+outcome+'" }',
            'MetricTransformations':[{'MetricNamespace':'JELV6/Sandbox','MetricName':{'Fn::Sub':'${AWS::StackName}-'+outcome},'MetricValue':'1','DefaultValue':0}]}
        alarm=r[name+'Alarm']['Properties']
        assert alarm['Namespace']=='JELV6/Sandbox'
        assert alarm['MetricName']=={'Fn::Sub':'${AWS::StackName}-'+outcome}
    assert r['FunctionLogs']['Properties']['RetentionInDays']==30
    return True
