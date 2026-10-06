"""Prepare an adapted ESA 2D campaign; never launches benchmarks."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import struct
import numpy as np

STATIC = ['hcds:best','hcds_hilbert:best','ehcds:best','ehcds_hilbert:best',
 'boost_lin','boost_quad','boost_star','cgal_rt','cgal_kd','thst_quad','thst_rtree',
 'pargeo','pam','pkd','naive','chan_sss','ann_fr','stann_fr'] + ['esa_'+n for n in
 ['sprk','kiddo','nabo','neighbourhood','vptree','orthtree','grid','sklearn_kd','sklearn_ball','snn','nanoflann']]
DYNAMIC = ['hcds_dyn','hcds_hilbert_dyn','hcds_dyn_std','boost_lin_dyn','boost_quad_dyn','boost_star_dyn',
 'chan_sss_dyn_ADAPTED_DYNAMIC','kiddo_mutable_dyn_UPSTREAM','nanoflann_dyn_UPSTREAM',
 'pkd_dyn_UPSTREAM','thst_rtree_dyn_UPSTREAM','thst_quad_dyn_UPSTREAM']
MAX = 2**32-1
MAX_DISTANCE2 = 2*MAX*MAX
UPSTREAM = 'a81b216a2a63bde3d4447e4053b4ca31081fe286'
POI = [('parking_hospital','parking','hospital'),('restaurant_trainstation','restaurant','trainstation'),
 ('pharmacy_hospital','pharmacy','hospital'),('busstop_trainstation','busstop','trainstation'),
 ('atm_supermarket','atm','supermarket'),('hospital_university','hospital','university'),('bakery_university','bakery','university')]

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write_data(path, points, queries):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('wb') as f:
  f.write(struct.pack('<8sQQ',b'ESA2D01\0',len(points),len(queries)))
  f.write(np.asarray(points,dtype='<u4').reshape((-1,2)).tobytes())
  for x,y,r2 in queries:f.write(struct.pack('<IIQQ',int(x),int(y),int(r2)&(2**64-1),int(r2)>>64))

def convert(train, query, radii, output):
 # Match upstream CSV point parsing (f32), then promote exactly to f64.
 points=np.loadtxt(train,delimiter=',',dtype=np.float32,ndmin=2).astype(np.float64)
 centers=np.loadtxt(query,delimiter=',',dtype=np.float32,ndmin=2).astype(np.float64)
 if points.shape[1]!=2 or centers.shape[1]!=2:raise ValueError('Not native 2D')
 if not np.isfinite(points).all() or not np.isfinite(centers).all():raise ValueError('Nonfinite coordinates')
 radii=np.full(len(centers),radii) if isinstance(radii,(int,float)) else np.loadtxt(radii,dtype=np.float64,ndmin=1)
 if radii.shape!=(len(centers),) or not np.isfinite(radii).all() or np.any(radii<0):raise ValueError('Invalid radii')
 origin=np.minimum(points.min(axis=0),centers.min(axis=0))
 upper=np.maximum(points.max(axis=0),centers.max(axis=0))
 extent=float(np.max(upper-origin));scale=float((MAX-2)/extent) if extent else 1.0
 p=np.rint((points-origin)*scale+1).astype('<u4');q=np.rint((centers-origin)*scale+1).astype('<u4')
 sf=Fraction.from_float(scale)
 radius2=[min(MAX_DISTANCE2,int((Fraction.from_float(float(r))*sf)**2)) for r in radii]
 write_data(output,p,[(int(c[0]),int(c[1]),r) for c,r in zip(q,radius2)])
 return dict(n=len(p),queries=len(q),origin=origin.tolist(),scale=scale,grid_padding=1,
   rounding='nearest integer, ties to even',radius_rule='floor((exact binary64 radius * exact binary64 scale)^2), capped at maximum grid distance squared',
   point_csv_dtype='f32 as upstream; exact promotion to f64 before affine conversion',
   mean_radius_original=float(radii.mean()),mean_radius_grid=float(radii.mean()*scale),
   source_points_sha256=sha(train),source_queries_sha256=sha(query),sha256=sha(output))

def fixtures(root):
 rng=random.Random(97123)
 points=[(0,0),(MAX,MAX),(0,MAX),(MAX,0),(100,100),(100,100),(103,104),(97,96)]
 points += [(rng.randrange(MAX+1),rng.randrange(MAX+1)) for _ in range(240)]
 queries=[(0,0,0),(MAX,MAX,0),(100,100,25),(100,100,24),(100,100,26),(0,0,MAX_DISTANCE2)]
 queries += [(rng.randrange(MAX+1),rng.randrange(MAX+1),rng.randrange(MAX+1)**2) for _ in range(60)]
 data=[('boundary_duplicates_random',points,queries),('empty',[],[(0,0,0),(100,100,100)]),
       ('collinear',[(100,i) for i in range(96)],[(100,48,24**2),(100,0,0),(100,48,100**2)])]
 result=[]
 for name,p,q in data:
  target=root/'correctness'/f'{name}.bin';write_data(target,p,q)
  result.append(dict(id=name,path=target.relative_to(root).as_posix(),n=len(p),queries=len(q),sha256=sha(target)))
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]/"data/esa2026-2d");args=ap.parse_args()
 root=args.root.resolve();
 if (root/'campaign.json').exists():raise RuntimeError('Prepared campaign exists; archive it before replacing inputs')
 root.mkdir(parents=True,exist_ok=True);data=root/'data';cases=[]
 metadata={r['export_prefix']:r for r in csv.DictReader((data/'embedding/metadata.csv').open())}
 for category in ['embedding','distributions']:
  for train in sorted((data/category).glob('*_train.csv')):
   stem=train.name[:-len('_train.csv')];q=train.with_name(stem+'_query_points.csv');r=train.with_name(stem+'_query_radii.csv')
   case_id=category+'/'+stem;output=root/'prepared'/(case_id+'.bin')
   info=convert(train,q,r,output)
   cases.append(dict(id=case_id,suite=category,path=output.relative_to(root).as_posix(),conversion=info,n=info['n'],queries=info['queries'],upstream_metadata=metadata.get(stem),source_radii_sha256=sha(r)))
   print(case_id,info['n'],flush=True)
 for name,p,q in POI:
  for radius in [500.,1000.,2000.,5000.]:
   case_id=f'poi/{name}_r{int(radius)}';output=root/'prepared'/(case_id+'.bin')
   info=convert(data/'poi'/f'{p}.csv',data/'poi'/f'{q}.csv',radius,output)
   cases.append(dict(id=case_id,suite='poi',path=output.relative_to(root).as_posix(),conversion=info,n=info['n'],queries=info['queries'],radius_original=radius))
   print(case_id,info['n'],flush=True)
 algorithms=[dict(name=a,mode='static' if a in STATIC else 'incremental_build_then_static_queries',
   provenance='Local dynamic adaptation' if 'ADAPTED_DYNAMIC' in a else 'existing suite implementation and adapter',
   binary='esa_runner_pargeo' if a=='pargeo' else 'esa_runner') for a in STATIC]
 manifest=dict(schema=1,name='esa-2026-2d-integer-grid',status='prepared_not_started',upstream_commit=UPSTREAM,
  upstream_url='https://github.com/wembed-pdf/rembed',zenodo_record=21243483,geometry='closed Euclidean circles on common integer grid',
  policy=json.loads((Path(__file__).resolve().parents[1]/'campaigns/execution.json').read_text()),
  radius_hint_policy='existing adapters: fixed defaults, no test-query tuning; differs from upstream set_radius_hint(mean radius)',
  algorithms=algorithms,cases=cases,correctness=fixtures(root))
 (root/'campaign.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps({'cases':len(cases),'static_entries':len(STATIC),'dynamic_entries':0,'screen_jobs':len(cases)*len(algorithms)}))

if __name__=='__main__':main()
