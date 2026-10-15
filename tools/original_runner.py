"""Run original reporting APIs; adapt file formats outside query timing only."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUST = {'esa_kiddo','esa_nabo','esa_neighbourhood','esa_vptree','esa_orthtree','esa_grid','esa_snn_rust'}
PYTHON = {'esa_sklearn_kd','esa_sklearn_ball','esa_snn','brute_force'}
UNSUPPORTED = {'chan_sss','stann_fr','chan_sss_ddim_MANUALLY_ADAPTED','stann_fr_ddim_MANUALLY_ADAPTED'}
FOREIGN = {'ann_fr':'ann','esa_nanoflann':'nano','cgal_kd':'cgal','pargeo':'pargeo','pam':'pam'}
TWO_D = RUST | PYTHON | UNSUPPORTED | {'ann_fr','esa_nanoflann','pargeo','pam','cgal_kd'}

def dependency_files(algorithm):
    if algorithm in UNSUPPORTED:return [ROOT/'tools/original_runner.py']
    if algorithm in RUST:return [ROOT/'build/original-rust/release/original-range-check']
    if algorithm in PYTHON:return [ROOT/'src/runner/dimensional/python_check.py']
    if algorithm in FOREIGN:return [ROOT/'build/dimensional'/('check_'+FOREIGN[algorithm])]
    return []

def main():
    dimensional = sys.argv[1] == '--dimensional'
    if dimensional:
        _, _, filename, algorithm, *options = sys.argv
        bench = '--bench' in options
        destination = None
    else:
        _, algorithm, filename, mode, *rest = sys.argv
        bench = mode == 'bench'
        destination = Path(rest[0]) if rest else None
    if algorithm in UNSUPPORTED:
        row = dict(status='unsupported_input', reason='Original implementation has no range-reporting API; local reporting adaptation is excluded by request.')
        output = json.dumps(row)+'\n'
        if destination: destination.write_text(output)
        print(output, end='')
        return 0
    with tempfile.TemporaryDirectory(prefix='original-range-') as folder:
        path = Path(filename)
        if not dimensional:
            with path.open('rb') as source:
                header = source.read(8)
                if header == b'ESA2D01\0':
                    n, q = struct.unpack('<QQ', source.read(16))
                    path = Path(folder)/'case.bin'
                    with path.open('wb') as target:
                        target.write(struct.pack('<IQQ', 2, n, q))
                        shutil.copyfileobj(source, target)
        if algorithm in RUST:
            command = [str(ROOT/'build/original-rust/release/original-range-check')]
        elif algorithm in PYTHON:
            command = [sys.executable, str(ROOT/'src/runner/dimensional/python_check.py')]
        else:
            command = [str(ROOT/'build/dimensional'/('check_'+FOREIGN[algorithm]))]
        result = subprocess.run([*command, str(path), algorithm, *(['--bench'] if bench else [])], text=True, capture_output=True)
        if destination and result.stdout.strip():
            try:
                row = json.loads(result.stdout)
                row.update(algorithm=algorithm, update_seconds=0, insertions=0, deletions=0)
                destination.write_text(json.dumps(row)+'\n')
            except json.JSONDecodeError:
                pass
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
