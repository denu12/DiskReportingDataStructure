"""Build the dimensional correctness adapters on Arch; do not run cases."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
out=root/'build/dimensional';out.mkdir(parents=True,exist_ok=True)
external=root/'src/bazel-src/external'
includes=[p/'include' for p in external.glob('boost.*') if (p/'include').is_dir()]
includes += [external/'+_repo_rules2+CGAL/include', root/'src/third_party/esa2026',root/'src/third_party/ann/include']
base=['g++','-std=c++20','-O3','-march=native','-DNDEBUG']
for path in includes:base+=['-I',str(path)]
commands={}
for kind in ['ANN','NANO','BOOST','CGAL','BRUTE']:
    cmd=base+[f'-DBACKEND_{kind}',str(root/'src/runner/dimensional/foreign_check.cpp')]
    if kind=='ANN':cmd+=list(map(str,(root/'src/third_party/ann/src').glob('*.cpp')))
    if kind=='CGAL':cmd+=['-lgmp','-lmpfr']
    commands[kind.lower()]=cmd+['-o',str(out/('check_'+kind.lower()))]
commands['rust']=['cargo','build','--release','--locked','--manifest-path',str(root/'src/runner/dimensional/rust/Cargo.toml'),
                  '--target-dir',str(root/'build/ddim-rust'),'-j','1']
env=dict(os.environ,RUSTFLAGS='-Ctarget-cpu=native')
if os.environ.get('OFFLINE')=='1':commands['rust'].insert(3,'--offline')
subprocess.run(['cmake','-S',str(root/'src/runner/dimensional'),'-B',str(out),'-DCMAKE_BUILD_TYPE=Release'],check=True)
subprocess.run(['cmake','--build',str(out),'-j','2'],check=True)
def build(item):
    name,cmd=item
    with (out/(name+'-build.log')).open('w') as log:
        p=subprocess.run(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
    return name,dict(returncode=p.returncode,log=str(out/(name+'-build.log')))
report={}
with ThreadPoolExecutor(max_workers=2) as pool:
    for f in as_completed([pool.submit(build,item) for item in commands.items()]):
        name,result=f.result();report[name]=result
        (out/'build-status.json').write_text(json.dumps(report,indent=2))
        print(name,result['returncode'],flush=True)
if any(v['returncode'] for v in report.values()):raise SystemExit(1)
