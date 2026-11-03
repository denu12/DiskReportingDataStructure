# Publication status

The repository includes the source, documented adaptations and [dated measurement snapshots](../measurements/README.md). Audit findings and validation are recorded in [audit resolution](AUDIT-RESOLUTION.md). Existing Git history is retained.

## Remaining source-permission question

The recovered Chan source (`src/third_party/chan_sss/sss-original.cc`) and STANN
mirror do not contain an explicit redistribution license in the files available
here. Their author notices are preserved; this project's MIT license does not
supply a license for those sources. Resolve permission with the source owners or
replace/remove the affected source before public release. STANN is an active
build dependency, so removing its files alone would break the current roster.
See [third-party credits](THIRD_PARTY.md) and the corresponding `NOTICE.txt` files.

## Release contents

- Eight retained standalone Morton implementations under `src/morton/2d`, `3d`, and `d_dim`; `dynamic` documents the absence of an active dynamic Morton.
- Five documented theaters, with campaign definitions inside each theater.
- One public orchestration entry point, `run_theater.py`.
- Explicit adapter provenance and both SPRK output contracts.
- Arch build scripts, dependency pins, Dockerfile and upstream notices.

Generated inputs, private documents, binaries and local toolchains are excluded from Git and Docker. Recorded measurements and logs are published separately under `measurements/`, with local machine identities redacted. Measurement bundles are excluded from Docker builds.
The checked Git history has no paths under `historical_data/`, `data/` or `results/`.
A source snapshot does not erase older source revisions from Git history.

## Validation and limits

Repository checks cover Python syntax, JSON definitions, documentation links and theater previews. Native validation uses Archie's cached pinned dependencies in an isolated source workspace; this does not establish a fresh online dependency download or a clean Docker image build. Targeted correctness checks and small end-to-end runner exercises are summarized in [audit resolution](AUDIT-RESOLUTION.md).

The Dockerfile builds the 2D programs; full imported and dimensional theaters use native user systemd as documented in [RUNNING.md](RUNNING.md).

Many published experiment results predate current source changes. Identify each recorded revision and reporting contract before comparing runs. Historical failures and partial runs are retained; their presence does not establish correctness or completed coverage. Publishing a snapshot does not restart or alter experiments.
