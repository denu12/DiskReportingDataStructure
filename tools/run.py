"""Explicit, bounded ESA campaign runner. No queue or automatic startup.

Run correctness first. Only passing, unchanged binaries may enter timing runs.
Jobs use one physical CPU and one library thread; budgets span campaigns.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import queue
import signal
import subprocess
import threading
import time
import sys
import sysconfig
from budget import budget,policy

def atomic(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2));tmp.replace(path)

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def identity(root,bindir):
 return {'manifest':sha(root/'campaign.json'),**{p.name:sha(p) for p in bindir.iterdir() if p.is_file()}}

def environment(base,bindir):
 env=os.environ.copy()
 for name in ['OMP_NUM_THREADS','OMP_THREAD_LIMIT','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PARLAY_NUM_THREADS','RAYON_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:env[name]='1'
 env['SFC_ESA_LIBRARY']=str(bindir/'libsfc_esa2026.so')
 env['SFC_DYNAMIC_LIBRARY']=str(bindir/'libsfc_esa2026.so')
 env['LD_LIBRARY_PATH']=str(base/'bin/lib')+':'+env.get('LD_LIBRARY_PATH','')
 env['PYTHONPATH']=str(base/'src/third_party/esa2026')+':'+sysconfig.get_path('purelib')+':'+env.get('PYTHONPATH','')
 return env

def classify(returncode,log,result):
 if any(s in log for s in ['Invalid ESA2D data header','Truncated or trailing ESA2D data','Unregistered ESA algorithm','error while loading shared libraries','Failed to connect to bus']):return 'infrastructure_error'
 if 'too many items with the same position on one axis' in log.lower():return 'unsupported_input'
 if 'oom-kill' in log or 'Failed due to memory' in log:return 'memory'
 if 'result: timeout' in log or 'Failed due to timeout' in log:return 'timeout'
 if result and result.get('status')=='incorrect':return 'incorrect'
 if returncode==0 and result and result.get('status')=='success':return 'success'
 if returncode in (-signal.SIGSEGV,-signal.SIGABRT,-signal.SIGILL,-signal.SIGBUS,-signal.SIGFPE) or 'code=dumped' in log or 'result: core-dump' in log:return 'crash'
 if returncode==-signal.SIGXCPU:return 'timeout'
 return 'error'

class Campaign:
 def __init__(self,args):
  self.root=args.root.resolve();self.base=args.base.resolve();self.bindir=self.base/'bin/esa2d'
  self.manifest=json.loads((self.root/'campaign.json').read_text());self.args=args
  self.manifest['policy']=policy(self.base)
  # Admission is based on ordinary workloads, not synthetic edge fixtures.
  # Preserve the original manifest and historical findings on disk.
  if self.manifest['policy'].get('correctness_case_policy')=='smallest_ordinary_workload_per_suite':
   ordinary={}
   for case in sorted(self.manifest['cases'],key=lambda c:(c['n'],c['id'])):
    ordinary.setdefault(case['suite'],case)
   if not ordinary:raise RuntimeError('No ordinary workloads available for correctness screening')
   self.manifest['correctness']=list(ordinary.values())
  self.stage=self.manifest['policy']['stages'][args.phase]
  self.timeout=self.stage['timeout_seconds']
  self.runroot=self.base/'results'/args.campaign/args.run;self.out=self.runroot/args.phase
  self.stop_file=self.runroot/'STOP';self.stop=threading.Event();self.cpus=queue.Queue()
  for cpu in (args.cpus or self.manifest['policy']['cpus']):self.cpus.put(cpu)
  self.env=environment(self.base,self.bindir)
  for c in self.manifest['cases']+self.manifest['correctness']:
   path=self.root/c['path']
   if not path.is_file():raise RuntimeError('Missing campaign input: '+c['path'])
   expected=c.get('sha256',c.get('conversion',{}).get('sha256'))
   if expected and sha(path)!=expected:raise RuntimeError('Input checksum mismatch: '+c['path'])
  self.deadline=args.deadline
  self.session=str(os.getpid());self.backend=args.backend
  if args.cpus:self.manifest['policy']['cpus']=args.cpus
  available=os.sched_getaffinity(0)
  if len(set(self.manifest['policy']['cpus']))!=len(self.manifest['policy']['cpus']):raise RuntimeError('Duplicate CPU IDs')
  if not set(self.manifest['policy']['cpus'])<=available:raise RuntimeError('Requested CPUs are not available; use --cpus with allowed CPU IDs')
  cores=[]
  for cpu in self.manifest['policy']['cpus']:
   topology=Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
   cores.append(((topology/'physical_package_id').read_text().strip(),(topology/'core_id').read_text().strip()))
  if len(set(cores))!=len(cores):raise RuntimeError('CPU selection includes sibling threads; choose distinct physical cores')
 def job(self,algorithm,case,mode,rep=0):
  if self.stop.is_set() or self.stop_file.exists() or time.monotonic()+self.timeout>self.deadline:return dict(status='not_started',algorithm=algorithm['name'],case=case['id'],repetition=rep)
  cpu=self.cpus.get()
  try:
   key=hashlib.sha256(json.dumps([algorithm['name'],case['id'],rep]).encode()).hexdigest()[:16]
   directory=self.out/'jobs'/key;directory.mkdir(parents=True,exist_ok=True)
   resultpath=directory/'result.json';resultpath.unlink(missing_ok=True)
   command=[str(self.bindir/algorithm['binary']),algorithm['name'],str(self.root/case['path']),mode,str(resultpath)]
   unit=f'esa2d-{self.session}-{key}'
   cmd=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,'--slice=esa2d-bench.slice',
    '-p',f'CPUAffinity={cpu}','-p','MemoryMax=16G','-p','MemorySwapMax=0','-p','MemoryAccounting=yes',
    '-p','OOMPolicy=kill','-p','KillMode=control-group','-p','TimeoutStopSec=2','-p','RuntimeMaxSec=60s',
    '/usr/bin/env']+[k+'='+v for k,v in self.env.items() if k in ['SFC_ESA_LIBRARY','SFC_DYNAMIC_LIBRARY','LD_LIBRARY_PATH','PYTHONPATH'] or k.endswith('_NUM_THREADS') or k in ['OMP_THREAD_LIMIT','MKL_NUM_THREADS','RAYON_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS']]+command
   timeout=self.timeout
   cmd=[x.replace('MemoryMax=16G',f"MemoryMax={self.manifest['policy']['memory_gib']}G").replace('RuntimeMaxSec=60s',f'RuntimeMaxSec={timeout}s') for x in cmd]
   if self.backend=='process':cmd=[sys.executable,str(self.base/'tools/worker.py'),str(cpu),str(self.manifest['policy']['memory_gib']*2**30),str(timeout)]+command
   start=time.monotonic();timed_out=False
   with (directory/'run.log').open('w') as log:
    process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=self.env,start_new_session=True)
    while process.poll() is None:
     if self.stop.is_set() or self.stop_file.exists() or time.monotonic()>self.deadline or time.monotonic()-start>=timeout:
      timed_out=time.monotonic()-start>timeout
      if self.backend=='systemd':subprocess.run(['systemctl','--user','stop',unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
      else:
       try:os.killpg(process.pid,signal.SIGKILL)
       except ProcessLookupError:pass
     time.sleep(.15)
   result=json.loads(resultpath.read_text()) if resultpath.exists() else None
   status=classify(process.returncode,(directory/'run.log').read_text(),result)
   if timed_out:status='timeout'
   if self.stop.is_set() or self.stop_file.exists():status='interrupted_user'
   return dict(status=status,algorithm=algorithm['name'],case=case['id'],mode=algorithm['mode'],repetition=rep,cpu=cpu,timeout_seconds=timeout,wall_seconds=time.monotonic()-start,result=result,log=str((directory/'run.log').relative_to(self.base)))
  finally:self.cpus.put(cpu)
 def run(self):
  if self.stop_file.exists():raise RuntimeError('STOP marker exists; use explicit --resume to authorize a new run')
  if (self.out/'state.json').exists():raise RuntimeError('This phase already has results; preserve them in a new campaign copy before rerunning')
  fingerprint=identity(self.root,self.bindir);fingerprint['backend']=self.backend;fingerprint['cpus']=self.manifest['policy']['cpus']
  fingerprint['execution_policy']=sha(self.base/'campaigns/execution.json')
  fingerprint['harness']={p.name:sha(p) for p in (self.base/'tools').glob('*.py')}
  selected=self.manifest['algorithms']
  if self.args.algorithms:selected=[a for a in selected if a['name'] in self.args.algorithms]
  if not selected:raise ValueError('No selected algorithms')
  results=[]
  if self.args.phase!='correctness':
   gate=json.loads((self.runroot/'correctness/state.json').read_text())
   if gate['identity']!=fingerprint:raise RuntimeError('Correctness gate is stale: manifest or binaries changed')
   allowed={a for a,v in gate['eligibility'].items() if v=='passed'}
   selected=[a for a in selected if a['name'] in allowed]
  if self.args.cases and not set(self.args.cases)<={c['id'] for c in self.manifest['cases']}:raise RuntimeError('Unknown case ID in --cases')
  measured=None;planned_cases=None
  if self.args.phase in ('final','contention','followup'):
   screen=json.loads((self.runroot/'screen/state.json').read_text())
   if screen['identity']!=fingerprint:raise RuntimeError('Screening results are stale')
   measured={(r['algorithm'],r['case']) for r in screen['results'] if r['status']=='success'}
   if self.args.phase=='final':
    plan=json.loads((self.base/'results/_plans'/(self.args.run+'.json')).read_text())
    entry=plan['campaigns'][self.args.campaign]
    if not plan['fits_budget'] or entry['screen_sha256']!=sha(self.runroot/'screen/state.json'):raise RuntimeError('Final plan is stale or exceeds the budget; run tools/plan.py')
    planned_cases=set(entry['cases'])
   elif self.args.phase=='contention':
    final=json.loads((self.runroot/'final/state.json').read_text())
    if final['identity']!=fingerprint:raise RuntimeError('Final results are stale')
    measured={(r['algorithm'],r['case']) for r in final['results'] if r['status']=='success'}
   else:
    rows=screen['results']
    path=self.runroot/'final/state.json'
    if path.exists():
     final=json.loads(path.read_text())
     if final['identity']!=fingerprint:raise RuntimeError('Final results are stale')
     rows=rows+final['results']
    measured={(r['algorithm'],r['case']) for r in rows if r['status']=='timeout'}
  if self.args.phase in ('followup','contention') and not any((a['name'],c) in measured for a in selected for c in self.args.cases):raise RuntimeError('No selected pair qualifies for this follow-up stage')
  if self.backend=='systemd':subprocess.run(['systemctl','--user','set-property','--runtime','esa2d-bench.slice',f"MemoryMax={self.manifest['policy']['aggregate_memory_gib']}G",'MemorySwapMax=0'],check=True)
  state=dict(phase=self.args.phase,execution=dict(timeout_seconds=self.timeout,workers=min(self.stage['workers'],len(self.manifest['policy']['cpus'])),shared_budget_pool=self.stage.get('budget_pool',self.args.phase)),status='running',identity=fingerprint,results=results,eligibility={},started=datetime.datetime.now(datetime.timezone.utc).isoformat())
  atomic(self.out/'state.json',state)
  def task(a):
   local=[];streak=0
   if self.args.phase=='correctness':
    for case in self.manifest['correctness']:
     r=self.job(a,case,'verify');local.append(r)
     if r['status']!='success':break
   else:
    repetitions=1 if self.args.phase in ('screen','followup') else self.manifest['policy']['repetitions']
    cases=sorted(self.manifest['cases'],key=lambda c:(c['suite'],c['n'],c['id']))
    if planned_cases is not None:cases=[c for c in cases if c['id'] in planned_cases]
    if self.args.cases:cases=[c for c in cases if c['id'] in self.args.cases]
    for case in cases:
     if measured is not None and (a['name'],case['id']) not in measured:
      local.append(dict(algorithm=a['name'],case=case['id'],status='not_selected_after_screen'));continue
     if self.args.phase=='screen' and self.args.campaign=='esa2026-2d' and case['suite']=='distributions' and streak>=2:
      local.append(dict(algorithm=a['name'],case=case['id'],status='skipped_after_two_scaling_timeouts'));continue
     for rep in range(repetitions):
      r=self.job(a,case,'bench',rep);local.append(r)
      if r['status']!='success':break
     if case['suite']=='distributions':streak=streak+1 if r['status']=='timeout' else 0
   return a['name'],local
  signal.signal(signal.SIGTERM,lambda *_:self.stop.set());signal.signal(signal.SIGINT,lambda *_:self.stop.set())
  with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.stage['workers'],len(self.manifest["policy"]["cpus"]))) as pool:
   futures=[pool.submit(task,a) for a in selected]
   for future in concurrent.futures.as_completed(futures):
    name,rows=future.result();results.extend(rows)
    if self.args.phase=='correctness':
     state['eligibility'][name]='blocked' if any(r['status'] in ('infrastructure_error','not_started','interrupted_user') for r in rows) else 'passed' if len(rows)==len(self.manifest['correctness']) and all(r['status']=='success' for r in rows) else 'excluded'
    atomic(self.out/'state.json',state);print(name,[(r.get('case'),r['status']) for r in rows],flush=True)
  state['status']='stopped' if self.stop.is_set() or self.stop_file.exists() else 'budget_exhausted' if time.monotonic()>self.deadline-self.timeout else 'complete'
  atomic(self.out/'state.json',state)

def main():
 p=argparse.ArgumentParser(description='Explicit correctness, screen and final campaign stages; no automatic queue.')
 p.add_argument('phase',choices=['correctness','screen','final','followup','contention','stop'])
 p.add_argument('--campaign',choices=['scaling','static','dynamic-circles','static-circles','esa2026-2d'],required=True)
 p.add_argument('--run',default='default');p.add_argument('--root',type=Path)
 p.add_argument('--base',type=Path,default=Path(__file__).resolve().parents[1])
 p.add_argument('--backend',choices=['systemd','process'],default=os.environ.get('DRR_BACKEND','systemd'))
 p.add_argument('--cpus',type=int,nargs='+');p.add_argument('--algorithms',nargs='+');p.add_argument('--cases',nargs='+');p.add_argument('--resume',action='store_true')
 args=p.parse_args()
 if args.phase in ('followup','contention') and (not args.algorithms or not args.cases):p.error('Follow-up and contention checks require explicit --algorithms and --cases')
 if not args.run or Path(args.run).name!=args.run or args.run in ('.','..'):p.error('--run must be a single directory name')
 if args.root is None:args.root=args.base/'data'/args.campaign
 stop=args.base/'results'/args.campaign/args.run/'STOP'
 if args.phase=='stop':
  stop.parent.mkdir(parents=True,exist_ok=True);stop.write_text('Stopped by explicit request\n');return
 if args.resume:stop.unlink(missing_ok=True)
 with budget(args):Campaign(args).run()

if __name__=='__main__':main()
