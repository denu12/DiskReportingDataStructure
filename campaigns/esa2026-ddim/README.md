# ESA dimensional correctness campaign

Current policy: use only the 18 ordinary ESA dataset cases. Synthetic boundary,
duplicate, empty and collinear fixtures in older manifests are not run or used
to exclude algorithms. Historical results are retained as records of the old
policy; all 20 implementations start eligible in a fresh run.

Includes 20 entries: Chan, STANN, ANN, three Boost configurations, SPRK,
Kiddo, Nabo, Neighbourhood, VP-tree, Orthtree, grid, scikit-learn KDTree and
BallTree, original Python SNN, ESA Rust SNN, nanoflann, CGAL and brute force.
`chan_sss_ddim_MANUALLY_ADAPTED` and `stann_fr_ddim_MANUALLY_ADAPTED`
are local reporting adaptations;
see [the modification record](../../d-dim/MANUAL-ADAPTATIONS.md).
This is a bounded scientific correctness/crash experiment, not a
timing comparison or the full ESA performance matrix.

The campaign selects the smallest training file (by uncompressed bytes) in
each available embedding/distribution dimension from Zenodo record 21243483:
embeddings in 2–16 dimensions and distributions in 2, 8 and 32 dimensions.
All training points and 32 evenly spaced source queries are retained per
selected dataset. The common integer-grid conversion follows the 2D campaign,
generalized to d coordinates and a maximum squared distance of d*(2^32-1)^2.
Correctness is measured on that converted geometry, not the original floats.
Source hashes, selected query indices and conversion parameters are saved.

Each reported list of original point indices is compared
with an independent exact integer brute-force scan, including multiplicity.
Each case runs on one CPU, with four independent jobs at once, a 60-second
timeout and 16 GiB address-space cap per job. The total execution budget is
30 minutes, excluding preparation and compilation. A wrong answer or crash
on an ordinary dataset excludes an implementation from remaining
cases; two timeouts also stop its remaining cases. All outcomes are retained.
A finished run has `execution_finished: true` and status `needs_attention` if
anything failed.

On Arch, from the repository root, with the existing NumPy Python environment:

```sh
python tools/build_ddim.py
python tools/run_ddim_all.py --run correctness-YYYYMMDD --cpus 1,2,3,4
```

Use a fresh run name; existing results are never overwritten. Prepared
datasets are shared between algorithms. The earlier sequential runner
`tools/ddim_campaign.py` remains available for the two manually adapted entries;
use the expanded runner for the full roster.
Downloaded and prepared inputs are cached under `data/esa2026-ddim`; results are under
`results/esa2026-ddim/<run>/state.json` and per-case JSON files. The configuration
is `campaigns/esa2026-ddim/campaign.json`. This separate runner does not use or
alter the completed 2D performance runs or their shared budget ledger.

The expanded build uses the existing Arch setup, downloaded Bazel dependency
headers under `src/bazel-src/external`, the pinned Rust lockfile and the existing
NumPy/SciPy/scikit-learn environment. Set `OFFLINE=1` after Cargo dependencies
are cached. See [adapter details](../../d-dim/ESA-ADAPTERS.md) for numerical
conventions and differences from the paper's configuration.

The ESA source is [rembed](https://github.com/wembed-pdf/rembed), by the authors
of *Benchmarking and Engineering Data Structures for Spherical Range Queries*;
datasets: [Zenodo 21243483](https://zenodo.org/records/21243483).
