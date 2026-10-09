# ESA_clustering

Part of the [D-dimensional imported workloads theater](../../README.md). This campaign defines **25 instances**.

Dimensions 4, 5, 7, 13 and 34.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/ESA_clustering/campaign.json`; measured results live in `results/ESA_clustering/<run>/<phase>/`.

Use `python run_theater.py d-dim` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
