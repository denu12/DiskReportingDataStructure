# Competitor labels and adaptations

Use the display names below in every table and plot. Machine IDs are stable selectors,
not publication labels. The canonical mapping is `tools/algorithm_labels.py`.
Prepared manifests and outcome rows record `display_name`, `provenance`,
`source_repairs` and `output_contract`; `tools/collect.py` exports these columns.

`(adapted)` means our integration changes the interface to the integer point-reporting
contract. It does not necessarily mean the upstream index or search was modified.
The provenance column distinguishes a local implementation of a published technique,
modified upstream source, and an upstream index used through our adapter. Historical
`UPSTREAM` IDs denote the index's origin, not the absence of a local adapter.
SPRK (cheating) retains its separate, explicitly relaxed IDs-only label.

Kiddo, Grid and Neighbourhood have previously applied source repairs. Their names
still end in `(adapted)`; `source_repairs=true` and the notices disclose the repairs.
No new competitor correctness repairs are part of this adapter cleanup.

## Current mapping

| Machine ID | Display name | Provenance |
|---|---|---|
| `Morton` | Morton | local implementation |
| `MortonSIMD` | MortonSIMD | local implementation |
| `Morton3D` | Morton3D | local implementation |
| `morton_d_dim` | MortonDDim | local implementation |
| `naive` | Brute force | local implementation |
| `brute_force` | Brute force | local implementation |
| `boost_lin` | Boost linear (adapted) | upstream index with local adapter |
| `boost_quad` | Boost quadratic (adapted) | upstream index with local adapter |
| `boost_star` | Boost R-star (adapted) | upstream index with local adapter |
| `cgal_rt` | CGAL range tree (adapted) | upstream index with local adapter |
| `cgal_kd` | CGAL k-d tree (adapted) | upstream index with local adapter |
| `thst_quad` | THST quadtree (adapted) | upstream index with local adapter |
| `thst_rtree` | THST R-tree (adapted) | upstream index with local adapter |
| `pargeo` | ParGeo (adapted) | upstream index with local adapter |
| `pam` | PAM (adapted) | upstream index with local adapter |
| `pkd` | Pkd-tree (adapted) | upstream index with local adapter |
| `chan_sss` | Chan (adapted) | local implementation of published technique |
| `chan_sss_ddim_MANUALLY_ADAPTED` | Chan (adapted) | local implementation of published technique |
| `chan_sss_dyn_ADAPTED_DYNAMIC` | Chan (adapted) | local implementation of published technique |
| `ann_fr` | ANN (adapted) | upstream index with local adapter |
| `stann_fr` | STANN (adapted) | modified upstream source and local adapter |
| `stann_fr_ddim_MANUALLY_ADAPTED` | STANN (adapted) | modified upstream source and local adapter |
| `esa_sprk` | SPRK (adapted) | upstream index with local adapter |
| `esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS` | SPRK (adapted) | modified upstream source and local adapter |
| `esa_sprk_CHEATING_IDS_ONLY` | SPRK (cheating) | upstream index with local adapter |
| `esa_kiddo` | Kiddo (adapted) | modified upstream source and local adapter; prior source repairs |
| `esa_nabo` | Nabo (adapted) | upstream index with local adapter |
| `esa_neighbourhood` | Neighbourhood (adapted) | modified upstream source and local adapter; prior source repairs |
| `esa_vptree` | Acap VP-tree (adapted) | upstream index with local adapter |
| `esa_orthtree` | Orthtree (adapted) | upstream index with local adapter |
| `esa_grid` | Grid (adapted) | modified upstream source and local adapter; prior source repairs |
| `esa_sklearn_kd` | scikit-learn k-d tree (adapted) | upstream index with local adapter |
| `esa_sklearn_ball` | scikit-learn ball tree (adapted) | upstream index with local adapter |
| `esa_snn` | SNN (Python) (adapted) | upstream index with local adapter |
| `esa_snn_rust` | SNN (Rust) (adapted) | upstream index with local adapter |
| `esa_nanoflann` | nanoflann (adapted) | upstream index with local adapter |
| `boost_lin_dyn` | Boost linear (adapted) | upstream index with local adapter |
| `boost_quad_dyn` | Boost quadratic (adapted) | upstream index with local adapter |
| `boost_star_dyn` | Boost R-star (adapted) | upstream index with local adapter |
| `kiddo_mutable_dyn_UPSTREAM` | Kiddo mutable (adapted) | upstream index with local adapter |
| `nanoflann_dyn_UPSTREAM` | nanoflann (adapted) | upstream index with local adapter |
| `pkd_dyn_UPSTREAM` | Pkd-tree (adapted) | upstream index with local adapter |
| `thst_rtree_dyn_UPSTREAM` | THST R-tree (adapted) | upstream index with local adapter |
| `thst_quad_dyn_UPSTREAM` | THST quadtree (adapted) | upstream index with local adapter |

## Adapter costs removed

- Dimensional nanoflann (adapted) builds once, retains query buffers, requests
  unsorted radius hits and gathers coordinates directly into the final output.
  Its upstream floating-point membership predicate is unchanged.
- Dimensional Boost variants store point coordinates directly. The native query
  combines box pruning with our exact sphere predicate on the stored point;
  accepted coordinates are written directly to the final output. There is no
  bounding-box hit vector, intermediate ID vector or input-array lookup.
- 2D SPRK (adapted) uses its Rust coordinate vector as the final result. Every
  coordinate is explicitly written during the timed query. The bridge exposes
  that completed vector without a second coordinate copy. Its storage remains
  valid until the next query or index destruction. It is not a subtree handle,
  input slice or promise to enumerate points later.

These changes require fresh measurements. Do not relabel historical timings as
measurements of these optimized adapters. Upstream sources and modification
records are linked from [third-party credits](THIRD_PARTY.md).
