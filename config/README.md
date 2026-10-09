# Shared experiment configuration

Campaign definitions live only in `theaters/<theater>/campaigns/<campaign>/`.
This directory holds active configuration shared across theaters:

- `execution.json`: timeouts, memory caps, repetitions and phase budgets.
- `disabled-algorithms.json`: explicit execution exclusions.
- `esa-workloads.json`: imported ESA workload catalog, used for preparation and selection.

The catalog supports the theater-local definitions; it is not an additional
campaign directory. `run_theater.py` records the execution policy for each run.
See [workload provenance](../docs/ESA-WORKLOADS.md) and
[theater membership](../theaters/README.md).
