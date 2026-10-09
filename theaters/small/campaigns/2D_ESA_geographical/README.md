# 2D_ESA_geographical

Part of the [Small: native 2D imported workloads theater](../../README.md). This campaign defines **28 instances**.

Seven original POI/query pairs, each at four radii.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/2D_ESA_geographical/campaign.json`; measured results live in `results/2D_ESA_geographical/<run>/<phase>/`.

Use `python run_theater.py small` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
