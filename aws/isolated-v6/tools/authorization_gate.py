"""Offline pre-activation contract. No deployment or evidence-verification authority.

verified_digests is supplied ONLY by an independent trusted verification boundary,
not by the evidence document. This module does not authenticate signatures or DevF.
The CLI has no such boundary and cannot produce COMPLETE from uploaded claims.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import re
from release_manifest import read_json

KINDS = {'account':'AWS_LIVE_READ_ONLY','region':'AWS_LIVE_READ_ONLY',
         'operator':'AWS_LIVE_READ_ONLY','recovery':'AWS_LIVE_READ_ONLY',
         'effective_authorization':'AWS_LIVE_READ_ONLY','schema':'AWS_LIVE_READ_ONLY',
         'offline_validation':'LOCAL_EXECUTION','devf_authorization':'HUMAN_AUTHORIZATION'}
CONTEXT = {'account_id','region','operator_arn','recovery_arn','candidate_commit',
           'artifact_sha256','template_sha256','bootstrap_sha256','binding_sha256'}
MAX_AGE_SECONDS = 86400


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def timestamp(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ',value):
        raise ValueError('timestamp_invalid')
    return datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def valid_context(c):
    if type(c) is not dict or set(c)!=CONTEXT or any(type(v) is not str for v in c.values()):return False
    if not re.fullmatch(r'[0-9]{12}',c['account_id']) or c['account_id']=='000000000000':return False
    if not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]',c['region']):return False
    role='arn:aws:iam::'+c['account_id']+':role/'
    if not c['operator_arn'].startswith(role) or not re.fullmatch(r'[A-Za-z0-9_+=,.@/-]+',c['operator_arn'][len(role):]):return False
    if not re.fullmatch(re.escape(role)+r'jel-v6-approved/[A-Za-z0-9_+=,.@-]{1,64}',c['recovery_arn']):return False
    if not re.fullmatch('[0-9a-f]{40}',c['candidate_commit']):return False
    return all(re.fullmatch('[0-9a-f]{64}',c[k]) for k in CONTEXT if k.endswith('sha256'))


def evaluate(record, expected, *, now, verified_digests=frozenset()):
    """Expected context, clock and verified digests are trusted caller inputs.

    Completeness is bounded to this contract and expires after 24 hours or any
    context/policy change. It never grants authority or proves live enforcement.
    """
    failures=[]
    def add(gate,status,reason):failures.append({'gate':gate,'status':status,'reason':reason})
    try:
        current=timestamp(now)
        if not valid_context(expected):raise ValueError('invalid_expected_context')
        if type(record) is not dict or set(record)!={'schema_version','context','blockers','evidence'} or record['schema_version']!='jel-v6-authorization/1':
            raise ValueError('invalid_record')
        if record['context']!=expected:add('context','BLOCKED','context_mismatch')
        if type(record['blockers']) is not list or record['blockers']:
            add('blockers','BLOCKED','unresolved_or_malformed_blockers')
        rows=record['evidence']
        if type(rows) is not list:raise ValueError('invalid_evidence')
        found={}
        for e in rows:
            if type(e) is not dict or set(e)!={'kind','source','mode','observed_at','context','result','approval'}:raise ValueError('invalid_evidence')
            kind=e['kind']
            if type(kind) is not str or kind not in KINDS or kind in found:raise ValueError('duplicate_or_unknown_evidence')
            found[kind]=e
        for kind,mode in KINDS.items():
            e=found.get(kind)
            if e is None:add(kind,'UNKNOWN','missing_evidence');continue
            age=(current-timestamp(e['observed_at'])).total_seconds()
            if e['context']!=expected:add(kind,'BLOCKED','context_mismatch')
            if e['mode']!=mode:add(kind,'BLOCKED','wrong_evidence_class')
            if not 0<=age<=MAX_AGE_SECONDS:add(kind,'BLOCKED','stale_or_future_evidence')
            if e['result']!='PASS':add(kind,'BLOCKED','failed_or_unknown_result')
            if type(e['source']) is not str or not e['source'].strip():add(kind,'UNKNOWN','missing_source')
            if digest(e) not in verified_digests:add(kind,'UNKNOWN','unverified_provenance')
            approval=e['approval']
            if kind=='devf_authorization':
                if type(approval) is not dict or set(approval)!={'by','decision','review_reference'} or approval['by']!='DevF' or approval['decision']!='AUTHORIZE_SANDBOX' or type(approval['review_reference']) is not str or not approval['review_reference'].strip():
                    add(kind,'BLOCKED','explicit_devf_authorization_missing')
            elif approval is not None:add(kind,'BLOCKED','unexpected_approval')
    except (ValueError,TypeError,KeyError,OverflowError):
        add('record','BLOCKED','malformed_contract_or_clock')
    status='BLOCKED' if any(f['status']=='BLOCKED' for f in failures) else 'UNKNOWN' if failures else 'COMPLETE'
    return {'schema_version':'jel-v6-gate-result/1','status':status,'logically_complete':status=='COMPLETE',
            'deployment_authorized':False,'failures':failures,
            'limit':'Offline contract only; independent evidence authentication and separate approved execution required.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',required=True);p.add_argument('--context',required=True);p.add_argument('--now',required=True)
    args=p.parse_args()
    try:result=evaluate(read_json(args.record),read_json(args.context),now=args.now)
    except Exception:result={'status':'BLOCKED','deployment_authorized':False,'reason':'invalid_input'}
    print(json.dumps(result,sort_keys=True))
    return 1  # No authenticated approval adapter exists in the CLI.

if __name__=='__main__':raise SystemExit(main())
