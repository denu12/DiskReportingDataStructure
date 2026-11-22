"""Verify pair isolation across screening, retries and concurrent workers."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from job_policy import PairPolicy


class Policy(unittest.TestCase):
    def test_one_timeout_even_with_concurrent_repeats(self):
        policy=PairPolicy();calls=[];lock=threading.Lock()
        def run(a,c,r):
            def backend():
                with lock:calls.append((a,c))
                time.sleep(.01)
                return dict(algorithm=a,case=c,repetition=r,status='timeout' if c=='bad' else 'success')
            return policy.execute(a,c,r,backend)
        with ThreadPoolExecutor(max_workers=6) as workers:
            rows=list(workers.map(lambda j:run(*j),[('tree',c,r) for r in range(3) for c in ('bad','good')]))
        self.assertEqual(calls.count(('tree','bad')),1)
        self.assertEqual(calls.count(('tree','good')),3)
        self.assertEqual(sum(r['status']=='skipped_after_timeout' for r in rows),2)

    def test_screen_timeout_suppresses_all_final_runs(self):
        policy=PairPolicy([dict(algorithm='tree',case='x',status='timeout')])
        def must_not_run():self.fail('A screening timeout reached final measurement')
        for rep in range(3):
            self.assertEqual(policy.execute('tree','x',rep,must_not_run)['status'],'skipped_after_timeout')

    def test_exception_is_local_and_incorrect_outputs_remain_timed(self):
        policy=PairPolicy()
        def broken():raise ValueError('bad backend JSON')
        self.assertEqual(policy.execute('bad','x',0,broken)['status'],'error')
        self.assertEqual(policy.execute('bad','x',1,broken)['status'],'skipped_after_error')
        for rep in range(3):
            row=policy.execute('wrong','x',rep,lambda:dict(algorithm='wrong',case='x',status='incorrect'))
            self.assertEqual(row['status'],'incorrect')


if __name__=='__main__':unittest.main()
