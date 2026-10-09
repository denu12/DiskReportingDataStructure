"""Estimate final wall time from screening and freeze a common workload selection."""
import argparse
import hashlib
import json
from pathlib import Path
from budget import policy, save


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--run', default='default')
    p.add_argument('--campaigns', nargs='+', default=['scaling', 'static', 'dynamic-circles'],
                   choices=['scaling', 'static', 'dynamic-circles'])
    p.add_argument('--matrix', type=Path, help='JSON mapping each campaign to case IDs; same cases for every algorithm')
    args = p.parse_args()
    if Path(args.run).name != args.run or args.run in ('', '.', '..'):
        p.error('--run must be a single directory name')
    config = policy(args.base)
    matrix = json.loads(args.matrix.read_text()) if args.matrix else None
    if matrix is not None and set(matrix) != set(args.campaigns):
        p.error('The matrix must list exactly the selected campaigns')
    output = {'run': args.run, 'campaigns': {}, 'estimated_seconds': 0,
              'budget_seconds': config['stages']['final']['budget_seconds'],
              'estimation': 'screen wall times, three repetitions, 25% margin; estimate, not a guarantee'}
    if any((args.base / 'results' / name / args.run / 'final/state.json').exists()
           for name in ['scaling', 'static', 'dynamic-circles']):
        raise RuntimeError('Final measurements already exist; their workload plan cannot be changed')
    for name in args.campaigns:
        path = args.base / 'results' / name / args.run / 'screen/state.json'
        screen = json.loads(path.read_text())
        if screen['status'] == 'running':
            raise RuntimeError('Screening is still running')
        rows = screen['results']
        known = {r['case'] for r in rows}
        cases = set(matrix[name]) if matrix is not None else known
        if not cases <= known:
            raise RuntimeError(f'Unknown cases in {name}: {sorted(cases-known)}')
        totals = {}
        jobs = 0
        for row in rows:
            if row['case'] in cases and row['status'] == 'success':
                totals[row['algorithm']] = totals.get(row['algorithm'], 0) + row['wall_seconds'] * config['repetitions'] * 1.25
                jobs += config['repetitions']
        workers = min(config['stages']['final']['workers'], len(screen['identity']['cpus']))
        loads = [0.0] * workers
        # The runner assigns one algorithm's sequence to each available worker.
        for seconds in totals.values():
            i = loads.index(min(loads))
            loads[i] += seconds
        estimate = max(loads)
        output['estimated_seconds'] += estimate
        output['campaigns'][name] = dict(cases=sorted(cases), jobs=jobs,
            estimated_seconds=estimate, screen_sha256=file_hash(path))
    ledger_path = args.base / 'results/_budgets' / (args.run + '.json')
    used = json.loads(ledger_path.read_text())['stages'].get('final', 0) if ledger_path.exists() else 0
    output['remaining_seconds'] = max(0, output['budget_seconds'] - used)
    output['fits_budget'] = output['estimated_seconds'] <= output['remaining_seconds']
    save(args.base / 'results/_plans' / (args.run + '.json'), output)
    print(json.dumps(output, indent=2))
    if not output['fits_budget']:
        raise SystemExit('Estimate exceeds the final budget. Reduce the common case matrix with --matrix before running final.')


if __name__ == '__main__':
    main()
