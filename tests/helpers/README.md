These tests compile the production supervisor and validation modules with the
repository's actual legacy Lwt in a temporary directory. They use synthetic
children, not Adobe software or photographs:

```
python3 tests/helpers/run_tests.py
python3 tests/helpers/run_tests.py --ocamlopt /Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt
```

The qualified SDK driver protocol is intentionally separate from stock
`dng_validate`. A stock exit code cannot reliably distinguish validation errors.
No Adobe driver is shipped or claimed qualified by this initial module.

The configured absolute executable and fixed argument prefix receive:

```
--unison-dng-validation-v1 --expected-sha256 HEX --expected-size DECIMAL --threads CPU_WEIGHT -- ABSOLUTE_CANDIDATE
```

The driver must independently read/hash and fully structurally validate and
decode the candidate. It must count SDK error reports (including errors that do
not throw), inspect all applicable raw digest results, and emit exactly this
ASCII stdout receipt, in this order, with a trailing newline. Other diagnostics
belong on bounded stderr. It must not simply echo the supplied expected hash:

```
UNISON-DNG-VALIDATION 1
candidate-sha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
candidate-size 12345
driver-build qualified-sdk-build-identifier
structure valid
decode success
raw-digest valid
errors 0
warnings 0
END
```

Allowed structure values: `valid`, `invalid`, `unsupported`. Decode values:
`success`, `failure`, `unsupported`, `not_checked`. Raw digest values: `valid`,
`mismatch`, `missing`, `unsupported`, `not_checked`. Missing optional tags are
not corruption. If a digest is present but cannot be checked, use `unsupported`
or `not_checked`, never `missing`. SHA-256 is 64 lowercase hex characters;
numbers are canonical nonnegative decimal with no leading zeros. Build IDs
contain 1–128 ASCII letters, digits, dot, underscore or hyphen. Unknown/repeated
fields, extra stdout, CRLF, partial receipts, and receipts over 4096 bytes fail.

Success requires exit zero, no supervisor failure/truncation, matching qualified
build and exact candidate identity, structure valid, decode success, raw digest
valid or missing, and zero errors. Tool and candidate are inspected before and
after invocation. Local tool configuration and deployment must be trusted;
content pins do not sandbox the executable or eliminate hostile path races.

Candidate pre-inspection failures, invalid expected snapshots and candidate
identity/content changes always reject, including under warn. Tool availability
and validation findings retain the explicit warn/require policy distinction.
The current companion checkpoint adds four focused pre-inspection controls;
its [actual receiving fault suite](../validation_inspection_fault/README.md)
qualifies local/remote rejection before any helper invocation.

Scheduling uses one owner-loop budget shared by child processes and future
domain jobs. A driver's CPU weight includes all its native threads. Qualified
single-thread SDK drivers can run one per available CPU permit; multithreaded
drivers reserve their configured native thread cap. Calling legacy Lwt from
another domain is forbidden: future workers request admission through the owner
mailbox. There is no blocking domain allocated per subprocess.

The POSIX backend creates a separate process group without running OCaml after
fork. Timeout, cancellation, and output overflow terminate that group and reap
the direct child. Escaping a process group is outside the trusted-helper contract.
Output caps bound capture memory, not child RSS. Admission time is excluded from
execution timeout. Native Windows support and strict OS RSS limits are future
backend work. Deadline accounting is monotonic; cooperative timer wakeups still
use legacy Lwt's wall-clock timer and can be delayed by a system clock rollback.

Connection teardown cannot depend on the owner loop ticking again. The separate
`cancel_and_cleanup` path immediately kills active helper groups, synchronously
reaps direct children, closes pipes, removes queued admission, and releases only
those helper permits. A normal-process-exit safeguard covers abandoned helpers;
completed registrations are removed. This exceptional path skips TERM/grace and
can briefly wait for kernel reaping (uninterruptible OS waits have no finite
bound). Ordinary cancellation remains asynchronous and graceful. Abrupt process
termination such as SIGKILL cannot run cleanup. Domain jobs receive a synchronous
`on_cancel` notification into their own Atomic flags and retain permits until
their completion is consumed. Cancellation tokens use stable object identities
so connection resource registries can hash and distinguish them after mutation.

Tests stop the owner loop before teardown, assert the child was reaped and its
permits released before any further tick, and then resume the stale monitor to
check idempotence. A subprocess-exit test deliberately abandons a running helper.
On macOS, an additional test opens an unrelated non-cloexec descriptor and proves
that `POSIX_SPAWN_CLOEXEC_DEFAULT` excludes it from the helper. Other POSIX systems
currently rely on unrelated application descriptors having close-on-exec set;
the supervisor's own pipe descriptors always have that flag.

The optional retained-group callback integration has focused controls for normal
completion, callback exceptions, timeout, pre-spawn cancellation and synchronous
disconnect teardown. A synchronous teardown retires its binding before blocking
reap and emits no group observation. The latest added timeout/disconnect controls
are source-only until the integration checkpoint records their actual runs.

Manual Make entry points (run from the repository root):

```
STOCK_PREFIX="$HOME/.opam/default/bin" make -f tests/Makefile helper-stock
OX_PREFIX="$HOME/.opam/5.2.0+ox/bin" make -f tests/Makefile helper-ox
BUILD_RECEIPT=/absolute/current-build.json make -f tests/Makefile validation-cli
make -f tests/Makefile group-parser
```

Prefix values are read as argument values, never shell fragments. Use
`DRY_RUN=1` to inspect a command without launching it. The helper suite compiles
serially and uses original synthetic children; validation-cli requires a current
successful build/selftest receipt and launches only synthetic receiving cases.
The group-parser target executes pure Python fixtures only. No target invokes
Adobe or opens Photo/Lightroom. Coordinate CPU reservations before native checks.

Current integration qualification supersedes the source-only checkpoint above:
[41 stock/Ox helper groups each](../helper_group_observation/integration-qualification.json)
and [both full builds/selftests plus five receiving cases each](../validation_process/group-integration-qualification.json)
pass. The new timeout, cancellation, synchronous teardown and receipt-forwarding
controls were actually executed. No SDK/Photo calls were involved.

`DngValidation.validate_with_execution` can forward an optional `observe_alive`
callback to the actual supervisor. The [bridge controls](../qualification/validation-live-observer-bridge-actual-20261016.json)
run43 synthetic groups per compiler: sample PID binding, valid versus exit-zero
error receipt decisions, and validation-off skipping both diagnostics/execution.
This remains observational, not commit authority or proof of SDK concurrency.
The receiving companion does not yet emit these samples into its diagnostic protocol.
