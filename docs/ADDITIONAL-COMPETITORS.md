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
Higher-dimensional runs use the capabilities below and explicit campaign rosters.
Dynamic update streams are not wired to these adapters.

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

The Sugiura–Ishikawa PostgreSQL implementation is now integrated separately as
`postgres_zrange`; see [its adapter documentation](POSTGRESQL.md). It is not
counted among these ten C++ entries.

See [third-party credits](THIRD_PARTY.md#additional-original-implementations)
for source URLs and [the revision record](../config/additional-sources.json) for pins.

## Campaign coverage (22 October 2026)

The additional-competitor queue runs the static 2D, static 3D, small 2D and
higher-dimensional theaters: 14 campaigns and 819 existing input cases. It uses
separate manifests and result labels (`additional-<theater>-20261022`), with
checksums and references to the existing input files. Earlier measurements and
inputs remain unchanged. All stages have unlimited aggregate campaign budgets;
individual job timeouts and memory limits remain enabled. Runs use one CPU,
three final repetitions, and retain correctness failures as previously requested.

| Implementation | Dimensions enabled in these campaigns |
|---|---|
| PH-tree | 2–16, 32, 34; upstream hypercube positions use at most 64 bits |
| PSI k-d tree | 2–16, 32, 34, 96, 100, 128; upstream dimension type is 8-bit |
| P-Orth tree | 2–8; upstream default skeleton heights only cover these dimensions |
| SPaC-Z / SPaC-H | 2 and 3; upstream curve encoders support only these dimensions |
| Multidimensional PGM-index | 2 and 3, subject to the coordinate-width limits above |
| Four libspatialindex variants | All dimensions in the campaigns, through 960 |

These changes instantiate the upstream indexes in more dimensions; they do not
modify upstream search or construction code. PGM's existing adapter remains
limited to 2D/3D; its shrinking coordinate-width allowance also prevents using
the full-width coordinates of our higher-dimensional inputs without rescaling.
No rescaling is performed.

Validation on Archie exercised dimensions 2, 3, 8, 34, 128 and 960: 724 successful
checks, 16 unsupported-input outcomes and 16 process failures. Four failures are
PGM's previously observed empty-input queries; twelve are P-Orth in dimension 8.
The latter remains scheduled, with its failures recorded separately from valid
measurements. Full records and the queue scripts are retained under
`results/_queue-additional-all-20261022/` on the experiment machine.

The dynamic theater is not scheduled: these adapters consume static point sets,
not insertion/deletion streams. PMQ remains blocked as described above. PostgreSQL is integrated separately;
its measurements are kept under separate run labels.
