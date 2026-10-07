"""Fetch ESA sources using the pinned artifact's datasets and preprocessing.

No benchmarks are launched. Download and source hashes are retained under data/ESA.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from catalog import ROOT, ARTIFACT, FAMILIES, save, sha


def download(url, target, expected_size=None, md5=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        partial = target.with_suffix(target.suffix+'.partial')
        offset = partial.stat().st_size if partial.exists() else 0
        request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'} if offset else {})
        with urllib.request.urlopen(request, timeout=120) as response:
            if offset and (getattr(response, 'status', None) != 206 or not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-')):
                raise RuntimeError('Resume range not honored: '+url)
            length = response.headers.get('Content-Length')
            with partial.open('ab' if offset else 'wb') as f:
                shutil.copyfileobj(response, f, 4*1024*1024)
            if length is not None and partial.stat().st_size != offset+int(length):
                raise ValueError('Truncated source download')
        if expected_size is not None and partial.stat().st_size != expected_size: raise ValueError('Wrong download size')
        if md5:
            with partial.open('rb') as f:
                if hashlib.file_digest(f, 'md5').hexdigest() != md5: raise ValueError('Archive checksum mismatch')
        partial.replace(target)
    if expected_size is not None and target.stat().st_size != expected_size: raise ValueError('Cached archive size mismatch')
    if md5:
        with target.open('rb') as f:
            if hashlib.file_digest(f, 'md5').hexdigest() != md5: raise ValueError('Cached archive checksum mismatch')
    receipt = dict(url=url, bytes=target.stat().st_size, sha256=sha(target))
    previous = target.with_suffix(target.suffix+'.receipt.json')
    if previous.exists() and json.loads(previous.read_text())['sha256'] != receipt['sha256']:
        raise ValueError('Downloaded source changed since its frozen receipt')
    save(previous, receipt)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--families', nargs='+', choices=FAMILIES, default=FAMILIES)
    args = ap.parse_args()
    data = ROOT/'data/ESA'; source = data/'source'; archives = data/'archives'
    archive_names = {'graph_embeddings': 'embedding_data.zip', 'uniform_points': 'distributions.zip', 'geographical': 'poi.zip'}
    if any(f in archive_names for f in args.families):
        candidates = [data/'zenodo-record.json', ROOT/'data/esa2026-ddim-full/archives/zenodo-record.json', ROOT/'data/esa2026-2d/data/zenodo-record.json']
        record = next((json.loads(p.read_text()) for p in candidates if p.exists()), None)
        if record is None:
            with urllib.request.urlopen('https://zenodo.org/api/records/21243483', timeout=120) as f: record = json.load(f)
        save(data/'zenodo-record.json', record)
        for family in args.families:
            if family not in archive_names: continue
            name = archive_names[family]; item = next(f for f in record['files'] if f['key'] == name)
            target = archives/name
            old = ROOT/'data/esa2026-ddim-full/archives'/name
            if not target.exists() and old.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                try: target.hardlink_to(old)
                except OSError: shutil.copyfile(old, target)
            download(item['links']['self'], target, item['size'], item['checksum'].removeprefix('md5:'))
            print('verified', name, flush=True)
    if not {'high_dimensional', 'clustering'} & set(args.families): return
    # Preserve the upstream Python data transformations, but supply the paths
    # the converter actually expects (the upstream shell helper disagrees).
    work = data/'import/reproducibility-cli'; work.mkdir(parents=True, exist_ok=True)
    if 'clustering' in args.families:
        subprocess.run([sys.executable, str(ARTIFACT/'data/download_scripts/download_clustering.py')], cwd=work, check=True)
        dest = source/'clustering'; dest.mkdir(parents=True, exist_ok=True)
        for p in (work/'data/realworld/clustering_data').glob('*.csv'): shutil.copyfile(p, dest/p.name)
    if 'high_dimensional' in args.families:
        cache = work/'data/realworld/nearest_neighbor_data/.download_cache'
        for name in ['fashion-mnist-784-euclidean.hdf5', 'gist-960-euclidean.hdf5', 'glove-100-angular.hdf5', 'deep-image-96-angular.hdf5']:
            download('http://ann-benchmarks.com/'+name, cache/name)
        for name in ['siftsmall', 'sift']:
            archive = cache/(name+'.tar.gz')
            download('ftp://ftp.irisa.fr/local/texmex/corpus/'+name+'.tar.gz', archive)
            with tarfile.open(archive) as tar:
                for kind in ['learn', 'query']:
                    member = f'{name}/{name}_{kind}.fvecs'
                    dest = cache/member; dest.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as src, dest.open('wb') as dst: shutil.copyfileobj(src, dst, 1024*1024)
        subprocess.run([sys.executable, str(ARTIFACT/'data/download_scripts/nn_download_to_csv.py')], cwd=work, check=True)
        dest = source/'high_dimensional'; dest.mkdir(parents=True, exist_ok=True)
        for p in (work/'data/realworld/nearest_neighbor_data').glob('*.csv'): shutil.copyfile(p, dest/p.name)
    versions = {}
    for name in ['numpy', 'pandas', 'h5py', 'scikit-learn']:
        try: versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: pass
    save(data/'realworld-source-receipt.json', dict(versions=versions,
         files={str(p.relative_to(source)): sha(p) for f in ['high_dimensional', 'clustering'] for p in (source/f).glob('*.csv')}))


if __name__ == '__main__':
    main()
