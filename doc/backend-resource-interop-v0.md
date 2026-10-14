# Pluggable backend resource interop, version0

This is the generic contract being implemented for format validators and native
backends. It supplements exact semantic-transfer and receiving-validation
contracts; a resource receipt never proves metadata identity, current edits,
preview reuse or rendering fidelity. Static trusted registration and endpoint
policy remain authoritative. No code or executable path is accepted from a peer.

The existing extension registry selects format interpretation independently of
filesystem capabilities. The validator registry selects post-materialization
checks independently of transfer optimization. Both use the shared owner-loop
worker/helper CPU and I/O supervisor. Their metadata work already uses bounded
payload/descriptor admission. The native `unison_memory::Budget` component now
provides a backend-independent quota, with the Adobe allocator as one injected
adapter. The owner-side validator registry now accepts immutable backend
declarations, and the core includes them in publication/validation admission.

Each backend must declare a versioned immutable resource plan before candidate
creation: maximum runnable CPU lanes (including caller and nested codec work),
covered allocation capacity in bytes, estimated uncovered workspace, descriptor
requirements, enforcement mechanism and its qualified coverage. Keep estimates,
actual enforced limits and measured usage distinct. Unknown or unsupported
coverage never upgrades to a full process/RSS bound. A declaration must specify
which limits apply to an individual allocation pool, process or whole operation.
Each endpoint chooses its own compiled adapter, qualified executable and settings.

Core must reserve the complete worst-case selected plan with the publication
transaction before opening/cloning staging. Refining recognition may release
unused capacity; changing a selected declaration currently requires restarting
Unison. Its first enabled selection pins the plan for the process lifetime.
This prevents a backend from growing into
space already reserved for retained metadata.
Resource-bearing enabled/disabled participation is now pinned as well. A
backend disabled at first selection cannot later become resource-bearing, and
an enabled resource-bearing backend cannot be disabled in the same process.
Otherwise re-enabling could add unreserved workspace to an already-staged
candidate whose metadata envelope happens to be large enough numerically.
Companions using `BackendResources.none` retain their existing policy toggles.
Do not hold a metadata consumer lease and then queue for additional memory from
the same gate: multiple staged candidates could deadlock while each waits for
capacity held by the others. Preserve source headroom for bidirectional progress.
CPU/I/O leases cover active work, with one budget for workers and native helpers;
no second allocator/scheduler may invent an independent CPU/memory allowance.

`CandidateValidators.register ~resources` supplies a trusted owner-side provider
of `BackendResources.t`. The sequential validators share one workspace, so the
core reserves the componentwise maximum CPU, memory and descriptor declaration,
adding memory/descriptors to the existing publication envelope. It rejects a
CPU declaration larger than the shared budget. Each invoked backend receives
its own declaration in `CandidateValidator.context.resources`; the aggregate
does not claim aggregate enforcement. Validation borrows the retained envelope
without another debit or a queued upgrade. Standalone validation acquires the
complete validation cost before recognition or helper execution. Existing
companions default to no additional declaration. This is static trusted-code
registration, not runtime loading of peer-supplied plugins.

The regular-file publication path reserves before staging. Existing staged
directory paths admit validation work, but this does not establish that their
entire tree was reserved before creation. With positive `validationtreememory`,
both retained-manifest estimates and parallel file workspaces are reserved
before enumeration; a local gate partitions held credits rather than nesting
global acquisition. Parallel workspace count divides the CPU budget by the
largest selected backend's caller-inclusive CPU-lane declaration. This avoids
reserving one large SDK workspace per core when the SDK uses several cores per
invocation; execution continues using the same weighted supervisor. Initial property reading/serialization is not allocator-
enforced. See the [directory contract](validation-tree-limits.md). CPU
declarations do not force an arbitrary library to honor nested thread limits;
the adapter must enforce and qualify that behavior using the shared supervisor.
Memory estimates, covered allocation quotas and OS process limits remain
separate. Production Adobe v1 does not gain experimental quota enforcement from
this registration API.

The DNG companion now supplies its endpoint-local `adobevalidatorthreads`
declaration to this API. When threads exceed one or `adobevalidatorworkspace`
is positive, the declaration is resource-bearing and therefore immutable while
Unison runs. The workspace preference is a conservative per-invocation native
estimate in MiB, default zero; it is admitted alongside publication/validation
credits. It does not enforce SDK allocation or RSS. Default one-thread/zero-
estimate operation retains legacy resource-free policy toggles. Invalid or
oversized declarations reject before staging/validation. Validation off does
not activate the backend. A declaration does not make the bundled v1 driver
internally parallel: v1 still accepts only `--threads 1`; experimental SDK host
protocols remain separately unqualified and unavailable to this caller.

An in-process backend receives an injected quota owner and implements allocation
and release callbacks for its library. Copies of `Budget` share one state and
capacity; multiple adapter instances can use the same owner. Every allocation
reserves requested backing bytes plus its accounting header before allocating;
SDK blocks additionally charge their wrapper object and the SDK's checked
physical padding. Free returns credits after backing storage is freed. Failed
allocation/construction rolls reservations back, and allocation headers retain
the owner while buffers remain live. Codec C callbacks return null rather than
unwinding an exception through C frames. Counters expose limit/current/peak/live/
denied values for reservations; failed backing allocations can contribute to
peak reservations. These totals must not exceed the declared covered capacity.
Bookkeeping-state/malloc-internal overhead and heap caches are not measured RSS.

An external backend receives explicit limits through a pinned, versioned argv
protocol and must expose coverage/usage tied to its qualified build. The native
helper launcher independently supports qualified descriptor hard limits before
exec. Unsupported OS memory-limit installation fails before target execution.
The experimental Adobe host-budget protocols are separate from production v1;
current Unison cannot invoke them as v1. Source compilation and synthetic tests
never qualify actual SDK execution or advertise a production capability.

The Adobe adapter covers `dng_memory_allocator::Allocate`, `Malloc` and `Free`,
including the SDK JPEG XL allocator bridge. It preserves SDK checked physical
size/SIMD alignment and keeps its allocator alive through joined area/codec work.
The SDK's `dng_memory_data`, ordinary C++ allocations, XMP internals, library/thread
stacks and allocator cache overhead bypass this quota. Therefore this declaration
is a covered allocation pool, not complete SDK/process memory containment.
Complete containment needs additional qualified mechanisms; macOS RLIMIT_AS
installation was rejected by the current probe. No estimate may hide that gap.

Production admission requires pinned implementation and runtime qualification
for allocation pairing/lifetime, concurrent pressure, failure rollback, nested
CPU behavior, codec coverage and observed usage. Cancellation must stop queued
admission immediately and retire active resources only after worker/child/task
settlement. Plugin or plan changes invalidate reuse of older qualifications.
Original/partial receiving publication follows existing guarded commits/recovery.

Current proof: injected shared adapters, exact boundary/overflow/zero cases,
virtual block deletion, caller/host lifetime separation, C callback failure,
18-lane pressure and malloc-failure rollback are tested without Adobe linkage.
Real SDK1.7.1 header compilation checks single/area/memory/area-memory modes.
[Source qualification](../tests/sdk_memory/qualification.json) keeps these scopes
separate. [Core admission qualification](../tests/backend_resources/qualification.json)
records compiled synthetic-backend registration, no-double-debit admission,
pre-staging rejection, immutable declarations and overflow/borrow controls on
stock and OxCaml. The [participation successor](../tests/backend_resources/participation-qualification.json)
adds pinned activation and a genuine previous-implementation negative control;
the original receipt remains historical. Actual SDK memory/codec parity, whole-process memory,
complete pre-creation directory admission and full M4-V/M6 remain open. Photo Root continues owning preview generators, Lightroom
oracles and publisher recovery; this work starts no competing native operation.
