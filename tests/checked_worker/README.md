# Actual checked worker qualification

Run compiler negatives against an actual OxCaml Make snapshot:

```sh
python3 tests/checked_worker/probe.py --compiler ~/.opam/5.2.0+ox/bin/ocamlopt --build SNAPSHOT/src --receipt /tmp/worker-negative.json
```

The six controls use real production interfaces, including a genuine former
mutable-counter worker from commit49dc756 (available git history is required)
compiled against the new extension
interfaces. None invoke native/Adobe work.

`tests/workers/run.py --build SNAPSHOT/src` links actual matching CMIs/CMXs and
native objects; it does not substitute checked interfaces. The full test,
`--stress-only`, and `--apply-stress-only` exercise the real production worker
and shared helper budget on private synthetic files. Stock and OxCaml run the
same runtime tests. The full suite caps its largest pools at18 workers;48 typed
observations independently compare whole metadata transcripts and exact proofs.

The [pinned qualification](qualification.json) records source and artifact
identities and separates mode proof from instrumented resource tests and open
M6/native/performance requirements.
