# dynamic-circles

Part of the [Dynamic 2D theater](../../README.md). This campaign defines **90 instances**.

45 phased and 45 interleaved workloads; n = 10k, 100k and 1m; update fractions 0.1, 0.5 and 0.9; five seeds.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/dynamic-circles/campaign.json`; measured results live in `results/dynamic-circles/<run>/<phase>/`.

Use `python run_theater.py dynamic` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
