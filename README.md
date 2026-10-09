# DiskRangeReport

Research code and experiments for **Practical Distance Reporting by Sorting Along a Space-Filling Curve**.

Distance reporting asks which stored points lie within a given distance of a query location. In two dimensions, this means listing every point inside a disk. This project studies a simple index: sort integer points in Morton (Z-)order, locate short contiguous ranges of candidates, and scan those ranges while checking the actual distance. We compare its construction, query and update costs with established spatial indexes.

Publication preparation and the outstanding Chan/STANN source-permission question
are recorded in [publication status](docs/PUBLICATION.md).

## Start here

- **Our code:** [2D Morton](src/morton/morton.cc), [2D Morton with SIMD](src/morton/mortonSIMD.cc), [specialized 3D Morton](src/morton/morton3D.cc), and [d-dimensional Morton](src/morton/morton_d_dim.cc).
- **Use an index directly:** [standalone 2D example](docs/MORTON.md) and [four-file API guide](src/morton/README.md).
- **Run experiments:** [`run_theater.py`](run_theater.py) is the single top-level entry point. [Build and preparation instructions](docs/RUNNING.md) explain how to supply its inputs.
- **Understand the comparison:** [reporting contract and adaptations](docs/REPORTING.md), [experimental protocol](docs/EXPERIMENTS.md), and [third-party credits](docs/THIRD_PARTY.md).

SIMD means single instruction, multiple data: several values are processed together. The active 2D pair is `Morton` and `MortonSIMD`. The scalar Morton baseline uses no SIMD and no early-termination oracle. Dimensional Morton supports at most 16 dimensions because its candidate-cell enumeration grows exponentially with dimension. The 3D implementation specializes that work for three coordinates.

## Workloads and theaters

Some workloads are derived from:

> Thomas Bläsius, Jean-Pierre von der Heydt, Tobias Kempf, Dennis Kobert and Nikolai Maas. **[Benchmarking and Engineering Data Structures for Spherical Range Queries](https://doi.org/10.4230/LIPIcs.ESA.2026.22)**. 34th Annual European Symposium on Algorithms, 2026, LIPIcs 388, 22:1–22:17.

**ESA** below refers to that European Symposium on Algorithms paper. Its [reproducibility artifact](https://github.com/wembed-pdf/rembed) supplies workload selections and several competitor implementations. We convert its floating-point inputs to a common integer grid and use our own timing and reporting protocol. These are adapted experiments, not a literal reproduction of the paper's measurements. See the [workload provenance guide](docs/ESA-WORKLOADS.md).

An experiment **theater** contains campaigns. A **campaign** studies a related question; a **suite** varies a workload property; an **instance** fixes the data, queries and parameters. A measured job runs one implementation on one instance for one repetition.

| Theater | Contents | Instances |
|---|---|---:|
| [static](theaters/static/README.md) | 2D scaling, fixed-size synthetic inputs, large geographical inputs | 170 |
| [small](theaters/small/README.md) | The paper's native 2D graph, uniform and geographical workloads | 50 |
| [static-3d](theaters/static-3d/README.md) | 3D synthetic scaling and fixed-size inputs | 70 |
| [d-dim](theaters/d-dim/README.md) | Four imported families, restricted to dimensions above two | 279 |
| [dynamic](theaters/dynamic/README.md) | 2D insertions, deletions and disk queries | 90 |

The current 2D static roster has 28 configurations: two Morton versions, 25 external configurations (including the two SPRK reporting contracts), and one scan reference. The dynamic roster has nine external configurations. The dimensional default has 19 enabled external configurations; 3D adds Morton3D and the IDs-only SPRK diagnostic.

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

The top-level runner uses **one worker on one physical core**, with CPU 1 selected by default (`--cpu` changes it). Serial jobs have a **64 GiB memory cap**, with swap disabled on native Arch execution. Correctness and screening have 60-second whole-job limits; final measurements have 180 seconds. Shared phase budgets are 30 minutes, eight hours and 24 hours respectively. These are caps, not promised completion times. Each run records its own policy; the low-level concurrent-job cap remains 16 GiB per job.

The [Arch Docker image](Dockerfile) builds the 2D programs. Native user systemd is the supported route for whole theaters containing imported or dimensional workloads. The container's process backend currently supports synthetic campaigns only; [details](docs/RUNNING.md#docker).

## What the measurements mean

Conforming queries materialize the original integer point coordinates, including repeated occurrences. Membership checks, adapter work and output writes belong inside query timing. Build, query and update times are separate; input loading and correctness verification are outside those algorithm timings.

The local **SPRK (adapted)** wrapper follows this coordinate-reporting contract. **SPRK (cheating)** reports point IDs inside timing and gathers coordinates only for verification afterwards. It measures a different output contract and must be identified separately in tables. That local label is not a claim that the upstream authors violated their own benchmark contract. [Reporting details](docs/REPORTING.md) explain the distinction.

Correctness admission uses ordinary workloads. Artificial boundary and duplicate stress fixtures are not admission gates. A failure means an implementation or adapter did not satisfy this experiment's contract on the tested inputs; it is not automatically evidence of an upstream defect. Incorrect outputs, timeouts, crashes and unsupported dimensions remain explicit in the results.

## Repository map

```text
run_theater.py                run all campaigns in a selected theater
theaters/<theater>/           theater README, membership and campaign definitions
  campaigns/<campaign>/      workload definition and README
config/                      shared execution policy and imported-workload catalog
src/
  morton/                    our four standalone algorithms
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
