# Recoverable DNG merge I/O failures

```sh
python3 tests/merge_io_errors/run.py \
  --build-receipt /absolute/current-Make-build-RESULT.json \
  --report /private/tmp/merge-io-errors.json
```

This macOS probe links the selected snapshot's actual production object prefix
through SemanticSync and its native dependencies. It starts one checked worker
and invokes the production asynchronous merge boundary with six controlled
filesystem acquisition failures: missing base, left, right and output files,
a non-directory base parent, and an output directory. No test hook or fake merge
module is installed. Inputs are tiny original synthetic files, not valid DNGs;
these acquisition tests must fail before format inspection or writes.

Each call must report Util.Transient, settle transaction/payload/descriptor,
CPU, worker and filesystem-I/O ledgers, and return to its prior descriptor count.
All input/output sentinel hashes must remain unchanged. The worker is shut down
before process exit. Cancellation, programming and allocation exceptions are not
converted by this filesystem error classification.

`--expected-exit 2` is reserved for a pinned older negative snapshot. It permits
source drift only for that historical negative, retains its actual raw Unix
errors, and is not a passing current-source qualification. A successful harness
exit means its explicitly expected probe exit was observed; inspect `probe_exit`
and `expected_exit` in the receipt. No SDK, photos, catalogs or production files
are opened, and no sanitizer/fuzz campaign runs.


The extended probe also compiles an explicitly private copy of SemanticSync
with eleven deterministic exception raises after four acquired descriptors.
It checks OS-error conversion versus preservation of Not_found, End_of_file,
Out_of_memory, Sys.Break, Failure, Invalid_argument, Fatal and existing Transient.
No production fault hook or actual memory exhaustion is introduced.
`--expected-fault-exit 2` selects a historical negative for this private probe;
the normal object probe and private probe exits are recorded separately.
Current positive runs require both probe exits to be zero. Historical negative
runs may select a nonzero expected exit explicitly; their receipts retain that
distinction and do not qualify current source. See
[exception classification evidence](exception-qualification.json) for the current
compiler-matched results and prior-implementation negative.
