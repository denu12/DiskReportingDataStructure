# DiskRangeReport

This repository contains the experiments for our work on reporting nearby points using space-filling curves.

The problem is simple: **given a set of points and a circle, return every point inside or on the circle.** If the input contains the same point more than once, each occurrence must be returned. We compare our implementations with other spatial data structures, measuring how long they take to build, answer queries, and handle updates.

The experiments run on **Arch Linux, on an x86-64 CPU with AVX2 and BMI2 support**. You can build directly on Arch or use the supplied Docker image. All algorithms run on one CPU core each; several independent experiments can run at the same time.

## What experiments are included?

We call a collection of related experiments a **campaign**. There are three:

| Campaign | What it investigates | Implementations included |
|---|---|---|
| `static-circles` | Querying a fixed point set: vary the number of points, their distribution, and the circle radius. | 29 static entries |
| `dynamic-circles` | Querying points while inserting and deleting them, with different amounts and orders of updates. | 12 dynamic entries |
| `esa2026-2d` | Running our comparison on the two-dimensional datasets used in the ESA 2026 study. | All 41 entries |

These counts include seven of our variants. Some entries are different configurations of the same data structure, rather than separate algorithms. The [competitor list](third_party/README.md) explains which implementation each entry uses and credits its source.

Within a campaign, a **suite** groups related workloads, such as increasing dataset sizes. A **case** fixes one dataset and its query parameters. We then **run** each implementation on that case, repeating measurements where required.

## How the comparison works

Every campaign follows the same steps:

1. **Check correctness.** Compare each implementation's complete answers with a simple scan of the points. An implementation that gives incorrect answers or fails a required input is excluded from later measurements. We keep its failure record; we do not repair competitors to make them pass.
2. **Screen.** Run each eligible implementation on the workloads with a short time limit. Record successes, failures and timeouts.
3. **Measure.** Repeat the successful implementation/workload pairs three times.
4. **Collect.** Export the recorded results as a CSV table.

You start each step explicitly. Preparing data or building the code does not start any experiments.

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
# Fixed point sets.
python tools/prepare.py --campaign static-circles

# Point sets with insertions and deletions.
python tools/prepare.py --campaign dynamic-circles

# Download and prepare the ESA two-dimensional datasets.
python tools/import_data.py --dest data/esa2026-2d/data
python tools/prepare_esa.py
```

For a small trial, add `--smoke` to either synthetic preparation command. This produces small workloads, labelled as a trial in the generated description. To switch from trial data to full data, first move the existing `data/<campaign>/` directory aside; preparation will not overwrite it.

### 2. Check, screen and measure

For example, to run the static campaign:

```sh
python tools/run.py correctness --campaign static-circles --run paper
python tools/run.py screen      --campaign static-circles --run paper
python tools/plan.py --run paper --campaigns static-circles
python tools/run.py final       --campaign static-circles --run paper
```

Replace `static-circles` with another campaign name to run that campaign. Here, `paper` is simply a label for this set of results. Keep the same label through all stages and campaigns in one experiment cycle: this also shares their time budgets. Choose a new label only for a genuinely new cycle. Existing results are not overwritten.

The runner refuses to use old correctness results after the inputs, programs or execution settings change. You must check correctness again for the new setup.

After screening all three campaigns, use `python tools/plan.py --run paper` without `--campaigns` to estimate their combined final runtime. The planner uses screening times, three repetitions and a 25% margin. Final measurements require a plan that fits the remaining 24-hour budget. If it does not fit, supply `--matrix selection.json` to select fewer cases consistently for every algorithm. See the [planning instructions](docs/EXPERIMENTS.md). The estimate is not a promise; the time budget remains a hard limit.

### 3. Export the results

```sh
python tools/collect.py results/static-circles/paper/final/state.json > results/static-circles/paper/final.csv
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
python tools/run.py stop --campaign static-circles --run paper
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
  disk-range-report:arch tools/prepare.py --campaign static-circles --smoke
```

Check its correctness:

```sh
docker run --rm --user "$(id -u):$(id -g)" \
  --cpuset-cpus=1-4 --memory=72g --memory-swap=72g \
  -v "$PWD/data:/opt/disk-range-report/data" \
  -v "$PWD/results:/opt/disk-range-report/results" \
  disk-range-report:arch correctness --campaign static-circles --run container
```

Once that finishes, run `screen`, then create a plan with the same image and results mount (`--entrypoint python`, command `tools/plan.py --run container --campaigns static-circles`). Finally run `final`. Remove `--smoke` from the preparation command when preparing full workloads in a fresh data directory. The other campaigns use the same preparation scripts and stage commands described above.

With rootless Podman, add `--userns=keep-id` so the container can write to your mounted directories. If Podman cannot apply `--cpuset-cpus`, omit that option; the experiment runner still sets each worker's CPU affinity.

Container and native memory limits work differently: the container limits each worker's address space, while native execution limits its memory through systemd. Keep their results separately labelled. See the [experimental protocol](docs/EXPERIMENTS.md) before comparing measurements across environments.

## Important details when interpreting results

Our implementations check circle membership during their search. Competitors that only support rectangular queries first report points in a surrounding rectangle, then discard those outside the circle. That extra work is included in their query time.

The ESA datasets originally use floating-point coordinates. We convert them to one common integer grid for every implementation. This can change which points fall exactly on a query boundary, so these experiments are an adapted comparison, not an exact reproduction of the paper's original measurements. In this campaign, dynamic structures insert the dataset and then answer queries; the separate dynamic campaign exercises ongoing insertions and deletions. See the [ESA campaign notes](campaigns/esa2026-2d/README.md).

Some competitors have been adapted to fit the comparison. In particular, `chan_sss_dyn_ADAPTED_DYNAMIC` is our local dynamic adaptation of Chan's technique. The [credits and modification notes](third_party/README.md) distinguish adaptations from upstream implementations.

## Where to find things

| Directory | Contents |
|---|---|
| `src/` | Algorithms, comparison adapters and build configuration. External implementations used by the build are in `src/third_party/`. |
| `campaigns/` | Definitions of the three campaigns and their workloads. |
| `tools/` | Commands for building, preparing data, running experiments and collecting results. |
| `correctness/` | Explanation of how answers are checked. |
| `docs/` | Experimental protocol, data formats and validation summary. |
| `third_party/` | Credits, licenses and source provenance. |
| `data/`, `results/`, `bin/`, `build/` | Generated data, results and compiled programs; these are not committed to Git. |

For reproducibility, retain the generated input descriptions, raw results and `results/build/` metadata. Container runs should also record the image ID and its build metadata. The build specifies Bazel 8.1.0, Rust 1.99.0 and fixed Python dependency versions; Arch's system packages may change over time.

The project code is covered by [LICENSE](LICENSE). External libraries retain their own licenses and copyright notices.
