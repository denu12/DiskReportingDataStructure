# Morton SIMD AVX-512 update - 14 October 2026

The current standalone 2D MortonSIMD requires AVX512F/BMI2. Its original
four-cell query coverage, construction, layered rank-index layout and exact
coordinate-reporting contract are unchanged. No Plus lookup table, adaptive
splitting, interval merging, cached block bounds or whole-cell acceptance was
added to MortonSIMD.

The changes are eight-key AVX-512 rank comparisons, eight-point exact integer
distance tests, native register compression and direct batch stores, and masked
loads for the final 1-7 points. The distance kernel preserves carries into the
65th bit and accepts all points for larger squared radii. The Results API exposes
only accepted points; seven spare positions permit a full-vector store. Iterator
output remains supported. The derived MortonBlocksSIMD inherits the new rank and
filter kernel but retains its existing iterator reporting path in the runner.

## Validation

Tests ran on Archie after the active campaign released the shared lock:
- MortonSIMD: 39,600 queries passed, both native and ASan/UBSan builds.
- MortonBlocksSIMD: 12,480 queries passed, both native and ASan/UBSan builds.
- All 252 shared-backend verification/timing invocations passed independent
  integer answer checks in both accepted input formats.
- Nine roster tests passed locally.

Checks include duplicate multiplicity, append and reuse, output ordering, every
small batch/tail size, full-width coordinates, squared radii around 2^64 and the
maximum 128-bit value, rectangle queries, and integer-radius overloads.

## Controlled sample

21 cases span all seven 2D suites. Both old and new MortonSIMD use reusable direct
batch output. Baseline AVX2 runs before and after the AVX-512 variant; each run
contains three repetitions. Ratios compare the six-sample baseline median against
the three-sample candidate median. Same executable, GCC -O3 -march=native, CPU 1.
Four queries per case are checked by full coordinate multisets; complete-run
answer counts agree. This is a sample, not the full campaign.

**1.376x overall**, **18/21 wins**. Speedup range: 0.907x to 1.844x.

| Suite | Geometric-mean speedup |
|---|---:|
| input_scaling | 1.368x |
| radius_scaling | 1.225x |
| static | 1.487x |
| GeographyLarge | 1.166x |
| 2D_ESA_uniform_points | 1.490x |
| 2D_ESA_geographical | 1.308x |
| 2D_ESA_graph_embeddings | 1.646x |

Frozen source, timings and validation workspace:
`results/_morton-simd-avx512-20261014/` on Archie. Performance of the inherited
blocks+simd change has not been separately measured. Existing full SIMD campaign
and PDF results remain the earlier AVX2 version; neither is silently replaced.

Current header SHA-256: `47af59469d764f88f29c60b6c934d9be622efe064c3b8a5a8cd3f7950587943e`.
