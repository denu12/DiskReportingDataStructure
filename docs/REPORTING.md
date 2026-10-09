# Reporting contract and comparison with the source paper

The task here is to list every original integer point inside or on a query disk or sphere. Coordinate multiplicity matters. Returning a count, a range descriptor, a batch handle or only point IDs is a different interface.

## Timed work

Conforming query timings include traversal, membership predicates, adapter filtering and materialization of the original point coordinates. Where a library returns IDs, looking up and writing coordinates is part of that wrapper's timed query. Allocation and conversion work performed inside that query are included. Input loading and the independent oracle are not query time.

The code's upstream behavior and this project's wrapper behavior must be distinguished. Native APIs may use floating-point coordinates, strict radius comparisons or different duplicate conventions. A failure against our exact integer contract does not establish a defect under that library's own contract.

## The two SPRK configurations

| Local configuration | Output inside query timing | Interpretation |
|---|---|---|
| SPRK (adapted) | Original integer point coordinates | Coordinate-reporting comparison. |
| SPRK (IDs only) | Materialized point IDs | Diagnostic with a different output contract; coordinate lookup for verification is outside timing. |

The diagnostic identifier remains `esa_sprk_CHEATING_IDS_ONLY` solely to preserve machine-readable run provenance; its display name is **SPRK (IDs only)** and its contract is `point_ids_only`. The 2D conforming identifier is `esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS`; dimensional coordinate-reporting SPRK uses `esa_sprk`. Historical measurements used different adapters and must retain their original source identity.

Both configurations now use the native **f32 SPRK SIMD candidate writer**, an outward numerical margin, and exact integer membership filtering inside timing. The conforming wrapper gathers and writes coordinates; the diagnostic writes individual accepted IDs. Reading coordinates for exact membership remains timed in both. Verification materializes the diagnostic's coordinates afterwards. Neither configuration returns a subtree handle or array interval. These timings remain distinct output contracts; runs from different batches also have different machine conditions.

The f32 margin covers coordinate quantization and distance arithmetic. Higher-dimensional projected/dot-product kernels additionally need an absolute cancellation allowance. Static double-coordinate adapters use a radius-relative margin and outward rounding, except cancellation-based SNN. Exact integer filtering removes excess candidates; it cannot restore a missed candidate. Boundary admission therefore remains mandatory. The remaining ESA wrappers retain their disclosed f64 adaptation so uint32 coordinates are represented exactly; they are not claimed to reproduce upstream f32 binaries.

## Why paper results can differ

The source paper is cited in the [root README](../README.md). These experiments change several things: the common integer grid, the output contract, the wrapper configuration, the compiler/environment and the bounded timing protocol. These differences prevent a direct claim that normalized results reproduce or refute the original paper.

The [workload guide](ESA-WORKLOADS.md) records float32 parsing, isotropic scaling, radius conversion and retained dataset selections. [Third-party notices](THIRD_PARTY.md) record local changes. Grid receives the mean declared query radius in both 2D and dimensional campaigns. ANN counts and retrieves results in timed passes through its native API. No true answer count is supplied to an index as advance knowledge.

When sharing a discrepancy, include the run label, instance ID, input and binary hashes, adapter identifier, reporting contract, compiler flags, CPU settings, and raw output. Separate conforming results from diagnostics and disclose exclusions. Preserve unsuccessful outcomes rather than assigning them invented timings.

Publication labels and modification categories are specified in the [adapter catalog](ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
