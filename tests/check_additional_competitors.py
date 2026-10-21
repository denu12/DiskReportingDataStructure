"""Exercise native adapters against exhaustive integer-ball answers, outside timing.

Includes duplicates, boundary points, uint32 extremes, empty inputs and varied
distributions. Records upstream failures rather than repairing their searches.
"""
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from additional_competitors import BACKENDS

def write_case(path,d,points,queries):
    with path.open('wb') as out:
        out.write(struct.pack('<IQQ',d,len(points),len(queries)))
        for p in points:out.write(struct.pack('<'+'I'*d,*p))
        for center,r2 in queries:
            out.write(struct.pack('<'+'I'*d,*center))
            out.write(struct.pack('<QQ',r2&((1<<64)-1),r2>>64))

def cases(d):
    rng=random.Random(762+d)
    zero=(0,)*d;maximum=(2**32-1,)*d
    for width in [1000,2**32-1]:
        for distribution in ['uniform','clustered','duplicates']:
            points=[tuple(rng.randrange(width+1) for _ in range(d)) for _ in range(513)]
            if distribution=='clustered':points=[tuple(width//2+rng.randrange(-10,11) for _ in range(d)) for _ in points]
            if distribution=='duplicates':points=[points[i%11] for i in range(len(points))]
            queries=[(tuple(rng.randrange(width+1) for _ in range(d)),rng.randrange(width+1)**2) for _ in range(17)]
            queries += [(points[0],0),(zero,0),(zero,d*width*width)]
            yield f'{width}-{distribution}',points,queries
    boundary=[zero,maximum,zero]+[tuple(3 if a==0 else 4 if a==1 else 0 for a in range(d))]
    yield 'boundary',boundary,[(zero,25),(zero,24),(maximum,0),(zero,d*(2**32-1)**2)]
    yield 'empty',[],[(zero,0),(maximum,25)]
    yield 'singleton',[zero],[(zero,0),(maximum,0)]

def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix='additional-check-') as folder:
        for d in [2,3]:
            for name,points,queries in cases(d):
                path=Path(folder)/'case.bin';write_case(path,d,points,queries)
                expected=sum(sum(sum((x-y)**2 for x,y in zip(p,c))<=r for p in points) for c,r in queries)
                for algorithm,backend in BACKENDS.items():
                    for mode in ['check','bench']:
                        cmd=[str(ROOT/'build/dimensional'/('check_'+backend)),str(path),algorithm]
                        if mode=='bench':cmd.append('--bench')
                        try:
                            run=subprocess.run(cmd,text=True,capture_output=True,timeout=30)
                            try:row=json.loads(run.stdout)
                            except ValueError:row={'status':'process_failure','stdout':run.stdout[-1000:],'stderr':run.stderr[-1000:]}
                            row.update(returncode=run.returncode)
                            if row.get('status')=='success' and row.get('answers')!=expected:
                                row['status']='incorrect_count';row['expected_answers']=expected
                        except subprocess.TimeoutExpired:row={'status':'timeout'}
                        except OSError as error:row={'status':'process_failure','stderr':str(error)}
                        results.append({**row,'algorithm':algorithm,'dimension':d,'case':name,'mode':mode})
    target=ROOT/'build/dimensional/additional-validation.json'
    target.write_text(json.dumps(results,indent=2)+'\n')
    summary={}
    for row in results:
        counts=summary.setdefault(row['algorithm'],{})
        status=row['status'];counts[status]=counts.get(status,0)+1
    print(json.dumps(summary,indent=2));print(target)
    return 0 if all(r['status'] in ['success','unsupported_input'] for r in results) else 1

if __name__=='__main__':raise SystemExit(main())
