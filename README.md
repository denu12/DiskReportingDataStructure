# DiskRangeReport

Research code and experiments for **Practical Distance Reporting by Sorting Along a Space-Filling Curve**.

Distance reporting asks which stored points lie within a given distance of a query location. In two dimensions, this means listing every point inside a disk. This project studies a simple index: sort integer points in Morton (Z-)order, locate short contiguous ranges of candidates, and scan those ranges while checking the actual distance. We compare construction and query costs with established spatial indexes. A separate dynamic theater studies updates in external indexes; there is no dynamic Morton implementation.

For closed, axis-aligned squares in 2D and cubes in 3D, see the companion
[SquareReportingDataStructure](https://github.com/denu12/SquareReportingDataStructure).
It benchmarks native box queries with points or IDs as output. This repository
benchmarks Euclidean distance reporting and retains the disk and ball measurements.

Publication preparation and the outstanding Chan/STANN source-permission question
are recorded in [publication status](docs/PUBLICATION.md).

## Start here

- **Sugiura–Ishikawa original implementation:** [upstream PostgreSQL code](src/third_party/psql-refine-z-range/README.md), included unchanged as a pinned Git submodule. Initialise it with `git submodule update --init src/third_party/psql-refine-z-range`. The `postgres_zrange` adapter runs their unchanged SQL with a PostgreSQL B-tree and exact distance filtering. See [PostgreSQL setup and timing](docs/POSTGRESQL.md). See [third-party credits](docs/THIRD_PARTY.md#sugiuraishikawa-z-ordered-range-refinement).

- **Our code:** Morton variants and tests in [2d](src/morton/2d/README.md), [3d](src/morton/3d/README.md), [d_dim](src/morton/d_dim/README.md), and [dynamic](src/morton/dynamic/README.md).
- **Use an index directly:** [standalone 2D example](docs/MORTON.md) and [Morton directory guide](src/morton/README.md).
- **Run experiments:** [`run_theater.py`](run_theater.py) is the single top-level entry point. [Build and preparation instructions](docs/RUNNING.md) explain how to supply its inputs.
- **Understand the comparison:** [reporting contract and adaptations](docs/REPORTING.md), [experimental protocol](docs/EXPERIMENTS.md), and [third-party credits](docs/THIRD_PARTY.md).

## Recorded measurements

The latest [22 November 2026 snapshot](measurements/2026-11-22/README.md) includes current and historical experiment records, including failures and partial runs. The [3 November snapshot](measurements/2026-11-03/README.md) remains available as an earlier capture. These are raw observations, not a single combined comparison: reporting contracts, source revisions and workloads differ between runs. Read each snapshot's captured queue status rather than treating an older status as current.

Indexicon and the native f64 exact higher-dimensional SPRK bridge are integrated.

See the [23 November result-version review](docs/RESULT-VERSIONS.md) for the
explicit 2D selection and newer-version-only higher-dimensional repair.
Historical coverage does not establish coverage of a changed adapter. Build
native Rust dispatch with `python3 tools/build_native_rust.py`; current routing
uses an isolated versioned target rather than a historical queue build.
Superseded adapter sources were removed on 25 November. The current native
Rust source is [here](src/runner/native-rust/README.md); PH/PSI use the retained
`ph-psi` profile. See the [source cleanup record](config/source-cleanup-20261125.json).
The [frozen source collection](reproducibility/2026-11-22/README.md) preserves later
disk adapters and controllers with hashes and dependency references. Use the
recorded version for each historical run; the current harness has newer failure
handling. The [repository audit](docs/REPOSITORY-AUDIT-2026-11-22.md) records the repairs.

## Checked-in algorithm rosters

The checked-in 2D roster has 50 entries and the 3D roster has 41, including controls and
entries with explicit unsupported outcomes. All implementations are listed below; native-output policy is described in
[the original-API campaign](docs/ORIGINAL-CAMPAIGN.md).
The October additions, their output types and validation limitations are listed
in [additional competitors](docs/ADDITIONAL-COMPETITORS.md). The later Indexicon
integration is described [separately](docs/INDEXICON.md).

## Competitor implementations

The table covers every implementation in the current 2D, 3D, higher-dimensional
and dynamic rosters, plus the PMQ integration still pending. Variants
that share source have the same count; their counts must not be added together.
Point indices identify stored points rather than containing their coordinates. The output column
describes what our timed query materializes. For rectangle-query APIs, the timed
query also filters the candidates against the disk or sphere.

Line counts include comments and blank lines. Single-file implementations are
counted directly; for libraries, the counted component is indicated in the table.
Separate benchmarks, tests and external dependencies are excluded, while inline
tests/examples remain part of their source files. These are source-size figures,
not a comparison of equivalent standalone programs or of code executed per query.
The [counting record](docs/competitor-source-counts.json) lists every counted file,
its line count and hash, together with the scope of each total. Sources available
only in the build environment were read from Archie's pinned dependency caches.

| Implementation | Source | Language | Lines of code | What it reports |
|---|---|---|---:|---|
| Morton (2D) | [This repository](src/morton/2d/morton.cc) | C++ | 159 | Integer points |
| Morton (simd, 2D) | [This repository](src/morton/2d/mortonSIMD.cc) | C++ | 259 | Integer points |
| Morton (plus, 2D) | [Local C++ implementation of ESA MortonPlus](src/morton/2d/mortonplus.hpp) | C++ | 294 | Integer points |
| Morton (3D) | [This repository](src/morton/3d/morton3D.cc) | C++ | 94 | Integer points |
| Morton (simd, 3D) | [This repository](src/morton/3d/mortonSIMD3D.hpp) | C++ | 269 | Integer points |
| Morton (plus, 3D) | [Local C++ implementation of ESA MortonPlus](src/morton/3d/mortonplus3d.hpp) | C++ | 271 | Integer points |
| Morton (d-dimensional) | [This repository](src/morton/d_dim/morton_d_dim.cc) | C++ | 324 | Integer points |
| Morton (plus, d-dimensional) | [Local C++ implementation of ESA MortonPlus](src/morton/d_dim/mortonplus_d_dim.hpp) | C++ | 348 | Integer points |
| SPRK (original) | [SPRK 0.2.0](https://github.com/wembed-pdf/sprk) | Rust | 3,237 (library) | Point indices |
| SPRK (adapted, 2D) | [ESA authors’ adaptation](https://github.com/TrueDoctor/DiskReportingDataStructure/tree/sprk-exact-point-reporting) | Rust | 3,625 (library + extension) | Integer points |
| SPRK (adapted, no explicit SIMD) | [ESA adaptation with local compiler-only option](src/third_party/esa2026/sprk/src/integer_reporting.rs) | Rust | 3,625 (library + extension) | Integer points |
| SPRK (adapted, 3D) | [Local 3D extension](src/third_party/esa2026/sprk/src/integer_reporting_3d.rs) | Rust | 3,789 (library + extensions) | Integer points |
| SPRK (native f64, exact d-dimensional) | [Native-tree bridge](src/runner/dimensional/sprk_ddim/main.rs) | Rust | Not included in the October source-size snapshot | Integer points after timed exact filtering |
| Indexicon (ten variants) | [Pinned headers and adapter guide](docs/INDEXICON.md) | C++ | Not included in the October source-size snapshot | Original point IDs after exact disk/ball filtering |
| Boost linear (static and dynamic) | [Boost.Geometry 1.87.0](https://github.com/boostorg/geometry/tree/boost-1.87.0/include/boost/geometry/index) | C++ | 20,748 (shared index headers) | Points |
| Boost quadratic (static and dynamic) | [Boost.Geometry 1.87.0](https://github.com/boostorg/geometry/tree/boost-1.87.0/include/boost/geometry/index) | C++ | 20,748 (shared index headers) | Points |
| Boost R-star (static and dynamic) | [Boost.Geometry 1.87.0](https://github.com/boostorg/geometry/tree/boost-1.87.0/include/boost/geometry/index) | C++ | 20,748 (shared index headers) | Points |
| CGAL range tree | [Upstream source](https://github.com/CGAL/cgal/tree/v6.0.1/Range_segment_trees) | C++ | 1,649 (component) | Points, then disk filtering |
| CGAL k-d tree | [Upstream source](https://github.com/CGAL/cgal/tree/v6.0.1/Spatial_searching) | C++ | 3,503 (component) | Floating-point points |
| THST quadtree | [Upstream source](https://github.com/tuxalin/THST/tree/4ff6aa575f87dce4321754981314a923b0b4bbb6/include/THST) | C++ | 1,998 (component) | Points, then disk filtering |
| THST R-tree | [Upstream source](https://github.com/tuxalin/THST/tree/4ff6aa575f87dce4321754981314a923b0b4bbb6/include/THST) | C++ | 2,630 (component) | Points, then disk filtering |
| Pkd-tree | [Upstream source](https://github.com/ucrparlay/Pkd-tree/tree/62c8839aa6e87b8cbf652a341a472f1fcf789ec0/include) | C++ | 2,813 (component) | Points, then disk filtering |
| PAM (repaired) | [Upstream source](https://github.com/cmuparlay/PAM/tree/3574543ad84c34acb22edbeecb9d11a97a5eb87d) | C++ | 3,218 (component) | Coordinate pairs, then disk filtering |
| ParGeo | [Upstream source](https://github.com/wangyiqiu/pargeo/tree/b87077ca253d28595e6887bb369501a64774712a) | C++ | 698 (component) | Point indices |
| Chan (adapted) | [Chan’s SSS source](src/third_party/chan_sss/sss-original.cc) | C++ | 98 | Original point IDs; fixed-radius adaptation of the original SSS search |
| STANN (adapted) | [Recovered STANN source](src/third_party/stann/upstream) | C++ | 6,204 (headers) | Original point IDs; fixed-box traversal and exact ball filter |
| ANN | [ANN](https://www.cs.umd.edu/~mount/ANN/) | C++ | 5,496 (library) | Point indices |
| nanoflann | [Vendored upstream header](src/third_party/esa2026/nanoflann.hpp) | C++ | 2,721 | Point indices and squared distances |
| Kiddo | [Upstream crate](https://github.com/sdd/kiddo) | Rust | 16,027 (crate source) | Point indices |
| Nabo | [Upstream crate](https://github.com/enlightware/nabo-rs) | Rust | 1,213 (crate source) | Point indices |
| Neighbourhood | [Upstream crate](https://github.com/HOminus/neighbourhood) | Rust | 466 (crate source) | Point indices |
| Acap VP-tree | [Upstream crate](https://github.com/tavianator/acap) | Rust | 3,674 (crate source) | Point indices |
| Orthtree | [Original ESA module](src/third_party/esa2026-workloads/src/orthtree.rs) | Rust | 367 (module) | Point indices |
| Grid | [Original ESA module](src/third_party/esa2026-workloads/src/grid.rs) | Rust | 249 (module) | Point indices |
| SNN (Rust) | [Original ESA module](src/third_party/esa2026-workloads/src/snn.rs) | Rust | 204 (module) | Point indices |
| scikit-learn k-d tree | [scikit-learn 1.9.1](https://github.com/scikit-learn/scikit-learn/tree/1.9.1/sklearn/neighbors) | Python / Cython | 2,945 (tree + shared templates) | Point indices |
| scikit-learn ball tree | [scikit-learn 1.9.1](https://github.com/scikit-learn/scikit-learn/tree/1.9.1/sklearn/neighbors) | Python / Cython | 2,893 (tree + shared templates) | Point indices |
| SNN (Python) | [Original SNN package](src/third_party/esa2026/snnpy) | Python / Cython | 186 (package) | Point indices |
| PH-tree | [Author-maintained C++ implementation](https://github.com/tzaeschke/phtree-cpp) | C++ | 8,441 (library headers) | Point indices |
| Multidimensional PGM-index | [PGM-index](https://github.com/gvinciguerra/PGM-index) | C++ | 13,977 (shared library headers) | Original point IDs; coarse indexing cells, exact ball filter, iterator fixes |
| PSI k-d tree | [SpaceTreeLib](https://github.com/ucrparlay/SpaceTreeLib) | C++ | 20,259 (shared PSI library) | Integer points with ID/curve-code fields |
| P-Orth tree | [SpaceTreeLib](https://github.com/ucrparlay/SpaceTreeLib) | C++ | 20,259 (shared PSI library) | Integer points with ID/curve-code fields |
| SPaC-Z tree | [SpaceTreeLib](https://github.com/ucrparlay/SpaceTreeLib) | C++ | 20,259 (shared PSI library) | Integer points with ID/curve-code fields |
| SPaC-H tree | [SpaceTreeLib](https://github.com/ucrparlay/SpaceTreeLib) | C++ | 20,259 (shared PSI library) | Integer points with ID/curve-code fields |
| libspatialindex linear | [libspatialindex](https://github.com/libspatialindex/libspatialindex) | C++ | 28,316 (shared library) | Point indices |
| libspatialindex quadratic | [libspatialindex](https://github.com/libspatialindex/libspatialindex) | C++ | 28,316 (shared library) | Point indices |
| libspatialindex R-star | [libspatialindex](https://github.com/libspatialindex/libspatialindex) | C++ | 28,316 (shared library) | Point indices |
| libspatialindex STR | [libspatialindex](https://github.com/libspatialindex/libspatialindex) | C++ | 28,316 (shared library) | Point indices |
| Brute force (2D control) | [This repository](src/app/algorithms/static/naive.hh) | C++ | 21 | Integer points |
| Brute force (dimensional control) | [Python runner](src/runner/dimensional/python_check.py) | Python | 57 (shared runner; scan is one expression) | Point indices |
| PMQ — integration blocked | [Original PMQ](https://github.com/cicerolp/pmq) | C++ | 648 (PMQ.h only) | Records through a callback; external PMA dependency missing |
| Sugiura–Ishikawa PostgreSQL Z-range refinement | [Original PostgreSQL implementation](https://github.com/dbgroup-nagoya-u/psql-refine-z-range) | PL/pgSQL | 575 (SQL functions) | Point IDs through the database adapter; original SQL returns interval endpoints |

Morton is the former Morton (compiler SIMD), promoted without changing its
four-cell search or reporting semantics. The old scalar Morton and experimental
split/table/lookup/blocks source variants have been removed; historical measurements remain.
Historical measurement files retain their original machine IDs; reports map the
completed `MortonAutoSIMD` campaign to the new Morton name. Older `Morton`
measurements describe the previous scalar version and must not be mixed with it.

Three-dimensional and d-dimensional defaults also include the external competitors
listed in their campaign definitions. The 3D roster contains compiler-vectorized Morton, explicit AVX-512 Morton
(simd), and AVX-512 Morton (plus). The adapted no-SIMD SPRK configuration is
currently a 2D implementation. Dynamic
defaults retain the three Boost variants. Completed campaigns remain unchanged.
Original SPRK reports IDs with relaxed floating-point membership; adapted SPRK
reports exact integer coordinates. Both contracts remain explicit in reports.

**Morton (plus) credit:** the algorithm and Rust implementation were supplied by
the ESA authors: Thomas Blasius, Jean-Pierre von der Heydt, Tobias Kempf, Dennis
Kobert and Nikolai Maas, with the Rust implementation by Dennis Kobert. This
repository's contribution is the C++ translation and benchmark integration.
Source: [MortonPlus branch](https://github.com/TrueDoctor/DiskReportingDataStructure/tree/morton-plus),
commit `7e6f57558ca6ae8b93a3ca0f64a2d1b0ec579097`. See
[third-party credits](docs/THIRD_PARTY.md) for licenses and the SPRK revision.

`bash tools/build_arch.sh` builds all active 2D backends, including `morton_cpp`, `sprk_rust_exact` and `sprk_rust_exact_nosimd`. To rebuild the selected Morton/SPRK backends, run
`bash tools/build_selected_2d.sh`. Existing prepared manifests must be regenerated
for the new roster; keep completed results and use fresh run labels.

The fixed AVX-512/BMI2 2D MortonPlus is frozen by a checked SHA-256 version record.
Build the new 3D versions with `bash tools/build_selected_3d.sh` and verify them
with `python3 tools/check_selected_3d.py`. See [version and 3D implementation
notes](docs/MORTONPLUS-VERSIONS.md) for the lock, APIs, and validation.

## Workloads and theaters

Some workloads are derived from:

> Thomas Blasius, Jean-Pierre von der Heydt, Tobias Kempf, Dennis Kobert and Nikolai Maas. **[Benchmarking and Engineering Data Structures for Spherical Range Queries](https://doi.org/10.4230/LIPIcs.ESA.2026.22)**. 34th European Symposium on Algorithms, 2026, LIPIcs 388, 22:1-22:17.

**ESA** below refers to that European Symposium on Algorithms paper. Its [reproducibility artifact](https://github.com/wembed-pdf/rembed) supplies workload selections and several competitor implementations. We convert its floating-point inputs to a common integer grid and use our own timing and reporting protocol. These are adapted experiments, not a literal reproduction of the paper's measurements. See the [workload provenance guide](docs/ESA-WORKLOADS.md).

An experiment **theater** contains campaigns. A **campaign** studies a related question; a **suite** varies a workload property; an **instance** fixes the data, queries and parameters. A measured job runs one implementation on one instance for one repetition.

| Theater | Contents | Instances |
|---|---|---:|
| [static](theaters/static/README.md) | 2D input/radius scaling, fixed-size synthetic inputs, large geographical inputs | 295 |
| [small](theaters/small/README.md) | The paper's native 2D graph, uniform and geographical workloads | 50 |
| [static-3d](theaters/static-3d/README.md) | 3D synthetic input/radius scaling and fixed-size inputs | 195 |
| [d-dim](theaters/d-dim/README.md) | Four imported families, restricted to dimensions above two | 279 |
| [dynamic](theaters/dynamic/README.md) | 2D insertions, deletions and disk queries | 90 |

Default rosters contain 50 2D configurations, 41 static 3D configurations,
up to 40 higher-dimensional configurations (subject to supported dimensions), and three
dynamic Boost configurations. These totals include controls and unsupported entries.
Static 3D includes Morton, Morton (simd) and Morton (plus).
See [competitor rosters](docs/COMPETITORS.md) and the
[3D upgrade evidence](docs/MORTON-3D-UPGRADE.md).

Counts describe configured instances, not successful jobs. Admission, supported dimensions and screening determine which implementation/instance pairs reach final measurement. Each theater has its own README and `theater.json`; campaign definitions live beneath it. The word `small` distinguishes the original 2D collection from `GeographyLarge`; it is not an upper bound on every input size.

## Run a theater on Arch Linux

From the repository root, after [building and preparing data](docs/RUNNING.md):

```sh
source .venv/bin/activate
python run_theater.py                         # list theaters
python run_theater.py small                   # preview; launches nothing
python run_theater.py small --check           # verify prepared inputs and binaries
python run_theater.py small --run paper-small --execute
python run_theater.py small --run paper-small --status
python run_theater.py small --run paper-small --stop
```

Replace `small` with any theater ID from the table. One command executes fresh correctness admission across that theater, screening, and three final repetitions of eligible pairs. It does not download data or build code implicitly. Use a fresh run label for each theater execution; existing measurements and stop markers are never overwritten.

The top-level runner uses **one worker on one physical core**, with CPU 1 selected by default (`--cpu` changes it). Serial jobs have a **64 GiB memory cap**, with swap disabled on native Arch execution. Correctness and screening have 60-second whole-job limits; final measurements have 180 seconds. There is no aggregate campaign or theater time cap. The per-job limits remain in force. Each run records its own policy; the low-level concurrent-job cap remains 16 GiB per job.

The [Arch Docker image](Dockerfile) builds the 2D programs. Native user systemd is the supported route for whole theaters containing imported or dimensional workloads. The container's process backend currently supports synthetic campaigns only; [details](docs/RUNNING.md#docker).

## What the measurements mean

Non-SPRK competitors now materialize their native output: points or indices, whichever their API returns. No conversion from indices to coordinates is required inside query timing. Membership checks and native output writes remain timed; correctness-only conversion is outside timing. SPRK configurations are unchanged. Build, query and update times are separate; memory caps are enforced but peak memory is not measured, so these results support no space claim; input loading and correctness verification are outside those algorithm timings.

## Original-API campaign (15 October 2026)

The full competitor roster is restored: 30 entries in 2D and 24 in 3D, including
scan controls. Morton uses the retained implementations; SPRK stays as configured.
Other competitors use original search implementations and native outputs. Necessary
file-format and box-to-disk query plumbing is still part of this benchmark harness.
Original arithmetic, boundary conventions, duplicate behavior and bugs are not repaired.

| Competitor | Timed output |
|---|---|
| Morton / SIMD / Plus | Integer points |
| Boost linear / quadratic / R-star | Native points |
| CGAL k-d tree | Native floating-point points |
| CGAL range tree; THST quad/R-tree; Pkd | Native points, with box-to-disk filtering |
| ParGeo | Native indices into its stored point sequence |
| PAM (repaired) | Native coordinate pairs from the original range-query example, with disk filtering |
| ANN | Native indices |
| nanoflann | Native index/distance pairs |
| Kiddo, Nabo, Neighbourhood, VP-tree, Orthtree, Grid | Indices from the original ESA wrappers |
| scikit-learn k-d/ball trees; Python SNN; Rust SNN | Indices |
| Brute-force controls | 2D points; dimensional indices |
| SPRK (original), unchanged | Indices |
| SPRK (adapted), including no-explicit-SIMD, unchanged | Integer points |
| Chan and STANN (adapted) | Original construction and search adapted for fixed-radius reporting; original point IDs |

The original ESA Rust search modules are included directly from the vendored
upstream source; their f32 arithmetic is retained. Kiddo uses the unpatched registry
crate. ParGeo/PAM use reconstructed pre-patch files whose Git blob IDs are verified.
No original radius-query result is filtered to force agreement with integer geometry.
PAM's original example uses signed int coordinates and its original reporting callback;
representation/boundary/duplicate discrepancies remain visible.

At the user's request, **failed correctness does not prevent timing**. Each timed
row carries `correctness_admission`, and count mismatches remain flagged. Success
of a timed process is not a correctness certificate. Crashes, timeouts and unsupported
queries remain explicit outcomes. Resource limits still apply. Old measurements
retain their previous contracts and are not relabeled as original-API results.

The ESA authors' Rust **SPRK (adapted)** implementation follows this coordinate-reporting contract. **SPRK (original)** restores the historical f64 floating-point radius search and materializes only point IDs. It omits exact integer membership filtering and coordinate output from query timing. It measures a different output contract and must be identified separately in tables. [Reporting details](docs/REPORTING.md) explain the distinction.

Correctness admission includes ordinary workloads and mandatory boundary/duplicate fixtures for every entry. Successful answer counts are compared across implementations and repetitions in every phase. Disagreements remain flagged; the current policy permits timing failed entries. A failure means an implementation or adapter did not satisfy this experiment's contract on the tested inputs; it is not automatically evidence of an upstream defect. Incorrect outputs, timeouts, crashes and unsupported dimensions remain explicit in the results.

## Repository map

```text
run_theater.py                run all campaigns in a selected theater
theaters/<theater>/           theater README, membership and campaign definitions
  campaigns/<campaign>/      workload definition and README
config/                      shared execution policy and imported-workload catalog
src/
  morton/                    standalone Morton indexes, including the credited MortonPlus port
  app/algorithms/static/     static competitor adapters and Morton registrations
  app/algorithms/dynamic/    dynamic competitor adapters
  benchmark/                 shared geometry, timing and correctness support
  runner/dimensional/       3D/d-dimensional benchmark drivers and adapters
  third_party/              vendored libraries and imported ESA dataset tools
tools/                       our build, data preparation and orchestration scripts
docs/                        usage, methodology, adaptation records and credits
measurements/                dated, compressed public result snapshots
historical_data/             ignored working copies of previous datasets/results
data/, results/             generated inputs and new measurements (not committed)
bin/, build/                 generated programs (not committed)
```

See the [source map](src/README.md) to distinguish algorithm code from benchmark adapters. Generated inputs may be shared between campaigns; do not copy only a campaign's `prepared/` folder without resolving the paths in its manifest.

The [project license](LICENSE) applies to project code. Third-party code retains its own licenses, notices and attribution. [Modification records](docs/THIRD_PARTY.md) identify local adaptations. Recorded results, logs and measurement metadata are published in [dated snapshots](measurements/README.md). Raw input datasets, private documents and local working copies in `historical_data/` remain excluded from Git and Docker. Old project code, obsolete campaign definitions and obsolete runners are removed. New experiments use fresh `data/` and `results/` directories; the runners never read `historical_data/` implicitly.

Publication labels and modification categories are specified in the [adapter catalog](docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.

The latest [measurement snapshot, captured on 22 November 2026](measurements/2026-11-22/README.md),
preserves completed campaigns and the recorded progress of ongoing queues.
Historical, incorrect and timed-out outcomes remain labelled in the raw records.

To check complete returned point multisets across a frozen queue, use the separate [output-verification script](verify_outputs.py). It compares every original query with exact integer geometry, including duplicates and the cheating diagnostic; see [usage and coverage](docs/OUTPUT-VERIFICATION.md).

An experimental standalone d-dimensional Plus header is available at
`src/morton/d_dim/mortonplus_d_dim.hpp` (dimensions 1-16, AVX2). Its default dimensional runner ID is
`MortonPlusDDim`; see the version notes for validation and memory tradeoffs.
Morton license text is supplied in `src/morton/LICENSE` rather than embedded
in the implementation files.

The current 2D Morton (plus), Morton (simd), and Morton (blocks+simd) require AVX512F/BMI2.
See [the optimization study](docs/MORTONPLUS-AVX512.md) for measured gains and
validation; historical PDF results retain their frozen implementation versions.

The minimally adapted Chan, STANN and Multidimensional PGM entries are documented
in [reporting adaptations](docs/REPORTING-ADAPTATIONS.md). Earlier original-only
measurements remain unchanged; new adapters require fresh runs.
