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
