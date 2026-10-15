# MortonPlus optimization study - 14 October 2026

No performance change was retained. The production header and release lock stay
at the fixed AVX2/BMI2 version. A 256-point stopping threshold looked promising
on exploratory cases but gave only 1.026x on the separate validation set, with a
worst-case speedup of 0.841x (about 19% slower). This tradeoff was not adopted.
The expanded correctness tests are retained.

## Method

Archie, CPU 1, GCC -O3 -march=native, one process at a time with the campaign lock.
Each candidate runs three complete query repetitions. The baseline runs before
and after candidates, giving six repetitions; its median is the denominator for
comparison (reported speedup is baseline seconds / candidate seconds). All use
the same exact coordinate-reporting contract and reusable Results buffer.
Four queries per case are compared as full output multisets; total answer counts
agree across all timed runs. All comparisons use the currently locked header,
not the older header represented in existing PDF measurements.

The exploratory set contains 21 cases across all seven 2D suites. The 256-point
candidate was additionally checked on 26 disjoint cases. These experiments are
samples, not a replacement for the full campaign. Small differences can include
measurement noise and code-layout effects; they do not establish causality.

## Exploratory results

| Experiment | Candidate | Geometric-mean speedup | Wins / 21 |
|---|---|---:|---:|
| plus-opt | batch32 | 1.007x | 10 |
| plus-opt | bucket_search | 0.999x | 15 |
| plus-opt | depth4 | 0.995x | 11 |
| plus-opt | empty_first | 0.982x | 9 |
| plus-opt | prepare_once | 1.017x | 15 |
| plus-opt | threshold256 | 1.061x | 16 |
| plus-opt | threshold64 | 0.920x | 7 |
| plus-opt2 | combined256 | 1.054x | 18 |
| plus-opt2 | threshold1024 | 1.067x | 11 |
| plus-opt2 | threshold256 | 1.050x | 16 |
| plus-opt2 | threshold512 | 1.063x | 12 |
| plus-masks | fast_masks | 0.803x | 0 |
| plus-masks | skip_empty | 0.863x | 0 |
| plus-squares | squares | 0.985x | 14 |

The threshold candidates replace only the 128-point stopping threshold. batch32
increases the eight-point scan batch to 32. depth4 caps refinement at four extra
levels rather than six. bucket_search replaces the global SIMD rank search with
binary search inside the lookup bucket. empty_first checks the lookup population
before cell geometry. prepare_once prepares SIMD constants once per query.
combined256 combines that preparation change with the 256-point cutoff.
skip_empty avoids writing zero-acceptance SIMD batches; fast_masks also directly
stores fully accepted batches. squares uses exact 64-bit component squares with
128-bit accumulation in scalar membership/cell-distance calculations.

## Validation set: 256-point threshold

26 cases, 17 wins, 1.026x overall.

| Suite | Speedup |
|---|---:|
| input_scaling | 1.034x |
| radius_scaling | 1.000x |
| static | 1.182x |
| GeographyLarge | 0.973x |
| 2D_ESA_uniform_points | 0.922x |
| 2D_ESA_geographical | 0.999x |
| 2D_ESA_graph_embeddings | 1.033x |

## Reproducibility

Frozen source, case plans, per-run timings and status are on Archie under:
- results/_morton-plus-opt-20261014/
- results/_morton-plus-opt2-20261014/
- results/_morton-plus-heldout-20261014/
- results/_morton-plus-masks-20261014/
- results/_morton-plus-squares-20261014/

The release remains unchanged. The test suite now exercises point counts around
128, 256, 512 and 1024, and all sixteen four-lane compression masks with guards.
