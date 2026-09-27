"""Offline phase-plan contract. No AWS executor or authenticated approval adapter.

Expected context and verified digests belong to an independent trust boundary.
The CLI does not have one: it always exits nonzero and never authorizes deployment.
PR13 remains a separate gate; this contract does not manufacture its evidence.
"""
import argparse
import re
from authorization_gate import digest, timestamp
from release_manifest import read_json

PHASES = {
    'BOOTSTRAP': ('NONE','CREATE_INERT_BOOTSTRAP','CLOSED','bootstrap'),
    'AUTHORITY': ('BOOTSTRAP','INSTALL_EXACT_AUTHORITY','CLOSED','authority'),
    'RUNTIME': ('AUTHORITY','CREATE_CONTAINED_RUNTIME','CLOSED','runtime'),
    'TEST_INGRESS': ('RUNTIME','PUBLISH_TEST_CAPABILITY_AND_CREATE_INGRESS','TEST','ingress'),
    'SANDBOX': ('TESTED','PUBLISH_REVIEWED_SANDBOX_CAPABILITY','SANDBOX','runtime'),
}
CONTEXT = {'account','region','source_commit','parent_commit','templates','bindings_sha256',
           'artifact_sha256','capability_sha256','capability_mode','s3','stacks','roles',
           'api_id','provider_profile_sha256'}
EVIDENCE = {'authority':'AWS_LIVE_READ_ONLY','containment':'AWS_LIVE_READ_ONLY',
            'recovery':'AWS_LIVE_READ_ONLY','validation':'OFFLINE_EXECUTION',
            'human':'HUMAN_AUTHORIZATION'}
ROLE_NAMES = {'operator','recovery','bootstrap_service','runtime_service','ingress_service','publisher'}


def sha(value,n=64):return type(value) is str and bool(re.fullmatch('[0-9a-f]{'+str(n)+'}',value))


def valid_context(c,phase):
    if type(c) is not dict or set(c)!=CONTEXT:return False
    if type(c['account']) is not str or not re.fullmatch('[0-9]{12}',c['account']) or c['account']=='000000000000':return False
    if type(c['region']) is not str or not re.fullmatch('[a-z]{2}(?:-[a-z]+)+-[0-9]',c['region']):return False
    if not all(sha(c[k],40) for k in ['source_commit','parent_commit']):return False
    if c['source_commit']==c['parent_commit']:return False
    if not all(sha(c[k]) for k in ['bindings_sha256','artifact_sha256','capability_sha256']):return False
    if type(c['templates']) is not dict or set(c['templates'])!={'bootstrap','authority','runtime','ingress'} or not all(sha(v) for v in c['templates'].values()):return False
    if type(c['stacks']) is not dict or set(c['stacks'])!=set(c['templates']):return False
    prefixes={'bootstrap':'bootstrap','authority':'authority','runtime':'sandbox','ingress':'ingress'}
    if not all(type(v) is str and re.fullmatch('jel-v6-'+prefixes[k]+'-[a-z0-9-]{1,24}',v) for k,v in c['stacks'].items()):return False
    if type(c['roles']) is not dict or set(c['roles'])!=ROLE_NAMES:return False
    prefix='arn:aws:iam::'+c['account']+':role/'
    if not all(type(v) is str and re.fullmatch(re.escape(prefix)+r'jel-v6(?:-approved)?/[A-Za-z0-9+=,.@_-]{1,64}',v) for v in c['roles'].values()):return False
    if len(set(c['roles'].values()))!=len(ROLE_NAMES):return False
    s=c['s3']
    if type(s) is not dict or set(s)!={'bucket','key','version'}:return False
    if not all(type(v) is str and v.strip() and v not in ('null','UNCONFIGURED') for v in s.values()):return False
    if not re.fullmatch('jel-v6-'+c['account']+'-'+c['region']+'-[a-z0-9]{8,12}',s['bucket']):return False
    if s['key']!='releases/'+c['artifact_sha256']+'.zip':return False
    # Before publication version is an explicit future prerequisite, never a fake version.
    if phase in ('BOOTSTRAP','AUTHORITY'):
        if s['version']!='NOT_PUBLISHED':return False
    elif s['version']=='NOT_PUBLISHED':return False
    if phase=='BOOTSTRAP':
        if c['api_id'] is not None:return False
    elif type(c['api_id']) is not str or not re.fullmatch('[a-z0-9]{1,16}',c['api_id']):return False
    if phase in ('TEST_INGRESS','SANDBOX'):
        if not sha(c['provider_profile_sha256']):return False
    elif c['provider_profile_sha256'] is not None:return False
    return c['capability_mode']==PHASES[phase][2]


def evaluate(plan,expected,*,now,verified_digests=frozenset()):
    failures=[]
    def fail(why):failures.append(why)
    try:
        current=timestamp(now)
        fields={'schema_version','phase','context','previous','mutation_class','resources',
                'starts_at','expires_at','stop_conditions','rollback','blockers','evidence'}
        if type(plan) is not dict or set(plan)!=fields or plan['schema_version']!='jel-v6-phase-plan/1':raise ValueError()
        phase=plan['phase']
        if type(phase) is not str or phase not in PHASES or not valid_context(expected,phase):raise ValueError()
        if plan['context']!=expected:fail('context_mismatch')
        start,end=timestamp(plan['starts_at']),timestamp(plan['expires_at'])
        if not start<=current<end or not 0<(end-start).total_seconds()<=3600:fail('invalid_or_expired_window')
        prev,mutation,mode,stack=PHASES[phase]
        prior=plan['previous']
        if type(prior) is not dict or set(prior)!={'state','result','receipt_sha256'}:raise ValueError()
        if prior['state']!=prev or prior['result']!='COMPLETE':fail('phase_skip_or_partial_create_requires_quarantine')
        if phase=='BOOTSTRAP':
            if prior['receipt_sha256'] is not None:fail('unexpected_prior_receipt')
        elif not sha(prior['receipt_sha256']) or prior['receipt_sha256'] not in verified_digests:fail('unverified_prior_state')
        if plan['mutation_class']!=mutation:fail('wrong_mutation_class')
        exact='arn:aws:cloudformation:'+expected['region']+':'+expected['account']+':stack/'+expected['stacks'][stack]+'/*'
        required=[exact]
        if phase=='TEST_INGRESS':
            required.append('arn:aws:cloudformation:'+expected['region']+':'+expected['account']+':stack/'+expected['stacks']['runtime']+'/*')
        if plan['resources']!=required:fail('wrong_mutation_resources')
        if plan['stop_conditions']!=['any_failed_or_unknown_gate','any_partial_create','any_unexpected_resource','window_expired']:fail('missing_stop_conditions')
        rb=plan['rollback']
        if type(rb) is not dict or set(rb)!={'strategy','operator_arn','procedure_sha256'}:raise ValueError()
        if rb['strategy']!='QUARANTINE_THEN_SEPARATE_RECOVERY_AUTHORIZATION' or rb['operator_arn']!=expected['roles']['recovery'] or not sha(rb['procedure_sha256']):fail('recovery_plan_required')
        if plan['blockers']!=[]:fail('unresolved_blockers')
        rows=plan['evidence'];kinds=dict(EVIDENCE)
        if phase=='SANDBOX':kinds['sandbox_observations']='OBSERVED_LIVE_BEHAVIOR'
        if type(rows) is not list or len(rows)!=len(kinds):raise ValueError()
        found=set()
        # Every observation binds the full operation, not merely a reusable commit.
        operation=digest({k:v for k,v in plan.items() if k!='evidence'})
        for e in rows:
            if type(e) is not dict or set(e)!={'kind','class','source','observed_at','operation_sha256','result','authorization_coordinate'}:raise ValueError()
            k=e['kind']
            if type(k) is not str or k not in kinds or k in found:raise ValueError()
            found.add(k)
            if e['class']!=kinds[k] or e['operation_sha256']!=operation or e['result']!='PASS':fail('wrong_evidence')
            if not start<=timestamp(e['observed_at'])<=current:fail('stale_or_future_evidence')
            if type(e['source']) is not str or not e['source'].strip():fail('missing_provenance')
            if k=='human':
                if type(e['authorization_coordinate']) is not str or not e['authorization_coordinate'].strip():fail('missing_human_coordinate')
            elif e['authorization_coordinate'] is not None:fail('unexpected_human_claim')
            if digest(e) not in verified_digests:fail('unverified_evidence_or_human_authority')
    except (ValueError,TypeError,KeyError,OverflowError):fail('malformed_plan_or_expected_context')
    return {'schema_version':'jel-v6-phase-result/1','status':'COMPLETE' if not failures else 'BLOCKED',
            'logically_complete':not failures,'deployment_authorized':False,'failures':sorted(set(failures)),
            'limit':'No executor; verified digests require an external trust boundary. Human text is not authenticated authorization.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True);p.add_argument('--context',required=True);p.add_argument('--now',required=True)
    a=p.parse_args()
    import json
    try:r=evaluate(read_json(a.plan),read_json(a.context),now=a.now)
    except Exception:r={'status':'BLOCKED','deployment_authorized':False,'failures':['invalid_input']}
    print(json.dumps(r,sort_keys=True));return 1

if __name__=='__main__':raise SystemExit(main())
