# dynamic-circles

See campaign.json for suites and parameters, and the root README for preparation and execution. --smoke creates small, labelled validation workloads. The correctness gate must pass before screening.

Reporting adapter revision (2026-10-07): dynamic nanoflann and Kiddo use the
requested circle directly, with one exact integer filter in the common harness.
The shared multiplicity adapter writes directly into the final point vector;
when points are distinct it performs no per-result multiplicity lookup. When
needed, duplicate occurrences are explicitly appended. The output vector and
nanoflann candidate capacity are reused across queries. All materialization,
expansion and filtering remain timed. Upstream index algorithms are unchanged.
Earlier measurements retain their old adapter overhead; use fresh run labels.

The publication roster contains nine external dynamic competitors. Our retired dynamic Morton variants are excluded.
