# Receiving validation tree limits

Optional endpoint-local preferences bound the structure of each receiving
validation manifest:

```text
validationtreeentries = 100000
validationtreepathbytes = 16777216
validationtreememory = 64
```

Each defaults to zero, preserving unlimited legacy enumeration. Negative values
reject when receiving validation runs. Limits apply separately to the before and
after snapshots of a finalized candidate, including its root, directories,
symlinks, hidden entries, auxiliary names and temporary-looking names. The entry
counter includes discovered but not yet inspected children. Path accounting adds
each relative path's bytes, including its parent prefix and separator. The root
uses its actual private staging name, so changing that name changes the count.

The directory reader checks global cancellation before each read. It charges a
discovered child before appending its name or constructing its Path object.
Limit/cancellation failure closes the native directory handle. A limit error is
an operational receiving error under both `require` and `warn`; no helper runs
if the initial snapshot fails. If a helper adds a hidden entry that exceeds the
limit in the final snapshot, ordinary failure handling rejects publication and
discards private staging. Live destinations and source inputs remain untouched.

`validationtreememory` is an opt-in retained-manifest estimate in MiB; zero
preserves legacy unadmitted manifest accounting. A positive value reserves two
snapshots plus a fixed number of file-validation workspaces before enumeration.
Unbound directories divide the shared CPU budget by the largest selected
backend's caller-inclusive CPU-lane declaration (legacy resource-free backends
use one lane). Regular files and existing
bound publication envelopes use one workspace. Each file workspace includes
the largest selected sequential backend declaration. A local admission gate
partitions the held credits, so child validation never queues for another
global lease. Shared weighted CPU and filesystem execution admission still
apply. Every active child settles before the parent releases, including on
rejection and cancellation.

The estimate charges 1,024 bytes per discovered entry, eight times relative path
bytes, and eight times serialized property/symlink target bytes. Charges reject
before retaining an over-budget entry. Each before/after snapshot is capped
separately, and both are reserved because they may coexist during comparison.
Regular-file publication adds both estimates to its existing envelope, even
when validators are currently off. The first observation pins the memory
declaration; changing it requires process restart. This prevents later policy
enablement or budget growth from consuming retained metadata capacity.

An unbound directory reserves `2 * manifest + N * (1 MiB + backend bytes)` and
`15 + N * (9 + backend descriptors)`, with N up to the configured CPU budget.
The parent is one global transaction; the child gate partitions its N workspaces.
N is `floor(CPU budget / max(1, backend CPU lanes))`, so an 18-core budget gives
18 one-lane, six three-lane or one 18-lane backend invocation. Actual native
thread compliance remains the backend's separately qualified responsibility.
If this complete plan cannot fit, admission rejects before enumeration. For
18 workspaces and no added backend declaration, a 64 MiB manifest budget needs
146 MiB and 177 descriptor credits. Source service headroom remains protected.

These remain estimates, not allocator-enforced heap/RSS limits. Initial property
reading/serialization, cache/allocator overhead, source-side archives and SDK
heaps are outside the estimate guarantee. Entry/path caps are independent;
property and symlink bytes are not path bytes. Directory staging was already
created before unbound validation admission; complete pre-creation directory
admission remains separate work.
These limit settings and implementation code are not accepted from a peer; the receiving
endpoint's local preferences are authoritative.

[Qualification](../tests/validation_tree_limits/qualification.json) records
stock/Ox actual-object arithmetic checks, seven actual receiving cases and a
controlled native-directory cancellation probe. A private negative removes only
the per-read cancellation check and fails the same designated oracle. The
probe does not establish interruptible filesystem syscalls or a wall-clock
cancellation deadline. All fixtures are private synthetic data; no Photo,
Adobe runtime or Lightroom operation is involved.

The [memory-admission successor](../tests/validation_tree_limits/memory-qualification.json)
adds actual single-global-transaction partition tests, two concurrent synthetic
helpers, oversized reservations and retained estimates, declaration pinning,
and same-process success/rejection/cancellation/retry with settled ledgers.
The original structural receipt remains historical.

The [nested-workspace successor](../tests/validation_tree_limits/nested-workspaces-qualification.json)
proves a two-lane backend holds both shared permits with one workspace: its
7 MiB envelope fits an 8 MiB budget. The exact preceding CandidateValidation
implementation requests 12 MiB and fails the designated overreservation oracle.
Both legacy and nested fixtures settle success/rejection/cancellation/retry in
the same process. These are synthetic permit/admission proofs, not actual SDK
threading or CPU-utilization measurements.
