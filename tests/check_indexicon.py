"""Exercise all built Indexicon variants against the harness's exact ID oracle."""
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT/'tools'))
from indexicon_competitors import BACKENDS, COMPILED_DIMS, supported

MAX = (1 << 32) - 1


def write(path, d, points, queries, two_d=False):
    with path.open('wb') as f:
        f.write(struct.pack('<8sQQ',b'ESA2D01\0',len(points),len(queries)) if two_d else struct.pack('<IQQ',d,len(points),len(queries)))
        for point in points:
            f.write(struct.pack('<'+'I'*d,*point))
        for center,r2 in queries:
            f.write(struct.pack('<'+'I'*d+'QQ',*center,r2 & ((1<<64)-1),r2>>64))


def fixture(d):
    rng = random.Random(347+d)
    zero = (0,)*d; high = (MAX,)*d; mid=(MAX//2,)*d
    points = [zero]*150 + [mid]*150 + [high]*150
    points += [(3,4)+zero[2:], (4,4)+zero[2:], (5,0)+zero[2:]]
    points += [tuple(rng.getrandbits(32) for _ in range(d)) for _ in range(260)]
    queries = [(zero,0),(zero,25),(zero,24),(high,0),(mid,0),(zero,MAX**2*d),
               (high,MAX**2*d-1),(mid,MAX**2//16)]
    queries += [(points[rng.randrange(len(points))],rng.randrange(1<<63)) for _ in range(9)]
    return points,queries


def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    if p.returncode:raise RuntimeError(f'{cmd}: {p.returncode}: {p.stdout} {p.stderr}')
    row=json.loads(p.stdout)
    assert row['status']=='success', row
    assert row['output_contract']=='point_ids_only', row
    return row


calls=0
with tempfile.TemporaryDirectory() as td:
    folder=Path(td)
    for d in COMPILED_DIMS:
        points,queries=fixture(d)
        path=folder/'case.bin';write(path,d,points,queries)
        empty=folder/'empty.bin';write(empty,d,[],queries[:1])
        expected=sum(sum((x-y)**2 for x,y in zip(point,center))<=r2 for point in points for center,r2 in queries)
        for algorithm,backend in BACKENDS.items():
            if not supported(algorithm,d):continue
            exe=ROOT/'build/dimensional'/('check_'+backend)
            verified=run([exe,path,algorithm]); bench=run([exe,path,algorithm,'--bench'])
            assert expected==verified['answers']==bench['answers'],(d,algorithm,expected,verified,bench)
            assert run([exe,empty,algorithm])['answers']==0
            calls+=3
            # Verify the dispatch used by the normal 2D and dimensional campaign runners.
            if d==2:
                two=folder/'case-2d.bin'; write(two,d,points,queries,two_d=True)
                dest=folder/'result.json'
                row=run([sys.executable,ROOT/'tools/original_runner.py',algorithm,two,'verify',dest])
                assert row['answers']==json.loads(dest.read_text())['answers']==expected
                calls+=1
            if d in {3,960}:
                assert run([sys.executable,ROOT/'tools/original_runner.py','--dimensional',path,algorithm])['answers']==expected
                calls+=1
print(f'{calls} Indexicon checks passed over dimensions {COMPILED_DIMS}')
