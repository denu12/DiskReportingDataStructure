"""Verify service-managed temporary cleanup after normal exit and forced timeout."""
from pathlib import Path
import os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from job_temporary import properties
for mode in ['normal','timeout']:
    unit=f'drr-cleanup-test-{os.getpid()}-{mode}'
    folder=Path('/tmp/drr-job-'+unit)
    code='import os,pathlib,time; p=pathlib.Path(os.environ["TMPDIR"]); (p/"leftover").write_bytes(b"x"*1048576); '+('time.sleep(30)' if mode=='timeout' else 'print(p)')
    cmd=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,*properties(unit),'-p','RuntimeMaxSec=1s','-p','TimeoutStopSec=1s','-p','KillMode=control-group',sys.executable,'-c',code]
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=15)
    assert (run.returncode==0)==(mode=='normal'),run.stderr
    assert not folder.exists(),folder
    print(mode,'cleanup passed',flush=True)
