# Third-party credits

## Sugiura–Ishikawa Z-ordered range refinement

Kento Sugiura and Yoshiharu Ishikawa, *Z-ordered Range Refinement for Multi-dimensional Range Queries* (2023): [paper](https://arxiv.org/abs/2305.12732), [original source](https://github.com/dbgroup-nagoya-u/psql-refine-z-range).

The original source is included unchanged as the Git submodule `src/third_party/psql-refine-z-range`, pinned to `5162f8700a150cdb0dba77159c5cc9b6bbb47a82`. Run `git submodule update --init src/third_party/psql-refine-z-range` after cloning this repository. No C++ translation or replacement implementation has been added.

Upstream provides PostgreSQL PL/pgSQL functions, including `GetNextJumpIn`, `GetNextJumpOut`, `RefineZOrderRange`, and `LoosenZOrderRange`, plus pgTAP tests and installation scripts. `RefineZOrderRange` returns Z-order interval endpoints, rather than materialized distance-query answers. It limits the combined coordinate encoding to 63 bits. The `postgres_zrange` integration preserves the original functions and retains full input coordinates alongside coarser index cells. See [PostgreSQL integration](POSTGRESQL.md) for key precision, exact filtering and timing.

Status: original source acquired; no benchmark runner, correctness validation, or timings yet. This is not an additional measured competitor. The pinned upstream revision contains no explicit license file; this project's license does not apply to it.

External source retains its original copyright and license notices. The project license does not replace them. Bazel revisions and hashes are in `src/MODULE.bazel`; Rust versions are in `src/third_party/esa2026/Cargo.lock`; Python versions are in its `python-requirements.txt`.

| Entries | Upstream credit and source |
|---|---|
| Boost linear/quadratic/R-star, static and dynamic | [Boost.Geometry](https://www.boost.org/libs/geometry/) contributors |
| CGAL range tree and k-d tree | [CGAL](https://www.cgal.org/) contributors |
| THST quadtree/R-tree, static and dynamic | [THST](https://github.com/tuxalin/THST), upstream authors |
| PAM | [PAM](https://github.com/cmuparlay/PAM), Parlay research group |
| Pkd-tree, static and dynamic | [Pkd-tree](https://github.com/ucrparlay/Pkd-tree), upstream authors |
| ParGeo | [ParGeo](https://github.com/wangyiqiu/pargeo), upstream authors |
| `chan_sss`, `chan_sss_dyn_ADAPTED_DYNAMIC` | [Timothy M. Chan's SSS technique](https://tmc.web.engr.illinois.edu/sss.pdf) |
| `ann_fr` | [ANN](https://www.cs.umd.edu/~mount/ANN/), David M. Mount and Sunil Arya |
| `stann_fr` | [STANN](https://github.com/charlesmcclendon/stann-for-python), Michael Connor and Piyush Kumar |
| SPRK | Vendored SPRK authors; revision in `src/third_party/esa2026/NOTICE.txt` |
| Kiddo, static and mutable | [Kiddo](https://github.com/sdd/kiddo), Scott Donnelly and contributors |
| Nabo, Neighbourhood and Acap/vantage-point tree | Respective crate authors; sources pinned by Cargo.lock |
| Orthtree and grid | [rembed](https://github.com/wembed-pdf/rembed), upstream authors |
| scikit-learn k-d and ball trees | [scikit-learn](https://scikit-learn.org/) developers |
| SNN | SNN authors; vendored source and SNN-LICENSE |
| nanoflann, static and dynamic | [nanoflann](https://github.com/jlblancoc/nanoflann), José Luis Blanco and contributors |

ESA workloads come from [rembed](https://github.com/wembed-pdf/rembed), commit `a81b216a2a63bde3d4447e4053b4ca31081fe286`, and [Zenodo record 21243483](https://zenodo.org/records/21243483). The MIT notice is retained in `src/third_party/esa2026/REMBED-LICENSE`.

The detailed vendored `NOTICE.txt` files are authoritative modification records. Chan and STANN are locally adapted for reporting. Chan's dynamic treap is a local dynamization, not recovered upstream dynamic code. ANN uses a timed reporting adapter around `annkFRSearch`.

Existing Kiddo, grid and Neighbourhood repairs predate the no-repair experimental policy and remain disclosed; these are not untouched upstream binaries. The audit repair corrects local adapter defects; see [audit resolution](AUDIT-RESOLUTION.md). Static 2D and dimensional Grid receive the arithmetic mean declared query radius, with normalized width .001 only as its empty/zero-radius fallback. Other fixed tuning is disclosed in the adapter notices; true per-query answer counts are not supplied as hints. ANN's two-pass reporting work is timed.

Chan's original source and the recovered STANN mirror did not include explicit license grants. Their notices retain that fact; no project license is asserted over them. Other dependencies include Abseil, protobuf, GMP, Google Benchmark, GoogleTest, Parlay and build tools; licenses remain in their distributions. Required inherited utility notices remain in source, and the inherited harness notice is preserved in `src/third_party/LEGACY-NOTICES.txt`.

## Experimental use

Current original-API policy, labels and native output contracts are specified in
[ORIGINAL-CAMPAIGN.md](ORIGINAL-CAMPAIGN.md); it supersedes older adaptation notes
below. New implementations are documented in [ADDITIONAL-COMPETITORS.md](ADDITIONAL-COMPETITORS.md).

Current workload membership is listed in the [theater index](../theaters/README.md). Prepared manifests identify candidate configurations; ordinary-workload correctness and dimension support determine which jobs proceed. The dimensional scan control is included; it has no construction normalization ratio. GPU comparisons are excluded.

The two local SPRK configurations compare coordinate reporting with an explicitly labelled IDs-only diagnostic. See the [reporting contract](REPORTING.md) for the timed-work distinction and the limits of comparing these runs with the source paper. Upstream READMEs and licenses are preserved as third-party documents; they do not describe this project's orchestration policy.

Publication labels and modification categories are specified in the [adapter catalog](ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.

## MortonPlus and retained SPRK source revisions

Morton (plus) is the C++ translation in `src/morton/2d/mortonplus.hpp` of the ESA
authors' MortonPlus algorithm, Rust implementation by Dennis Kobert. Credit:
Thomas Blasius, Jean-Pierre von der Heydt, Tobias Kempf, Dennis Kobert and Nikolai
Maas, authors of *Benchmarking and Engineering Data Structures for Spherical
Range Queries* (ESA 2026). The port does not claim invention of MortonPlus.
Upstream source: https://github.com/TrueDoctor/DiskReportingDataStructure/tree/morton-plus
Revision: `7e6f57558ca6ae8b93a3ca0f64a2d1b0ec579097`. The original MIT license
notice (copyright 2026 Ivor van der Hoog) is retained in the header.

SPRK (adapted) vendors `integer_reporting.rs` from
https://github.com/TrueDoctor/DiskReportingDataStructure/tree/sprk-exact-point-reporting,
revision `6ee75fdbd33ecb3d4014b99c5036509b6a7c9f97`. It uses their default
`IntegerPointSprk`; the upstream SPRK MIT license, copyright 2026 wembed-pdf,
and authors Dennis Kobert and Tobias Kempf are retained. The campaign driver is
local integration code. The old local integer adapter has been replaced, not
renamed as the authors' implementation. The Rust MortonPlus implementation is
not vendored as an active competitor.

## Additional original implementations

All five repositories below are unmodified Git submodules. The superproject's
gitlinks and `config/additional-sources.json` record exact revisions. Their
licenses and notices remain inside the upstream repositories.

| Source | Credit | License | Use |
|---|---|---|---|
| [PGM-index](https://github.com/gvinciguerra/PGM-index) | Paolo Ferragina and Giorgio Vinciguerra; multidimensional implementation in the authors' library | Apache-2.0; bundled components retain their notices | Original multidimensional range API; restricted coordinates and failed checks documented |
| [PH-tree C++](https://github.com/tzaeschke/phtree-cpp) | Tilmann Zäschke; derived from Improbable's implementation. PH-tree research: Zäschke, Zimmerli and Norrie, SIGMOD 2014 | Apache-2.0 | Author-maintained multimap, native IDs |
| [SpaceTreeLib](https://github.com/ucrparlay/SpaceTreeLib) | Ziyang Men, Bo Huang, Yan Gu and Yihan Sun, Parallel Dynamic Spatial Indexes, PPoPP 2026; Men, Shen, Gu and Sun, Parallel kd-tree with Batch Updates, 2025 | MIT plus upstream third-party notices | Maintained authors' k-d, P-Orth, SPaC-Z and SPaC-H implementations |
| [libspatialindex](https://github.com/libspatialindex/libspatialindex) | Marios Hadjieleftheriou and contributors | MIT, with upstream licensing history retained | Native linear, quadratic, R-star and STR-packed R-trees |
| [PMQ](https://github.com/cicerolp/pmq) | Júlio Toss, Cícero A. L. Pahins, Bruno Raffin and João L. D. Comba, Computers & Graphics 2018 | GPL-3.0 | Original source included; missing external `pma_cd` dependency blocks integration |

SpaceTreeLib's nested Parlay and libmorton repositories are initialized at the
revisions specified by its own gitlinks. Benchmark adapters are separate from
upstream code. The PH-tree C++ fork and maintained PSI revision are identified
explicitly; neither is represented as the exact historical paper artifact.
## November 2026 source integration

[Indexicon](https://github.com/psimatis/Indexicon-Spatial-Library) is vendored at
`69da8a364f3437a1110d89b9ebeb99473dc25807`, with unchanged upstream headers and
its [MIT license](../src/third_party/indexicon/LICENSE). The project supplies the
range-query adapters and exact disk/ball filtering; see [integration details](INDEXICON.md).
The later frozen PSI/Indexicon disk-aware traversal profiles contain disclosed
local traversal modifications and are kept separate from that native-box baseline.

The added native f64 dimensional SPRK bridge calls the existing SPRK tree and
performs exact integer filtering and coordinate materialization in query timing.
It is a separate adapter, not a new upstream SPRK release or the original
floating-contract IDs-only diagnostic. Existing SPRK authorship and licenses apply
to the tree; the bridge and [frozen harness sources](../reproducibility/2026-11-22/README.md)
retain their individual provenance.
