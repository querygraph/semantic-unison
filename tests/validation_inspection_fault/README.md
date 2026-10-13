# Warn-mode candidate inspection failure

The runner copies an already frozen compiler-matched Make snapshot and changes
only its private `CandidateValidation.snapshot` implementation. The initial
typed identification and conditional SHA-256 run normally; the first candidate
pre-inspection then records its private path and returns EIO. The production
sources and public preferences contain no fault hook.

```sh
python3 tests/validation_inspection_fault/run.py \
  --build /absolute/frozen/build --ocamlopt /absolute/compiler/bin/ocamlopt \
  --report /private/tmp/validation-inspection-fault.json
```

Both local and loopback remote ordinary receive paths use a renamed synthetic
DNG and an endpoint-configured synthetic driver. Warn must reject the inspection
error before helper execution, preserve old live bytes/inode and the decoded
`renamed.bin` archive node's full fingerprint, and discard the partial candidate. An unmodified retry must
publish exact bytes and invoke the driver once; a subsequent no-op preserves
inodes and invokes no helper. A compiler-matched private reader uses the public
production format-23 codec; raw containers are retained and may change auxiliary
metadata. Work, source mutations, linked objects/binaries, traces, terminal
logs and owned-group cleanup remain available. No Adobe invocation, photographic
input, performance or whole-process resource accounting is claimed.
