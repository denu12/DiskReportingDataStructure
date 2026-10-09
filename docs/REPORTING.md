# Reporting contract and comparison with the source paper

The task here is to list every original integer point inside or on a query disk or sphere. Coordinate multiplicity matters. Returning a count, a range descriptor, a batch handle or only point IDs is a different interface.

## Timed work

Conforming query timings include traversal, membership predicates, adapter filtering and materialization of the original point coordinates. Where a library returns IDs, looking up and writing coordinates is part of that wrapper's timed query. Allocation and conversion work performed inside that query are included. Input loading and the independent oracle are not query time.

The code's upstream behavior and this project's wrapper behavior must be distinguished. Native APIs may use floating-point coordinates, strict radius comparisons or different duplicate conventions. A failure against our exact integer contract does not establish a defect under that library's own contract.

## The two SPRK configurations

| Local configuration | Output inside query timing | Interpretation |
|---|---|---|
| SPRK (adapted) | Original integer point coordinates | Coordinate-reporting comparison. |
| SPRK (cheating) | Materialized point IDs | Diagnostic with a different output contract; coordinate lookup for verification is outside timing. |

The diagnostic identifier is `esa_sprk_CHEATING_IDS_ONLY`, and its result contract is `point_ids_only`. The word cheating is our experimental label, **not an allegation about the upstream authors**. The 2D conforming identifier is `esa_sprk_MANUALLY_ADAPTED_INTEGER_POINTS`; dimensional coordinate-reporting SPRK uses `esa_sprk`. Private prior results may use a different reporting contract; retain run provenance when using them for correspondence or drafting.

IDs-only reporting still enumerates individual IDs. It does not merely return a tuple describing an array interval. Do not describe every timing difference between these configurations as coordinate-copying cost: the 2D wrappers also differ in integer adaptation and filtering. The 3D diagnostic uses the dimensional search engine with a different output materialization path. Runs measured in different batches can also experience different machine conditions.

## Why paper results can differ

The source paper is cited in the [root README](../README.md). These experiments change several things: the common integer grid, the output contract, the wrapper configuration, the compiler/environment and the bounded timing protocol. These differences prevent a direct claim that normalized results reproduce or refute the original paper.

The [workload guide](ESA-WORKLOADS.md) records float32 parsing, isotropic scaling, radius conversion and retained dataset selections. [Third-party notices](THIRD_PARTY.md) record local changes. The dimensional Grid configuration, for example, differs from the paper's mean-radius hint; ANN counts and retrieves results in timed passes. No true answer count is supplied as advance knowledge.

When sharing a discrepancy, include the run label, instance ID, input and binary hashes, adapter identifier, reporting contract, compiler flags, CPU settings, and raw output. Separate conforming results from diagnostics and disclose exclusions. Preserve unsuccessful outcomes rather than assigning them invented timings.

Publication labels and modification categories are specified in the [adapter catalog](ADAPTERS.md). Use **STANN (adapted)** and **Chan (adapted)** consistently across dimensions; machine IDs remain unchanged.
