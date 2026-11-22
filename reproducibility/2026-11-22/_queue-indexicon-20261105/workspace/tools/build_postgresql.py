"""Build a pinned, private PostgreSQL runtime; never touch a system database."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
VERSION='18.4'
SHA256='81a81ec695fb0c7901407defaa1d2f7973617154cf27ba74e3a7ab8e64436094'
URL=f'https://ftp.postgresql.org/pub/source/v{VERSION}/postgresql-{VERSION}.tar.bz2'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,help='Use a previously downloaded source archive')
    parser.add_argument('--jobs',type=int,default=2)
    args=parser.parse_args()
    folder=ROOT/'build/postgresql';folder.mkdir(parents=True,exist_ok=True)
    archive=args.archive or folder/f'postgresql-{VERSION}.tar.bz2'
    if not archive.exists():
        if args.archive:raise FileNotFoundError(archive)
        urllib.request.urlretrieve(URL,archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA256:
        raise ValueError('PostgreSQL source checksum mismatch')
    with tarfile.open(archive) as source:source.extractall(folder,filter='data')
    source=folder/f'postgresql-{VERSION}'
    prefix=ROOT/'toolchains'/f'postgresql-{VERSION}'
    commands=[['./configure',f'--prefix={prefix}','--without-icu','--without-readline','--without-zlib'],
              ['make',f'-j{args.jobs}'],['make','install']]
    with (folder/'build.log').open('w') as log:
        for command in commands:subprocess.run(command,cwd=source,stdout=log,stderr=log,check=True)
    print(prefix)


if __name__=='__main__':main()
