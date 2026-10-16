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

`shared_child.invoke` is a direct-child component without CLI/admission or resource
acquisition. It retains a separate group leader until terminal observation and
other-member absence, then waits once and drains bounded output. Expired/unknown
observation retains the owner and capture objects without signalling; capture
finish failures preserve pre-close identity without numeric retry. It never
claims aggregate/parent terminal or IO/CPU release authority.
[Three component groups](../qualification/sdk-shared-child-component-actual-20261016.json)
run three actual original Python helpers (normal, exit7, truncated output), not
SDK code. Unknown/group/close-fault injection, inherited resource descriptors,
exact artifact/input/admission binding and the real parent remain unqualified.
No native runtime or SDK admission follows from this component.

[Child fault controls](../qualification/sdk-shared-child-faults-actual-20261016.json)
now cover live observation/census refusal without signals or reap, partial
capture construction, close uncertainty and nested uncertainty propagation.
The carrier preserves child/capture objects plus every original uncertain-close
identity, excluding those numbers from any retained-FD retry set. These five
cases use inert owners and injected errors that never actually call OS close;
three actual fake-child regressions also pass on the corrected source. Real
SDK/native ancestry and resource inheritance remain separate future gates.

[Actual fake composition](../qualification/sdk-shared-composed-fake-actual-20261016.json)
now runs16 original Python helpers through the one-use journal kernel, retained
child adapter, qualified durable persistence and independent result auditor.
Twelve reference/experimental-shaped fake calls succeed; warning divergence and
missing telemetry each stop after the second call. All attempted direct children
and groups settle, every outcome persists, and the outer Unison8 owner closes.
Inert fixture paths are never opened; fake structured raw-digest fields are not
SDK verification. The component has no SDK mode or native admission route.
Canonical IO/inherited grant9FD binding, input/tool pins, actual aggregate owner
and independently reviewed native dispatch remain outstanding before real SDK use.

`shared_binding.verify` now checks the actual parent/worker/expected command and
ordered nine inherited descriptions against pinned standing8 policy, CPU00..07
and the sole EXglobal barrier manifest. It rejects caller-selected token ranges,
missing/duplicate/reordered/noncanonical descriptors, stdio collisions and fresh
fstat type/owner/mode/link/size/identity mismatches. It returns inherited numbers
for a future owned child, never independently claims that flock locks are held
or authorizes resource release.
[Four source groups](../qualification/sdk-shared-binding-source-actual-20261016.json)
use actual pinned manifest metadata and injected descriptor observations. Real
inherited canonical ownership/dispatcher binding remains to be qualified.

[Actual disposable inheritance](../qualification/sdk-shared-inheritance-actual-20261016.json)
now exercises two real Python children through the retained child adapter:
all9 inherited lock descriptions reach the guard and fresh distinct contenders
see all locks busy; omitting one refuses before further work. Parent copies
remain held until actual child reap/group absence, then close and fresh lock
acquisition succeeds. Canonical inventory and child START metadata are explicit
test doubles. This proves descriptor lifetime/refusal mechanics, not actual
canonical IO admission, the new exact parent dispatcher or SDK authorization.

`shared_parent_audit.audit` adds the parent-side attempted-call boundary: exact
ordered intent/outcome commands and identities, direct wait status, group absence
before reap, bounded raw diagnostics and journal-to-functional-row equality.
Complete matrices additionally pass the independent functional audit; known
nonzero prefixes remain FAILED, not functional success. An empty prefix requires
an explicit PREPARING_NO_CALL failure. Unknown outcomes or group proofs refuse.
[Actual source/composed controls](../qualification/sdk-shared-parent-audit-actual-20261016.json)
cover inert faults and the16 original fake-helper composition. The audit never
proves its aggregate parent exited or that IO/CPU FDs closed. It precedes new
exact-target dispatcher integration, which remains unimplemented/unadmitted.

## Exact shared native entry: source integrated, unadmitted

`shared_execute.py` and the `shared-sdk-host-matrix` dispatcher target now wire
fresh exact admission, immutable plan/source/tool manifests, three readonly
private fixture identities, the pinned interpreter and actual inherited9FD
binding. Tool/input payload hashes run only inside the owned IO grant; tool pins
are rechecked per call. Every direct helper inherits resource FDs and receives
an explicit observation deadline; unknown child/capture/group state retains.
The parent independently audits every attempted prefix before aggregate reap,
checks input epochs, and closes CPU then IO only after known settlement. A
complete result with failed worker exit, or failed result with successful worker
exit, retains ownership instead of claiming closure.

[Source controls and prior dispatcher regressions](../qualification/sdk-shared-entry-dispatch-source-actual-20261016.json)
pass17 groups using metadata/artifact/owner doubles. No plan/admission/native
runtime exists for this target yet. New-target parent fault controls and actual
entry/dispatcher composition must precede a fresh reviewed native request.
Historical18-credit matrix and consumed receiving slots are not reusable.

[New-target parent fault controls](../qualification/sdk-shared-dispatch-faults-actual-20261016.json)
now cover audit-before-reap/reverse-close, known failed-prefix closure without
functional pass, unknown direct groups, complete/failed worker-exit contradictions,
live observation and one-shot CPU-close uncertainty retaining IO. Seven new
inert-owner cases plus four reused audit cases pass with actual outerCPU8 closure.
MockPID900001 is never an OS child and mock close failures never call OS close;
no native/canonical IO or actual new-target lifecycle is inferred.

[Actual new-target entry composition](../qualification/sdk-shared-entry-lifecycle-actual-20261016.json)
now exercises three worker children:9inheritedFDs reach a deliberately refused
kernel,8refuse before it, and a third runs12 original fake validators through the
actual worker/kernel/child/persistence/parent audit path. All worker and helper
groups settle, parent disposable grants close and fresh exclusive reacquisition
passes. Actual tiny fixture/fake-helper hashes are checked. Canonical inventory,
admission/child argv and interpreter SHA remain explicit doubles; these controls
are not canonical IO admission or actual SDK/native plan qualification.

## Prepared shared native V1 request

[Exact request](../../doc/shared-sdk-host-request-v1.json) and
[plan](../../doc/shared-sdk-host-plan-v1.json) freeze125 execution sources,
20 prerequisite receipts, the existing qualified reference and unqualified
experimental artifact, and three retained SDK-generated codecs. Metadata-only
preflight passed without opening tool/fixture payloads. The generated fixtures
remain their exact0644 native identities;0400 inputs are also supported. The
worker performs read-only access and preserves exact metadata, not a chmod or
recopy. Input provenance is the pinned historical generated-input READY/plan,
not Photo's separately owned readonly-copy contract.

[Seven policy/entry controls](../qualification/sdk-shared-generated-fixture-policy-source-actual-20261016.json)
include0400/0644 acceptance and matching0600 refusal. Driver source opens hashing
streams `rb`; the pinned SDK file-stream constructor defaults to output=false.
The source checks do not prove runtime behavior of the experimental tool.
The new request covers12 serial SDK calls/reference1/experimental1,2,6 under
Unison8+EXglobal; no admission exists and no runtime is dispatched. Task/allocator
observations and validation-result parity will not establish pixels, OS-thread
hard caps, RSS, scaling speedup or throughput. A new exact Root admission is
required; historical18-credit plans and prior consumed SDK slots stay unchanged.
