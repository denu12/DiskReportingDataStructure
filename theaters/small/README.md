# Small: native 2D imported workloads theater

This theater uses only the originally two-dimensional instances from the paper cited in the [root README](../../README.md). No higher-dimensional dataset is projected into two dimensions.

| Campaign | Instances | Workload |
|---|---:|---|
| [2D_ESA_graph_embeddings](campaigns/2D_ESA_graph_embeddings/README.md) | 15 | Graph vertices embedded in two dimensions. |
| [2D_ESA_uniform_points](campaigns/2D_ESA_uniform_points/README.md) | 7 | Uniform datasets, n = 10k through 10 million. |
| [2D_ESA_geographical](campaigns/2D_ESA_geographical/README.md) | 28 | Seven original POI/query pairs, each at four radii. |

These 50 instances use their complete original query lists and the common integer-grid conversion. Input size varies by dataset; small is a theater name, not a size guarantee. Use GeographyLarge in the static theater for the 1–5 million POI extension.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs with `bash tools/build_arch.sh`. From the repository root, prepare missing inputs separately:

```sh
python tools/esa/fetch.py --families graph_embeddings uniform_points geographical
python tools/esa/prepare.py --campaign 2D_ESA_graph_embeddings 2D_ESA_uniform_points 2D_ESA_geographical
```

Preparation can download large datasets. Reuse validated existing inputs; do not replace data associated with previous measurements. Each definition and prepared manifest records the workload selection.

```sh
python run_theater.py small
python run_theater.py small --check
python run_theater.py small --run paper-small --execute
python run_theater.py small --run paper-small --status
python run_theater.py small --run paper-small --stop
```

The first command is a preview. Execution uses one worker on one core, fresh ordinary-workload correctness admission, screening and three final repetitions of eligible pairs. See the [protocol](../../docs/EXPERIMENTS.md) for exclusions, limits and timing. Historical IDs-only SPRK diagnostics must remain separate from coordinate-reporting comparisons; see the [reporting contract](../../docs/REPORTING.md).

Results remain under `results/<campaign>/<run>/<phase>/`. Controller progress and its recorded policy are under `results/_execution-<run>/`; shared elapsed budgets are under `results/_budgets/<run>.json`. Counts above are instances, not executed or successful jobs.

Publication labels and modification categories are specified in the [adapter catalog](../../docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
