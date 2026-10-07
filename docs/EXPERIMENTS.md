# Experimental protocol

A campaign groups a scientific question; suites vary workload families. A case fixes data, parameters and seed. Each algorithm/case/repetition is a run.

Static suites vary size, distribution and circle radius independently. Uniform coordinates span the uint32 grid; normal points are clipped at the boundary; skew inputs use an exponential second coordinate. Radius is a fraction of grid width, not an expected answer count. Seeds 1–5 define separate cases; final repetitions reuse those cases.

Dynamic inputs begin with uniform points. Phased cases execute updates before queries; interleaved cases shuffle operation types while generating valid deletions. Deletion removes one occurrence. Update fractions are 0.1, 0.5 and 0.9. ESA compares static implementations only.

Construction includes representation conversion and index building. Update calls, result allocation/reporting and adapter filtering are timed. Input loading is outside build/query/update measurements but inside the whole-job limit. Preparation and oracle verification are not algorithm timings.

Correctness failures exclude entries; environment errors block them. Competitor code is not repaired to pass. Screening uses one run per case; final measurement repeats successful screened pairs three times. ESA uniform scaling stops after two consecutive size timeouts. Missing, crashed and timed-out runs retain explicit statuses without imputed timings. Budgets are shared across campaigns with the same run label: 30 minutes for correctness, eight hours for screening, 24 hours for final measurement and two hours shared by optional follow-ups and contention checks. They count active controller time across invocations, including input validation, but not pauses between commands. The authoritative settings are in `campaigns/execution.json`; they also apply to previously prepared inputs.

Select one logical CPU per physical core using `lscpu -e=CPU,CORE,SOCKET` and `--cpus`. Defaults are four workers on CPUs 1–4. Record CPU model, governor, memory, affinity, background load, toolchain and binary hashes. Keep different machines and execution backends separately labelled.

Native execution requires a user systemd session and cgroup-v2 delegation. Each worker has 16 GiB memory, no swap and a stage-specific runtime cap (60 seconds for correctness/screening, 180 seconds for final/contention checks, 300 seconds for timeout follow-ups); the shared slice has 72 GiB. Container execution uses process groups, CPU affinity and 16 GiB address-space limits under the outer container memory cap. Address-space and resident-memory limits have different semantics. The controller kills workers on stop or timeout.

Use a fresh run name to repeat a stage. Manifest, harness and binary changes invalidate gates. Preparation and building never start measurements. Do not run multiple controllers against one result directory.


## Planning the final measurements

After screening all campaigns under one run label:

```sh
python tools/plan.py --run paper
```

The planner projects the observed whole-job screening times onto three final repetitions, includes a 25% margin and estimates scheduling on four workers. This is an estimate, not a worst-case guarantee. Only successful screened pairs are included. The final runner requires a matching plan that fits the budget. For a deliberately smaller study, pass `--campaigns scaling` (or the other campaign names) explicitly.

If the estimate is too large, select fewer workloads uniformly across algorithms. A JSON selection file maps each included campaign to its case IDs, for example:

```json
{"scaling": ["scaling/uniform-n10000-r0.01-s1"]}
```

Then run `python tools/plan.py --run paper --campaigns scaling --matrix selection.json`. Use IDs from the generated manifest. List exactly the campaigns selected with `--campaigns` in the selection file. The fixed-size `static` campaign is planned separately from `scaling`. The selected workload list is common to every algorithm; pair-specific correctness or screening failures still exclude the affected pair. Once final results exist, the plan cannot be changed within that cycle.

## Optional bounded follow-ups

These require explicit algorithm and case selections:

```sh
python tools/run.py followup --campaign scaling --run paper --algorithms ALGORITHM --cases CASE_ID
python tools/run.py contention --campaign scaling --run paper --algorithms ALGORITHM --cases CASE_ID
```

`followup` retries only pairs that timed out during screening or final measurement, once each, with 300 seconds and one worker. It never overrides a correctness exclusion. `contention` repeats selected pairs that succeeded in final measurement, three times, with 180 seconds and one worker. Choose representative cases before inspecting the serial results. Compare their build/query/update times with the corresponding concurrent final measurements; keep the two result sets separate. These stages share a two-hour allowance and retain the same memory limits. CPU selection must match the correctness gate; recorded rows include the actual assigned CPU.

The persistent budget ledger is `results/_budgets/<run>.json`. A repository-wide file lock prevents simultaneous controllers from multiplying the worker count. A normal stop charges elapsed time. An uncatchable controller crash conservatively charges its reserved remaining stage allowance, rather than silently granting a fresh budget on restart. Preserve the ledger with the results. Reusing a new run label starts a new experiment cycle, not a continuation of the old budget.
