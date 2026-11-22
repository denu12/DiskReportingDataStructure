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
g++ "${common[@]}" -DBACKEND_CGAL_RANGE -I"$external/+_repo_rules2+CGAL/include" \
    -I"$boost" -frounding-math -o bin/cgal_rt
g++ "${common[@]}" -DBACKEND_EXACT_PARGEO -DPARLAY_SEQUENTIAL \
    -I"$external/+_repo_rules+pargeo/include" -I"$external/+_repo_rules+parlaylib/include" -o bin/pargeo
g++ "${common[@]}" -DBACKEND_STREAM_PAM -DPARLAY_SEQUENTIAL -mcx16 \
    -I"$external/+_repo_rules+PAM/include" -I"$external/+_repo_rules+PAM/examples/range_query" \
    -I"$external/+_repo_rules+parlaylib/include" -o bin/pam
psi="$previous/src/third_party/space-tree-lib/include"
python3 prepare_psi.py "$psi" psi-patched
g++ "${common[@]}" -DBACKEND_ADDITIONAL -DADDITIONAL_PSI -DPARLAY_SEQUENTIAL -mcx16 -mbmi2 \
    -Ipsi-patched -I"$psi" -I"$psi/parlaylib/include" -I"$psi/libmorton/include" -o bin/psi
g++ "${common[@]}" -DBACKEND_THST \
    -I"$HOME/Projects/SquareReportingDataStructure/src/third_party/thst/include" -o bin/thst
indexicon="$HOME/Projects/SquareReportingDataStructure/src/third_party/indexicon/indexes"
python3 prepare_indexicon.py "$indexicon" indexicon-patched
for variant in KDTREE QUADTREE MXCIF; do
    g++ "${common[@]}" -DBACKEND_INDEXICON -DINDEXICON_DISK_TRAVERSAL -DINDEXICON_DIMS=2 \
        "-DINDEXICON_$variant" -Iindexicon-patched -I"$indexicon" -o "bin/indexicon_${variant,,}"
done
