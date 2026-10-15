# Static 3D theater

This theater lifts the synthetic 2D scaling and fixed-size designs to three-dimensional sphere reporting. It contains no geographical workloads.

| Campaign | Instances | Workload |
|---|---:|---|
| [input_scaling](campaigns/input_scaling/README.md) | 60 | Uniform points: n = 100k, 500k, 2m, 4m, 6m, 8m, 10m, 12m, 14m, 16m, 18m, 20m; five seeds. |
| [radius_scaling](campaigns/radius_scaling/README.md) | 35 | Four million uniform points; seven fixed radii; five seeds; 1,000 queries per instance. |
| [Static3D](campaigns/Static3D/README.md) | 100 | Four million points; all 20 distribution/centre/output combinations; five seeds. |

Each instance has 1,000 queries. The current roster contains Morton, Morton
(simd), Morton (plus), SPRK (original), SPRK (adapted), and three Boost variants.
Morton uses readable compiler-vectorized scans. SIMD and Plus use the validated
AVX-512 upgrades. See [implementation and timing evidence](../../docs/MORTON-3D-UPGRADE.md).
Input scaling and fixed-size suites calibrate output sizes; radius scaling uses
fixed radii. Nonuniform inputs have uniform and distribution-matched queries.
Completed older runs retain their original source versions and names.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs first, then run `python tools/build_ddim.py` for dimensional backends and `bash tools/build_selected_3d.sh` for the current Morton/SPRK selection. From the repository root, prepare missing inputs separately:

```sh
python tools/prepare_synthetic_ddim.py --campaign input_scaling_3d radius_scaling_3d Static3D
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

Publication labels and modification categories are specified in `tools/algorithm_labels.py`.
Prepare fresh manifests after changing a roster or implementation; never replace
completed results. The upgrade study uses sampled queries and does not replace
the full theatre (now 195 cases) or its existing PDF results.
