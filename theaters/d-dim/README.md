# D-dimensional imported workloads theater

This theater contains the imported workload instances with dimension greater than two. Geography is excluded because it is entirely two-dimensional.

| Campaign | Instances | Workload |
|---|---:|---|
| [ESA_graph_embeddings](campaigns/ESA_graph_embeddings/README.md) | 210 | Dimensions 3â€“16. |
| [ESA_uniform_points](campaigns/ESA_uniform_points/README.md) | 14 | Dimensions 8 and 32. |
| [ESA_high_dimensional](campaigns/ESA_high_dimensional/README.md) | 30 | Dimensions 96, 100, 128, 784 and 960. |
| [ESA_clustering](campaigns/ESA_clustering/README.md) | 25 | Dimensions 4, 5, 7, 13 and 34. |

The default roster includes all external competitors, a scan control, dimensional
Morton and dimensional MortonPlus. Both Morton entries support dimensions 1-16;
specialized Morton3D belongs to the static-3d theater. Original SPRK supports
compiled dimensions 2-16 and 32; adapted SPRK is available only in dimension 3
here. Unsupported jobs are labelled, not treated as incorrect. See
[competitor rosters](../../docs/COMPETITORS.md).


## Protected time budgets

| Campaign | Screening | Final measurements |
|---|---:|---:|
| Graph embeddings | 12 hours | 12 hours |
| Uniform points | 4 hours | 4 hours |
| High-dimensional data | 4 hours | 4 hours |
| Clustering | 4 hours | 4 hours |

The theater has a 24-hour screening allocation and a 24-hour final allocation, for a 48-hour active-time ceiling. Each campaign has its own protected share; graph embeddings cannot spend the others' time. Existing usage stays charged to the campaign that consumed it. Whole-job caps remain 60 seconds for screening and 180 seconds for final measurements.

When a campaign exhausts screening, the controller proceeds to the next campaign. Successfully screened implementation/instance pairs still receive up to three final repetitions, even when screening coverage is incomplete. Finals stop at that campaign's own budget; unexecuted work remains explicitly unmeasured. A final estimate larger than its protected allocation does not block all measurements.

## Prepare and run

Use the [Arch setup guide](../../docs/RUNNING.md). Build the 2D programs first, then run `python tools/build_ddim.py` for dimensional backends. From the repository root, prepare missing inputs separately:

```sh
python tools/esa/fetch.py --families graph_embeddings uniform_points high_dimensional clustering
python tools/esa/prepare.py --campaign ESA_graph_embeddings ESA_uniform_points ESA_high_dimensional ESA_clustering
```

Preparation can download large datasets. Reuse validated existing inputs; do not replace data associated with previous measurements. Each definition and prepared manifest records the workload selection.

```sh
python run_theater.py d-dim
python run_theater.py d-dim --check
python run_theater.py d-dim --run paper-d-dim --execute
python run_theater.py d-dim --run paper-d-dim --status
python run_theater.py d-dim --run paper-d-dim --stop
```

The first command is a preview. Execution uses one worker on one core, fresh ordinary and boundary/duplicate correctness admission, screening and three final repetitions of eligible pairs. See the [protocol](../../docs/EXPERIMENTS.md) for exclusions, limits and timing. Historical IDs-only SPRK diagnostics must remain separate from coordinate-reporting comparisons; see the [reporting contract](../../docs/REPORTING.md).

Results remain under `results/<campaign>/<run>/<phase>/`. Controller progress and its recorded policy are under `results/_execution-<run>/`; shared elapsed budgets are under `results/_budgets/<run>.json`. Counts above are instances, not executed or successful jobs.

Publication labels and modification categories are specified in the [adapter catalog](../../docs/ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
