"""Prepare and run the bounded ESA dimensional correctness campaign.

Linux execution; separate from the timing campaign controller. No competitor
changes, performance repetitions or regression-test framework.
"""
import argparse
import collections
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import time
import zipfile

import numpy as np
from import_data import RECORD, RemoteZip, request

ROOT = Path(__file__).resolve().parents[1]
MAX = 2**32 - 1


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.partial')
    tmp.write_text(json.dumps(value, indent=2))
    tmp.replace(path)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def binary(path, d, points, centers, radii2):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        f.write(struct.pack('<IQQ', d, len(points), len(centers)))
        f.write(np.asarray(points, dtype='<u4').reshape(-1, d).tobytes())
        for p, r in zip(centers, radii2):
            f.write(struct.pack('<' + 'I'*d + 'QQ', *map(int, p), r & (2**64-1), r >> 64))


def prepare(data, policy):
    data.mkdir(parents=True, exist_ok=True)
    if (data/'campaign.json').exists():
        return json.loads((data/'campaign.json').read_text())
    cached = ROOT/'data/esa2026-2d/data/zenodo-record.json'
    if cached.exists():
        record = json.loads(cached.read_text())
    else:
        with request(RECORD) as f:
            record = json.load(f)
    save(data/'zenodo-record.json', record)
    cases = []
    for archive in record['files']:
        if archive['key'] not in ('embedding_data.zip', 'distributions.zip'):
            continue
        family = 'embedding' if archive['key'].startswith('embedding') else 'distributions'
        with zipfile.ZipFile(RemoteZip(archive['links']['self'], archive['size'])) as z:
            groups = collections.defaultdict(list)
            for info in z.infolist():
                m = re.search(r'(?:dim-|_d)(\d+)(?:_|\.)', info.filename)
                if m and info.filename.endswith('_train.csv') and not info.filename.startswith('__MACOSX/'):
                    d = int(m[1])
                    if d in policy['dimensions']:
                        groups[d].append(info)
            for d, entries in sorted(groups.items()):
                chosen = min(entries, key=lambda i: (i.file_size, i.filename))
                prefix = chosen.filename[:-len('_train.csv')]
                sources = []
                for suffix in ('_train.csv', '_query_points.csv', '_query_radii.csv'):
                    member = prefix + suffix
                    info = z.getinfo(member)
                    dest = data/'source'/family/Path(member).name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        content = z.read(member)  # Full read checks ZIP CRC.
                        dest.write_bytes(content)
                    sources.append(dict(member=member, path=dest.relative_to(data).as_posix(),
                                        sha256=sha(dest), zip_crc32=info.CRC))
                paths = [data/s['path'] for s in sources]
                points = np.loadtxt(paths[0], delimiter=',', dtype=np.float32, ndmin=2).astype(np.float64)
                centers = np.loadtxt(paths[1], delimiter=',', dtype=np.float32, ndmin=2).astype(np.float64)
                radii = np.loadtxt(paths[2], dtype=np.float64, ndmin=1)
                if points.shape[1] != d or centers.shape[1] != d or radii.shape != (len(centers),):
                    raise ValueError('Unexpected dataset shape')
                if not all(np.isfinite(a).all() for a in (points, centers, radii)) or (radii < 0).any():
                    raise ValueError('Invalid input geometry')
                origin = np.minimum(points.min(axis=0), centers.min(axis=0))
                extent = float(np.max(np.maximum(points.max(axis=0), centers.max(axis=0))-origin))
                scale = (MAX-2)/extent if extent else 1.0
                ids = np.linspace(0, len(centers)-1, min(policy['queries_per_dataset'], len(centers)), dtype=int)
                p = np.rint((points-origin)*scale+1).astype('<u4')
                q = np.rint((centers[ids]-origin)*scale+1).astype('<u4')
                sf = Fraction.from_float(scale)
                r2 = [min(d*MAX*MAX, int((Fraction.from_float(float(radii[i]))*sf)**2)) for i in ids]
                case_id = f'{family}/d{d}'
                out = data/'prepared'/f'{case_id}.bin'
                binary(out, d, p, q, r2)
                cases.append(dict(id=case_id, dimension=d, points=len(p), queries=len(q),
                    path=out.relative_to(data).as_posix(), sha256=sha(out), sources=sources,
                    conversion=dict(origin=origin.tolist(), scale=scale, rounding='nearest, ties to even',
                        radius_rule='floor exact scaled squared radius, capped at dimension * UINT32_MAX squared',
                        coordinate_parse='float32 promoted to float64', query_indices=ids.tolist())))
                print('prepared', case_id, len(p), len(q), flush=True)
    for d in policy['dimensions']:
        rng = np.random.default_rng(917+d)
        p = rng.integers(0, MAX+1, size=(128, d), dtype=np.uint32)
        p[0] = 0; p[1] = MAX; p[2] = 0
        p[3] = 0; p[3, 0] = 3; p[3, 1] = 4
        p[4] = p[3]
        q = np.vstack([np.zeros((5, d), dtype=np.uint32), p[1], p[3], p[3]])
        radii2 = [0, 24, 25, 26, d*MAX*MAX, 0, 0, 1]
        for label, points in [('boundary_duplicates', p), ('empty', p[:0]),
                              ('collinear', np.pad(np.arange(64, dtype=np.uint32)[:, None], ((0, 0), (0, d-1))))]:
            case_id = f'{label}/d{d}'
            out = data/'prepared'/f'{case_id}.bin'
            binary(out, d, points, q, radii2)
            cases.append(dict(id=case_id, dimension=d, points=len(points), queries=len(q),
                              path=out.relative_to(data).as_posix(), sha256=sha(out)))
    manifest = dict(policy=policy, cases=cases, algorithms=['chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED'])
    save(data/'campaign.json', manifest)
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--cpu', type=int, default=1)
    ap.add_argument('--algorithms', nargs='+', help='Default: all registered campaign algorithms')
    args = ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run):
        raise ValueError('Run name must be a simple identifier')
    data = ROOT/'data/esa2026-ddim'
    results = ROOT/'results/esa2026-ddim'/args.run
    results.mkdir(parents=True, exist_ok=False)
    policy = json.loads((ROOT/'campaigns/esa2026-ddim/campaign.json').read_text())
    supported = ['chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED']
    algorithms = args.algorithms or supported
    if not algorithms or any(a not in supported for a in algorithms) or len(set(algorithms)) != len(algorithms):
        raise ValueError('Unknown or duplicate algorithm')
    state = dict(status='preparing', algorithms=algorithms, policy=policy, jobs=[], cpu=args.cpu)
    save(results/'state.json', state)
    try:
        manifest = prepare(data, policy)
        manifest = dict(manifest, cases=[c for c in manifest['cases']
            if c['id'].split('/')[0] in policy['enabled_case_families']])
        exe = ROOT/'build/d-dim/ddim_check'
        state.update(status='running', planned_jobs=len(manifest['cases'])*len(algorithms), binary_sha256=sha(exe),
                     manifest_sha256=sha(data/'campaign.json'))
        def limits():
            import resource
            os.sched_setaffinity(0, {args.cpu})
            memory = policy['memory_gib'] * 1024**3
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        for algorithm, case in ((a,c) for a in algorithms for c in manifest['cases']):
            state['current'] = algorithm+'/'+case['id']; save(results/'state.json', state)
            started = time.monotonic()
            job = dict(id=case['id'], algorithm=algorithm, dimension=case['dimension'])
            path = data/case['path']
            if sha(path) != case['sha256']:
                raise ValueError('Prepared data hash mismatch')
            try:
                p = subprocess.run([str(exe), str(path), algorithm], capture_output=True, text=True,
                    timeout=policy['timeout_seconds'], preexec_fn=limits)
                job.update(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
                job['status'] = 'incorrect' if p.returncode == 2 else 'crash' if p.returncode else 'success'
                if p.returncode == 0:
                    job.update(json.loads(p.stdout))
            except subprocess.TimeoutExpired:
                job['status'] = 'timeout'
            job['wall_seconds'] = time.monotonic()-started
            state['jobs'].append(job)
            save(results/algorithm/(case['id']+'.json'), job)
            save(results/'state.json', state)
            print(algorithm, case['id'], job['status'], round(job['wall_seconds'], 3), flush=True)
        state['status'] = 'complete' if all(j['status'] == 'success' for j in state['jobs']) else 'needs_attention'
        state['current'] = None
        state['outcomes'] = dict(collections.Counter(j['status'] for j in state['jobs']))
        save(results/'state.json', state)
        print(json.dumps(state['outcomes']), flush=True)
    except Exception as e:
        state.update(status='needs_attention', error=str(e))
        save(results/'state.json', state)
        raise


if __name__ == '__main__':
    main()
