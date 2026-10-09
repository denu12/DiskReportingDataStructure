# Experimental protocol

The public orchestration command is `python run_theater.py THEATER --run LABEL --execute`. It runs correctness across the theater, then screening across the theater, then final measurements. Data preparation and compilation are separate. Use a fresh run label; historical results are never overwritten or automatically resumed.

## Inputs and admission

Definitions live in `theaters/<theater>/campaigns/<campaign>/campaign.json`. Existing data and results are held separately in the private `historical_data/` folder. New prepared manifests live in `data/<campaign>/campaign.json` and identify the actual input files and their hashes. Paths may refer to a shared sibling input directory. Preflight resolves and checks those paths rather than assuming all data live in the campaign's own folder. Smoke inputs and stale definitions are rejected by the theater entry point.

All coordinates use the agreed uint32 grid. Imported floating-point geometry is converted as described in the [workload guide](ESA-WORKLOADS.md). Synthetic radii are calibrated to nominal output sizes: 1,000 for scaling/distribution suites, and 1, 100 or 10,000 for selectivity. For each instance, 16 independent pilot query centers determine the median kth-neighbor squared distance. Rare targets use all points; larger targets use at most 262,144 deterministically sampled points. This is approximate workload calibration, not advance answer counts supplied to competitors. The manifest records the target, sample size and resulting integer squared radius. Actual answer counts remain measured outcomes. Uniform data use uniform query centers; normal and skew data have separate uniform and distribution-matched query instances. Query streams differ between suites, so no workload is duplicated. Seeds specify separate instances; final repetitions reuse those instances.

Admission uses the smallest ordinary workload per suite for synthetic campaigns and per dimension for imported/dimensional campaigns. The latter retain all indexed points and up to 32 original queries. Boundary, zero-radius, grid-edge and duplicate fixtures are additional mandatory admission gates, including for Morton. The independent oracle checks the coordinate multiset on the exercised workload. Incorrect answers exclude entries; infrastructure errors block execution. Failures are reported against our contract, without attributing adapter failures to upstream algorithms. Every phase also compares successful answer counts for identical cases/query counts across algorithms, repetitions and earlier phases. A disagreement marks all implicated current rows and blocks progression; it does not guess which algorithm is correct. Equal totals alone are not proof of equal point multisets.

## Timing and selection

Construction includes index building, representation conversion and persistent reporting workspace. Runtime loading and Python interpreter/import startup happen before the construction timer; they still count towards whole-job limits. Both C++ build paths use release optimization with NDEBUG. Query and update timing includes work performed by their adapters. Conforming queries materialize coordinates inside timing; the [IDs-only diagnostic](REPORTING.md) is explicitly different. Input loading and correctness verification are outside algorithm timings but can consume the whole-job timeout. Static performance runs time the complete query loop, including query geometry, clearing reusable buffers and output writes. Admission keeps per-query timing to exclude its oracle; admission timings are not performance results. Dynamic operations retain individual query/update clocks to separate their costs. Dynamic construction currently performs individual inserts, including for batch-oriented Pkd; this measures the single-update regime, not optimal bulk construction.

Screening runs eligible pairs once. Final measurements repeat successful screened pairs three times. Unsupported dimensions, disabled entries, correctness exclusions and pairs not selected after screening are not executed jobs. Crashes, memory failures, timeouts and interrupted jobs retain their statuses; missing times are not imputed.

The synthetic planner uses observed whole-job screen times, three repetitions and a 25% margin. Imported campaigns check their final estimate internally. A stage refuses work that exceeds the remaining shared budget. An estimate is not a guarantee; serial execution can exhaust a budget even when a previous parallel run fit it.

## Execution policy

| Stage | Whole-job cap | Shared active wall-time budget |
|---|---:|---:|
| Correctness | 60 seconds | 30 minutes |
| Screening | 60 seconds | 8 hours |
| Final | 180 seconds | 24 hours |

The top-level runner uses **one worker, one core and 64 GiB per job**. CPU 1 is the default; use `--cpu` to choose an available CPU. Library thread counts are one. Both the job and aggregate memory caps are 64 GiB, configured by `single_worker_memory_gib` in `config/execution.json`. It writes the effective policy to `results/_execution-<run>/execution.json`; subprocesses use that policy through `DRR_EXECUTION_POLICY`. The low-level concurrent configuration retains its 16 GiB per-job cap and 72 GiB aggregate cap.

Native execution uses user systemd, CPU affinity, a memory cgroup, disabled swap and job timeouts. The synthetic process backend uses process groups, RLIMIT_CPU and RLIMIT_AS (virtual address space); reserved address space may penalize some runtimes differently. Each outcome records its execution_backend; it is not identical memory enforcement. Imported/dimensional campaigns require native systemd. Do not mix backend measurements without labelling them.

Budgets persist in `results/_budgets/<run>.json` and are shared across the theater's campaigns. They charge active phase-controller wall time, including validation performed inside those controllers, but not gaps between phases or initial theater preflight. A live reservation is not elapsed consumption: use session start times. The controller lock prevents phase overlap; the theater lock prevents two public theater controllers running together. Do not launch unrelated benchmarks alongside a measurement run.

## Results, stopping and provenance

The controller's schedule, policy, preflight hashes, logs and status live in `results/_execution-<run>/`. Per-campaign phases live in `results/<campaign>/<run>/<phase>/`. Performance state rows are appended per job. Correctness sequences may finish before their aggregate state update. Do not double-count both representations.

```sh
python run_theater.py small --run paper-small --status
python run_theater.py small --run paper-small --stop
python tools/collect.py results/2D_ESA_graph_embeddings/paper-small/final/state.json
```

Stop creates controller and campaign markers. Running workers observe them, terminate, and preserve partial records. A fresh run label is required for another full execution. Completion means the scheduled stages ended; inspect phase outcomes before treating all entries as successful.

Input, binary, harness, roster and policy identities connect admission to timing. Keep code and binaries unchanged during a run. Phase identities automatically record CPU governors, available boost/turbo controls, kernel and microcode. Unavailable settings are null, not assumed disabled. Performance jobs are shuffled with a recorded fixed seed; each phase saves its exact schedule. Preserve compiler and Python/Rust package versions alongside these identities. Preserve `results/build/`, prepared manifests and raw job logs when publishing tables.

## Summaries

Compare the same successful instance set when normalizing algorithms against a fastest value of one. State whether the statistic is a ratio of sums, median ratio or geometric mean. Show successful/configured case coverage beside every aggregate; tools/collect.py exports it beside each measurement. Screening failures stay in the denominator. Use a common successful intersection for speed comparisons and disclose that intersection. The current synthetic campaigns use distinct query streams across suites.

Memory limits are enforced but peak memory is not recorded: no space comparison is supported. Separate construction, query and update costs. Keep IDs-only diagnostics separate from conforming rankings. Do not pool historical runs with different reporting contracts, workloads or execution conditions into one unlabeled table.
