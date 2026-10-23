"""Exact reporting regressions for the three minimally adapted competitors."""
import argparse
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from check_additional_competitors import cases, write_case

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from original_runner import FOREIGN
from additional_competitors import supported

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', default=['chan_sss', 'stann_fr', 'pgm_multidimensional','pam'])
    parser.add_argument('--dimensions', type=int, nargs='+', default=[2,3,8,16,32,34,128,960])
    parser.add_argument('--binary-dir', type=Path, default=ROOT/'build/dimensional')
    parser.add_argument('--output', type=Path, default=ROOT/'build/dimensional/reporting-validation.json')
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory() as folder:
        for d in args.dimensions:
            samples = list(cases(d))
            # Dense Morton intervals force PGM's BIGMIN jump after 64 misses.
            if d in (2,3):
                rng = random.Random(456+d)
                points = [(x,y)+((0,) if d==3 else ()) for x in range(128) for y in range(128)]
                queries = [(tuple(rng.randrange(128) for _ in range(2))+((0,) if d==3 else ()), rng.randrange(1,12)**2) for _ in range(80)]
                scale = 1 << (32-(64//d-1))
                points = [tuple(x*scale for x in p) for p in points]
                queries = [(tuple(x*scale for x in c),r*scale*scale) for c,r in queries]
                samples.append(('dense-small-balls', points, queries))
            for name, points, queries in samples:
                path = Path(folder)/'case.bin'
                write_case(path,d,points,queries)
                expected = sum(sum(sum((x-y)**2 for x,y in zip(p,c)) <= r for p in points) for c,r in queries)
                for algorithm in args.only:
                    if algorithm=='pam' and d!=2: continue
                    if algorithm=='pgm_multidimensional' and not supported(algorithm,d): continue
                    for mode in ('check','bench'):
                        command = [str(args.binary_dir/('check_'+FOREIGN[algorithm])),str(path),algorithm]
                        if mode=='bench': command.append('--bench')
                        run = subprocess.run(command,capture_output=True,text=True,timeout=60)
                        row = json.loads(run.stdout) if run.stdout.strip() else {'status':'process_failure','stderr':run.stderr[-2000:]}
                        ok = run.returncode==0 and row.get('status')=='success' and row.get('answers')==expected
                        results.append(dict(algorithm=algorithm,dimension=d,case=name,mode=mode,passed=ok,result=row))
                        if not ok: print(json.dumps(results[-1]),flush=True)
            print('Checked dimension', d, flush=True)
    args.output.write_text(json.dumps(results,indent=2)+'\n')
    print(f'{sum(r["passed"] for r in results)}/{len(results)} passed')
    return int(not all(r['passed'] for r in results))

if __name__=='__main__': raise SystemExit(main())
