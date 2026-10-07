# Active implementations

The active static 2D implementations are `Morton` (fully scalar), `MortonSIMD` (SIMD search and reporting), and `MoronSIMDearly` (SIMD plus the original early oracle). Each occupies one file in `src/app/algorithms/sfc`.

The SIMD files duplicate the original implicit B-tree search and the exact integer SIMD circle kernel. They use Highway for CPU dispatch and vector instructions. Squared distances use a carry plus a 64-bit sum, preserving the full 65-bit distance range. Scalar tails use 128-bit arithmetic. Accepted coordinates are explicitly emitted point by point; no interval-only output or later circle filter is used.

`Morton` uses scalar binary search, scalar point checks and compiler flags disabling auto-vectorization. Its new timings are not interchangeable with historical `hcds:best`, which already used SIMD rank searches. Retired source is kept outside the publication repository.

Running experiments retain their frozen binaries and input manifests. Prepare new campaign data/manifests with the new roster before running these implementations; do not rename historical results.

Arch validation (7 October 2026): both runner configurations built successfully. All 31 ordinary-workload verification runs passed: 27 across the three new static algorithms (including full uint32 coordinates and a million-point construction), plus four checks of retained dynamic implementations. No regression-test suite was added. Evidence: `results/three-morton-20261007/verification.json`; staged binaries and hashes: `bin/three-morton-20261007`. These checks are correctness validation, not new performance measurements.
