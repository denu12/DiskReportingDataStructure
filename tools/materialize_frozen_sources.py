"""Verify or unpack frozen harness sources; never start a benchmark."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'reproducibility/2026-11-22'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path)
    parser.add_argument('--projects-root',type=Path,help='Replacement for the captured Projects directory')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'source-manifest.json').read_text())
    if args.destination and not args.projects_root:parser.error('--destination requires --projects-root')
    if args.destination:args.destination.mkdir(parents=True,exist_ok=False)
    for row in manifest['files']:
        rel=Path(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid frozen path')
        source=ROOT/rel;data=source.read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['published_sha256'],str(rel)
        if args.destination:
            text=data.decode().replace('@PROJECTS_ROOT@',str(args.projects_root.resolve())).replace('@HOME@',str(Path.home()))
            target=args.destination/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
            if source.suffix=='.sh':target.chmod(0o755)
    print(f"Verified {len(manifest['files'])} frozen source files; no experiments started")


if __name__=='__main__':main()
