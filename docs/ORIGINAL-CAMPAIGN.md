## Original-API campaign (15 October 2026)

The full competitor roster is restored: 30 entries in 2D and 24 in 3D, including
scan controls. Morton uses the retained implementations; SPRK stays as configured.
Other competitors use original search implementations and native outputs. Necessary
file-format and box-to-disk query plumbing is still part of this benchmark harness.
Original arithmetic, boundary conventions, duplicate behavior and bugs are not repaired.

| Competitor | Timed output |
|---|---|
| Morton / SIMD / Plus | Integer points |
| Boost linear / quadratic / R-star | Native points |
| CGAL k-d tree | Native floating-point points |
| CGAL range tree; THST quad/R-tree; Pkd | Native points, with box-to-disk filtering |
| ParGeo | Native indices into its stored point sequence |
| PAM | Native coordinate pairs from the original range-query example, with disk filtering |
| ANN | Native indices |
| nanoflann | Native index/distance pairs |
| Kiddo, Nabo, Neighbourhood, VP-tree, Orthtree, Grid | Indices from the original ESA wrappers |
| scikit-learn k-d/ball trees; Python SNN; Rust SNN | Indices |
| Brute-force controls | 2D points; dimensional indices |
| SPRK (original), unchanged | Indices |
| SPRK (adapted), including no-explicit-SIMD, unchanged | Integer points |
| Chan and STANN originals | No original range-reporting API wired here; explicitly unsupported, no adapted substitute |

The original ESA Rust search modules are included directly from the vendored
upstream source; their f32 arithmetic is retained. Kiddo uses the unpatched registry
crate. ParGeo/PAM use reconstructed pre-patch files whose Git blob IDs are verified.
No original radius-query result is filtered to force agreement with integer geometry.
PAM's original example uses signed int coordinates and its original reporting callback;
representation/boundary/duplicate discrepancies remain visible.

At the user's request, **failed correctness does not prevent timing**. Each timed
row carries `correctness_admission`, and count mismatches remain flagged. Success
of a timed process is not a correctness certificate. Crashes, timeouts and unsupported
queries remain explicit outcomes. Resource limits still apply. Old measurements
retain their previous contracts and are not relabeled as original-API results.
