# Static 3D theater

This theater lifts the synthetic 2D scaling and fixed-size designs to three-dimensional sphere reporting. It contains no geographical workloads.

| Campaign | Instances | Workload |
|---|---:|---|
| [Scaling3D](campaigns/Scaling3D/README.md) | 40 | Uniform points: n = 10k, 100k, 2m, 4m, 6m, 8m, 10m, 12m; five seeds. |
| [Static3D](campaigns/Static3D/README.md) | 40 | Four million points; distribution and target-output suites; five seeds. |

Each instance has 1,000 queries. Morton3D is the specialized standalone implementation. Compatible dimensional competitors are used; SPRK has coordinate-reporting and IDs-only diagnostic entries. The synthetic suites use calibrated output sizes and distinct query streams; nonuniform inputs have uniform and distribution-matched query variants. Generic Morton, geography and brute force are not selected by this theater.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs first, then run `python tools/build_ddim.py` for dimensional backends. From the repository root, prepare missing inputs separately:

```sh
python tools/prepare_synthetic_ddim.py --campaign Scaling3D Static3D
```

Preparation can download large datasets. Reuse validated existing inputs; do not replace data associated with previous measurements. Each definition and prepared manifest records the workload selection.

```sh
python run_theater.py static-3d
python run_theater.py static-3d --check
python run_theater.py static-3d --run paper-static-3d --execute
python run_theater.py static-3d --run paper-static-3d --status
python run_theater.py static-3d --run paper-static-3d --stop
```

The first command is a preview. Execution uses one worker on one core, fresh ordinary and boundary/duplicate correctness admission, screening and three final repetitions of eligible pairs. See the [protocol](../../docs/EXPERIMENTS.md) for exclusions, limits and timing. Historical IDs-only SPRK diagnostics must remain separate from coordinate-reporting comparisons; see the [reporting contract](../../docs/REPORTING.md).

Results remain under `results/<campaign>/<run>/<phase>/`. Controller progress and its recorded policy are under `results/_execution-<run>/`; shared elapsed budgets are under `results/_budgets/<run>.json`. Counts above are instances, not executed or successful jobs.

Publication labels and modification categories are specified in the [adapter catalog](../../docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
