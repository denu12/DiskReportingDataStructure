"""Verify native Boost point output, including duplicates and integer boundaries."""
import argparse
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--binary', type=Path, default=Path(__file__).resolve().parents[1]/'build/dimensional/check_boost')
args = parser.parse_args()
rng = random.Random(20261015)
checks = 0
with tempfile.TemporaryDirectory(prefix='native-boost-') as folder:
    case = Path(folder)/'case.bin'
    for dimension in [*range(2, 17), 32]:
        for size in [0, 1, 65]:
            points = [tuple(rng.randrange(2**32) for _ in range(dimension)) for _ in range(size)]
            if size == 65:
                points[:5] = [(0,)*dimension]*2 + [(2**32-1,)*dimension]*2 + [(3,)*dimension]
            queries = []
            for center in [(0,)*dimension, (2**32-1,)*dimension]:
                for radius in [0, 9*dimension-1, 9*dimension, 9*dimension+1, 2**64-1, 2**64, dimension*(2**32-1)**2]:
                    queries.append((center, radius))
            with case.open('wb') as f:
                f.write(struct.pack('<IQQ', dimension, size, len(queries)))
                for point in points:
                    f.write(struct.pack('<'+'I'*dimension, *point))
                for center, radius in queries:
                    f.write(struct.pack('<'+'I'*dimension+'QQ', *center, radius & (2**64-1), radius >> 64))
            expected = sum(sum(sum((x-y)**2 for x, y in zip(point, center)) <= radius for point in points) for center, radius in queries)
            for algorithm in ['boost_lin', 'boost_quad', 'boost_star']:
                for mode in [[], ['--bench']]:
                    result = subprocess.run([str(args.binary.resolve()), str(case), algorithm, *mode], check=True, text=True, capture_output=True)
                    row = json.loads(result.stdout)
                    assert row['status'] == 'success' and row['answers'] == expected, (dimension, size, algorithm, row)
                    assert row['output_contract'] == 'integer_points'
                    assert row['output_representation'] == 'native_boost_points'
                    assert row['membership_contract'] == 'closed_integer_ball'
                    checks += 1
print(f'{checks} native Boost verification/benchmark checks passed')
