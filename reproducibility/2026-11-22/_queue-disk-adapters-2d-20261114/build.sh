#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

previous=../_queue-additional-all-20261022/workspace
pgm=../_queue-reporting-adapted-20261023/workspace/build/pgm-reporting/include
external="$HOME/Projects/SFC-Index/offline/external"
boost="$HOME/Projects/SquareReportingDataStructure/deps/include"
mkdir -p bin
common=(-std=c++20 -O3 -march=native -DNDEBUG foreign_check.cpp)
g++ "${common[@]}" -DBACKEND_ADDITIONAL -DADDITIONAL_PHTREE -I"$previous/src/third_party/phtree-cpp/include" -o bin/phtree
g++ "${common[@]}" -DBACKEND_ADDITIONAL -DADDITIONAL_PGM -I"$pgm" -o bin/pgm_multidimensional
spatial_lib="$(realpath "$previous/build/libspatialindex/src")"
g++ "${common[@]}" -DBACKEND_ADDITIONAL -DADDITIONAL_SPATIALINDEX \
    -I"$previous/src/third_party/libspatialindex/include" -L"$spatial_lib" \
    "-Wl,-rpath,$spatial_lib" -lspatialindex -o bin/spatialindex
g++ "${common[@]}" -DBACKEND_EXACT_CGAL_2D -I"$external/+_repo_rules2+CGAL/include" \
    -I"$boost" -frounding-math -o bin/cgal_kd
