# Build, prepare and run on Arch Linux

Run commands from the repository root. Building and preparation do not launch measurements. Start with `python run_theater.py` to list theaters and read the chosen theater's README before downloading data.

## Build

```sh
sudo pacman -Syu --needed base-devel git python python-pip rustup clang cmake ninja pkgconf openssl curl wget unzip zip bazelisk
bash tools/setup_arch.sh
source .venv/bin/activate
BAZEL=bazelisk bash tools/build_arch.sh
```

The setup script creates `.venv` and installs the pinned Python requirements and Rust toolchain. The 2D build produces `bin/esa2d/esa_runner`, `esa_runner_pargeo` and `libsfc_esa2026.so`, and records toolchain information under `results/build/`. Compilation targets the build machine's CPU; do not assume binaries are portable to older processors. Scalar Morton requires BMI2; dimensional SIMD Morton requires AVX2.

For `d-dim` or `static-3d`, also run:

```sh
python tools/build_ddim.py
```

This builds dimensional C++, Rust and Python-facing adapters. The 2D build must have fetched the external headers first. Python-backed competitors need the active scientific environment. Retain the generated build logs if a backend is unavailable; preflight refuses missing programs.

## Prepare inputs

| Theater | Preparation instructions |
|---|---|
| static | [Synthetic scaling, fixed-size and GeographyLarge](../theaters/static/README.md) |
| small | [The three native 2D imported families](../theaters/small/README.md) |
| static-3d | [Synthetic 3D generation](../theaters/static-3d/README.md) |
| d-dim | [Imported families above two dimensions](../theaters/d-dim/README.md) |
| dynamic | [Dynamic 2D generation](../theaters/dynamic/README.md) |

Existing datasets and measurements are stored privately in `historical_data/` and are not read by the runners. Prepare fresh inputs for a new experiment cycle. Preparation creates `data/<campaign>/campaign.json`, checksums and binary inputs. Downloads and generated data can be large. GeographyLarge uses the upstream POI extractor and a frozen Europe extract, pools categories and samples real points; it does not replicate a small dataset to inflate n. It contains exactly 1,000 queries per instance. Its broad geographic projection is an extension of the upstream method, not an original paper workload.

Do not overwrite inputs used by existing results. Keep the whole referenced data layout: manifests can refer to sibling directories. A `--smoke` preparation is a small format check and cannot be used as a full theater measurement. Rebuilding a manifest from changed definitions creates a new experiment identity.

## One command per theater

```sh
python run_theater.py small                       # read-only schedule preview
python run_theater.py small --check               # hash inputs and check backend files
python run_theater.py small --run paper-small --cpu 1 --execute
```

Replace `small` with `static`, `static-3d`, `d-dim` or `dynamic`. The default roster comes from prepared campaign manifests, filtered by the disabled-algorithm policy. An explicit `--algorithms ID ...` applies to every campaign in the theater and is recorded in the run identity. For example, use `--algorithms morton_d_dim` for the supported dimensional Morton-only study.

Execution is serial, with one single-threaded benchmark job at a time. Use `lscpu -e=CPU,CORE,SOCKET` to choose a suitable CPU. Keep this machine free of other benchmark jobs. Correctness, screening and final measurements run in that order across the theater; final repetition count is three. The policy and budget details are in the [protocol](EXPERIMENTS.md).

The command stays in the foreground. For a long remote run, use a persistent terminal such as tmux, or launch the command in a deliberately named user service. Do not create an additional scheduler or restart a stopped experiment implicitly.

```sh
python run_theater.py small --run paper-small --status
python run_theater.py small --run paper-small --stop
```

Status prints the controller record, not a fabricated count of successful jobs. Inspect the campaign phase states and raw logs for outcomes. On failure, preserve the result directory, resolve the preparation/environment problem, then choose a fresh run label. The public runner does not resume or overwrite partial runs.

## Docker

The Dockerfile builds the 2D benchmark programs in an Arch Linux base image:

```sh
docker build -t disk-range-report:arch .
docker run --rm disk-range-report:arch --help
```

The default entry point is `python run_theater.py`; listing and previews do not start experiments. The imported and dimensional harnesses need native user systemd, so full static, small and dimensional theaters are not supported by the container's process backend. The synthetic-only dynamic theater can use that backend after preparation, with CPU affinity and an outer container memory/swap cap. Those limits have different semantics from native cgroups and must be labelled separately.

Use `--entrypoint python` for preparation helpers, and mount writable `data/` and `results/` directories owned by the container user. The low-level `tools/run.py` interface remains available for individual synthetic campaigns. Docker is a build/environment option, not a claim of identical results across machines.
