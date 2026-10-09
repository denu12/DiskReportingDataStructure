# Using the standalone 2D Morton index


`src/morton/morton.cc` is a standalone implementation. Copy that file next to a client source file and include it directly:

```cpp
#include "morton.cc"
#include <iterator>
using namespace diskreport::morton_Morton;

int main() {
    std::vector<Point> points{{100, 200}, {300, 400}, {500, 600}};
    Morton index(points);
    std::vector<Point> matches;
    index.query(Point{300, 400}, uint64_t{100}, std::back_inserter(matches));
}
```

Compile the client on x86-64 with BMI2 support using `g++ -std=c++20 -O3 -mbmi2 -fno-tree-vectorize -fno-tree-slp-vectorize client.cc -o client`. GCC or Clang support for `unsigned __int128` is required. The file includes only compiler/standard-library headers by default.

The index owns a fixed copy of the input points. Queries append every matching coordinate, including coincident input points, to the supplied output iterator. The disk is closed: points on its boundary are included. Clear a reused output vector before the next query. An explicit squared-radius query is also available: `index.query(Circle{center, radius_squared}, output)`, where `radius_squared` has type `Wide` (`unsigned __int128`). Rectangle queries use `Box`.

The repository registers a separate adapter in `src/app/algorithms/static/morton_adapter.cc`. The standalone algorithm receives its circle explicitly and has no dependency on the benchmark's thread-local context.


See [dimensional implementations](../src/morton/README.md) for 3D and d-dimensional usage.
