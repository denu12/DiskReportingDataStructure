# Indexicon range-reporting competitors

The Indexicon headers are vendored unchanged at revision
[`69da8a3`](https://github.com/psimatis/Indexicon-Spatial-Library/tree/69da8a364f3437a1110d89b9ebeb99473dc25807),
with the upstream MIT license. All ten variants use the native C++ range query.

| Index | Variants | Upstream dimensions | Indexed data |
| --- | ---: | --- | --- |
| R-tree | 2 | Arbitrary, compile time | Points; minimum bounding rectangles (MBRs) |
| k-d tree | 3 | Arbitrary, compile time | Points; adaptive, round-robin, and longest-axis splits |
| Point quadtree | 3 | 2D | Points; point-region, pseudo-median, and longest-axis splits |
| MX-CIF quadtree | 1 | 2D | MBRs |
| Octree | 1 | 3D | Points |

The five arbitrary-dimensional variants are instantiated for every dimension in
the current workloads: 2–16, 32, 34, 96, 100, 128, 784, and 960. A 2D workload
can use nine variants; a 3D workload can use six. Other supported dimensions
use five. These are static reporting competitors.

All variants bulk-load the unchanged input points and use upstream default
node capacities. The two MBR indexes represent each input point by a box with
equal lower and upper corners. Binary scaling preserves all uint32 coordinates
exactly. In 2D and 3D, each payload carries its original integer coordinates
alongside its ID. The output iterator applies the exact squared-distance test
as the native box traversal emits candidates, avoiding a second pass and random
lookups in the input array. Higher dimensions use the ID-based post-filter.
The output is a materialized vector of original point IDs, with distinct IDs
for duplicate coordinates.
Correctness mode checks those IDs against the same exhaustive oracle used by
the dimensional adapters.

Build the adapters on the benchmark host with `python3 tools/build_indexicon.py`,
or use the normal Arch build. After building, `python3 tests/check_indexicon.py`
checks all compiled dimensions against the exhaustive oracle, including duplicate
points, boundary radii, empty data, and the normal runner dispatch.
Fresh campaigns include the supported variants.
Re-prepare manifests after a roster change. The separate Indexicon workspace on
Archie reuses prepared inputs with their original checksums and has its own
campaign definitions and result labels.
