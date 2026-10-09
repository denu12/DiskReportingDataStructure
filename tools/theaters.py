"""Describe theaters and their campaign definitions; launches no experiments."""
import argparse
import json
from pathlib import Path
from campaign_paths import campaign_directory, theater_manifests
ROOT = Path(__file__).resolve().parents[1]


def case_count(spec):
    if 'cases' in spec: return len(spec['cases'])
    if 'expected_instances' in spec: return spec['expected_instances']
    total = 0
    for suite in spec.get('suites', {}).values():
        count = 1
        for field in ['sizes', 'distributions', 'radii', 'update_ratios']:
            count *= len(suite.get(field, [None]))
        total += count
    return total*len(spec.get('seeds', [None]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--theater', help='Filter by theater ID')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(); rows = []
    for path, theater in theater_manifests(ROOT):
        if args.theater and args.theater != theater['name']: continue
        campaigns = []
        for name in theater['campaigns']:
            definition = campaign_directory(ROOT, name)/'campaign.json'
            spec = json.loads(definition.read_text(encoding='utf-8-sig'))
            campaigns.append(dict(name=name, instances=case_count(spec), definition=definition.relative_to(ROOT).as_posix()))
        rows.append(dict(name=theater['name'], title=theater['title'], campaigns=campaigns))
    if args.theater and not rows: ap.error('Unknown theater')
    if args.json: print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(row['name']+' theater')
            for c in row['campaigns']: print('  '+c['name']+': '+str(c['instances'])+' instances')
if __name__ == '__main__': main()
