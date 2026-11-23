# Current result versions

Do not fill a failed newer adapter run with timings from an older adapter or
combine repetitions from different versions. A terminal timeout has no numeric
score, even when an older version completed that workload.

## Reviewed 2D disk selection

[The 23 November selection index](../config/result-selection-2d-20261123.json)
lists the frozen run profiles for all 17,250 supported algorithm/workload pairs
across seven 2D campaigns: 16,566 cases have three final timings and 684 have a
terminal timeout. The finished replacement adapter/native-output runs are used
where available; unchanged baselines retain their original versions.

The full artifact is on the benchmark host at
`results/_selection-disk-2d-20261123/selection.json`. Its SHA-256 is in the index.
The [published redacted selection](../measurements/selections/2026-11-23/README.md)
has its own published hashes.
Validate/export it with `python3 tools/versioned_results.py selection.json`
and `python3 tools/versioned_results.py selection.json --csv` respectively.
Contracts, correctness admissions and version labels remain in the export.
This is an explicit campaign selection, not a claim that every default adapter
in an arbitrary checkout was measured. Frozen Indexicon disk-aware traversal
profiles differ from the public native-box-plus-filter baseline; keep their
version labels. The IDs-only SPRK diagnostic remains distinct from exact SPRK.

## Native Rust dispatch

Build with `python3 tools/build_native_rust.py`. The isolated versioned target
supports dimensions 2–16 and 32. The entire generic search/reporting function is
preserved; only module paths and dimension dispatch change. Source, function
and binary hashes are recorded, dependencies stay pinned, and Cargo uses one
build job. Both 2D and dimensional routing use this target without falling back
to a historical queue's Cargo directory.

## Newer-version reruns only

The higher-dimensional disk repair queues only the seven Rust competitors whose
older integer-coordinate adapters were replaced by native-output adapters:
Kiddo, Nabo, Neighbourhood, VP-tree, Orthtree, Grid and SNN Rust. There are 1,674
algorithm/workload pairs, reusing 34 already resolved SNN native-output cases.
Unchanged implementations and provenance-only gaps are not part of this queue.

Execution is single core, one worker, CPU 1. Correctness failures are flagged
and still timed. Screening has a 60-second limit; finals have a 180-second
limit. A screening timeout skips all finals; the first final timeout skips
remaining repetitions. A case error skips its remaining repeats and allows
other cases to continue. No search algorithm is changed.

At the user's request, superseded result observations are deleted when a newer
replacement has three timed final repetitions or a terminal timeout. Cases
awaiting their replacement are retained until that condition is met. Use
`tools/prune_superseded_results.py` with an explicit replacement selection;
it previews changes unless `--apply` is passed. Inputs and unrelated results
are retained. Rewritten published bundles record their pruning and receive new
bundle/content hashes. Git history is not rewritten.
