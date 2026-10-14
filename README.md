# DiskRangeReport

Research code and experiments for **Practical Distance Reporting by Sorting Along a Space-Filling Curve**.

Distance reporting asks which stored points lie within a given distance of a query location. In two dimensions, this means listing every point inside a disk. This project studies a simple index: sort integer points in Morton (Z-)order, locate short contiguous ranges of candidates, and scan those ranges while checking the actual distance. We compare construction and query costs with established spatial indexes. A separate dynamic theater studies updates in external indexes; there is no dynamic Morton implementation.

Publication preparation and the outstanding Chan/STANN source-permission question
are recorded in [publication status](docs/PUBLICATION.md).

## Start here

- **Our code:** [2D Morton](src/morton/morton.cc), [2D Morton with SIMD](src/morton/mortonSIMD.cc), [specialized 3D Morton](src/morton/morton3D.cc), and [d-dimensional Morton](src/morton/morton_d_dim.cc).
- **Use an index directly:** [standalone 2D example](docs/MORTON.md) and [four-file API guide](src/morton/README.md).
- **Run experiments:** [`run_theater.py`](run_theater.py) is the single top-level entry point. [Build and preparation instructions](docs/RUNNING.md) explain how to supply its inputs.
- **Understand the comparison:** [reporting contract and adaptations](docs/REPORTING.md), [experimental protocol](docs/EXPERIMENTS.md), and [third-party credits](docs/THIRD_PARTY.md).

SIMD means single instruction, multiple data: several values are processed together. The active 2D Morton variants are `Morton`, `MortonSIMD` and `MortonPlusCPP`. The scalar Morton baseline uses no SIMD and no early-termination oracle. Dimensional Morton supports at most 16 dimensions because its candidate-cell enumeration grows exponentially with dimension. The 3D implementation specializes that work for three coordinates.


## Retained Morton and SPRK implementations (14 October 2026)

All non-Morton/SPRK competitors are retained, including all three Boost variants.
The 2D roster now has 29 configurations. The retained family entries are:

| Display name | Machine ID | Implementation |
|---|---|---|
| Morton | `Morton` | Scalar C++ Morton |
| Morton (simd) | `MortonSIMD` | SIMD C++ Morton |
| Morton (plus) | `MortonPlusCPP` | C++ translation of the ESA authors' MortonPlus |
| SPRK (original) | `esa_sprk_CHEATING_IDS_ONLY` | Original f64 SPRK, materialized IDs |
| SPRK (adapted) | `esa_sprk_RUST_EXACT` | Their Rust `IntegerPointSprk`, exact integer coordinates |

Morton3D and MortonDDim remain available in their existing dimensions. The Rust
MortonPlus competitor and our old/fast SPRK adaptations are retired. The old
higher-dimensional exact SPRK wrapper is also removed. New local 3D extensions
are available as `MortonPlus3D` and `esa_sprk_RUST_EXACT_3D`, displayed as
Morton (plus) and SPRK (adapted). Other dimensional competitors remain available.
Machine IDs preserve correspondence with recorded results; the `CHEATING` token
is historical and is no longer the display label. The original SPRK contract is
still different and must be disclosed; it is eligible to set normalization baselines.

**Morton (plus) credit:** the algorithm and Rust implementation were supplied by
the ESA authors: Thomas Blasius, Jean-Pierre von der Heydt, Tobias Kempf, Dennis
Kobert and Nikolai Maas, with the Rust implementation by Dennis Kobert. This
repository's contribution is the C++ translation and benchmark integration.
Source: [MortonPlus branch](https://github.com/TrueDoctor/DiskReportingDataStructure/tree/morton-plus),
commit `7e6f57558ca6ae8b93a3ca0f64a2d1b0ec579097`. See
[third-party credits](docs/THIRD_PARTY.md) for licenses and the SPRK revision.

`bash tools/build_arch.sh` builds all active 2D backends, including the standalone
`morton_cpp` and `sprk_rust_exact` programs. To rebuild just those two, run
`bash tools/build_selected_2d.sh`. Existing prepared manifests must be regenerated
for the new roster; keep completed results and use fresh run labels.

The fixed AVX2/BMI2 2D MortonPlus is frozen by a checked SHA-256 version record.
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
| [static](theaters/static/README.md) | 2D input/radius scaling, fixed-size synthetic inputs, large geographical inputs | 235 |
| [small](theaters/small/README.md) | The paper's native 2D graph, uniform and geographical workloads | 50 |
| [static-3d](theaters/static-3d/README.md) | 3D synthetic input/radius scaling and fixed-size inputs | 135 |
| [d-dim](theaters/d-dim/README.md) | Four imported families, restricted to dimensions above two | 279 |
| [dynamic](theaters/dynamic/README.md) | 2D insertions, deletions and disk queries | 90 |

Default rosters run all retained competitors. The 2D roster has 29 entries
(three Morton, two SPRK, all other competitors and a scan control). Static 3D
has 23 entries (two Morton and two SPRK); d-dimensional suites have 23 entries
(two dimensional Morton and up to two supported SPRK entries). Dynamic suites
have nine competitors. Unsupported dimensions and correctness exclusions are
recorded rather than silently substituted. See [competitor rosters](docs/COMPETITORS.md).

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

The top-level runner uses **one worker on one physical core**, with CPU 1 selected by default (`--cpu` changes it). Serial jobs have a **64 GiB memory cap**, with swap disabled on native Arch execution. Correctness and screening have 60-second whole-job limits; final measurements have 180 seconds. Each theater has separate phase budgets: 30 minutes for correctness, eight hours for screening and 24 hours for final measurements. Campaigns within a theater share those budgets; different theaters do not. The d-dimensional theater has a separate 24-hour screening total and 24-hour final total, with [protected campaign allocations](theaters/d-dim/README.md). These are caps, not promised completion times. Each run records its own policy; the low-level concurrent-job cap remains 16 GiB per job.

The [Arch Docker image](Dockerfile) builds the 2D programs. Native user systemd is the supported route for whole theaters containing imported or dimensional workloads. The container's process backend currently supports synthetic campaigns only; [details](docs/RUNNING.md#docker).

## What the measurements mean

Conforming queries materialize the original integer point coordinates, including repeated occurrences. Membership checks, adapter work and output writes belong inside query timing. Build, query and update times are separate; memory caps are enforced but peak memory is not measured, so these results support no space claim; input loading and correctness verification are outside those algorithm timings.

The ESA authors' Rust **SPRK (adapted)** implementation follows this coordinate-reporting contract. **SPRK (original)** restores the historical f64 floating-point radius search and materializes only point IDs. It omits exact integer membership filtering and coordinate output from query timing. It measures a different output contract and must be identified separately in tables. [Reporting details](docs/REPORTING.md) explain the distinction.

Correctness admission includes ordinary workloads and mandatory boundary/duplicate fixtures for every entry. Successful answer counts are compared across implementations and repetitions in every phase; disagreements block the run. A failure means an implementation or adapter did not satisfy this experiment's contract on the tested inputs; it is not automatically evidence of an upstream defect. Incorrect outputs, timeouts, crashes and unsupported dimensions remain explicit in the results.

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
historical_data/             private previous datasets/results; never published
data/, results/             generated inputs and new measurements (not committed)
bin/, build/                 generated programs (not committed)
```

See the [source map](src/README.md) to distinguish algorithm code from benchmark adapters. Generated inputs may be shared between campaigns; do not copy only a campaign's `prepared/` folder without resolving the paths in its manifest.

The [project license](LICENSE) applies to project code. Third-party code retains its own licenses, notices and attribution. [Modification records](docs/THIRD_PARTY.md) identify local adaptations. Previous datasets, results, logs and measurement metadata are kept only in the ignored `historical_data/` folder for correspondence and paper drafting. That folder is excluded from Git, Git exports and Docker builds. Old project code, obsolete campaign definitions and obsolete runners are removed. New experiments use fresh `data/` and `results/` directories; the runners never read `historical_data/` implicitly.

Publication labels and modification categories are specified in the [adapter catalog](docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.

To check complete returned point multisets across a frozen queue, use the separate [output-verification script](verify_outputs.py). It compares every original query with exact integer geometry, including duplicates and the cheating diagnostic; see [usage and coverage](docs/OUTPUT-VERIFICATION.md).

An experimental standalone d-dimensional Plus header is available at
`src/morton/mortonplus_d_dim.hpp` (dimensions 1-16, AVX2). Its default dimensional runner ID is
`MortonPlusDDim`; see the version notes for validation and memory tradeoffs.
Morton license text is supplied in `src/morton/LICENSE` rather than embedded
in the implementation files.
