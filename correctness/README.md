# Scientific correctness benchmark

After building and preparing inputs, run `python tools/run.py correctness --campaign NAME --run LABEL`. This is the first experimental stage, not a new regression-test framework.

Shared fixtures cover random inputs, duplicates, boundary and zero-radius circles, uint32 extremes, empty input and collinear points. Dynamic fixtures add insertions, deletion of individual duplicate occurrences, empty-index queries and reinsertion.

The oracle independently scans the live multiset using signed 128-bit squared-distance arithmetic. Full sorted coordinate multisets are compared. Output order is unrestricted; missing or extra occurrences fail. Failures exclude entries; infrastructure errors block them. Inputs and logs are retained.

Eligibility records manifest, harness, binary/library, backend and CPU fingerprints. Passing exercised inputs is evidence, not a proof for all inputs. Existing source test files are retained; no new regression tests are required by this workflow.
