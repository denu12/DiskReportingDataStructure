#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
deps="${1:-$(realpath ../_queue-additional-all-20261022/workspace/src/third_party)}"
mkdir -p bin
common=(-std=c++20 -O3 -march=native -DNDEBUG ph_psi_followup.cpp)
g++ "${common[@]}" -DFOLLOWUP_PH -I"$deps/phtree-cpp/include" -o bin/phtree
psi="$deps/space-tree-lib/include"
python3 prepare_psi.py "$psi" psi-patched --classify
g++ "${common[@]}" -DFOLLOWUP_PSI -DPARLAY_SEQUENTIAL -mcx16 -mbmi2 \
    -Ipsi-patched -I"$psi" -I"$psi/parlaylib/include" -I"$psi/libmorton/include" -o bin/psi

if (( $# )); then exit 0; fi
older=../_queue-additional-all-20261022/workspace
pgm=../_queue-reporting-adapted-20261023/workspace/build/pgm-reporting/include
external="$HOME/Projects/SFC-Index/offline/external"
square="$HOME/Projects/SquareReportingDataStructure"
indexicon="$square/src/third_party/indexicon/indexes"
python3 prepare_indexicon.py "$indexicon" indexicon-patched
g++ "${common[@]}" -DFOLLOWUP_INDEXICON -Iindexicon-patched -I"$indexicon" -o bin/indexicon_kd_3d
g++ "${common[@]}" -DFOLLOWUP_PGM -I"$pgm" -mbmi2 -o bin/pgm_3d
spatial_lib="$(realpath "$older/build/libspatialindex/src")"
g++ "${common[@]}" -DFOLLOWUP_LSI -I"$deps/libspatialindex/include" -L"$spatial_lib" \
    "-Wl,-rpath,$spatial_lib" -lspatialindex -o bin/lsi_3d
g++ "${common[@]}" -DFOLLOWUP_CGAL -I"$external/+_repo_rules2+CGAL/include" \
    -I"$square/deps/include" -frounding-math -o bin/cgal_kd_3d
