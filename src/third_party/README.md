# Imported code and dependencies

This directory groups vendored competitor libraries, integration crates,
upstream notices and imported ESA workload-generation tools.
`esa2026-workloads/` is the imported paper artifact; it supplies dataset tools
and reference source. `esa2026/` contains the Rust/Python integration and its
vendored dependencies. ANN, STANN and Chan source/notices have separate folders.

`indexicon/` contains the unchanged headers pinned at
`69da8a364f3437a1110d89b9ebeb99473dc25807`, their upstream MIT license and
source record. The [Indexicon guide](../../docs/INDEXICON.md) describes our
native-box-to-ball adapter. Historical disk-aware traversal modifications are
kept separately in the [frozen source collection](../../reproducibility/2026-11-22/README.md).

Not every dependency is checked into this directory. Bazel downloads the
libraries pinned in `src/MODULE.bazel`; Cargo resolves the pinned lockfiles;
Python packages are specified by `esa2026/python-requirements.txt`.

Root [tools/](../../tools/README.md) contains our own build, preparation and
orchestration scripts. Imported scripts retain their upstream layout here.
[Credits, licenses and modifications](../../docs/THIRD_PARTY.md) identify origin;
[publication labels](../../docs/ADAPTERS.md) distinguish adaptations.
