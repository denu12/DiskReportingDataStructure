# Static3D

Part of the [Static 3D theater](../../README.md). This campaign defines **100 instances**.

Four million points; distribution and target-output suites; five seeds.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/Static3D/campaign.json`; measured results live in `results/Static3D/<run>/<phase>/`.

Use `python run_theater.py static-3d` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.

Query centers are uniform and, for nonuniform inputs, also distribution-matched. Every distribution/centre pair is tested at target outputs 1, 100, 1,000 and 10,000. This gives 20 combinations per seed: uniform/uniform, normal/uniform, normal/matched, skew/uniform and skew/matched, each at four output sizes. The existing distributions suite retains target 1,000; the selectivity suite covers the other three targets for all distributions. Uniform/matched is omitted because it duplicates uniform/uniform. Independent pilot queries calibrate the radius; the manifest records the calibration and measured counts remain authoritative.
