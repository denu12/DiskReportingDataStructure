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
accepts 1–16 dimensions because candidate-cell enumeration grows exponentially.

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
