"""Prepare GeographyLarge from real OSM POIs; no benchmark execution."""
import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
import urllib.request
import numpy as np
from campaign_paths import campaign_directory
from algorithm_labels import metadata

ROOT = Path(__file__).resolve().parents[1]
MAX = 2**32 - 1

def sha(path, kind='sha256'):
    with path.open('rb') as f: return hashlib.file_digest(f, kind).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(value, indent=2)); tmp.replace(path)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=ROOT)
    ap.add_argument('--proxy', help='HTTP proxy for preparation downloads')
    args = ap.parse_args(); root = args.root.resolve()
    spec_path = campaign_directory(root,'GeographyLarge')/'campaign.json'
    spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
    folder = root/'data/GeographyLarge'; folder.mkdir(parents=True, exist_ok=True)
    control = folder/'preparation-status.json'
    if (folder/'campaign.json').exists(): raise RuntimeError('Prepared campaign exists; use a fresh destination')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', RAYON_NUM_THREADS='1', CARGO_BUILD_JOBS='1')
    if args.proxy:
        for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']: env[k] = args.proxy
        env['CARGO_HTTP_PROXY'] = args.proxy
        urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({'http':args.proxy,'https':args.proxy})))
    started = time.time()
    def status(stage, **extra):
        save(control, dict(status='preparing', stage=stage, started_unix=started, updated_unix=time.time(), **extra))
    def call(command, label):
        with (folder/(label+'.log')).open('a') as f:
            subprocess.run(command, env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
    try:
        status('dependencies')
        runtime = root/'toolchains/geography-large'; runtime.mkdir(parents=True, exist_ok=True)
        package = runtime/'python'
        if not (package/'osmium').exists():
            call([sys.executable,'-m','pip','install','--only-binary=:all:','--no-deps','--target',str(package),'osmium==4.3.1'], 'dependencies')
        sys.path.insert(0,str(package)); import osmium
        source = root/'src/third_party/esa2026-workloads/benchmark/poi'
        for name, expected in spec['source']['extractor_files'].items():
            if sha(source/name) != expected: raise RuntimeError('Changed upstream extractor: '+name)
        crate = runtime/'poi'
        if not crate.exists(): shutil.copytree(source,crate)
        for name, expected in spec['source']['extractor_files'].items():
            if sha(crate/name) != expected: raise RuntimeError('Changed extractor build copy: '+name)
        shutil.copy2(root/'src/third_party/esa2026/REMBED-LICENSE',crate/'UPSTREAM-LICENSE')
        cargo = Path(os.environ.get('CARGO') or shutil.which('cargo') or 'cargo')
        env['PATH'] = str(cargo.parent)+os.pathsep+env.get('PATH','')
        env['CARGO_TARGET_DIR'] = str(runtime/'target')
        binary = runtime/'target/release/poi'
        if not binary.exists(): call([str(cargo),'build','--release','--manifest-path',str(crate/'Cargo.toml'),'--jobs','1'], 'build-extractor')
        osm = folder/'source/europe-260930.osm.pbf'; osm.parent.mkdir(parents=True,exist_ok=True)
        if not osm.exists():
            status('download', expected_bytes=spec['source']['bytes'])
            partial = osm.with_suffix(osm.suffix+'.partial')
            offset = partial.stat().st_size if partial.exists() else 0
            req = urllib.request.Request(spec['source']['url'], headers={'Range':f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(req,timeout=120) as response:
                if offset and (response.status != 206 or not response.headers.get('Content-Range','').startswith(f'bytes {offset}-')): raise RuntimeError('Source resume range not honored')
                with partial.open('ab' if offset else 'wb') as out:
                    last=0
                    while chunk := response.read(4*1024*1024):
                        out.write(chunk)
                        if time.time()-last>10:
                            out.flush(); status('download',downloaded_bytes=partial.stat().st_size,expected_bytes=spec['source']['bytes']);last=time.time()
            if partial.stat().st_size != spec['source']['bytes'] or sha(partial,'md5') != spec['source']['md5']: raise RuntimeError('OSM download checksum/size mismatch')
            partial.replace(osm)
        if osm.stat().st_size != spec['source']['bytes'] or sha(osm,'md5') != spec['source']['md5']: raise RuntimeError('Cached OSM checksum/size mismatch')
        save(folder/'source/receipt.json',dict(spec['source'],sha256=sha(osm)))
        filtered = folder/'source/poi-reference-complete.osm.pbf'
        if not filtered.exists():
            status('prefilter')
            tags = [('amenity',v) for v in ['parking','atm','bank','restaurant','cafe','fast_food','bar','pub','pharmacy','hospital','doctors','school','university','place_of_worship','post_office','fuel']]
            tags += [('shop','supermarket'),('shop','bakery'),('highway','bus_stop')]
            tags += [('railway',v) for v in ['station','halt','tram_stop']]
            tags += [('public_transport',v) for v in ['station','stop_position','platform']]
            tmp = filtered.with_name('poi-filtered.partial.osm.pbf')
            if tmp.exists(): tmp.unlink()
            with osmium.BackReferenceWriter(str(tmp),str(osm),remove_tags=False) as writer:
                for obj in osmium.FileProcessor(str(osm)).with_filter(osmium.filter.TagFilter(*tags)): writer.add(obj)
            tmp.replace(filtered)
            save(folder/'source/prefilter-receipt.json',dict(sha256=sha(filtered),tag_filter=tags,reference_complete=True,remove_reference_tags=False,pyosmium='4.3.1'))
        csv_dir = folder/'source/extracted'
        receipt = folder/'source/extraction-receipt.json'
        if not receipt.exists():
            status('upstream_extraction')
            call([str(binary),str(filtered),'--output',str(csv_dir)], 'extractor')
            save(receipt,dict(binary_sha256=sha(binary),cargo_lock_sha256=sha(crate/'Cargo.lock'),files={p.name:sha(p) for p in sorted(csv_dir.glob('*.csv'))}))
        pool_path = folder/'source/pooled-f32.bin'; pool_info = folder/'source/pool.json'
        if not pool_info.exists():
            status('pooling'); count=0; categories={}
            with pool_path.open('wb') as out:
                for path in sorted(csv_dir.glob('*.csv')):
                    before=count
                    with path.open() as f:
                        import itertools
                        while lines := list(itertools.islice(f,8192)):
                            a=np.loadtxt(lines,delimiter=',',dtype='<f4',ndmin=2)
                            if a.shape[1]!=2 or not np.isfinite(a).all():raise ValueError('Invalid extracted coordinates')
                            out.write(a.tobytes());count+=len(a)
                    categories[path.stem]=count-before
            save(pool_info,dict(points=count,category_counts=categories,sha256=sha(pool_path),coordinate_dtype='f32, matching ESA input parsing'))
        info=json.loads(pool_info.read_text()); count=info['points']; q=spec['queries']; maximum=max(spec['sizes'])
        if count<maximum+q:raise RuntimeError(f'Only {count} genuine POIs; need {maximum+q}; no point replication permitted')
        pool=np.memmap(pool_path,dtype='<f4',mode='r',shape=(count,2))
        lo=np.array([np.inf,np.inf]);hi=-lo
        for start in range(0,count,65536):
            a=pool[start:start+65536].astype(np.float64);lo=np.minimum(lo,a.min(axis=0));hi=np.maximum(hi,a.max(axis=0))
        scale=(MAX-2)/float(max(hi-lo)); sf=Fraction.from_float(scale)
        def grid(a):return np.rint((a.astype(np.float64)-lo)*scale+1).astype('<u4')
        STATIC = spec['algorithms']
        cases=[]; metadata=folder/'metadata';metadata.mkdir(exist_ok=True)
        for seed in spec['seeds']:
            status('sampling_and_conversion',seed=seed,completed_cases=len(cases),total_cases=spec['expected_instances'])
            chosen=np.random.default_rng(seed).choice(count,size=maximum+q,replace=False)
            query=grid(pool[chosen[:q]]); index=grid(pool[chosen[q:]])
            for n in spec['sizes']:
                for radius in spec['radii']:
                    case_id=f'geography-large/pooled-n{n}-r{radius}-s{seed}'
                    output=folder/'prepared'/(case_id+'.bin');output.parent.mkdir(parents=True,exist_ok=True)
                    rr=min(2*MAX*MAX,int((Fraction(radius)*sf)**2))
                    with output.open('wb') as f:
                        f.write(struct.pack('<8sQQ',b'ESA2D01\0',n,q));f.write(index[:n].tobytes())
                        for x,y in query:f.write(struct.pack('<IIQQ',int(x),int(y),rr&MAX_DISTANCE_MASK,rr>>64))
                    cases.append(dict(id=case_id,suite='geography-large',dimension=2,seed=seed,n=n,points=n,queries=q,radius=radius,path=output.relative_to(folder).as_posix(),sha256=sha(output),status='ready'))
            save(metadata/f'sampling-seed-{seed}.json',dict(seed=seed,sampled_rows=maximum+q,held_out_queries=q,source_row_indices_sha256=hashlib.sha256(chosen.astype('<u8').tobytes()).hexdigest(),nested_sizes=spec['sizes']))
        assert len(cases)==spec['expected_instances'] and all(1000000<=c['n']<=5000000 and c['queries']==1000 for c in cases)
        manifest=dict(schema=1,name='GeographyLarge',input_format='ESA2D01',status='ready',specification_sha256=sha(spec_path),algorithms=STATIC,cases=cases,dimensions=[2],geometry=spec['geometry'],conversion=dict(origin=lo.tolist(),scale=scale,rounding='nearest ties to even',coordinate_parse='f32 promoted to f64',shared_grid='whole extracted POI pool'),source=spec['source'],pool=info,comparison_contract=dict(coordinates='common uint32 grid',output='explicit integer points',exceptions={'esa_sprk_CHEATING_IDS_ONLY':'point_ids_only'}))
        manifest['algorithm_metadata'] = {a: metadata(a) for a in manifest['algorithms']}
        save(folder/'campaign.json',manifest)
        save(control,dict(status='ready',stage='complete',instances=len(cases),pool_points=count,started_unix=started,finished_unix=time.time()))
        print(json.dumps(dict(status='ready',instances=len(cases),pool_points=count)))
    except Exception as error:
        save(control,dict(status='needs_attention',error=str(error),started_unix=started,updated_unix=time.time()));raise

MAX_DISTANCE_MASK=2**64-1
if __name__=='__main__':main()
