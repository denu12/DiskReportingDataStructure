# DiskRangeReport

This repository contains the experiments for our work on reporting nearby points using space-filling curves.

The problem is simple: **given a set of points and a circle, return every point inside or on the circle.** If the input contains the same point more than once, each occurrence must be returned. We compare our implementations with other spatial data structures, measuring how long they take to build, answer queries, and handle updates.

The experiments run on **Arch Linux, on an x86-64 CPU with AVX2 and BMI2 support**. You can build directly on Arch or use the supplied Docker image. All algorithms run on one CPU core each; several independent experiments can run at the same time.

## What experiments are included?

The [d-dimensional adapters](d-dim/README.md) retain the agreed external competitors. Their [ESA correctness campaign](campaigns/esa2026-ddim/README.md) has 20 entries, including the brute-force control and explicitly labelled Chan/STANN adaptations. Our published algorithms are the three static 2D Morton implementations listed below.

We call a collection of related experiments a **campaign**. Our synthetic workloads are:

| Campaign | What varies | Cases | Competitor entries |
|---|---|---:|---:|
| `scaling` | Point count: 10,000 to 10,000,000 | 20 | 29 static |
| `static` | Distribution and query radius, fixed at 1,000,000 points | 30 | 29 static |
| `dynamic-circles` | Updates and queries | 90 | 9 dynamic |

Case counts include five seeds. `static` contains 15 distribution cases and 15 selectivity cases. The former combined `static-circles` inputs and results are retained for historical runs.

The ESA workload suite is split into five full campaigns and three native-2D companions:

| Full ESA campaign | Cases | Dimensions | 2D companion cases |
|---|---:|---|---:|
| `ESA_graph_embeddings` | 225 | 2–16 | 15 |
| `ESA_uniform_points` | 21 | 2, 8, 32 | 7 |
| `ESA_high_dimensional` | 30 | 96, 100, 128, 784, 960 | None |
| `ESA_clustering` | 25 | 4, 5, 7, 13, 34 | None |
| `ESA_geographical` | 28 | 2 | 28 |

Companions use the prefix `2D_ESA_`, followed by the same family name. They retain only native 2D instances, with no projection. There are no empty companion campaigns. The five full campaigns use the 20-entry dimensional roster; the three 2D companions use all 29 static entries. Unsupported adapter dimensions are recorded explicitly.

See the [ESA campaign guide](campaigns/ESA.md) for the exact source selections, downloads, preparation and execution commands. The 329 source workloads reproduce the artifact's dataset/query/radius matrix under our agreed integer conversion and explicit point-output contract. They do not claim to reproduce its floating-point timings. Campaign definitions and downloaded/prepared data have separate readiness states.

The old combined `esa2026-2d` campaign and the small dimensional correctness campaign are retained for historical runs.

These counts include our three static 2D variants. Dynamic and d-dimensional campaigns contain external competitors and reference controls only. Some entries are different configurations of the same data structure, rather than separate algorithms. The [competitor list](third_party/README.md) explains which implementation each entry uses and credits its source.

Our three active static 2D algorithms each live in one source file under `src/app/algorithms/sfc`:

| Algorithm | Search and reporting | Early termination |
|---|---|---|
| `Morton` | Scalar; compiler auto-vectorization disabled | No |
| `MortonSIMD` | Original SIMD rank index and exact SIMD circle reporting | No |
| `MoronSIMDearly` | Same SIMD search and reporting | Original 24-level occupancy oracle |

Each file contains its own Morton encoding, index, query and reporting code. Shared headers provide only benchmark integration, point/query types and third-party facilities. Every matching point is explicitly output. The scalar PDEP instruction used for Morton encoding is not SIMD. Our older static, dynamic and d-dimensional Morton implementations are excluded from this publication tree. Retired research snapshots are kept outside the repository; historical results keep their original names. See [SIMD reporting](docs/SIMD-reporting.md).

Hilbert implementations are excluded from this publication tree and future campaigns.

Within a campaign, a **suite** groups related workloads, such as increasing dataset sizes. A **case** fixes one dataset and its query parameters. We then **run** each implementation on that case, repeating measurements where required.

## How the comparison works

Every campaign follows the same steps:

1. **Check correctness.** Compare complete answers on ordinary workloads with a simple scan. Synthetic boundary and duplicate findings are informational, not exclusion grounds. Failures on ordinary workloads still affect admission. See the [admission policy](docs/correctness-admission.md). We retain findings and do not repair competitors to make them pass.
2. **Screen.** Run each eligible implementation on the workloads with a short time limit. Record successes, failures and timeouts.
3. **Measure.** Repeat the successful implementation/workload pairs three times.
4. **Collect.** Export the recorded results as a CSV table.

Preparing data or building the code does not start experiments. The new ESA runner executes correctness, screening and final measurement only when explicitly invoked; `--phase` can select one stage.

## Build on Arch Linux

Run these commands from the repository's top-level directory:

```sh
sudo pacman -Syu --needed base-devel git python python-pip rustup clang cmake ninja pkgconf openssl curl wget unzip zip bazelisk
bash tools/setup_arch.sh
source .venv/bin/activate
BAZEL=bazelisk bash tools/build_arch.sh
```

The setup script installs the Python dependencies and Rust toolchain. The build script compiles the experiment programs and puts them in `bin/`. Build on the machine you intend to measure: the compiler uses that machine's CPU features.

In a new terminal, run `source .venv/bin/activate` before using the Python commands below. Native execution also needs a working user systemd session to enforce the resource limits.

## Run a campaign

### 1. Prepare its data

Choose the campaign you want to run:

```sh
# Increasing point counts.
python tools/prepare.py --campaign scaling

# Fixed-size point sets: distributions and selectivity.
python tools/prepare.py --campaign static

# Point sets with insertions and deletions.
python tools/prepare.py --campaign dynamic-circles

# Download and prepare the ESA two-dimensional datasets.
python tools/import_data.py --dest data/esa2026-2d/data
python tools/prepare_esa.py
```

For a small trial, add `--smoke` to any synthetic preparation command. This produces small workloads, labelled as a trial in the generated description. To switch from trial data to full data, first move the existing `data/<campaign>/` directory aside; preparation will not overwrite it.

### 2. Check, screen and measure

For example, to run the static campaign:

```sh
python tools/run.py correctness --campaign static --run paper
python tools/run.py screen      --campaign static --run paper
python tools/plan.py --run paper --campaigns static
python tools/run.py final       --campaign static --run paper
```

This command family accepts `scaling`, `static`, `dynamic-circles`, and the historical `static-circles` and `esa2026-2d`. Use the same stage commands with `--campaign scaling` for the scaling workloads. Use `tools/esa/run.py` for the eight new ESA campaigns, as described in the [ESA guide](campaigns/ESA.md). Here, `paper` is simply a label for this set of results. Keep the same label through all stages and campaigns in one experiment cycle: this also shares their time budgets. Choose a new label only for a genuinely new cycle. Existing results are not overwritten.

The runner refuses to use old correctness results after the inputs, programs or execution settings change. You must check correctness again for the new setup.

After screening both synthetic static campaigns, use `python tools/plan.py --run paper --campaigns scaling static` to estimate their combined final runtime. Add `dynamic-circles` if it is part of the same experiment cycle. Without `--campaigns`, the planner includes `scaling`, `static`, `dynamic-circles` and the historical `esa2026-2d`, all of which must have screening results. The planner uses screening times, three repetitions and a 25% margin. Final measurements require a plan that fits the remaining 24-hour budget. If it does not fit, supply `--matrix selection.json` to select fewer cases consistently for every algorithm. See the [planning instructions](docs/EXPERIMENTS.md). The estimate is not a promise; the time budget remains a hard limit.

### 3. Export the results

```sh
python tools/collect.py results/static/paper/final/state.json > results/static/paper/final.csv
```

The `results/` directory also contains individual job results and logs. Failed and timed-out jobs remain visible; they are not assigned invented running times.

### Limits and stopping

Each algorithm runs on one core. Up to four independent jobs run at once, each with 16 GiB of memory. Native execution also caps their combined memory at 72 GiB and disables swap.

| Stage | Limit per whole job | Jobs at once | Shared budget across all campaigns |
|---|---:|---:|---:|
| Correctness | 60 seconds | 4 | 30 minutes |
| Screening | 60 seconds | 4 | 8 hours |
| Final measurements | 180 seconds | 4 | 24 hours |
| Selected timeout follow-ups | 300 seconds | 1 | 2 hours, shared with contention checks |
| Selected contention checks | 180 seconds | 1 | Same 2-hour allowance |

This allows up to 34.5 hours of active experiment time, leaving some room in a roughly 36-hour measurement cycle. Budgets persist across commands with the same `--run` label; switching campaigns does not reset them. Pauses between commands are not charged. Only one controller runs at a time in a repository, so simultaneous commands cannot multiply the worker count.

A screening timeout excludes that algorithm/workload pair, not the algorithm from every other workload. Follow-ups must name the algorithms and cases explicitly. Contention checks repeat selected successful final cases one job at a time, to see whether concurrent jobs affected the measurements. Their results stay separate from the main measurements.
The default CPU IDs are 1, 2, 3 and 4. Check your machine with `lscpu -e=CPU,CORE,SOCKET` and choose one logical CPU from each physical core. If necessary, supply your selection with `--cpus`, using the same selection for all stages. These defaults assume a machine with enough cores and memory; see the [experimental protocol](docs/EXPERIMENTS.md) for details.

To stop a running campaign:

```sh
python tools/run.py stop --campaign static --run paper
```

This stops its workers and prevents another stage from starting accidentally. A later command with `--resume` clears that stop request; it does not continue or overwrite an already recorded stage.

## Run with Docker instead

The Dockerfile builds the programs inside an Arch Linux image. You still keep the input data and results in directories on your host machine.

First build the image:

```sh
docker build -t disk-range-report:arch .
mkdir -p data results
```

Then prepare a small static trial:

```sh
docker run --rm --user "$(id -u):$(id -g)" --entrypoint python \
  -v "$PWD/data:/opt/disk-range-report/data" \
  disk-range-report:arch tools/prepare.py --campaign static --smoke
```

Check its correctness:

```sh
docker run --rm --user "$(id -u):$(id -g)" \
  --cpuset-cpus=1-4 --memory=72g --memory-swap=72g \
  -v "$PWD/data:/opt/disk-range-report/data" \
  -v "$PWD/results:/opt/disk-range-report/results" \
  disk-range-report:arch correctness --campaign static --run container
```

Once that finishes, run `screen`, then create a plan with the same image and results mount (`--entrypoint python`, command `tools/plan.py --run container --campaigns static`). Finally run `final`. Remove `--smoke` from the preparation command when preparing full workloads in a fresh data directory. The other campaigns use the same preparation scripts and stage commands described above.

With rootless Podman, add `--userns=keep-id` so the container can write to your mounted directories. If Podman cannot apply `--cpuset-cpus`, omit that option; the experiment runner still sets each worker's CPU affinity.

Container and native memory limits work differently: the container limits each worker's address space, while native execution limits its memory through systemd. Keep their results separately labelled. See the [experimental protocol](docs/EXPERIMENTS.md) before comparing measurements across environments.

## Important details when interpreting results

Our implementations check circle membership during their search. Competitors that only support rectangular queries first report points in a surrounding rectangle, then discard those outside the circle. That extra work is included in their query time.

Every timed query explicitly writes the reported points' integer coordinates into an output vector. Counts, IDs alone, and references to unexpanded ranges are not accepted as final output. Internal ID lookup, coordinate materialization, and any required circle filtering are timed. Buffer capacity may be reused. Adapters that already apply the exact circle predicate are not filtered a second time. The ESA bridge uses its internal ID buffer to enumerate coordinates directly into the caller's result vector.

The ESA datasets originally use floating-point coordinates. We convert them to one common integer grid for every implementation. This can change which points fall exactly on a query boundary, so these experiments are an adapted comparison, not an exact reproduction of the paper's original measurements. The ESA campaign compares static implementations only. Insertions and deletions are evaluated in the separate dynamic campaign. See the [ESA campaign notes](campaigns/esa2026-2d/README.md).

Some competitors have been adapted to fit the comparison. In particular, `chan_sss_dyn_ADAPTED_DYNAMIC` is our local dynamic adaptation of Chan's technique. The [credits and modification notes](third_party/README.md) distinguish adaptations from upstream implementations.

## Where to find things

| Directory | Contents |
|---|---|
| `src/` | Algorithms, comparison adapters and build configuration. External implementations used by the build are in `src/third_party/`. |
| `campaigns/` | Definitions of the synthetic, ESA and dimensional campaigns and their workloads. |
| `tools/` | Commands for building, preparing data, running experiments and collecting results. |
| `correctness/` | Explanation of how answers are checked. |
| `docs/` | Experimental protocol, data formats and validation summary. |
| `third_party/` | Credits, licenses and source provenance. |
| `data/`, `results/`, `bin/`, `build/` | Generated data, results and compiled programs; these are not committed to Git. |

For reproducibility, retain the generated input descriptions, raw results and `results/build/` metadata. Container runs should also record the image ID and its build metadata. The build specifies Bazel 8.1.0, Rust 1.99.0 and fixed Python dependency versions; Arch's system packages may change over time.

The project code is covered by [LICENSE](LICENSE). External libraries retain their own licenses and copyright notices.

Static reporting adapters enumerate integer coordinates inside the timed query.
Except for CGAL, rectangle-only APIs filter candidates as they are emitted, avoiding an extra
output-and-erase pass. ANN uses its native Euclidean fixed-radius search;
VP-tree uses its public radius visitor. Python adapters reuse their query arrays.
The static 2D Grid receives the mean query radius before construction as workload
metadata. Boost combines its native rectangle query with an exact circle predicate before output; its R-tree is unchanged. CGAL retains its original reporting path. Native API costs such as
ANN's count/report traversals and immutable Kiddo's result vector remain timed.
Measurements from before this revision must be rerun before comparison with it.
