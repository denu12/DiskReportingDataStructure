# Publication status

The current source tree is staged for review. No publication push is performed by
repository preparation. Existing Git history is retained.

## Remaining source-permission question

The recovered Chan source (`src/third_party/chan_sss/sss-original.cc`) and STANN
mirror do not contain an explicit redistribution license in the files available
here. Their author notices are preserved; this project's MIT license does not
supply a license for those sources. Resolve permission with the source owners or
replace/remove the affected source before public release. STANN is an active
build dependency, so removing its files alone would break the current roster.
See [third-party credits](THIRD_PARTY.md) and the corresponding `NOTICE.txt` files.

## Release contents

- Four standalone Morton implementations under `src/morton/`.
- Five documented theaters, with campaign definitions inside each theater.
- One public orchestration entry point, `run_theater.py`.
- Explicit adapter provenance and both SPRK output contracts.
- Arch build scripts, dependency pins, Dockerfile and upstream notices.

Private historical data, generated inputs, results, binaries and local toolchains
are excluded from Git and Docker. The staged file list contains none of these.
The checked Git history has no paths under `historical_data/`, `data/` or `results/`.
A source snapshot does not erase older source revisions from Git history.

## Validation and limits

Publication checks inspect the staged tree, relative documentation links, Python
syntax, JSON definitions, executable script modes and common credential/workstation
path patterns. These are repository checks, not new experimental regression tests.

The clean staged source export passes all five theater previews, shell syntax
checks, compilation of the four standalone Morton files, the three CMake
dimensional C++ targets, and both 2D Bazel configurations (default and ParGeo). Native compilation uses Archie's cached dependencies. That does
not establish a fresh online dependency download or a clean Docker image build.
The Dockerfile builds the 2D programs; full imported and dimensional theaters use
native user systemd as documented in [RUNNING.md](RUNNING.md).

Existing experiment results predate some source changes. They remain private and
must not be presented as measurements of the current source without identifying
the recorded source revision. Preparing this release does not start experiments.
