# Receiving helper diagnostics

[Stock/Ox qualification](qualification.json) records successful Make/selftests
and five actual CLI controls per compiler. Run after local CPU coordination permits:

```sh
python3 tests/validation_process/cli.py \
  --build-receipt /absolute/current-build-RESULT.json \
  --report /private/tmp/fresh-validation-process-report.json
```

The five finite CLI controls use original fake validators, not Adobe or photos.
They check default-off logging, actual helper PID and raw receipt binding,
no-op silence, an exit-zero validation finding that still rejects publication,
and arbitrary stderr bytes clipped independently of the helper capture limit.
No fuzzing or sanitizer campaign runs.

`-debug validation-process` enables owner-side `Helper result v0` lines after
supervised execution settles. They include the direct child's historical PID,
wait status/outcome, the receiving candidate hash/size, capture truncation,
and at most 4096 bytes each of stdout/stderr encoded as lowercase hex. Explicit
per-stream clipping flags distinguish a diagnostic prefix from complete capture.
Hex encoding keeps arbitrary bytes and terminal control characters out of the
line framing. Collection/formatting occurs only in the enabled debug callback.
Both endpoint logs are required for a bidirectional merge audit.

A completed helper with exit zero may report validation errors. The diagnostic
precedes validator interpretation and does not authorize publication, prove
validation success, retain a PID reservation, or prove descendant-group absence.
Do not signal its returned PID. This does not replace the separate helper-group
ownership prerequisite for an actual SDK receiving pilot.


[The independent parser](records.py) bounds logs to 4 MiB, recognized lines to
20,000 characters, records to 4096 and decoded streams to 4096 bytes each. It
rejects malformed/unknown framing, overflow, odd hex and inconsistent clipping;
it preserves empty observation sets, duplicate diagnostic identities, nonzero
statuses and capture-incomplete records. Its immutable records never authorize
signaling or publication. SDK acceptance still requires independently parsing
and binding the complete SDK protocol and its qualified tool/candidate pins.

```sh
python3 tests/validation_process/parser_test.py
```

[Pure qualification](parser-qualification.json) covers 22 malformed controls,
actual six-record readback against pinned original CLI reports, arbitrary byte
preservation, endpoints and empty/clipped/nonzero observations. Python3.14 and
system3.9 both pass; this does not qualify Python3.9 native process supervision.
No child process is launched by this parser test.

Optional retained-group diagnostics (integration source checkpoint)
----------------------------------------------------------------

`-debug validation-group` enables a spawn-bound query on the DNG validator helper
only. The owner captures it while the terminal direct child is retained, then
prints after helper settlement:

```
Retained group v0 pid=123 candidate-sha256=<hex> other-members=0
```

`unknown` means unsupported backend or query failure; `unobserved` means the
normal terminal observation did not run (for example synchronous teardown).
A nonnegative number is only a bounded process-table observation before reap.
It is neither an SDK verdict nor durable/escaped-process absence proof and
does not grant authority to signal the historical PID. The existing bounded
`validation-process` v0 format/parser remains unchanged; it does not parse this
separate trace class. Tracing remains off by default.

This forwarding/trace integration is source-only until current stock/Ox helper
and receiving CLI checks complete; prior native primitive or diagnostic results
do not qualify this new source. No SDK invocation is authorized by the flag.
