"""Import only native 2D datasets from the paper's Zenodo ZIP archives.

HTTP ranges avoid downloading the higher-dimensional datasets. ZIP CRC checks
and per-file SHA-256 hashes protect extracted files. No upstream source edits.
"""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
import time
import urllib.request
import zipfile

RECORD = 'https://zenodo.org/api/records/21243483'

def request(url, headers=None):
    for attempt in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=120)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(min(2 ** attempt, 20))

class RemoteZip(io.RawIOBase):
    def __init__(self, url, size):
        self.url, self.size, self.pos = url, size, 0
        self.cache = b''
        self.start = 0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset + (self.pos if whence == 1 else self.size if whence == 2 else 0)
        return self.pos
    def read(self, count=-1):
        if count < 0: count = self.size - self.pos
        count = min(count, self.size - self.pos)
        if count <= 0: return b''
        if not (self.start <= self.pos and self.pos + count <= self.start + len(self.cache)):
            end = min(self.size, self.pos + max(count, 2097152)) - 1
            with request(self.url, {'Range': f'bytes={self.pos}-{end}'}) as response:
                if response.status != 206:
                    raise RuntimeError('Server did not honor byte range; refusing a full archive download')
                if not response.headers.get('Content-Range', '').startswith(f'bytes {self.pos}-'):
                    raise RuntimeError('Incorrect Content-Range')
                self.cache = response.read()
                self.start = self.pos
        result = self.cache[self.pos-self.start:self.pos-self.start+count]
        self.pos += len(result)
        return result

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dest', type=Path, required=True)
    ap.add_argument('--list-only', action='store_true')
    args = ap.parse_args()
    args.dest.mkdir(parents=True, exist_ok=True)
    with request(RECORD) as response: record = json.load(response)
    (args.dest/'zenodo-record.json').write_text(json.dumps(record, indent=2))
    manifest = []
    for archive in record['files']:
        name = archive['key']
        if name not in ('embedding_data.zip', 'distributions.zip', 'poi.zip'): continue
        z = zipfile.ZipFile(RemoteZip(archive['links']['self'], archive['size']))
        entries = [i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')]
        (args.dest/(name+'.listing.json')).write_text(json.dumps([{'name':i.filename,'bytes':i.file_size,'compressed':i.compress_size} for i in entries], indent=2))
        if args.list_only:
            print(name, len(entries), [i.filename for i in entries[:15]], flush=True)
            continue
        selected = set()
        if name == 'poi.zip':
            selected = {i.filename for i in entries if i.filename.endswith('.csv')}
        else:
            for i in entries:
                if i.filename.endswith('metadata.csv'):
                    selected.add(i.filename)
                if i.filename.endswith('_train.csv'):
                    dimension = re.search(r'(?:dim-|_d)(\d+)(?:_|\.)', i.filename)
                    if dimension and int(dimension.group(1)) != 2: continue
                    with z.open(i) as f: first = f.readline().decode().strip()
                    if len(first.split(',')) == 2:
                        prefix = i.filename[:-len('_train.csv')]
                        selected.update(prefix + suffix for suffix in ('_train.csv','_query_points.csv','_query_radii.csv'))
        category = {'embedding_data.zip':'embedding','distributions.zip':'distributions','poi.zip':'poi'}[name]
        for i in entries:
            if i.filename not in selected: continue
            target = args.dest/category/Path(i.filename).name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.stat().st_size != i.file_size:
                tmp = target.with_suffix(target.suffix+'.partial')
                with z.open(i) as src, tmp.open('wb') as dst:
                    while chunk := src.read(1024*1024): dst.write(chunk)
                tmp.replace(target)
            manifest.append({'archive':name,'member':i.filename,'path':target.relative_to(args.dest).as_posix(), 'bytes':i.file_size,'sha256':sha(target),'zip_crc32':i.CRC})
            print('imported', target.name, i.file_size, flush=True)
        (args.dest/'files.json').write_text(json.dumps(manifest, indent=2))
    print('Imported',len(manifest),'files', flush=True)

if __name__ == '__main__': main()
