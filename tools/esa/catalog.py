"""Freeze the five workload families from the pinned ESA artifact; never run jobs."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from workloads import STATIC, DIMENSIONAL
from campaign_paths import campaign_directory

REVISION = 'a81b216a2a63bde3d4447e4053b4ca31081fe286'
ARTIFACT = ROOT / 'src/third_party/esa2026-workloads/reproducibility-cli'
FAMILIES = ['graph_embeddings', 'uniform_points', 'high_dimensional', 'clustering', 'geographical']
DIMENSIONS = {'deep': 96, 'fmn': 784, 'sift': 128, 'sift_large': 128,
              'gist': 960, 'glo': 100, 'banknote': 4, 'dermatology': 34,
              'ecoli': 7, 'phoneme': 5, 'wine': 13}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.partial')
    tmp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archives', type=Path, default=ROOT/'data/ESA/archives')
    args = ap.parse_args()
    source = (ARTIFACT/'src/main.rs').read_text()
    radii = {name: [float(x) for x in values.split(',') if x.strip()]
             for name, values in re.findall(r'"(\w+)" => vec!\[([^\]]+)\]', source)}
    cases = {f: [] for f in FAMILIES}
    for archive, family in [('embedding_data.zip', 'graph_embeddings'), ('distributions.zip', 'uniform_points')]:
        with zipfile.ZipFile(args.archives/archive) as z:
            entries = {i.filename: i for i in z.infolist() if not i.is_dir() and not i.filename.startswith('__MACOSX/')}
            if family == 'graph_embeddings':
                metadata_name = next(n for n in entries if n.endswith('metadata.csv'))
                metadata = list(csv.DictReader(io.TextIOWrapper(z.open(metadata_name))))
                by_prefix = {r['export_prefix']: r for r in metadata}
            for name in sorted(n for n in entries if n.endswith('_train.csv')):
                prefix = name[:-len('_train.csv')]
                stem = Path(prefix).name
                dim = int(re.search(r'(?:dim-|_d)(\d+)(?:_|\.)', name)[1])
                if family == 'graph_embeddings' and stem not in by_prefix:
                    raise ValueError('Embedding missing from upstream metadata: '+stem)
                files = {}
                for key, suffix in [('train', '_train.csv'), ('query', '_query_points.csv'), ('radii', '_query_radii.csv')]:
                    member = prefix+suffix
                    item = entries[member]
                    files[key] = dict(path=f'{family}/{Path(member).name}', archive=archive,
                                      member=member, bytes=item.file_size, crc32=item.CRC)
                case = dict(id=stem, suite=family, dimension=dim, files=files,
                            queries_policy='all_source_queries', radius_policy='source_radius_per_query')
                if family == 'graph_embeddings':
                    case['upstream_metadata'] = by_prefix[stem]
                cases[family].append(case)
            if family == 'graph_embeddings' and len(cases[family]) != len(metadata):
                raise ValueError('Embedding metadata/archive coverage differs')
    for family, names in [('high_dimensional', ['deep', 'fmn', 'sift', 'sift_large', 'gist', 'glo']),
                          ('clustering', ['banknote', 'dermatology', 'ecoli', 'phoneme', 'wine'])]:
        for name in names:
            train = f'{family}/{name}'+('_train.csv' if family == 'high_dimensional' else '.csv')
            query = f'{family}/{name}_query.csv' if family == 'high_dimensional' else train
            for radius in radii[name]:
                # The clustering branch calls nearest_neighbors(i, 1), whose
                # graph weight is sqrt(radius). Preserve its f64 round trip.
                effective = (math.sqrt(radius)*math.sqrt(radius)) if family == 'clustering' else radius
                cases[family].append(dict(id=f'{name}_r{radius:g}', suite=family,
                    dataset=name, dimension=DIMENSIONS[name], files=dict(train=dict(path=train), query=dict(path=query)),
                    queries_policy='all_training_points' if family == 'clustering' else 'all_source_queries',
                    radius_policy='constant', nominal_radius=radius, radius=effective))
    pair_block = source.split('let poi_pairs = vec![', 1)[1].split('];', 1)[0]
    pairs = re.findall(r'\("([^"]+)", "([^"]+)", "([^"]+)"\)', pair_block)
    poi_radii = [float(x) for x in source.split('let poi_radii = vec![', 1)[1].split('];', 1)[0].split(',')]
    for name, train, query in pairs:
        for radius in poi_radii:
            cases['geographical'].append(dict(id=f'{name}_r{radius:g}', suite='geographical', dimension=2,
                files=dict(train=dict(path=f'geographical/{train}', archive='poi.zip', basename=train),
                           query=dict(path=f'geographical/{query}', archive='poi.zip', basename=query)),
                queries_policy='all_source_queries', radius_policy='constant', radius=radius))
    ndim = DIMENSIONAL
    source_paths = ['src/main.rs', 'src/benchmark/distribution_bench.rs', 'src/benchmark/runner.rs',
                    'data/download_scripts/download_clustering.py', 'data/download_scripts/nn_download_to_csv.py',
                    'data/download_scripts/download_nn.sh']
    provenance = dict(repository='https://github.com/wembed-pdf/rembed', revision=REVISION,
                      zenodo_record=21243483, files={p: sha(ARTIFACT/p) for p in source_paths})
    index = dict(schema=1, upstream=provenance, full=[], native_2d=[], omitted_empty_2d=[])
    for family in FAMILIES:
        for only2d in ([True] if family == 'geographical' else [False, True]):
            selected = [c for c in cases[family] if (c['dimension'] == 2 if only2d else c['dimension'] > 2)]
            name = ('2D_ESA_' if only2d else 'ESA_')+family
            if not selected:
                if only2d: index['omitted_empty_2d'].append(name)
                continue
            manifest = dict(schema=1, name=name, family=family, upstream=provenance,
                parent=None,
                selection='native dimension == 2, no projection' if only2d else 'upstream workload family restricted to dimension > 2; native 2D cases belong to the small theater',
                input_format='ESA2D01' if only2d else 'ddim-u32',
                algorithms=STATIC if only2d else ndim,
                comparison_contract=dict(coordinates='common uint32 grid', output='explicit original integer coordinates',
                    exceptions={'esa_sprk_CHEATING_IDS_ONLY': 'SPRK (IDs only): floating-point radius search, materialized IDs only; no timed exact integer filter or coordinate output'} if only2d else {},
                    measurement='bounded single-core jobs; separate build/query timing; three final repetitions',
                    claim='upstream workload matrix; not a floating-point/Criterion timing reproduction'),
                dimensions=sorted({c['dimension'] for c in selected}), cases=selected)
            folder = campaign_directory(ROOT,name)
            save(folder/'campaign.json', manifest)
            folder.joinpath('README.md').write_text(
                f'# {name}\n\n{len(selected)} upstream workload cases; dimensions: '+', '.join(map(str, manifest['dimensions']))+
                '. All source training points, queries and radii are retained.\n\n'
                'See [the ESA campaign guide](../../../../docs/ESA-WORKLOADS.md) for preparation, execution, provenance and the integer-coordinate contract. '
                'This file defines workloads; it does not mean all input data have been downloaded or all dimensions are supported by every adapter.\n', encoding='utf-8')
            index['native_2d' if only2d else 'full'].append(dict(name=name, cases=len(selected), dimensions=manifest['dimensions']))
    index['theater_workloads'] = sum(len([c for c in cases[f] if c['dimension'] > 2]) for f in FAMILIES if f != 'geographical')
    index['unique_workloads'] = sum(len(v) for v in cases.values())
    save(ROOT/'config/esa-workloads.json', index)
    print(json.dumps({k: index[k] for k in ['full', 'native_2d', 'omitted_empty_2d', 'unique_workloads']}, indent=2))


if __name__ == '__main__':
    main()
