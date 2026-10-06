# Third-party credits

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

Existing Kiddo, grid and Neighbourhood repairs predate the no-repair experimental policy and remain disclosed; these are not untouched upstream binaries. Publication cleanup makes no competitor correctness repairs. Adapters retain fixed tuning, including normalized grid width .001; true per-query answer counts are not supplied as hints. ANN's two-pass reporting work is timed.

Chan's original source and the recovered STANN mirror did not include explicit license grants. Their notices retain that fact; no project license is asserted over them. Other dependencies include Abseil, Highway, protobuf, GMP, Google Benchmark, GoogleTest, Parlay and build tools; licenses remain in their distributions. Required inherited utility notices remain in source, and the inherited harness notice is preserved in LEGACY-NOTICES.txt.
