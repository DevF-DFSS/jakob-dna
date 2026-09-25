"""Offline, common-field comparison. Missing observations stay unresolved."""
import json
import sys
from pathlib import Path


def project(value, example):
    if isinstance(example, dict):
        return {k: project(value.get(k), v) for k, v in example.items()}
    if isinstance(example, list):
        if not example:
            return value
        if not isinstance(value, list):
            return value
        return [project(v, example[0]) for v in value]
    return value


def compare(old, new):
    rows = []
    def record(kind, region, name, before, after):
        rows.append(dict(kind=kind, region=region, name=name, before=before, after=after,
                         delta='unchanged' if before == after else 'changed'))
    current = {r['region']: r for r in new['batch2']['snapshot']['regions']}
    for previous in old['details']['regions']:
        region = previous['region']
        now = current.get(region)
        if now is None:
            rows.append(dict(region=region, delta='🐈📦 UNRESOLVED'))
            continue
        fs = {f['configuration']['FunctionName']: f for f in now['functions']}
        for f in previous['functions']:
            if f['FunctionName'] not in fs:
                rows.append(dict(kind='function', name=f['FunctionName'], delta='no longer observed'))
                continue
            nf = fs[f['FunctionName']]
            keys = ['FunctionName','Runtime','Handler','Role','CodeSha256','CodeSize','LastModified',
                    'PackageType','Architectures','State','LastUpdateStatus','Timeout','MemorySize','environment_names']
            record('function',region,f['FunctionName'],{k:f[k] for k in keys},{k:nf['configuration'][k] for k in keys})
            record('invoke_policy',region,f['FunctionName'],f['invoke_policy'],json.loads(nf['policy']['Policy']))
            record('aliases',region,f['FunctionName'],f['aliases'],nf['aliases']['Aliases'])
        ts = {t['TableName']: t for t in now['tables']}
        for t in previous['tables']:
            keys = ['TableName','KeySchema','AttributeDefinitions','TableStatus']
            before = {k:t[k] for k in keys}
            record('table',region,t['TableName'],before,project(ts.get(t['TableName'],{}),before))
        apis = {a['api']['ApiId']: a for a in now['apis']}
        for a in previous['apis']:
            n = apis.get(a['id'])
            if n is None:
                rows.append(dict(kind='api',name=a['id'],delta='no longer observed'))
                continue
            for field in ['routes','integrations','stages','authorizers']:
                record('api_'+field,region,a['id'],a[field],project(n[field]['Items'],a[field]))
    return rows

if __name__ == '__main__':
    old, new = (json.loads(Path(p).read_text()) for p in sys.argv[1:3])
    print(json.dumps(compare(old,new), indent=2, ensure_ascii=False))
