"""Compile a selected frozen disk adapter against explicit pinned dependencies."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PROFILES={'2d':'_queue-disk-adapters-2d-20261114',
          'parity':'_queue-disk-adapters-parity-20261115',
          'ph-psi':'_queue-ph-psi-2d-3d-20261115'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=PROFILES,required=True)
    parser.add_argument('--algorithms',nargs='+',required=True)
    parser.add_argument('--third-party',type=Path,default=ROOT/'src/third_party')
    parser.add_argument('--square',type=Path,help='Square repository supplying captured rectangle headers and THST')
    args=parser.parse_args()
    if args.profile=='2d' and set(args.algorithms)-{'phtree','pgm_multidimensional','spatialindex','cgal_kd'}:
        parser.error('The November 14 profile contains phtree, pgm_multidimensional, spatialindex and cgal_kd only')
    source=ROOT/'reproducibility/2026-11-22'/PROFILES[args.profile]
    out=ROOT/'build/frozen-adapters'/args.profile;out.mkdir(parents=True,exist_ok=True)
    third=args.third_party.resolve()
    index=ROOT/'src/third_party/indexicon/indexes'
    includes=[source,third/'phtree-cpp/include',third/'space-tree-lib/include',
              third/'space-tree-lib/include/parlaylib/include',third/'space-tree-lib/include/libmorton/include',
              ROOT/'src/third_party/esa2026']
    if (source/'psi-patched').exists():includes.insert(0,source/'psi-patched')
    if (source/'indexicon-patched').exists():includes.insert(0,source/'indexicon-patched')
    includes.append(index)
    if any('pgm' in a for a in args.algorithms):
        from prepare_pgm_reporting import prepare
        includes.insert(0,prepare(ROOT))
    if args.square:
        square=args.square.resolve();rect=square/'src/third_party/rectangle'
        includes += [rect/'PAM/include',rect/'PAM/examples/range_query',rect/'parlaylib/include',square/'src/third_party/thst/include']
        if 'pargeo' in args.algorithms:
            compat=out/'pargeo-compat'
            subprocess.run([sys.executable,str(square/'tools/prepare_pargeo.py'),str(rect/'pargeo'),str(compat)],check=True)
            includes.insert(0,compat)
    common=[os.environ.get('CXX','g++'),'-std=c++20','-O3','-march=native','-DNDEBUG']
    common += ['-I'+str(p) for p in includes]
    ph=args.profile=='ph-psi'
    for algorithm in args.algorithms:
        flags=[];libs=[]
        if ph:
            macro={'phtree':'PH','psi':'PSI','indexicon_kd_3d':'INDEXICON','pgm_3d':'PGM','lsi_3d':'LSI','cgal_kd_3d':'CGAL'}.get(algorithm)
            if not macro:parser.error('Algorithm is not in the ph-psi profile: '+algorithm)
            flags=['-DFOLLOWUP_'+macro];file=source/'ph_psi_followup.cpp'
        else:
            file=source/'foreign_check.cpp'
            if algorithm in ('phtree','pgm_multidimensional','psi','spatialindex'):
                macro={'phtree':'PHTREE','pgm_multidimensional':'PGM','psi':'PSI','spatialindex':'SPATIALINDEX'}[algorithm]
                flags=['-DBACKEND_ADDITIONAL','-DADDITIONAL_'+macro]
            elif algorithm in ('cgal_kd','cgal_rt','pam','pargeo','thst'):
                macro={'cgal_kd':'EXACT_CGAL_2D','cgal_rt':'CGAL_RANGE','pam':'STREAM_PAM','pargeo':'EXACT_PARGEO','thst':'THST'}[algorithm]
                flags=['-DBACKEND_'+macro]
            elif algorithm.startswith('indexicon_'):
                macro={'indexicon_kdtree':'KDTREE','indexicon_quadtree':'QUADTREE','indexicon_mxcif':'MXCIF'}.get(algorithm)
                if not macro:parser.error('Unknown frozen Indexicon binary: '+algorithm)
                flags=['-DBACKEND_INDEXICON','-DINDEXICON_DISK_TRAVERSAL','-DINDEXICON_DIMS=2','-DINDEXICON_'+macro]
            else:parser.error('Unknown frozen adapter: '+algorithm)
        if algorithm in ('psi','pam','pargeo'):flags+=['-DPARLAY_SEQUENTIAL','-mcx16','-mbmi2']
        if 'pgm' in algorithm:flags+=['-mbmi2']
        if algorithm in ('spatialindex','lsi_3d'):libs+=['-lspatialindex']
        if 'cgal' in algorithm:flags+=['-frounding-math'];libs+=['-lgmp','-lmpfr']
        command=common+flags+[str(file)]+libs+['-o',str(out/algorithm)]
        print('Building',args.profile,algorithm,flush=True)
        subprocess.run(command,check=True)
    print('Build complete; no experiments started')


if __name__=='__main__':main()
