"""Bounded parallel correctness screening, one physical core per child job."""
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from ddim_campaign import ROOT, save, sha

def command(algorithm):
    manual=['chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED']
    rust=['esa_sprk','esa_kiddo','esa_nabo','esa_neighbourhood','esa_vptree','esa_orthtree','esa_grid']
    if algorithm in manual:return [str(ROOT/'build/d-dim/ddim_check')]
    if algorithm in rust:return [str(ROOT/'build/ddim-rust/release/ddim-esa-check')]
    if algorithm=='esa_snn_rust':return [str(ROOT/'build/ddim-rust/release/ddim-snn-check')]
    if algorithm in ['esa_sklearn_kd','esa_sklearn_ball','esa_snn','brute_force']:
        return [sys.executable,str(ROOT/'d-dim/python_check.py')]
    kind='boost' if algorithm.startswith('boost_') else {'ann_fr':'ann','cgal_kd':'cgal','esa_nanoflann':'nano'}[algorithm]
    return [str(ROOT/'build/d-dim'/('check_'+kind))]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--cpus',default='1,2,3,4')
    args=ap.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+',args.run):raise ValueError('Invalid run name')
    cpus=list(map(int,args.cpus.split(',')))
    if len(set(cpus))!=len(cpus) or len(cpus)!=4:raise ValueError('Four distinct CPUs required')
    policy=json.loads((ROOT/'campaigns/esa2026-ddim/campaign.json').read_text())
    data=ROOT/'data/esa2026-ddim';manifest=json.loads((data/'campaign.json').read_text())
    results=ROOT/'results/esa2026-ddim'/args.run;results.mkdir(parents=True,exist_ok=False)
    # Only ordinary ESA workloads: synthetic edge fixtures are not eligible gates.
    cases=sorted([c for c in manifest['cases'] if c['id'].split('/')[0] in policy['enabled_case_families']],key=lambda c:(c['dimension'],c['id']))
    for c in cases:
        if sha(data/c['path'])!=c['sha256']:raise ValueError('Data hash mismatch')
    state=dict(status='running',policy=policy,cpus=cpus,planned_jobs=len(cases)*len(policy['algorithms']),
               manifest_sha256=sha(data/'campaign.json'),current={},jobs=[],binaries={})
    for a in policy['algorithms']:
        cmd=command(a);state['binaries'][a]=[dict(path=p,sha256=sha(Path(p))) for p in cmd if Path(p).is_file()]
    started=time.monotonic();deadline=started+policy['total_budget_seconds'];lock=threading.Lock();todo=queue.Queue()
    for a in policy['algorithms']:todo.put(a)
    env=dict(os.environ,OMP_NUM_THREADS='1',OMP_THREAD_LIMIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',RAYON_NUM_THREADS='1')
    env['PYTHONPATH']=str(ROOT/'src/third_party/esa2026')+os.pathsep+env.get('PYTHONPATH','')
    def record(job):
        with lock:
            state['jobs'].append(job)
            state['elapsed_seconds']=time.monotonic()-started
            save(results/job['algorithm']/(job['id']+'.json'),job)
            save(results/'state.json',state)
        print(job['algorithm'],job['id'],job['status'],flush=True)
    def worker(cpu):
        while True:
            try:a=todo.get_nowait()
            except queue.Empty:return
            base=command(a);excluded=None;timeouts=0
            if not all(Path(p).is_file() for p in base):excluded='backend_unavailable'
            for c in cases:
                job=dict(algorithm=a,id=c['id'],dimension=c['dimension'],cpu=cpu)
                remaining=deadline-time.monotonic()
                if excluded or remaining<=0:
                    job['status']=excluded or 'not_run_budget';record(job);continue
                with lock:
                    state['current'][str(cpu)]=a+'/'+c['id'];save(results/'state.json',state)
                t=time.monotonic()
                try:
                    p=subprocess.run(['taskset','-c',str(cpu),'prlimit',f'--as={policy["memory_gib"]*1024**3}','--core=0','--']+base+[str(data/c['path']),a],
                        env=env,capture_output=True,text=True,timeout=min(policy['timeout_seconds'],remaining))
                    job.update(returncode=p.returncode,stdout=p.stdout[-10000:],stderr=p.stderr[-10000:])
                    job['status']='incorrect' if p.returncode==2 else 'crash' if p.returncode else 'success'
                    if p.returncode in [0,2]:
                        try:job.update(json.loads(p.stdout))
                        except ValueError:job['status']='invalid_output'
                except subprocess.TimeoutExpired:job['status']='timeout'
                job['wall_seconds']=time.monotonic()-t
                if job['status'] in ['incorrect','crash','invalid_output']:excluded='not_run_after_'+job['status']
                if job['status']=='timeout':
                    timeouts+=1
                    if timeouts>=2:excluded='not_run_after_two_timeouts'
                record(job)
            with lock:
                state['current'].pop(str(cpu),None);save(results/'state.json',state)
    save(results/'state.json',state)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,cpu) for cpu in cpus]
        for f in futures:f.result()
    state['outcomes']=dict(collections.Counter(j['status'] for j in state['jobs']))
    state['elapsed_seconds']=time.monotonic()-started
    state['status']='complete' if all(j['status']=='success' for j in state['jobs']) else 'needs_attention'
    state['execution_finished']=True
    save(results/'state.json',state)
    print(json.dumps(dict(status=state['status'],elapsed_seconds=state['elapsed_seconds'],outcomes=state['outcomes'])),flush=True)

if __name__=='__main__':main()
