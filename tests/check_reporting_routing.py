"""Exercise repaired reporting entries through the real campaign launchers."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from experiment_integrity import boundary_case
from original_runner import dependency_files
from algorithm_labels import metadata
from algorithm_backends_2d import binary
from backends import command
with tempfile.TemporaryDirectory() as folder:
    checks=0
    for d in [2,3]:
        case=boundary_case(folder,d,format2d=d==2)
        names=['chan_sss','stann_fr','pgm_multidimensional']+(['pam'] if d==2 else ['chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED'])
        for name in names:
            out=Path(folder)/'out.json'
            args=[str(ROOT/'bin/esa2d'/binary(name)),name,case['path'],'verify',str(out)] if d==2 else [*command(name),case['path'],name]
            run=subprocess.run(args,capture_output=True,text=True,check=True,timeout=30)
            row=json.loads(run.stdout)
            assert row['status']=='success',(name,d,row)
            assert metadata(name)['output_contract']==row['output_contract']
            assert all(p.is_file() for p in dependency_files(name))
            if d==2:assert json.loads(out.read_text())['status']=='success'
            checks+=1
print(f'{checks} campaign routes passed')
