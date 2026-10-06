import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import bounded_campaign as bc

def job(id,n=10,series=None,lane='ordinary',scaling=True):
    return dict(id=id,n=n,series=series or id,lane=lane,scaling=scaling,case=id)

class SchedulerTests(unittest.TestCase):
    def test_proto_roundtrip(self):
        p={'instances':[{'name':['a:1'], 'seed':[1], 'mix':[True], 'double_params':[{'key':['fixed_w'],'value':[.001]}]}]}
        self.assertEqual(bc.parse(bc.proto(p)),p)
    def test_four_distinct_series(self):
        js=[job(str(i)) for i in range(8)]
        self.assertEqual(len(bc.choose_jobs(js,{}, {},'screen',4)),4)
    def test_ordered_growth(self):
        js=[job('a',10,'s'),job('b',100,'s'),job('c',10,'t')]
        self.assertEqual([x['id'] for x in bc.choose_jobs(js,{}, {},'screen',4)],['a','c'])
        self.assertEqual([x['id'] for x in bc.choose_jobs(js,{}, {'a':{'job':js[0]}},'screen',4)],['c'])
    def test_large_exclusive_and_barrier(self):
        js=[job('big',100,'s','large'),job('small',10)]
        self.assertEqual(bc.choose_jobs(js,{}, {},'screen',4),[js[0]])
        self.assertEqual(bc.choose_jobs(js,{}, {'x':{'job':job('x')}},'screen',4),[])
        self.assertEqual(bc.choose_jobs(js,{}, {'big':{'job':js[0]}},'screen',4),[])
    def test_two_timeouts_only_larger_same_series(self):
        js=[job('a',10,'s'),job('b',100,'s'),job('c',1000,'s'),job('d',1000,'t')]
        r={'a':{'status':'timeout'},'b':{'status':'timeout'}}
        self.assertIsNotNone(bc.skip_reason(js[2],r,js,'screen'))
        self.assertIsNone(bc.skip_reason(js[3],r,js,'screen'))
        r['b']['status']='success'
        self.assertIsNone(bc.skip_reason(js[2],r,js,'screen'))
    def test_final_failure_stops_repetitions(self):
        a=job('a');b=job('b');b['case']='a'
        self.assertEqual(bc.skip_reason(b,{'a':{'status':'crash'}},[a,b],'final'),'skipped_after_case_failure')
    def test_failure_classification(self):
        self.assertEqual(bc.classify('Too many items with the same position on one axis',None,0),'unsupported_input')
        self.assertEqual(bc.classify('Finished with result: oom-kill',None,9),'memory')
        self.assertEqual(bc.classify('Finished with result: timeout',None,1),'timeout')
        self.assertEqual(bc.classify('probably segfaulted',None,0),'crash')
        self.assertEqual(bc.classify('',None,1),'error')
        self.assertEqual(bc.classify('',{'size':[0]},0),'success')
    def test_final_selection_15_and_excludes_failed(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);src=t/'src';src.mkdir()
            js=[dict(job('good'),instance={'seed':[1]}),dict(job('bad'),instance={'seed':[1]})]
            bc.atomic(src/'manifest.json',dict(base='/tmp',jobs=js,binary_dir='/tmp/dynamic-v2',worker_cpus=[0]))
            bc.atomic(src/'state.json',dict(results={'good':{'status':'success'},'bad':{'status':'timeout'}}))
            bc.select_followup(src,t/'final','final')
            manifest=json.loads((t/'final/manifest.json').read_text())
            self.assertEqual(manifest['binary_dir'],'/tmp/dynamic-v2')
            self.assertEqual(manifest['worker_cpus'],[0])
            new=manifest['jobs']
            self.assertEqual(len(new),15)
            self.assertEqual({j['seed'] for j in new},{1,2,3,4,5})
            self.assertEqual({j['case'] for j in new},{'good'})
    def test_confirmation_requires_selection(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);bc.atomic(t/'manifest.json',dict(jobs=[]));bc.atomic(t/'state.json',dict(results={}))
            with self.assertRaises(ValueError):bc.select_followup(t,t/'c','confirm')
    def test_memory_admission(self):
        self.assertGreater(bc.estimated_memory_gib('cgal_rt',10_000_000),12)
        self.assertLess(bc.estimated_memory_gib('esa_sprk',1_000_000),12)

@unittest.skipUnless(os.environ.get('SFC_TEST_CGROUPS')=='1','Linux cgroup integration tests opt-in')
class CgroupTests(unittest.TestCase):
    def test_budget_persists_without_launch_or_extension(self):
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);manifest=dict(base=str(t),phase='screen',jobs=[job('never')])
            bc.atomic(t/'manifest.json',manifest)
            deadline=time.time()-1
            bc.atomic(t/'state.json',dict(started=deadline-100,deadline=deadline,results={},active={}))
            bc.run(t);bc.run(t)
            s=json.loads((t/'state.json').read_text())
            self.assertEqual(s['status'],'budget_exhausted')
            self.assertEqual(s['deadline'],deadline)
            self.assertEqual(s['active'],{})
            self.assertFalse((t/'jobs').exists())
    def probe(self,name,code,seconds=3):
        unit='sfc-policy-test-'+name
        result=subprocess.run(bc.cmd_systemd(unit,2,.0625,seconds,[sys.executable,'-c',code],bc.POLICY['slice']),
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15)
        print(result.stdout,flush=True)
        return result
    def test_actual_affinity_memory_swap_and_parent(self):
        code='''import os,json,pathlib
p=pathlib.Path('/sys/fs/cgroup'+pathlib.Path('/proc/self/cgroup').read_text().strip().split('::')[1])
print(json.dumps(dict(cpus=list(os.sched_getaffinity(0)),memory=(p/'memory.max').read_text().strip(),swap=(p/'memory.swap.max').read_text().strip(),parent_memory=(p.parent/'memory.max').read_text().strip(),parent_swap=(p.parent/'memory.swap.max').read_text().strip())))'''
        r=self.probe('settings',code);self.assertEqual(r.returncode,0)
        d=json.loads(next(line for line in r.stdout.splitlines() if line.startswith('{')))
        self.assertEqual(d,dict(cpus=[2],memory=str(64*1024**2),swap='0',parent_memory=str(72*bc.GIB),parent_swap='0'))
    def test_timeout_kills_child(self):
        r=self.probe('timeout','import subprocess,time; p=subprocess.Popen(["sleep","30"]); print("CHILD",p.pid,flush=True); time.sleep(30)',seconds=1)
        self.assertEqual(bc.classify(r.stdout,None,r.returncode),'timeout')
        pid=int(next(l for l in r.stdout.splitlines() if l.startswith('CHILD ')).split()[1])
        path=Path(f'/proc/{pid}/stat')
        self.assertTrue(not path.exists() or path.read_text().split()[2]=='Z')
    def test_memory_kill(self):
        r=self.probe('memory','x=bytearray(256*1024*1024)')
        self.assertEqual(bc.classify(r.stdout,None,r.returncode),'memory')

if __name__=='__main__':unittest.main(verbosity=2)
