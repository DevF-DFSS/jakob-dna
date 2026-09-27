"""PR19 identity/maximum-policy construction. Pure offline data, never AWS calls."""
from copy import deepcopy
from isolation_policy import doc, allow


def source_bound_data(table, function):
    """Unqualified function ARN; identity/boundary only, never resource policy."""
    return allow(['dynamodb:GetItem', 'dynamodb:PutItem'], table,
                 Condition={'ArnEquals': {'lambda:SourceFunctionArn': function}})


def source_data_deny(function):
    # Negated ARN condition also matches an absent key (AWS IAM operator rules).
    return {'Sid': 'DenyOtherOrMissingSourceFunction', 'Effect': 'Deny',
            'Action': ['dynamodb:GetItem', 'dynamodb:PutItem'], 'Resource': '*',
            'Condition': {'ArnNotEquals': {'lambda:SourceFunctionArn': function}}}


def associated_pass(role, function):
    return allow('iam:PassRole', role, Condition={
        'StringEquals': {'iam:PassedToService': 'lambda.amazonaws.com'},
        'ArnEquals': {'iam:AssociatedResourceArn': function}})


def pass_denies(role, function):
    return [dict(Effect='Deny', Action='iam:PassRole', Resource=role, Condition={op: {key: value}})
            for op, key, value in [
                ('StringNotEquals', 'iam:PassedToService', 'lambda.amazonaws.com'),
                ('ArnNotEquals', 'iam:AssociatedResourceArn', function)]]


def legacy_fence(*, function, table, roles, boundaries, api, bucket, stacks):
    """Proposed attachment to legacy identities. No Principal/resource-policy fiction.

    Caller supplies exact generated API ARN after inert bootstrap. Installation
    and coverage of every relevant identity/role-use path remain external gates.
    """
    if not api or '*' in api or not api.split('/apis/')[-1]:
        raise ValueError('exact_api_required')
    return doc(
        dict(Effect='Deny', Action='lambda:*', Resource=[function, function+':*']),
        dict(Effect='Deny', Action='dynamodb:*', Resource=[table, table+'/index/*']),
        dict(Effect='Deny', Action='iam:*', Resource=roles+boundaries),
        dict(Effect='Deny', Action=['sts:AssumeRole','sts:TagSession'], Resource=roles),
        dict(Effect='Deny', Action=['apigateway:POST','apigateway:PUT','apigateway:PATCH','apigateway:DELETE'], Resource=[api,api+'/*']),
        dict(Effect='Deny', Action='s3:*', Resource=[bucket,bucket+'/*']),
        dict(Effect='Deny', Action='cloudformation:*', Resource=stacks))


def maximum(statements):
    """Maximum of explicit exact-resource Allows; conditions require extra Denies
    when resistance to an additional session/resource grant is a claimed property.
    """
    actions=[];resources=[]
    for s in statements:
        for key,out in [('Action',actions),('Resource',resources)]:
            for v in s[key] if isinstance(s[key],list) else [s[key]]:
                if v not in out:out.append(v)
    # Preserve action/resource association under a hypothetical extra Allow.
    # A union of all actions/resources alone would allow POST on GET-only API
    # children. These callers use non-overlapping action patterns.
    scoped=[]
    for action in actions:
        allowed=[]
        for statement in statements:
            named=statement['Action'] if isinstance(statement['Action'],list) else [statement['Action']]
            if action in named:
                for r in statement['Resource'] if isinstance(statement['Resource'],list) else [statement['Resource']]:
                    if r not in allowed:allowed.append(r)
        scoped.append({'Effect':'Deny','Action':action,'NotResource':allowed})
    return doc(*deepcopy(statements),
        {'Effect':'Deny','NotAction':actions,'Resource':'*'},
        {'Effect':'Deny','Action':'*','NotResource':resources},*scoped)


def timed(policy, starts, expires):
    """Absolute policy window; trust/session expiry alone cannot revoke sessions."""
    from datetime import datetime
    a,b=(datetime.fromisoformat(x.replace('Z','+00:00')) for x in (starts,expires))
    if a.tzinfo is None or b.tzinfo is None or not 0 < (b-a).total_seconds() <= 3600:
        raise ValueError('authority_window_must_be_at_most_one_hour')
    result=deepcopy(policy)
    result['Statement'] += [
        {'Effect':'Deny','Action':'*','Resource':'*','Condition':{'DateLessThan':{'aws:CurrentTime':starts}}},
        {'Effect':'Deny','Action':'*','Resource':'*','Condition':{'DateGreaterThanEquals':{'aws:CurrentTime':expires}}},
        {'Effect':'Deny','Action':'*','Resource':'*','Condition':{'Null':{'aws:CurrentTime':'true'}}}]
    return result
