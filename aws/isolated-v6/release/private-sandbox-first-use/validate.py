"""Offline consistency check for a deliberately BLOCKED first-use package.

This verifies bytes/shape and refuses an approval-like state. It cannot decide
whether an AWS principal exists or a human authorized any write.
"""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
CANDIDATE=HERE.parents[1]


def read(name):return json.loads((HERE/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    c=read('FROZEN_COORDINATE.json');m=read('BOOTSTRAP_MUTATION_MANIFEST.json');l=read('AWS_READ_LEDGER.json')
    assert c['schema_version']=='jel-v6-private-first-use-coordinate/1'
    assert m['schema_version']=='jel-v6-first-bootstrap-mutation/1'
    assert c['status']=='PROPOSED_UNAPPROVED' and m['status']=='BLOCKED_FIRST_WRITER'
    assert not c['deployment_authorized'] and not m['deployment_authorized'] and not m['aws_mutation_performed']
    assert not c['roles_created'] and not c['account_human_approved'] and m['human_authorization'] is None
    assert not m['operator']['exists_and_approved'] and m['operator']['observed_arn'] is None
    assert not m['cloudformation_service_role']['exists_and_approved'] and m['cloudformation_service_role']['observed_arn'] is None
    assert c['account_id']==m['account_id']==l['account']=='083127296577'
    assert c['region']==m['region']==l['region']=='us-east-1'
    assert c['namespace']==m['namespace']=='trident27'
    assert re.fullmatch('[0-9a-f]{40}',c['candidate_source_commit'])
    assert c['candidate_source_commit']==m['candidate_source_commit']
    for k,v in c['phase_template_sha256'].items():
        assert v==sha(CANDIDATE/'infra/phases'/f'{k}.json')
    assert m['bootstrap_template_sha256']==c['phase_template_sha256']['bootstrap']
    assert c['closed_capability_sha256']==sha(CANDIDATE/'aws_v6/capability.json')
    assert c['binding_sha256']==sha(CANDIDATE/'aws_v6/bindings.json')
    assert json.loads((CANDIDATE/'aws_v6/capability.json').read_text())['mode']=='CLOSED'
    assert c['artifact']['key']=='releases/'+c['artifact_sha256']+'.zip'
    assert c['artifact']['object_version'] is None and m['artifact_version'] is None
    assert m['stack_name']==c['stack_names']['bootstrap']
    assert m['parameters']=={'RuntimeStackName':c['stack_names']['runtime'],
        'ApprovedRecoveryRoleArn':c['proposed_role_arns']['recovery_operator'],
        'Namespace':c['namespace'],
        'BootstrapServiceRoleArn':c['proposed_role_arns']['bootstrap_service']}
    assert m['operator']['proposed_arn']==c['proposed_role_arns']['bootstrap_operator']
    assert m['cloudformation_service_role']['proposed_arn']==c['proposed_role_arns']['bootstrap_service']
    template=json.loads((CANDIDATE/'infra/phases/bootstrap.json').read_text())
    assert set(template['Parameters'])==set(m['parameters'])
    assert sorted(m['expected_resource_types'])==sorted(x['Type'] for x in template['Resources'].values())
    assert all(not x['Type'].startswith(('AWS::Lambda::','AWS::DynamoDB::','AWS::IAM::')) for x in template['Resources'].values())
    assert len(l['pre_api_validation_failures'])==l['totals']['pre_api_validation_failures']==10
    assert len(l['api_calls'])==l['totals']['aws_service_attempted']==28
    assert sum(x['status']=='SUCCESS' for x in l['api_calls'])==l['totals']['aws_service_successful']==27
    assert l['totals']['aws_service_failed']==1 and l['totals']['aws_mutations']==0
    assert not l['deployment_authorized']
    return {'status':'CONSISTENT_BUT_BLOCKED','deployment_authorized':False,'first_live_mutation_fully_specified':False,
            'reason':'No approved non-root first writer or bootstrap CF service role exists.'}


if __name__=='__main__':
    try:print(json.dumps(check(),sort_keys=True))
    except (AssertionError,KeyError,ValueError,TypeError,OSError):
        print(json.dumps({'status':'INVALID','deployment_authorized':False}));raise SystemExit(1)
