"""Check both real campaign routes, metadata and pinned binary dependencies."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from additional_competitors import BACKENDS
from algorithm_backends_2d import binary
from algorithm_labels import metadata
from backends import command
from experiment_integrity import boundary_case
from original_runner import dependency_files
from workloads import STATIC, STATIC_3D, validate_roster

validate_roster(STATIC);validate_roster(STATIC_3D)
assert len(STATIC)==41 and len(STATIC_3D)==35
with tempfile.TemporaryDirectory() as directory:
    for d in [2,3]:
        case=boundary_case(directory,d,format2d=d==2)
        for name in BACKENDS:
            assert metadata(name)['source_repairs'] is False
            assert all(path.is_file() for path in dependency_files(name))
            output=Path(directory)/'result.json'
            if d==2:
                args=[str(ROOT/'bin/esa2d'/binary(name)),name,case['path'],'verify',str(output)]
            else:args=[*command(name),case['path'],name]
            result=subprocess.run(args,text=True,capture_output=True,timeout=30)
            row=json.loads(result.stdout)
            assert result.returncode==0,(name,d,result.stderr,row)
            assert row['status']==('unsupported_input' if name=='pgm_multidimensional' else 'success'),(name,d,row)
            if d==2:assert json.loads(output.read_text())['status']==row['status']
print('20 campaign-route checks passed; rosters and dependencies verified')
