# Compiler-checked worker boundary: installed-toolchain findings

The historical probe below predates the completed
[production checked boundary](checked-semantic-worker.md). The current OxCaml
build uses Safe.spawn, checked extension handles and atomic counter state.

At the time of that probe, the production worker pool was built and tested on stock OCaml5.5.1 and pinned
OxCaml5.2.0+ox, but remained a manually audited boundary. Its ordinary
`Domain.spawn` call produces `unsafe_multidomain` and `do_not_spawn_domains`
alerts. Runtime tests of exact results/cancellation/settlement do not establish
compiler-enforced portability.

The installed compiler was tested against the real production worker source and
compiler-matched dependency objects, in a separate private tree:

| Probe | Observed result |
| --- | --- |
| Unchanged production worker | Compiles, with existing domain alerts |
| Only change spawn to Domain.Safe.spawn | Rejected: worker closure is nonportable |
| Portable closure capturing an Atomic integer | Compiles and actually executes with expected42 result |
| Closure capturing an ordinary mutable reference | Rejected: contended data required uncontended |
| Same reference guarded by a plain Mutex | Still rejected: the compiler cannot derive safe capsule access from that lock protocol |

[Pinned evidence](../tests/oxcaml_boundary/qualification.json) retains the
compiler, installed Domain/Mutex interfaces, current source dependency graph,
private object hashes and exact diagnostics. [Reproducer](../tests/oxcaml_boundary/probe.py)
requires an actual compiler-matched retained worker build. No production files
are patched by the probe. The positive control is an API mechanism check, not a
qualified production worker or SHA-256 backend.

The next implementation must preserve the owner-loop Lwt/RPC/archive boundary
while making domain-visible state compiler-checkable. The current shared record
combines mutable queues, counters, stopping state, raw notification descriptor
and mutex/condition references. A normal mutex wrapper does not by itself give
these fields portable modes. Queue data needs an actual mode-aware synchronized
container/capsule or a bounded portable atomic representation, with explicit
job/result ownership transitions. Simply annotating mutable fields as portable
or suppressing alerts is insufficient.

Selected extension handles must also carry portable worker-call interfaces;
owner-only registry/feature functions must not enter the domain closure.
Hash/file/delta operations and their foreign interfaces need individually
justified mode contracts. Compiler checking cannot prove ownership or thread
safety inside C, so retained native FFI audits and descriptor/cancellation
settlement tests remain required. Detached child execution is not a substitute
for the requested parallel worker data path.

Implement a compiler-selected backend without weakening stock OCaml support.
Use an actual supported mode-aware synchronization/task facility from the pinned
installation after its API/lifetime qualification. The installed
`capsule0.blocking_sync` explicitly deprecates its heavyweight synchronization
in favor of Await; choosing its convenient spelling alone is not justification.
The installed Domain API also warns against mixing a new Multicore scheduler
with independent spawned domains. Backend selection must retain one runtime,
shared CPU owner and native-thread admission, not start a second pool.

Acceptance requires compiler-negative capture controls, real hashing/inspection/
apply jobs, exact outputs, queued and active cancellation, pool shutdown,
notification/descriptor settlement, helper contention and mixed compiler wire/
archive tests, followed by measured throughput/RSS/resource evidence. Full
worker portability and the wider M6 milestone remain open. No Photo/Adobe or
native preview work is part of this investigation.

The later atomic mailbox and File/Hash contracts are now joined by checked
extension/recognition/observation/delta interfaces and atomic counters. The
actual complete worker closure compiles with Safe.spawn. The former worker
still rejects against those new interfaces because its running field is mutable;
this isolates the counter migration rather than weakening capture checks.
See [current qualification](checked-semantic-worker.md). Full M6 remains open.
