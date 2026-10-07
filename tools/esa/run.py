"""Run one new ESA campaign with shared budgets and fresh correctness admission."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import sys
import sysconfig
import threading
import time
from catalog import ROOT, save, sha

sys.path.insert(0, str(ROOT/'tools'))
from budget import budget, policy
from run_ddim_all import command as ddim_command

COMPILED_DIMS = set(range(2, 17)) | {32}
DYNAMIC_DIMENSION = {'ann_fr', 'cgal_kd', 'esa_nanoflann', 'esa_sklearn_kd',
                     'esa_sklearn_ball', 'esa_snn', 'brute_force'}


def supported(algorithm, case, format2d):
    return format2d or algorithm in DYNAMIC_DIMENSION or case['dimension'] in COMPILED_DIMS


def backend(algorithm, format2d, bindir):
    if format2d:
        return [str(bindir/('esa_runner_pargeo' if algorithm == 'pargeo' else 'esa_runner'))]
    return ddim_command(algorithm)


def sample(original, target, format2d):
    """Keep all original points and up to 32 evenly spaced original queries."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with original.open('rb') as src, target.open('wb') as dst:
        if format2d:
            magic, n, q = struct.unpack('<8sQQ', src.read(24)); d = 2
            if magic != b'ESA2D01\0': raise ValueError('Bad input header')
        else:
            d, n, q = struct.unpack('<IQQ', src.read(20))
        count = min(q, 32)
        dst.write(struct.pack('<8sQQ', magic, n, count) if format2d else struct.pack('<IQQ', d, n, count))
        left = n*d*4
        while left:
            chunk = src.read(min(left, 1024*1024))
            if not chunk: raise ValueError('Truncated points')
            dst.write(chunk); left -= len(chunk)
        start = src.tell(); width = 4*d+16
        for i in range(count):
            at = i*(q-1)//(count-1) if count > 1 else 0
            src.seek(start+at*width); row = src.read(width)
            if len(row) != width: raise ValueError('Truncated queries')
            dst.write(row)
    return count


def run_phase(args, manifest):
    config = policy(ROOT); stage = config['stages'][args.phase]
    folder = ROOT/'results'/args.campaign/args.run
    target = folder/args.phase/'state.json'
    if target.exists(): raise RuntimeError('Phase already exists; use a fresh run label')
    if (folder/'STOP').exists(): raise RuntimeError('This run is stopped')
    if manifest.get('status') != 'ready': raise RuntimeError('Campaign has missing data; prepare every case first')
    if manifest.get('specification_sha256') != sha(ROOT/'campaigns'/args.campaign/'campaign.json'):
        raise RuntimeError('Prepared campaign specification is stale; prepare it again')
    cases = manifest['cases']; algorithms = manifest['algorithms']
    format2d = manifest['input_format'] == 'ESA2D01'
    data = ROOT/'data'/args.campaign
    cpus = config['cpus']
    cores = [(Path(f'/sys/devices/system/cpu/cpu{c}/topology/physical_package_id').read_text(),
              Path(f'/sys/devices/system/cpu/cpu{c}/topology/core_id').read_text()) for c in cpus]
    if len(set(cores)) != len(cores) or not set(cpus) <= os.sched_getaffinity(0):
        raise RuntimeError('Configured CPUs must be distinct available physical cores')
    paths = {p for a in algorithms for p in backend(a, format2d, args.bin_dir)}
    if format2d: paths.add(str(args.bin_dir/'libsfc_esa2026.so'))
    if not all(Path(p).is_file() for p in paths): raise RuntimeError('Build the campaign backends first')
    identity = dict(manifest=sha(data/'campaign.json'), policy=sha(ROOT/'campaigns/execution.json'),
        binaries={p: sha(Path(p)) for p in sorted(paths)},
        harness={str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT/'tools/esa').glob('*.py'))})
    for p in [ROOT/'tools/budget.py', ROOT/'tools/run_ddim_all.py', ROOT/'src/third_party/esa2026/snnpy.py']:
        if p.is_file(): identity['harness'][str(p.relative_to(ROOT))] = sha(p)
    for p in (ROOT/'src/third_party/esa2026/snnpy').rglob('*.py'):
        identity['harness'][str(p.relative_to(ROOT))] = sha(p)
    identity['python_packages'] = {}
    for name in ['numpy', 'scipy', 'scikit-learn']:
        try: identity['python_packages'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: identity['python_packages'][name] = None
    for c in cases:
        if sha(data/c['path']) != c['sha256']: raise RuntimeError('Input checksum mismatch: '+c['id'])
    eligible = set(algorithms)
    measured = None
    if args.phase != 'correctness':
        gate = json.loads((folder/'correctness/state.json').read_text())
        if gate['identity'] != identity or gate['status'] != 'complete': raise RuntimeError('Correctness gate incomplete or stale')
        eligible = {a for a, v in gate['eligibility'].items() if v == 'passed'}
    if args.phase == 'correctness':
        smallest = {}
        for c in sorted(cases, key=lambda c: (c['n'], c['id'])): smallest.setdefault(c['dimension'], c)
        selected = list(smallest.values())
    else: selected = cases
    repetitions = config['repetitions'] if args.phase == 'final' else 1
    if args.phase == 'final':
        screen = json.loads((folder/'screen/state.json').read_text())
        if screen['identity'] != identity or screen['status'] != 'complete': raise RuntimeError('Screen is incomplete or stale')
        measured = {(r['algorithm'], r['case']) for r in screen['results'] if r['status'] == 'success'}
        loads = [0.0]*min(stage['workers'], len(cpus))
        for i, a in enumerate(algorithms):
            cost = sum(r.get('wall_seconds', 0)*repetitions*1.25 for r in screen['results'] if r['algorithm'] == a and r['status'] == 'success')
            loads[i % len(loads)] += cost
        estimate = max(loads)
        remaining = args.deadline-time.monotonic()
        save(folder/'plan.json', dict(estimated_seconds=estimate, remaining_seconds=remaining,
             fits_budget=estimate <= remaining, basis='screen wall times, repetitions and 25 percent margin'))
        if estimate > remaining: raise RuntimeError('Final estimate exceeds remaining shared budget')
    env = os.environ.copy()
    for k in ['OMP_NUM_THREADS', 'OMP_THREAD_LIMIT', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'PARLAY_NUM_THREADS', 'RAYON_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS']: env[k] = '1'
    env['PYTHONPATH'] = str(ROOT/'src/third_party/esa2026')+os.pathsep+sysconfig.get_path('purelib')+os.pathsep+env.get('PYTHONPATH', '')
    env['SFC_ESA_LIBRARY'] = str(args.bin_dir/'libsfc_esa2026.so')
    env['LD_LIBRARY_PATH'] = str(ROOT/'bin/lib')+os.pathsep+env.get('LD_LIBRARY_PATH', '')
    subprocess.run(['systemctl', '--user', 'set-property', '--runtime', 'esa2d-bench.slice',
                    f'MemoryMax={config["aggregate_memory_gib"]}G', 'MemorySwapMax=0'], check=True)
    state = dict(status='running', phase=args.phase, identity=identity, results=[], eligibility={},
                 started_unix=time.time(), current={})
    lock = threading.Lock(); stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set()); signal.signal(signal.SIGINT, lambda *_: stopped.set())
    save(target, state)
    def record(row):
        with lock:
            state['results'].append(row); state['outcomes'] = dict(Counter(r['status'] for r in state['results']))
            save(target, state)
    def algorithm_task(a, cpu):
        checked = []
        for c in selected:
            for rep in range(repetitions):
                row = dict(algorithm=a, case=c['id'], dimension=c['dimension'], repetition=rep, cpu=cpu)
                status = None
                if not supported(a, c, format2d): status = 'unsupported_dimension'
                elif a not in eligible: status = 'excluded_by_correctness'
                elif measured is not None and (a, c['id']) not in measured: status = 'not_selected_after_screen'
                elif stopped.is_set() or (folder/'STOP').exists(): status = 'stopped'
                elif time.monotonic()+stage['timeout_seconds'] > args.deadline: status = 'not_run_budget'
                if status:
                    row['status'] = status; record(row); continue
                key = hashlib.sha256(json.dumps([a, c['id'], rep]).encode()).hexdigest()[:16]
                job = folder/args.phase/'jobs'/key; job.mkdir(parents=True)
                input_path = data/c['path']; expected = c['queries']
                if args.phase == 'correctness':
                    input_path = job/'ordinary-input.bin'; expected = sample(data/c['path'], input_path, format2d)
                result = job/'result.json'; native = backend(a, format2d, args.bin_dir)
                if format2d: native += [a, str(input_path), 'verify' if args.phase == 'correctness' else 'bench', str(result)]
                else: native += [str(input_path), a]+([] if args.phase == 'correctness' else ['--bench'])
                unit = f'esa-family-{os.getpid()}-{key}'
                cmd = ['systemd-run', '--user', '--wait', '--pipe', '--collect', '--unit='+unit, '--slice=esa2d-bench.slice',
                       '-p', f'CPUAffinity={cpu}', '-p', f'MemoryMax={config["memory_gib"]}G', '-p', 'MemorySwapMax=0',
                       '-p', 'OOMPolicy=kill', '-p', 'KillMode=control-group', '-p', 'TimeoutStopSec=2',
                       '-p', f'RuntimeMaxSec={stage["timeout_seconds"]}s', '/usr/bin/env']
                cmd += [k+'='+v for k, v in env.items() if k.endswith('_NUM_THREADS') or k in ['OMP_THREAD_LIMIT', 'PYTHONPATH', 'LD_LIBRARY_PATH', 'SFC_ESA_LIBRARY']]+native
                start = time.monotonic()
                with (job/'run.log').open('w') as log:
                    process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                    with lock: state['current'][str(cpu)] = [a, c['id']]; save(target, state)
                    while process.poll() is None:
                        if stopped.is_set() or (folder/'STOP').exists() or time.monotonic() > args.deadline or time.monotonic()-start > stage['timeout_seconds']+3:
                            subprocess.run(['systemctl', '--user', 'stop', unit], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        time.sleep(.15)
                text = (job/'run.log').read_text(); report = None
                if result.exists(): report = json.loads(result.read_text())
                elif not format2d:
                    for line in reversed(text.splitlines()):
                        try:
                            item = json.loads(line)
                            if isinstance(item, dict) and 'status' in item: report = item; break
                        except ValueError: pass
                if stopped.is_set() or (folder/'STOP').exists(): outcome = 'stopped'
                elif 'timeout' in text.lower() or time.monotonic()-start > stage['timeout_seconds']: outcome = 'timeout'
                elif 'oom-kill' in text.lower(): outcome = 'memory'
                elif 'core-dump' in text.lower() or 'code=dumped' in text.lower(): outcome = 'crash'
                elif report and report.get('status') == 'incorrect': outcome = 'incorrect'
                elif process.returncode == 0 and report and report.get('queries') == expected and report.get('status') == 'success': outcome = 'success'
                else: outcome = 'error'
                # The common CSV collector merges result fields into the row;
                # keep the controller's timeout/error classification authoritative.
                measurements = ({k: v for k, v in report.items() if k != 'status'} if report else None)
                row.update(status=outcome, wall_seconds=time.monotonic()-start, result=measurements,
                           backend_status=report.get('status') if report else None, returncode=process.returncode)
                save(job/'outcome.json', row); record(row); checked.append(outcome)
                with lock: state['current'].pop(str(cpu), None); save(target, state)
                print(args.phase, a, c['id'], outcome, flush=True)
                if outcome != 'success': break
        if args.phase == 'correctness':
            with lock:
                state['eligibility'][a] = 'unsupported_dimension' if not checked else 'passed' if all(v == 'success' for v in checked) else 'excluded'
                save(target, state)
    # Each worker owns one physical core and processes complete algorithm sequences.
    assignments = [[] for _ in range(min(stage['workers'], len(cpus)))]
    for i, a in enumerate(algorithms): assignments[i % len(assignments)].append(a)
    def worker(i):
        for a in assignments[i]: algorithm_task(a, cpus[i])
    with ThreadPoolExecutor(max_workers=len(assignments)) as pool:
        list(pool.map(worker, range(len(assignments))))
    statuses = {r['status'] for r in state['results']}
    state['status'] = 'stopped' if 'stopped' in statuses else 'budget_exhausted' if 'not_run_budget' in statuses else 'complete'
    state['needs_attention'] = bool(statuses-{'success', 'unsupported_dimension', 'excluded_by_correctness', 'not_selected_after_screen'})
    state['finished_unix'] = time.time(); save(target, state)
    if state['status'] != 'complete': raise RuntimeError('Phase did not complete: '+state['status'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign', required=True); ap.add_argument('--run', required=True)
    ap.add_argument('--phase', choices=['correctness', 'screen', 'final', 'all'], default='all')
    ap.add_argument('--describe', action='store_true', help='Report input and dimension coverage; launch nothing')
    ap.add_argument('--bin-dir', type=Path, default=ROOT/'bin/esa2d')
    args = ap.parse_args()
    index = json.loads((ROOT/'campaigns/esa-campaigns.json').read_text())
    if args.campaign not in [c['name'] for c in index['full']+index['native_2d']]: ap.error('Unknown ESA campaign')
    if Path(args.run).name != args.run or args.run in ['', '.', '..']: ap.error('Invalid run label')
    args.bin_dir = args.bin_dir.resolve(); args.base = ROOT
    path = ROOT/'data'/args.campaign/'campaign.json'
    manifest = json.loads((path if path.exists() else ROOT/'campaigns'/args.campaign/'campaign.json').read_text())
    if args.describe:
        print(json.dumps(dict(name=args.campaign, status=manifest.get('status', 'not_prepared'), cases=len(manifest['cases']),
            dimensions=manifest['dimensions'], unsupported={a: [d for d in manifest['dimensions'] if not supported(a, {'dimension': d}, manifest['input_format'] == 'ESA2D01')] for a in manifest['algorithms']}), indent=2)); return
    if sys.platform != 'linux': raise RuntimeError('Execute campaigns on Arch Linux')
    phases = ['correctness', 'screen', 'final'] if args.phase == 'all' else [args.phase]
    for phase in phases:
        args.phase = phase
        with budget(args): run_phase(args, manifest)


if __name__ == '__main__':
    main()
