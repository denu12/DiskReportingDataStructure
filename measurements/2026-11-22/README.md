# Measurements captured on 22 November 2026

After the requested removal of superseded results on 23 November, this snapshot
contains **756,591 recorded files in 352 bundles**, totaling **82.7 MB compressed**.
Phase-state summaries contain **266,812 rows**, including historical and
overlapping observations. These counts are not independent successful measurements.
The original capture contained 808,176 files and 371,319 phase-state rows.
Pruned records and bundles carry updated hashes and explicit pruning metadata.

Capture interval: **18:52:56–19:04:44 UTC**. The sources are Archie's current
`results/` and relocated `historical_data/results/`. The
[23 November selection](../selections/2026-11-23/README.md) supplies completed
newer replacements, including the rest of the native-output 2D measurements.

The capture includes the completed Indexicon 2D/3D campaigns, disk adapter reruns, the newer MortonPlus/SPRK higher-dimensional runs, and the latest native-output measurement queue. Incorrect, timed-out, unsupported, interrupted and infrastructure-failed outcomes remain in their original runs.

Queue status captured during export:

- `_queue-indexicon-20261105`: complete for its original static, static-3d and small theaters; its original higher-dimensional theater was excluded.
- `_queue-disk-adapters-2d-20261114` and `_queue-disk-adapters-parity-20261115`: complete.
- `_queue-measure-inexact-and-ddim-20261120`: partial, with final Static3D measurements in progress. Its four higher-dimensional campaigns and preceding 2D/3D campaigns were recorded as completed.
- `_queue-higherdim-missing-indexicon-20261122`: queued behind the active measurement queue. Its plan is included; future SNN Rust, nanoflann and higher-dimensional Indexicon timings are not in this snapshot.

Files were read over an interval, rather than from an atomic filesystem snapshot. Queue status, phase states and append-only logs may therefore describe different moments within that interval. Later measurements require a later export.

See [index.json](index.json) for original file counts, bundle SHA-256 hashes and phase summaries; [verification.json](verification.json) for verified counts and JSONL summaries; and the [format description](../README.md) for reading bundles. All 352 bundles passed hash and record-count verification, with no unreadable source files or credential-pattern findings. JSONL artifacts contained no invalid lines.

Prepared binary inputs, build outputs and dependency caches are excluded. Local home paths, host/user fields and private IP addresses are redacted. Keep source identities, workload definitions, reporting contracts and correctness admissions when comparing algorithms; do not combine historical and replacement runs as independent repeats.
