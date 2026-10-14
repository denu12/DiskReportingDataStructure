#!/usr/bin/env bash
# Build only the new 3D MortonPlus and SPRK adaptation; no campaigns launched.
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"${PYTHON:-python3}" "$base/tools/check_mortonplus_lock.py"
mkdir -p "$base/build/dimensional" "$base/build/ddim-rust/release"
"${CXX:-g++}" -std=c++20 -O3 -march=native -DNDEBUG "$base/src/runner/dimensional/morton_plus_3d_campaign.cpp" -o "$base/build/dimensional/morton_plus_3d_check.next"
mv "$base/build/dimensional/morton_plus_3d_check.next" "$base/build/dimensional/morton_plus_3d_check"
export RUSTFLAGS="${RUSTFLAGS:--Ctarget-cpu=native}"
target="${CARGO_TARGET_DIR:-$base/build/selected-3d-rust}"
args=(build --release --locked --manifest-path "$base/src/third_party/esa2026/sprk/Cargo.toml" -p sprk --example campaign3d --target-dir "$target" -j "${BUILD_JOBS:-2}")
[[ ${OFFLINE:-0} == 1 ]] && args+=(--offline)
cargo "${args[@]}"
install -m755 "$target/release/examples/campaign3d" "$base/build/ddim-rust/release/sprk-adapted-3d-check.next"
mv "$base/build/ddim-rust/release/sprk-adapted-3d-check.next" "$base/build/ddim-rust/release/sprk-adapted-3d-check"
