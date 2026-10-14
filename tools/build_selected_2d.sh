#!/usr/bin/env bash
# Build the retained standalone Morton and exact SPRK campaign backends.
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"${PYTHON:-python3}" "$base/tools/check_mortonplus_lock.py"
mkdir -p "$base/bin/esa2d"
"${CXX:-g++}" -std=c++20 -O3 -march=native -DNDEBUG -I"$base/src/morton" "$base/src/runner/morton_2d_campaign.cpp" -o "$base/bin/esa2d/morton_cpp.next"
mv "$base/bin/esa2d/morton_cpp.next" "$base/bin/esa2d/morton_cpp"
export RUSTFLAGS="${RUSTFLAGS:--Ctarget-cpu=native}"
target="${CARGO_TARGET_DIR:-$base/build/selected-2d-rust}"
args=(build --release --locked --manifest-path "$base/src/third_party/esa2026/sprk/Cargo.toml" -p sprk --example campaign --target-dir "$target" -j "${BUILD_JOBS:-2}")
[[ ${OFFLINE:-0} == 1 ]] && args+=(--offline)
cargo "${args[@]}"
install -m755 "$target/release/examples/campaign" "$base/bin/esa2d/sprk_rust_exact.next"
mv "$base/bin/esa2d/sprk_rust_exact.next" "$base/bin/esa2d/sprk_rust_exact"
