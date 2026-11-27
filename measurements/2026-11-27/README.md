# Disk results captured on 27 November 2026

This incremental snapshot contains **50 result/metadata files in 15 bundles**
(2.73 MB compressed), with **41,637 recorded job rows** and
**28,469 successful final repetitions**. These are observations,
not independent algorithm/workload pairs; snapshots and phases overlap.

Result files were captured on Archie from **2026-11-27T08:54:59.791062+00:00** to
**2026-11-27T08:55:00.275467+00:00**, at low IO/CPU priority away from benchmark CPU 1.
Only result logs and manifests were read; inputs and builds were excluded.

- Native-output measurement queue: complete, including all 19,335 successful final repetitions.
- Indexicon/nanoflann follow-up and SNN recovery: complete as recorded, retaining failures and timeouts.
- Newer-version Rust repair: 1,600 cases completed three repetitions, 63 screening timeouts, 11 Orthtree allocation failures.
- Remaining 260 cases: finished with 219 successful final repetitions; 151 screening timeouts and 35 screening errors.
- Timeout-repeat follow-up: **partial, 1,586 of 2,847 attempts captured**—329 successful, 1,240 timeouts and 17 errors. Later attempts are absent from this snapshot.
- The one observation overlapping cleanup verification IO is identified in `measurement-exclusions.json`; its clean replacement is still queued.

Current append-only logs are authoritative. Some original queue-status counters
precede removal of superseded observations. Preserve reporting contracts,
correctness admissions, source-run labels and backend hashes; a successful
timed process is not a correctness certificate. Timeout follow-ups complement
their named source runs and must not be treated as unrelated full campaigns.

[index.json](index.json) lists bundle hashes and
[verification.json](verification.json) records successful hash, record-count,
JSONL and redaction checks. Capture details are in [capture.json](capture.json).
`cleanup-replacements.json.gz` records exact campaign/algorithm/case replacement
keys used to prune older snapshots. Historical exports with unknown campaign
identity remain historical and must not supply selected-version comparisons.

An overly broad older cleanup rule could confuse same-named 2D/3D cases. The
older snapshots were rebuilt from their original Git archives and pruned using
exact campaign identities. [Independent verification](restored-3d-verification.json)
confirmed **50,479 unsuperseded 3D rows across 139 state artifacts were retained**.
