"""Check retained exact 2D binaries after tools/build_selected_2d.sh (Linux)."""
from pathlib import Path
import sys,json,struct,subprocess,random
import tempfile
R=Path(__file__).resolve().parents[1]
_temporary=tempfile.TemporaryDirectory(prefix='diskreport-2d-check-')
tmp=Path(_temporary.name);rng=random.Random(42)
# Exercise both accepted input formats, duplicate multiplicities and 65-bit radii.
for n in [0,1,7,8,9,129,1000]:
 points=[(rng.randrange(2**32),rng.randrange(2**32)) for _ in range(n)]
 if n>8:points[:8]=[(0,0)]*3+[(2**32-1,2**32-1)]*3+[(3,4),(4,3)]
 qs=[(0,0,r) for r in [0,24,25,26,2**64-1,2**64,2*(2**32-1)**2]]+[(rng.randrange(2**32),rng.randrange(2**32),rng.randrange(2**65)) for _ in range(30)]
 for fmt in [0,1]:
  p=tmp/f'fixture-{n}-{fmt}.bin'
  with p.open('wb') as f:
   f.write(struct.pack('<8sQQ',b'ESA2D01\0',n,len(qs)) if fmt==0 else struct.pack('<IQQ',2,n,len(qs)))
   for x,y in points:f.write(struct.pack('<II',x,y))
   for x,y,r in qs:f.write(struct.pack('<IIQQ',x,y,r&((1<<64)-1),r>>64))
  for a,b in [('Morton','morton_cpp'),('MortonSIMD','morton_cpp'),('MortonPlusCPP','morton_cpp'),('esa_sprk_RUST_EXACT','sprk_rust_exact')]:
   dest=tmp/'result.json'
   for mode in ['verify','bench']:
    run=subprocess.run([str(R/'bin/esa2d'/b),a,str(p),mode,str(dest)],capture_output=True,text=True)
    assert run.returncode==0,(n,fmt,a,mode,run.stderr,run.stdout)
    s=json.loads(dest.read_text());assert s['status']=='success'
    expected=sum(sum((px-x)**2+(py-y)**2<=r for px,py in points) for x,y,r in qs)
    assert s['answers']==expected,(n,fmt,a,mode,s)
print('112 runner invocations passed; exact output verified in both input formats; 4 retained backends.')
