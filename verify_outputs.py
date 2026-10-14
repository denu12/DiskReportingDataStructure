#!/usr/bin/env python3
"""Verify complete query outputs for a frozen theater queue against integer geometry.

Uses native full-query verification, not sampled admission or answer-count equality.
No arguments beyond --queue: preview only. --execute performs the checks serially.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time

CHEATING = 'esa_sprk_CHEATING_IDS_ONLY'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def header(path, format2d):
    with path.open('rb') as stream:
        if format2d:
            magic, points, queries = struct.unpack('<8sQQ', stream.read(24))
            if magic != b'ESA2D01\0':
                raise ValueError('Expected a static 2D input')
            return 2, points, queries
        dimension, points, queries = struct.unpack('<IQQ', stream.read(20))
        return dimension, points, queries


def verdict(result, returncode, expected_queries):
    if result.get('status') == 'incorrect':
        if result.get('membership_contract') == 'expanded_f64_ball' and not result.get('integer_mismatch_queries'):
            return 'inconclusive'
        return 'does_not_match'
    if returncode or result.get('status') != 'success':
        return 'inconclusive'
    if result.get('queries') != expected_queries:
        return 'inconclusive'
    if result.get('membership_contract') == 'expanded_f64_ball':
        mismatches = result.get('integer_mismatch_queries')
        if not isinstance(mismatches, int) or mismatches < 0:
            return 'inconclusive'
        if mismatches:
            return 'does_not_match'
    return 'matches_exact_integer_oracle'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True, help='Frozen results/_queue-... directory')
    parser.add_argument('--campaigns', nargs='+', help='Optional subset of campaigns from that queue')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--boundary-only', action='store_true', help='Check existing-style boundary/duplicate fixtures instead of campaign data')
    parser.add_argument('--timeout-seconds', type=int, default=180, help='Whole-job cap; unfinished checks are inconclusive')
    parser.add_argument('--wall-limit-seconds', type=int, default=7200, help='Total cap; remaining jobs are recorded as not checked')
    parser.add_argument('--cpu', type=int, default=1)
    parser.add_argument('--memory-gib', type=int, default=64)
    parser.add_argument('--run', help='Fresh report label')
    args = parser.parse_args()
    if min(args.timeout_seconds, args.wall_limit_seconds, args.memory_gib) <= 0:
        parser.error('Timeouts and memory must be positive')
    queue = args.queue.resolve()
    workspace = queue / 'workspace'
    plan = read(queue / 'plan.json')
    rosters = read(queue / 'status.json')['rosters']
    sys.path.insert(0, str(workspace / 'tools'))
    from backends import command as dimensional_command
    if (workspace / "tools/algorithm_backends_2d.py").exists():
        from algorithm_backends_2d import binary as binary_2d
    else:
        # Frozen historical queues retain their original binary routing.
        def binary_2d(algorithm):
            return "esa_runner_pargeo" if algorithm == "pargeo" else "esa_runner"
    from experiment_integrity import boundary_case
    available = {name for item in plan for name in item['campaigns']}
    if args.campaigns and set(args.campaigns) - available:
        parser.error('Campaign selection is not in this queue')
    specs = []
    for item in plan:
        for name in item['campaigns']:
            if args.campaigns and name not in args.campaigns:
                continue
            path = workspace / 'data' / name / 'campaign.json'
            manifest = read(path)
            format2d = name in {'scaling', 'input_scaling', 'radius_scaling', 'static'} or manifest.get('input_format') == 'ESA2D01'
            specs.append((name, path, manifest, format2d, rosters[item['theater']]))
    jobs = sum((1 if args.boundary_only else len(m['cases'])) * len(a) for _, _, m, _, a in specs)
    print(f'{jobs} serial full-output checks; one CPU, {args.memory_gib} GiB/job.')
    print('Each complete native verifier compares sorted coordinate multisets with an exact integer scan.')
    print('SPRK (cheating) integer disagreements count as mismatches here, despite floating-contract admission.')
    if not args.execute:
        print('Preview only; add --execute. Full inputs and all original queries are used by default.')
        return 0
    if sys.platform != 'linux' or args.cpu not in os.sched_getaffinity(0):
        parser.error('Execute on Archie with an available CPU')
    import fcntl
    results = workspace / 'results'
    lock = (results / '_theater-controller.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('An experiment controller is running; verification must run separately')
    label = args.run or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,48}', label):
        parser.error('Invalid report label')
    folder = results / ('_output-verification-' + label)
    folder.mkdir()  # Never overwrite an earlier verification.
    report = dict(status='running', queue=str(queue), scope='boundary fixtures' if args.boundary_only else 'all original points and queries',
                  algorithm_outputs='sorted original coordinate multisets, including duplicate occurrences',
                  all_outputs_match=None, planned_jobs=jobs, completed_jobs=0, results=[],
                  started_unix=time.time(), resources=dict(cpu=args.cpu,memory_gib=args.memory_gib,timeout_seconds=args.timeout_seconds,wall_limit_seconds=args.wall_limit_seconds),
                  manifests={name:sha(path) for name,path,_,_,_ in specs}, binaries={})
    target = folder / 'summary.json'
    save(target, report)
    deadline = time.monotonic() + args.wall_limit_seconds
    env = dict(os.environ, SFC_ESA_LIBRARY=str(workspace/'bin/esa2d/libsfc_esa2026.so'),
               PARLAY_NUM_THREADS='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', RAYON_NUM_THREADS='1')
    checked_files = {}
    for name, manifest_path, manifest, format2d, algorithms in specs:
        cases = [boundary_case(folder/'fixtures'/name, 2 if format2d else manifest['dimension'], format2d)] if args.boundary_only else manifest['cases']
        for case in cases:
            data = (manifest_path.parent / case['path']).resolve()
            for algorithm in algorithms:
                row = dict(campaign=name,case=case['id'],algorithm=algorithm,status='inconclusive')
                job = folder / 'jobs' / str(len(report['results']))
                job.mkdir(parents=True)
                unit = 'drr-output-check-' + label + '-' + str(len(report['results']))
                try:
                    remaining = deadline - time.monotonic()
                    if remaining < 1:
                        row['status']='not_checked_wall_limit'
                    else:
                        if data not in checked_files:
                            checked_files[data]=sha(data)
                        expected = case.get('sha256',case.get('conversion',{}).get('sha256'))
                        if not expected or checked_files[data]!=expected:
                            raise ValueError('Input checksum mismatch or missing checksum')
                        dimension, n, q = header(data, format2d)
                        row.update(input_sha256=checked_files[data],dimension=dimension,points=n,expected_queries=q)
                        result_path=job/'result.json'
                        if format2d:
                            binary=workspace/'bin/esa2d'/binary_2d(algorithm)
                            command=[str(binary),algorithm,str(data),'verify',str(result_path)]
                        else:
                            command=dimensional_command(algorithm)+[str(data),algorithm]  # Deliberately no --bench.
                        for binary in [Path(command[0]),*([workspace/'bin/esa2d/libsfc_esa2026.so'] if format2d else [])]:
                            if str(binary) not in report['binaries']:
                                report['binaries'][str(binary)]=sha(binary)
                        timeout=max(1,min(args.timeout_seconds,int(deadline-time.monotonic())))
                        wrapper=['systemd-run','--user','--quiet','--wait','--pipe','--unit='+unit,
                                 '--property=AllowedCPUs='+str(args.cpu),'--property=MemoryMax='+str(args.memory_gib)+'G',
                                 '--property=MemorySwapMax=0','--property=RuntimeMaxSec='+str(timeout),
                                 '--property=TimeoutStopSec=5',
                                 *['--setenv='+key+'='+env[key] for key in ['SFC_ESA_LIBRARY','PARLAY_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','RAYON_NUM_THREADS']],*command]
                        started=time.monotonic()
                        try:
                            process=subprocess.run(wrapper,cwd=workspace,env=env,text=True,capture_output=True,timeout=timeout+20)
                            (job/'stdout.txt').write_text(process.stdout);(job/'stderr.txt').write_text(process.stderr)
                            if format2d:
                                result=read(result_path) if result_path.exists() else {}
                            else:
                                lines=[line for line in process.stdout.splitlines() if line.startswith('{')]
                                result=json.loads(lines[-1]) if lines else {}
                            row.update(status=verdict(result,process.returncode,q),returncode=process.returncode,result=result)
                        except subprocess.TimeoutExpired:
                            subprocess.run(['systemctl','--user','stop',unit],check=False,capture_output=True)
                            row.update(status='inconclusive',reason='timeout')
                        row['wall_seconds']=time.monotonic()-started
                except Exception as error:
                    row.update(status='inconclusive',reason=str(error))
                report['results'].append(row)
                report['completed_jobs']=sum(r['status'] in {'matches_exact_integer_oracle','does_not_match'} for r in report['results'])
                report['outcomes']=dict(Counter(r['status'] for r in report['results']))
                save(target,report)
                print(f"{name} | {case['id']} | {algorithm}: {row['status']}",flush=True)
    statuses={r['status'] for r in report['results']}
    complete=not statuses-{'matches_exact_integer_oracle','does_not_match'}
    report.update(status='complete' if complete else 'incomplete',finished_unix=time.time(),
                  all_outputs_match=False if 'does_not_match' in statuses else True if complete else None)
    save(target,report)
    print(json.dumps({k:v for k,v in report.items() if k not in {'results','binaries','manifests'}},indent=2))
    print('Report:',target)
    return 1 if report['all_outputs_match'] is False else 0 if complete else 2


if __name__ == '__main__':
    raise SystemExit(main())
