"""Build the six Indexicon executables; no experiment is started."""
import os
from pathlib import Path
import subprocess
import tempfile

from indexicon_competitors import BACKENDS, COMPILED_DIMS

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'build/dimensional'
    out.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'src/runner/dimensional/foreign_check.cpp'
    includes = ROOT / 'src/third_party/indexicon/indexes'
    for backend in dict.fromkeys(BACKENDS.values()):
        with tempfile.TemporaryDirectory(dir=out, prefix='.indexicon-build-') as stage:
            executable = Path(stage) / ('check_' + backend)
            cmd = [os.environ.get('CXX', 'g++'), '-std=c++20', '-O3', '-march=native', '-DNDEBUG',
                   '-DBACKEND_INDEXICON', '-D' + backend.upper(),
                   '-DINDEXICON_DIMS=' + ','.join(map(str, COMPILED_DIMS)),
                   '-I' + str(includes), str(source), '-o', str(executable)]
            print('Building ' + backend, flush=True)
            subprocess.run(cmd, check=True)
            executable.replace(out / executable.name)
    launcher = ROOT / 'bin/esa2d/original_runner'
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if not launcher.exists():
        launcher.write_text('#!/usr/bin/env sh\nexec "${PYTHON:-python3}" "$(dirname "$0")/../../tools/original_runner.py" "$@"\n')
        launcher.chmod(0o755)


if __name__ == '__main__':
    main()
