"""Check built frozen profiles against their own exact boundary oracle."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from experiment_integrity import boundary_case

PARITY={'cgal_kd':['cgal_kd'],'cgal_rt':['cgal_rt'],'pam':['pam'],'pargeo':['pargeo'],
        'thst':['thst_quad','thst_rtree'],'spatialindex':['lsi_linear','lsi_quadratic','lsi_rstar','lsi_str'],
        'indexicon_kdtree':['indexicon_kdtree_adaptive','indexicon_kdtree_round_robin','indexicon_kdtree_longest_axis'],
        'indexicon_quadtree':['indexicon_quadtree_pr','indexicon_quadtree_pseudo_median','indexicon_quadtree_longest_axis'],
        'indexicon_mxcif':['indexicon_mxcif_quadtree']}
FOLLOWUP={'phtree':['phtree'],'psi':['psi_kd','psi_orth','psi_spac_z','psi_spac_h'],
          'indexicon_kd_3d':['indexicon_kdtree_adaptive','indexicon_kdtree_round_robin','indexicon_kdtree_longest_axis'],
          'pgm_3d':['pgm_multidimensional'],'lsi_3d':['lsi_linear','lsi_quadratic','lsi_rstar','lsi_str'],
          'cgal_kd_3d':['cgal_kd']}
checks=0
with tempfile.TemporaryDirectory() as directory:
    cases={d:boundary_case(directory,d,format2d=d==2) for d in (2,3)}
    for profile,mapping in [('parity',PARITY),('ph-psi',FOLLOWUP)]:
        for binary,algorithms in mapping.items():
            exe=ROOT/'build/frozen-adapters'/profile/binary
            if not exe.exists():continue
            dims=(2,) if profile=='parity' else (2,3) if binary in ('phtree','psi') else (3,)
            for d in dims:
                for algorithm in algorithms:
                    rows=[]
                    for flags in ([],['--bench']):
                        p=subprocess.run([str(exe),cases[d]['path'],algorithm,*flags],capture_output=True,text=True,timeout=30)
                        row=json.loads(p.stdout) if p.stdout.strip() else {}
                        assert p.returncode==0 and row.get('status')=='success',(profile,binary,algorithm,d,p.returncode,p.stderr,row)
                        rows.append(row);checks+=1
                    assert rows[0]['answers']==rows[1]['answers'],(algorithm,d,rows)
print(f'{checks} frozen adapter oracle/bench consistency checks passed')
