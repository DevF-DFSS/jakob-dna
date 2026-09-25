"""Offline versioned release-record validation, never a deployment command.

An approval declaration is not cryptographic proof of human authorization.
The caller must separately review provenance/source attribution and live gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

FIELDS = {'schema_version','approval','account_id','region','issuer','audience','client_id',
          'allowed_scopes','binding_version','binding_sha256','source_commit','template_sha256',
          'artifact_sha256','artifact'}


def fail():
    raise ValueError('release_manifest_rejected')


def pairs(items):
    result = {}
    for key,value in items:
        if key in result: fail()
        result[key] = value
    return result


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > 1048576: fail()
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _:fail())


def text(value):
    return type(value) is str and 0 < len(value) <= 2048 and value == value.strip() and all(ord(c)>=33 and ord(c)!=127 for c in value)


def validate(m, *, expected_source, template, artifact, bindings, provenance):
    if type(m) is not dict or set(m)!=FIELDS or m['schema_version']!='jel-v6-release/1': fail()
    approval=m['approval']
    if (type(approval) is not dict or set(approval)!={'status','review_reference'} or
            approval['status']!='APPROVED' or not text(approval['review_reference'])): fail()
    for name in ['account_id','region','issuer','audience','client_id','binding_version','source_commit',
                 'binding_sha256','template_sha256','artifact_sha256']:
        if not text(m[name]) or m[name].upper() in {'UNCONFIGURED','UNAPPROVED','PLACEHOLDER','TODO'}: fail()
    if not re.fullmatch(r'[0-9]{12}',m['account_id']) or m['account_id']=='000000000000': fail()
    if not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]',m['region']): fail()
    issuer=urlsplit(m['issuer'])
    if issuer.scheme!='https' or not issuer.hostname or issuer.username or issuer.password or issuer.query or issuer.fragment: fail()
    if not re.fullmatch(r'[0-9a-f]{40}',expected_source) or m['source_commit']!=expected_source: fail()
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',m['binding_version']): fail()
    scopes=m['allowed_scopes']
    if (type(scopes) is not list or not scopes or any(type(s) is not str for s in scopes) or
            len(scopes)!=len(set(scopes)) or not set(scopes)<={'jel-v6/read','jel-v6/write'}): fail()
    a=m['artifact']
    if type(a) is not dict or set(a)!={'bucket','key','version'} or not all(text(v) for v in a.values()): fail()
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',a['bucket']) or any(v.upper() in {'TODO','PLACEHOLDER','UNCONFIGURED','NULL'} for v in a.values()): fail()
    if a['bucket'] in {'jakob-asset-store','jakob-backup-vault','dfss-jakob-anchors'}: fail()
    for field,path in [('template_sha256',template),('artifact_sha256',artifact),('binding_sha256',bindings)]:
        if not re.fullmatch(r'[0-9a-f]{64}',m[field]) or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=m[field]: fail()
    if not __debug__: fail()
    from security import check
    check(read_json(template))
    inputs={x['path']:x['sha256'] for x in provenance.get('source_inputs',[])}
    if (inputs.get('aws/isolated-v6/infra/template.json')!=m['template_sha256'] or
            inputs.get('aws/isolated-v6/aws_v6/bindings.json')!=m['binding_sha256']): fail()
    registry=read_json(bindings)
    if registry.get('version')!=m['binding_version'] or not registry.get('bindings'): fail()
    # Reuse runtime validation, including strict duplicate/unknown fields and
    # issuer/client/subject binding shape. No SDK construction or credential read.
    from aws_v6.config import settings, load_registry
    config=settings(dict(V6_TABLE_NAME='jel-v6-release-validation',EXPECTED_REGION=m['region'],AWS_REGION=m['region'],
        EXPECTED_API_ID='releasevalidation',EXPECTED_STAGE='sandbox',EXPECTED_ISSUER=m['issuer'],EXPECTED_AUDIENCE=m['audience'],
        EXPECTED_CLIENT_IDS=json.dumps([m['client_id']]),BINDINGS_VERSION=m['binding_version'],BINDINGS_SHA256=m['binding_sha256'],
        EXPECTED_ALIAS_ARN='arn:aws:lambda:'+m['region']+':'+m['account_id']+':function:release-validation-v6:sandbox'))
    load_registry(config,Path(bindings))
    if provenance.get('source_commit')!=expected_source or provenance.get('artifact_sha256')!=m['artifact_sha256']: fail()
    tests=provenance.get('tests',{})
    if tests.get('passed') is not True or tests.get('tests_run',0)<=0 or tests.get('failures')!=0 or tests.get('errors')!=0 or tests.get('skipped')!=0: fail()
    if provenance.get('cloudformation',{}).get('passed') is not True: fail()
    return {'offline_manifest_consistent':True,'deployment_authorized':False,'live_gates':'UNRESOLVED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ['manifest','template','artifact','bindings','provenance']:
        parser.add_argument('--'+field,type=Path,required=True)
    parser.add_argument('--expected-source',required=True)
    args=parser.parse_args()
    try:
        result=validate(read_json(args.manifest),expected_source=args.expected_source,template=args.template,
            artifact=args.artifact,bindings=args.bindings,provenance=read_json(args.provenance))
    except Exception:
        print('{"offline_manifest_consistent":false,"deployment_authorized":false}')
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
