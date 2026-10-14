Run the optional compact base's actual CLI and kernel tests locally:

```sh
python3 tests/semantic_base_cache/run.py --unison /absolute/current/unison --receipt /private/tmp/cache-cli.json
python3 tests/semantic_base_cache/kernel.py --compiler /absolute/ocamlopt --report /private/tmp/cache-kernel.json
python3 tests/semantic_base_cache/fingerprint.py --compiler /absolute/ocamlopt \
  --build /absolute/current/Make/snapshot --report /private/tmp/cache-fingerprint.json
```

The CLI uses disposable loopback replicas, original DNG-shaped bytes and
mock validators; no Adobe/SDK/Photo input is involved. Its twelve cases include
cache-only convergence, missing/damaged/permissive/symlinked/stale/disabled
records, image/conflicting edits, wrong common generation, a checksum-valid
wrong policy, and second-receiver failure followed by fresh convergence.
Full backup behavior has its independent existing merge suite.

The kernel compares exact output against independent Python SDB bytes and
runs thirteen finite codec/reconciliation controls. OxCaml executes them in an
actual Safe.spawn domain. The descriptor probe links the actual native objects
and verifies eight MD5 compatibility, cursor, path replacement and FD controls.
These are deterministic functional tests, not fuzzing or SDK qualification.
All retained private workspaces/logs are reported in the receipts.
