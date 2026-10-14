"""Check new 3D campaign backends against independent integer point multisets.
Build with tools/build_selected_3d.sh first. No campaign data is modified.
"""
import json,random,struct,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
backends=[('MortonPlus3D',ROOT/'build/dimensional/morton_plus_3d_check'),
          ('esa_sprk_RUST_EXACT_3D',ROOT/'build/ddim-rust/release/sprk-adapted-3d-check')]
rng=random.Random(20261014);checks=0
with tempfile.TemporaryDirectory(prefix='diskreport-3d-check-') as folder:
    path=Path(folder)/'fixture.bin'
    for n in [0,1,3,4,7,8,9,16,17,128,129,1000,4097]:
        for kind in ['uniform','duplicate','extremes','grid']:
            points=[tuple(rng.randrange(2**32) for _ in range(3)) for _ in range(n)]
            if kind=='duplicate':points=[(4,5,6)]*n
            if kind=='extremes':points=[tuple((2**32-1)-x%16 for x in p) for p in points]
            if kind=='grid':points=[tuple(x&0xff000000 for x in p) for p in points]
            queries=[]
            for c in [(0,0,0),(2**32-1,)*3,points[-1] if points else (1,2,3)]:
                d=sum((a-b)**2 for a,b in zip(points[-1],c)) if points else 0
                for r in [0,1,(1<<64)-1,1<<64,(1<<64)+1,(1<<65)-1,1<<65,(1<<65)+1,3*(2**32-1)**2,(1<<128)-1,max(0,d-1),d,d+1]:queries.append((c,r))
            queries += [(tuple(rng.randrange(2**32) for _ in range(3)),rng.randrange(1<<66)) for _ in range(10)]
            with path.open('wb') as f:
                f.write(struct.pack('<IQQ',3,n,len(queries)))
                for p in points:f.write(struct.pack('<III',*p))
                for c,r in queries:f.write(struct.pack('<IIIQQ',*c,r&((1<<64)-1),r>>64))
            expected=sum(sum(sum((a-b)**2 for a,b in zip(p,c))<=r for p in points) for c,r in queries)
            for name,binary in backends:
                for bench in [False,True]:
                    p=subprocess.run([str(binary),str(path),name]+(['--bench'] if bench else []),capture_output=True,text=True,check=True)
                    result=json.loads(p.stdout)
                    assert result['status']=='success' and result['answers']==expected,(n,kind,name,result)
                    assert result['queries']==len(queries) and result['dimension']==3
                    assert result['output_contract']=='integer_points' and result['membership_contract']=='closed_integer_ball'
                    checks+=1
    # Unsupported dimensions must fail instead of silently reinterpreting coordinates.
    path.write_bytes(struct.pack('<IQQ',2,0,0))
    for name,binary in backends:
        assert subprocess.run([str(binary),str(path),name],capture_output=True).returncode!=0
print(f'{checks} 3D runner invocations passed; unsupported dimensions rejected.')
