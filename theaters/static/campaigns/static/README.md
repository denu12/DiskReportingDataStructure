# static

Part of the [Static 2D theater](../../README.md). This campaign defines **30 instances**.

Four million points; distribution and radius suites; five seeds.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/static/campaign.json`; measured results live in `results/static/<run>/<phase>/`.

Use `python run_theater.py static` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
