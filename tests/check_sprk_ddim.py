"""Check the native f64 bridge's exact output across every compiled dimension."""
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
EXE=ROOT/'build/sprk-ddim/release/sprk-ddim'
DIMS=tuple(range(3,17))+(32,34,96,100,128,784,960)
MAX=(1<<32)-1
calls=0
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'case.bin'
    for d in DIMS:
        rng=random.Random(20261122+d);zero=(0,)*d;high=(MAX,)*d
        points=[zero,zero,high,high,(3,4)+(0,)*(d-2)]+[tuple(rng.getrandbits(32) for _ in range(d)) for _ in range(40)]
        queries=[(zero,0),(zero,25),(high,0),(zero,d*MAX*MAX),(points[-1],0)]
        for data in ([],points):
            with path.open('wb') as f:
                f.write(struct.pack('<IQQ',d,len(data),len(queries)))
                for p in data:f.write(struct.pack('<'+'I'*d,*p))
                for center,r2 in queries:f.write(struct.pack('<'+'I'*d+'QQ',*center,r2&((1<<64)-1),r2>>64))
            expected=sum(sum((x-y)**2 for x,y in zip(p,c))<=r for p in data for c,r in queries)
            for flags in ([],['--bench']):
                result=subprocess.run([str(EXE),str(path),'esa_sprk_RUST_EXACT_DDIM',*flags],capture_output=True,text=True,timeout=30,check=True)
                row=json.loads(result.stdout)
                assert row['status']=='success' and row['answers']==expected,(d,row,expected)
                assert row['output_contract']=='integer_points'
                calls+=1
print(f'{calls} exact f64 SPRK checks passed across {len(DIMS)} dimensions')
