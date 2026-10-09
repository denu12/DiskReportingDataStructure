# ESA_graph_embeddings

Part of the [D-dimensional imported workloads theater](../../README.md). This campaign defines **210 instances**.

Dimensions 3–16.

The versioned [campaign.json](campaign.json) is the authoritative workload definition. Prepared inputs and their checksums live in `data/ESA_graph_embeddings/campaign.json`; measured results live in `results/ESA_graph_embeddings/<run>/<phase>/`.

Use `python run_theater.py d-dim` from the repository root to preview the complete theater, or add `--run FRESH_LABEL --execute` to run it after preparation. The [theater README](../../README.md) documents preparation, roster constraints and workload interpretation.

Instance counts do not include algorithm configurations or final repetitions. Correctness failures, unsupported dimensions and unsuccessful screening pairs remain explicit outcomes; they are not successful measurements.
