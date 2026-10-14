# input_scaling

Part of the [Static 3D theater](../../README.md). This campaign defines **60 instances**.

Uniform points: n = 100k, 500k, 2m, 4m, 6m, 8m, 10m, 12m, 14m, 16m, 18m, 20m; five seeds.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/input_scaling_3d/campaign.json`; measured results live in `results/input_scaling_3d/<run>/<phase>/`.

Use `python run_theater.py static-3d` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.

Radii are calibrated to a nominal 1,000 answers per query across input sizes. This separates index-size scaling from increasing output volume. Calibration uses independent pilot queries; actual answer counts are recorded.

The campaign folder is `input_scaling`; its unique execution ID is `input_scaling_3d` to keep 3D inputs and results separate from 2D.
