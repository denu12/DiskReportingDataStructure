"""Current competitor rosters and integer 2D workload serialization."""
import hashlib
import struct
import numpy as np

STATIC = ['Morton','MortonSIMD',
 'boost_lin','boost_quad','boost_star','cgal_rt','cgal_kd','thst_quad','thst_rtree',
 'pargeo','pam','pkd','naive','chan_sss','ann_fr','stann_fr','esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS'] + ['esa_'+n for n in
 ['sprk_CHEATING_IDS_ONLY','kiddo','nabo','neighbourhood','vptree','orthtree','grid','sklearn_kd','sklearn_ball','snn','nanoflann']]
DYNAMIC = ['boost_lin_dyn','boost_quad_dyn','boost_star_dyn',
 'chan_sss_dyn_ADAPTED_DYNAMIC','kiddo_mutable_dyn_UPSTREAM','nanoflann_dyn_UPSTREAM',
 'pkd_dyn_UPSTREAM','thst_rtree_dyn_UPSTREAM','thst_quad_dyn_UPSTREAM']
MAX = 2**32-1
MAX_DISTANCE2 = 2*MAX*MAX

DIMENSIONAL = [
 'chan_sss_ddim_MANUALLY_ADAPTED', 'stann_fr_ddim_MANUALLY_ADAPTED',
 'ann_fr', 'boost_lin', 'boost_quad', 'boost_star', 'esa_sprk', 'esa_kiddo',
 'esa_nabo', 'esa_neighbourhood', 'esa_vptree', 'esa_orthtree', 'esa_grid',
 'esa_sklearn_kd', 'esa_sklearn_ball', 'esa_snn', 'esa_snn_rust',
 'esa_nanoflann', 'cgal_kd']

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write_data(path, points, queries):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('wb') as f:
  f.write(struct.pack('<8sQQ',b'ESA2D01\0',len(points),len(queries)))
  f.write(np.asarray(points,dtype='<u4').reshape((-1,2)).tobytes())
  for x,y,r2 in queries:f.write(struct.pack('<IIQQ',int(x),int(y),int(r2)&(2**64-1),int(r2)>>64))
