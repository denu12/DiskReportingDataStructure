# Experiment infrastructure

The public entry point is [`../run_theater.py`](../run_theater.py). The files here implement its build, preparation, execution and collection steps. They are not separate experiment theaters.

| Tools | Responsibility |
|---|---|
| `setup_arch.sh`, `build_arch.sh`, `build_ddim.py` | Install the Python/Rust environment and compile benchmark programs. No experiments are launched. |
| `prepare.py`, `prepare_synthetic_ddim.py` | Generate reproducible synthetic integer inputs. |
| `esa/fetch.py`, `esa/prepare.py`, `esa/catalog.py` | Download, convert and describe imported workload families. |
| `prepare_geography_large.py` | Prepare the large real-POI extension. |
| `campaign_paths.py`, `theaters.py` | Resolve definitions and describe theater membership. |
| `run.py`, `esa/run.py` | Execute individual campaign phases; preserve outcomes and enforce limits. |
| `budget.py`, `plan.py`, `worker.py` | Persistent budgets, synthetic final planning and the container process backend. |
| `collect.py` | Export completed phase rows for analysis. |

`workloads.py` holds current rosters and binary serialization helpers; `backends.py` resolves dimensional executables. Obsolete controllers, combined-campaign preparation tools and compatibility paths have been removed. Existing data are held privately in `historical_data/`; current tools do not read that folder implicitly.

See [running experiments](../docs/RUNNING.md) and the [protocol](../docs/EXPERIMENTS.md). Keep algorithm correctness fixes out of experiment-controller changes.
