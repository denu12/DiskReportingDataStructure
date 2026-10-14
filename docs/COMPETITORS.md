# Competitor rosters

The default action is to run every retained competitor. Correctness admission,
screening and dimensional support determine which pairs reach final measurements.
`tools/workloads.py` defines the canonical rosters; campaign definitions and
catalog generation use the same entries. Preflight rejects retired names,
duplicates, more than three Morton variants or more than two SPRK variants.

| Theater | Morton entries | SPRK entries |
|---|---|---|
| 2D static / small | Morton, Morton (simd), Morton (plus) | Original, authors' Rust adaptation |
| Static 3D | Morton3D, Morton (plus) | Original, local 3D extension of authors' Rust adaptation |
| d-dimensional | MortonDDim, Morton (plus, d-dimensional) | Original; 3D adaptation only where dimension is 3 |
| Dynamic 2D | None | None |

All unrelated competitors remain: Boost linear/quadratic/R-star, CGAL, ANN,
STANN, Chan, the retained ESA indexes, and the existing 2D parallel/dynamic
indexes where supported. Scan controls are included; they have no meaningful
index-construction ratio. No algorithm is disabled globally by default.

The C++ MortonPlus implementations credit the ESA authors. Rust MortonPlus and
our former old/fast SPRK adaptations are retired. Their historical result IDs
remain valid provenance, not active aliases. `esa_sprk_CHEATING_IDS_ONLY` is the
stable machine ID for SPRK (original); its display label no longer says cheating.

Morton and dimensional Plus support up to 16 dimensions. Original SPRK has
compiled dimensional adapters for 2-16 and 32; the authors-based exact adaptation
supports only 2D and 3D. Other dimensions retain every compatible external index.
No missing implementation is silently substituted.

## Running

After building and preparing fresh inputs, run:

```sh
python run_theater.py static --run all-static --execute
python run_theater.py small --run all-small --execute
python run_theater.py static-3d --run all-3d --execute
python run_theater.py d-dim --run all-ddim --execute
python run_theater.py dynamic --run all-dynamic --execute
```

Run these sequentially: one controller owns the machine-wide benchmark lock.
Omit `--algorithms` for the full default roster. That flag is for explicitly
requested subsets. Prepared manifests from older rosters must be regenerated
in a fresh workspace; do not rewrite manifests tied to completed results.

Run `python -m unittest discover -s tests` to check roster consistency and
support boundaries. Run the selected-binary checks documented in RUNNING.md
for exact-output validation. This repository cleanup does not alter any frozen
workspace or running queue on Archie.
