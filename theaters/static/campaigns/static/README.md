# static

Part of the [Static 2D theater](../../README.md). This campaign defines **40 instances**.

Four million points; distribution and target-output suites; five seeds.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/static/campaign.json`; measured results live in `results/static/<run>/<phase>/`.

Use `python run_theater.py static` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.

Query centers are uniform and, for nonuniform inputs, also distribution-matched. Distribution cases target 1,000 outputs; selectivity cases target 1, 100 and 10,000. Independent pilot queries calibrate the radius; the manifest records the calibration and measured counts remain authoritative.
