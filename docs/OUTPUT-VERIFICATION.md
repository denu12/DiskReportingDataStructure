# Complete output verification

`verify_outputs.py` is a separate correctness checker for a frozen queue. Run it from the repository on Archie. It uses that queue's original input manifests, selected algorithms, frozen source and compiled backends; it never changes benchmark data, timings or admission decisions.

```sh
python verify_outputs.py --queue results/_queue-morton-boost-sprk-cheating-20261009
python verify_outputs.py --queue results/_queue-morton-boost-sprk-cheating-20261009 --execute
```

The first command previews 2,090 implementation/instance checks in the current queue. The second uses all original indexed points and every original query. It does not substitute sampled admission inputs or compare only answer counts. Native verification compares each sorted coordinate multiset against an exact integer scan, preserving duplicate occurrences. If all implementations match that oracle for every query, their outputs match one another, independent of ordering. This checker does not export the full coordinate lists.

SPRK (original) IDs are mapped back to original coordinates for verification. Its `integer_mismatch_queries` field records actual multiset disagreements with integer geometry. The checker treats these as mismatches even though the experimental admission gate accepts its different floating-point contract. A success under that floating contract alone cannot make this checker pass.

Jobs run serially on CPU 1 with a 64 GiB memory cap and no swap. The defaults are 180 seconds per complete verifier invocation and two hours total. Full integer scans can be substantially slower than benchmark queries. Increase `--timeout-seconds` and `--wall-limit-seconds` when broader coverage is needed. Timeouts, crashes, missing output, input-checksum failures and unexecuted jobs are inconclusive; they are never counted as matches. The checker refuses to overlap a theater controller.

Optional selections:

```sh
python verify_outputs.py --queue results/_queue-morton-boost-sprk-cheating-20261009 --campaigns static --execute
python verify_outputs.py --queue results/_queue-morton-boost-sprk-cheating-20261009 --campaigns scaling Scaling3D --boundary-only --execute
```

`--boundary-only` explicitly changes the scope to boundary/duplicate fixtures and does not verify the full campaign. Validation of the checker on those fixtures found 11 conforming implementation checks matching the integer oracle and the two SPRK (original) checks differing. This is not evidence that every query in the full campaigns has been verified.

Each invocation writes a fresh `results/_output-verification-<label>/summary.json`, native result files and stdout/stderr logs. `--run` sets an explicit fresh label. The summary records scope, resources, input/binary hashes and coverage. `all_outputs_match` is false when any actual mismatch is established, true only when every planned check completes and matches, and null when no mismatch is established but coverage is incomplete. A native verifier may stop at its first mismatch; a successful result is accepted only when its verified query count equals the input header. Exit codes are 0 for complete agreement, 1 for an established mismatch, and 2 for incomplete/inconclusive verification.
