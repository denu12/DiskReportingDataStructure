"""Prepare every available ESA embedding/distribution case and every query."""
import json
from fractions import Fraction
from pathlib import Path
import re
import shutil
import time
import zipfile
import numpy as np
from ddim_campaign import ROOT, MAX, binary, save, sha

def main():
    root=ROOT/'data/esa2026-ddim-full';archives=root/'archives'
    cases=[]
    dimensions=json.loads((ROOT/'campaigns/esa2026-ddim/campaign.json').read_text())['dimensions']
    started=time.monotonic()
    for name,family in [('embedding_data.zip','embedding'),('distributions.zip','distributions')]:
        path=archives/name
        while not path.exists():
            save(root/'preparation-status.json',dict(status='waiting_for_archive',archive=name,prepared=len(cases)))
            if time.monotonic()-started>7200:raise RuntimeError('Archive delivery exceeded two hours')
            time.sleep(10)
        with zipfile.ZipFile(path) as z:
            members=[]
            for i in z.infolist():
                m=re.search(r'(?:dim-|_d)(\d+)(?:_|\.)',i.filename)
                if m and i.filename.endswith('_train.csv') and not i.filename.startswith('__MACOSX/') and int(m[1]) in dimensions:
                    members.append((i,int(m[1])))
            for entry,d in sorted(members,key=lambda x:(x[1],x[0].file_size,x[0].filename)):
                prefix=entry.filename[:-len('_train.csv')];stem=Path(prefix).name;case_id=family+'/'+stem
                metadata=root/'metadata'/f'{case_id}.json'
                save(root/'preparation-status.json',dict(status='preparing',case=case_id,prepared=len(cases)))
                if metadata.exists():
                    info=json.loads(metadata.read_text())
                    if sha(root/info['path'])!=info['sha256']:raise RuntimeError('Prepared checksum mismatch')
                    cases.append(info);continue
                sources=[]
                for suffix in ['_train.csv','_query_points.csv','_query_radii.csv']:
                    member=prefix+suffix;target=root/'source'/family/Path(member).name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    if not target.exists():
                        temporary=target.with_suffix('.partial')
                        with z.open(member) as src,temporary.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
                        temporary.replace(target)
                    sources.append(dict(path=target.relative_to(root).as_posix(),sha256=sha(target),member=member,zip_crc32=z.getinfo(member).CRC))
                points=np.loadtxt(root/sources[0]['path'],delimiter=',',dtype=np.float32,ndmin=2).astype(np.float64)
                centers=np.loadtxt(root/sources[1]['path'],delimiter=',',dtype=np.float32,ndmin=2).astype(np.float64)
                radii=np.loadtxt(root/sources[2]['path'],dtype=np.float64,ndmin=1)
                if points.shape[1]!=d or centers.shape[1]!=d or radii.shape!=(len(centers),):raise ValueError('Unexpected dimensions')
                if not all(np.isfinite(a).all() for a in [points,centers,radii]) or (radii<0).any():raise ValueError('Nonfinite geometry')
                origin=np.minimum(points.min(axis=0),centers.min(axis=0))
                extent=float(np.max(np.maximum(points.max(axis=0),centers.max(axis=0))-origin))
                scale=(MAX-2)/extent if extent else 1.0
                # In-place affine conversion keeps peak preparation memory bounded.
                points-=origin;points*=scale;points+=1;np.rint(points,out=points)
                p=points.astype('<u4');del points
                centers-=origin;centers*=scale;centers+=1;np.rint(centers,out=centers)
                q=centers.astype('<u4');del centers
                sf=Fraction.from_float(scale)
                r2=[min(d*MAX*MAX,int((Fraction.from_float(float(r))*sf)**2)) for r in radii]
                out=root/'prepared'/f'{case_id}.bin';binary(out,d,p,q,r2)
                info=dict(id=case_id,family=family,dimension=d,points=len(p),queries=len(q),path=out.relative_to(root).as_posix(),sha256=sha(out),sources=sources,
                          conversion=dict(origin=origin.tolist(),scale=scale,rounding='nearest, ties to even',radius_rule='floor exact scaled squared radius; cap d*UINT32_MAX^2',queries='all',point_dtype='f32 promoted to f64'))
                del p,q,r2,radii
                save(metadata,info);cases.append(info);print('prepared',case_id,info['points'],info['queries'],flush=True)
    save(root/'campaign.json',dict(name='esa2026-ddim-full',cases=cases,selection='all available embedding and distribution files in supported dimensions; every source query',dimensions=dimensions))
    save(root/'preparation-status.json',dict(status='complete',cases=len(cases)))

if __name__=='__main__':main()
