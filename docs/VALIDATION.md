# Publication validation — 7 October 2026

The publication tree contains exactly three project algorithms: `Morton`, `MortonSIMD` and `MoronSIMDearly`, each in one C++ source file. Retired static, dynamic, dimensional and Hilbert implementations are excluded. The competitor and control rosters contain 29 static entries (including the three Morton versions), nine dynamic entries and 20 dimensional entries.

Both native Arch runner configurations and the dimensional Chan/STANN adapter executable built successfully. The union of the native registries exactly matches the declared 29 static and nine dynamic entries, with no retired names. All 27 ordinary Morton validation runs passed, including full uint32 coordinates and million-point construction. The dimensional Chan/STANN adapters passed four additional ordinary checks across dimensions 2 and 3 after removing their dependency on the retired Morton header. This does not assert correctness of every competitor; existing ordinary-workload admission rules remain in force.

The scaling/static split preserves the original 50 workload definitions (20 plus 30); smoke preparation passed for both. The publication index passes the Git whitespace check and excludes generated datasets, results, binaries and retired research archives. No new regression-test suite was added. Docker was not rebuilt during this cleanup; the native Arch builds were verified.

Validation evidence is retained locally in `results/publication-20261007/`; binaries and hashes are under `bin/publication-20261007/`. Earlier performance results retain their original names and binaries.

---

# Publication validation — 6 October 2026

This is a historical validation record from before Hilbert was retired on
7 October 2026. Its variant names describe that earlier build, not the current
research roster. Retired research snapshots are kept outside the publication
repository; current builds and campaigns exclude them.

Both native Arch runners and the Rust bridge build successfully. The Arch-based container also builds from its pinned base image and fetched dependencies. Validation uses the scientific correctness protocol; no new regression-test suite was added.

| Campaign | Entries passing | Entries excluded |
|---|---:|---:|
| Static circles | 25 | 4 |
| Dynamic circles, including updates | 10 | 2 |
| ESA native-2D integer-grid adaptation | 35 | 6 |

All seven project variants pass: `hcds:best`, `hcds_hilbert:best`, `ehcds:best`, `ehcds_hilbert:best`, `hcds_dyn`, `hcds_hilbert_dyn`, `hcds_dyn_std`.

Native exclusions: `cgal_rt`, `pam` and `pkd` report incorrect results; `pargeo` fails on empty input; `pkd_dyn_UPSTREAM` crashes on the boundary fixture; `kiddo_mutable_dyn_UPSTREAM` rejects the collinear fixture. Their code was not repaired. Container static and dynamic gates produce the same eligibility decisions.

Additional native checks passed: 175 static workload checks, 60 dynamic stream checks, and 105 ESA checks (35 eligible entries across three imported families, each with 16 original queries and all training points). These are bounded validation workloads, not final performance results. All 50 ESA cases prepare successfully.

Raw logs, manifests, binary hashes and toolchain metadata are retained outside Git in `results/`. Gates must be generated again for each new build or changed harness; this document does not authorize timing with unverified binaries.
