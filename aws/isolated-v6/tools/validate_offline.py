"""Offline diagnostics; nonzero lint results remain failures, never waivers."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from isolation_security import check_bootstrap
from security import check


def validate(candidate):
    check(json.loads((candidate/'infra/template.json').read_text()))
    check_bootstrap(json.loads((candidate/'infra/bootstrap.json').read_text()))
    runs=[]
    for region in ['us-east-1','eu-west-1']:
        proc=subprocess.run([sys.executable,'-B',str(candidate/'tools/lint_offline.py'),'-t',
            str(candidate/'infra/template.json'),str(candidate/'infra/bootstrap.json'),'-r',region,'-f','json'],capture_output=True,text=True)
        findings=json.loads(proc.stdout or '[]')
        if proc.stderr: raise RuntimeError('unexpected_linter_stderr')
        for finding in findings:
            finding['Filename']=Path(finding['Filename']).name
        runs.append({'region_schema':region,'exit_code':proc.returncode,'findings':findings})
    return {'tool':'cfn-lint','version':importlib.metadata.version('cfn-lint'),
        'passed':all(r['exit_code']==0 for r in runs),'runs':runs,'static_security':'passed',
        'network':'socket and credential discovery blocked',
        'deployment_authorized':False,'schema_discrepancy':'UNRESOLVED: FunctionResourceArn reference vs ResourceArn examples/CDK/local schema'}


if __name__=='__main__':
    result=validate(Path(__file__).resolve().parents[1])
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result['passed'] else 1)
