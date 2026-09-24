"""Compare source expectations with supplied inventory; no SDK, network, or writes."""
import argparse
import json
from pathlib import Path

def compare(expected, inventory):
    results=[]
    for resource in expected:
        matches=[r for r in inventory.get('resources',[]) if r.get('service')==resource['service'] and r.get('name')==resource['name'] and (resource.get('region') is None or r.get('region')==resource['region'])]
        evidenced=[r for r in matches if all(r.get(k) for k in ('account','region','observed_at','evidence_ref'))]
        results.append({**resource,'status':'OBSERVED_IN_SUPPLIED_INVENTORY' if evidenced else '🐈📦 UNRESOLVED','observations':[{k:r[k] for k in ('account','region','observed_at','evidence_ref')} for r in evidenced],'note':'Name match is not deployment lineage proof; timestamp freshness requires review.' if evidenced else 'Missing observation or provenance does not prove absence.'})
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory',type=Path)
    args=parser.parse_args()
    expected=json.loads(Path(__file__).with_name('expected_resources.json').read_text())
    inventory=json.loads(args.inventory.read_text())
    print(json.dumps(compare(expected,inventory),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
