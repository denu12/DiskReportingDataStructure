# scaling

Part of the [Static 2D theater](../../README.md). This campaign defines **40 instances**.

Uniform points: n = 10k, 100k, 2m, 4m, 6m, 8m, 10m, 12m; five seeds; radius 0.01 of grid width.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/scaling/campaign.json`; measured results live in `results/scaling/<run>/<phase>/`.

Use `python run_theater.py static` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
