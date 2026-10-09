"""Materialize exact ESA workload selections on the common integer grid.

Missing data remain explicit in the manifest; execution refuses incomplete
campaigns. --existing-only inventories/prepares cached data without downloading.
"""
import argparse
from fractions import Fraction
from functools import lru_cache
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import zipfile
import zlib
import numpy as np
from catalog import ROOT, save, sha
from campaign_paths import campaign_directory
from algorithm_labels import metadata

MAX = 2**32-1


def chunks(path, dimension):
    with path.open(encoding='utf-8') as f:
        while lines := list(itertools.islice(f, 8192)):
            a = np.loadtxt(lines, delimiter=',', dtype=np.float32, ndmin=2).astype(np.float64)
            if a.shape[1] != dimension or not np.isfinite(a).all():
                raise ValueError(f'Invalid coordinates/dimension: {path}')
            yield a


def source_file(desc, source, archives):
    target = source/desc['path']
    if not target.exists():
        archive = archives/desc.get('archive', '__missing__')
        if archive.is_file():
            with zipfile.ZipFile(archive) as z:
                member = desc.get('member')
                if member is None:
                    matches = [n for n in z.namelist() if not n.startswith('__MACOSX/') and Path(n).name == desc['basename']]
                    if len(matches) != 1:
                        raise ValueError('Ambiguous ZIP member: '+desc['path'])
                    member = matches[0]
                info = z.getinfo(member)
                if 'crc32' in desc and info.CRC != desc['crc32']:
                    raise ValueError('Archive does not match frozen catalog')
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix('.partial')
                with z.open(member) as src, temporary.open('wb') as dst:
                    shutil.copyfileobj(src, dst, 1024*1024)
                temporary.replace(target)  # ZipFile checked the decompressed CRC.
    return target if target.exists() else None


def validate_source(path, desc):
    if 'bytes' in desc and path.stat().st_size != desc['bytes']:
        raise ValueError('Source length differs from artifact: '+str(path))
    crc = 0
    if 'crc32' in desc:
        with path.open('rb') as f:
            while data := f.read(1024*1024):
                crc = zlib.crc32(data, crc)
        if crc != desc['crc32']:
            raise ValueError('Source CRC differs from artifact: '+str(path))
    return sha(path)


def convert(case, files, output, format2d):
    d = case['dimension']
    lo = np.full(d, np.inf); hi = np.full(d, -np.inf)
    sizes = {}
    for path in dict.fromkeys([files['train'], files['query']]):
        count = 0
        for a in chunks(path, d):
            lo = np.minimum(lo, a.min(axis=0)); hi = np.maximum(hi, a.max(axis=0)); count += len(a)
        if not count:
            raise ValueError('Unexpected empty source dataset')
        sizes[path] = count
    n, q = sizes[files['train']], sizes[files['query']]
    extent = float(np.max(hi-lo)); scale = (MAX-2)/extent if extent else 1.0
    sf = Fraction.from_float(scale)

    @lru_cache(maxsize=65536)
    def radius2(value):
        if not np.isfinite(value) or value < 0:
            raise ValueError('Invalid radius')
        return min(d*MAX*MAX, int((Fraction.from_float(value)*sf)**2))

    def grid(a):
        a -= lo; a *= scale; a += 1; np.rint(a, out=a)
        if (a < 0).any() or (a > MAX).any():
            raise ValueError('Coordinate outside common integer grid')
        return a.astype('<u4')

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.partial')
    radii_file = files.get('radii')
    f_radii = radii_file.open() if radii_file else None
    total_radius = 0.0
    try:
        with temporary.open('wb') as f:
            f.write(struct.pack('<8sQQ', b'ESA2D01\0', n, q) if format2d else struct.pack('<IQQ', d, n, q))
            for a in chunks(files['train'], d):
                f.write(grid(a).tobytes())
            for a in chunks(files['query'], d):
                coordinates = grid(a)
                radii = [float(next(f_radii)) for _ in coordinates] if f_radii else [case['radius']]*len(coordinates)
                total_radius += sum(radii)
                records = np.empty(len(a), dtype=[('center', '<u4', (d,)), ('lo', '<u8'), ('hi', '<u8')])
                records['center'] = coordinates
                rr = [radius2(r) for r in radii]
                records['lo'] = [r & (2**64-1) for r in rr]
                records['hi'] = [r >> 64 for r in rr]
                f.write(records.tobytes())
            if f_radii and f_radii.read().strip():
                raise ValueError('Extra radii after last query')
        temporary.replace(output)
    finally:
        if f_radii:
            f_radii.close()
    return dict(n=n, points=n, queries=q, conversion=dict(origin=lo.tolist(), scale=scale,
        coordinate_parse='f32 promoted to f64', rounding='nearest, ties to even', padding=1,
        radius_rule='floor exact binary64 scaled radius squared, cap d*UINT32_MAX^2',
        mean_radius_original=total_radius/q, mean_radius_grid=(total_radius/q)*scale))


def prepare(name, source, archives):
    specification = campaign_directory(ROOT,name)/'campaign.json'
    spec = json.loads(specification.read_text()); root = ROOT/'data'/name
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in spec['cases']:
        metadata = root/'metadata'/(case['id']+'.json')
        fingerprint = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
        if metadata.exists():
            row = json.loads(metadata.read_text())
            if row.get('spec_sha256') == fingerprint and sha(root/row['path']) == row['sha256']:
                rows.append(row); continue
        row = dict(case, spec_sha256=fingerprint)
        files = {k: source_file(v, source, archives) for k, v in case['files'].items()}
        if not all(files.values()):
            row.update(status='missing_source', missing=[case['files'][k]['path'] for k, v in files.items() if v is None])
            rows.append(row); continue
        row['source_sha256'] = {k: validate_source(p, case['files'][k]) for k, p in files.items()}
        output = root/'prepared'/(case['id']+'.bin')
        row.update(convert(case, files, output, spec['input_format'] == 'ESA2D01'))
        row.update(status='ready', path=os.path.relpath(output, root).replace(os.sep, '/'), sha256=sha(output))
        save(metadata, row); rows.append(row)
        print(name, case['id'], 'ready', flush=True)
    manifest = dict(spec, specification_sha256=sha(specification), cases=rows,
                    status='ready' if all(c['status'] == 'ready' for c in rows) else 'awaiting_data')
    manifest['algorithm_metadata'] = {a: metadata(a) for a in manifest['algorithms']}
    save(root/'campaign.json', manifest)
    return dict(name=name, ready=sum(c['status'] == 'ready' for c in rows), total=len(rows), status=manifest['status'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--campaign', nargs='+', required=True, help='Campaign names, or all')
    ap.add_argument('--source', type=Path, default=ROOT/'data/ESA/source')
    ap.add_argument('--archives', type=Path, default=ROOT/'data/ESA/archives')
    ap.add_argument('--existing-only', action='store_true', help='Allow an inventory with explicitly missing cases')
    args = ap.parse_args()
    index = json.loads((ROOT/'config/esa-workloads.json').read_text())
    known = [r['name'] for r in index['full']+index['native_2d']]
    names = known if args.campaign == ['all'] else args.campaign
    if not set(names) <= set(known): ap.error('Unknown ESA campaign')
    summaries = [prepare(n, args.source, args.archives) for n in names]
    save(ROOT/'data/ESA/preparation-status.json', summaries)
    print(json.dumps(summaries, indent=2))
    if not args.existing_only and any(s['status'] != 'ready' for s in summaries):
        raise SystemExit('Source data missing; see manifests and docs/ESA-WORKLOADS.md. No partial campaign is runnable.')


if __name__ == '__main__':
    main()
