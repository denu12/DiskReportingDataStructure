# Additional original competitors (21 October 2026)

These are pinned upstream implementations, not local reimplementations. Their
source files are unmodified. The adapters load our integer data, call the native
rectangular query, and filter returned candidates with the closed integer-ball
predicate. Both candidate reporting and filtering are timed. Output is materialized.
Conversion, index construction and initial buffer allocation enter construction time.

| Machine ID | Implementation | Timed output | Construction |
|---|---|---|---|
| `phtree` | Author-maintained C++ PH-tree multimap | IDs | Native insertion; duplicate coordinates retain distinct IDs |
| `pgm_multidimensional` | Multidimensional PGM-index, epsilon 64 | Decoded integer points | Native Morton sorting and PGM construction |
| `psi_kd` | SpaceTreeLib k-d tree | Native augmented points | Native build, max-stretch/object-median split |
| `psi_orth` | P-Orth tree | Native augmented points | Native build, rotate-dimension/spatial-median split |
| `psi_spac_z` | SPaC-Z tree | Native augmented points | Native Morton-based build |
| `psi_spac_h` | SPaC-H tree | Native augmented points | Native Hilbert-based build |
| `lsi_linear` | libspatialindex linear R-tree | IDs | Native insertion |
| `lsi_quadratic` | libspatialindex quadratic R-tree | IDs | Native insertion |
| `lsi_rstar` | libspatialindex R-star tree | IDs | Native insertion |
| `lsi_str` | libspatialindex STR-packed R-tree | IDs | Native STR bulk loading |

libspatialindex uses its in-memory storage manager, capacities 16, and fill factors
0.5 for linear/quadratic and 0.7 for R-star/STR. Its floating-point boxes exactly
represent uint32 coordinates. SpaceTreeLib is compiled with its supported
`PARLAY_SEQUENTIAL` configuration for the single-core comparison. Its augmented
point records retain upstream curve-code/ID fields. PSI k-d tree is a separately
identified implementation/version, not a new algorithm distinct from Pkd.

The defaults include these entries in newly prepared static 2D/3D and small 2D
campaigns. Existing prepared manifests and completed measurements are unchanged.
They have not yet been added to higher-dimensional or dynamic campaigns.

## Build and validate

On Linux, including WSL:

```sh
git submodule update --init --recursive
python3 tools/build_additional.py
python3 tests/check_additional_competitors.py
```

The build writes four backend executables under `build/dimensional/` and retains
per-backend logs. It uses the pinned libspatialindex source, not a system package.
The shared library is included in benchmark dependency fingerprints. The main
Arch build invokes this additional build too. BMI2 is required for PGM. Upstream
SpaceTreeLib recommends GCC 14 or newer; the adapters also built with GCC 13.3 in
the recorded local validation. No upstream source was edited to make them build.

## Validation and limitations

The initial local validation uses exhaustive answer-multiset checks and separate
timed-mode answer-count checks in 2D and 3D: uniform, clustered and duplicate data,
small and full-width coordinates, disk boundaries, empty inputs and singletons.
Nine entries pass all 36 process runs each (18 cases, each checked and timed).
These are adapter checks, not campaign performance measurements.
The [validation record](../config/additional-validation.json) records outcome
counts, compiler version and binary hashes. Twenty additional checks exercise
the actual campaign routes, output files, metadata and dependency fingerprints.

PGM is included with explicit limitations. Its original constructor requires
coordinate bit widths strictly smaller than `floor(64/d)`: at most 31 bits per
coordinate in 2D and 20 in 3D. Full uint32 inputs are reported as
`unsupported_input`; coordinates are not truncated or rescaled. On supported-width
tests all nonempty cases pass in both dimensions; the original API crashes on
empty-input queries. The validation command therefore currently exits nonzero.
The full report is `build/dimensional/additional-validation.json`. Do not describe
this entry as validated for unrestricted inputs or include failed results in
performance claims. The final PGM totals are 16 passing runs, 16 unsupported runs
and four empty-input crashes.

SPaC's native 3D curve encoders use 21 bits per axis, although point records retain
the full coordinates. The full-width validation passed, but curve collisions may
affect its performance. The adapter does not replace the encoder or change the data.

The current SpaceTreeLib revision is the authors' maintained release, which their
README describes as an AI-assisted refactor of their original prototype. It is
not our adaptation. Its measurements must identify this exact revision rather
than be presented as reproductions of the paper's prototype timings.

## Source available, integration blocked

The original [Packed-Memory Quadtree](https://github.com/cicerolp/pmq) is included
unchanged as `src/third_party/pmq`. Its build requires a separate `pma_cd` build
tree and `pma-exports.cmake`; this dependency is not supplied in that repository
and a verified original source for it has not been located. PMQ is not counted
among the runnable entries. No substitute packed-memory array was written.

The previously added Sugiura–Ishikawa PostgreSQL source remains available as a
submodule; its database integration is still pending. It is not counted among
these ten entries.

See [third-party credits](THIRD_PARTY.md#additional-original-implementations)
for source URLs and [the revision record](../config/additional-sources.json) for pins.
