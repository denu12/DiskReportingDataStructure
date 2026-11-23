"""Export only explicitly selected runs; never backfill a failed version."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys


def validate(selection):
    seen = set()
    for pair in selection['pairs']:
        key = pair['campaign'], pair['algorithm'], pair['case']
        if key in seen:
            raise ValueError('Duplicate selected case: ' + str(key))
        seen.add(key)
        if not pair.get('version') or not pair.get('run'):
            raise ValueError('Every selected case needs an explicit version and run')
        rows = pair['rows']
        if hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest() != pair['rows_sha256']:
            raise ValueError('Selected evidence changed: ' + str(key))
        final = [r for r in rows if r['phase'] == 'final' and r['status'] in
                 ('success', 'incorrect', 'answer_count_mismatch') and
                 isinstance((r.get('result') or r).get('query_seconds'), (float, int))]
        complete = len({r.get('repetition') for r in final}) >= 3
        timeout = any('timeout' in r['status'] for r in rows)
        if pair['outcome'] == 'complete' and not complete:
            raise ValueError('Incomplete final repetitions: ' + str(key))
        if pair['outcome'] == 'timeout_resolved' and not timeout:
            raise ValueError('Timeout outcome lacks timeout evidence: ' + str(key))
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('selection', type=Path)
    parser.add_argument('--csv', action='store_true')
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text())
    count = validate(selection)
    if not args.csv:
        print(json.dumps(dict(selected_cases=count, summary=selection['summary']), indent=2))
        return
    fields = ['campaign', 'algorithm', 'case', 'version', 'run', 'outcome',
              'phase', 'repetition', 'status', 'correctness_admission',
              'output_contract', 'membership_contract', 'build_seconds', 'query_seconds']
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    for pair in selection['pairs']:
        for row in pair['rows']:
            # A selected timeout has no numeric score; retain its evidence only.
            if pair['outcome'] != 'complete' and row['status'] == 'success':
                continue
            merged = {**row, **(row.get('result') or {}),
                      **{key: pair[key] for key in ('campaign','algorithm','case','version','run','outcome')}}
            writer.writerow({key: merged.get(key, '') for key in fields})


if __name__ == '__main__':
    main()
