"""Download the two full ESA dimensional archives, verifying their record MD5."""
import argparse
import hashlib
import json
from pathlib import Path
from import_data import request, RECORD

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dest',type=Path,required=True);ap.add_argument('--record',type=Path)
    args=ap.parse_args();args.dest.mkdir(parents=True,exist_ok=True)
    if args.record:record=json.loads(args.record.read_text())
    else:
        with request(RECORD) as f:record=json.load(f)
    (args.dest/'zenodo-record.json').write_text(json.dumps(record,indent=2))
    for item in record['files']:
        if item['key'] not in ['embedding_data.zip','distributions.zip']:continue
        path=args.dest/item['key'];partial=path.with_suffix('.partial')
        if not path.exists():
            offset=partial.stat().st_size if partial.exists() else 0
            if offset<item['size']:
                with request(item['links']['self'],{'Range':f'bytes={offset}-'} if offset else {}) as response:
                    if offset and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {offset}-')):
                        raise RuntimeError('Server did not honor resume range')
                    with partial.open('ab' if offset else 'wb') as out:
                        last=offset
                        while chunk:=response.read(4*1024*1024):
                            out.write(chunk);offset+=len(chunk)
                            if offset-last>=128*1024*1024:
                                print(item['key'],offset,'/',item['size'],flush=True);last=offset
            if partial.stat().st_size!=item['size']:raise RuntimeError('Wrong archive length')
            with partial.open('rb') as f:digest=hashlib.file_digest(f,'md5').hexdigest()
            if item['checksum']!='md5:'+digest:raise RuntimeError('Archive checksum mismatch')
            partial.replace(path)
        else:
            with path.open('rb') as f:digest=hashlib.file_digest(f,'md5').hexdigest()
            if path.stat().st_size!=item['size'] or item['checksum']!='md5:'+digest:raise RuntimeError('Cached archive checksum mismatch')
        print('verified',path.name,flush=True)

if __name__=='__main__':main()
