"""Prepare synthetic dimensional workloads; never launch benchmarks."""
import argparse
import itertools
import json
from pathlib import Path
import struct
import time
import numpy as np
from campaign_paths import campaign_directory
from algorithm_labels import metadata
from prepare import points
from workloads import MAX, sha

ROOT = Path(__file__).resolve().parents[1]

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)

def prepare(name, destination, smoke):
    definition = campaign_directory(ROOT, name)/'campaign.json'
    spec = json.loads(definition.read_text(encoding='utf-8-sig'))
    d = spec['dimension']
    if d != 3 or spec['input_format'] != 'ddim-u32':
        raise ValueError('Expected the synthetic 3D campaign definition')
    folder = destination/name
    if (folder/'campaign.json').exists():
        raise RuntimeError('Prepared campaign already exists: '+name)
    seeds = [1] if smoke else spec['seeds']
    plan = [(suite,n,seed,dist,radius)
            for suite,s in spec['suites'].items()
            for n,seed,dist,radius in itertools.product(
                [256] if smoke else s['sizes'], seeds, s['distributions'], s['radii'])]
    state = dict(status='running', name=name, total=len(plan), completed=0,
                 started_unix=time.time(), smoke=smoke, current=None)
    status_path = folder/'preparation-status.json'
    save(status_path,state)
    rows=[]
    try:
        for suite,n,seed,distribution,radius in plan:
            case_id=f'{suite}/{distribution}-n{n}-r{radius}-s{seed}'
            state['current']=case_id;save(status_path,state)
            rng=np.random.default_rng(seed)
            indexed=points(rng,n,distribution,d)
            centers=points(rng,16 if smoke else spec['queries'],'uniform',d)
            radius_squared=int(radius*MAX)**2
            output=folder/'prepared'/(case_id+'.bin')
            output.parent.mkdir(parents=True,exist_ok=True)
            temporary=output.with_suffix('.partial')
            with temporary.open('wb') as stream:
                stream.write(struct.pack('<IQQ',d,n,len(centers)))
                indexed.astype('<u4',copy=False).tofile(stream)
                for center in centers:
                    stream.write(center.astype('<u4',copy=False).tobytes())
                    stream.write(struct.pack('<QQ',radius_squared&((1<<64)-1),radius_squared>>64))
            temporary.replace(output)
            rows.append(dict(id=case_id,suite=suite,dimension=d,n=n,queries=len(centers),
                             seed=seed,distribution=distribution,radius_fraction=radius,
                             path=output.relative_to(folder).as_posix(),sha256=sha(output),status='ready'))
            del indexed,centers
            state['completed']+=1;save(status_path,state)
            print(name,case_id,'ready',flush=True)
        manifest=dict(spec,cases=rows,status='ready',smoke=smoke,
                      specification_sha256=sha(definition),
                      generator_sha256=sha(Path(__file__)),
                      point_generator_sha256=sha(ROOT/'tools/prepare.py'),
                      numpy_version=np.__version__)
        manifest['algorithm_metadata'] = {a: metadata(a) for a in manifest['algorithms']}
        save(folder/'campaign.json',manifest)
        state.update(status='complete',current=None,finished_unix=time.time());save(status_path,state)
    except Exception as error:
        state.update(status='needs_attention',error=str(error),finished_unix=time.time());save(status_path,state)
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign',nargs='+',choices=['Scaling3D','Static3D'],required=True)
    ap.add_argument('--dest',type=Path,default=ROOT/'data',help='Parent directory for prepared campaign folders')
    ap.add_argument('--smoke',action='store_true',help='Small ordinary workload for checking the input format')
    args=ap.parse_args()
    for name in args.campaign:prepare(name,args.dest.resolve(),args.smoke)
    print('Preparation complete; no benchmarks started',flush=True)

if __name__=='__main__':main()
