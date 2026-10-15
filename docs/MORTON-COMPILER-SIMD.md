# Morton: compiler-vectorized scan

The former Morton (compiler SIMD) is now the default Morton in the standalone
`src/morton/2d/morton.cc`. Its four-cell searches are unchanged. A 32-point loop
computes independent membership flags; a second loop appends accepted points.
GCC 16 on Archie generates 64-byte vectors for membership at `-O3 -march=native`.
The exact distance helper compares a 64-bit sum and its carry against the
128-bit squared radius. No handwritten SIMD or vectorization pragma is used
in the scan. The encoder retains its scalar BMI2 PDEP.

The old scalar source and ablation variants have been removed. Completed results are immutable: historical
`MortonAutoSIMD` is displayed as Morton in the current report; historical
`Morton` refers to the previous scalar code. Never pool these two series.

Validation covers 19,800 independent-oracle queries, duplicates, extremes and
batch tails, plus sanitized execution and the campaign runner's two input
formats. The completed seven-suite campaign has 855 final measurements for
the promoted implementation. Other compilers may choose different instructions.
