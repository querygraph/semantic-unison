# Checked production semantic worker boundary

OxCaml now compiles the actual SemanticWorkers domain closure through
Domain.Safe.spawn. Job/completion mailboxes, cancellation flags and stopping /
running / peak state are atomic. Counter transitions and condition waits retain
the existing mutex, preserving the no-lost-wakeup and coherent usage protocol.
The owner record, Lwt promises, CPU/I/O admission, RPC and archive operations
remain outside the domain closure. Stock OCaml retains the same runtime protocol
through ordinary Domain.spawn.

FormatRecognition and FormatExtension now have compiler-selected portable,
contention-safe abstract immutable handles. Their packaged module signatures and
observer callback fields carry matching contracts. Built-in DNG recognition,
classic/extended DNG and JPEG inspectors, XMP observations, and worker-safe
SemanticDelta operations compile against checked interfaces. Proofs and plans
remain immutable. Registry operations and the registry-resolving apply variants
are explicitly nonportable. SemanticFormats keeps its owner-only interface and
accepts only a package satisfying the checked extension contract on OxCaml.

The build selector checks every template against an exact transformation of its
ordinary interface; signature/field/native/spawn marker counts must match.
No peer-supplied executable code, unsafe cast or alert suppression is added.
Stock extensions still rely on a locally trusted callback audit. OxCaml checks
captured OCaml state, while bounds, algorithm behavior, descriptor lifetime and
native/Unix foreign code retain manual contracts and runtime qualification.

The installed compiler retains its do_not_spawn_domains scheduler warning for
Safe.spawn. This change keeps the existing single endpoint pool and shared
HelperSupervisor CPU owner; it introduces no second Multicore scheduler. Auto
runtime admission still uses physical cores on macOS (18 on this host), and
weights externally parallel helpers against that same owner. Individual tests
use at most18 active worker credits and run the large worker suites sequentially.

Tests use actual compiled Make objects, without replacing their interfaces.
They exercise18-domain hashing and extended DNG inspection/application, typed
recognition,48 parallel metadata observations against sequential full transcripts,
queued/active cancellation, helper contention, filesystem admission, owner
responsiveness, exact bytes and descriptor settlement. Seeded hash/inspection and
apply scheduling tests cover receipt delivery and retry. Compiler negatives
reject mutable recognizer/inspector/observer captures, owner registry and pool
captures, and the real former worker with mutable running counters even when
compiled against current checked extension interfaces. Make and Dune each build
and run CLI selftests with stock5.5.1 and OxCaml5.2.0+ox.

Separate injected acquisition/waiter faults qualify resource-settlement behavior
in private instrumented source. They do not claim that the injected mutable
fault infrastructure is itself a checked production domain closure. Historical
acquisition negatives adapt mailbox and atomic-counter representation only;
the original ownership guards remain unchanged.

[Qualification](../tests/checked_worker/qualification.json) distinguishes these
artifacts and limits. This completes the OCaml worker portability integration,
not all M6: hard RSS/FD/global ceilings, native ownership/fault coverage, matched
throughput/resource measurements, GUI/platform gates and remaining Adobe SDK
qualification are separate requirements. No Photo/Adobe invocation occurred.
