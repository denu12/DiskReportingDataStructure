> Current policy: [original implementations and native outputs](ORIGINAL-CAMPAIGN.md). Correctness failures are recorded but do not suppress measurements in this campaign. Older adaptation descriptions below describe historical runs.

# Reporting contract and comparison with the source paper

The task is range reporting with native output. Non-SPRK implementations may report points or individual indices using their normal API; duplicate occurrences must be preserved. Counts alone are not reporting. SPRK keeps its existing configurations and membership contracts. The root README lists the actual output of every retained implementation.

## Timed work

Query timings include traversal, membership predicates, necessary geometric filtering, allocation and native output materialization. Non-SPRK index outputs do not undergo a timed conversion to point coordinates. Verification may resolve indices or convert native point types after timing. Dimensional Boost writes directly to a reusable vector of its native point type. Input loading and the independent oracle are not query time. This supersedes the earlier mandatory-coordinate output policy; historical measurements are unchanged.

The code's upstream behavior and this project's wrapper behavior must be distinguished. Native APIs may use floating-point coordinates, strict radius comparisons or different duplicate conventions. A failure against our exact integer contract does not establish a defect under that library's own contract.

## The two SPRK configurations

| Local configuration | Output inside query timing | Interpretation |
|---|---|---|
| SPRK (adapted) | Original integer point coordinates | Coordinate-reporting comparison. |
| SPRK (original) | Materialized point IDs | Diagnostic with a different output contract; coordinate lookup for verification is outside timing. |

The diagnostic identifier remains `esa_sprk_CHEATING_IDS_ONLY` solely to preserve machine-readable run provenance; its display name is **SPRK (original)** and its contract is `point_ids_only`. The conforming identifiers are `esa_sprk_RUST_EXACT` in 2D and `esa_sprk_RUST_EXACT_3D` for our new 3D extension of the authors' Rust adaptation; our former dimensional exact SPRK wrapper is retired. Historical measurements used different adapters and must retain their original source identity.

**SPRK (adapted)** uses the ESA authors' Rust IntegerPointSprk: the f32 tree conservatively selects leaf ranges, then integer leaf predicates and bulk writes materialize exact original coordinates inside timing.

**SPRK (original)** deliberately restores the earlier f64 tree (width 8) and native floating-point radius search in both 2D and dimensional adapters. Coordinates are normalized by 2^32. Its search radius is sqrt(integer squared radius / 2^64 + 64 * f64 epsilon). Timing includes traversal, floating-point predicates, and writing individual IDs into a reusable vector. It excludes original-point lookup, exact integer membership filtering, and coordinate materialization. It returns individual IDs, not intervals or subtree handles. The f64 precision and numerical margin are local adapter choices; this diagnostic mirrors the lighter ID-reporting interface and does not claim to reproduce the paper's f32 configuration or published timings.

The word **cheating** labels our deliberately relaxed local benchmark contract; it does not allege misconduct by the upstream authors. This diagnostic can disagree with closed integer geometry at boundaries. Ordinary and boundary/duplicate admission validate the diagnostic against an independent scan of its declared expanded f64 ball, including duplicate multiplicity. The same admission queries also compare its output with exact integer geometry and record `integer_mismatch_queries` during admission (benchmark mode does not run the oracle); these expected contract differences do not exclude this deliberately relaxed diagnostic. A failure under its declared floating contract still excludes it. Answer counts are compared across repetitions/phases within the same membership contract; floating diagnostic counts are not required to equal integer-reporting counts. No reported IDs are silently corrected.

This revision requires fresh measurements. The completed audited run used **SPRK (IDs only)** with timed integer filtering; its frozen source, labels and measurements retain that meaning and must not be relabelled as SPRK (original).

The f32 margin covers coordinate quantization and distance arithmetic. Higher-dimensional projected/dot-product kernels additionally need an absolute cancellation allowance. Static double-coordinate adapters use a radius-relative margin and outward rounding, except cancellation-based SNN. Exact integer filtering removes excess candidates; it cannot restore a missed candidate. Boundary admission therefore remains mandatory under each entry's declared membership contract. The remaining ESA wrappers retain their disclosed f64 adaptation so uint32 coordinates are represented exactly; they are not claimed to reproduce upstream f32 binaries.

## Normalization

SPRK (original) is eligible to set the query normalization baseline, despite its
separately disclosed ID-reporting contract. For a graph, choose one reference by
geometric-mean query time across all plotted x-coordinates and divide every
algorithm by that reference at each coordinate. Show only the best-average Boost
variant in graphs. Tables normalize each row to its fastest displayed result.
Use common successful cases and disclose missing coverage. Scan controls never
set the construction baseline and have no construction ratio.

## Why paper results can differ

The source paper is cited in the [root README](../README.md). These experiments change several things: the common integer grid, the output contract, the wrapper configuration, the compiler/environment and the bounded timing protocol. These differences prevent a direct claim that normalized results reproduce or refute the original paper.

The [workload guide](ESA-WORKLOADS.md) records float32 parsing, isotropic scaling, radius conversion and retained dataset selections. [Third-party notices](THIRD_PARTY.md) record local changes. Grid receives the mean declared query radius in both 2D and dimensional campaigns. ANN counts and retrieves results in timed passes through its native API. No true answer count is supplied to an index as advance knowledge.

When sharing a discrepancy, include the run label, instance ID, input and binary hashes, adapter identifier, reporting contract, compiler flags, CPU settings, and raw output. Separate conforming results from diagnostics and disclose exclusions. Preserve unsuccessful outcomes rather than assigning them invented timings.

Publication labels and modification categories are specified in the [adapter catalog](ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
