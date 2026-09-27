"""Render time-bounded operator proposals, not grants, approval, or deployment."""
from datetime import datetime
import re
from isolation_policy import doc, allow
from phase_policy import maximum, timed


def topology(c):
    if set(c)!={'account','region','namespace','stacks','trusted_operator','starts_at','expires_at'}:
        raise ValueError('exact_topology_context_required')
    account,region,ns=c['account'],c['region'],c['namespace']
    if not re.fullmatch('[0-9]{12}',account) or not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]',region) or not re.fullmatch('[a-z0-9]{8,12}',ns):raise ValueError('invalid_scope')
    if not re.fullmatch('arn:aws:iam::'+account+r':role/jel-v6-approved/[A-Za-z0-9+=,.@_-]{1,64}',c['trusted_operator']):raise ValueError('approved_nonroot_role_required')
    if set(c['stacks'])!={'bootstrap','authority','runtime','ingress'}:raise ValueError('exact_stacks_required')
    for k,name in c['stacks'].items():
        prefix='sandbox' if k=='runtime' else k
        if not re.fullmatch('jel-v6-'+prefix+'-[a-z0-9-]{1,24}',name):raise ValueError('new_stack_names_required')
    stack={k:f'arn:aws:cloudformation:{region}:{account}:stack/{v}/*' for k,v in c['stacks'].items()}
    runtime=c['stacks']['runtime']
    roles={k:f'arn:aws:iam::{account}:role/jel-v6/{runtime}-{suffix}' for k,suffix in [('runtime','runtime-deploy'),('ingress','ingress-deploy'),('publisher','publisher')]}
    bootstrap_service=f'arn:aws:iam::{account}:role/jel-v6-approved/{ns}-bootstrap-service'
    roles['bootstrap']=bootstrap_service
    bucket=f'arn:aws:s3:::jel-v6-{account}-{region}-{ns}'
    read=['cloudformation:DescribeStacks','cloudformation:DescribeStackEvents','cloudformation:DescribeStackResources','cloudformation:GetTemplate']
    result={}
    def add(name,statements,trust='operator',purpose=''):
        boundary=timed(maximum(statements),c['starts_at'],c['expires_at'])
        principal={'AWS':c['trusted_operator']} if trust=='operator' else {'Service':'cloudformation.amazonaws.com'}
        identity=timed(doc(*statements),c['starts_at'],c['expires_at'])
        result[name]={'role_arn':f'arn:aws:iam::{account}:role/jel-v6-approved/{ns}-{name}',
            'trust':doc(dict(Effect='Allow',Principal=principal,Action='sts:AssumeRole',Condition={'DateLessThan':{'aws:CurrentTime':c['expires_at']},'DateGreaterThanEquals':{'aws:CurrentTime':c['starts_at']}})),
            'identity_policy':identity,'maximum_boundary':boundary,'max_session_duration_seconds':3600,
            'authority':'temporary; install only for its separately approved phase', 'purpose':purpose,
            'removal':'Absolute maximum-policy deadline denies existing sessions; separately approved installer removes grants/trust after use; read back removal. Trust removal alone is insufficient.',
            'failure':'Stop/quarantine; retained resources are not automatically deleted; fresh bounded repair approval if this window expires.'}
    def operator(name,domain,actions):
        statements=[allow(read,stack[domain]),allow(actions,stack[domain],Condition={'ArnEquals':{'cloudformation:RoleArn':roles[domain]}}),allow('iam:PassRole',roles[domain],Condition={'StringEquals':{'iam:PassedToService':'cloudformation.amazonaws.com'}})]
        add(name,statements,purpose=domain+' stack only; no direct runtime invocation or other-stack mutation')
        # Explicit constraints survive hypothetical additional identity/session Allow.
        result[name]['maximum_boundary']['Statement'] += [
          {'Effect':'Deny','Action':actions,'Resource':stack[domain],'Condition':{'ArnNotEquals':{'cloudformation:RoleArn':roles[domain]}}},
          {'Effect':'Deny','Action':'iam:PassRole','Resource':roles[domain],'Condition':{'StringNotEquals':{'iam:PassedToService':'cloudformation.amazonaws.com'}}}]
    operator('bootstrap-operator','bootstrap',['cloudformation:CreateStack'])
    operator('runtime-operator','runtime',['cloudformation:CreateStack','cloudformation:UpdateStack'])
    operator('ingress-operator','ingress',['cloudformation:CreateStack','cloudformation:UpdateStack','cloudformation:DeleteStack'])
    operator('recovery-operator','runtime',['cloudformation:ContinueUpdateRollback'])
    operator('emergency-operator','runtime',['cloudformation:UpdateStack','cloudformation:ContinueUpdateRollback'])
    add('publisher-operator',[allow('sts:AssumeRole',roles['publisher'])],purpose='Assume exact S3-only publisher, cannot deploy or alter policies')
    # No API children mutation, IAM writes, function or data rights in bootstrap.
    # Read wildcard API metadata is required before a generated ID is known.
    api=f'arn:aws:apigateway:{region}::/apis'
    add('bootstrap-service',[allow('apigateway:POST',api),allow('apigateway:GET',[api,api+'/*']),
        allow(['s3:CreateBucket','s3:GetBucket*','s3:ListBucket','s3:PutBucketPolicy','s3:PutBucketPublicAccessBlock','s3:PutBucketOwnershipControls','s3:PutEncryptionConfiguration','s3:PutBucketVersioning'],bucket)],
        trust='service',purpose='Inert API and exact private bucket only; retained on failure; no routes/roles/data/function/stage. Conditional provider dependencies remain sandbox tests.')
    return {'schema_version':'jel-v6-authority-topology/1','context':c,'roles':result,'service_role_arns':roles,
        'installation_prerequisite':{'status':'UNCONFIGURED_EXTERNAL_TRUST_BOUNDARY','normal_root_use':False,
          'required_actor':'Independently approved existing non-root installation authority, not created or granted here.',
          'scope':'Install reviewed new roles/maximum boundaries and legacy fence. IAM policy contents cannot be constrained by another IAM policy; installer is trusted for these writes. No standing installer or emergency IAM-admin grant is rendered.',
          'before':'Select federation/trusted actor, exact role/policy documents, account, window and authenticated human authorization before ANY first write.',
          'after':'Read back all policies/role-use paths, remove temporary installation rights and verify before runtime creation.'},
        'deployment_authorized':False,'live_gates_closed':False}
