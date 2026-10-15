# Three-dimensional Morton upgrade (15 October 2026)

The 3D lineup now follows the 2D names and roles. All retain full uint32 triples,
96-bit Morton keys, exact closed-ball membership (up to 66 distance bits),
uint128 squared radii and duplicate multiplicities.

| Variant | Main changes | API |
|---|---|---|
| Morton | Readable 32-point independent membership loops; exact carry arithmetic; compiler vectorization; scalar BMI2 Morton encoding | `Morton3D::query_squared(center, radius2, output_iterator)` |
| Morton (simd) | Eight-point AVX-512 distance tests; one vector comparison per eight-key rank node; compressed coordinate axes interleaved directly into output | `MortonSIMD3D::query_squared(center, radius2, Results&)` |
| Morton (plus) | Eight-point AVX-512 boundary tests; masked tails; compacted xyz triples; AVX-512 rank comparisons; 512-point splitting cutoff | `MortonPlus::query(center, radius2, Results&)` |

Plain Morton is a standalone 100-line implementation. Explicit SIMD retains
its prior coordinate-block layout and batched key encoder. Its result buffer
reserves scratch space for full vector stores. Plus retains the ESA-derived
prefix table, octree rejection/acceptance, merged ranges and memcpy of contained
points. The Plus source remains standalone. No ISA dispatch branches were added.

## Controlled timing evidence

Machine: Archie, Ryzen 5 7600X, CPU 1, one worker. Query time only. Construction
is outside timed regions. All algorithms materialize coordinates, with a compiler
barrier observing the output. One warm pass precedes three measured repetitions
in shuffled order. Each case uses 96 evenly selected queries from its 1,000-query
input. Input hashes and answer counts agree. This is an optimization study, not
a replacement for the full campaign.

Tuning used 19 seed-1 cases: input sizes 100k/2m/8m/20m, all seven radius settings,
and all eight fixed-size distribution/selectivity settings. Validation used
the corresponding 19 seed-3 cases. Median time per case, then geometric mean
of old/new time ratios, gives:

| Current implementation | Previous implementation | Speedup | Cases faster |
|---|---|---:|---:|
| Morton | Old handwritten-AVX2 Morton3D | 0.915x | 3 / 19 |
| Morton (simd) | Old handwritten-AVX2 Morton3D | 1.251x | 19 / 19 |
| Morton (plus) | Old AVX2 MortonPlus3D | 1.491x | 19 / 19 |

The new plain Morton is about 9% slower than the previous handwritten-SIMD
implementation; it provides the readable compiler-only counterpart rather than
a claimed speed improvement over explicit SIMD. GCC confirms vectorization of
its membership loop. SIMD improved 1.148x-1.567x across these cases; Plus improved
1.008x-2.043x. These finite samples do not establish a universal speedup.

An initial interleaved-coordinate SIMD draft was approximately tied with old
AVX2 and was discarded. Keeping the old blocked coordinate layout produced the
retained SIMD improvement. Plus thresholds 128, 512 and 1024 were compared;
512 gave a strong improvement with less extra scanning than 1024. A separate
branchless preallocated-output experiment for plain Morton was slower and was
also discarded. It is not in the active implementation.

## Correctness and integration

- 19,216 geometry and output-compaction cases, passed natively and under
  AddressSanitizer/UndefinedBehaviorSanitizer for the retained code.
- All 256 acceptance masks for each tail size 1-8, with distinct xyz values,
  prefix/suffix guards, duplicates and output-append checks.
- Independent 128-bit oracle checks around 2^64, 2^65, exact boundaries, extreme
  coordinates, zero/maximal radii, batch tails and splitting cutoffs.
- MortonPlus3D's existing 95,603 checks also pass, including rank boundaries,
  full-width encoding, concurrent reads and output-buffer moves.
- 416 runner verification/benchmark invocations pass across all three Morton
  variants and retained SPRK; unsupported dimensions are rejected.
- Five roster tests pass. The static 3D roster has three Morton variants;
  MortonSIMD3D is not inserted into the higher-dimensional campaign.

Build via `bash tools/build_selected_3d.sh`, then run
`python tools/check_selected_3d.py`. CMake and Bazel targets are also updated.
Explicit SIMD and Plus require AVX-512F; Plus and plain encoding require BMI2.
GCC/Clang with unsigned __int128 and C++20 are required.

Superseded 3D source copies have been removed; historical lineage is retained. Study records are in
`docs/evidence/morton-3d-upgrade/`; remote scratch records are under
`results/_morton-3d-upgrade-20261015/` on Archie. Existing full-campaign results
and PDFs still describe their older 3D implementations. Fresh full-campaign
measurements are required before relabeling those results.
