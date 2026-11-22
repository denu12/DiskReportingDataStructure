# Frozen Archie source collection

This collection preserves source used by the later disk experiments. It contains
the 2D disk adapters, parity adapters, PH/PSI 2D/3D follow-up, Indexicon workspace
drivers, native-output modules and the November 20/22 queue controllers.
It excludes input datasets, executables, build caches and measurements.

[source-manifest.json](source-manifest.json) records both the original file hash
and the published hash. Local paths are replaced by `@PROJECTS_ROOT@` and
`@HOME@`; no index arithmetic or search implementation was edited in these
captured files. Files retain their bytes in Git so line-ending conversion cannot
invalidate the published hashes. Upstream notices are retained in the source
and [LICENSES](LICENSES).

The parity and PH/PSI profiles contain earlier local changes to query traversal,
including PSI and Indexicon disk-aware traversal copies. They are **not** the
unmodified native-box-plus-filter Indexicon baseline now integrated under
`src/runner/dimensional/indexicon_adapter.hpp`. Keep these versions separate in
comparisons. Original labels and correctness failures in raw results are not
rewritten by this source publication.

## Verify and build without starting experiments

From the disk repository root:

```sh
python3 tools/materialize_frozen_sources.py
git submodule update --init --recursive src/third_party/phtree-cpp src/third_party/pgm-index src/third_party/space-tree-lib
python3 tools/build_frozen_adapters.py --profile ph-psi --algorithms phtree psi
python3 tools/build_frozen_adapters.py --profile parity --algorithms cgal_kd cgal_rt pam pargeo thst spatialindex indexicon_kdtree indexicon_quadtree indexicon_mxcif --square /path/to/SquareReportingDataStructure
```

Builds go to `build/frozen-adapters/<profile>/`. The helper uses the checked-in
submodule revisions, system CGAL/libspatialindex and the captured rectangle
dependencies from the square repository. It compiles selected backends only and
never starts a campaign. PGM's already documented reporting patch is prepared
in the build directory. ParGeo uses the square project's build-only Parlay API
compatibility qualification, leaving the captured dependency tree untouched.

The PH/PSI source also builds `indexicon_kd_3d`, `pgm_3d`, `lsi_3d` and
`cgal_kd_3d`. The earlier `2d` profile remains available for the November 14
implementations. Required development packages and headers must be installed;
the helper does not download dependencies or silently replace missing libraries.

## Captured controllers and old layouts

```sh
python3 tools/materialize_frozen_sources.py --destination /new/empty/directory --projects-root /path/to/Projects
```

This makes a separate copy with local path tokens expanded. It does not execute
the controllers. Their original queue names, prerequisite runs, frozen binary
locations and prepared-input layout remain explicit. Replaying one requires
reconstructing those workspaces and checksum-matching inputs; materialization is
not an automatic replay or a dataset download. The original project directory
was named `DiskRangeReport`; provide that layout or a local alias when rebuilding
old controllers. Never point a replay at an active results directory.

Fresh measurements should normally use the public harness, which now suppresses
repetitions after a timeout and isolates failed cases. Historical controllers
are preserved as evidence of their original scheduling policy, including older
policies that retried timeouts. Rebuilding with another compiler or changed
dependencies does not reproduce an old binary or certify an old timing.
