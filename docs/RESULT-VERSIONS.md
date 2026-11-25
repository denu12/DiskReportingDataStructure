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

The separately requested [remaining-case queue](../config/disk-remaining-260-20261123.json)
waits for that repair to finish. It includes all 195 remaining competitor cases,
the 14 IDs-only SPRK diagnostic cases, and 51 previously disabled brute-force
control cases: 260 algorithm/workload pairs total. Only those explicit control
cases are re-enabled. Existing algorithms and adapters remain unchanged. The
IDs-only diagnostic remains excluded from exact-contract rankings. The same
single-core, timeout, correctness-flag and case-error policies below apply.

On 24 November the user additionally requested all missing final repetitions
previously suppressed by a timeout. The
[timeout-repeat follow-up](../config/timeout-repeat-followup-20261124.json) waits
for the 260-case queue and refreshes its case inventory afterward, considering
both disk and square. Its initial inventory was 2,523 final repetitions across
953 disk cases; square had no unattempted repetitions caused by timeout.
Already attempted repetitions, including recorded timeouts, are not rerun.

This follow-up explicitly overrides timeout suppression: each queued final
repetition runs independently with a 180-second limit, even if an earlier
repetition times out. Slots suppressed after a screening timeout are included.
No algorithm changes are made. Original source-run labels and backend hashes
remain attached; unlike adapter versions must not be pooled as repetitions.
The initial inventory has a worst-case duration of 126.2 hours if every attempt
reaches its limit; the final count is determined after the prerequisite ends.

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

On 25 November the user also requested deletion of superseded adapter source.
The November 14 profile, pre-fix controller backups, retired Rust coordinate
drivers and duplicate 2D/3D-only bootstrap sources were removed. The current
native dispatcher is canonical at `src/runner/native-rust`; its generic search
function is unchanged. Build targets, routing and source manifests no longer
refer to the removed drivers. Selected parity/PH-PSI profiles, shared SPRK
code and source needed by active queues are retained.
The older PH/PSI branches inside the parity header and their patched-library
copy were also removed; the current PH/PSI profile remains intact. The retained
PGM and libspatialindex function bodies and native Rust search function are
unchanged, with hashes in the source cleanup record.
