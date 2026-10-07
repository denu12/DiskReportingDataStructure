"""Generate reproducible circle workloads, never execute a benchmark."""
import argparse,json,random,struct
from pathlib import Path
import numpy as np
from prepare_esa import STATIC,DYNAMIC,MAX,MAX_DISTANCE2,fixtures,sha,write_data
BASE=Path(__file__).resolve().parents[1]
def dynamic_data(path,points,events):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('wb') as f:
  f.write(struct.pack('<8sQQ',b'DRRDYN1\0',len(points),len(events)))
  for x,y in points:f.write(struct.pack('<II',x,y))
  for kind,x,y,r in events:f.write(struct.pack('<BIIQQ',kind,x,y,r&(2**64-1),r>>64))
def points(rng,n,distribution):
 if distribution=='uniform':a=rng.random((n,2))
 elif distribution=='normal':a=np.clip(rng.normal(.5,.125,(n,2)),0,1)
 else:a=np.column_stack((rng.random(n),np.minimum(rng.exponential(.1,n),1)))
 return np.rint(a*MAX).astype(np.uint32)
def main():
 p=argparse.ArgumentParser();p.add_argument('--campaign',choices=['scaling','static','dynamic-circles'],required=True);p.add_argument('--smoke',action='store_true',help='Small validation workload, recorded in manifest');args=p.parse_args()
 config=json.loads((BASE/'campaigns'/args.campaign/'campaign.json').read_text());root=BASE/'data'/args.campaign
 if (root/'campaign.json').exists():raise RuntimeError('Prepared campaign exists; archive it before replacing inputs')
 root.mkdir(parents=True,exist_ok=True);cases=[]
 def add(id,suite,seed,n,path,**extra):cases.append(dict(id=id,suite=suite,seed=seed,n=n,path=path.relative_to(root).as_posix(),sha256=sha(path),**extra))
 seeds=[1] if args.smoke else config['seeds']
 for suite,spec in config['suites'].items():
  for n in ([256] if args.smoke else spec['sizes']):
   for seed in seeds:
    if args.campaign in ('scaling','static'):
     for dist in spec['distributions']:
      for radius in spec['radii']:
       rng=np.random.default_rng(seed);pts=points(rng,n,dist);q=points(rng,16 if args.smoke else config['queries'],'uniform');r2=int(radius*MAX)**2
       id=f'{suite}/{dist}-n{n}-r{radius}-s{seed}';path=root/'prepared'/(id+'.bin');write_data(path,pts,[(int(x),int(y),r2) for x,y in q]);add(id,suite,seed,n,path,queries=len(q),distribution=dist,radius_fraction=radius)
    else:
     for ratio in spec['update_ratios']:
      rng=random.Random(seed);initial=[(rng.randrange(MAX+1),rng.randrange(MAX+1)) for _ in range(n)];live=list(initial);events=[]
      count=64 if args.smoke else config['operations'];updates=int(count*ratio);kinds=([0,1]*(updates//2)+[0]*(updates%2))+[2]*(count-updates)
      if suite=='interleaved':rng.shuffle(kinds)
      for kind in kinds:
       if kind==0:x,y=rng.randrange(MAX+1),rng.randrange(MAX+1);live.append((x,y))
       elif kind==1:
        i=rng.randrange(len(live));x,y=live[i];live[i]=live[-1];live.pop()
       else:x,y=rng.randrange(MAX+1),rng.randrange(MAX+1)
       events.append((kind,x,y,int(config['radius']*MAX)**2 if kind==2 else 0))
      id=f'{suite}/n{n}-u{ratio}-s{seed}';path=root/'prepared'/(id+'.bin');dynamic_data(path,initial,events);add(id,suite,seed,n,path,operations=len(events),update_ratio=ratio)
 correct=fixtures(root)
 if args.campaign=='dynamic-circles':
  initial=[(100,100),(100,100),(103,104),(0,0),(MAX,MAX)];events=[(2,100,100,25),(1,100,100,0),(2,100,100,0),(0,100,100,0),(2,100,100,25)]
  for x,y in initial:events.extend([(1,x,y,0),(2,100,100,MAX_DISTANCE2)])
  events.extend([(0,7,9,0),(2,7,9,0),(1,7,9,0),(2,7,9,0)])
  path=root/'correctness/dynamic-updates.bin';dynamic_data(path,initial,events);correct.append(dict(id='dynamic-updates',path=path.relative_to(root).as_posix(),sha256=sha(path),n=len(initial)))
 roster=STATIC if args.campaign in ('scaling','static') else DYNAMIC
 algorithms=[dict(name=a,mode='static' if a in STATIC else 'dynamic_updates',provenance='manual integer-point reporting adaptation' if 'MANUALLY_ADAPTED_INTEGER_POINTS' in a else 'local dynamic adaptation' if 'ADAPTED_DYNAMIC' in a else 'implementation and adapter',binary='esa_runner_pargeo' if a=='pargeo' else 'esa_runner') for a in roster]
 manifest=dict(schema=1,name=args.campaign,smoke=args.smoke,policy=json.loads((BASE/'campaigns/execution.json').read_text()),geometry='closed circles on uint32 grid',algorithms=algorithms,cases=cases,correctness=correct)
 (root/'campaign.json').write_text(json.dumps(manifest,indent=2)+'\n');print(len(cases),'cases prepared; no benchmarks started')
if __name__=='__main__':main()
