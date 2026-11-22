"""Build the frozen native f64 SPRK bridge; do not start measurements."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    cmd = ['cargo', 'build', '--release', '--locked', '--manifest-path',
           str(ROOT/'src/runner/dimensional/sprk_ddim/Cargo.toml'),
           '--target-dir', str(ROOT/'build/sprk-ddim'), '-j', os.environ.get('BUILD_JOBS','2')]
    if os.environ.get('OFFLINE') == '1':
        cmd.append('--offline')
    env = dict(os.environ, RUSTFLAGS=os.environ.get('RUSTFLAGS','-Ctarget-cpu=native'))
    subprocess.run(cmd, check=True, env=env)


if __name__ == '__main__':
    main()
