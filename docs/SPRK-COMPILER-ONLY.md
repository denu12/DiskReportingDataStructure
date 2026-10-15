# SPRK compiler-only experiment

Enable vendored `sprk` feature `compiler-only` with release optimization and
`RUSTFLAGS=-Ctarget-cpu=native`. This bypasses explicit AVX-512 dispatch,
`wide` compression, and explicit integer-reporting kernels. Existing ordinary
Rust fallbacks run with unchanged batch widths, trees and output contracts.
The compiler remains free to generate vector instructions.

Build the adapted campaign example with `--features compiler-only`; build the
parent FFI crate with `--features sprk/compiler-only` for SPRK (original).
Default builds are unchanged. Diagnostic builds live in a separate campaign
workspace and retain algorithm IDs to preserve correctness contracts. Label
these results separately when comparing with normal builds.

The retained configuration is SPRK (adapted, no SIMD), machine ID `esa_sprk_RUST_EXACT_NOSIMD`, binary `sprk_rust_exact_nosimd`. Compiler-only original SPRK measurements are historical and no longer displayed.
