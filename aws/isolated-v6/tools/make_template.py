"""Offline template source generator; never calls AWS."""
import json
from pathlib import Path


def ref(name): return {'Ref': name}
def sub(text): return {'Fn::Sub': text}
def arn(name): return {'Fn::GetAtt': [name, 'Arn']}
def resource(kind, **properties): return {'Type': 'AWS::' + kind, 'Properties': properties}


def template():
    params = {
        'JwtIssuer': {'Type': 'String', 'AllowedPattern': 'https://.+', 'Description': 'Approved issuer; no provider provisioned'},
        'JwtAudience': {'Type': 'String', 'MinLength': 1},
        'ClientIdsJson': {'Type': 'String', 'MinLength': 3, 'Description': 'Approved nonempty JSON array of client IDs'},
        'BindingsVersion': {'Type': 'String', 'AllowedPattern': '[A-Za-z0-9_.-]{1,64}'},
        'BindingsSha256': {'Type': 'String', 'AllowedPattern': '[0-9a-f]{64}'},
        'ArtifactBucket': {'Type': 'String', 'MinLength': 3},
        'ArtifactKey': {'Type': 'String', 'MinLength': 1},
        'ArtifactVersion': {'Type': 'String', 'MinLength': 1},
        'ArtifactCodeSha256': {'Type': 'String', 'AllowedPattern': '[A-Za-z0-9+/]{43}='},
    }
    r = {}
    r['Events'] = resource('DynamoDB::Table', TableName=sub('jel-v6-${AWS::StackName}-events'), BillingMode='PAY_PER_REQUEST',
        AttributeDefinitions=[{'AttributeName': k, 'AttributeType': 'S'} for k in ('PK','SK')],
        KeySchema=[{'AttributeName': 'PK','KeyType': 'HASH'}, {'AttributeName': 'SK','KeyType': 'RANGE'}],
        PointInTimeRecoverySpecification={'PointInTimeRecoveryEnabled': True},
        SSESpecification={'SSEEnabled': True}, DeletionProtectionEnabled=True)
    r['Events'].update(DeletionPolicy='Retain', UpdateReplacePolicy='Retain')
    r['FunctionLogs'] = resource('Logs::LogGroup', LogGroupName=sub('/aws/lambda/${AWS::StackName}-v6'), RetentionInDays=30)
    r['FunctionLogs'].update(DeletionPolicy='Retain', UpdateReplacePolicy='Retain')
    r['ExecutionRole'] = resource('IAM::Role', AssumeRolePolicyDocument={'Version':'2012-10-17','Statement':[
        {'Effect':'Allow','Principal':{'Service':'lambda.amazonaws.com'},'Action':'sts:AssumeRole'}]},
        Policies=[{'PolicyName':'IsolatedEventsAndLogs','PolicyDocument':{'Version':'2012-10-17','Statement':[
            {'Effect':'Allow','Action':['dynamodb:PutItem','dynamodb:GetItem'],'Resource':arn('Events')},
            {'Effect':'Allow','Action':['logs:CreateLogStream','logs:PutLogEvents'],
             'Resource':sub('arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}-v6:log-stream:*')}
        ]}}])
    r['Api'] = resource('ApiGatewayV2::Api', Name=sub('${AWS::StackName}-v6'), ProtocolType='HTTP')
    r['Authorizer'] = resource('ApiGatewayV2::Authorizer', ApiId=ref('Api'), Name='V6Jwt', AuthorizerType='JWT',
        IdentitySource=['$request.header.Authorization'], JwtConfiguration={'Issuer':ref('JwtIssuer'),'Audience':[ref('JwtAudience')]})
    r['Function'] = resource('Lambda::Function', FunctionName=sub('${AWS::StackName}-v6'), Runtime='python3.13',
        Architectures=['x86_64'], Handler='aws_v6.activation.handler', Role=arn('ExecutionRole'), Timeout=10, MemorySize=256,
        
        Code={'S3Bucket':ref('ArtifactBucket'),'S3Key':ref('ArtifactKey'),'S3ObjectVersion':ref('ArtifactVersion')},
        Environment={'Variables':{'V6_TABLE_NAME':ref('Events'),'EXPECTED_API_ID':ref('Api'),'EXPECTED_STAGE':'sandbox',
            'EXPECTED_ISSUER':ref('JwtIssuer'),'EXPECTED_AUDIENCE':ref('JwtAudience'),'EXPECTED_REGION':ref('AWS::Region'),
            'EXPECTED_CLIENT_IDS':ref('ClientIdsJson'),'BINDINGS_VERSION':ref('BindingsVersion'),
            'BINDINGS_SHA256':ref('BindingsSha256'),
            'EXPECTED_ALIAS_ARN':sub('arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${AWS::StackName}-v6:sandbox')}})
    r['Function']['DependsOn'] = ['FunctionLogs']
    r['CandidateVersion'] = resource('Lambda::Version', FunctionName=ref('Function'), CodeSha256=ref('ArtifactCodeSha256'), Description='Offline candidate; reviewed packaged registry required')
    r['Alias'] = resource('Lambda::Alias', Name='sandbox', FunctionName=ref('Function'), FunctionVersion={'Fn::GetAtt':['CandidateVersion','Version']})
    r['Integration'] = resource('ApiGatewayV2::Integration', ApiId=ref('Api'), IntegrationType='AWS_PROXY', IntegrationMethod='POST',
        IntegrationUri=ref('Alias'), PayloadFormatVersion='2.0', TimeoutInMillis=10000)
    for name, route, scope in [('PostRoute','POST /v6/events','jel-v6/write'), ('GetRoute','GET /v6/senders/{sender}/events/{event_id}','jel-v6/read')]:
        r[name] = resource('ApiGatewayV2::Route', ApiId=ref('Api'), RouteKey=route, AuthorizationType='JWT', AuthorizerId=ref('Authorizer'), AuthorizationScopes=[scope], Target=sub('integrations/${Integration}'))
    r['CandidateDeployment'] = resource('ApiGatewayV2::Deployment', ApiId=ref('Api'), Description='Explicit reviewed sandbox snapshot')
    r['CandidateDeployment']['DependsOn'] = ['PostRoute','GetRoute']
    r['Stage'] = resource('ApiGatewayV2::Stage', ApiId=ref('Api'), StageName='sandbox', AutoDeploy=False, DeploymentId=ref('CandidateDeployment'), DefaultRouteSettings={'ThrottlingBurstLimit':2,'ThrottlingRateLimit':1})
    for name, path in [('PostPermission','POST/v6/events'), ('GetPermission','GET/v6/senders/*/events/*')]:
        r[name] = resource('Lambda::Permission', Action='lambda:InvokeFunction', FunctionName=ref('Alias'), Principal='apigateway.amazonaws.com', SourceAccount=ref('AWS::AccountId'), SourceArn=sub('arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${Api}/sandbox/'+path))
    r['ErrorsAlarm'] = resource('CloudWatch::Alarm', AlarmDescription='Sandbox invocation failures; action destination requires owner approval', Namespace='AWS/Lambda', MetricName='Errors', Dimensions=[{'Name':'FunctionName','Value':ref('Function')}], Statistic='Sum', Period=60, EvaluationPeriods=1, Threshold=1, ComparisonOperator='GreaterThanOrEqualToThreshold', TreatMissingData='notBreaching')
    r['ThrottleAlarm'] = resource('CloudWatch::Alarm', Namespace='AWS/Lambda', MetricName='Throttles', Dimensions=[{'Name':'FunctionName','Value':ref('Function')}], Statistic='Sum', Period=60, EvaluationPeriods=1, Threshold=1, ComparisonOperator='GreaterThanOrEqualToThreshold', TreatMissingData='notBreaching')
    for outcome in ['rejected', 'unavailable']:
        name = outcome.title()
        r[name+'Metric'] = resource('Logs::MetricFilter', LogGroupName=ref('FunctionLogs'),
            FilterPattern='{ $.kind = "v6_outcome" && $.outcome = "'+outcome+'" }',
            MetricTransformations=[{'MetricNamespace':'JELV6/Sandbox','MetricName':sub('${AWS::StackName}-'+outcome),'MetricValue':'1','DefaultValue':0}])
        r[name+'Alarm'] = resource('CloudWatch::Alarm', Namespace='JELV6/Sandbox', MetricName=sub('${AWS::StackName}-'+outcome),
            Statistic='Sum',Period=60,EvaluationPeriods=1,Threshold=1,ComparisonOperator='GreaterThanOrEqualToThreshold',TreatMissingData='notBreaching')
    r['Gateway4xxAlarm'] = resource('CloudWatch::Alarm', Namespace='AWS/ApiGateway',MetricName='4xx',
        Dimensions=[{'Name':'ApiId','Value':ref('Api')},{'Name':'Stage','Value':'sandbox'}],
        Statistic='Sum',Period=60,EvaluationPeriods=1,Threshold=5,ComparisonOperator='GreaterThanOrEqualToThreshold',TreatMissingData='notBreaching')
    return {'AWSTemplateFormatVersion':'2010-09-09','Description':'OFFLINE isolated V6 sandbox candidate. Not approved for deployment; packaged registry is intentionally unconfigured.',
            'Parameters':params,'Resources':r,'Outputs':{'SandboxApi':{'Description':'Proposed sandbox endpoint','Value':sub('https://${Api}.execute-api.${AWS::Region}.${AWS::URLSuffix}/sandbox')},'AliasArn':{'Description':'Only intended invocation target','Value':ref('Alias')}}}


if __name__ == '__main__':
    Path(__file__).resolve().parents[1].joinpath('infra/template.json').write_text(json.dumps(template(),indent=2)+'\n')
