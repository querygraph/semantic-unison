# Manual audit of new foreign boundaries

Current owner-loop addition: durable reservations start before native target
preparation and survive producer return. Explicit semantic/validation loans
retain that envelope through settlement; native close precedes retirement.
`Lwt.wakeup_from` publishes a preallocated completed state before observer dispatch,
avoiding a result-constructor allocation at the debit/reply handoff. Early reader,
worker, nonce, helper/CPU acquisition and PID ownership guards have separate finite
controls. See [resource-admission.md](resource-admission.md) and the component
receipts linked by [SOL.md](../SOL.md). This adds selected lifetime admission;
it does not establish a complete native/heap/process resource cap or universal
allocation-failure recovery. Existing native positional-write contracts remain.

Reviewed on 2026-10-13 against the uncommitted `feat/semantic-dng-oxcaml` tree.
This covers the new SHA-256, positional-write and helper supervisor primitives,
`unison_clone_stage`/`unison_clone_stage_status`/`unison_clone_stage_handles`,
`unison_file_observation` and the `unison_stage_publication_*` primitives, their
ML declarations, and
their current call owners.
It is a manual ownership/rooting audit, not a compiler proof, sanitizer result
or qualification of untested platforms. Existing clone/range primitives and
other inherited Unison C code require separate review.

## SHA-256 primitives

Declarations are private to [SemanticHash](../src/semanticHash.ml):
`native_init : unit -> bytes option`,
`native_feed : bytes -> bytes -> int -> int -> unit`, and
`native_finish : bytes -> string`. [The C implementation](../src/semanticHash_stubs.c)
uses CommonCrypto on macOS; other platforms return `None` at initialization
and use the portable ML reference. Native feed/finalize raise if invoked on
those platforms. The public context type is abstract.

| Function | Roots, allocation and runtime | Buffers and ownership | Cancellation and ABI |
| --- | --- | --- | --- |
| `unison_semantic_sha256_init` | `CAMLparam1(unit)` and `CAMLlocal2(context,result)` cover both allocations. Runtime remains held. | A stack-aligned `CC_SHA256_CTX` is initialized, then copied into newly allocated ML bytes. `Some` contains those bytes. No native resource survives independently of the ML context. | Short native call with no cancellation hook. Context layout is the compiled CommonCrypto ABI; bytes are never serialized or passed to another executable. |
| `unison_semantic_sha256_feed` | All four arguments are rooted; no ML allocation on success. Runtime remains held while reading ML buffers and writing context bytes. Error helpers may raise with roots live. | Context byte length must equal `sizeof(CC_SHA256_CTX)`. Offset/length arithmetic is checked before access; chunks are at most 65,536 bytes. Context is copied to a stack-aligned native object, updated, and copied back. Input is read-only. | No callback or runtime release; cancellation is cooperative between bounded reads/chunks in callers. The chunk cap fits `CC_LONG`; no heap pointer is retained by the stub after return. |
| `unison_semantic_sha256_finish` | Context rooted, output rooted. Runtime remains held. The 32-byte result allocation occurs after finalization. | Stack-native context and digest; context bytes are zeroed, then digest copied into a fresh ML string. ML wrapper forbids reuse after finalization. An allocation exception loses a completed digest but leaks no FD/native allocation. | No in-call cancellation. SHA-256 output is exactly 32 raw bytes. Non-macOS calls raise; portable fallback is selected at create time. |

There is no mutable C global state or OCaml callback. The portable constants
are read-only ML data; each reference state owns its arrays/buffer. Current
worker callers create contexts inside a job; owner-side envelope/report
validation creates separate contexts. A `SemanticFile.iter` scratch buffer is
local to that invocation and is consumed synchronously. Context exclusivity is
a manual caller contract: the abstract type does not statically prohibit two
domains from sharing the same context or a caller from mutating input bytes
concurrently. Retaining the runtime does not itself make that sharing safe.

Evidence: native/reference parity and externally generated SHA vectors in
[kernel tests](../tests/semantic/test.ml), and 36 actual domains, cancellation,
mutation checks and repeated lifecycle/descriptor tests in
[worker tests](../tests/workers/test.ml). These do not constitute a race
sanitizer run; the pinned compiler reports TSAN unavailable.

## Positional semantic output

[SemanticFile](../src/semanticFile.mli) exposes an abstract borrowed `writer`.
`prepare_writer` admits a private singly linked regular output; it owns no FD.
The existing caller keeps that FD live, its status flags stable and output
access exclusive until retirement. Workers retain their duplicate through job
settlement; synchronous callers retain their existing ownership. Preparing an
unchanged plan still checks admission. An allocation failure creating the ML
record cannot leak a new native resource.

The private [native primitives](../src/semanticFile_stubs.c) have these boundaries:

| Primitive | Roots, runtime and buffers | Effects and error contract |
| --- | --- | --- |
| `unison_semantic_prepare_writer` | FD rooted. Pending actions dispatch before interpreting the borrow. POSIX releases through no-pending entry for `F_GETFL` and `fstat`; only stack/native values are used. No FD is allocated or consumed. | Rejects read-only/append flags, nonregular/negative-size/multiply linked outputs. Returns an immediate backend boolean or saved Unix error after acquisition. ML retries EINTR with cancellation checks. Windows returns false without interpreting its descriptor as a POSIX integer; ML preserves kind/link checks and legacy seek/write. |
| `unison_semantic_pwrite` | All five arguments rooted. Checks signed slice/subtraction bounds, 64 KiB cap, nonnegative int64 span and native `off_t` round trips before effects. Copies into 64 KiB stack storage while held, then no-pending release. No OCaml heap pointer, allocation or callback is used while released. | One `pwrite`, no C retry. Saves errno before reacquisition, rejects impossible returned progress and returns an immediate byte count or Unix error. Owns no FD and does no pathname/property/flush/rename work. Private Windows invocation raises ENOSYS; the selected ML fallback never invokes it. |

POSIX admission is once per writer, rather than an extra flags/stat query for
every chunk. `SemanticDelta` also keeps its earlier output-link stat, for three
fixed queries on that path. It computes each attempt's absolute offset from
successful progress; EINTR retries that offset and short writes advance it.
Zero/invalid progress terminates. Cancellation is checked before each attempt.
Operational failures do not switch backends or authorize publication. Actual
live-file commit and archive ownership remain with the existing caller.

Rejecting append flags bounds the Linux `pwrite` append behavior documented in
the [Linux man-pages API reference](https://man7.org/linux/man-pages/man2/pwrite.2.html).
The borrowed lifetime requires no concurrent close or `F_SETFL` on the shared
open-file description; an abstract ML type does not enforce that contract
against another process or unsafe caller. There is no new FD identity lease or
hostile flag-change protection.

Each native write preserves the shared position. Entire materialization still
uses seek/read on duplicates for proof and final hashing, which can move it.
Application bytes count successful returned writes; attempts include EINTR.
These counters do not attest physical allocation/writes, durability or speed.
An asynchronous exception after a completed native effect can leave an
unreported private effect. Stack storage is bounded per active call, but is not
an aggregate RSS limit. Native I/O has no in-call cancellation or hard deadline;
Windows/native other-platform runtime qualification remains separate.

Evidence: [direct qualification](../tests/positional_write/qualification-20261013.json)
passes 59 native/application cases plus five explicitly artificial/backend
controls, 64 positive cases / 1,131 assertions per compiler; three designated
source regressions detect the intended defects. The [integration receipt](../tests/qualification/positional-write-integration-20261013.json)
binds fresh 316-input Make/Dune builds/selftests, kernel/conformance/workers,
actual local/remote/old-peer transfers and all 79 final-publication cases per
compiler. Four actual partial-write sync cases and eight finite owner-cleanup
controls pass. Partial private bytes and intermediate failure states are
asserted during execution; later retained artifacts do not reconstruct every
discarded byte. Archive observations remain raw fingerprint-byte evidence.
The [independent acceptance](../tests/positional_write/independent-review-20261013.json)
records read-only source/artifact/log review, not independent test execution.

## Helper supervisor primitives

[HelperSupervisor](../src/helperSupervisor.ml) declares all five primitives.
They run on the Lwt owner domain. Mutable admission, cancellation and process
records remain there; worker domains use atomic cancellation and do not invoke
helper lifecycle code. [The C implementation](../src/helperSupervisor_stubs.c)
has no mutable per-process globals or OCaml callbacks.

| Function | Roots, allocation and runtime | Native resources and ownership | Cancellation and ABI |
| --- | --- | --- | --- |
| `unsn_helper_available_cpus` | Immediate argument/result only; no allocation or exception helper, so no `CAMLparam` is needed. Runtime remains held. | Queries `sysconf(_SC_NPROCESSORS_ONLN)`; invalid results fall back to 1. No owned buffer/FD. | Returns a positive ML integer on tested hosts. This is online CPU topology, not an affinity/cgroup quota oracle. Windows returns 1. |
| `unsn_helper_available_physical_cpus` | Same immediate-only behavior. Runtime remains held. | On macOS, stack `int` plus `size_t` passed to `sysctlbyname`; accepts the expected size and a positive physical count, capped by logical count. Else logical fallback. | No cancellation hook; portable platforms do not gain physical-topology detection. Tested independently against macOS `sysctl`. |
| `unsn_helper_monotonic_now` | Unit rooted; `caml_copy_double` allocates the result. Runtime remains held; error helper preserves roots. | Stack `timespec`; `CLOCK_MONOTONIC`, no owned resource. | POSIX clock/time ABI. Windows primitive raises, and the supervisor's Windows branch avoids it. Calls do not establish a hard deadline for blocking OS operations. |
| `unsn_helper_exited_unreaped` | PID rooted; immediate boolean result. Runtime remains held. | Stack `siginfo_t`; `waitid(P_PID, ..., WEXITED\|WNOHANG\|WNOWAIT)` retries EINTR. Successful observation does not reap the child. | ML retains PID/group ownership until `waitpid`; group termination precedes reaping to avoid signaling a recycled PID. Requires POSIX `waitid`/`WNOWAIT`; other platform ABI qualification remains open. |
| `unsn_helper_spawn_group` | All five arguments rooted throughout. Runtime remains held. No ML allocation on success; error/out-of-memory helpers run after native cleanup. | Copies argv/env strings into malloc-owned, NULL-terminated vectors and frees them on every path. Executable string is borrowed only while runtime is held. File actions/attributes have initialization flags and are destroyed if initialized. stdout/stderr FDs are duplicated above 2 with CLOEXEC, and temporary duplicates closed on success/error. Original FDs remain ML-owned. | `posix_spawn` returns a PID in a new process group; no forked OCaml code executes. stdin is `/dev/null`; stdout/stderr redirected; signal mask/defaults reset. `POSIX_SPAWN_CLOEXEC_DEFAULT` is used when available. Windows raises. Spawn itself has no cooperative cancellation point. |

ML checks an absolute NUL-free executable, NUL-free argv/environment and valid
limits before dispatch, constructs argv[0], and creates CLOEXEC pipes. Capture
ends are nonblocking and drained with bounded reads on each owner turn. Only
the owner closes them. The C stub does not consume or close the caller's FDs.
It returns a PID, not a native handle requiring finalization.

CPU permits and child admission are held through child termination/reap.
Ordinary cancellation sends TERM then KILL after grace. Disconnect cleanup
kills/reaps synchronously even if the owner loop will not tick again; a
release-once wrapper prevents duplicate permit return. The process-group
contract assumes a trusted helper does not escape the group or change
credentials. `ECHILD` handling avoids signaling a PID already known to have
been reaped elsewhere; the intended owner is the sole reaper for these PIDs.

Unresolved limits: `posix_spawn` is synchronous with the runtime held, and
exceptional reap can block in the OS. Monitoring cannot enforce a hard timeout
while the owner is inside those calls. On platforms without CLOEXEC-default,
unrelated non-CLOEXEC descriptors are not forcibly closed by this stub;
macOS descriptor isolation has a dedicated test. CPU reservation is a declared
helper weight, not measured enforcement of native thread creation. There is
no child RSS limit or sandbox.

Evidence: [helper tests](../tests/helpers/helper_tests.ml) cover literal argv,
simultaneous bounded streams, timeout escalation, weighted admission,
cancellation, stopped-owner disconnect/reap, process exit cleanup, macOS
descriptor isolation, descendants and spawn failure. Actual SDK qualification
is separate from these synthetic supervisor controls.

## Receiver-local clone stage

[Fs](../src/fs.ml) declares the compatibility option-returning
`clone_stage_raw`, strict `clone_stage_status_raw` and additive strict
`clone_stage_handles_raw`, each taking two strings after normal filesystem path
translation. All three exported primitives share
[unsn_clone_stage_impl](../src/copy_stubs.c). Legacy `Some` and strict
`Shared_stage` retain their two-FD layout; `Shared_stage_handles` contains basis,
output and actual creation parent. Strict declines retain the tagged immediate
reason layout. Ordinary receiver Copy uses the three-FD result; other Copy,
SemanticSync and SemanticRemote consumers keep the strict two-FD result. These
handoffs happen on the owner before worker descriptor borrowing. The option ABI
remains available.
Semantic async callers hold transaction credits before cloning; generic copy
uses its existing lifecycle. Workers receive duplicated FDs after return.

Both input strings are rooted and result blocks use `CAMLlocal3`: the FD pair
or triple, success wrapper and strict decline wrapper. All descriptor fields are
initialized before later allocation. All result allocations precede
native resource acquisition; returned FD fields are filled only after runtime
reacquisition, without another ML allocation on success. Source,
destination and scratch names are copied into malloc-owned buffers before
runtime release. While released, native code uses only those copies, native
FDs, stack `stat` values and malloc-owned xattr storage. It reacquires before
raising a Unix error or filling the preallocated result. There is no callback or
mutable C global. `unsn_same_basis` is a pure stack-stat comparison.

The macOS backend opens the source without following a final symlink, checks a
regular unflagged file, opens the parent directory, and uses exclusive clone
creation. Source FD/path stamps are checked after making the private basis.
The output is data-only: ACL, mode and xattrs/resource-fork inheritance are
cleared before return. A second opened output FD is checked against the FD
used for metadata changes. The immutable basis is unlinked; its read-only FD
and the output read-write FD transfer to the caller. The three-FD ABI additionally
retains the actual native creation parent, without reopening its pathname; all
other outcomes and both old ABIs close that parent. Other native FDs and
malloc/ACL storage have cleanup paths before return. Strict declines distinguish
platform absence, nonregular source, source flags, cross-device pair and
unsupported operation; they are observations, not cached volume capabilities.
Only first-basis-clone ENOTSUP/EXDEV/ENOSYS become native declines. Later clone,
identity, ACL/mode and attribute failures retain their original errno and native
phase in `Unix_error`. Legacy declines remain `None`. Copy and both semantic
consumers fail a nonregular basis rather than fall through to an ordinary basis
open. Namespace deletion on error is best effort, not a guaranteed absence of
temporary artifacts. Non-macOS/older-runtime branches decline without owning
native resources.

POSIX descriptors are represented by immediate ML integers. The implementation
is gated to macOS 10.12 APIs, uses Darwin `stat` timestamp/flag fields,
`fclonefileat`, ACL and xattr signatures, and requires the host compiler's
availability check. It is not a Windows FD ABI or a qualified Linux/ZFS/ReFS
clone implementation. No C string-length/NUL check is added here; callers
must supply valid filesystem paths.

### Findings and remaining qualification

1. **Success-path allocation was moved before native acquisition.** The audit
   found tuple/option allocation after successful FD/stage acquisition, where
   an allocation exception bypassed native cleanup. The current source
   preallocates the FD pair/triple and success wrapper, plus the strict decline
   wrapper, under three local roots before native resources are acquired and
   fills their immediate FD fields after reacquiring the runtime. This removes
   that C result-allocation exposure by source inspection; it does not close
   every exceptional ownership window in the caller. Allocation/OOM fault
   injection remains unqualified.
2. **File opens now use O_NONBLOCK before regular-file checks.** The audit found
   a FIFO input could block before `fstat`, preventing owner cancellation from
   running. Source and private-file opens are now nonblocking. Native tests
   reject a direct FIFO promptly, and a private baseline source negative
   control reproduced the old two-second timeout. Runtime release still does
   not make clone/metadata calls asynchronous or impose an OS deadline.
3. **Stage-name ownership has a namespace assumption.** Metadata clearing
   checks the regular FD it opened, but does not establish that it is the inode
   originally created by cloning. A same-UID writer replacing the private
   stage with a regular file/hardlink could redirect metadata changes before
   first admission. The current source checks single-link regular
   basis/stage inodes, distinct source/basis/output identities and matching
   devices before metadata clearing, then rechecks writable output identity
   and link count. These defend against a hardlinked replacement, but cannot
   prove object birth after replacement by a moved regular file. The scratch
   follow-on now checks each current name through the retained parent and cleans
   only names matching still-held admitted witnesses. Parent pathname rebinding
   no longer redirects reservation or cleanup. Trusted staging
   directories and cooperative namespace ownership remain required; this is
   not a same-UID sandbox.
4. **Cancellation and memory remain limited.** Native clone/metadata syscalls
   have no in-call cancellation hook or hard deadline. The xattr list uses
   native allocation outside the payload estimate. The reservation FD now uses
   `O_CLOEXEC` at exclusive relative creation and stays held through removal.
   Direct close/unlink failure controls qualify cooperative cleanup and explicit
   preserved-artifact outcomes; they do not establish crash recovery or a
   complete-lifetime descriptor/memory budget.
5. **Failed-clone creation tracking follows Apple's documented contract.**
   Apple's [clonefile manual](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/man/man2/clonefile.2)
   describes clonefile, clonefileat and fclonefileat as atomic: creation either
   succeeds for all new objects or creates none. The engine never removes a
   destination after a failed clone; successful creation still needs an
   admitted held witness before authorizing later name cleanup. The public
   [VFS implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/vfs/vfs_syscalls.c)
   checks existing destinations and cross-mount pairs before VNOP_CLONEFILE,
   then delegates creation to that filesystem operation; it contains no
   independent unlink rollback for a failing VNOP. This source review does not
   establish APFS fault behavior or power-loss recovery. Do not blindly unlink
   after a failed clone: an EEXIST destination belongs to someone else.
6. **Cleanup retains the first operational failure.** Error paths remove only
   names matching held admitted witnesses before closing those witnesses.
   A close/unlink failure without an earlier error becomes an operational
   failure, including after a scoped decline. With an earlier error, its errno /
   phase survives; a second cleanup failure is not separately represented.
   Direct fault controls now qualify replaced names, repeated errors and
   recycled-FD survival. A failed first admission or repeated cleanup failure
   can leave an artifact, and a last legacy parent-close error can leave linked
   output. Orphan recovery and crash durability remain open.
7. **The C pending-handler buffer window has a specific fix.** OCaml 5.2's
   [blocking-section entry](https://github.com/ocaml/ocaml/blob/5.2/runtime/signals.c)
   can dispatch a raising pending signal handler. The pinned OxCaml source has
   the same entry behavior. The shared stage body now processes pending actions
   before the first path allocation, uses blocking-section entry without pending
   dispatch while it owns native resources, and frees all path/xattr buffers
   before runtime reacquisition. These operations close that buffer window by
   source inspection; they do not freeze delivery after returning to ML.
8. **ML handoffs now guard synchronous initialization/registration failures.**
   Copy protects channel creation and both registrations, including the local
   source channel; setup errors close the channel objects rather than re-closing
   their original FD integers. The synchronous semantic path guards allocation
   of its ownership closures. Async semantic transactions/candidates separately
   guard owner-record creation and registration, emptying/marking the owner
   before best-effort unregister so retained cleanup entries cannot close reused
   FD integers. Source-FD list retention and remote source/report holder
   registration have equivalent guards. The guards finish before workers borrow;
   existing deferred cleanup retains borrowed descriptors until settlement.
9. **Arbitrary asynchronous exceptions remain a separate qualification.**
   The pinned OxCaml runtime raises ordinary allocation Out_of_memory through
   its synchronous exception path. Its Sys.with_async_exns documentation instead
   concerns asynchronous Break/Stack_overflow, which can bypass ordinary try
   guards; this compiler-specific API is not added to portable consumer code.
   Delivery between successful C return and ML ownership capture, interrupted
   cleanup state, actual memory exhaustion and failing cleanup remain outside a
   complete resource guarantee. Three C roots and ML handoff catches do not
   establish universal exception safety.

Evidence: [clone-stage tests](../tests/clone_stage.ml) cover exclusive creation,
read-only input, source preservation, stable unlinked basis, ACL/xattr/resource
fork clearing and flagged decline. Native nonblocking FIFO rejection passes
both compilers, with a private old-source timeout negative control.
The coordinating root additionally reports strict decline-scope, native phase
and descriptor checks passing stock/Ox in an isolated harness; this document
update did not rerun those builds or tests.
The focused [handoff driver](../tests/test_clone_adoption.py) injects synchronous
Failure/Out_of_memory at actual production initialization/registration sites,
including before/after registry installation. It checks FD/name cleanup,
unchanged source, original exception, reused-FD survival on disconnect and
successful follow-up. All 40 current cases and 36 private old-handoff leak
controls pass per compiler, stock and Ox. The adjacent local source handoff has
positive fault coverage without its own old-handoff control; rsync setup ref
rollback is source-reviewed and normal-integration-tested. The independent
[pending-signal counter fixture](../tests/test_clone_stage_signals.py) also
passes both compilers: the declined path frees all owned buffers while the old
release boundary leaks exactly three. These controlled exceptions are not actual heap exhaustion or arbitrary
signal-delivery qualification.
Generic/local/remote integration covers normal candidate lifecycle and
cancellation. The additive [creation-parent suite](../tests/clone_handles/README.md)
passes 20 native cases on both compilers: all three descriptor identities/modes,
parent replacement during and after native cloning, held-parent lookup/cleanup,
source properties, repeated resource cleanup and both old ABIs. Its preallocation
source-order check is not allocator-exhaustion qualification. These tests do not
qualify real OOM, hostile stage-name mutation or crash durability. The later
[native scratch slice](native-scratch-next.md) replaces pathname reservation
with bounded exclusive `openat` and held-witness `unlinkat`. All three ABIs now
keep reservation and clone namespace operations under the retained parent.
Both compilers pass 182 direct APFS cases / 1,984 assertions, including actual
recycled-FD close errors and two designated source regressions through every
ABI. Cleanup precedes witness close; slots clear before one close attempt and
the first operational failure survives cleanup. First clone-to-open admission
intervals and cooperative comparison/unlink remain explicit limits. Repeated
failures or late legacy parent close may leave artifacts. Existing stale-temp
pathname cleanup can later act on those names; they are not durable quarantine.
The pending-signal fixture remains at zero owned buffers versus three in the
old-release control. Current Make/Dune builds and synthetic caller reruns are
pinned in the [scratch integration receipt](../tests/qualification/native-scratch-integration-20261013.json).

## Held-descriptor observation and borrowed lease

[FileObservation](../src/fileObservation.mli) declares
`observe : Unix.file_descr -> t`, backed by
[unison_file_observation](../src/fileObservation_stubs.c). It returns a flat
record of file identity/kind/size/links/flags, filesystem identity/mount flags,
optional volume UUID and exact mtime/ctime seconds/nanoseconds. IDs use fixed-width
lowercase hexadecimal on macOS, without floating-point or machine-int narrowing.
The observer reports native facts; it does not attest immutable content, clone
capability, physical sharing, a mount incarnation or pathname publication.

| Boundary | Roots, runtime and memory | Ownership, errors and ABI |
| --- | --- | --- |
| macOS native observation | `CAMLparam1` retains the descriptor argument; its immediate fd is extracted before runtime release. `stat`, `statfs`, attribute request/reply and UUID buffers are fixed-size stack values. There is no malloc, new descriptor or callback. Native work reads no ML heap value while released. The result and temporary values use three local roots; all 13 record fields are initialized before later allocations. | The descriptor is borrowed and must remain open/unreassigned through settlement. `fstat`, `fstatfs`, a separate volume-only `fgetattrlist`, and final `fstat` preserve its offset. Native errno and phase are captured before reacquiring the runtime. Final exposed-file-field mismatch raises EBUSY. Negative size/invalid timestamp fractions and unsupported native kind fail instead of fabricating a value. |
| UUID reply parser | `memcpy` decodes the four-byte-packed native reply, avoiding unaligned struct casts. Bounds and exact expected length are checked before UUID access; only the requested common/volume masks and empty remaining groups are accepted. No ML allocation or mutable global state. | Missing UUID bit or an all-zero successful UUID is `None`. Short/oversized/unknown-field replies raise native EPROTO with the volume-attributes phase; syscall errors, including unsupported operations, remain errors. The public SDK/XNU volume query may substitute the mount root vnode, so no file identity fields are requested in that call. |
| Other platforms | The platform branch raises phased Unix ENOSYS with the argument rooted; it never interprets a Windows descriptor as an integer fd. | This is an explicit unavailable observer, not a portable native implementation. Linux/ZFS/ReFS and non-macOS builds are not qualified by the macOS fixture. |

All result allocations occur after native queries finish and no native resource
is owned by the stub. A result-allocation or pending-handler exception therefore
does not leak a newly acquired resource. The caller must still retain its borrowed
FD and any associated credits until the call/worker settles. Runtime release
does not impose a hard syscall deadline or make this a nonblocking Lwt operation.
The several queries are not an atomic file-plus-mount snapshot; the final file
check detects reported changes without proving an unchanging namespace/mount.

[CloneLease](../src/cloneLease.mli) is the ML bridge to `CloneRange`. Abstract
owner/lease records use atomic owner epochs and invalidation flags; enrollment
and refresh check the epoch before and after both observations. It borrows the
exact source and destination descriptors and passes those same descriptors to
the adapter. No lease cleanup/finalizer closes them. Source timestamps and native
constraints are fixed; destination write timestamps are allowed while enrolled
identity, size, links, flags and mount constraints stay fixed. Missing enrolled
identity, owner/lease invalidation and source changes stop the range operation.
The controller supplies a fresh owner identity and must report observed lifecycle
events; these epochs do not infer every remount or reformat from UUID/fsid alone.

The production owner is currently the ordinary APFS receiver in
[Copy](../src/copy.ml). It obtains a random transaction-local owner identity,
pre-establishes stage EOF, adopts the clone channels and registers lease
invalidation with connection cleanup. `copyClonedRange` flushes buffered output,
uses explicit offsets and the enrolled descriptors, and reconciles the channel
position after native copying. It permits at most 10 MiB per operation and sets
`range = None`; all materialized bytes are `Copied`, without a sharing claim.
The inner `CopyRange` preserves exact unsupported-suffix fallback. A native or
buffered error is marked indeterminate and stops rather than triggering another
planner fallback. The final lease check now precedes the held-parent exclusive
clone-to-temp publication described below, while the original channels are still
open. Logical-root/follow-target binding at the later live commit remains open;
trusted staging namespace ownership and normal verification/property/commit
lifecycle remain necessary. Semantic and local-producer paths keep their existing
materializers.

Evidence: the independent [observation suite](../tests/file_observation/README.md)
passes 11 cases and [lease suite](../tests/clone_lease/README.md) 21 cases on stock
5.5.1 and Ox5.2.0+ox. Python stat/utime supplies independent full-width identity,
flags and nanosecond expectations. Private native reply faults, actual held-file
changes/`dup2`, unchanged offsets, repeated leak checks and invalidation during
observation are covered. Lease adapters verify exact borrowed descriptors,
bytes/sentinels, cancellation/errors and ownership survival. These fixtures do
not modify mounts or qualify caller publication. The focused actual
[`Copy.copyClonedRange` harness](../tests/test_clone_bound_range.py) passes
9 groups/27 scenarios on stock/Ox. It hooks only the native copy step in a
private full-source module; native leases, channels and fallback remain actual
code. A stock negative control detects removed channel-position reconciliation. Fresh Make and Dune text
builds/selftests and ordinary clone integration pass both compilers; Ox also
passes local/semantic remote integration. Dune receipts in host-temp
`unison-dune-observer-final-3wkxzfq0` bind all 303 production/package/INSTALL
inputs before/after both builds, excluding generated `.depend`. This follow-on
does not rerun or broaden the earlier Adobe, benchmark or platform evidence.
The [held-FD receipt](../tests/qualification/filesystem-observer-20261013.json)
pins that predecessor independently of the earlier checkpoint. It does not pin
the newer publication source.

## Held-parent intermediate publication

[StagePublication](../src/stagePublication.mli) has an abstract custom owner with
native working-directory/stage-parent/temporary-parent identities, an owned actual
creation-parent FD, and a retained stage-witness duplicate. It authorizes only the
ordinary receiver's private-stage to normal-temporary-name transition. The final
live-file commit and original logical replica root/follow-target mapping remain
separate.

| Boundary | Roots, runtime and memory | Ownership and error behavior |
| --- | --- | --- |
| `prepare` | All three strings and the custom handle are rooted. The finalizable custom block is allocated and initialized before native allocation/opens; its memory accounting includes the context and path copies. Released-runtime work uses malloc-owned strings, native context and stack query buffers only. | Pins the effective working directory and both parents. Identity-only directory rechecks ignore size/link/timestamp changes from sibling operations. Ordinary followed ancestry, distinct parents and O_SEARCH permissions are supported. Failure closes descriptors before raising; finalization frees remaining native allocations. No name is owned yet. |
| `adopt` | The custom handle and descriptor arguments are rooted. Blocking entry uses the no-pending form; the context mutex is locked only with runtime released and unlocked before reacquisition. No ML heap is accessed while released. | Consumes actual creation parent on success and failure; borrows the original stage during the call. Checks bindings and a singly linked regular no-follow name, then retains a CLOEXEC duplicate witness. Error cleanup uses the still-borrowed original if duplication failed. The caller still owns basis/output. |
| `publish` | Rooted custom owner survives released-runtime native queries/rename. Native errno and phase are retained before reacquisition. | Fresh effective-directory/parent checks and singly linked stage identity precede exclusive `renameatx_np`. Native rename failure preserves stage ownership. Success sets TEMP_OWNED immediately, before a pending exception may be delivered. A controlled post-rename Sys.Break fixture confirms subsequent temporary cleanup at this boundary. |
| `disarm`, `abort_and_close`, finalizer | Rooted calls use the same mutex/release ordering. FD slots clear before close, so repeated cleanup cannot close recycled integers. Finalization cannot race a rooted call and closes without name mutation. | Disarm relinquishes temporary-name ownership and closes proof FDs. Abort identity-checks the owned stage/temp via the captured parent, attempts every close despite cleanup failure, then raises the first native error. Added foreign hardlinks block admission/publication, but identity-bound owned-leaf cleanup preserves those foreign links. Finalizers close/free only. |
| `preparation_unavailable` | Exact ML phase matching delegates errno classification to the native runtime conversion, without assuming Darwin ENODATA numbers. It owns no descriptors. | Only ENODATA/ENOTSUP/EOPNOTSUPP/ENOSYS at the three exact preparation identity phases permits auto decline before stage creation. Path/open, malformed, operational, stale and later-phase errors do not qualify. Require mode fails. |

After successful adoption the context retains four extra steady descriptors:
working directory, actual creation parent, temporary parent and witness. The
expected stage-parent descriptor is closed at adoption; transient preparation
and cloning descriptors are additional. It is not a global FD admission limit.

Copy registers the publication owner before native cloning; guarded option and
registry handoffs close it on synchronous setup failures. Parent adoption precedes
channel conversion, so failure or reuse of the original output integer cannot
invalidate the internal witness. Connection cleanup invalidates the range lease,
cleans publication, then closes channels. EOF publication occurs after flush,
exact-length, lease and cancellation checks; disarm transfers the normal temp to
the existing property/verification/commit lifecycle. Ordinary reference fallback
now opens data nonblocking with CLOEXEC, rejects nonregular files before channel
adoption, and guards registration/option storage. Resource-fork handling retains
its existing path.

Source review identified and fixed auto-mode failure on unavailable preparation
identity and the missing single-link admission guard. The independent
[publication suite](../tests/stage_publication/README.md) passes all 58 cases on
stock OCaml 5.5.1 and OxCaml 5.2.0+ox, including the exact fallback classifier,
replacement sentinels, search-only/followed/distinct parents, mutable directory
entries, native identity/error faults, finalizers/recycled descriptors and one
post-rename signal. The [actual Copy publication harness](../tests/test_clone_publication.py)
passes 86 cases per compiler through real rsync/EOF and native publication,
including post-adoption allocation/registration failure, post-rename/pre-disarm
exceptions, collisions, rebound-parent sentinels and reference FIFO/FD reuse. A
stock private negative control detects removed caller cleanup. Current ordinary
clone, bound-range and adoption reruns pass both; Ox local/semantic/remote suites
also pass.

Fresh Make snapshots `unison-build-eiyawftj` and `unison-build-e0r79j3i` pass stock/
Ox builds and selftests. Fresh Dune 3.22.2 builds/selftests in host-temp
`unison-dune-publication-final-evu31q2x` pass both compilers and bind all 306
production/package/INSTALL inputs before/after, excluding generated `.depend`.
The [publication receipt](../tests/qualification/filesystem-publication-20261013.json)
pins current source/test inputs and retained production-caller logs; the held-FD
checkpoint above retains its predecessor hashes.
No SDK, Photo, performance or other-platform evidence was added.

This primitive retains cooperative namespace assumptions: lookup followed by
rename/unlink is not an atomic identity compare-and-swap. Initial old-temp path
cleanup, mount-incarnation discovery, capability caching and crash durability
remain open. Later retained-producer qualification closes regular-file final
`Files.renameLocal` binding, and the scratch slice closes pathname reservation;
neither changes these cooperative namespace or lifecycle limits.
The controlled signal test does not qualify arbitrary asynchronous delivery
between successful clone return and ML ownership capture, actual OOM or every
concurrent caller schedule.

## Adjacent ML opening boundary

`SemanticFile.with_fd` accepts an already-open descriptor. It checks cancellation
and regular-file kind using `fstat` before duplicating into a private channel;
it owns only that duplicate and closes it on completion/error. Its initial
guard cannot prevent an earlier pathname open from blocking.

The audit identified O_RDONLY opens in `SemanticSync.with_file`,
`SemanticSync.try_local_async`, `SemanticRemote.make_plan` and
`CandidateValidation.snapshot` without O_NONBLOCK. Each occurs on the owner
before worker submission. The validator uses the same snapshot path for candidate
hashing and executable pin checks; its child execution timeout has not begun
at that point. SIR/0 `inspect_file` already opened nonblocking. All four audited
ML sites now open nonblocking (the synchronous reference also sets CLOEXEC),
while preserving existing regular-fd checks, descriptor cleanup, errors and
cancellation ownership. [Disposable FIFO fixtures](../tests/test_nonblocking_open.py)
pass stock/Ox for the synchronous reference, async local source, source planner,
validator candidate and executable pin. Each checks rejection, descriptor/CPU/
admission cleanup and usable exact follow-up work. Private copies with the old
blocking opens reproduce timeouts for all five paths on both compilers. These
direct FIFO inputs qualify prompt kind rejection, rather than a deterministic
live pathname-replacement race.

The broader foreign-call inventory, supported sanitizer/platform runs,
representative corpus, filesystem fault matrix and enforced parent/child memory
limits remain open M6 acceptance work. This audit narrows the reviewed surface;
it does not close those gates.

## Worker-reachable primitive inventory (2026-10-14)

This source inventory follows `SemanticWorkers.execute` and its worker loop,
`SemanticFile`, `SemanticHash`, and `SemanticDelta.apply_report_with_extension`.
It narrows the inherited-FFI review work; it is not a review of the compiler's
Unix/runtime C sources, every installed extension, or all inherited Unison FFI.
The five private local primitives below are the only `external` declarations
in the current SemanticFile/SemanticHash modules. Registration does not make
arbitrary future extension native code safe.

| Boundary | Worker use and ownership | Remaining obligation |
| --- | --- | --- |
| `unison_semantic_sha256_init/feed/finish` | Job-local hash context and bounded input, through SemanticHash. No shared context or callback. Existing native rooting/runtime review above applies. | Context/input exclusivity is a caller contract; compiler modes do not verify C. Other-platform native hashing is not qualified by macOS tests. |
| `unison_semantic_prepare_writer/pwrite` | Apply only. Worker holds its output duplicate through completion; admission checks precede writes. Bounded native stack copy, no heap pointer retained across runtime release. | Output/status-flag exclusivity, one-attempt short-write/EINTR handling and caller publication fence remain necessary. No in-call I/O deadline. |
| `Unix.LargeFile.fstat`, `Unix.dup`, channel conversion/descriptor lookup, `LargeFile.seek_in`, `really_input[_string]`, channel/Unix close | Each reader owns its duplicate/channel, checks regular kind and initial/final stamp, and closes on callback failure. Primary input and nested output verification use separate reader lifetimes. | `dup` shares an open-file-description position. Neither Safe.spawn nor immutable job records permit concurrent seek/read through the original or another duplicate. Borrowers must hold that position exclusively until settlement; separate opens are needed for independent concurrent readers. Successful reads remain observations, not a hostile mutation lock. |
| Windows fallback `Unix.LargeFile.lseek` / `Unix.write_substring` | Apply's non-positional writer uses the worker-held private output. | It changes the shared position; do not infer POSIX positional-write guarantees or Windows runtime qualification. |
| `Mutex`, `Condition`, `Atomic`, domain entry/join and Unix pipe write | Queue transitions use the pool mutex; mailbox payloads are immutable, cancellation is atomic. Worker closes job duplicates before publishing completion and notifying the owner. Owner retains pipe ends until shutdown/joins settle. The notification uses an immutable one-byte string (qualified change ad7a385). | Runtime primitives still require their supplied domain-safe implementation. Removal of an explicit scratch allocation does not establish allocation-free notification or recovery from arbitrary worker termination. Pipe errors other than EINTR/EAGAIN/EWOULDBLOCK propagate; complete unexpected-domain-exit recovery is not proved by ordinary shutdown tests. |
| Extension/recognizer callbacks and portable ML parser/hash operations | Owner selects trusted immutable handles. Jobs call identification/inspection/observation/reconciliation/application without invoking the registry. Each callback receives the worker-local bounded reader. | Checked portable signatures constrain ML values, not foreign libraries, hidden mutable globals, arbitrary callbacks, parser heap use or native thread creation. Each new backend needs its own resource and foreign-boundary review. |

Descriptor duplication at submission, CPU/filesystem admission, reply callbacks,
read-observer logging, helper spawn/reap, clone/range creation and final rename
belong to the owner/control path. They are not run by `execute` merely because
an Apply job uses a previously cloned output. The trusted SDK validator is a
supervised child, not an in-domain Adobe call. Therefore its allocator/task-host
qualification remains separate from both this inventory and Safe.spawn.

The current worker contract expressly forbids caller seek/read/write/close on
borrowed descriptors until promise settlement. The 48-job diagnostic control
uses independently opened inputs; it does not qualify simultaneous jobs sharing
one open-file-description position. Deterministic reader cleanup and normal
pool shutdown have current stock/Ox evidence in
[the wake-up qualification](../tests/read_stats/wakeup-qualification.json).
No new compiler/native test or sanitizer run was performed for this inventory.

## Spawn-bound helper group observation (unintegrated primitive)

[Current stock/Ox native/bytecode and kernel evidence](../tests/helper_group_observation/qualification.json)
covers the new functions in helperSupervisor_stubs.c; production calls do not
activate them yet. The old native spawn body is source-identical behind its
unchanged entry point and passes the ordinary helper suite and full builds.

Creation roots its unit argument and custom result before allocating a fixed
metadata-only context. Default finalization owns no FD, process, signal or reap;
serialization is rejected. The six-argument bound-spawn entry roots five values
plus the owner, checks custom operations/owner process/unused state, and calls
the existing native spawn implementation. No ML allocation/callback occurs
between successful native spawn, context assignment and immediate PID return.
Native and explicit six-argument bytecode entry points are exercised separately.
C strings/file actions/temporary FD cleanup remain the existing implementation.

The observer roots and authenticates the local custom owner, checks terminal
unreaped direct-child status, queries at most64kinfo_proc records on its C stack,
validates returned sizes/identities and rechecks the direct-child relationship.
The runtime remains held; it borrows no ML heap pointer across runtime release,
opens no descriptor, and neither signals nor reaps. A separately rooted retire
operation invalidates observation before the caller releases the PID. These
are owner-loop contracts, not compiler-enforced C/domain or hostile-OS proofs.
Query/syscall duration is not a hard deadline and unsupported platforms cannot
infer zero. See [scope/source reference](../tests/helper_group_observation/README.md).
