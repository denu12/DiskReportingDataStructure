# Current Morton implementations

The static 2D implementations are `Morton` (fully scalar) and `MortonSIMD` (SIMD search and reporting). Each occupies one file in `src/morton/`. Neither uses an early-termination oracle.

`MortonSIMD` is standalone and uses AVX2 intrinsics for rank search and reporting. It requires AVX2 and BMI2; Highway dispatch is no longer part of this implementation. Its integer circle kernel represents squared distances with a carry and a 64-bit sum, preserving the full 65-bit range. Scalar tails use 128-bit arithmetic. Accepted coordinates are explicitly emitted point by point; no interval-only output or later circle filter is used.

`Morton` uses scalar binary search, scalar membership checks and compiler flags disabling auto-vectorization. Its standalone `Point`, `Box` and `Circle` types provide integer-radius and squared-radius query APIs. BMI2 encoding and unsigned 128-bit distance checks remain scalar. The optional benchmark adapter supplies the existing bounding box and explicit circle to the same scan.

See the [standalone usage example](MORTON.md) and the [3D/d-dimensional implementations](../src/morton/README.md). New measurements require fresh correctness admission for the exact binaries and manifests being timed.

The standalone conversion changes the SIMD executable. Previous Highway measurements remain historical results; use fresh admission and timing for this version.

## Reporting and search optimization

MortonSIMD checks eight contiguous points per AVX2 iteration. It separates x/y
coordinates in registers and evaluates even and odd lanes with exact 64-bit
products and carry handling before compressing accepted coordinates. Its public
output-iterator API is unchanged.

Morton3D prepares at most eight query cells on the stack, encodes corners four
at a time, and computes the bounding radius from a square-root estimate corrected
by exact integer arithmetic. Search uses contiguous eight-key nodes instead of
four scattered probes. Points are stored once in aligned blocks of eight, with
separate x/y/z lanes inside each block; reporting uses contiguous loads and
materializes each accepted coordinate tuple. Every candidate still has all three
coordinates checked. No early-distance termination or IDs-only output is used.

The layered 3D rank index adds approximately two bytes per point: steady index
storage is about 30 bytes per point rather than 28, excluding allocator overhead
and temporary construction storage. Both indexes remain standalone single files.

Development comparisons used one pinned core, ordinary uniform/normal/skew inputs,
two seeds at four million points, and a 100,000-point scaling case. Each comparison
used 200 evenly spaced original queries, an untimed warm-up, nine alternating
before/after rounds, reused output capacity, and exact coordinate-multiset checks
on 32 ordinary queries. These targeted comparisons are not replacement campaign
results. Per-point output was retained: batch-vector insertion and the tested 2D
rank alignment did not provide consistent benefits.

## General-dimensional Morton optimization

MortonDDim now uses the same eight-point coordinate blocks and contiguous
eight-key search nodes as Morton3D, generalized across all rank words. Its SIMD
encoder spreads bits with compile-time masks and shifts rather than examining
individual bits. Query bounding radii use square-root estimates corrected by
exact integer arithmetic. Crossing axes are ordered by their most significant
changed Morton bit; precomputed axis XOR deltas stream query cells in sorted
rank order and adjacent cells are merged. No heap allocation or cell sort is
required inside the index query.

The public API and 1–16 dimension limit are unchanged. All candidate distances
retain exact low-word and carry accumulation, and accepted original coordinates
are emitted inside query timing, with duplicate occurrences preserved. The
entire uint32 universe can be emitted directly only when the exact squared
radius proves that all points must be inside. Maximal valid keys are handled
explicitly when they equal search-node padding. Cell enumeration remains
exponential in the number of crossing axes; streaming does not remove that limit.

Steady storage is approximately 4D + 9*ceil(D/2) bytes per point, compared with
4D + 8*ceil(D/2) previously, excluding vector objects, allocation rounding and
temporary construction storage. Coordinates are stored once. Padding is confined
to the final coordinate block and the rank-node levels.

On Archie (Ryzen 5 7600X, GCC 16.1.1, one pinned core), 96 targeted uniform-input
comparisons used 100k and 1m points, two seeds, four radii, 64 queries, an untimed
warm-up and seven alternating before/after rounds. Query geometric-mean speedups
were 2.31x, 2.88x, 3.37x, 4.27x, 4.90x and 6.01x for D=2,3,4,8,12,16 respectively.
These are development comparisons, not replacement results for the full
dimensional campaigns. Reused output buffers still materialized every coordinate.

The standalone regression test checks every dimension 1–16 against an independent
integer-coordinate multiset oracle, including closed boundaries, duplicates,
zero and maximal radii, carry overflow, padded nodes and every encoding depth.
Build and run it with `g++ -std=c++20 -O3 -mavx2 src/morton/d_dim/morton_d_dim_test.cc
-o /tmp/morton_ddim_test && /tmp/morton_ddim_test`, or use CMake/CTest's
`morton_ddim_test` target in `src/runner/dimensional`. Fresh campaign admission is
required before using the new implementation for publication timings.
