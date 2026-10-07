"""Full dimensional performance campaign with durable progress and hard budgets."""
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from ddim_campaign import ROOT,save,sha
from run_ddim_all import command

def backend(a):
    return [str(ROOT/'build/d-dim/check_brute')] if a=='brute_force' else command(a)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+',args.run):raise ValueError('Invalid run name')
    policy=json.loads((ROOT/'campaigns/esa2026-ddim/performance.json').read_text())
    out=ROOT/'results/esa2026-ddim'/args.run;out.mkdir(parents=True,exist_ok=False)
    original=json.loads((ROOT/'results/esa2026-ddim'/policy['admission_run']/'state.json').read_text())
    eligible=[a for a in original['policy']['algorithms'] if a not in policy['excluded'] and
              len([j for j in original['jobs'] if j['algorithm']==a and j['status']=='success'])==18]
    if len(eligible)!=18:raise RuntimeError('Expected 18 eligible implementations')
    cpus=policy['cpus'];lock=threading.Lock()
    state=dict(status='running',stage='correctness',run=args.run,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               policy=policy,algorithms=eligible,current={},completed_phases=[],identity={})
    for a in eligible:
        state['identity'][a]=[dict(path=p,sha256=sha(Path(p))) for p in backend(a)]
    save(out/'state.json',state)
    env=dict(os.environ,OMP_NUM_THREADS='1',OMP_THREAD_LIMIT='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',RAYON_NUM_THREADS='1')
    env['PYTHONPATH']=str(ROOT/'src/third_party/esa2026')+os.pathsep+env.get('PYTHONPATH','')
    def phase(name,root,jobs,budget,timeout):
        start=time.monotonic();deadline=start+budget;pending=queue.Queue();rows=[];excluded=set()
        for job in jobs:pending.put(job)
        state.update(stage=name,current={});save(out/'state.json',state)
        phase_state=dict(status='running',planned_jobs=len(jobs),results=rows,budget_seconds=budget)
        target=out/name/'state.json';save(target,phase_state)
        def worker(cpu):
            while True:
                try:a,c,rep=pending.get_nowait()
                except queue.Empty:return
                row=dict(algorithm=a,case=c['id'],dimension=c['dimension'],points=c['points'],queries_expected=c['queries'],repetition=rep,cpu=cpu)
                remaining=deadline-time.monotonic()
                with lock:
                    skip=a in excluded
                    state['current'][str(cpu)]=a+'/'+c['id'];save(out/'state.json',state)
                if remaining<=0 or skip:row['status']='not_run_budget' if remaining<=0 else 'not_run_after_failure'
                else:
                    t=time.monotonic()
                    cmd=['taskset','-c',str(cpu),'prlimit',f'--as={policy["memory_gib"]*1024**3}','--core=0','--']+backend(a)+[str(root/c['path']),a]
                    if name!='correctness':cmd.append('--bench')
                    try:
                        p=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=min(timeout,remaining))
                        row.update(returncode=p.returncode,stdout=p.stdout[-5000:],stderr=p.stderr[-5000:])
                        row['status']='incorrect' if p.returncode==2 else 'crash' if p.returncode else 'success'
                        if p.returncode in [0,2]:
                            try:row.update(json.loads(p.stdout))
                            except ValueError:row['status']='invalid_output'
                        if row['status']=='success' and row.get('queries')!=c['queries']:row['status']='incomplete_output'
                    except subprocess.TimeoutExpired:row['status']='timeout'
                    row['wall_seconds']=time.monotonic()-t
                with lock:
                    if name=='correctness' and row['status']!='success':excluded.add(a)
                    rows.append(row)
                    phase_state.update(elapsed_seconds=time.monotonic()-start,outcomes=dict(collections.Counter(r['status'] for r in rows)))
                    save(out/name/a/(c['id']+f'-r{rep}.json'),row)
                    save(target,phase_state)
                print(name,a,c['id'],rep,row['status'],flush=True)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(worker,cpu) for cpu in cpus]
            for f in futures:f.result()
        phase_state['status']='budget_exhausted' if any(r['status']=='not_run_budget' for r in rows) else 'complete'
        save(target,phase_state)
        state['current']={};state['completed_phases'].append(name);save(out/'state.json',state)
        return rows
    try:
        small_root=ROOT/'data/esa2026-ddim'
        small=json.loads((small_root/'campaign.json').read_text())
        small_cases=[c for c in small['cases'] if c['id'].split('/')[0] in ['embedding','distributions']]
        for c in small_cases:
            if sha(small_root/c['path'])!=c['sha256']:raise RuntimeError('Correctness input checksum mismatch')
        checked=phase('correctness',small_root,[(a,c,0) for c in small_cases for a in eligible],policy['correctness_budget_seconds'],60)
        eligible=[a for a in eligible if len([r for r in checked if r['algorithm']==a and r['status']=='success'])==len(small_cases)]
        state['verified_algorithms']=eligible;state['stage']='preparation';save(out/'state.json',state)
        with (out/'prepare.log').open('w') as log:
            subprocess.run([sys.executable,str(ROOT/'tools/prepare_ddim_full.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
        full_root=ROOT/'data/esa2026-ddim-full';manifest=json.loads((full_root/'campaign.json').read_text())
        cases=sorted(manifest['cases'],key=lambda c:(c['points'],c['dimension'],c['id']))
        state['full_cases']=len(cases);state['full_queries']=sum(c['queries'] for c in cases);state['manifest_sha256']=sha(full_root/'campaign.json')
        state['stage']='screen';save(out/'state.json',state)
        screened=phase('screen',full_root,[(a,c,0) for c in cases for a in eligible],policy['screen_budget_seconds'],policy['screen_timeout_seconds'])
        good={(r['algorithm'],r['case']):r for r in screened if r['status']=='success'}
        final_jobs=[(a,c,rep) for rep in range(policy['repetitions']) for c in cases for a in eligible if (a,c['id']) in good]
        loads=[0.0]*4
        for a,c,rep in final_jobs:
            i=loads.index(min(loads));loads[i]+=good[a,c['id']]['wall_seconds']*1.25
        estimate=max(loads)
        plan=dict(jobs=len(final_jobs),estimated_seconds=estimate,budget_seconds=policy['final_budget_seconds'],fits_budget=estimate<=policy['final_budget_seconds'],estimation='screen wall times, 3 repetitions, four workers, 25 percent margin')
        save(out/'plan.json',plan)
        if not plan['fits_budget']:raise RuntimeError('Final estimate exceeds budget; review plan before further execution')
        final=phase('final',full_root,final_jobs,policy['final_budget_seconds'],policy['final_timeout_seconds'])
        summary=dict(eligible=eligible,cases=len(cases),correctness=dict(collections.Counter(r['status'] for r in checked)),screen=dict(collections.Counter(r['status'] for r in screened)),final=dict(collections.Counter(r['status'] for r in final)))
        save(out/'summary.json',summary)
        state.update(status='complete' if all(r['status']=='success' for r in final) else 'needs_attention',stage=None,execution_finished=True)
        save(out/'state.json',state)
    except Exception as e:
        state.update(status='needs_attention',error=str(e));save(out/'state.json',state);raise

if __name__=='__main__':main()
