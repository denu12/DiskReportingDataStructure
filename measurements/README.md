# Recorded measurements

Dated snapshots preserve observations available at publication time. They include successful jobs, failures, partial runs, logs and provenance. Input datasets, binaries, private drafts and correspondence are excluded.

The [23 November reviewed selection](selections/2026-11-23/README.md) supplies
completed newer 2D measurements and the finished higher-dimensional follow-up.
At the user's request, superseded measurements have been deleted from the
current snapshot when a newer completed or timed-out replacement exists.
Earlier source/bundle hashes remain historical identities; pruned contents
have new content/bundle hashes and explicit pruning metadata.

- [3 November 2026](2026-11-03/README.md): historical capture with superseded observations removed where replacements exist.
- [22 November 2026](2026-11-22/README.md): refreshed current and historical results from Archie, with superseded observations removed where replacements exist.

Each snapshot contains an `index.json` and gzip-compressed JSONL bundles. Each line is an object with `path`, `original_sha256`, `original_bytes` and `content`. The path is relative to its named source. Content is the recorded UTF-8 text, with local home paths, host/user names and private IP addresses redacted. Original hashes describe the bytes before redaction; bundle hashes describe the published compressed files.

Read a bundle without unpacking a directory:

```python
import gzip, json
with gzip.open('measurements/2026-11-03/current/static/original-all-2d-20261015.jsonl.gz', 'rt') as f:
    for line in f:
        record = json.loads(line)
        if record['path'].endswith('/state.json'):
            state = json.loads(record['content'])
            print(record['path'], len(state.get('results', [])))
```

The index lists bundle hashes, record counts and phase summaries. State rows overlap with per-job records and sometimes with earlier snapshots: do not add them together as independent measurements. Retain correctness admission, reporting contracts, timeouts and unsupported cases in analyses. A successful timed process is not a correctness certificate. Historical algorithm labels and source identities are preserved rather than replaced by today's labels.

To export a fresh snapshot:

```sh
python tools/export_measurements.py --source current=results --source historical=historical_data/results --output measurements/YYYY-MM-DD
```

The exporter reads sources without modifying them and excludes inputs, build workspaces and binaries. Files are captured over an interval; this is not an atomic snapshot of a live campaign. Check the capture timestamps and each phase status before treating a run as complete. Do not mix runs with different source revisions, contracts or workload definitions into an unlabeled aggregate.
