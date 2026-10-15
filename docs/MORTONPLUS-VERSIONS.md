# Current versions

2D Plus uses the locked AVX-512 release in `config/mortonplus-2d-lock.json`.
3D Plus now uses the 15 October AVX-512 upgrade, with exact triple compaction
and a 512-point split cutoff; see [current 3D evidence](MORTON-3D-UPGRADE.md).
The d-dimensional Plus implementation remains AVX2. The sections below are
historical implementation and validation notes; their older ISA descriptions
do not describe the current 2D/3D sources.

# MortonPlus versions and dimensional extensions

## Current 2D lock: 2026-10-14-fixed-avx2-bmi2

`src/morton/2d/mortonplus.hpp` is now the 305-line fixed AVX2/BMI2 header.
SHA-256: `f1ae43f3cc98623f867cc071bfc9f49cb8d7979dfb6b5baaef2a86411503209e`.

This explicitly supersedes the fixed-defaults source freeze at the user's request.
The previous checksum is preserved in the version JSON. Old campaign binaries
and archived source bundles are unchanged. Current Morton headers have no SIMD
selection branches: 2D Plus uses AVX2 and BMI2, 3D Plus uses AVX2. The previous
optional AVX-512 kernels and portable fallbacks are removed. This is a source
change; historical timings do not measure the new fixed kernel.

MIT text is in `src/morton/LICENSE` (identical to the repository license), not
inside the implementation files. Include LICENSE when distributing source.
The attribution comments remain.
The version record is `config/mortonplus-2d-lock.json`; run
`python3 tools/check_mortonplus_lock.py` to enforce it. Both selected build
scripts check this lock. Changing the release requires an explicit version update.
This is a source/checksum freeze, not a Git tag.

Defaults remain eight-point batches, six refinement levels, a 128-point stopping
threshold, prefix lookup, inside-cell copying and Results output. Prior validation
passed 17,244 checks per portable, AVX2, AVX-512 and sanitizer build, plus 112
runner invocations and 2,536 differential queries against the Rust implementation.

## 3D implementations

`src/morton/3d/mortonplus3d.hpp` is standalone C++20, requiring GCC or Clang's
unsigned __int128. Use `mortonplus3d::MortonPlus` and `mortonplus3d::Results`.
The API appends original uint32 triples, preserving duplicates. It uses full
96-bit Morton keys, an octree prefix lookup (depth capped at eight), an eight-key
rank tree, up to six octree refinement levels, and contiguous copying for fully
contained cells. Rank comparisons are scalar; boundary distance tests use AVX2
unconditionally. Selected triples are written directly
to the result buffer. Squared distances count both possible 64-bit carries.

`src/third_party/esa2026/sprk/src/integer_reporting_3d.rs` extends the authors'
IntegerPointSprk design using Sprk<3,8,f32,u32>, conservative candidate ranges,
and exact integer filtering of eight-point leaf blocks. The filter has AVX-512,
AVX2 and portable implementations. Queries append original coordinates; an ID
API is also tested. The existing 2D Rust implementation is unchanged by this
extension. Neither 3D implementation is a generic higher-dimensional adapter.

The algorithmic credit remains with the ESA authors Thomas Blasius,
Jean-Pierre von der Heydt, Tobias Kempf, Dennis Kobert and Nikolai Maas;
the original Rust MortonPlus implementation is by Dennis Kobert. The C++ port
and these 3D extensions are local contributions. Original license notices accompany the source in LICENSE. See THIRD_PARTY.md for source revisions and license details.

## Build, integration and validation

```sh
bash tools/build_selected_3d.sh
python3 tools/check_selected_3d.py
```

Machine IDs are `MortonPlus3D` and `esa_sprk_RUST_EXACT_3D`; display names are
Morton (plus) and SPRK (adapted). They are registered in static 3D campaigns and
in the dimensional roster for dimension three only. Regenerate prepared manifests
and use fresh run labels. Existing competitors and historical results are retained.
The regular dimensional CMake and Cargo builds include the new programs.

Validation on 14 October 2026:

- MortonPlus3D: 95,603 checks per native AVX2, portable, ASan/UBSan and Archie
  native build, including full-width encoding, rank lookup, exact boundaries,
  duplicates, append behavior and concurrent queries.
- Rust: portable 3D tests, plus full native test suites on AVX2 and Archie's
  AVX-512 CPU. The 3D oracle test covers 18,720 queries with both coordinate and
  ID outputs; direct SIMD-mask tests cover distance carry boundaries.
- 208 runner invocations each locally and on Archie, exercising verification
  and timing protocols; wrong dimensions rejected. Verification compares full
  coordinate multisets with an independent exact scan.
- CMake test and driver targets built; CTest passed.

No full 3D performance campaign has been run for these versions. Correctness
validation does not establish a speed advantage over existing competitors.

## D-dimensional MortonPlus

`src/morton/d_dim/mortonplus_d_dim.hpp` provides
`diskreport::ddimplus::MortonPlusDDim<D>` for dimensions 1 through 16.
`Results<D>` appends original integer coordinates and bulk-copies fully contained
ranges; output iterators are also supported. Compile with C++20 and AVX2.

It retains full 32-bit coordinates and 32*D-bit Morton keys, with exact
unsigned-128 squared-distance sums. A capped 12-bit prefix lookup narrows rank
searches, ending in an eight-lane AVX2 comparison. Query refinement splits one
Morton bit at a time instead of enumerating 2^D children. Exact cell-distance
bounds reject disjoint cells and accept fully contained cells. Queries stop
splitting at 128 candidates or 4096 splits and scan the remaining ranges exactly.
The limit bounds refinement work, not output size or correctness.

The implementation stores sorted points both as contiguous output coordinates
and as eight-point coordinate blocks, trading extra memory for bulk output and
SIMD scans. It is a local dimensional extension using the ESA authors' Plus
techniques, not an unchanged port of their original 2D algorithm.

Build `morton_plus_ddim_check` and `mortonplus_ddim_test` using dimensional CMake.
The runner accepts `CASE.bin MortonPlusDDim [--bench]` and rejects unsupported
dimensions. `MortonPlusDDim` is included in the default dimensional roster. No active queue
is modified, and no full performance campaign has been run for this prototype.

Correctness: 81,808 independent checks across dimensions 1-16, exercising both
iterator and bulk-output APIs, duplicates, maximal coordinates, append semantics,
exact-radius boundaries, SIMD tails and multiword encoding. The fixed 2D and 3D
kernels pass 17,244 and 95,603 checks respectively.

The d-dimensional checks also pass with AddressSanitizer and UndefinedBehaviorSanitizer.
All 160 runner verification/timing invocations pass independent answer-count
checks across dimensions 1-16; dimensions 0, 17 and 32 are rejected. The scalar
and SIMD 2D runner, existing 3D/d-dimensional runners, and new Plus dimensional
runner compile successfully after removal of the instruction-set conditionals.

## AVX-512 2D release (14 October 2026)

The latest locked version is `2026-10-14-avx512-batch32-cutoff512`.
It requires AVX512F/BMI2, scans 32-point batches with masked tails, and uses a
512-point splitting cutoff. See [the release study](MORTONPLUS-AVX512.md).
It passed 27,740 native/sanitizer checks and 252 runner checks on Archie.
The separate 26-case comparison gives 1.218x geometric-mean speedup over the
previous locked AVX2 version. No new full campaign or PDF update is claimed.
