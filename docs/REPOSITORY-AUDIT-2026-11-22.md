# Repository audit — 22 November 2026

Audited the published disk baseline `9c47b9e` against its source, definitions,
documentation and November 22 measurement snapshot. The companion square
baseline was `72975eb`. Documentation corrections are separate from the
recorded experiment versions. No algorithm or active Archie job was changed.

## Source-integration follow-up

The source and scheduling gaps below have been addressed after the audit:

- The ten pinned Indexicon variants and native f64 exact dimensional SPRK bridge
  are integrated, with build tools and capability-aware campaign definitions.
- The newer disk adapters and controllers are preserved in the
  [frozen source collection](../reproducibility/2026-11-22/README.md), with original
  and published hashes, notices and explicit build/materialization helpers.
- Screening timeouts suppress final runs; final timeouts suppress remaining
  repetitions. Errors isolate the affected pair. Incorrect outputs remain timed
  under the explicit policy. A failed phase pauses its campaign while others finish.
- Current rosters are 50 2D, 41 3D and up to 40 dimensional configurations.
  Historical roster counts and raw measurements are unchanged.

The baseline findings below are retained as audit history, not current missing-source claims.

## Source-integration validation

- 12 Python policy/roster/publication tests passed, including concurrent repeat
  suppression, incorrect-output timing and continuing after a failed campaign.
- 365 Indexicon oracle, bench and dispatch checks passed across all 22 compiled
  dimensions, including 784D and 960D.
- 84 exact native-f64 SPRK checks passed across 21 dimensions.
- Nine parity-profile and six PH/PSI-profile binaries were built locally; 72
  frozen-adapter oracle/bench consistency checks passed on boundary fixtures.
- All 258 frozen source hashes verified. The checked-in algorithms and captured
  native headers were not repaired to change their outputs. Active experiments
  and historical measurement bundles were not modified.
- The complete original disk Bazel/dependency matrix was not rebuilt; these
  targeted checks do not certify historical rankings.

## Findings at the audited baseline

### High: the latest measurement snapshot is not fully reproducible from this checkout

The snapshot contains Indexicon runs, later disk adapters and the newer
`esa_sprk_RUST_EXACT_DDIM` driver. This baseline has no Indexicon integration
and does not register that newer SPRK driver in [workloads.py](../tools/workloads.py).
Several runs were produced by separate frozen Archie workspaces/controllers.
The exporter excludes those workspaces and Python source; publishing result
artifacts and hashes alone does not supply their implementation.

Preserve and publish the corresponding adapters, controllers, dependency pins
and source identities before claiming that this checkout reproduces those runs.
This is a source-publication gap, not evidence that the recorded timings are
wrong. Historical labels must continue to identify their actual contracts.

### High: public scheduling differs from the requested timeout/failure policy

In [the imported runner](../tools/esa/run.py), the default
`measure_failed_correctness=true` also selects failed screening rows for final
measurement. Its schedule contains all three final repetitions without a
per-pair timeout suppression set. The [synthetic runner](../tools/run.py) likewise
does not implement the newer skip-after-timeout behavior. A timed-out pair can
therefore be retried despite the newer request to stop its repetitions.

The [public theater controller](../run_theater.py) also stops the theater on a
nonzero phase-controller exit. The recent custom queue's behavior of recording
a failed case and continuing other cases is not fully integrated here.

Publish and validate that orchestration policy separately from the algorithms.
The live follow-up queue remains on its existing custom controller and was not
changed by this audit.

### Existing source-permission question

The pre-existing Chan/STANN permission issue remains recorded in
[publication status](PUBLICATION.md). This audit does not resolve it or supply
a new license assessment.

## Documentation corrections

- The root README now starts with the November 22 snapshot and distinguishes
  captured status from live status and checked-in code from later workspaces.
- Checked-in roster counts are **41 2D, 35 3D, 24 d-dimensional and 3 dynamic**.
  The previous lower counts omitted the PostgreSQL entry.
- The theater index now reports **295 static** and **195 static-3d** instances,
  matching the definitions, rather than 180 and 80.
- The protocol now describes the actual failed-screen and repeat behavior;
  it no longer promises selection only from successful screening by default.

## Validation of the original audited baseline

- Eight existing roster/publication unit tests passed under local Ubuntu WSL.
- All five theater previews ran successfully; definition totals are 295 static,
  50 small, 195 static-3d, 279 d-dimensional and 90 dynamic instances.
- First-party Markdown links were checked against repository paths and
  submodule roots. Disk links passed; four inherited square links were corrected
  in the companion working copy.
- The published snapshot's verification record reports 352 verified bundles,
  808,176 artifacts, no unreadable source files and no credential-pattern findings.
- This audit did not rebuild the complete disk Bazel/Rust dependency graph,
  rerun publication benchmarks, certify every historical output, or establish
  comparability between different implementation revisions.
