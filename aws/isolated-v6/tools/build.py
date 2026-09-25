"""Offline deterministic ZIP builder. Source attribution is externally verified.

No downloading, SDK construction, credential discovery, signing, or uploading.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def build(core, candidate, output, source_commit, run_tests=True, wheelhouse=None):
    if not re.fullmatch('[0-9a-f]{40}', source_commit):
        raise ValueError('full_source_commit_required')
    if sys.version_info[:2] != (3,13):
        raise RuntimeError('python_3_13_required')
    files={}
    for root, name in [(core/'isolated_v6','isolated_v6'), (candidate/'aws_v6','aws_v6')]:
        for path in sorted(root.glob('*.py')):
            if path.is_symlink(): raise ValueError('symlink_not_allowed')
            files[name+'/'+path.name]=path.read_bytes()
    if not files: raise ValueError('empty_package')
    files['aws_v6/bindings.json']=(candidate/'aws_v6/bindings.json').read_bytes()
    dependencies=json.loads((candidate/'dependencies.lock.json').read_text())
    wheelhouse=Path(wheelhouse) if wheelhouse else candidate/'wheelhouse'
    for dependency in dependencies:
        wheel=wheelhouse/dependency['filename']
        if hashlib.sha256(wheel.read_bytes()).hexdigest()!=dependency['sha256']:
            raise ValueError('wheel_hash_mismatch')
        with zipfile.ZipFile(wheel) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith('/'): continue
                if name.startswith('/') or '..' in Path(name).parts: raise ValueError('invalid_wheel_path')
                if '.data/' in name:
                    # CLI scripts are not needed by the Lambda runtime.
                    if '.data/scripts/' in name: continue
                    raise ValueError('unsupported_wheel_data')
                if name in files: raise ValueError('package_collision')
                files[name]=archive.read(name)
    tests={'passed':False,'status':'not_run'}
    if run_tests:
        completed=subprocess.run([sys.executable,'-B',str(candidate/'tools/run_checks.py'),'--core',str(core)],
            check=True, capture_output=True, text=True)
        tests=json.loads(completed.stdout)
        if not tests['passed']: raise RuntimeError('checks_failed')
        subprocess.run([sys.executable,'-B',str(candidate/'tools/lint_offline.py'),'-t',str(candidate/'infra/template.json'),'-r','us-east-1'],check=True,capture_output=True,text=True)
    output.mkdir(parents=True,exist_ok=True)
    artifact=output/'isolated-v6-candidate.zip'
    with zipfile.ZipFile(artifact,'w',compression=zipfile.ZIP_STORED) as archive:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            info.create_system=3; info.external_attr=0o100644 << 16
            archive.writestr(info,data)
    included=[{'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)} for name,data in sorted(files.items())]
    # Hash the test/tool/template inputs too, not just the runtime ZIP.
    evidence=[]
    for root,prefix in [(core,'reference/isolated-v6'),(candidate,'aws/isolated-v6')]:
        for path in sorted(root.rglob('*')):
            allowed = {'isolated_v6','tests','README.md'} if root == core else {'aws_v6','tests','tools','infra','release','README.md','PREFLIGHT.md','dependencies.lock.json','requirements.lock','validation-toolchain.lock'}
            if (path.is_file() and path.relative_to(root).parts[0] in allowed and
                    path.suffix in ('.py','.json','.md','.lock') and '__pycache__' not in path.parts):
                evidence.append({'path':prefix+'/'+str(path.relative_to(root)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'source_commit':source_commit,'source_binding':'caller-supplied commit; verify every input hash against that Git tree before deployment',
        'runtime_target':'python3.13','architecture':'x86_64','build_python':sys.version.split()[0],
        'dependencies':{'third_party':{d['name']:d['version'] for d in dependencies},'wheels':dependencies},
        'included_files':included,'source_inputs':evidence,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'template_sha256':hashlib.sha256((candidate/'infra/template.json').read_bytes()).hexdigest(),
        'binding_sha256':hashlib.sha256((candidate/'aws_v6/bindings.json').read_bytes()).hexdigest(),
        'release_manifest':'UNAPPROVED; offline consistency is not deployment authorization',
        'tests':tests,'cloudformation':{'tool':'cfn-lint','version':importlib.metadata.version('cfn-lint'),'region_schema':'us-east-1','passed':bool(run_tests),'network':'blocked'},'activation':'composition root wired; packaged bindings intentionally unconfigured; AWS trust unproven'}
    (output/'provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--wheelhouse',type=Path)
    args=parser.parse_args()
    manifest=build(args.core.resolve(),Path(__file__).resolve().parents[1],args.output.resolve(),args.source_commit,wheelhouse=args.wheelhouse)
    print(json.dumps({'sha256':manifest['artifact_sha256'],'tests':manifest['tests']},sort_keys=True))

if __name__=='__main__':
    main()
