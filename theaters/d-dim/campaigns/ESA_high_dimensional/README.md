# ESA_high_dimensional

Part of the [D-dimensional imported workloads theater](../../README.md). This campaign defines **30 instances**.

Dimensions 96, 100, 128, 784 and 960.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/ESA_high_dimensional/campaign.json`; measured results live in `results/ESA_high_dimensional/<run>/<phase>/`.

Use `python run_theater.py d-dim` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
