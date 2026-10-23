# Minimal reporting adaptations (23 October 2026)

Chan, STANN and PGM are explicitly labelled **adapted**; PAM is labelled **repaired**. Original source copies
and notices remain unchanged. Construction, candidate enumeration, exact ball
filtering and output materialization are included in the appropriate timers.
Chan, STANN and PGM return original point IDs, including distinct occurrences of duplicates.
PAM returns coordinate pairs and preserves duplicate occurrences.
Existing archived measurements still refer to their archived source snapshots.

## Chan

`chan_reporting.h` follows `sss-original.cc` directly. It retains qsort, the
shifted Morton comparator, drand48 and its original seed formula,
midpoint-first examination, distance-to-common-cell pruning and center-first
recursion. Fixed-radius reporting replaces nearest-neighbour selection.
Comparisons become inclusive to preserve boundary duplicates. Shift/cell
arithmetic uses uint64 and squared distances use unsigned 128-bit integers.
Query bounds are allocated once, as in the original. Radius bounds use sqrt
with exact integer rounding corrections. The approximation factor is one. The old locally reconstructed Chan class is
not used by these static campaign routes. Dimension is determined at runtime.

## STANN

The existing reporting additions to STANN are reused, with no further changes
to its source. Original paired serial sorting, Z-order comparisons, center-first
recursion and scans of fewer than four points remain. The nearest-neighbour
queue and shrinking radius are replaced by fixed-box reporting; candidates
receive an exact ball test. Integer cell-intersection pruning replaces the
original floating-point distance bound. Inclusive comparisons and an empty-input
guard handle boundary duplicates and empty sets. See the detailed STANN notice.
Compiled dimensions are 2 through 16, 32, 34, 96, 100, 128, 784 and 960.

## Multidimensional PGM-index

The original Morton encoder, sort, PGM model, range iterator and BIGMIN search
are retained. The constructor allows only `floor(64/d)-1` coordinate bits.
The adapter indexes cells obtained by shifting uint32 coordinates right;
it keeps all original coordinates for exact membership tests. Query endpoints
are shifted the same way, so candidate cells conservatively cover the query.
In 2D the shift is one bit; in 3D it is twelve bits. Collisions may increase
filtering work, especially in higher dimensions, but cannot change answers.
Every input occurrence gets a key, and a parallel sorted ID array maps each
iterator position to its original point. Creating and sorting that mapping is
included in construction time. No points are merged.

`tools/prepare_pgm_reporting.py` generates a patched header under `build/`,
leaving the pinned submodule untouched. Its four small changes are:

- Avoid dereferencing the end iterator after scanning.
- Handle an empty index before looking up a model segment.
- Use lower_bound at BIGMIN and resume examination there, preserving the
  inclusive target and all its duplicates without decrementing before begin.
- Expose the current sorted position for the original-ID mapping.

The generated unified diff is `build/pgm-reporting/reporting.patch`.
Compiled dimensions are 2 through 16 and 32. Beyond 32 dimensions the original
64-bit encoding has no usable coordinate bits under its constructor constraint.
The older unmodified adapter's unsupported outcomes are not new timing results.

## Validation and reproduction

```sh
python3 tools/build_additional.py --only pgm reporting pam
python3 tests/check_reporting_adapters.py
```

Local GCC 13.3 validation passed 410 process checks, covering dimensions
2, 3, 8, 16, 32, 34, 128 and 960 where supported. Each dataset runs both
full answer-ID comparison and timed-mode count verification. Cases cover
uniform and clustered points, duplicate coordinates, full uint32 values,
exact boundaries, empty sets, singletons and dense Morton intervals with
small query balls. Nine additional checks passed through the actual 2D/3D
campaign routes. PAM also passed 20 address/undefined-behaviour sanitizer checks (allocator leak
checking disabled for its persistent memory pools). These are correctness checks,
not performance measurements.

## PAM repairs

The original range-tree library remains unchanged. A generated patch to its
range-query example fixes a `(y,y)` output typo to `(y,x)`, includes an upper-bound
key in the count used to allocate the output buffer, and makes count storage
and the query-count return type `size_t`. The example point type now respects
its coordinate and weight template parameters; the adapter instantiates int64
coordinates, preserving the ordering of the full uint32 input range.

The original constructor, map representation, two-pass count/report query and
subtree range extraction are retained. Because the native map coalesces equal
coordinate keys, the adapter checks whether duplicates exist. Only if they do,
it builds a multiplicity map and expands reported coordinates accordingly.
This work is timed. Distinct-point queries incur no multiplicity hash lookup.
The original float weight type is retained; integer answer counts no longer
pass through a float return value. The ball filter uses exact integer distances.

`tools/prepare_pam_reporting.py` writes the patched example headers and a unified
diff under `build/pam-reporting/`. It uses the PAM revision already specified
in `src/MODULE.bazel`, `3574543ad84c34acb22edbeecb9d11a97a5eb87d`.
The builder finds dependencies in the existing Bazel tree or `build/` directories.
For a separate source checkout set `PAM_SOURCE` to the PAM root and
`PAM_PARLAY_INCLUDE` to the directory containing the pinned Parlay headers.
The queued rerun copies the exact dependency snapshot used by the earlier PAM
campaign and records source hashes. PAM's example applies only in 2D.

PAM's earlier failures cannot establish its performance: both the adapter's
signed coordinate conversion and the upstream example's reporting defects
invalidate those measurements. The rerun receives a fresh result label.
