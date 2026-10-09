#!/usr/bin/env python3
"""Preview, check, run, inspect or stop a complete experiment theater.

No arguments lists theaters. Execution requires --execute and a fresh --run label.
Preparation and compilation are deliberately separate from measurement.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from budget import save
from campaign_paths import campaign_directory, theater_manifests
from theaters import case_count

SYNTHETIC = {'scaling', 'static', 'dynamic-circles'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def execution_policy(cpu):
    """Record the resources available to one serial, single-core theater run."""
    config = read(ROOT / 'config/execution.json')
    memory = config['single_worker_memory_gib']
    config.update(workers=1, cpus=[cpu], memory_gib=memory, aggregate_memory_gib=memory)
    for stage in config['stages'].values():
        stage['workers'] = 1
    return config


def commands(campaigns, label, backend, algorithms):
    """Keep admission, screening and final measurements in separate passes."""
    synthetic = [name for name in campaigns if name in SYNTHETIC]
    for phase in ('correctness', 'screen', 'final'):
        if phase == 'final' and synthetic:
            yield 'plan', None, [sys.executable, 'tools/plan.py', '--run', label,
                                 '--campaigns', *synthetic]
        for name in campaigns:
            if name in SYNTHETIC:
                command = [sys.executable, 'tools/run.py', phase, '--campaign', name,
                           '--run', label, '--backend', backend]
            else:
                command = [sys.executable, 'tools/esa/run.py', '--campaign', name,
                           '--run', label, '--phase', phase]
            if algorithms:
                command += ['--algorithms', *algorithms]
            yield phase, name, command


def preflight(campaigns, algorithms, hash_inputs):
    """Resolve the actual manifest paths, including shared ESA data directories."""
    errors, inputs, rosters, checked, binaries = [], {}, {}, {}, set()
    disabled = set(read(ROOT / 'config/disabled-algorithms.json')['algorithms'])
    from backends import command as dimensional_command
    for name in campaigns:
        definition = campaign_directory(ROOT, name) / 'campaign.json'
        path = ROOT / 'data' / name / 'campaign.json'
        if not path.is_file():
            errors.append(f'{name}: prepare data/{name}/campaign.json first')
            continue
        manifest = read(path)
        inputs[name] = {'manifest_sha256': digest(path), 'definition_sha256': digest(definition)}
        if manifest.get('smoke'):
            errors.append(f'{name}: smoke inputs are not full experimental inputs')
        if manifest.get('specification_sha256') != digest(definition):
            errors.append(f'{name}: prepared specification is stale')
        if name not in SYNTHETIC and manifest.get('status') != 'ready':
            errors.append(f'{name}: preparation is not ready')
        if len(manifest.get('cases', [])) != case_count(read(definition)):
            errors.append(f'{name}: prepared case count differs from the definition')
        entries = manifest.get('algorithms', [])
        names = [a['name'] if isinstance(a, dict) else a for a in entries]
        extra = {'morton_d_dim', 'Morton3D'} if name not in SYNTHETIC else set()
        selected = algorithms or names
        if set(selected) - set(names) - extra:
            errors.append(f'{name}: unknown algorithm selection')
        selected = [a for a in selected if a not in disabled]
        if not selected:
            errors.append(f'{name}: no enabled algorithms')
        rosters[name] = selected
        format2d = name in SYNTHETIC or manifest.get('input_format') == 'ESA2D01'
        if format2d:
            binaries.add(ROOT / 'bin/esa2d/libsfc_esa2026.so')
        for algorithm in selected:
            if format2d:
                binaries.add(ROOT / 'bin/esa2d' / ('esa_runner_pargeo' if algorithm == 'pargeo' else 'esa_runner'))
            else:
                try:
                    binaries.update(Path(p) for p in dimensional_command(algorithm))
                except KeyError:
                    errors.append(f'{name}: no backend for {algorithm}')
        for case in manifest.get('cases', []):
            original = (path.parent / case['path']).resolve()
            if not original.is_file():
                errors.append(f'{name}: missing input {original}')
                continue
            expected = case.get('sha256', case.get('conversion', {}).get('sha256'))
            if not expected:
                errors.append(f'{name}: missing input checksum for {case["id"]}')
            if hash_inputs:
                if original not in checked:
                    checked[original] = digest(original)
                if checked[original] != expected:
                    errors.append(f'{name}: checksum mismatch for {case["id"]}')
    for path in sorted(binaries):
        if not path.is_file():
            errors.append(f'Missing backend: {path}')
    if errors:
        raise RuntimeError('\n'.join(dict.fromkeys(errors)))
    return {'inputs': inputs, 'algorithms': rosters,
            'binaries': {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): digest(p)
                         for p in sorted(binaries)}, 'verified_input_files': len(checked)}


def request_stop(folder, campaigns, label):
    for path in [folder / 'STOP', *(ROOT / 'results' / c / label / 'STOP' for c in campaigns)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Stopped by explicit request\n', encoding='utf-8')


def execute(args, campaigns, plan, folder):
    if sys.platform != 'linux':
        raise RuntimeError('Execute on Arch Linux; previews work on other platforms')
    import fcntl
    if args.backend == 'process' and any(c not in SYNTHETIC for c in campaigns):
        raise RuntimeError('Imported and dimensional campaigns require native user systemd')
    if args.cpu not in os.sched_getaffinity(0):
        raise RuntimeError('Requested CPU is not available to this process')
    if args.backend == 'systemd':
        subprocess.run(['systemctl', '--user', 'show-environment'], check=True, stdout=subprocess.DEVNULL)
    lockpath = ROOT / 'results/_theater-controller.lock'
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    with lockpath.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another theater controller is running') from None
        if folder.exists() or (ROOT / 'results/_budgets' / (args.run + '.json')).exists():
            raise RuntimeError('Run label already exists; use a fresh label')
        if any((ROOT / 'results' / c / args.run).exists() for c in campaigns):
            raise RuntimeError('Campaign results or STOP markers exist; use a fresh label')
        print('Checking inputs and backends before starting any job...', flush=True)
        provenance = preflight(campaigns, args.algorithms, True)
        config = execution_policy(args.cpu)
        folder.mkdir(parents=True)
        save(folder / 'execution.json', config)
        save(folder / 'provenance.json', provenance)
        save(folder / 'plan.json', {'theater': args.theater, 'campaigns': campaigns, 'commands': plan})
        env = dict(os.environ, DRR_EXECUTION_POLICY=str(folder / 'execution.json'))
        state = dict(status='running', theater=args.theater, run=args.run, campaigns=campaigns,
                     started_unix=time.time(), completed=[], needs_attention=False)
        save(folder / 'status.json', state)
        stopped = False

        def stop(*_):
            nonlocal stopped
            stopped = True
            request_stop(folder, campaigns, args.run)

        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
        try:
            for phase, name, command in plan:
                if stopped or (folder / 'STOP').exists():
                    state['status'] = 'stopped'
                    break
                state.update(phase=phase, campaign=name)
                save(folder / 'status.json', state)
                print(shlex.join(command), flush=True)
                with (folder / f'{phase}-{name or "theater"}.log').open('w') as log:
                    child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
                    while child.poll() is None:
                        if (folder / 'STOP').exists() and not stopped:
                            stop()
                        time.sleep(.2)
                if stopped:
                    state['status'] = 'stopped'
                    break
                if child.returncode:
                    raise RuntimeError(f'{phase}/{name}: exit {child.returncode}; see controller log')
                if name:
                    result = read(ROOT / 'results' / name / args.run / phase / 'state.json')
                    if result['status'] != 'complete':
                        raise RuntimeError(f'{phase}/{name}: {result["status"]}')
                    if any(v == 'blocked' for v in result.get('eligibility', {}).values()):
                        raise RuntimeError(f'{phase}/{name}: infrastructure blocked admission')
                    state['needs_attention'] |= result.get('needs_attention', False)
                state['completed'].append({'phase': phase, 'campaign': name})
                save(folder / 'status.json', state)
            else:
                state['status'] = 'complete'
        except Exception as error:
            state.update(status='needs_attention', error=str(error))
            raise
        finally:
            state['finished_unix'] = time.time()
            save(folder / 'status.json', state)
        print(json.dumps(state, indent=2))


def main():
    theaters = {spec['name']: spec for _, spec in theater_manifests(ROOT)}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('theater', nargs='?', choices=sorted(theaters))
    parser.add_argument('--run', help='Fresh result label; required to execute, inspect or stop')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--execute', action='store_true', help='Run all three phases after preflight')
    actions.add_argument('--check', action='store_true', help='Verify all inputs and backend files; launch nothing')
    actions.add_argument('--status', action='store_true')
    actions.add_argument('--stop', action='store_true')
    parser.add_argument('--cpu', type=int, default=1, help='One logical CPU on one physical core (default: 1)')
    parser.add_argument('--backend', choices=['systemd', 'process'], default=os.environ.get('DRR_BACKEND', 'systemd'))
    parser.add_argument('--algorithms', nargs='+', help='Optional explicit roster, valid in every selected campaign')
    args = parser.parse_args()
    if not args.theater:
        if args.execute or args.check or args.status or args.stop:
            parser.error('Select a theater')
        for name, spec in theaters.items():
            print(f'{name}: ' + ', '.join(spec['campaigns']))
        return
    if args.run and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.run):
        parser.error('--run must contain letters, digits, underscores or hyphens')
    if args.algorithms and len(set(args.algorithms)) != len(args.algorithms):
        parser.error('--algorithms must not contain duplicates')
    if (args.execute or args.status or args.stop) and not args.run:
        parser.error('--run is required for this action')
    campaigns = theaters[args.theater]['campaigns']
    folder = ROOT / 'results' / ('_execution-' + (args.run or 'PREVIEW'))
    if args.status or args.stop:
        state = read(folder / 'status.json')
        if state.get('theater') != args.theater:
            raise RuntimeError('Run label belongs to a different controller/theater')
        if args.stop:
            request_stop(folder, campaigns, args.run)
            print('Stop requested; active workers will terminate and preserve their results.')
        else:
            print(json.dumps(state, indent=2))
        return
    plan = list(commands(campaigns, args.run or 'FRESH_LABEL', args.backend, args.algorithms))
    for name in campaigns:
        definition = campaign_directory(ROOT, name) / 'campaign.json'
        print(f'{name}: {case_count(read(definition))} instances; {definition.relative_to(ROOT)}')
    if args.check:
        print(json.dumps(preflight(campaigns, args.algorithms, True), indent=2))
    elif args.execute:
        execute(args, campaigns, plan, folder)
    else:
        memory = execution_policy(args.cpu)['memory_gib']
        print(f'\nPreview only. One worker, CPU {args.cpu}, {memory} GiB memory cap; no experiments started.\n')
        for _, _, command in plan:
            print(shlex.join(command))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
