"""Small OFFLINE decision model for only the IAM subset used in this candidate.

Not AWS simulation: no services, SCPs, session context discovery or propagation.
Unknown operators fail instead of being silently accepted. Role sessions must
supply the documented IAM role ARN as aws:PrincipalArn in synthetic context.
"""
from fnmatch import fnmatchcase


def values(x): return x if isinstance(x,list) else [x]
def matches(value,patterns):return value is not None and any(fnmatchcase(value,p) for p in values(patterns))
def condition(conditions, context):
    for operator,clauses in conditions.items():
        for key,expected in clauses.items():
            actual=context.get(key)
            if operator in ('ArnLike','ArnEquals','StringEquals'):
                ok=matches(actual,expected) if operator=='ArnLike' else actual in values(expected)
            elif operator in ('ArnNotLike','ArnNotEquals','StringNotEquals','StringNotEqualsIfExists'):
                ok=not matches(actual,expected) if operator=='ArnNotLike' else actual not in values(expected)
            elif operator=='Bool':ok=actual in values(expected)
            elif operator=='Null':ok=(actual is None)==(expected=='true')
            elif operator in ('DateLessThan','DateGreaterThanEquals'):
                from datetime import datetime
                if actual is None:ok=False
                else:
                    a,b=(datetime.fromisoformat(v.replace('Z','+00:00')) for v in (actual,expected))
                    if a.tzinfo is None or b.tzinfo is None:raise ValueError('timezone_required')
                    ok=a<b if operator=='DateLessThan' else a>=b
            else:raise ValueError('unsupported_condition_operator')
            if not ok:return False
    return True


def decision(statements, action, resource, context, *, identity_allow=False):
    allowed=identity_allow
    for s in statements:
        if 'NotPrincipal' in s:raise ValueError('not_principal_forbidden')
        if 'Action' in s and not matches(action.lower(),[a.lower() for a in values(s['Action'])]):continue
        if 'NotAction' in s and matches(action.lower(),[a.lower() for a in values(s['NotAction'])]):continue
        if 'Resource' in s and not matches(resource,s['Resource']):continue
        if 'NotResource' in s and matches(resource,s['NotResource']):continue
        principal=s.get('Principal','*')
        if isinstance(principal,dict):
            key='aws:PrincipalServiceName' if 'Service' in principal else 'aws:PrincipalArn'
            if not matches(context.get(key),principal.get('Service',principal.get('AWS'))):continue
        elif principal!='*':raise ValueError('unsupported_principal')
        if not condition(s.get('Condition',{}),context):continue
        if s['Effect']=='Deny':return 'explicitDeny'
        allowed=True
    return 'allowed' if allowed else 'implicitDeny'
