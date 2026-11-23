"""Build native-output Rust dispatch in isolation, preserving the search function."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIMENSIONS = tuple(range(2, 17)) + (32,)


def prepare(source, destination, workspace):
    original = source.read_text()
    run = original[original.index('fn run<'):original.index('fn main()')]
    text = original[:original.index('fn main()')]
    def relocate(match):
        path = (source.parent / match[1]).resolve()
        if not path.is_file():
            relative = match[1].split('third_party/', 1)[1]
            path = workspace / 'src/third_party' / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        return '#[path=' + json.dumps(str(path)) + ']'
    text = re.sub(r'#\[path="([^"]+)"\]', relocate, text)
    text += ('fn main(){let args:Vec<_>=std::env::args().collect();'
             'let mut f=std::fs::File::open(&args[1]).unwrap();let d=u32_read(&mut f);'
             'let bench=args.iter().any(|a|a=="--bench");match d{' +
             ''.join(f'{d}=>run::<{d}>(&mut f,&args[2],bench),' for d in DIMENSIONS) +
             '_=>panic!("Unsupported native driver dimension")}}\n')
    assert text[text.index('fn run<'):text.index('fn main()')] == run
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'main.rs').write_text(text)
    manifest = (source.parent / 'Cargo.toml').read_text()
    manifest = re.sub(r'path = "[^"]*/sprk"',
                      'path = ' + json.dumps(str(workspace / 'src/third_party/esa2026/sprk')), manifest)
    (destination / 'Cargo.toml').write_text(manifest)
    shutil.copyfile(source.parent / 'Cargo.lock', destination / 'Cargo.lock')
    identity = dict(source_sha256=hashlib.sha256(original.encode()).hexdigest(),
                    generic_run_sha256=hashlib.sha256(run.encode()).hexdigest(),
                    dimensions=DIMENSIONS, algorithm_changes=False)
    (destination / 'dispatch-version.json').write_text(json.dumps(identity, indent=2))
    return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'reproducibility/2026-11-22/original-native/src/runner/original-rust/main.rs')
    parser.add_argument('--workspace', type=Path, default=ROOT)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    stage = args.workspace / 'build/native-rust-20261123'
    for path in (args.workspace / 'build', stage, stage / 'driver', stage / 'target'):
        if path.is_symlink():
            raise RuntimeError('Refusing a shared/symlinked build directory: ' + str(path))
    identity = prepare(args.source, stage / 'driver', args.workspace)
    if args.prepare_only:
        print(json.dumps(identity, indent=2))
        return
    env = dict(os.environ, CARGO_BUILD_JOBS='1', RUSTFLAGS='-C target-cpu=native')
    subprocess.run(['cargo', 'build', '--release', '--locked', '--manifest-path', str(stage / 'driver/Cargo.toml'),
                    '--target-dir', str(stage / 'target'), '-j', '1'], env=env, check=True)
    target = stage / 'target/release/original-range-check'
    identity['binary_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    (target.parent / 'dispatch-version.json').write_text(json.dumps(identity, indent=2))
    print(json.dumps(identity, indent=2))


if __name__ == '__main__':
    main()
