"""Static isolation contracts. Not an IAM simulator or AWS authorization proof."""
import json
from isolation_policy import apply, bootstrap, execution_boundary, deny_legacy, sub, ref, arn


def check_isolation(t):
    r=t['Resources']
    assert not any(v['Type']=='AWS::Lambda::Permission' for v in r.values())
    assert [v['Type'] for v in r.values()].count('AWS::Lambda::ResourcePolicy')==1
    assert 'NotPrincipal' not in json.dumps(t)
    # Independently require the intended trust skeleton; deny contents are also
    # covered by decision-table tests with deliberately broad identity Allows.
    policy=r['FunctionResourcePolicy']['Properties']
    assert set(policy)=={'ResourceArn','PolicyDocument'} and policy['ResourceArn']==arn('Function')
    s=policy['PolicyDocument']['Statement'];assert len(s)==6
    assert s[0]==deny_legacy('lambda',[arn('Function'),sub('${Function.Arn}:*')])
    assert s[1]['Effect']=='Deny' and s[1]['Condition']=={'StringNotEqualsIfExists':{'aws:PrincipalServiceName':'apigateway.amazonaws.com'}}
    assert s[1]['Principal']=='*' and s[1]['Action']==['lambda:InvokeFunction','lambda:InvokeFunctionUrl']
    assert s[1]['Resource']==[arn('Function'),sub('${Function.Arn}:*')]
    for statement in s[2:4]:
        assert statement['Effect']=='Deny' and statement['Principal']=={'Service':'apigateway.amazonaws.com'}
        assert statement['Action']=='lambda:InvokeFunction' and statement['Resource']==[arn('Function'),sub('${Function.Arn}:*')]
    assert s[2]['Condition']=={'StringNotEquals':{'aws:SourceAccount':ref('AWS::AccountId')}}
    sources=[]
    from isolation_policy import imported
    for path,statement in zip(['POST/v6/events','GET/v6/senders/*/events/*'],s[-2:]):
        source={'Fn::Sub':['arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${Api}/sandbox/'+path,{'Api':imported('ApiId')}]}
        sources.append(source)
        assert statement['Effect']=='Allow' and statement['Action']=='lambda:InvokeFunction'
        assert statement['Principal']=={'Service':'apigateway.amazonaws.com'} and statement['Resource']==ref('Alias')
        assert statement['Condition']=={'StringEquals':{'aws:SourceAccount':ref('AWS::AccountId')},'ArnLike':{'aws:SourceArn':source}}
    assert s[3]['Condition']=={'ArnNotLike':{'aws:SourceArn':sources}}
    assert r['Stage']['DependsOn']==['FunctionResourcePolicy']
    table=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${AWS::StackName}-events')
    index=sub('arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/jel-v6-${AWS::StackName}-events/index/*')
    assert r['Events']['Properties']['ResourcePolicy']['PolicyDocument']['Statement']==[deny_legacy('dynamodb',[table,index])]
    assert r['ExecutionRole']['Properties']['PermissionsBoundary']==imported('RuntimeBoundaryArn')
    assert r['Function']['Properties']['Code']['S3Bucket']==imported('ArtifactBucket')
    for key in ['ErrorsAlarm','ThrottleAlarm','RejectedAlarm','UnavailableAlarm','Gateway4xxAlarm']:
        assert r[key]['Properties']['AlarmName']==sub('${AWS::StackName}-v6-'+key)
    return True


def check_bootstrap(t):
    # An exact reviewed shape prevents extra resources/trust grants. Semantic
    # counterexamples are tested separately, not inferred from this comparison.
    assert t==bootstrap()
    r=t['Resources'];b=r['Artifacts']['Properties']
    assert 'BucketName' not in b
    assert all(b['PublicAccessBlockConfiguration'].values())
    assert b['VersioningConfiguration']=={'Status':'Enabled'}
    assert 'NotPrincipal' not in json.dumps(t)
    assert set(r)=={'SandboxApi','Artifacts','RuntimeBoundary','DeploymentBoundary','DeploymentRole','PublisherBoundary','PublisherRole','ArtifactPolicy'}
    for role in ['Deployment','Publisher']:
        assert r[role+'Role']['Properties']['PermissionsBoundary']==ref(role+'Boundary')
    return True
