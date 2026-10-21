"""Build pinned original competitors on Linux (including WSL); no benchmarks."""
import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', choices=['phtree','pgm','psi','spatialindex'])
    args = parser.parse_args()
    out = ROOT/'build/dimensional'
    out.mkdir(parents=True, exist_ok=True)
    launcher=ROOT/'bin/esa2d/original_runner'
    launcher.parent.mkdir(parents=True,exist_ok=True)
    launcher.write_text('#!/usr/bin/env sh\nexec "${PYTHON:-python3}" "$(dirname "$0")/../../tools/original_runner.py" "$@"\n')
    launcher.chmod(0o755)
    third = ROOT/'src/third_party'
    base = [os.environ.get('CXX','g++'), '-std=c++20','-O3','-march=native','-DNDEBUG',
            '-DBACKEND_ADDITIONAL', str(ROOT/'src/runner/dimensional/foreign_check.cpp')]
    commands = {
        'phtree': base+['-DADDITIONAL_PHTREE','-I'+str(third/'phtree-cpp/include')],
        'pgm': base+['-DADDITIONAL_PGM','-mbmi2','-I'+str(third/'pgm-index/include')],
        'psi': base+['-DADDITIONAL_PSI','-DPARLAY_SEQUENTIAL','-mcx16']+
               ['-I'+str(third/'space-tree-lib'/p) for p in
                ['include','include/parlaylib/include','include/libmorton/include']],
        'spatialindex': base+['-DADDITIONAL_SPATIALINDEX','-I'+str(third/'libspatialindex/include'),
                            '-L'+str(ROOT/'build/libspatialindex/src'),
                            '-Wl,-rpath,$ORIGIN/../libspatialindex/src','-lspatialindex'],
    }
    status_path=out/'additional-build-status.json'
    report = json.loads(status_path.read_text()) if args.only and status_path.exists() else {}
    for name in args.only or commands:
        with (out/(name+'-build.log')).open('w') as log:
            status = 0
            if name == 'spatialindex':
                for command in [
                    ['cmake','-S',str(third/'libspatialindex'),'-B',str(ROOT/'build/libspatialindex'),
                     '-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=OFF'],
                    ['cmake','--build',str(ROOT/'build/libspatialindex'),'-j',os.environ.get('BUILD_JOBS','2')]]:
                    status = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
                    if status: break
            if not status:
                temporary = out/('check_'+name+'.next')
                status = subprocess.run(commands[name]+['-o',str(temporary)],
                                        stdout=log, stderr=subprocess.STDOUT).returncode
                if not status: temporary.replace(out/('check_'+name))
        report[name] = {'returncode':status,'log':str(out/(name+'-build.log'))}
        print(name, status, flush=True)
    status_path.write_text(json.dumps(report,indent=2)+'\n')
    return int(any(r['returncode'] for r in report.values()))

if __name__ == '__main__':
    raise SystemExit(main())
