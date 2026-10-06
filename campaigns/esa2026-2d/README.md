ESA 2026 native-2D workload campaign (common integer-grid adaptation)
=================================================================

Source: https://github.com/wembed-pdf/rembed
Pinned commit: a81b216a2a63bde3d4447e4053b4ca31081fe286
Paper: Benchmarking and Engineering Data Structures for Spherical Range Queries
Data: https://zenodo.org/records/21243483
The upstream source snapshot and MIT license are in third_party/esa2026-workloads/.

This is an imported workload campaign using our bounded harness, NOT a claim
to reproduce the paper's original floating-point timings or Criterion/perf
methodology. The original CSV files, archive-member CRCs and SHA-256 hashes
are retained. import_data.py uses HTTP ranges to import native 2D files only.
The released 2D data provide 15 graph embeddings, 7 uniform-distribution sizes,
and 7 point-of-interest/query pairs at 4 radii: 50 distinct workload cases.
No high-dimensional dataset is projected to 2D. Tables/figures sharing input
files are not counted as independent workloads.

Roster: all 29 static entries. Dynamic implementations are evaluated only in
the separate dynamic-circles campaign. Correctness exclusions are applied
before timing; the current static eligibility count is 25.

Common coordinate policy:
- Parse source point coordinates as f32, matching upstream, then promote to f64.
- For each train/query pair, use the union bounding box and one common scale
  for BOTH axes. Map to uint32 with one-unit padding and nearest-even rounding.
- Apply that identical conversion to every implementation; preserve duplicates.
- Scale every original query radius with the same factor. The closed-circle
  threshold is floor((radius * scale)^2), computed as an exact rational from
  the stored binary64 operands. Distances are compared with 128-bit integers.
- Rounding can change boundary membership versus the original floating-point
  problem. Correctness is defined on the common converted data, not the CSVs.
- campaign.json records origin, scale, rounding, counts and hashes per case.

Our HCDS/EHCDS static and HCDS dynamic variants perform the circle predicate at
the existing candidate-membership check. No post-report circle filter is used
for our variants. Conservative bounding rectangles select candidate ranges.
ESA static radius backends receive native circle queries with a conservative
floating-point envelope and exact integer boundary filtering. Other existing
rectangle adapters use a timed bounding-rectangle-plus-circle filter. Their
underlying indexing and reporting code is not repaired.

All construction, incremental insertion, per-query allocations, candidate
reporting and circle filtering are charged. Dataset loading is outside the
reported build/query times, but inside the whole-job resource limit. The common
integer conversion is preprocessing and not timed as algorithm construction.
The scan-based correctness reference is outside performance timings.

Differences from upstream beyond integer coordinates:
- Existing adapter tuning is retained (including grid cell width .001 after
  normalization); the paper's mean-radius construction hint is not applied.
- All implementations are single-threaded; CPU-only, four independent jobs.
- Separate construction and batch-query wall times replace Criterion sampling
  and hardware counter results. No instruction/cycle comparability is claimed.
- Existing bridge modifications predate this import; see
  ../../src/third_party/esa2026/NOTICE.txt (including prior Kiddo, grid and
  Neighbourhood patches). No new correctness repairs were made to competitors.

Stages and resource limits
-------------------------
correctness: independent brute-force exact multiset checks on random points,
duplicates, extreme coordinates, boundary/zero-radius circles, empty input and
collinear input. A mismatch, unsupported case, crash or other failure excludes
the entry from subsequent timing; logs and the exact input are preserved.
screen: up to 1,450 jobs before exclusions; 60 seconds for the whole job.
final: only successful screening cases, three repetitions (same source data;
not fabricated independent ESA dataset seeds).
Each stage: at most four jobs, physical CPUs 1/2/3/4, 16 GiB per job, 72 GiB
aggregate cgroup limit and no swap. Budgets are shared with the other campaigns:
30 minutes for correctness, 8 hours for screening and 24 hours for final.
Final jobs have 180 seconds; selected serial follow-ups have 300 seconds
and share a 2-hour allowance with serial contention checks. In the uniform
scaling series, two successive size timeouts skip larger sizes.
Correctness eligibility is tied to the manifest and binary/library hashes.

Preparation and execution
-------------------------
Use the shared commands in the root README. Raw CSV files belong in data/esa2026-2d/data; prepared inputs and generated manifest belong in data/esa2026-2d. Results belong in results/esa2026-2d/<run>.
The reference-manifest.json records the original imported workload mapping and hashes; the generated manifest is authoritative for a run.
