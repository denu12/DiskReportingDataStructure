# Experiment theaters

A theater is the top-level experiment collection. Its `theater.json` lists campaign IDs; each campaign has a `campaign.json` and a README in `campaigns/<id>/` beneath that theater.

| Theater | Purpose | Instances |
|---|---|---:|
| [static](static/README.md) | Synthetic 2D and large real geographical workloads | 180 |
| [small](small/README.md) | Original native 2D imported workloads | 50 |
| [static-3d](static-3d/README.md) | Synthetic 3D workloads | 80 |
| [d-dim](d-dim/README.md) | Imported workloads above two dimensions | 279 |
| [dynamic](dynamic/README.md) | Updates and queries in 2D | 90 |

From the repository root, `python run_theater.py THEATER` previews the complete schedule. Add `--run FRESH_LABEL --execute` to run it. See the [execution guide](../docs/RUNNING.md) before launching measurements.

Current definitions contain only the active campaigns. New prepared inputs use `data/<campaign>/`, and new measurements use `results/<campaign>/<run>/<phase>/`. Existing datasets and measurements have been moved to the private, ignored `historical_data/` folder for correspondence and paper drafting; they are not an execution queue.
