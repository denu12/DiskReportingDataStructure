# ESA workload campaigns

These campaigns follow the five workload families in the pinned ESA 2026 artifact,
*Benchmarking and Engineering Data Structures for Spherical Range Queries*.
The source is [rembed](https://github.com/wembed-pdf/rembed), revision
`a81b216a2a63bde3d4447e4053b4ca31081fe286`, vendored under
`third_party/esa2026-workloads`. Released archives are from
[Zenodo record 21243483](https://zenodo.org/records/21243483).
The original authors and library licences remain credited in that snapshot and
the competitor notices.

| Full campaign | Cases | Dimensions | Native 2D companion | 2D cases |
|---|---:|---|---|---:|
| `ESA_graph_embeddings` | 225 | 2–16 | `2D_ESA_graph_embeddings` | 15 |
| `ESA_uniform_points` | 21 | 2, 8, 32 | `2D_ESA_uniform_points` | 7 |
| `ESA_high_dimensional` | 30 | 96, 100, 128, 784, 960 | None | 0 |
| `ESA_clustering` | 25 | 4, 5, 7, 13, 34 | None | 0 |
| `ESA_geographical` | 28 | 2 | `2D_ESA_geographical` | 28 |

There are 329 unique full-suite workloads. The 50 companion workloads are exact
dimension-2 subsets, not additional datasets or projections. Empty companion
campaigns are not created. Figures/tables that reuse the same inputs do not
create duplicate cases.

## What is reproduced

`campaign.json` in each campaign freezes its full dataset/query/radius matrix:

- Graph embeddings: every row of `embedding_export/metadata.csv`, all 225 training
  files and their complete query-point and per-query-radius files; all seeds and sizes.
- Uniform points: all 20 released train/query/radius triples, including all seven
  sizes in each of 2, 8 and 32 dimensions.
- High-dimensional data: deep, Fashion-MNIST, SIFT-small, SIFT-large, GIST and
  GloVe; the five radii per dataset from the artifact. SIFT uses the **learn**
  vectors, exactly as its converter does, not the base vectors. HDF5 train/test
  arrays are retained in full. No new normalization is applied to angular-source files;
  queries follow the artifact's Euclidean radius interface.
- Clustering: banknote, dermatology, ecoli, phoneme and wine from OpenML version 1,
  using the artifact's preprocessing (including missing-value handling and
  feature standardization). Every training point is a query, at each of five radii.
  The artifact calls `nearest_neighbors(i, 1)` with graph weight `sqrt(radius)`;
  the effective binary64 radius `sqrt(radius)**2` is recorded alongside the nominal
  value, preserving that route rather than silently changing it.
- Geographical: the seven original POI/query pairs, at 500, 1000, 2000 and 5000 metres.

Input CSV coordinates are parsed as float32, matching the artifact, before the
agreed common conversion to uint32. One isotropic scale covers training and query
coordinates. Radius thresholds use exact rational arithmetic on stored binary64
values. All algorithms see the same converted input and must enumerate original
integer point coordinates, including multiplicity.

This recreates the **workload suite**, subject to the agreed integer conversion.
It does not reproduce the original floating-point geometry, Criterion sampling,
hardware-counter measurements, or original output interface. Our bounded timing
protocol and reporting adapters remain in force. The artifact gives structures
a mean-radius hint; our 2D Grid receives it, while the existing d-dimensional Grid
wrapper currently retains its own configuration. These are documented differences,
not claims of bit-for-bit reproduction of the paper's measurements.

## Data and preparation

Campaign definitions are versioned in `campaigns/`. Downloaded sources, prepared
inputs and readiness manifests live under ignored `data/`. A catalog entry does
not imply its dataset has been downloaded. Preparation records missing sources
explicitly; execution refuses an incomplete campaign. Performance preparation
never truncates training sets or query sets.

Activate the scientific Python environment from the root README. The original
real-world converters additionally need `pandas` and `h5py`:

```sh
python -m pip install pandas h5py
python tools/esa/fetch.py --families graph_embeddings uniform_points high_dimensional clustering geographical
python tools/esa/prepare.py --campaign all
```

Downloads preserve receipts with hashes; Zenodo ZIPs are checked against record
MD5s and catalog member CRCs. OpenML dataset versions and converter package versions
are recorded. The helper uses the pinned upstream Python conversion scripts, while
resolving their inconsistent shell-helper filename/cache paths. Source data are
never replaced by synthetic data.

To prepare a subset, pass one or more campaign names. To inventory already cached
data without downloading, use:

```sh
python tools/esa/prepare.py --campaign all --existing-only
```

Existing validated `data/esa2026-2d` inputs are reused for the three 2D companions.
Their 2D cases in the full campaigns use the same payload with a d-dimensional
header. The old 32-query d-dimensional correctness inputs are **not** mistaken for
full performance inputs. Conversion streams CSV chunks to keep memory bounded.

Catalog regeneration, when the two full Zenodo archives are available:

```sh
python tools/esa/catalog.py --archives data/ESA/archives
```

## Running on Arch

Full campaigns use the existing 20-entry d-dimensional roster. The 2D companions
use all 29 static entries, including Morton, MortonSIMD and MoronSIMDearly and the
manual integer-point SPRK variant. No dynamic implementation is added to ESA.

Several compiled adapters currently support only dimensions 2–16 and 32. The
runner records `unsupported_dimension` explicitly instead of removing the input
from the campaign. ANN, dynamic-dimension CGAL/nanoflann and the Python interfaces
accept dimensions at runtime; ordinary-data correctness admission still applies.
Unsupported dimensions are not numerical correctness failures. In particular,
creating the 96–960D campaign does not imply every competitor executable supports it.

```sh
bash tools/build_arch.sh
python tools/build_ddim.py

# Inspect coverage without launching jobs.
python tools/esa/run.py --campaign ESA_clustering --run paper-v2 --describe

# Run correctness, screening, planning and final measurements for one campaign.
python tools/esa/run.py --campaign 2D_ESA_graph_embeddings --run paper-v2

# Or execute stages individually.
python tools/esa/run.py --campaign ESA_graph_embeddings --run paper-v2 --phase correctness
python tools/esa/run.py --campaign ESA_graph_embeddings --run paper-v2 --phase screen
python tools/esa/run.py --campaign ESA_graph_embeddings --run paper-v2 --phase final
```

Use the same run label across the eight campaigns to share the existing budget
ledger. The common controller lock prevents overlap with an existing campaign.
Jobs use one physical core and 16 GiB each; up to four jobs share a 72 GiB cgroup
limit. Correctness/screening use 60-second job limits; final jobs use 180 seconds
and three repetitions. Shared budgets remain 30 minutes / 8 hours / 24 hours.
The final stage refuses a screen-based estimate exceeding the remaining budget.

Correctness uses the smallest ordinary workload per dimension with all its
training points and up to 32 evenly spaced original queries. No artificial
boundary/duplicate fixtures are used for admission. Source selections in the
performance manifest remain complete. Failed or timed-out screening pairs are
not repeated as successful final measurements. Input, backend and harness hashes
tie the stages together. Existing results are never overwritten.

Write `results/<campaign>/<run>/STOP` to stop a run. Results use the existing
collector:

```sh
python tools/collect.py results/2D_ESA_graph_embeddings/paper-v2/final/state.json
```

The older combined `esa2026-2d` and small `esa2026-ddim` campaigns remain available
for historical results. They are not the new full ESA suite.
