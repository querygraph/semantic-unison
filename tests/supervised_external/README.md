Private SDK-free controls for actual `SupervisedExternal`, helper/worker CPU
sharing and real Unison external copy/merge workflows. No photograph, preview,
catalog, native UI, Adobe executable or production data is used.

`run.py` links the compiler-matched full source graph through the new bridge.
Fourteen cases cover preserved argv[0]/literal arguments/environment, shell
formatting and nonzero exit policy, invalid/missing invocation, CPU weight,
timeout, both output streams, signals, active/queued cancellation and actual
worker admission behind an all-CPU helper. The helper-only owner and subsequent
worker runtime must be the same object. Direct helpers are independently
observed reaped, and CPU/child/worker ledgers settle. Normal controls use a
ten-second deadline; the deliberate timeout remains one second. Retained
one-second startup failures are distinct from the final qualification.

`copy_status.py` runs actual client/server CLI transport with a synthetic
external copier that fully writes its candidate. Success publishes exact
bytes. Exit 7, timeout and output overflow must reject and preserve destination
absence plus independent existing sibling bytes. The genuine previous binary
negative must actually publish after exit 7. External-copy selection is the
new-file `Copy` branch; an update fixture would test the ordinary copier instead.
That first fixture failure is preserved rather than counted as qualification.

Existing receiving-path tests cover real copy/merge, resumed and hint-reused
candidates plus SDK-style validation/cancellation policies. Existing helper
ownership and returned-work tests exercise descriptor/PID/permit faults.
Native syscall and promise observation hooks in those suites remain private.

```sh
python3 tests/supervised_external/run.py --build /private/path/snapshot \
  --ocamlopt /absolute/ocamlopt --receipt /private/path/helpers.json
python3 tests/supervised_external/copy_status.py --unison /private/path/unison \
  --parent /private/path/previous-unison --receipt /private/path/copy.json
```

Current evidence is root-owned, not a new independent-agent review. Declared
CPU weights do not constrain unknown internal parallelism; Windows, child
memory/global FD limits, actual SDK/corpus and broader M4-V/M5/M6 work remain
open. No benchmark or machine-wide quota is inferred.

## Installed ExifTool read-only control

Pass `--exiftool /absolute/installed/exiftool --exiftool-only` to run the
separate real-tool case (the default fourteen synthetic cases are unchanged).
It disables ExifTool user configuration with `-config ""`, requests only JSON
Rating/Label/ExifToolVersion from a newly authored private XMP, and submits16
hash jobs to the same production runtime/budget. Status, metadata values, exact
source bytes/eight-field native stat fence and settled helper/worker ledgers are
checked. No editing flag, photo input, SDK or catalog is involved.

[Actual stock/Ox evidence](../qualification/shared-exiftool-hash-actual-20261016.json)
passes24 assertions/compiler and records installed version13.10, script SHA
before/after, compiler-matched object/source pins and actual containing group/
CPU8 closure. Perl/module inventory, standalone child-PID observation, sampled
CPU overlap, hard limits, simultaneous ExifTool/Adobe and throughput remain
outside this case. Tool configuration is explicitly opt-in; no installation or
change to production preferences occurs.

## Opt-in external helper lifecycle diagnostics

`-debug external-process` enables an owner-side result record after helper
execution settles. It reports the historical PID, wait status/outcome, declared
CPU weight, capture truncation and a retained-group observation. Command
arguments and captured stdout/stderr are omitted. Default execution does not
query the process table or emit this record. Ordinary nonzero exit policy,
cancellation, signals, output and timeout limits keep their existing behavior.

`other-members=unobserved` means no callback ran; `unknown` is an unsupported or
failed observation. Numeric counts describe one census before leader reap,
not durable process-tree closure or authorization to signal a historical PID.
The observed fixture case binds the record to its actual PID file and independent
ECHILD check. ExifTool's PID comes from the supervised trace, not process absence.
The initial [component receipt](../qualification/external-process-observation-actual-20261016.json)
retains16cases/compiler; its private overlay inferred the CMI. The [successor current-interface16-case runs](../qualification/external-process-current-interface-actual-20261016.json)
pass on both compilers with exact CMI equality, and
[full Make builds/CLI selftests](../qualification/external-process-full-cli-actual-20261016.json)
pass/close on both. Current Dune/GUI qualification is not inferred.
`--current-bridge` compiles only the current bridge against the snapshot's
unchanged dependency objects and matching explicit production interface; other
production source mismatches still refuse.

`external_records.py` is the bounded strict consumer for these diagnostics.
It preserves client/server endpoints, canonical historical PID/status/CPU fields,
truncation and observed/unknown/unobserved group distinctions. It does not dedupe
PIDs into a lifetime claim. All parsed records explicitly lack producer
authentication and resource-release authority: merged output could contain
helper-authored lookalikes, so an independent call/owner/source binding remains
required. Unknown versions/extra fields, contradictory identities, overflow and
line/count/UTF-8 byte limits refuse. [Six controls](../qualification/external-process-parser-actual-20261016.json)
include independent reparse/hash checks on four saved real stock/Ox records;
no external helper is rerun by the parser test.
