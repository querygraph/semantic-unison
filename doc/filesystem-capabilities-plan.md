# Filesystem capabilities: implementation and qualification plan

Status: **ordinary APFS receiver range copying, intermediate publication,
regular-file final publication and native scratch reservation/cleanup use held
descriptors; native range sharing and lifecycle discovery remain open**,
2026-10-13.
This maps [SOL.md's M2-G contract](../SOL.md) onto the current code. It preserves
the working APFS path and ordinary upstream acceleration while preparing a
constrained range adapter for future ZFS/ReFS qualification. Review was limited
to source/document reads during the Adobe benchmark. After that benchmark,
`CopyRange` and its `Copy.copyFileRange` integration were implemented and the
11 isolated injected-step tests passed on stock OCaml and OxCaml. They cover
exact prefixes, unsupported suffix fallback, operational errors, invalid/zero
progress, overflow and callback/cancellation boundaries. Combined integration
qualification is owned by the coordinating build run.

The integrated `CopyRange` slice retains legacy unsupported
EINVAL/ESPIPE/ENOTSOCK conventions; EBADF escaping the native adapter now fails.
The separate `CloneRange` slice implements bounded alignment planning and
fresh binding checks. `FileObservation` now supplies actual macOS held-FD facts,
`CloneLease` fences borrowed descriptors with owner epochs, and
`Copy.copyClonedRange` uses them for ordinary APFS receiver rsync shifted matches.
This caller advertises no range-sharing capability and copies at most 10 MiB
per planner operation. No capability cache or new ZFS/ReFS adapter exists.
Strict APFS stage status and production caller
migration pass direct native and combined transfer tests on this host; the
legacy optional/boolean interfaces remain available. Resource-exception
hardening passes separate controlled fault tests and final Make/Dune
qualification; actual exhaustion, arbitrary async delivery and crash recovery
remain separate gates. [Checkpoint receipts](../tests/qualification/filesystem-20261013.json)
retain the prior filesystem source hashes and scope.

The held-FD follow-on passes 11 observation and 21 lease cases on both compilers.
Fresh Make snapshots `unison-build-v2izyqvq` (stock) and
`unison-build-tpvddl2b` (Ox) pass builds/selftests; fresh Dune 3.22.2 text
builds/selftests pass in host-temp `unison-dune-observer-final-3wkxzfq0`.
Its manifests bind 303 production/package/INSTALL inputs before and after both
builds, excluding generated `.depend`. Ordinary clone-transfer integration and
40 current/36 old-handoff adoption controls pass both compilers; Ox also passes
local producer/semantic and remote/bidirectional/old-peer suites. The focused
[production adapter harness](../tests/test_clone_bound_range.py) passes 9 groups
and 27 scenarios on both compilers; a stock negative control detects missing
channel-position reconciliation. The [held-FD checkpoint](../tests/qualification/filesystem-observer-20261013.json)
binds that predecessor's source and test hashes. These checks add no sharing,
storage performance or other-platform qualification.

The new publication slice retains the actual native creation parent through
`Fs.clone_stage_handles` and uses `StagePublication` for the ordinary receiver's
exclusive stage-to-normal-temp rename. The three-FD native suite passes 20 cases
and the publication suite passes 58 cases on both compilers, including scoped
preparation fallback and a controlled post-rename `Sys.Break`. Fresh Make
snapshots `unison-build-eiyawftj` (stock) and `unison-build-e0r79j3i` (Ox) pass
builds/selftests. Fresh Dune 3.22.2 builds/selftests pass in host-temp
`unison-dune-publication-final-evu31q2x`: all 306 production/package/INSTALL
inputs match frozen/workspace/both-snapshot after manifests, excluding generated
`.depend`. The [publication receipt](../tests/qualification/filesystem-publication-20261013.json)
pins this source independently of the held-FD predecessor. Actual Copy
publication/reference tests pass 86 cases per compiler, with a stock private
cleanup-removal negative control. Ordinary clone, bound-range and adoption
reruns pass both; Ox local/semantic/remote/bidirectional/old-peer suites pass. No SDK, Photo or performance qualification was added.

The later [retained-producer checkpoint](../tests/qualification/retained-producer-publication-20261013.json)
qualifies regular-file final live publication and logical-root/follow-target
binding, retaining actual output descriptors through finalization, validation
and commit. The [native scratch implementation](native-scratch-next.md) replaces
absolute reservation/removal with bounded exclusive `openat` and held-witness
`unlinkat` through the retained parent. It passes 182 direct APFS cases /
1,984 assertions per compiler, plus current Make/Dune builds and synthetic
ordinary/semantic/remote/old-peer integration. The full final `Files` caller
passes 79 cases per compiler against this source. Initial old-temp pathname
cleanup, additional-name families, first-admission intervals, cooperative
comparison/namespace assumptions and crash recovery remain explicit limits.
Current receipts are [direct](../tests/clone_scratch/qualification-20261013.json),
[integration](../tests/qualification/native-scratch-integration-20261013.json) and
[final caller](../tests/qualification/native-scratch-final-files-20261013.json).

## First implementation slice

The first slice adds explicit **range-copy outcomes and fallback reasons**
around the existing `Fs.copy_file` operation. `Copy.copyFileRange` no longer
treats every Unix error as permission to retry by copying. The existing private
APFS basis/stage construction is preserved. After this injected-step error
qualification, strict native clone status and a pure alignment planner were
added, followed by held-FD observations, owner-scoped leases and the ordinary
receiver integration described below. No new wire format, archive invariant or
semantic equality rule is needed for these receiver-local changes.

Do not begin by adding a second clone engine, guessing capabilities from a
filesystem name, or promising new native ZFS/ReFS support. The concrete first
acceptance target is: unsupported acceleration still falls back exactly, while
ENOSPC/EIO/access errors fail the item without overwriting the live target or
trying an expensive alternate copy that conceals the original failure.

## Current implementation and gaps

| Location | Present behavior | Required change |
| --- | --- | --- |
| [Fs](../src/fs.ml), [interface](../src/fs.mli) | Reexports upstream boolean `clone_path`/`clone_file` and byte-count `copy_file`; retains optional descriptor-pair `clone_stage` and strict `clone_stage_status`, plus additive strict `clone_stage_handles` returning basis/output/actual-creation-parent FDs. | Strict native/caller tests pass here; cross-volume, unavailable-platform and fault qualification remain. Keep compatibility wrappers. |
| [System interface](../src/system/system_intf.ml) | Whole-file clone calls explicitly promise not to raise; range copy advances destination position on success. | Add strict entry points rather than silently changing the old interface's exception contract. Migrate production callers deliberately. |
| [APFS stage stub](../src/copy_stubs.c) | Opens a regular, unflagged source without following its final symlink; pins destination parent; clones an unlinked immutable basis, then a writable stage; checks source identity/stability; clears inherited stage ACL/xattrs/resource fork. Strict status work preserves this transaction and the old ABI. | The new three-FD ABI retains the actual creation parent on success; both older two-FD ABIs are unchanged. Twenty handle cases and 182 scratch cases / 1,984 assertions pass stock/Ox. Scratch reservation/removal is descriptor-relative; initial old-temp cleanup remains pathname-based. Regular-file final live commit is separately qualified. |
| [Copy range loop](../src/copy.ml), [CopyRange](../src/copyRange.mli) | Typed exact-prefix outcomes now restrict fallback to the legacy unsupported set; zero/invalid progress and operational errors fail. Native-step errors are separate from notification/cancellation exceptions. | Full transfer suites pass. Narrow ambiguous compatibility errnos through strict backend status and qualify native partial failures. |
| [Upstream C adapters](../src/copy_stubs.c) | macOS path cloning and Linux `FICLONE` return booleans; Linux/FreeBSD/Solaris range APIs may copy; Windows invokes extent duplication. | Retain supported mechanisms; add precise native status/errno capture and per-backend effect reporting. A successful generic copy is not evidence of sharing. |
| Receiver/local/SDE consumers | Strict stage results remain shared. Ordinary receiver rsync shifted matches now use `copyClonedRange` on the immutable basis through `CloneLease`/`CloneRange`; same-offset inherited skips remain separate. Exact output length, fingerprints/SDE hashes and ordinary finalization remain in place. | Focused actual-adapter fault qualification passes 9 groups/27 scenarios on stock/Ox. Local producer and SDE paths retain their existing materializers; no claim that every sink uses the planner. |
| [CloneRange](../src/cloneRange.mli), [implementation](../src/cloneRange.ml) | Pure range executor separates native-whole/composed-whole/range support, checks fresh bindings, plans aligned bounded operations, and accounts authoritative adapter prefixes. It now has an ordinary receiver caller. | Constrained fake adapters pass stock/Ox. Actual native sharing adapters and their effect/error results remain unqualified. |
| [FileObservation](../src/fileObservation.mli), [CloneLease](../src/cloneLease.mli) | Fresh macOS held-FD facts and borrowed-descriptor leases connect native identities to owner generations. Production leases invalidate on connection cleanup/release. No cache is used. | No true mount-incarnation detector, lifecycle event discovery or immutable-content proof. The separate publication owners guard intermediate rename and regular-file logical-root/final-live-commit binding; broader additional-name transactions remain open. Non-macOS observation raises ENOSYS. |
| [StagePublication](../src/stagePublication.mli) | Finalizable native owner pins the effective working directory, distinct name parents and retained stage witness; checks fresh bindings; exclusively renames to an absent normal temp; performs identity-bound cleanup. | Fifty-eight native cases pass stock/Ox. Actual Copy publication/reference qualification passes 86 cases per compiler with a stock cleanup-removal negative control. This is cooperative intermediate publication, with four extra steady owned FDs, not the final `Files.renameLocal` or original logical-root/follow-target guard. |

Existing [APFS fixtures](../tests/CLONE.md) verify exclusive staging, live-source
isolation, immutable unlinked basis, properties, hardlinks, shifted references,
growth/shrink and retry. Direct strict-stage fixtures also verify scoped source
declines, phase-specific errors and compatibility ABI. The portable constrained
range suite below tests injected generation changes and exact partial progress;
it does not qualify remount/reformat detection, cross-volume attempts or other platforms.

## Portable capability executor

`CloneRange.execute` is a standalone, synchronous contract below the transfer
layer. It allocates one bounded operation at a time; it never constructs an
operation list proportional to file size. Native-whole and composed-whole
support are independent flags and never imply range support. The caller must
establish source and destination EOF before execution; this module neither
grows a candidate nor publishes it.

Each expected binding contains a local owner-instance identity, backend revision,
separate source/destination volume and file identities, nonnegative generations
and sizes. The owner-instance identity must not be reused on controller restart.
The injected `observe` callback must return fresh endpoint observations before
every operation and before completion, including zero-length requests. Exact
comparison rejects stale owner/backend/volume/file/generation/size observations
before any new mutation. This implements the comparison boundary; it does not
detect an actual remount or reformat until an endpoint adapter supplies a real
observation. Peer-supplied records and cached copies of the expected record do
not qualify as that observer.

The executor rejects negative/overflowing/out-of-EOF requests and every
same-file overlapping interval, including ordinary copying. Disjoint same-file
sharing is independently configurable. Equal offset/length alignment defines
copied head, aligned interior and copied tail; unequal residues, incompatible
pairs and a positive maximum below one alignment unit select bounded copying.
Whole-file support alone never authorizes a sharing operation.

Adapters return `Shared`, `Copied`, `Unsupported` or `Error`, with a contiguous
known-prefix receipt and an explicit uncertain-effect flag on unsuccessful
calls. Shared bytes are accepted only from a sharing operation and only in
alignment multiples; ordinary copied progress may be short and unaligned.
Both counts must fit the current operation using checked arithmetic. Counts
describe the aggregate prefix, not the order of extents within it; the adapter
remains responsible for native restrictions on each extent. Invalid counts
terminate with `Invalid_result` and `Indeterminate`, retaining only previous
validated progress and never notifying the invalid claim.

A known-prefix unsupported sharing call disables sharing for the remainder and
copies exactly its suffix. Unsupported copying, typed operational errors,
indeterminate effects and changed bindings all stop without fallback. A valid
positive prefix reported with an error is retained/notified once; it does not
make the candidate publishable. `Copied` deliberately makes no physical-sharing
claim. Callback, cancellation and unexpectedly raised adapter/observer exceptions
propagate unchanged, so they cannot be reclassified as unsupported acceleration.

The endpoint owner still retains the immutable basis, descriptors and admission
credits through worker settlement. This pure module does not close descriptors,
discard private stages, establish source stability, enforce placement policy,
or implement a commit guard. A completed receipt must still pass ordinary exact
byte/property verification and fresh root binding checks at publication. Durable
recovery must reopen/reobserve objects with new tokens; persisted receipts do not
make an old process-local owner/generation current. These are explicit native
publication/lifecycle gates, not behavior demonstrated by synthetic adapters.

The independently authored [constrained adapter suite](../tests/clone_range/README.md)
passes all **48 named tests**, including **960 alignment/maximum/length
combinations**, on stock OCaml 5.5.1 and OxCaml 5.2.0+ox. It checks immutable
source/evolving-stage bytes, authorized-write sentinels and per-byte write
counts independently of the planner. Coverage includes short/copied/aligned
progress, suffix-only unsupported fallback, operational and indeterminate
failures, invalid claims, every binding field before/mid/after transfer,
zero-length final checks, exception propagation and cancellation of a huge
streamed request without eager allocation. These are portable synthetic tests;
they do not qualify any native ZFS/ReFS operation or mounted-volume observer.

## Proposed contract below the semantic layer

Keep filesystem mechanics in `Fs` and a small copy-planning module next to
`Copy`; use a shared internal type module if dependency order requires one.
The interface should separate these operations:

1. **Native whole-file clone:** source handle into an exclusive destination
   name, or a qualified existing-destination form when that backend supports it.
2. **Composed whole-file materialization:** explicit range operations plus
   copied edges, with an aggregate receipt. This is not implicitly a native
   whole-file clone or a stable snapshot of a changing source.
3. **Range sharing:** exact source/destination offsets and bounded length,
   with independently declared constraints.
4. **Accelerated/ordinary copying:** exact bytes, with sharing unreported
   unless the invoked operation explicitly guarantees it.

Each request records `basis_role = Source | Receiver_previous_version`, source
and destination identity, stability evidence, current logical cursor, valid
inherited length and the destination's private ownership. Only the candidate is
mutable. A held source descriptor pins an inode; it does not freeze its bytes.
Do not use a composed clone as an immutable receiver basis unless its stability
proof covers the whole operation and subsequent reads.

Use explicit `Shared`, `Copied`, `Unsupported` and `Error` outcomes. A suitable
internal shape is a result plus a progress receipt; exact OCaml naming can
follow the existing modules. The receipt must include:

- Requested range and **contiguous completed prefix**, using checked 64-bit
  arithmetic. A completed prefix is not an arbitrary set of written extents.
- Bytes explicitly shared and bytes otherwise materialized, which sum to the
  completed prefix. `Copied` means no sharing guarantee was reported; a kernel
  may still optimize it. Neither field is physical disk-write telemetry.
- Whether the unsuccessful call leaves a known prefix/position or an
  indeterminate candidate. Indeterminate mutation requires discard and failure;
  it cannot authorize blind suffix fallback.
- Native error/code, operation, backend and phase, without arbitrary peer paths
  or unbounded diagnostics. Unsupported results also state their scope.
- Descriptor-position and property side effects. New range operations should
  use explicit offsets; the legacy implicit-output-position adapter must flush
  buffered output first and reconcile positions before returning to channels.

One backend step may report a short successful prefix. The loop must continue
from that prefix or apply its documented fallback; it must never silently
report the whole request. For nonzero requests, zero completion is an explicit
source-EOF/no-progress failure unless the adapter returns a specific unsupported
result with no mutation. All counts must fit the request, source bounds and
destination target length. Keep cancellation checks between bounded chunks.

## Held-FD observations, leases and the receiver caller

[FileObservation.observe](../src/fileObservation_stubs.c) is implemented on
macOS. It reads full-width `fstat` file identity, kind, size, flags, links and
nanosecond timestamps, plus `fstatfs` filesystem ID and mount flags. Volume UUID
uses a separate `fgetattrlist` request and a fixed-size stack buffer. Exact
returned-length/mask checks reject malformed, truncated or unexpected fields;
missing/all-zero UUID is explicitly `None`. Syscall errors retain their phase
and never become missing identity. A final `fstat` rejects detected changes to
the exposed file facts with EBUSY. Current
[XNU volume-attribute handling](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/vfs/vfs_attrlist.c)
may substitute the mounted root vnode; combining file and volume attributes
can therefore misidentify the file. The observer opens/closes no descriptors,
allocates no native buffer, preserves offsets and does not access the ML heap
while the runtime is released. Other platforms raise ENOSYS.

[CloneLease](../src/cloneLease.ml) borrows the exact source/destination descriptors;
the owning caller retains and closes them. Abstract owners carry a fresh trusted
controller identity and an atomic epoch. Enrollment and refresh check the epoch
before and after native observation, require distinct regular objects and
available volume identities, and retain full-width length-framed volume IDs.
Explicit owner closure/invalidation and per-lease invalidation stop future work.
Source timestamps and native constraints must stay enrolled; destination write
timestamps may change while identity, size, links, flags and mount constraints
remain fixed. A disappearing enrolled UUID is an error. Source stamps detect
change but do not freeze bytes or replace the caller's immutable basis proof.

The [observation suite](../tests/file_observation/README.md) passes 11 cases and
the [lease suite](../tests/clone_lease/README.md) 21 cases under stock OCaml 5.5.1
and OxCaml 5.2.0+ox. Independent Python stat/utime values and synthetic native
attribute replies cover IDs, flags, nanoseconds, missing/zero/malformed UUIDs,
errors, unchanged offsets, writes/truncation/unlink/rename/`dup2`, bounded calls
and descriptor retention. Lease tests cover changed identities/constraints,
owner invalidation during observations, fresh checks after a completed receipt,
borrowed-FD survival, exceptions, exact copied bytes and sentinels. These are
disposable local files and controlled observations, not mount mutation tests.

The production caller is deliberately narrow. `Copy.transferFileContents`
pre-establishes the private stage's target EOF, enrolls its immutable unlinked
basis and writable output, and registers lease invalidation on connection
cleanup. Missing identity at enrollment discards the clone and permits ordinary
fallback in auto mode; require mode fails. Malformed observations, operational
errors and later identity loss fail the transfer. The receiver observes the
lease at each instruction and again after final flush/EOF checks. Shifted
matches use `Copy.copyClonedRange`: `range = None`, bounded 10 MiB copying,
explicit source/destination offsets, exact descriptor/channel identity checks,
flushed buffered output and repaired channel position after native copying.
`CopyRange` retains its exact unsupported-suffix fallback. Native or buffered
failure becomes an indeterminate adapter error; no planner retry is allowed.
Successful bytes are `Copied`, with no sharing guarantee. Same-offset inherited
skips, literal writes and the local/SDE materializers remain their distinct paths.
The focused production-adapter harness passes 9 groups/27 scenarios on both
compilers: bounded shifted offsets, short native progress, exact unsupported
suffix fallback, quiet fallback EOF, EIO/ENOSPC, invalid/zero progress, changed
source/destination bindings or owner epochs, and channel-FD mismatch. A private
stock negative control removes channel-position reconciliation and triggers the
expected failure. Ordinary receiver integration passes the exact shift/duplicate/
grow/shrink/off/require/interruption suites.

## Intermediate stage-to-normal-temp publication

The ordinary receiver now prepares [StagePublication](../src/stagePublication.ml)
before cloning. Preparation pins the effective working directory and both name
parents, allowing distinct parents, followed directory ancestry and search-only
directory access. Directory observations compare native identity, flags and
volume facts, ignoring mutable directory size, link count and timestamps so
parallel sibling updates do not spuriously invalidate a transfer.

[Fs.clone_stage_handles](../src/fs.mli) uses the existing native clone engine and
returns caller-owned immutable-basis, writable-output and actual-creation-parent
descriptors. The older two-FD ABIs are unchanged. Publication adoption consumes
the actual parent on success and failure, borrows the original output only until
settlement, and retains its own CLOEXEC duplicate as the stage witness. It checks
a singly linked regular stage with a no-follow final-component lookup. Channel
adoption can subsequently fail or close/recycle the original output FD without
losing that witness. After adoption the context owns four additional steady FDs:
effective root, actual stage parent, temporary parent and witness. Preparation
and native cloning have separate transient descriptors; four is not a peak count.

After exact EOF, flush, lease and cancellation checks, `publish` freshly checks
the effective root/parent bindings and stage witness, then calls descriptor-relative
`renameatx_np(..., RENAME_EXCL)`. A collision is preserved. Native ownership moves
from stage to temporary immediately upon rename success, before runtime
reacquisition can deliver a pending exception. `disarm` relinquishes cleanup
ownership to the ordinary temporary-file lifecycle and closes proof handles.
Abort removes only the matching owned leaf through its captured parent, including
a renamed/rebound parent; identity-only cleanup can remove its own leaf after
an added hardlink without removing that foreign link. Explicit cleanup closes
every owned descriptor even on failure; finalizers close descriptors without
unlinking names. Connection cleanup invalidates range leases before publication
cleanup and channel closure.

The review found two issues that were fixed in source: default `clone=auto`
must still work when preparation cannot obtain volume identity, and stage
admission must reject added hardlinks. `preparation_unavailable` recognizes only
native ENODATA/ENOTSUP/EOPNOTSUPP/ENOSYS at the exact working/stage/temporary
identity-observation preparation phases. Auto then uses ordinary rsync; require
fails. Path/open errors, malformed replies, operational failures, stale bindings
and every later adoption/publication error stay terminal. The ordinary data
reference opens nonblocking, checks for a regular file and guards channel,
registration and `Some` handoffs, including after a preparation decline.

The [three-FD native suite](../tests/clone_handles/README.md) passes 20 cases and
[publication suite](../tests/stage_publication/README.md) passes 58 cases on both
compilers. Tests cover real held-parent replacement, distinct/followed/search-only
parents, sentinels, descriptor reuse, finalization, malformed/changed native
identities, scoped fallback and one post-rename pending-signal boundary. The
[actual Copy publication harness](../tests/test_clone_publication.py) passes
86 cases per compiler through real receiver rsync/EOF, including ownership
failure, native rename-before-disarm exceptions, sentinels and reference FIFO/FD
reuse. A stock negative control detects removed caller cleanup. Ordinary clone,
bound-range and adoption reruns pass both; Ox local/semantic/remote suites pass.

This closes the intermediate stage-to-normal-temp binding implementation gap.
Later retained-producer qualification guards original logical replica root /
follow-target resolution and regular-file final `Files.renameLocal` publication
after source-selected properties and candidate verification. Native scratch
reservation/removal is now descriptor-relative. Initial old-temp path cleanup
and additional-name transactions remain separate work. Fresh lookup followed
by rename/unlink is cooperative, not an atomic inode compare-and-swap against
hostile namespace mutation. No mount-incarnation, crash-durability or universal
asynchronous-handoff guarantee follows from this change.

## Capabilities and generation lifetime

The next final-live slice has a source-only integration review. It is not
implemented by `StagePublication`. Enroll the logical root, translated path,
current follow policy, effective working directory, intended normalized target
and temp name after `setupTargetPaths*Local` creates the required parents. Fresh
`findWorkingDir` resolution must bind the same physical parents and selected
name, preserving configured followed links outside the replica. Mutable
directory timestamps, size and links remain irrelevant to identity.

Keep an opaque endpoint-owned token with connection/session lifetime and bounded
registry ownership. A negotiated additive setup/rename command may echo a bounded
nonce; native descriptors and identities stay local. A deterministic temp-path
map alone does not bind a session or replay. Old peers retain their existing
behavior without acquiring a stronger publication claim.

Attach the finalized candidate witness after resource-fork transfer,
source-selected property application and `paranoidCheck`. Validation should
return a retained proof tied to that candidate baseline and policy/verdict,
then recheck identity around asynchronous helpers. Off/warn validation still
needs namespace identity fences. Rejected-candidate quarantine/removal must use
captured owned parents/names. Bracket `Update.checkNoUpdates` with target
observations and retain the exact accepted target through backup work and final
rename. Ordinary replacement needs `Absent` or `Replace_expected`; the current
intermediate `Expected_absent` policy cannot be applied to every live target.
Conflict-copy retargeting is an explicit endpoint-authorized selection.

A first qualified regular-file commit could exclude move-first directory
transactions and require a separately qualified auxiliary-file policy.
`Os.rename` also manages AppleDouble names, so main-file rename alone cannot
claim complete resource-family publication. Preserve backups, conflict choices,
native forks and effective source-selected properties. After native success,
track published/uncertain state: later failure must suppress archive advancement
and reconcile, never delete the live target or blindly roll back. Archive,
transfer-hint and stash changes remain last. Directory commits, source moves,
cross-volume behavior and Windows replacement remain separate qualifications.

The focused future matrix covers root/follow/parent rebinding during transfer,
validation and backups; late candidate/content/resource/property mutation;
accepted-target replacement; equivalent followed aliases and normalized names;
unrelated sibling changes; wrong-session/replayed tokens; helper settlement;
owned quarantine after rebinding; and post-success main/sidecar failures. These
are proposed fixtures, not passing evidence or a new operational oracle gate.

Public volume UUID/fsid, inode generation and write counters do not provide a
reliable mount-incarnation counter. The controller must invalidate leases on
lifecycle/rebind events it observes; the observer does not discover every such
event. A held descriptor may still refer to an old mount or replaced pathname.
The intermediate clone-to-temp rename now uses held-parent publication after
the final lease check and before channel closure. A configured logical root and
follow-target resolution still need fresh binding checks at the later normal
candidate commit. Effective working-directory checks at the intermediate
boundary do not establish that final guarantee. No reusable capability cache or
per-chunk subprocess is present.
ReFS's wider file IDs and ZFS's pool/dataset identities must retain their full
backend-specific representation when their native adapters are later qualified.

Capabilities describe an operation on the actual open objects, not a volume's
marketing name. The record needs native-whole/composed-whole/range support,
exclusive-create requirements, source/destination compatibility scope, offset
and length alignment, maximum request length, pre-established EOF requirements,
overlap rules, and relevant sparse/integrity/encryption/property constraints.
Unknown values mean “attempt under a safe contract” or “decline”; they never
permit an unchecked operation.

Keep the current absence of a process-wide positive/negative capability cache.
Before adding one, capture a
transaction-local token from the held source and destination parent, with
verified volume identity and an owner-managed **binding generation**. Where
available, include mounted-filesystem identity and relevant mount/driver state.
`st_dev`, a mount path or a volume UUID by itself does not prove a particular
mount incarnation. If a platform cannot establish a reliable reusable token,
do not cache across transactions; the operation remains authoritative.

Later caching must be bounded and keyed by backend revision, volume/mount token,
binding generation and the relevant source/destination pair. Invalidate on
root replacement, disconnect/rebind, remount observation, reformat, policy or
capability-relevant state change. Hold/reprobe when freshly opened handles no
longer match; a stale capability does not justify switching to a different
mounted target. Expected placement-root identities from the
[component contract](component-placement-v0.md) remain an independent guard.

Scope declines precisely:

| Decline | Cache scope |
| --- | --- |
| API absent on the running platform | Backend/version, until executable/runtime changes |
| Filesystem reports this operation unsupported | At most a verified mount-generation and operation |
| Source/destination cross-device or incompatible dataset pair | That pair, not all copies on either volume |
| Source flags, sparse/integrity/encryption mismatch, range residue | This file pair/operation state; never a volume-wide negative |
| ENOSPC, EIO, permission failure or changed source | Error, never an unsupported capability cache entry |

The current APFS stub's flagged/nonregular decline is per-file. Its successful
first clone does not guarantee its second clone, ACL change or xattr removal
will succeed. Those later failures must keep their phase and error; do not
disable cloning globally after a metadata operation fails. Reformatting Quasar
invalidates previous tokens even if `/Volumes/Quasar` is reused.

## Unsupported versus operational errors

Classification belongs in each native adapter, after validating its arguments
and known prerequisites. Do not replace the current broad catch with another
global errno allowlist that treats bad descriptors or malformed requests as
ordinary fallback.

| Result | Required action |
| --- | --- |
| ENOSYS / documented ENOTSUP or EOPNOTSUPP for the attempted acceleration | Return scoped `Unsupported`; `auto` may use a legal copy path, `require` fails clearly at its existing optimized-attempt boundary. |
| Documented cross-volume restriction / EXDEV | Pair-scoped unsupported; do not infer either filesystem lacks cloning. |
| Alignment/compatibility precondition absent | Planner declines before syscall. Native EINVAL is unsupported only when that backend can attribute it to a documented unfulfilled capability; otherwise preserve it as an error. |
| ENOSPC / EDQUOT / EIO / EACCES / EPERM / EROFS / invalid handle | Fail the item with original operation context. Keep any partial receipt for cleanup/diagnostics; do not retry as full copying. |
| Source mutation, path/identity mismatch, checksum failure | Fail/rescan under current transfer rules; never label unsupported. |
| Unsupported after a known successful prefix | Copy only the remaining suffix when cursor/property state is proved valid and policy permits; never recopy or recount the prefix. |
| Error after a successful prefix, or unknown mutation within the failing call | Discard owned candidate and fail; retain original error plus cleanup failures. No live/archive change. |

Retry EINTR only where the API defines a safe retry and its partial effect is
accounted for. Capture errno/GetLastError before runtime reacquisition or other
native calls can change it. Preserve existing cancellation and connection-close
ownership: settling an operation never frees descriptors still borrowed by an
active worker. Compatibility wrappers can retain old signatures for remaining
callers, but migrated transfer paths must not lose the richer status through
those wrappers.

## Alignment and exact-range planning

The initial fake constrained adapter uses a single configurable alignment `A`,
representing compatible source-offset, destination-offset and length rules.
Given `(s,d,n)`:

1. Check nonnegative offsets/length, overflow and valid source/target bounds.
2. If `s mod A` differs from `d mod A`, no common advancement makes both aligned;
   copy the entire requested interval through the reference path.
3. Otherwise copy the head `min(n, (A - (s mod A)) mod A)`, share the largest
   remaining whole-alignment interior, and copy the exact tail.
4. Split interiors into strictly positive aligned chunks no larger than the
   backend's actual maximum. Never round a request outward. If separate source,
   destination and length alignments are later supported, solve/check them
   explicitly; do not reuse the equal-alignment formula by assumption.
5. Establish required candidate EOF before sharing, without publishing it.
   Preserve sparse/integrity constraints with reversible candidate-local
   changes; no alteration of the immutable basis or live destination.
6. Advance logical progress once for each completed prefix, then require exact
   target EOF and whole-file verification before normal commit.

Same-offset inherited skips remain distinct: they are legal only inside a
verified whole-file receiver clone's still-inherited region. They do not invoke
a range backend or prove new shared extents. Shifted and duplicate references
always read/share from the immutable basis. Monotonic output prevents earlier
writes from invalidating a later inherited skip; out-of-order construction
would require explicit interval ownership, which this change does not add.

APFS v1 advertises only its qualified whole-file clone operation. It has no
new arbitrary-range sharing implementation; shifted ranges continue exact
copying. The sparse DNG writer's 4 KiB comparison windows are an application
write policy, not APFS allocation alignment or this adapter's range alignment.

For ReFS, Microsoft documents cluster boundaries, a request limit below 4 GiB,
same-volume/integrity compatibility, sparse prerequisites, non-overlap and
destination EOF established in advance. The inherited Windows stub needs a
focused audit: its current `len + cluster - (len % cluster)` expression adds
one cluster even for aligned lengths, while EOF growth uses only `offset+len`.
Replace such outward rounding with exact interiors/copied tails in the planned
adapter, and test boundaries before claiming native support. This is a source
finding, not a reproduced Windows failure.
[Microsoft ReFS restrictions](https://learn.microsoft.com/en-us/windows-server/storage/refs/block-cloning).

For OpenZFS, feature state and compatible records/encryption can affect
cross-dataset cloning. Qualify each OS/version/native operation; neither the
feature name nor a successful generic `copy_file_range` result alone establishes
that this request shared blocks. Never enable a pool feature or change dataset
properties automatically to satisfy an optimization.
[OpenZFS block-cloning feature](https://openzfs.github.io/openzfs-docs/man/master/7/zpool-features.7.html#block_cloning).

## Metadata and exact-byte invariants

Retain the current APFS receiver-stage normalization: a private writable inode,
no inherited receiver ACL/xattrs/Finder info/resource fork, and no permission
change to the live source. Flagged/compressed sources remain conservatively
unsupported until the required metadata semantics are independently qualified.
Do not remove compression metadata from a file whose data representation
depends on it.

Keep source clones and receiver clones explicit. A source clone's copied
attributes are not automatically the final Unison property policy; compare the
final result with the ordinary fresh-copy behavior under the same preferences.
All backends still perform the normal source-selected property/resource-fork
finalization, `paranoidCheck`, source/destination update fences, optional Adobe
validation, rename/stashing and archive lifecycle. Range sharing alone copies
no assumed ACLs, alternate streams or registration records.

Ordinary/old-peer transfers retain their existing fullfingerprint guarantees;
SDE retains complete SHA-256 identities and preservation proofs. Sharing
provenance, block ancestry or a generation token never substitutes for content
equality. No new durability or physical-write claim follows from these APIs.

## Implementation slices and meaningful tests

| Slice | Implementation boundary | Acceptance before the next slice |
| --- | --- | --- |
| 1. Outcomes and error visibility | Range-loop types, receipts and injectable steps are implemented; strict native APFS stage results also exist. Existing wrappers are retained. | Eleven isolated tests pass stock/Ox: unsupported-before-write fallback; EIO/ENOSPC/permissions/EBADF fail; short/zero/invalid progress; exact suffix fallback; callbacks and cancellation. Ordinary/local/remote transfer integration passes. Strict native range classification remains open. |
| 2. APFS reasons and generation | Strict two-clone stage results, native `FileObservation` and abstract borrowed `CloneLease` owner epochs are implemented. No capability cache. | Direct stage fixtures, 11 observation and 21 lease cases pass stock/Ox, including real held-file changes and controlled invalidation. Actual remount/reformat/lifecycle discovery and crash recovery remain open; intermediate and regular-file final publication are separately qualified. |
| 3. Pure planner and fake adapter | `CloneRange` implements streaming bounded `Copy`/`Share` operations and independent fresh binding observations. A separately authored fake adapter keeps immutable source/evolving stage bytes and independently checks operation constraints. | Passed: 48 named tests and 960 geometry combinations on stock/Ox, byte-for-byte sequential parity, exact write envelope/counts, immutable source, typed failure/generation/cancellation boundaries and bounded-space execution. This closes only the portable synthetic gate. |
| 4. Shared sink integration | Ordinary APFS receiver rsync shifted ranges now use the borrowed lease/planner with 10 MiB copying and no range-sharing capability. Same-offset skips and current local/SDE stage consumption are preserved. | Ordinary transfer tests pass both compilers; Ox local/remote/old-peer suites pass. Focused actual-adapter tests pass 9 groups/27 scenarios on stock/Ox, with a stock position-reconciliation negative control. Other sink/composed-materialization integration remains future work; no wire/archive change or native sharing claim. |
| 5. Intermediate publication | Native three-FD creation-parent handles and `StagePublication` are integrated into ordinary receiver EOF publication, with exact auto-decline scope and identity-bound cleanup. | Twenty handle cases and 58 publication cases pass both compilers; fresh Make/Dune builds/selftests pass. Actual Copy publication/reference tests pass 86 cases per compiler; ordinary clone/bound-range/adoption reruns pass both and Ox local/remote suites pass. Later retained-producer/final caller qualification closes regular-file live commit/logical-root binding, and direct native controls close pathname scratch reservation. Initial old-temp pathname cleanup, broader transactions and crash recovery remain open. |
| 6. Platform qualification | Audit/refactor inherited Linux/FreeBSD/Solaris/Windows native paths against the contract, retaining fallback support. Add real platform-specific adapters only with evidence. | Actual filesystem/version tests, ABI/foreign-call audit and physical-sharing evidence where claimed. Fake tests alone never close this gate. |

The fake adapter must test behavior, not simply mirror the planner's formulas:

- Hand-written cases: zero length; below/exactly/above alignment; equal and
  unequal residues; head-only/tail-only; exact maximum and one byte beyond;
  multiple chunks; boundary EOF; overflow near the supported integer limit.
- Assert each shared call independently satisfies the adapter's alignment,
  maximum, EOF, identity, non-overlap and compatibility rules. Place sentinels
  immediately outside the authorized interval and prove they remain unchanged.
- Reconstruct insertion, deletion, duplicate and shifted references against an
  independent sequential byte model. Include deliberately overwritten stage
  prefixes to catch accidental reads from evolving output.
- Inject unsupported at call 1 and after a successful aligned prefix; inject
  EIO/ENOSPC/access failure at those same boundaries. Check fallback count,
  exact prefix receipt, failure visibility, bounded calls and candidate cleanup.
- Inject an indeterminate mutation, source change, stale binding generation,
  property mismatch and cancellation. None may become successful fallback or
  update the live destination/archive.
- Model backend success that performs ordinary copying. It must increment
  copied/unreported bytes, never explicit shared bytes. Separate inherited-skip
  counters from newly shared and application-written bytes.
- After slice 2, inject native stage failures after basis clone, output clone,
  ACL/mode changes and attribute removal in a private harness. Assert owned
  files/descriptors settle and existing destination/source properties survive.

Use small synthetic byte arrays/files and deterministic failures first. After
the benchmark window, run the relevant isolated stock/Ox suites once per
meaningful change. Actual separate-volume APFS/non-APFS tests and platform builds
remain explicit qualification work; a simulated cross-volume producer is not
evidence of their performance or native semantics.
