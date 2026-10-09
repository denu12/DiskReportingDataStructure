# Dynamic 2D theater

This theater measures insertions, deletions and disk queries on changing sets of integer points. Construction, updates and queries are recorded separately.

| Campaign | Instances | Workload |
|---|---:|---|
| [dynamic-circles](campaigns/dynamic-circles/README.md) | 90 | 45 phased and 45 interleaved workloads; n = 10k, 100k and 1m; update fractions 0.1, 0.5 and 0.9; five seeds. |

Every instance has 10,000 operations. Phased workloads perform updates before queries; interleaved workloads mix them. Deletion removes one occurrence. The current publication roster contains nine external dynamic configurations. The standalone Morton files are static indexes and are not dynamic competitors.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs with `bash tools/build_arch.sh`. From the repository root, prepare missing inputs separately:

```sh
python tools/prepare.py --campaign dynamic-circles
```

Preparation can download large datasets. Reuse validated existing inputs; do not replace data associated with previous measurements. Each definition and prepared manifest records the workload selection.

```sh
python run_theater.py dynamic
python run_theater.py dynamic --check
python run_theater.py dynamic --run paper-dynamic --execute
python run_theater.py dynamic --run paper-dynamic --status
python run_theater.py dynamic --run paper-dynamic --stop
```

The first command is a preview. Execution uses one worker on one core, fresh ordinary and boundary/duplicate correctness admission, screening and three final repetitions of eligible pairs. See the [protocol](../../docs/EXPERIMENTS.md) for exclusions, limits and timing. Historical IDs-only SPRK diagnostics must remain separate from coordinate-reporting comparisons; see the [reporting contract](../../docs/REPORTING.md).

Results remain under `results/<campaign>/<run>/<phase>/`. Controller progress and its recorded policy are under `results/_execution-<run>/`; shared elapsed budgets are under `results/_budgets/<run>.json`. Counts above are instances, not executed or successful jobs.

Publication labels and modification categories are specified in the [adapter catalog](../../docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
