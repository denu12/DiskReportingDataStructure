# Selected current disk results, 23 November 2026

`disk-2d.json.gz` contains the explicit reviewed 2D selection: 17,250 supported
algorithm/workload pairs, with 16,566 complete three-repeat measurements and
684 terminal timeout outcomes. It includes the completed newer native-output
2D measurements that were not yet present in the 22 November capture. Each
case retains its selected run, version, contracts, correctness admission and
outcomes. There is no fallback to an older successful version after a timeout.

`higherdim-indexicon.jsonl.gz` and `higherdim-snn.jsonl.gz` contain the finished
Indexicon/nanoflann follow-up and SNN native-driver recovery, respectively,
after superseded records were removed. They do not include the still-running
newer-version Rust repair. Do not treat that repair as complete.

[index.json](index.json) records compressed and uncompressed SHA-256 hashes.
Local identities are redacted. The 2D artifact's row hashes describe published
redacted rows; `original_rows_sha256` identifies the original source rows.
The source artifact hash is retained in the
[selection profile](../../../config/result-selection-2d-20261123.json).

To validate the selection, decompress `disk-2d.json.gz` and run
`python3 tools/versioned_results.py /path/to/disk-2d.json` from the repository
root. Add `--csv` to export the selected observations, including failures and
correctness flags. A successful timed process does not prove correct output.

At the user's request, superseded older observations were removed from the
current 22 November snapshot as replacements became available. Git history
retains earlier commits; no history rewrite was performed. Raw states and
per-job records overlap, so record counts are not independent experiments.
