# Runtime and report settlement

These source probes qualify resource ownership around actual asynchronous
runtime work and read-only semantic reports. Private legacy-Lwt instrumentation
watches actual returned promise identities and fails one or two observer
installations with distinct preallocated exceptions. Promise state and payloads
are never modified.

The runner links a compiler-matched full core, rebuilding dependencies after the
private Lwt implementation so native optimization assumptions remain consistent.
Actual preferences, resource gates, CPU scheduling, filesystem admission, worker
domains, held-file owners and Remote cleanup registries remain in use. Test-only
exports observe private slot/held-file state and request ordinary cleanup.

Runtime controls allow two filesystem leases for an outer `with_io_file` and
its actual worker on the same device. Report controls cover the SIR/0 mapper and
the meaning-enabled path, held-file closing, cancellation, retained scalar
resource loans and concurrent reports. Actual Atomic-paused callbacks and a
kernel FD census independently expose early closure or retirement while the
owner event loop continues running.

The scoped RPC control uses the real connection, bounded server command,
argument decoder, `processRequest` dispatcher and output queue on its own socket
pair. It excludes the version handshake and client receive parser. Its 512 KiB
answer is preallocated fixture data, outside the tiny profile's resource-cost
estimate: this control proves temporal Source retention through a sleeping
output action, not that those credits bound the custom answer's memory. A
normal reply must decode to one exact id/header/body with no trailing packet.
An output-observer failure may leave the copied final buffer tail unsent; the
received bytes must remain a prefix of the expected reply, with no appended
exception packet. The fixture never forces a flush or replays that reply.

The runner restores exact parent `2059949` owner implementations for negative
controls while retaining the current `BorrowedWork` support API needed to link
the fixture. This is a documented mixture, not a complete parent binary. A
separate private group mutation removes only started-participant tracking and
settlement guards; actual descriptors and resource credits identify its early
return independently of the mutated implementation.

The full-core probes deliberately keep the worker's explicit cancellation token
separate from the Runtime wrapper's inherited token. Connection cleanup can
therefore retire the wrapper while the actual borrowed worker remains paused.
This tests retained ownership across cleanup; automatic propagation from that
inherited token to the independent worker is not asserted.

All files are small synthetic fixtures in private temporary directories. No
Photo, Lightroom, Adobe SDK, production volume or benchmark work is authorized
by this preparation. Persistent allocation failure, arbitrary asynchronous
exceptions and a complete process RSS/FD ceiling remain outside its scope.

After a production freeze and a matching isolated native Make snapshot are
available, run with `--build`, `--ocamlopt`, `--freeze`, `--keep-work` and
`--receipt`. Stock and OxCaml runs are sequential. Receipts retain the original
and privately transformed sources, compiler/native objects, exact commands,
logs, binaries and test files, including any failed fixture trials. Preparation
does not authorize qualification while another session owns an active native
oracle window.

Qualification on the frozen 331-input production source passed with stock OCaml
5.5.1 and genuine installed OxCaml 5.2.0+ox, sequentially. Each compiler passed
67 current controls and detected six exact-parent owner regressions plus two
private untracked-group regressions. Runtime/report FD, CPU, filesystem,
transaction, descriptor, payload, pending and slot owners settled after the
actual workers or output actions stopped. The output-error controls received
512,000 bytes of the expected 524,356-byte reply, an exact packet prefix with no
appended exception; normal/scope controls decoded one complete reply.

[qualification-20261013.json](qualification-20261013.json) pins both final
receipts and all retained fixture trials. Initial preflight and private compile
failures were fixture issues: generated ProjectInfo comparison, three OCaml
syntax/type mistakes and collision with the production Test interface. One
partial runtime trial exposed an early assertion on the second report observer;
it was moved to the actual installation phase before the final full reruns.
Production source stayed frozen throughout. OxCaml's legacy `Domain.spawn`
safety alerts remain in the logs; this qualification does not claim a compiler
proof for that manually audited boundary.
