# Capped SDK host comparison preparation

`plan.py` hashes existing executables and the three accepted generated codec
inputs, then writes an exclusive output plan. It never launches a validator,
fixture writer, Lightroom or Photo process. Production endpoint settings remain
unchanged. Example, from the repository root:

```sh
python3 tests/sdk_host_matrix/plan.py \
  --reference-manifest /private/path/reference/build-manifest.json \
  --experimental-manifest /private/path/experimental/build-manifest-area-memory-unqualified.json \
  --receive-ready /private/path/previous-receive-workspace/READY.json \
  --host-memory-bytes 1073741824 \
  --output /private/tmp/new-host-comparison-plan.json
python3 tests/sdk_host_matrix/test.py
python3 tests/sdk_host_matrix/executor_test.py
```

For each uncompressed, JPEG and JPEG XL input, the plan compares one reference
call against experimental calls with 1, 6 and 18 total requested threads,
including the caller. Calls must run sequentially: twelve calls, three inputs,
twelve logical states, eighteen reserved CPU credits and one 300-second
aggregate. `run.py` revalidates pins before dispatch, binds a fresh Root admission
and deadline, owns/reaps the aggregate, and retains raw stdout/stderr and every
call result. The owner must still prove parent terminal exit separately. There
is deliberately no native execution mode in the preparation tool `plan.py`.

The executor requires an explicit `--mode mock|native`; mock mode refuses tools
without a `MOCK-` build identity. Native mode additionally verifies the actual
reference/experimental manifests and requires `--admission` with state
`ROOT_ADMITTED_FINITE_UNISON_HOST_MATRIX_V1`, exact `plan` path/SHA256, exact
`command` argv including the Python executable, exact plan `limits`, and fresh
`startDeadlineUnix`. A receiving-pilot admission cannot satisfy this state.
Run directories are created exclusively and cannot be resumed or replayed.
An abandoned WRAPPER-START without aggregate closure retains owner responsibility.
The sequential direct SDK calls must remain in the owned group; descendants
which intentionally escape that group are outside this trusted-tool contract.

`executor_test.py` launches only original fake Python validators. It proves the
twelve-call success path, warning divergence and zero-exit bad-digest rejection,
noncanonical argv refusal before acquisition, consumed-workspace refusal, and
genuine aggregate closure on both normal and failed runs. These deterministic
controls are not fuzzing, SDK execution or real thread/memory qualification.

The current executor also requires exactly one bounded version-1 area and memory
stderr record for each experimental call. It rejects malformed/duplicate/missing
records, unexercised or unsettled covered allocation accounting, quota denials,
live callback frames, incomplete task lifecycle, and oversized partitions. A
one-thread call must report explicit reference delegation; higher allowances
must report joined custom tasks. It retains parsed observations alongside raw
diagnostics. Callback peak is not capped at the requested thread count because
nested callback frames can share a thread; the declared partition is capped.
These checks consume the pinned tool's observations, not independent OS metrics.
Additional fake-tool cases prove missing telemetry/live allocations/active
callbacks cannot produce a success packet even when stdout validation succeeds.

`receipt` checks exact framing, input/build identity, valid structure, successful
decode, valid raw digest and zero errors. Compare its returned fields, including
warning counts, against that codec's reference. Different warning counts need
review rather than an automatic equivalence claim. Deterministic tests exercise
all twelve argv/positive-receipt combinations and malformed receipts and plans.

The actual twelve-call matrix passed and Root independently accepted its sealed
return and genuine closure. See [Root adoption](../qualification/sdk-host-matrix-v1-root-adoption-20261014.json)
and [raw return](../qualification/sdk-host-matrix-v1-actual-return-20261014.json).
All three generated codecs matched reference validation outcomes at experimental
1/6/18 allowances; callback tasks joined and covered allocations retired.

This proves validation-result/callback/covered-allocation behavior for those
inputs. It does not expose decoded pixels or independently measure OS threads,
thread cancellation, RSS or all heaps. Those remain separate gates before
production integration or a scaling claim. One fixed-order sample per setting
is not a throughput benchmark. The actual admission is consumed; preparation
and accepted results do not authorize another SDK invocation.

## Shared8 source successor

`shared_plan.shared_matrix` is a pure metadata constructor for a future versioned
executor: three codecs, reference1 and experimental1/2/6,12 sequential calls,
Unison00..07 with2owner credits. It reuses the existing protocol constructor and
preserves the old18-credit matrix and historical source receipts. It does not
open/hash inputs or tools, build, admit or execute anything.

[Six source controls](../qualification/sdk-shared-matrix-source-actual-20261016.json)
verify thread argv/accounting, reference versus experimental protocol/memory,
codec/budget refusal and false runtime/hard-cap flags. A fresh exact executor
must still acquire IO→CPU, own every helper/group through actual settlement,
retain unknown ownership, bind telemetry and compare reference results before
any real SDK scaling qualification. This constructor is not accepted by the old
18-credit native executor and cannot grant a shared or borrowed native window.

`shared_result.audit` independently joins twelve ordered returned call frames to
that pure shared plan, checking exact commands, normal direct-child waits,
reference-equivalent structured validation, and experimental task/allocator
settlement observations. It rejects decoded-success frames with live/denied
memory or unfinished/active tasks. Its resource-release, aggregate/group,
parent-terminal, OS-thread scaling, RSS and pixel proof flags remain false.
[Source controls](../qualification/sdk-shared-result-source-actual-20261016.json)
use inert frames, not real SDK lifecycles. A future executor must bind these
frames to its actual journal/pins and separately own the aggregate and all IO/CPU
FD copies; this functional auditor cannot substitute for that work.

`shared_kernel.Kernel` is an inert, one-use composition around an injected
`invoke` callback and persistence sink. It reuses the invocation journal, saves
intent before calling and outcome before functional audit, and stops at the
first failed call. A possible call with no returned outcome, or failure to
persist a returned outcome, raises retained ownership rather than ordinary
failed-prefix closure. All returned results retain false release authority.
[Ten source controls](../qualification/sdk-shared-kernel-source-actual-20261016.json)
exercise five kernel groups and five result groups with inert callbacks/frames.
No CLI/native entrypoint, deadline or real helper ownership is implemented here;
a separately qualified owner must supply those before any native admission.
