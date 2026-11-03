# Measurements captured on 3 November 2026

The snapshot contains **743,947 recorded files** in **308 bundles**, totaling **93.5 MB** compressed. The phase summaries contain 333,418 rows, including historical and overlapping records; this is not a count of independent successful measurements.

The primary Archie export was captured between **08:45:49 and 08:46:52 UTC**. Local historical export, tuning and validation records were added separately; the index records their capture time. See [index.json](index.json) for counts, SHA-256 hashes and phase summaries, and the [format description](../README.md) for reading bundles.

| Source | Contents |
|---|---|
| `current` | Archie's result directory: campaign states, job logs, execution policies and queue/provenance records |
| `historical` | Earlier relocated measurements, including retired algorithm variants and unsuccessful runs |
| `earlier-export` | The retained October 12 export and its summaries; these overlap with primary records |
| `tuning` | Historical Morton tuning measurements |
| `sprk-validation` | Historical SPRK boundary/output verification |
| `archived-validation` | Text validation records retained in earlier archives; input binaries and source archives excluded |

The original 2D/3D campaigns, additional-competitor campaigns and reporting-adaptation campaigns have finished. PostgreSQL's replacement campaign is still running: its completed 2D, 3D and small-theater records and partial d-dimensional records are included. The later coverage-completion queue is waiting for PostgreSQL. Its future measurements are not in this snapshot.

The older PostgreSQL attempt was interrupted and includes infrastructure failures. It is retained as history and must not be substituted for the replacement campaign. Older Morton/SPRK ablations also remain historical, regardless of today's roster.

These bundles publish recorded evidence, not a claim that every scheduled case succeeded or that all observations are comparable. Use source identities, phase status and correctness fields when selecting results. Files created after the capture interval require a later snapshot. Private manuscripts, correspondence, raw input datasets, executables and build caches are not included.
