# MortonPlus AVX-512 release - 14 October 2026

The retained 2D implementation requires AVX512F and BMI2. It replaces the locked
AVX2 kernel, keeping the Morton (plus) algorithm ID, standalone header and Results
API. No ISA-conditional implementation or extra competitor is introduced.

## Changes

- Eight packed uint32 coordinate pairs per AVX-512 vector.
- Exact integer distance calculations, unsigned mask comparisons and carry checks.
- Register compression followed by an ordinary vector store; no per-point append.
- One AVX-512 comparison for all eight separator keys in each rank node.
- Four independent vectors per 32-point scan batch.
- Masked loads for the final 1-7 points; inactive lanes are excluded from output.
- Stop refinement at 512 points instead of 128; retain the six-level cap.

The prefix table, cell classification, interval merging, full-cell copying, output
semantics, and construction algorithm are otherwise retained. Source credit and
licence are unchanged. Compile with C++20, -O3 -mavx512f -mbmi2. The shared 2D
campaign executable also requires this ISA; the local WSL host lacks AVX-512, so
execution tests were performed on Archie. 3D and d-dimensional kernels are unchanged.

## Performance evidence

Two exploratory passes each used 21 cases spanning all seven 2D suites. Variants
covered filter-only AVX-512, AVX-512 rank lookup, 8/32-point batches, 128/256/512/1024
stopping thresholds, and masked tails. The selected version improved the second
exploratory pass by 1.272x overall (20/21 wins).

A separate set of 26 cases then compared the selected version against the previous
locked AVX2 implementation. Both were built with GCC -O3 -march=native and used
CPU 1. Each new variant has three full-query repetitions; baseline before and
after gives six repetitions. Ratios use median baseline time divided by median
new time, aggregated as a geometric mean. All complete-query answer counts agree;
four queries per case also have full output multiset comparisons.

Validation: **1.218x overall**, **24/26 wins**, range **0.940x to 1.723x**.

| Suite | Geometric-mean speedup |
|---|---:|
| input_scaling | 1.359x |
| radius_scaling | 1.090x |
| static | 1.344x |
| GeographyLarge | 1.147x |
| 2D_ESA_uniform_points | 1.161x |
| 2D_ESA_geographical | 1.244x |
| 2D_ESA_graph_embeddings | 1.177x |

These are sampled comparisons against the locked AVX2 header. They do not replace
the full 285-case campaign or the older frozen Morton Plus data in the PDF.
The new version is not faster on every case, and gains are specific to this CPU.

## Correctness and integration

27,740 checks passed in native and ASan/UBSan builds on Archie. Coverage includes
all 256 lane masks, guarded output, masked tails, cutoff boundaries, duplicate
multiplicity, full-width coordinates, 65-bit distance sums, append and buffer
moves, concurrent queries, and rank searches. The shared runner passed all 252
verification/timing invocations against an independent integer oracle in both
input formats. The version lock records the new header checksum and previous
release checksum.

Frozen sources, timings and plans are on Archie:
- results/_morton-plus-avx512-20261014/
- results/_morton-plus-avx512b-20261014/
- results/_morton-plus-avx512-heldout-20261014/

The last directory also contains validation.zip and runner-validation.log.
