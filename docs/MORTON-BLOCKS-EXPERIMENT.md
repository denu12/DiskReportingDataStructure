# Morton (blocks): isolated-change experiment

Historical experiment: deprecated implementation/test copies have been removed. The measurements below remain historical evidence. Current implementations are in [src/morton](../src/morton/README.md).

All measurements below are query time, on Archie CPU 1, using the existing frozen 2D inputs. These are controlled exploratory measurements, not a full campaign rerun.

## Selection

Four isolated changes were first tested on 21 cases (three from each of seven suites): 64-bit intermediate squares (1.06x geometric-mean speedup), tighter Morton intervals (1.22x), a preallocated output buffer (1.02x), and branchless output compaction (0.98x). No combination of these changes was adopted.

Cached bounds were then tested with blocks of 16, 64 and 256 points. The 64-point design gave 1.72x across the 21 selection cases; 16 and 256 gave 1.67x and 1.52x. The 64-point rejection-only control gave 1.53x. The retained feature is the per-block bounding-box index, used for outside rejection and inside acceptance.

## Held-out validation

The final source was tested on 26 different cases from the same seven suites. Each index used three timed repetitions over all original queries. Scalar Morton was measured both before and after Morton (blocks); the denominator is the median of those six scalar measurements. Per-suite and overall speedups are geometric means of per-case ratios. Overall, Morton (blocks) was 1.63x faster and won 17 of 26 cases.

| Suite | Held-out cases | Scalar time / blocks time |
|---|---:|---:|
| input_scaling | 4 | 2.31x |
| radius_scaling | 4 | 2.64x |
| static | 4 | 1.64x |
| GeographyLarge | 4 | 1.20x |
| 2D_ESA_uniform_points | 2 | 1.00x |
| 2D_ESA_geographical | 4 | 1.03x |
| 2D_ESA_graph_embeddings | 4 | 1.97x |

Ratios above one favor blocks. Some small-query cases regress; the lowest held-out ratio was about 0.82x. These measurements do not establish that this feature alone explains the full MortonPlus speedup.

Both variants were compiled together with GCC, `-O3 -march=native -fno-tree-vectorize -fno-tree-slp-vectorize`. There is no manually written SIMD in either variant. Construction and sampled output verification occur before timing; the timed loop materializes every answer and uses a compiler barrier. The first four queries per case have their complete output multisets checked against scalar Morton. All-query answer totals agree across all repetitions.

Independent integer-oracle tests passed 12,480 queries including block boundaries, duplicates, extreme coordinates, 65-bit distances, rectangles and append semantics. ASan/UBSan passed; the common 2D runner passed 196 invocations across the retained implementations.

## Reproducibility

Archie retains source snapshots, compiler commands, case selection, raw per-repetition measurements and logs under:
- `results/_morton-one-change-20261014`
- `results/_morton-blocks-explore-20261014`
- `results/_morton-blocks-heldout-20261014`

The experiment used the now-removed `morton_blocks.hpp`. Extra storage is one 16-byte box per 64 points; extra construction work is linear after the existing sort. No other Morton feature is enabled in this variant.
