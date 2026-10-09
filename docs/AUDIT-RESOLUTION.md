# Audit repair record

This revision addresses the retained review of publication commit `0067462`. Earlier measurements remain historical evidence for their recorded source, not results of these changes. Fresh admission and measurements are required before publishing rankings.

| Finding | Change |
|---|---|
| C1: Pkd emitted box hits | Native-point accessors no longer bypass the shared circle output filter. |
| C2: PAM coordinate transposition | One local range-sum reporting callback emits x,y and preserves duplicate multiplicity as integer weights. The faulty upstream example reporting callback is not used. |
| C3: ParGeo midpoint overflow | Cast endpoints to the library's floating type before addition in our uint32 patch. |
| C4 / M3: CGAL kernel and upper edge | Double kernels represent uint32 exactly. Build the k-d tree inside construction timing. Convert closed range-tree upper bounds to exclusive double endpoints, including UINT32_MAX + 1. |
| C5: SPRK adaptation | Native f32 SIMD candidate reporting, conservative outward radius, timed exact integer filtering and explicit coordinate writes. IDs-only uses the same candidate/membership path. The former f64/scalar variant is removed from the active roster; its source remains in Git history. |
| M2: correctness evidence | Mandatory boundary/duplicate admission for every entry; cross-algorithm and cross-repetition answer-count disagreement blocks progression in all phases. |
| M4: dimensional rounding | Floating dimensional backends receive outward margins and exact integer filtering. Numerical failure remains an admission failure, never silently repaired in results. |
| M5: adapter overhead | Flat pre-normalized dimensional nanoflann storage, runtime/import warmup before build timing, one-pass Pkd and PAM reporting. ANN retains its native count/report API and both passes are timed. |
| M7: configuration | NDEBUG in both C++ build paths; f32 SPRK; dimensional Grid receives the mean declared query radius. Remaining f64 wrapper adaptations are explicit. THST's suspected slowdown is not treated as an established source defect: its quadtree midpoint uses min + (max-min)/2, so the ParGeo overflow mechanism does not apply there. |
| M8: claims | README distinguishes static Morton from the external-only dynamic study. Memory caps are not peak-memory measurements; no space comparison is claimed. |
| M9: workloads | Uniform and distribution-matched query locations; pilot-calibrated output sizes; distinct query streams between suites. New fixed-size campaigns have 40 cases each. |
| Timing details | Query geometry and reusable-buffer clearing are timed. Static bench mode uses one timer around the complete query loop; verification remains outside timing. |
| Scheduling / provenance | Seeded interleaving of performance jobs, saved schedules, per-row execution backend, governor/turbo/microcode identity, successful/configured coverage columns. |
| Labels | SPRK (IDs only) is the public display name. Historical machine IDs are retained solely for provenance. |
| Dynamic Pkd | The single-insert construction and single-update regime is disclosed; no claim of optimal batch-dynamic performance. |

## External prerequisite

Redistribution permission for the recovered Chan and STANN sources remains unresolved. Their available source files do not supply an explicit grant; the original STANN site redirects to a login and the attempted Google Code archive metadata requests are forbidden. No license has been invented and no author has been contacted automatically. The current notices preserve attribution and identify this limitation. See [publication status](PUBLICATION.md).

## Validation

Validation uses an isolated Arch workspace with cached pinned dependencies. It does not rerun the publication campaigns or certify historical rankings.

- Both 2D Bazel configurations and all dimensional C++/Rust backends are compiled with the release policy.
- A 2D end-to-end smoke run completed 27 correctness, 72 screening and 216 final jobs; a dimensional run completed 16 correctness, 64 screening and 192 final jobs. All those jobs succeeded and counts agreed. These use small validation inputs, not publication workloads.
- On the final 2D source, 112 targeted jobs (28 entries, three ordinary distributions plus the boundary fixture) yielded 111 passes and the expected THST quadtree duplicate failure. ParGeo, PAM, Pkd and CGAL k-d also pass a 200,000-point uniform check. THST quadtree exceeded the 60-second limit on that check; no unverified cause is asserted.
- A final-source end-to-end run including THST records 29 successful admission jobs and one incorrect result, excludes THST in subsequent phases, and completes 72 screening plus 216 final jobs with equal counts. Exclusion rows carry zero coverage and are not counted as executed jobs.
- Targeted dimensional boundary/duplicate checks cover dimensions 3, 8, 16 and 32. All 18 tested 3D entries pass; all 16 tested entries pass at 8D and 16D. At 32D, Grid misses zero-radius duplicates and Orthtree requests an allocation exceeding the private 4 GiB validation limit. The latter is a validation-cap observation, not a result under the publication 64 GiB cap. Morton is capped at 16 dimensions.
- Dynamic fixture validation passes eight of nine entries; dynamic Pkd terminates with a segmentation fault. The restored gate exposes that failure; the upstream dynamic structure is not repaired.
- THST quadtree loses duplicate multiplicity at a zero-radius query in 2D. This remains a contract failure and is not repaired upstream.
- Python syntax, JSON definitions, all theater previews, local documentation links and git whitespace checks pass. Injected same-phase and cross-phase count disagreements exercise the blocking path and leave prior records unchanged.

Full publication measurements, clean online dependency downloads and a fresh Docker image build are not part of these checks.

Raw validation records are retained privately under `historical_data/audit-20261009/`; that directory is excluded from publication. No new publication rankings are inferred from these small checks.
