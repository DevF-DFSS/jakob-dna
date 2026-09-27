"""Derive PR19 phased candidate from reviewed generators. No AWS/CLI execution.

Combined infra/template.json and bootstrap.json remain historical fixtures.
Only this explicit phase bundle is the new composition; no combined deploy path.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from make_template import template
from isolation_policy import bootstrap, ref, sub, arn, imported, resource, doc, allow
from phase_policy import source_bound_data, source_data_deny, associated_pass, pass_denies, maximum


def walk(value, replacements):
    for before,after in replacements:
        if value==before:return deepcopy(after)
    if isinstance(value,dict):return {k:walk(v,replacements) for k,v in value.items()}
    if isinstance(value,list):return [walk(v,replacements) for v in value]
    return value


def exported(stack,name):return {'Fn::ImportValue':sub('${'+stack+'}-'+name)}
def output(name,value):return {'Description':name,'Value':value,'Export':{'Name':sub('${AWS::StackName}-'+name)}}
def role_arn(suffix):return sub('arn:${AWS::Partition}:iam::${AWS::AccountId}:role/jel-v6/${RuntimeStackName}-'+suffix)
def stack_parameter(prefix):return {'Type':'String','AllowedPattern':prefix+'[a-z0-9-]{1,24}'}


def templates(revision):
    if len(revision)!=64 or any(c not in '0123456789abcdef' for c in revision):raise ValueError('sha256_revision_required')
    old=bootstrap();b=deepcopy(old)
    b['Description']='PR19 phase1 inert bootstrap: no roles, data authority, routes or stage. Separate approval required.'
    b['Resources']={k:v for k,v in b['Resources'].items() if k in ['SandboxApi','Artifacts','ArtifactPolicy']}
    b['Parameters']['Namespace']={'Type':'String','AllowedPattern':'[a-z0-9]{8,12}'}
    b['Resources']['Artifacts']['Properties']['BucketName']=sub('jel-v6-${AWS::AccountId}-${AWS::Region}-${Namespace}')
    b['Resources']['SandboxApi'].update(DeletionPolicy='Retain',UpdateReplacePolicy='Retain')
    # Deny exceptions can name future role ARNs without creating/trusting those roles.
    b=walk(b,[(arn('DeploymentRole'),role_arn('runtime-deploy')),(arn('PublisherRole'),role_arn('publisher'))])
    b['Parameters']['BootstrapServiceRoleArn']={'Type':'String','AllowedPattern':'arn:aws:iam::[0-9]{12}:role/jel-v6-approved/[A-Za-z0-9+=,.@_-]{1,64}'}
    b['Resources']['ArtifactPolicy']['Properties']['PolicyDocument']['Statement'][-1]['Condition']['ArnNotEquals']['aws:PrincipalArn'].append(ref('BootstrapServiceRoleArn'))
    b['Outputs']={k:v for k,v in b['Outputs'].items() if k in ['ApiId','ArtifactBucket']}

    a=deepcopy(old)
    a['Description']='PR19 exact-ID authority installation. Trusted external installer required; no runtime or ingress.'
    a['Parameters']['BootstrapStackName']=stack_parameter('jel-v6-bootstrap-')
    a['Parameters']['PublisherAuthorityExpiresAt']={'Type':'String','AllowedPattern':'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z'}
    a['Resources']['PublisherBoundary']['Properties']['PolicyDocument']['Statement'].append({'Effect':'Deny','Action':'*','Resource':'*','Condition':{'DateGreaterThanEquals':{'aws:CurrentTime':ref('PublisherAuthorityExpiresAt')}}})
    a['Parameters']['ApprovedPublisherOperatorArn']={'Type':'String','AllowedPattern':'arn:aws:iam::[0-9]{12}:role/jel-v6-approved/[A-Za-z0-9+=,.@_-]{1,64}'}
    a['Resources']['PublisherRole']['Properties']['AssumeRolePolicyDocument']['Statement'][0]['Principal']['AWS']=ref('ApprovedPublisherOperatorArn')
    a['Resources']={k:v for k,v in a['Resources'].items() if k not in ['SandboxApi','Artifacts','ArtifactPolicy']}
    a=walk(a,[(ref('SandboxApi'),imported('ApiId')),(ref('Artifacts'),imported('ArtifactBucket')),
              (arn('Artifacts'),{'Fn::Sub':['arn:${AWS::Partition}:s3:::${Bucket}',{'Bucket':imported('ArtifactBucket')}]}),
              (sub('${Artifacts.Arn}/*'),{'Fn::Sub':['arn:${AWS::Partition}:s3:::${Bucket}/*',{'Bucket':imported('ArtifactBucket')}]}),
              (sub('arn:${AWS::Partition}:apigateway:${AWS::Region}::/apis/${SandboxApi}/*'),
               {'Fn::Sub':['arn:${AWS::Partition}:apigateway:${AWS::Region}::/apis/${Api}/*',{'Api':imported('ApiId')} ]})])
    function=sub('arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${RuntimeStackName}-v6')
    role=sub('arn:${AWS::Partition}:iam::${AWS::AccountId}:role/jel-v6/${RuntimeStackName}-v6-execution')
    boundary=a['Resources']['RuntimeBoundary']['Properties']['PolicyDocument']['Statement']
    boundary[0]=source_bound_data(boundary[0]['Resource'],function);boundary.append(source_data_deny(function))
    # Runtime service role has no API mutation capability. Existing explicit
    # NotAction boundary is rebuilt to remove its former Gateway allowlist too.
    statements=a['Resources']['DeploymentRole']['Properties']['Policies'][0]['PolicyDocument']['Statement']
    statements=[s for s in statements if not any(x.startswith('apigateway:') for x in (s['Action'] if isinstance(s['Action'],list) else [s['Action']]))]
    statements=[associated_pass(role,function) if s['Action']=='iam:PassRole' else s for s in statements]
    a['Resources']['DeploymentRole']['Properties']['Policies'][0]['PolicyDocument']=doc(*statements)
    oldmax=a['Resources']['DeploymentBoundary']['Properties']['PolicyDocument']['Statement']
    tail=[s for s in oldmax if s.get('Effect')=='Deny']
    tail[0]['NotResource']=[r for r in tail[0]['NotResource'] if 'apigateway:' not in json.dumps(r)]
    tail[1]['NotAction']=[x for x in tail[1]['NotAction'] if not x.startswith('apigateway:')]
    a['Resources']['DeploymentBoundary']['Properties']['PolicyDocument']=doc(*deepcopy(statements),*tail,*pass_denies(role,function))
    for name,suffix in [('DeploymentRole','runtime-deploy'),('PublisherRole','publisher')]:
        a['Resources'][name]['Properties'].update(RoleName=sub('${RuntimeStackName}-'+suffix),Path='/jel-v6/',MaxSessionDuration=3600)
    api={'Fn::Sub':['arn:${AWS::Partition}:apigateway:${AWS::Region}::/apis/${Api}',{'Api':imported('ApiId')}]}
    children={'Fn::Sub':['arn:${AWS::Partition}:apigateway:${AWS::Region}::/apis/${Api}/*',{'Api':imported('ApiId')}]}
    ingress=[allow('apigateway:GET',[api,children]),allow(['apigateway:POST','apigateway:PUT','apigateway:PATCH','apigateway:DELETE'],children)]
    a['Resources']['IngressBoundary']=resource('IAM::ManagedPolicy',PolicyDocument=maximum(ingress))
    a['Resources']['IngressRole']=resource('IAM::Role',RoleName=sub('${RuntimeStackName}-ingress-deploy'),Path='/jel-v6/',MaxSessionDuration=3600,
        PermissionsBoundary=ref('IngressBoundary'),AssumeRolePolicyDocument=doc({'Effect':'Allow','Principal':{'Service':'cloudformation.amazonaws.com'},'Action':'sts:AssumeRole'}),
        Policies=[{'PolicyName':'ExactApiChildrenOnly','PolicyDocument':doc(*ingress)}])
    for name,suffix in [('DeploymentBoundary','deployment-boundary'),('PublisherBoundary','publisher-boundary'),('IngressBoundary','ingress-boundary')]:
        a['Resources'][name]['Properties']['ManagedPolicyName']=sub('${RuntimeStackName}-'+suffix)
    a['Outputs']={k:v for k,v in a['Outputs'].items() if k not in ['ApiId','ArtifactBucket']}
    a['Outputs']['IngressRoleArn']=output('IngressRoleArn',arn('IngressRole'))

    r=template();r['Description']='PR19 contained runtime: no API management resources; closed packaged capability by default.'
    api_names={'Authorizer','Integration','PostRoute','GetRoute','CandidateDeployment','Stage','Gateway4xxAlarm'}
    ingress_resources={k:deepcopy(v) for k,v in r['Resources'].items() if k in api_names and k!='Gateway4xxAlarm'}
    r['Resources']={k:v for k,v in r['Resources'].items() if k not in api_names}
    r['Parameters']['AuthorityStackName']=stack_parameter('jel-v6-authority-')
    r['Resources']['ExecutionRole']['Properties']['PermissionsBoundary']=exported('AuthorityStackName','RuntimeBoundaryArn')
    data=r['Resources']['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement']
    data[0]=source_bound_data(arn('Events'),sub('arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${AWS::StackName}-v6'))
    r['Resources']['Function']['Properties']['Handler']='aws_v6.phase_host.handler'
    # CLOSED capability returns before config/SDK construction. Empty values are
    # explicitly unconfigured, not invented provider endpoints or subjects.
    for key in ['JwtIssuer','JwtAudience','ClientIdsJson','BindingsVersion']:
        r['Parameters'][key]={'Type':'String','Default':'','Description':'Unconfigured only valid with CLOSED packaged capability'}
    r['Parameters']['BindingsSha256']['Default']='0'*64
    r['Parameters']['CapabilitySha256']={'Type':'String','AllowedPattern':'[0-9a-f]{64}'}
    r['Resources']['Function']['Properties']['Environment']['Variables']['CAPABILITY_SHA256']=ref('CapabilitySha256')
    r['Outputs']={k:output(k,v) for k,v in [('AliasArn',ref('Alias')),('FunctionArn',arn('Function'))]}
    # Different immutable capability/artifact must accompany each config release.
    version='CandidateVersion'+revision[:16]
    r['Resources'][version]=r['Resources'].pop('CandidateVersion')
    r=walk(r,[({'Fn::GetAtt':['CandidateVersion','Version']},{'Fn::GetAtt':[version,'Version']})])

    i={'AWSTemplateFormatVersion':'2010-09-09','Description':'PR19 separately authorized ingress. Test vs reviewed mode lives in immutable runtime capability; never approval strings.',
       'Parameters':{'BootstrapStackName':stack_parameter('jel-v6-bootstrap-'),'RuntimeStackName':stack_parameter('jel-v6-sandbox-'),
                     'JwtIssuer':{'Type':'String','AllowedPattern':'https://.+'},'JwtAudience':{'Type':'String','MinLength':1}},'Resources':ingress_resources}
    i=walk(i,[(ref('Alias'),exported('RuntimeStackName','AliasArn'))])
    i['Resources']['Stage'].pop('DependsOn',None) # Runtime export cannot exist before its full policy completes.
    deployment='CandidateDeployment'+revision[:16]
    i['Resources'][deployment]=i['Resources'].pop('CandidateDeployment')
    i=walk(i,[(ref('CandidateDeployment'),ref(deployment))])
    return {'bootstrap':b,'authority':a,'runtime':r,'ingress':i}


def write(candidate):
    raw=(candidate/'aws_v6/capability.json').read_bytes();revision=hashlib.sha256(raw).hexdigest()
    folder=candidate/'infra/phases';folder.mkdir(exist_ok=True)
    for name,value in templates(revision).items():
        (folder/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')

if __name__=='__main__':write(Path(__file__).resolve().parents[1])
