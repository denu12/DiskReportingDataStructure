# Morton Split traversal experiment

Historical experiment: deprecated implementation/test copies have been removed. The measurements below remain historical evidence. Current implementations are in [src/morton](../src/morton/README.md).

The updated scalar Split avoids unnecessary rank searches for repeated, empty,
or fully covered child ranges. It derives child Morton intervals from the parent
prefix and directly tests ranges with at most 16 points. Larger partial cells
still stop splitting at 64 points. Construction, exact membership, multiplicity,
and vector/iterator output contracts remain unchanged. No SIMD or auxiliary
index was added.

## Validation

- 16,000 queries against a scan, both output APIs, including duplicates, threshold
  boundaries, full-width coordinates, and 65-bit squared radii; ASan/UBSan passed.
- All 252 selected-backend runner invocations passed, with independent integer
  answer checks in both input formats.

## Controlled timings on Archie

21 exploratory cases covered all seven 2D suites. A separate 26-case set then
compared the selected version with the previous Split. Each variant ran three
full query repetitions; the old version ran both before and after the new one.
The baseline is the median of its six repetitions. Speedups are old/new query
seconds, aggregated by geometric mean. Both use the same vector bulk-output
API, CPU 1, GCC `-O3 -march=native -fno-tree-vectorize -fno-tree-slp-vectorize`.
Four queries per case were checked by full output multiset comparison, and total
answer counts agreed across all timed runs. This is a sample, not a replacement
for the full campaign or existing PDF measurements.

Held-out result: 1.108x overall, 21/26 wins; range 0.976x to 2.645x.

| Suite | Speedup |
|---|---:|
| input_scaling | 1.017x |
| radius_scaling | 1.335x |
| static | 1.035x |
| GeographyLarge | 1.081x |
| 2D_ESA_uniform_points | 1.036x |
| 2D_ESA_geographical | 1.203x |
| 2D_ESA_graph_embeddings | 1.050x |

Source and raw measurements are frozen on Archie under
`results/_morton-split-heldout-20261014/`. Exploratory runs are under
`results/_morton-split-improve-20261014/` and
`results/_morton-split-jump-20261014/`.

The 64-point early-scan alternative and common-prefix tree-jumping alternative
were not retained. The shortcuts also slowed lookup+split in the sample, so
that variant remains unchanged.

Old Split SHA-256: `97d459ae332fb6b575f1bd488146cabf8866dacb553cc6030b5ba0304614f069`.

New Split SHA-256: `449a6fd136c1bc61d4b37e126500c652150f03ae85592c9be1309ac1c015830d`.
