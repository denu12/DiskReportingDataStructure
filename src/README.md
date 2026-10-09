# Source code

Our algorithm code is in **[morton/](morton/README.md)**. Each of its four `.cc`
files is standalone: copy one file into a C++20 client and include it. None uses
project headers, the experiment harness or an external SIMD library.

| Location | Purpose |
|---|---|
| [morton/morton.cc](morton/morton.cc) | Scalar 2D Morton index. |
| [morton/mortonSIMD.cc](morton/mortonSIMD.cc) | 2D Morton with SIMD rank search and reporting. |
| [morton/morton3D.cc](morton/morton3D.cc) | Specialized 3D Morton index. |
| [morton/morton_d_dim.cc](morton/morton_d_dim.cc) | Generic Morton index for 1–16 dimensions. |
| [app/](app/) | Native entry points and algorithm registration. |
| [app/algorithms/static/](app/algorithms/static/) | Static adapters, including separate wrappers for our 2D indexes. |
| [app/algorithms/dynamic/reporting/](app/algorithms/dynamic/reporting/) | Dynamic competitor adapters. |
| [benchmark/](benchmark/) | Shared point/query types, integer geometry, timing and correctness oracle. |
| [runner/](runner/) | Current dimensional benchmark drivers and adapters. |
| [third_party/](third_party/README.md) | Vendored libraries and imported workload-generation code. |
| [utils/](utils/) | Shared logging and random-generation utilities. |

Bazel builds the 2D harness. CMake, direct C++ compilation and Cargo build the
dimensional drivers. Use the root build scripts documented in
[RUNNING.md](../docs/RUNNING.md). The public experiment command is
`python run_theater.py THEATER`; the four standalone indexes do not run experiments.
