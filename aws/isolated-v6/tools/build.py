"""Offline deterministic ZIP builder. Source attribution is externally verified.

No downloading, SDK construction, credential discovery, signing, or uploading.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def build(core, candidate, output, source_commit, run_tests=True):
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
    tests={'passed':False,'status':'not_run'}
    if run_tests:
        completed=subprocess.run([sys.executable,'-B',str(candidate/'tools/run_checks.py'),'--core',str(core)],
            check=True, capture_output=True, text=True)
        tests=json.loads(completed.stdout)
        if not tests['passed']: raise RuntimeError('checks_failed')
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
            allowed = {'isolated_v6','tests','README.md'} if root == core else {'aws_v6','tests','tools','infra','README.md'}
            if (path.is_file() and path.relative_to(root).parts[0] in allowed and
                    path.suffix in ('.py','.json','.md') and '__pycache__' not in path.parts):
                evidence.append({'path':prefix+'/'+str(path.relative_to(root)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'source_commit':source_commit,'source_binding':'caller-supplied commit; verify every input hash against that Git tree before deployment',
        'runtime_target':'python3.13','architecture':'x86_64','build_python':sys.version.split()[0],
        'dependencies':{'third_party':{},'aws_sdk':'not bundled or imported; low-level client is injected; SDK selection/pinning unresolved'},
        'included_files':included,'source_inputs':evidence,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'tests':tests,'activation':'deny-all packaged entry point; authentication/SDK composition unresolved'}
    (output/'provenance.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    args=parser.parse_args()
    manifest=build(args.core.resolve(),Path(__file__).resolve().parents[1],args.output.resolve(),args.source_commit)
    print(json.dumps({'sha256':manifest['artifact_sha256'],'tests':manifest['tests']},sort_keys=True))

if __name__=='__main__':
    main()
