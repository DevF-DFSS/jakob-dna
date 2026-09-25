"""Offline policy construction from explicit isolation evidence and new names."""
import json
from pathlib import Path


def ref(n): return {'Ref':n}
def sub(s): return {'Fn::Sub':s}
def arn(n): return {'Fn::GetAtt':[n,'Arn']}
def doc(*statements): return {'Version':'2012-10-17','Statement':list(statements)}
def resource(kind, **props): return {'Type':'AWS::'+kind,'Properties':props}
def imported(name): return {'Fn::ImportValue':sub('${BootstrapStackName}-'+name)}
def legacy():
    data=json.loads((Path(__file__).resolve().parents[1]/'isolation/legacy-identities.json').read_text())
    return [sub('arn:${AWS::Partition}:iam::${AWS::AccountId}:'+p) for e in data['principals'] for p in e['patterns']]
# AWS Lambda Developer Guide supported resource-policy actions, reviewed 2026-09-25.
# API Invoke maps to IAM lambda:InvokeFunction. No unsupported management claims.
LAMBDA_RESOURCE_ACTIONS = ['lambda:'+a for a in [
    'CreateAlias','DeleteAlias','DeleteFunction','DeleteFunctionConcurrency',
    'DeleteFunctionEventInvokeConfig','DeleteProvisionedConcurrencyConfig',
    'GetAlias','GetFunction','GetFunctionConcurrency','GetFunctionConfiguration',
    'GetFunctionEventInvokeConfig','GetPolicy','GetProvisionedConcurrencyConfig',
    'InvokeFunction','InvokeFunctionUrl','ListAliases','ListFunctionEventInvokeConfigs',
    'ListProvisionedConcurrencyConfigs','ListTags','ListVersionsByFunction',
    'PublishVersion','PutFunctionConcurrency','PutFunctionEventInvokeConfig',
    'PutProvisionedConcurrencyConfig','TagResource','UntagResource','UpdateAlias',
    'UpdateFunctionCode','UpdateFunctionEventInvokeConfig']]

def deny_legacy(service, resources):
    return {'Sid':'DenyKnownLegacy','Effect':'Deny','Principal':'*','Action':LAMBDA_RESOURCE_ACTIONS if service=='lambda' else service+':*','Resource':resources,
            'Condition':{'ArnLike':{'aws:PrincipalArn':legacy()}}}
def allow(actions, resources, **extra):
    return dict(Effect='Allow',Action=actions,Resource=resources,**extra)


def execution_boundary():
    table=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${AWS::StackName}-events')
    logs=sub('arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${AWS::StackName}-v6:log-stream:*')
    actions=['dynamodb:GetItem','dynamodb:PutItem','logs:CreateLogStream','logs:PutLogEvents']
    return doc(allow(actions[:2],table),allow(actions[2:],logs),
        {'Effect':'Deny','NotAction':actions,'Resource':'*'},
        {'Effect':'Deny','Action':'*','NotResource':[table,logs]})


def apply(t):
    r=t['Resources'];p=t['Parameters']
    p['BootstrapStackName']={'Type':'String','AllowedPattern':'jel-v6-bootstrap-[a-z0-9-]{1,32}'}
    p.pop('ArtifactBucket')
    r.pop('Api')
    # API and artifact storage exist in bootstrap first; runtime cannot choose a legacy ID.
    r['Function']['Properties']['Code']['S3Bucket']=imported('ArtifactBucket')
    def replace(x):
        if x=={'Ref':'Api'}:return imported('ApiId')
        if isinstance(x,dict):
            if 'Fn::Sub' in x and isinstance(x['Fn::Sub'],str) and '${Api}' in x['Fn::Sub']:
                return {'Fn::Sub':[x['Fn::Sub'],{'Api':imported('ApiId')}]}
            return {k:replace(v) for k,v in x.items()}
        if isinstance(x,list):return [replace(v) for v in x]
        return x
    t=replace(t);r=t['Resources']
    role=r['ExecutionRole']['Properties'];role['RoleName']=sub('${AWS::StackName}-v6-execution');role['Path']='/jel-v6/'
    role['PermissionsBoundary']=imported('RuntimeBoundaryArn')
    table=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${AWS::StackName}-events')
    index=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${AWS::StackName}-events/index/*')
    r['Events']['Properties']['ResourcePolicy']={'PolicyDocument':doc(deny_legacy('dynamodb',[table,index]))}
    function=arn('Function');qualified=sub('${Function.Arn}:*')
    statements=[deny_legacy('lambda',[function,qualified]),
        {'Sid':'DenyNonGatewayInvoke','Effect':'Deny','Principal':'*',
         'Action':['lambda:InvokeFunction','lambda:InvokeFunctionUrl'],'Resource':[function,qualified],
         'Condition':{'StringNotEqualsIfExists':{'aws:PrincipalServiceName':'apigateway.amazonaws.com'}}},
        {'Sid':'DenyOtherGatewayAccount','Effect':'Deny','Principal':{'Service':'apigateway.amazonaws.com'},
         'Action':'lambda:InvokeFunction','Resource':[function,qualified],
         'Condition':{'StringNotEquals':{'aws:SourceAccount':ref('AWS::AccountId')}}}]
    paths=['POST/v6/events','GET/v6/senders/*/events/*']
    sources=[{'Fn::Sub':['arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${Api}/sandbox/'+path,{'Api':imported('ApiId')}]} for path in paths]
    statements.append({'Sid':'DenyOtherGatewaySource','Effect':'Deny','Principal':{'Service':'apigateway.amazonaws.com'},
        'Action':'lambda:InvokeFunction','Resource':[function,qualified],'Condition':{'ArnNotLike':{'aws:SourceArn':sources}}})
    for i,source in enumerate(sources):
        statements.append(dict(Sid='AllowSandboxRoute'+str(i),**allow('lambda:InvokeFunction',ref('Alias'),
            Principal={'Service':'apigateway.amazonaws.com'},Condition={'StringEquals':{'aws:SourceAccount':ref('AWS::AccountId')},'ArnLike':{'aws:SourceArn':source}})))
    r['FunctionResourcePolicy']=resource('Lambda::ResourcePolicy',ResourceArn=function,PolicyDocument=doc(*statements))
    # Policy must exist before a stage makes the new API reachable.
    r['Stage']['DependsOn']=['FunctionResourcePolicy']
    return t


def bootstrap():
    params={'RuntimeStackName':{'Type':'String','AllowedPattern':'jel-v6-sandbox-[a-z0-9-]{1,24}'},
        'ApprovedRecoveryRoleArn':{'Type':'String','AllowedPattern':'arn:aws:iam::[0-9]{12}:role/jel-v6-approved/[A-Za-z0-9+=,.@_-]{1,64}',
            'Description':'Independently approved existing recovery/operator role, not a legacy identity. No default.'}}
    r={}
    r['SandboxApi']=resource('ApiGatewayV2::Api',Name=sub('${RuntimeStackName}-v6'),ProtocolType='HTTP')
    r['Artifacts']=resource('S3::Bucket',VersioningConfiguration={'Status':'Enabled'},
        PublicAccessBlockConfiguration={k:True for k in ['BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets']},
        OwnershipControls={'Rules':[{'ObjectOwnership':'BucketOwnerEnforced'}]},
        BucketEncryption={'ServerSideEncryptionConfiguration':[{'ServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]})
    r['Artifacts'].update(DeletionPolicy='Retain',UpdateReplacePolicy='Retain')
    function=sub('arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${RuntimeStackName}-v6')
    versions=sub('arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${RuntimeStackName}-v6:*')
    table=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${RuntimeStackName}-events')
    logs=sub('arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${RuntimeStackName}-v6:*')
    log_base=sub('arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${RuntimeStackName}-v6')
    role=sub('arn:${AWS::Partition}:iam::${AWS::AccountId}:role/jel-v6/${RuntimeStackName}-v6-execution')
    runtime_boundary=json.loads(json.dumps(execution_boundary()).replace('${AWS::StackName}','${RuntimeStackName}'))
    r['RuntimeBoundary']=resource('IAM::ManagedPolicy',ManagedPolicyName=sub('${RuntimeStackName}-runtime-boundary'),PolicyDocument=runtime_boundary)
    boundary=ref('RuntimeBoundary')
    api=sub('arn:${AWS::Partition}:apigateway:${AWS::Region}::/apis/${SandboxApi}/*')
    bucket=arn('Artifacts');objects=sub('${Artifacts.Arn}/*')
    statements=[allow(['lambda:CreateFunction','lambda:Get*','lambda:List*','lambda:UpdateFunctionConfiguration',
        'lambda:UpdateFunctionCode','lambda:DeleteFunction','lambda:PublishVersion',
        'lambda:*Alias',
        'lambda:PutResourcePolicy','lambda:DeleteResourcePolicy',
        'lambda:AddPermission','lambda:RemovePermission','lambda:TagResource','lambda:UntagResource'],[function,versions]),
        allow(['dynamodb:CreateTable','dynamodb:DescribeTable','dynamodb:UpdateTable','dynamodb:DeleteTable','dynamodb:UpdateContinuousBackups',
            'dynamodb:DescribeContinuousBackups','dynamodb:PutResourcePolicy','dynamodb:GetResourcePolicy','dynamodb:DeleteResourcePolicy',
            'dynamodb:TagResource','dynamodb:UntagResource','dynamodb:ListTagsOfResource'],table),
        allow(['logs:CreateLogGroup','logs:DescribeLogStreams','logs:PutRetentionPolicy','logs:DeleteLogGroup','logs:DeleteRetentionPolicy',
               'logs:PutMetricFilter','logs:DeleteMetricFilter','logs:DescribeMetricFilters','logs:TagResource','logs:UntagResource'],[logs,log_base]),
        allow(['logs:DescribeLogGroups'],'*'),
        allow(['apigateway:GET','apigateway:POST','apigateway:PATCH','apigateway:PUT','apigateway:DELETE'],api),
        allow(['iam:CreateRole'],role,Condition={'ArnEquals':{'iam:PermissionsBoundary':boundary}}),
        allow(['iam:GetRole*','iam:DeleteRole','iam:PutRolePolicy','iam:DeleteRolePolicy','iam:TagRole','iam:UntagRole'],role),
        allow('iam:PassRole',role,Condition={'StringEquals':{'iam:PassedToService':'lambda.amazonaws.com'}}),
        allow(['s3:GetObjectVersion'],objects),allow(['s3:GetBucketLocation'],bucket),
        allow(['cloudwatch:PutMetricAlarm','cloudwatch:DeleteAlarms','cloudwatch:DescribeAlarms','cloudwatch:TagResource','cloudwatch:UntagResource'],sub('arn:${AWS::Partition}:cloudwatch:${AWS::Region}:${AWS::AccountId}:alarm:${RuntimeStackName}-v6-*'))]
    # New deployment boundary: exact new resources; metadata DescribeLogGroups is
    # the sole Resource:* Allow (API has no resource-level scope). No data access.
    resources=[function,versions,table,logs,log_base,role,api,bucket,objects,
        sub('arn:${AWS::Partition}:cloudwatch:${AWS::Region}:${AWS::AccountId}:alarm:${RuntimeStackName}-v6-*')]
    deploy_boundary=doc(*statements,
        {'Effect':'Deny','NotAction':'logs:DescribeLogGroups','NotResource':resources},
        {'Effect':'Deny','NotAction':sorted({a for s in statements for a in (s['Action'] if isinstance(s['Action'],list) else [s['Action']])}),'Resource':'*'},
        {'Effect':'Deny','Action':'iam:CreateRole','Resource':role,'Condition':{'ArnNotEquals':{'iam:PermissionsBoundary':boundary}}},
        {'Effect':'Deny','Action':'iam:PassRole','Resource':role,'Condition':{'StringNotEquals':{'iam:PassedToService':'lambda.amazonaws.com'}}})
    r['DeploymentBoundary']=resource('IAM::ManagedPolicy',PolicyDocument=deploy_boundary)
    r['DeploymentRole']=resource('IAM::Role',PermissionsBoundary=ref('DeploymentBoundary'),
        AssumeRolePolicyDocument=doc({'Effect':'Allow','Principal':{'Service':'cloudformation.amazonaws.com'},'Action':'sts:AssumeRole'}),
        Policies=[{'PolicyName':'NewRuntimeOnly','PolicyDocument':doc(*statements)}])
    pubstatements=[allow(['s3:PutObject','s3:GetObjectVersion'],objects),allow(['s3:GetBucketLocation','s3:ListBucketVersions'],bucket),
        {'Effect':'Deny','Action':'*','NotResource':[bucket,objects]},
        {'Effect':'Deny','NotAction':['s3:PutObject','s3:GetObjectVersion','s3:GetBucketLocation','s3:ListBucketVersions'],'Resource':'*'}]
    r['PublisherBoundary']=resource('IAM::ManagedPolicy',PolicyDocument=doc(*pubstatements))
    r['PublisherRole']=resource('IAM::Role',PermissionsBoundary=ref('PublisherBoundary'),
        AssumeRolePolicyDocument=doc({'Effect':'Allow','Principal':{'AWS':ref('ApprovedRecoveryRoleArn')},'Action':'sts:AssumeRole'}),
        Policies=[{'PolicyName':'NewArtifactOnly','PolicyDocument':doc(*pubstatements[:2])}])
    r['ArtifactPolicy']=resource('S3::BucketPolicy',Bucket=ref('Artifacts'),PolicyDocument=doc(
        deny_legacy('s3',[bucket,objects]),
        {'Sid':'RequireTLS','Effect':'Deny','Principal':'*','Action':'s3:*','Resource':[bucket,objects],'Condition':{'Bool':{'aws:SecureTransport':'false','aws:PrincipalIsAWSService':'false'}}},
        {'Sid':'DenyOtherPrincipals','Effect':'Deny','Principal':'*','Action':'s3:*','Resource':[bucket,objects],
         'Condition':{'ArnNotEquals':{'aws:PrincipalArn':[arn('DeploymentRole'),arn('PublisherRole'),ref('ApprovedRecoveryRoleArn')]}}}))
    r['ArtifactPolicy'].update(DeletionPolicy='Retain',UpdateReplacePolicy='Retain')
    outputs={name:{'Value':value,'Export':{'Name':sub('${AWS::StackName}-'+name)}} for name,value in
        [('RuntimeBoundaryArn',ref('RuntimeBoundary')),('ApiId',ref('SandboxApi')),('ArtifactBucket',ref('Artifacts')),('DeploymentRoleArn',arn('DeploymentRole')),('PublisherRoleArn',arn('PublisherRole'))]}
    return {'AWSTemplateFormatVersion':'2010-09-09','Description':'OFFLINE bootstrap candidate. New resources only; no approved operator supplied.',
        'Parameters':params,'Rules':{'SameAccountRecovery':{'Assertions':[{'Assert':{'Fn::Equals':[{'Fn::Select':[4,{'Fn::Split':[':',ref('ApprovedRecoveryRoleArn')]}]},ref('AWS::AccountId')]},'AssertDescription':'Recovery role must belong to this account'}]}},'Resources':r,'Outputs':outputs}
