"""A failed phase pauses its campaign while other campaigns finish."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import run_theater as theater


@unittest.skipUnless(sys.platform=='linux','Native theater execution targets Linux')
class TheaterFailures(unittest.TestCase):
    def test_failed_campaign_does_not_stop_other_campaigns(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run='test';campaigns=['input_scaling','radius_scaling'];calls=[]
            plan=[(phase,c,['fake',phase,c]) for phase in ('correctness','screen','final') for c in campaigns]
            class Child:
                def __init__(self,command,**_):
                    _,phase,c=command;calls.append((phase,c));bad=c=='input_scaling'
                    path=root/'results'/c/run/phase/'state.json';path.parent.mkdir(parents=True)
                    path.write_text(json.dumps(dict(status='needs_attention' if bad else 'complete',eligibility={})))
                    self.returncode=int(bad)
                def poll(self):return self.returncode
            args=SimpleNamespace(backend='systemd',cpu=min(os.sched_getaffinity(0)),run=run,theater='static',algorithms=None)
            config=dict(protected_campaign_budgets={},measure_failed_correctness=True)
            target=root/'results/_execution-test'
            with patch.object(theater,'ROOT',root),patch.object(theater,'preflight',return_value={}),patch.object(theater,'execution_policy',return_value=config),patch.object(theater.subprocess,'run'),patch.object(theater.subprocess,'Popen',Child),contextlib.redirect_stdout(io.StringIO()):
                theater.execute(args,campaigns,plan,target)
            self.assertEqual(calls,[('correctness','input_scaling'),('correctness','radius_scaling'),('screen','radius_scaling'),('final','radius_scaling')])
            state=json.loads((target/'status.json').read_text())
            self.assertEqual(state['status'],'complete_with_errors')
            self.assertIn('input_scaling',state['paused_campaigns'])
            self.assertEqual(len(state['skipped_phases']),2)


if __name__=='__main__':unittest.main()
