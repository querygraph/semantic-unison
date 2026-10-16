# Strict whole-file clone results

Add strict whole-file clone results and migrate the remaining ordinary Copy
branches that consume booleans. Keep the existing `clone_file`, `clone_path`,
native symbols and their source implementation unchanged. A failed acceleration
may select ordinary copying only when an explicit decline establishes an
untouched usable destination. An operational error is terminal even when its
measured effects are empty.

This is a source-only proposal at
`aa53e3a499ce8fc1da70360edad894bcbf165112`, following the qualified strict range
and returned-work checkpoints. It introduces no implementation or runtime
qualification. No build, native clone experiment, Adobe/Photo/cache/UI operation,
mounted-volume change or benchmark was performed for this review. OS behavior
below is attributed to inspected repository code or primary documentation;
the proposed checks and acceptance controls are design requirements.

## Observed callers and gaps

| Current code evidence | Consequence |
| --- | --- |
| [System interface](../src/system/system_intf.ml:47) promises non-raising booleans; [generic bindings](../src/system/system_generic.ml:71) expose the two old C symbols; [Fs](../src/fs.ml:71) forwards them. | There is no typed distinction between unsupported acceleration and an operational failure. |
| [Linux `unison_clone_file`](../src/copy_stubs.c:138) calls `ioctl(out_fd,FICLONE,in_fd)` and returns only `status == 0`. It saves no errno or byte/EOF/cursor facts. Other platforms return false for this existing-destination operation. | Permission, bad-FD, I/O, space and uncertain-effect failures are indistinguishable from absent support. |
| [macOS `unison_clone_path`](../src/copy_stubs.c:73) calls `clonefile` with `CLONE_NOFOLLOW | CLONE_NOOWNERCOPY`, using unchecked `strdup` results and the ordinary runtime-release boundary. Other platforms return false. | Allocation failures and all native errors are hidden; no created-object/parent witness reaches the caller. Pending-handler/native-resource boundaries also need explicit review in an additive implementation. |
| [Copy.copyFile](../src/copy.ml:690) flushes output, attempts the boolean FD clone for `DATA`, then notifies the captured `len` without supplying it to the native operation. | An entire-source clone is accepted for an independently captured length. Neither exact source/destination EOF nor output channel/FD position is established by this branch. A following output literal can start at offset zero. |
| [Copy.copyByPath](../src/copy.ml:762) calls the boolean path operation for absent/legacy producers; [copyContents](../src/copy.ml:772) skips descriptor copying and reports `fileLength` on success. | Path success bypasses expected-size validation. False permits copying regardless of the original error or uncertain namespace effect. |
| The bound source-clone branch calls [copyBoundClone](../src/copy.ml:722) with an empty write callback. It uses strict `clone_stage_handles` and owned intermediate publication, but does not receive `fileLength`. | This avoids the boolean error gap but still permits publication of a source clone whose EOF differs from the captured requested length. `StagePublication.publish` establishes intermediate namespace ownership, not content length or a live final commit. |
| `copyLocalClonedLegacy` and `localFileContents` reconstruct a new target from an older receiver basis. | Their basis EOF may legitimately differ from target EOF. Do not impose source-whole equality on receiver-basis reconstruction. Keep its bounded reconstruction and final target truncation checks. |

The old Linux primitive operates on the whole source independently of its
current read cursor. The inspected Linux v6.12 dispatcher invokes cloning with
zero offsets and length; its ioctl wrapper discards the returned byte count
when the requested length is zero. This supports the need for explicit EOF
qualification; it is not a Linux runtime observation. [Kernel dispatcher](https://raw.githubusercontent.com/torvalds/linux/v6.12/fs/ioctl.c).

Linux documents regular descriptor access, same-filesystem requirements and
ambiguous EBADF/EINVAL cases. Neither error can be promoted to an unsupported
result merely because its numeric value is familiar. [FICLONE manual](https://man7.org/linux/man-pages/man2/ioctl_ficlonerange.2.html).

Apple documents exclusive destination creation, copy-on-write data sharing,
attribute copying, held-source `fclonefileat`, and that `CLONE_NOFOLLOW` clones
the symbolic link itself. A regular source FD therefore requires its own
admission check. [Apple clonefile manual](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/man/man2/clonefile.2).

## FD operation: minimal additive interface

Add a small pure `WholeFileClone` module for the result decoder and policy.
Expose `Fs.clone_file_status ~expected_length source destination`; the native
entry point borrows both existing descriptors. It never closes, duplicates,
truncates, seeks or owns them. Initially the native FD cloning backend is Linux
`FICLONE`. APFS still uses named creation, not this existing-output-FD form.

Use a separate eight-field protocol, sharing conventions with strict range
results but not reusing their backend/phase ID meanings:

```ocaml
type raw =
  int * int64 * int * int * Unix.error option * int * int * int64
(* status, completed, backend, phase, mapped_error, mutation, decline, raw_code *)

type mutation = No_effect | Known_prefix | Indeterminate
type backend = Platform | Linux_ficlone | Macos_fclonefileat
type decline = Platform_unavailable | Kernel_unavailable
  | Filesystem_unsupported | Cross_device | Source_constraints | Empty_source
type receipt = {
  requested : int64;
  completed : int64;
  backend : backend;
  phase : phase;
  errno : Unix.error option;
  native_code : int64;
  mutation : mutation;
}
type result = Native_shared of receipt | No_work of receipt
  | Declined of decline * receipt | Failed of receipt
```

Recommended status IDs are 0 native whole success, 1 decline, 2 failure and
3 empty no-work. Completed lengths use boxed Int64, not an OCaml int; whole
files are not bounded to the range primitive's 10 MiB chunk size. Keep native
error bits separately from mapped `Unix.error`. POSIX errno is saved immediately
after the authoritative call; future Win32 DWORD/NTSTATUS values remain opaque,
not inferred from numeric ranges.

Use backend IDs 0 Platform, 1 Linux FICLONE and 2 macOS fclonefileat;
mutation IDs 0 No_effect, 1 Known_prefix and 2 Indeterminate; decline ID 0
means none, followed by 1 Platform, 2 Kernel, 3 Filesystem, 4 Cross_device,
5 Source_constraints and 6 Empty_source. These are distinct from range IDs.

Use explicit phases for arguments, source descriptor, destination descriptor,
source EOF, destination EOF, source position, destination position, destination
parent, native clone, source verification, destination verification, cursor
verification, property profile and cleanup. A backend/phase/error/decline table
must reject contradictory or unknown tags; an invalid result stops the caller.
Assign those listed phases IDs 1 through 14 in that order, with 0 Unavailable.
Success carries no error/decline/code and completed equals the request; No_work
has requested/completed zero, No_effect and no native sharing assertion. Decline
has completed zero, No_effect and one consistent scope. Failure carries a
mapped error and no decline; a raw code can be zero for an internal consistency
failure that has no saved native errno.

The FD preflight must establish all of these facts before mutation, including
on a platform that will subsequently decline:

- The requested signed length is nonnegative and representable as native file
  size/offset. Descriptor integers/HANDLE kinds are valid; fstat/query failures
  preserve their original error.
- Source and destination are distinct regular objects, including separately
  opened or duplicated handles to the same inode. Source is readable;
  destination is writable, nonappend, initially empty and at native offset zero.
  The output has one link and no disallowed native constraints.
- The caller already owns a private exclusive output/adopted producer and
  retains both handles throughout the operation. Distinct/single-link/empty
  observations alone do not establish that ownership.
- Source EOF equals `expected_length`. Record source identity, size, relevant
  timestamps/flags and both native positions. A held FD pins an object but does
  not freeze source bytes or prove a mount incarnation.

Reject invalid descriptors, access modes, nonregular objects, aliasing, nonempty
or shifted destinations and stale expected EOF as terminal preflight failures.
Do not reset/truncate the caller's output to make it eligible. Source position
may be nonzero: a native whole-source clone starts from byte zero and must leave
the source cursor untouched.

`Copy.copyFile` has a narrower optimization gate than the native FD API. Select
whole-source cloning only when the input channel's logical position is zero;
buffered read-ahead may already have advanced its native FD, which must remain
unchanged. Once the channel has consumed source bytes, use the existing bounded
copy path. Pending output, a nonempty output or a nonzero logical/native output
position also skips the whole-file optimization and preserves ordinary DATA
copying behavior. Establish private output ownership through the existing
exclusive/adopted producer; an output opened through a compatibility truncation
fallback is not eligible merely because it is now empty. These caller
eligibility decisions make no native sharing assertion. An explicit strict
API request still treats an invalid destination preflight as a terminal error.

After native success, recheck both identities, source stability, exact source
and destination EOF and preserved native positions. `Native_shared` is valid
only after all checks pass. It attests the explicit native operation's sharing
contract under the borrowed/private-object assumptions, not measured physical
allocation or the continued sharing of blocks after subsequent writes. Normal
strong/fingerprint/property/publication verification remains necessary.
Its byte completion names the source bytes observed by the native operation,
not a digest of the previously archived source version. Identity/EOF/stamps do not replace
that final expected-byte verification or manufacture an immutable-source proof.

A valid empty FD request performs no clone call and returns `No_work` only
after source EOF zero, destination EOF/offset zero and all descriptor/ownership
checks. It makes no sharing claim. Native whole operations have no usable short
prefix result: complete success is the full request; a native error with no
authoritative count reports completed zero and indeterminate effects. Once full
completion was qualified, a later cursor/cleanup failure can retain completed
`expected_length` for accounting, but remains terminal. EOF alone cannot prove
that a failed operation materialized the correct bytes.

## Decline and failure policy

`Declined` requires completed zero and `No_effect`: the admitted private output
remains usable with its original logical data/EOF/cursor and constraints, and
no existing destination name was replaced. This is a scoped operation result,
not a cacheable filesystem capability. Output change timestamps are not a
physical-write measurement or a persistent-data prefix.

For Linux, consider ENOSYS/ENOTTY for unavailable ioctl/kernel support,
EOPNOTSUPP for unsupported reflinking and EXDEV for a different clone domain
only in the specific native-clone phase with the backend's qualified no-effect
contract and destination/source checks. ENOTTY is a new FICLONE-specific case,
not permission to copy the strict range API's historical errno set. A failed
postcheck, surviving output bytes, changed constraints/cursors or unknown
backend error effects defeats the decline. Source-reviewed error classification
is not runtime qualification of every Linux filesystem/version.

For named APFS creation, use its documented atomic native failure contract and
the held parent's absent destination entry. ENOTSUP, EXDEV and genuine API
absence may decline before admitting any created output. An existing entry,
permission/space/I/O failure or failed observation is terminal. Unsupported
source flags can be a pre-call `Source_constraints` decline when explicitly
declared by the implementation; invalid/nonregular sources remain failures.

EINVAL, EBADF, EACCES, EPERM, EIO, ENOSPC, EBUSY, EROFS, EEXIST, EINTR and
unclassified errors never become fallback solely from their errno. Even a
`Failed/No_effect` result remains failure. Do not retry EINTR or a failed clone
as ordinary copying: a whole-file ioctl exposes no partial byte count. Any
indeterminate result requires discard/reporting through the existing owner;
never seek/truncate and continue into another backend on that stage.

## Named creation: separate ownership result

Add `Fs.clone_path_status ~expected_length source destination` as a regular-file
creation API. Its Fs/owner facade opens a held source and actual destination
parent; the native core validates those borrowed handles, the private leaf and absence, and calls
`fclonefileat` into that parent on macOS. The Linux FD API remains available after
a no-effect platform decline here; implementing a Linux named wrapper is not
required for the first slice. A pathname receipt alone is insufficient.

Source resolution belongs to the caller's ordinary DATA-copy policy. Open the
held regular source using that same approved follow/resolution behavior; do not
silently impose a new no-follow rule on every legacy source path. The new native
creation primitive borrows that held FD without closing or duplicating it. An intentionally followed
source symlink must retain resolved-file copying, while a changed/invalid
declared regular object remains terminal. The old boolean CLONE_NOFOLLOW symbol
continues its existing behavior. This compatibility case needs its own tests;
the separately constrained no-follow clone-stage API is not its substitute.

```ocaml
type path_handles = {
  output_witness : Unix.file_descr;
  creation_parent : Unix.file_descr;
}
type residual = Absent | Removed_owned_entry | Unqualified_entry_may_remain
type path_failure = {
  primary : receipt;
  cleanup_error : receipt option;
  residual : residual;
}
type path_result = Created_path of receipt * path_handles
  | Declined_path of decline * receipt | Failed_path of path_failure
```

The path result needs its own native ownership carrier in addition to the raw
scalar context. Preallocate success carriers before acquiring native resources;
check every native string allocation, process pending actions before ownership,
copy immutable argument scalars/bytes before no-pending runtime release, save
primary errors before cleanup and settle every transient resource before error
delivery. Validate the actual installed stock/Ox runtime boundaries rather than
inventing a `leave_blocking_section_no_pending` API: the inspected headers expose
no such function. Native resource transfer and ML adoption must receive their
own allocation/interruption/close-reuse qualification.
After native creation, an interruption during reacquisition, source close or
adoption must leave the output witness discoverable by that facade owner until
settlement; preallocating a tuple alone does not establish this ownership.

The native core borrows both the source and destination-parent handles from the
preallocated Fs/owner facade. It closes neither; that facade remains their owner
until an explicit handoff. The core owns only newly opened internal/output
descriptors, transferring an admitted output witness on success and settling
its own descriptors on failure. The facade closes its transient source before
delivering success and transfers its actual parent together with that output to
the caller. Failed/no-effect paths close the facade's source/parent exactly once
after native settlement. Borrowing a caller/channel FD never transfers its
ownership to the facade or core. The witness/parent remain live through identity checks and
intermediate publication or relative cleanup. `StagePublication.adopt` is a
candidate integration point. Native creation plus a later opened witness has
the existing cooperative first-admission assumption; it cannot prove the absence
of an identical foreign replacement before that first witness. Do not claim
an atomic created-inode receipt, mount lifetime or hostile-namespace guarantee.

On failure, remove only an admitted identity-bound entry relative to its actual
parent; never unlink an EEXIST entry or a foreign/rebound name. Close each newly
owned FD once, preserving the primary failure and any cleanup failure. If the
clone created a leaf but opening/admitting its witness failed, report possible
unqualified residue and stop. Do not blind-delete the pathname or fall back.
Failed close semantics are platform-specific and do not authorize retrying a
possibly reused FD number. No crash-recovery guarantee follows from cleanup.

Keep the first strict named API's property profile explicit and compatible with
the legacy clone operation: source attributes/xattrs/resource-fork and inherited
directory ACL behavior remain native clone behavior, with ownership controlled
by CLONE_NOOWNERCOPY. It is not a drop-in alias of data-only `clone_stage_handles`,
which clears inherited ACL/xattrs and makes writable private output. Any switch
to data-only behavior is a separately reviewed transfer-property change.

For zero-length named sources, the smallest safe rule is an untouched
`Empty_source` decline after regular-source/expected-EOF and destination-absence
checks. Ordinary exclusive creation then creates the empty destination.
Returning `No_work` while its name is absent would falsely complete copying.
An eventual explicit empty-created result could preserve the native metadata
profile, but must transfer a real owned output and cannot claim shared bytes.

## Exact production edits

| File/function | Proposed change |
| --- | --- |
| NEW `src/wholeFileClone.{ml,mli}` | Typed int64 receipts, consistent raw decoder, scoped decline policy and pure caller decision. No Fs dependency or capability cache. |
| NEW `src/wholeFileClone_stubs.c` | Add `unison_clone_file_status` and separate owned named-creation primitive. Keep the old functions in `copy_stubs.c` byte-identical. Linux FICLONE FD path, macOS held-parent named path and explicit other-platform absence; qualify descriptor preflight rather than asserting unimplemented HANDLE checks. |
| `src/system/system_intf.ml`, `src/system/system_generic.ml`, `src/fs.{ml,mli}` | Add raw FD binding/strict wrapper and ownership-aware named wrapper. Existing Core/boolean interfaces remain available with their old types and behavior. |
| `src/Makefile.OCaml`, `src/dune`, affected isolated runners | Add pure module before Fs/Copy and native stub to both build/link paths; account for the added dependencies in private snapshots. System's raw tuple avoids a type-module dependency cycle. |
| `Copy.copyFile` | Gate whole-source optimization on logical input start zero and an owned empty output with no pending bytes and zero logical/native position; otherwise retain ordinary bounded copying. Native input read-ahead does not disqualify logical start zero and must remain untouched. Pass captured int64 `len`; consume only checked full success/no-work or explicit no-effect decline. After success seek/reconcile output channel and FD to `expected_length` before notifying once. Preserve source channel logical/native positions and unread buffered bytes. Seek/notify/cancellation errors propagate without fallback; hold/discard the private output through the existing owner. |
| `Copy.copyByPath` / `copyContents` | Pass `fileLength` into the strict named operation; adopt output/actual-parent ownership before allocating another wrapper; check exact EOF and source/name/property fences; publish via an owned intermediate rather than naked pathname cleanup. Only a scoped decline enters descriptor copying. Return success/progress after verified ownership/length; retain final Files fingerprint/publication enforcement. |
| `Copy.copyBoundClone` source-clone call | Thread expected length into the source-clone use and check immutable basis/output EOF before empty callback/intermediate publication and after it. This may need an additive sized stage primitive to perform expected-size admission before native creation; preserve the unsized legacy/stage APIs. |
| Receiver-basis uses of `copyBoundClone` / local reconstruction | Keep basis and target EOF distinct; check final target length after reconstruction. Do not require old basis EOF to equal new target length. |

The `clone` preference currently describes receiver-basis staging. Keep its
existing off/auto/require meaning; do not silently turn optional source-file
acceleration declines into a new global require policy. No wire/archive format
or peer feature changes are needed for these endpoint-local receipts.

## APFS, ZFS, ReFS and workers

APFS native whole creation, Linux FICLONE, composed whole materialization and
arbitrary range sharing stay distinct capabilities. Generic `copy_file_range`
success leaves sharing unreported, even on a filesystem that opportunistically
shares storage. OpenZFS documents `block_cloning` for operations such as
`copy_file_range`, with OS/dataset constraints; this does not qualify FICLONE or
another file pair. [OpenZFS feature documentation](https://openzfs.github.io/openzfs-docs/man/master/7/zpool-features.7.html#block_cloning).

A future ReFS whole operation is a composition of aligned bounded extent
duplications plus exact copied edges and EOF setup, with an aggregate receipt.
It must retain partial-error information; it cannot be mislabeled one atomic
native whole clone. Volume, integrity/sparse and cluster constraints require
their own backend qualification. [Microsoft block-cloning contract](https://learn.microsoft.com/en-us/windows-server/storage/refs/block-cloning).

The new native operations can run in audited OxCaml workers using immutable
job descriptions and independently retained descriptors, with the existing
shared CPU/I/O/workspace budgets. Their callers must preserve returned-work
settlement and resources until native completion; cancellation of an active
native call does not permit early stage/FD retirement. Do not add an independent
18-worker pool or claim all-core speed from runtime release alone. Scheduling,
physical-sharing measurement and 1/6/18-worker performance are later evidence.

## Required qualification before acceptance

Use the [source-only test plan](whole-file-clone-status-test-plan.md) for the
complete controls. The minimum acceptance includes strict decoder contradictions;
exact-length mismatch before/during/after cloning; closed/read-only/append,
aliased, nonregular, nonempty or shifted FDs; preserved source positions and
output channel reconciliation followed by a literal; zero FD/no-work and real
empty path creation; unsupported-before-mutation fallback; operational and
indeterminate failures with no fallback/retry; cleanup, interruption, adoption
and close-number reuse; candidate/parent replacement; unchanged source/live
destination/archive state after rejection; and exact subsequent reuse/retry.

Platform availability is not native clone success. Actual macOS controls can
qualify named APFS creation and no-effect FD absence; a typed FICLONE fake can
qualify caller decisions but cannot qualify Linux sharing. Linux filesystems,
future ZFS/ReFS operations, cross-volume performance, physical allocation,
mount-lifetime changes, hostile first-admission races and crash recovery remain
separate gates. Existing source-range/final-publication/returned-work suites must
pass on stock and Ox after each meaningful implementation change.

Include ordinary approved source-symlink/follow cases, resolved-target changes,
nonregular sources and data-only versus legacy native-clone property profiles.
Do not mistake cloning a symlink entry for copying its selected DATA bytes.

Source pins at this audit: `copy_stubs.c`
`8478e89400128ba53500e3d78e4e8eab854ad744ffc3a886a6d5b037c9d8760b`;
`copy.ml` `b1586879651ca20538e4eb1cf00394021e9db089a980abae0987757142f2e42f`;
`fs.ml` `e8e4d320ae22dbd3c0a97a2f6a531a3d1b8f1e3ee2fd4ef0fb218db02eaf2551`.
