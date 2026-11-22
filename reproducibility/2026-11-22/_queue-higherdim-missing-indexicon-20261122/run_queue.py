"""Resume missing higher-dimensional measurements using frozen, unchanged backends."""
import argparse
from collections import Counter
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import signal
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
RESULTS = PROJECT / 'results'
INDEX = RESULTS / '_queue-indexicon-20261105/workspace'
ORIGINAL = RESULTS / '_queue-coverage-completion-20261030/workspace'
DATA = INDEX / 'data'
HIGH = ('ESA_clustering', 'ESA_graph_embeddings', 'ESA_high_dimensional', 'ESA_uniform_points')
OLD_RUN = 'publication-remaining-20261007'
AFTER = 'drr-measure-inexact-resume-20261121.service'
CHILD = None
COUNTS = Counter()
STOPPING = False


def save(name, value):
    target = ROOT / name
    temp = target.with_suffix(target.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(target)


def status(stage, **extra):
    save('status.json', dict(status=stage, cpu=1, workers=1, counts=dict(COUNTS),
                            updated_unix=time.time(), after_service=AFTER, **extra))


def command(algorithm, path, bench):
    if algorithm.startswith('indexicon_'):
        import sys
        sys.path.insert(0, str(INDEX / 'tools'))
        from indexicon_competitors import BACKENDS
        backend = INDEX / 'build/dimensional' / ('check_' + BACKENDS[algorithm])
    elif algorithm == 'esa_snn_rust':
        backend = ORIGINAL / 'build/original-rust/release/original-range-check'
    elif algorithm == 'esa_nanoflann':
        backend = ORIGINAL / 'build/dimensional/check_nano'
    else:
        raise ValueError(algorithm)
    return [str(backend), str(path), algorithm] + (['--bench'] if bench else [])


def prepare():
    if (ROOT / 'plan.json').exists():
        return json.loads((ROOT / 'plan.json').read_text())
    import sys
    sys.path.insert(0, str(INDEX / 'tools'))
    from indexicon_competitors import VARIANTS, supported
    pairs = []
    for campaign in HIGH:
        manifest = json.loads((DATA / campaign / 'campaign.json').read_text())
        cases = {case['id']:case for case in manifest['cases']}
        for algorithm in ('esa_snn_rust', 'esa_nanoflann'):
            state_path = PROJECT / 'historical_data/results' / campaign / OLD_RUN / 'final/state.json'
            state = json.loads(state_path.read_text())
            missing = {r['case'] for r in state['results']
                       if r['algorithm']==algorithm and r['status']=='excluded_by_correctness'}
            # A later run may already have filled a historical correctness exclusion.
            for base in (PROJECT/'historical_data/results', RESULTS):
                for later in (base/campaign).glob('*/final/state.json'):
                    completed={}
                    for row in json.loads(later.read_text()).get('results',[]):
                        if row['algorithm']==algorithm and row['status'] in ('success','answer_count_mismatch'):
                            completed.setdefault(row['case'],set()).add(row.get('repetition'))
                    missing-={case_id for case_id,reps in completed.items() if len(reps)==3}
            for case_id in sorted(missing & cases.keys()):
                case = cases[case_id]
                pairs.append(dict(campaign=campaign, algorithm=algorithm, case=case_id,
                                  dimension=case['dimension'], path=str((DATA/campaign/case['path']).resolve()),
                                  sha256=case.get('sha256') or case['conversion']['sha256'],
                                  reason='previously_excluded_by_correctness', previous_state=str(state_path)))
        for case_id, case in sorted(cases.items()):
            for algorithm in VARIANTS:
                if not supported(algorithm, case['dimension']):
                    continue
                pairs.append(dict(campaign=campaign, algorithm=algorithm, case=case_id,
                                  dimension=case['dimension'], path=str((DATA/campaign/case['path']).resolve()),
                                  sha256=case.get('sha256') or case['conversion']['sha256'],
                                  reason='indexicon_higher_dim_not_run'))
    assert len(pairs)==1474, len(pairs)
    assert Counter(p['algorithm'] for p in pairs)['esa_snn_rust']==34
    assert Counter(p['algorithm'] for p in pairs)['esa_nanoflann']==30
    for pair in pairs:
        assert Path(pair['path']).is_file(), pair['path']
        assert Path(command(pair['algorithm'],pair['path'],True)[0]).is_file()
    plan = dict(created_unix=time.time(), cpu=1, workers=1, repetitions=3,
                screen_timeout_seconds=60, final_timeout_seconds=180,
                timeout_policy='screen timeout: no finals; final timeout: skip remaining repeats',
                error_policy='record failed case, skip its remaining repeats, continue other cases',
                measure_failed_correctness=True, modify_algorithms=False, after_service=AFTER,
                pairs=pairs, pairs_by_algorithm=dict(Counter(p['algorithm'] for p in pairs)))
    save('plan.json',plan)
    status('queued',total_pairs=len(pairs))
    return plan


def busy():
    service = subprocess.run(['systemctl','--user','is-active',AFTER],capture_output=True,text=True).stdout.strip()
    if service in ('active','activating','deactivating','reloading'):
        return AFTER
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():
            continue
        try:
            args = (proc/'cmdline').read_bytes().split(b'\0')
        except (OSError,ProcessLookupError):
            continue
        if any(a.endswith(b'/run_requested_queue.py') for a in args):
            return 'existing benchmark controller'
        if b'--bench' in args and any(str(PROJECT).encode() in a for a in args):
            return 'existing benchmark process'
    return None


def limits():
    # Limit each backend, leaving the controller alive to record failures and continue.
    resource.setrlimit(resource.RLIMIT_AS,(60*1024**3,60*1024**3))


def run_job(cmd, timeout):
    global CHILD
    started = time.monotonic()
    CHILD = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                             start_new_session=True,preexec_fn=limits)
    try:
        out,err = CHILD.communicate(timeout=timeout)
        try:
            result = json.loads(out)
        except (ValueError,TypeError):
            result = dict(status='error',detail=(out+err)[-1500:])
        if not isinstance(result,dict):
            result = dict(status='error',detail='Backend did not return a JSON object')
        result.setdefault('status','error')
        result['returncode']=CHILD.returncode
        if CHILD.returncode and result['status']=='success':
            result['status']='error'
        if err.strip():
            result['stderr_tail']=err[-1500:]
    except subprocess.TimeoutExpired:
        os.killpg(CHILD.pid,signal.SIGKILL)
        CHILD.communicate()
        result=dict(status='timeout',timeout_seconds=timeout)
    finally:
        CHILD=None
    return dict(result,wall_seconds=time.monotonic()-started)


def stop(*_):
    global STOPPING
    STOPPING=True
    if CHILD and CHILD.poll() is None:
        os.killpg(CHILD.pid,signal.SIGKILL)
    raise SystemExit('Controller stopped; resume uses recorded completed jobs')


def fixture(pair):
    path=ROOT/'fixtures'/('d'+str(pair['dimension'])+'.bin')
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        return path
    with Path(pair['path']).open('rb') as source, path.open('wb') as out:
        d,n,q=struct.unpack('<IQQ',source.read(20))
        small,count=min(n,2000),min(q,4)
        out.write(struct.pack('<IQQ',d,small,count))
        out.write(source.read(small*d*4))
        for i in range(count):
            which=i*(q-1)//max(1,count-1)
            source.seek(20+n*d*4+which*(d*4+16))
            row=source.read(d*4+16)
            assert len(row)==d*4+16
            out.write(row)
    return path


def terminal_skip(rows):
    if any(r['status'] in ('timeout','skipped_after_timeout') for r in rows):
        return 'skipped_after_timeout'
    if any(r['status'] in ('error','unsupported_dimension','unsupported_input','skipped_after_error')
           or (r['status']=='incorrect' and 'query_seconds' not in r) for r in rows):
        return 'skipped_after_error'
    return None


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    plan=prepare()
    if args.prepare:
        print(json.dumps({k:v for k,v in plan.items() if k!='pairs'},indent=2))
        return
    os.sched_setaffinity(0,{1})
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','RAYON_NUM_THREADS','PARLAY_NUM_THREADS'):
        os.environ[key]='1'
    signal.signal(signal.SIGTERM,stop)
    signal.signal(signal.SIGINT,stop)
    while reason:=busy():
        status('waiting_for_existing_queue',waiting_for=reason,total_pairs=len(plan['pairs']))
        time.sleep(30)
    with (RESULTS/'_theater-controller.lock').open('a') as lock:
        while True:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except BlockingIOError:
                status('waiting_for_benchmark_lock',total_pairs=len(plan['pairs']))
                time.sleep(30)
        if reason:=busy():
            raise RuntimeError('Another benchmark started while acquiring lock: '+reason)
        history={}
        log_path=ROOT/'jobs.jsonl'
        if log_path.exists():
            for line in log_path.open():
                row=json.loads(line)
                key=(row['campaign'],row['case'],row['algorithm'],row['phase'],row.get('repetition'))
                if key in history:
                    raise RuntimeError('Duplicate completed job: '+str(key))
                history[key]=row
                COUNTS[row['phase']+'_'+row['status']]+=1
        def record(pair,phase,repetition,result):
            row=dict(result,campaign=pair['campaign'],case=pair['case'],algorithm=pair['algorithm'],
                     dimension=pair['dimension'],phase=phase,repetition=repetition,cpu=1,workers=1,
                     input_sha256=pair['sha256'],measure_failed_correctness=True,
                     correctness_admission=gates.get((pair['algorithm'],pair['dimension']),'not_rechecked'),
                     finished_unix=time.time())
            key=(row['campaign'],row['case'],row['algorithm'],phase,repetition)
            assert key not in history
            with log_path.open('a') as log:
                log.write(json.dumps(row)+'\n')
                log.flush()
                os.fsync(log.fileno())
            history[key]=row
            COUNTS[phase+'_'+row['status']]+=1
        status('validating_inputs',total_pairs=len(plan['pairs']))
        for path,sha in sorted({(p['path'],p['sha256']) for p in plan['pairs']}):
            with open(path,'rb') as f:
                assert hashlib.file_digest(f,'sha256').hexdigest()==sha, path
        binary_paths=sorted({command(p['algorithm'],p['path'],True)[0] for p in plan['pairs']})
        binaries={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in binary_paths}
        previous=ROOT/'binary-sha256.json'
        if previous.exists():
            assert json.loads(previous.read_text())==binaries,'Backend changed during queue; preserve run integrity'
        else:
            save('binary-sha256.json',binaries)
        gates={}
        for pair in plan['pairs']:
            gate=(pair['algorithm'],pair['dimension'])
            if gate in gates:
                continue
            key=(pair['campaign'],pair['case'],pair['algorithm'],'correctness',None)
            if key in history:
                result=history[key]
            else:
                status('correctness',algorithm=pair['algorithm'],dimension=pair['dimension'])
                result=run_job(command(pair['algorithm'],fixture(pair),False),60)
                record(pair,'correctness',None,result)
            gates[gate]=result['status']
        jobs=[(p,phase,rep) for phase,reps in [('screen',1),('final',3)]
              for p in plan['pairs'] for rep in range(reps)]
        random.Random(20261122).shuffle(jobs)
        jobs.sort(key=lambda job:job[1]!='screen')
        grouped={}
        for row in history.values():
            if row['phase']!='correctness':
                grouped.setdefault((row['campaign'],row['case'],row['algorithm']),[]).append(row)
        for i,(pair,phase,rep) in enumerate(jobs,1):
            key=(pair['campaign'],pair['case'],pair['algorithm'],phase,rep)
            if key in history:
                continue
            pk=key[:3]
            skipped=terminal_skip(grouped.get(pk,[]))
            status(phase,job=i,total_jobs=len(jobs),campaign=pair['campaign'],algorithm=pair['algorithm'],
                   case=pair['case'],repetition=rep,total_pairs=len(plan['pairs']))
            result=(dict(status=skipped,wall_seconds=0) if skipped else
                    run_job(command(pair['algorithm'],pair['path'],True),60 if phase=='screen' else 180))
            record(pair,phase,rep,result)
            grouped.setdefault(pk,[]).append(result)
        failures=sum(n for k,n in COUNTS.items() if k.endswith('_error'))
        status('complete_with_errors' if failures else 'complete',total_pairs=len(plan['pairs']))


if __name__=='__main__':
    main()
