# Our four standalone Morton implementations

Each file contains a complete static index and includes only standard-library
or compiler intrinsic headers. Copy the selected file next to your client;
no other repository file, benchmark global or third-party library is required.
Benchmark wrappers live elsewhere under `src/app/algorithms/static/` and
`src/runner/dimensional/`.

| File | Index type | Compiler flags (C++20) |
|---|---|---|
| [morton.cc](morton.cc) | `diskreport::morton_Morton::Morton` | `-O3 -mbmi2 -fno-tree-vectorize -fno-tree-slp-vectorize` |
| [mortonSIMD.cc](mortonSIMD.cc) | `diskreport::morton_MortonSIMD::MortonSIMD` | `-O3 -mavx2 -mbmi2` |
| [morton3D.cc](morton3D.cc) | `diskreport::morton3d::Morton3D` | `-O3 -mavx2` |
| [morton_d_dim.cc](morton_d_dim.cc) | `diskreport::ddim::MortonDDim<D>` | `-O3 -mavx2` |

Use GCC or Clang on x86-64 with the indicated CPU features and `unsigned __int128`
support. The scalar baseline disables auto-vectorization. SIMD variants use AVX2
for search and reporting; there is no early-termination oracle. The generic index
accepts 1â€“16 dimensions because candidate-cell enumeration grows exponentially.

```cpp
#include "mortonSIMD.cc"
#include <iterator>
using namespace diskreport::morton_MortonSIMD;
int main() {
    std::vector<Point> points{{100, 200}, {300, 400}, {500, 600}};
    MortonSIMD index(points);
    std::vector<Point> matches;
    index.query(Point{300, 400}, uint64_t{100}, std::back_inserter(matches));
}
```

Compile with `g++ -std=c++20 -O3 -mavx2 -mbmi2 client.cc -o client`.
The index owns a copy of the input. Queries append actual coordinates of all
matches to the supplied output iterator. Clear your result vector before reusing
it. Both 2D indexes also accept `Circle{center, squared_radius}` and rectangle `Box`
queries. 3D and generic indexes use `Index::Point` and expose
`query_squared(center, squared_radius, output)` as well as integer-radius `query`.
See the [scalar example](../../docs/MORTON.md).

The generic Morton index also uses contiguous eight-key search nodes and aligned
eight-point coordinate blocks. It streams and merges query cells without query
heap allocations. The exact coordinate-reporting API remains unchanged. See the
[optimization and validation notes](../../docs/SIMD-reporting.md#general-dimensional-morton-optimization).

## Morton (plus)

`mortonplus.hpp` is the standalone C++20 port of the ESA authors' MortonPlus,
Rust implementation by Dennis Kobert. See [credits](../../docs/THIRD_PARTY.md).
Use `mortonplus::MortonPlus` with `mortonplus::Results` for native bulk output.
It supports 2D uint32 points and exact uint128 squared radii. GCC or Clang is
required. `mortonplus_test.cc` checks geometry, duplicates, output buffers and
the fixed experimental configuration. The Rust MortonPlus competitor is retired.

The standalone API is intentionally fixed to the measured default: 8-point
batches, six refinement levels, a 128-point stopping threshold, prefix lookup,
inside-cell copying and bulk output. Use `Results`; the ablation switches,
width template and `std::vector` query overload have been removed.

The validated 2D header is locked in `config/mortonplus-2d-lock.json`; selected
builds verify its checksum. `mortonplus3d.hpp` is the standalone 3D extension.
Use `mortonplus3d::MortonPlus`, `mortonplus3d::Results`, and uint32 triples.
It uses full 96-bit Morton keys and exact 66-bit distance sums. See
[version notes](../../docs/MORTONPLUS-VERSIONS.md) for validation and build commands.

## Fixed instruction sets and separate license

Morton source files no longer contain SIMD-selection conditionals or embedded
MIT text. Keep the adjacent LICENSE file with redistributed sources. ESA author
credits remain in the Plus implementations. Scalar Morton remains scalar and
uses BMI2; Morton SIMD and 2D Plus require AVX2 and BMI2. 3D and dimensional
variants require AVX2. There is no automatic scalar or AVX-512 kernel selection.

The experimental `mortonplus_d_dim.hpp` supports dimensions 1-16 with bounded
binary-prefix refinement and bulk output. See the version notes linked above;
performance relative to the baseline is not yet established.
