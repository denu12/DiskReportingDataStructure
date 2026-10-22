"""Check the original SQL example and exact reported multisets across cell boundaries."""
import argparse
import importlib.util
import subprocess
import json
from pathlib import Path
import random
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'src/runner/dimensional/postgres_check.py'
spec=importlib.util.spec_from_file_location('postgres_check',path)
pg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pg)


def write_case(path,d,points,queries):
    with path.open('wb') as stream:
        stream.write(struct.pack('<IQQ',d,len(points),len(queries)))
        for point in points:stream.write(struct.pack('<'+'I'*d,*point))
        for center,r2 in queries:
            stream.write(struct.pack('<'+'I'*d,*center))
            stream.write(struct.pack('<QQ',r2&((1<<64)-1),r2>>64))


def route_checks(folder):
    sys.path.insert(0,str(ROOT/'tools'))
    from original_runner import dependency_files
    from algorithm_backends_2d import binary
    from backends import command
    from algorithm_labels import metadata
    assert binary('postgres_zrange')=='original_runner'
    assert metadata('postgres_zrange')['output_contract']=='point_ids_only'
    assert all(p.is_file() for p in dependency_files('postgres_zrange'))
    for d in [2,3]:
        path=folder/f'route-{d}.bin'
        points=[(0,)*d,(0,)*d,tuple([3,4]+[0]*(d-2)),(2**32-1,)*d]
        write_case(path,d,points,[((0,)*d,25)])
        if d==2:
            payload=path.read_bytes()[20:]
            path.write_bytes(struct.pack('<8sQQ',b'ESA2D01\0',4,1)+payload)
        for bench in [False,True]:
            out=folder/'route-output.json'
            args=([sys.executable,str(ROOT/'tools/original_runner.py'),'postgres_zrange',str(path),
                   'bench' if bench else 'verify',str(out)] if d==2 else
                  command('postgres_zrange')+[str(path),'postgres_zrange']+(['--bench'] if bench else []))
            run=subprocess.run(args,capture_output=True,text=True,check=True)
            result=json.loads(run.stdout)
            assert result['status']=='success' and result['answers']==3,result
            if d==2:assert json.loads(out.read_text())['answers']==3
    print('Four campaign-route checks passed',flush=True)


def main():
    folder=ROOT/'build/postgresql-validation';folder.mkdir(parents=True,exist_ok=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--routes-only',action='store_true')
    args=parser.parse_args()
    route_checks(folder)
    if args.routes_only:return
    rows=[]
    with pg.database() as db:
        expected=[[16371,16371],[16374,16375],[16377,16377],[16379,16383],
                  [27298,27299],[27304,27307],[38225,38225],[38227,38231],[49152,49155]]
        actual=[[int(x) for x in row] for row in db.execute('SELECT * FROM RefineZOrderRange(16371,49155,8,2)')]
        assert actual==expected,actual
    for d in [2,3,8,32,63,64]:
        rng=random.Random(675+d);zero=(0,)*d;maximum=(2**32-1,)*d
        for name in ['mixed','empty']:
            points=[] if name=='empty' else [zero,zero,maximum,tuple([3,4]+[0]*(d-2))]+[
                tuple(rng.randrange(2**32) for _ in range(d)) for _ in range(61)]
            queries=[(zero,0),(zero,24),(zero,25),(maximum,0),(zero,d*(2**32-1)**2),
                     ((2**31,)*d,(2**30)**2)]
            # Points and query faces straddle coarse-cell boundaries.
            if points:
                shift=32-min(31,63//d) if d<=63 else 32
                edge=min(2**32-1,1<<shift)
                points.extend([(edge,)*d,(edge-1,)*d])
                queries.extend([((edge,)*d,0),((edge,)*d,d)])
            path=folder/f'{d}-{name}.bin';write_case(path,d,points,queries)
            expected_count=sum(sum(sum((x-y)**2 for x,y in zip(p,c))<=r2 for p in points) for c,r2 in queries)
            for bench in [False,True]:
                result=pg.run(path,bench)
                wanted='success' if d<=63 else 'unsupported_input'
                assert result['status']==wanted,result
                if d<=63:assert result['answers']==expected_count,result
                rows.append(dict(result,case=name,dimension=d,bench=bench))
                print(d,name,'bench' if bench else 'check',result['status'],flush=True)
    (folder/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(f'{len(rows)} checks passed; original SQL example passed')


if __name__=='__main__':main()
