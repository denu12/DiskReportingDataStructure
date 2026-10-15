# Static 2D theater

This theater compares disk reporting as the number of points, spatial distribution and radius change. It also includes a separate large real-world geographical extension.

| Campaign | Instances | Workload |
|---|---:|---|
| [input_scaling](campaigns/input_scaling/README.md) | 60 | Uniform points: n = 100k, 500k, 2m, 4m, 6m, 8m, 10m, 12m, 14m, 16m, 18m, 20m; five seeds; nominal 1,000 answers per query. |
| [radius_scaling](campaigns/radius_scaling/README.md) | 35 | Four million uniform points; seven fixed radii; five seeds; 1,000 queries per instance. |
| [static](campaigns/static/README.md) | 100 | Four million points; all 20 distribution/centre/output combinations; five seeds. |
| [GeographyLarge](campaigns/GeographyLarge/README.md) | 100 | Real pooled European POIs; n = 1â€“5 million, five seeds, four radii. |

Every instance has 1,000 queries. Nonuniform fixed-size suites separate uniform and distribution-matched query centers. Input scaling and fixed-size suites calibrate radii by target output size; radius scaling uses fixed radii and paired points and query centers. Query streams differ between suites. GeographyLarge extends the source methodology and is not one of the original paper datasets.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs with `bash tools/build_arch.sh`. From the repository root, prepare missing inputs separately:

```sh
python tools/prepare.py --campaign input_scaling
python tools/prepare.py --campaign radius_scaling
python tools/prepare.py --campaign static
python tools/prepare_geography_large.py
```

Preparation can download large datasets. Reuse validated existing inputs; do not replace data associated with previous measurements. Each definition and prepared manifest records the workload selection.

```sh
python run_theater.py static
python run_theater.py static --check
python run_theater.py static --run paper-static --execute
python run_theater.py static --run paper-static --status
python run_theater.py static --run paper-static --stop
```

The first command is a preview. Execution uses one worker on one core, fresh ordinary and boundary/duplicate correctness admission, screening and three final repetitions of eligible pairs. See the [protocol](../../docs/EXPERIMENTS.md) for exclusions, limits and timing. Historical IDs-only SPRK diagnostics must remain separate from coordinate-reporting comparisons; see the [reporting contract](../../docs/REPORTING.md).

Results remain under `results/<campaign>/<run>/<phase>/`. Controller progress and its recorded policy are under `results/_execution-<run>/`; shared elapsed budgets are under `results/_budgets/<run>.json`. Counts above are instances, not executed or successful jobs.

Publication labels and modification categories are specified in the [adapter catalog](../../docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
