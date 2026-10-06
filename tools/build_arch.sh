#!/usr/bin/env bash
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $(uname -s) == Linux ]] || { echo "Build on Arch Linux" >&2; exit 1; }
export PYO3_PYTHON="${PYO3_PYTHON:-$base/.venv/bin/python}"
export RUSTFLAGS="${RUSTFLAGS:--Ctarget-cpu=native}"
export PARLAY_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 RAYON_NUM_THREADS=1
jobs="${BUILD_JOBS:-2}"
mkdir -p "$base/bin/esa2d" "$base/results/build"
cd "$base/src/third_party/esa2026"
cargo_args=(build --release --locked --target-dir "${CARGO_TARGET_DIR:-$base/build/rust}" -j "$jobs")
[[ ${OFFLINE:-0} == 1 ]] && cargo_args+=(--offline)
cargo "${cargo_args[@]}"
install -m755 "${CARGO_TARGET_DIR:-$base/build/rust}/release/libsfc_esa2026.so" "$base/bin/esa2d/libsfc_esa2026.so.next"
mv -f "$base/bin/esa2d/libsfc_esa2026.so.next" "$base/bin/esa2d/libsfc_esa2026.so"
cd "$base/src"
bazel=("${BAZEL:-bazel}")
[[ -n ${BAZEL_OUTPUT_ROOT:-} ]] && bazel+=(--output_user_root="$BAZEL_OUTPUT_ROOT")
[[ -n ${BAZEL_EXTRA_RC:-} ]] && bazel+=(--bazelrc="$BAZEL_EXTRA_RC")
flags=(--config=opt --jobs="$jobs" --local_ram_resources=14000 --cxxopt=-mbmi2 --conlyopt=-std=gnu17 --host_conlyopt=-std=gnu17 --extra_toolchains=@rules_foreign_cc//toolchains:preinstalled_pkgconfig_toolchain)
"${bazel[@]}" build "${flags[@]}" //app:esa_runner
install -m755 bazel-bin/app/esa_runner "$base/bin/esa2d/esa_runner.next"
mv -f "$base/bin/esa2d/esa_runner.next" "$base/bin/esa2d/esa_runner"
"${bazel[@]}" build "${flags[@]}" --define=pargeo=enabled //app:esa_runner
install -m755 bazel-bin/app/esa_runner "$base/bin/esa2d/esa_runner_pargeo.next"
mv -f "$base/bin/esa2d/esa_runner_pargeo.next" "$base/bin/esa2d/esa_runner_pargeo"
{ date -u; uname -srmo; gcc --version; rustc --version; "${bazel[@]}" version; "$PYO3_PYTHON" --version; sha256sum "$base"/bin/esa2d/*; } > "$base/results/build/toolchain.txt"
echo "Build complete; no experiments started."
