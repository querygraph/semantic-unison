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
adapter. Core scheduling of backend memory declarations is the next integration
step; it is not implemented by merely adding this C++ component.

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
unused capacity; increasing a plan requires a fresh reservation/transaction.
Do not hold a metadata consumer lease and then queue for additional memory from
the same gate: multiple staged candidates could deadlock while each waits for
capacity held by the others. Preserve source headroom for bidirectional progress.
CPU/I/O leases cover active work, with one budget for workers and native helpers;
no second allocator/scheduler may invent an independent CPU/memory allowance.

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
separate. Actual SDK memory/codec parity, core memory-plan scheduling and full
M4-V/M6 remain open. Photo Root continues owning preview generators, Lightroom
oracles and publisher recovery; this work starts no competing native operation.
