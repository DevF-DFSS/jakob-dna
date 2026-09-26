"""Orchestrate existing offline entry points; never grant deployment authority."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def decision(codes, identical):
    return {'passed':all(c==0 for c in codes.values()) and identical,
            'deployment_authorized':False,'evidence_class':'GITHUB_CI_EXECUTION' if os.environ.get('GITHUB_ACTIONS')=='true' else 'LOCAL_EXECUTION'}


def main():
    root=Path(__file__).resolve().parents[3]
    candidate=root/'aws/isolated-v6';core=root/'reference/isolated-v6'
    output=Path(sys.argv[1]).resolve();output.mkdir(parents=True,exist_ok=True)
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    commands={'suite':[sys.executable,'-B',str(candidate/'tools/run_checks.py'),'--core',str(core)],
              'static_and_lint':[sys.executable,'-B',str(candidate/'tools/validate_offline.py')]}
    for name in ['a','b']:
        commands['build_'+name]=[sys.executable,'-B',str(candidate/'tools/build.py'),'--core',str(core),'--source-commit',sha,'--output',str(output/name),'--diagnostic-only']
    codes={}
    for name,cmd in commands.items():
        p=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
        codes[name]=p.returncode
        (output/(name+'.stdout')).write_text(p.stdout);(output/(name+'.stderr')).write_text(p.stderr)
        print(name,'exit',p.returncode,flush=True);print(p.stdout);print(p.stderr)
    identical=False;verified=0;hashes={};tests=None
    try:
        tests=json.loads((output/'suite.stdout').read_text())
        identical=all((output/'a'/n).read_bytes()==(output/'b'/n).read_bytes() for n in ['isolated-v6-candidate.zip','provenance.json'])
        m=json.loads((output/'a/provenance.json').read_text())
        assert m['source_commit']==sha
        for e in m['source_inputs']:
            b=subprocess.check_output(['git','show',sha+':'+e['path']],cwd=root)
            assert hashlib.sha256(b).hexdigest()==e['sha256'];verified+=1
        hashes={k:m[k] for k in ['artifact_sha256','template_sha256','bootstrap_sha256','binding_sha256']}
        hashes['provenance_sha256']=hashlib.sha256((output/'a/provenance.json').read_bytes()).hexdigest()
    except (OSError,ValueError,KeyError,AssertionError,subprocess.CalledProcessError):
        identical=False;codes['source_or_build_verification']=1
    result={**decision(codes,identical),'commit':sha,'python':sys.version,'exit_codes':codes,'tests':tests,
            'workflow_sha256':hashlib.sha256((root/'.github/workflows/v6-evidence.yml').read_bytes()).hexdigest(),'two_builds_identical':identical,'source_inputs_verified':verified,'hashes':hashes,
            'limits':'Execution evidence only; not authenticated authorization, AWS live state or recovery proof.'}
    text=json.dumps(result,indent=2,sort_keys=True);(output/'summary.json').write_text(text+'\n');print(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write('## V6 offline execution evidence\n```json\n'+text+'\n```\n')
    return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
