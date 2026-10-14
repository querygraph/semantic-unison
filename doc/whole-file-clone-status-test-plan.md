# Whole-file clone status: independent caller audit and test plan

Source checkpoint: `aa53e3a499ce8fc1da70360edad894bcbf165112`.
Coordinated native proposal SHA256:
`511dff57f586b0d69f708b05ac3d0b3303a5517ca0ad648d23d27650657410a4`.
This is a source-only design/test plan. No production or test implementation,
build, syscall experiment, benchmark, Photo access or Adobe invocation was
performed for this audit.

## Concrete gaps in the current callers

`Copy.copyFile` (`src/copy.ml:690`) flushes output, then calls
`Fs.clone_file src dst` for `DATA`. The call has no expected length. A true
result only invokes `notify len` (`:696–697`): it does not verify source/output
EOF or reconcile either output cursor. The strict range branch below it already
flushes and reconciles the output channel (`:716–718`). The distinction matters
even if the common whole-file caller subsequently closes its channels.

The Linux legacy stub (`src/copy_stubs.c:138`) invokes whole-file `FICLONE` and
returns `status == 0` (`:146–150`), with no explicit cursor adjustment. A
preserving-cursor native adapter that copies the entire source and returns true
is sufficient to expose the caller's unchecked assumptions independently of
Linux runtime availability on this machine.

`Copy.copyByPath` (`src/copy.ml:762`) likewise receives no expected length. Its
legacy branch returns `Fs.clone_path` directly. The bound producer branch calls
`copyBoundClone` with an empty write callback (`:768–769`). That helper adopts
owned handles and renames its clone stage into the ordinary temporary candidate
(`:739–755`) without a size check in the empty callback. `StagePublication`
explicitly qualifies namespace ownership, not content. This is temporary
candidate publication, **not** proof that an incorrect file reaches the live
replica: later producer/fingerprint checks remain relevant.

`copyContents` (`src/copy.ml:777`) reports its expected `fileLength` and skips
opening the ordinary output when path cloning returns true. Therefore a wrong
source length, a misleading success receipt, or an empty-file outcome that
creates no destination can escape this immediate caller boundary. All three
source-copy call sites have an expected size available: `copyContents`, the
source-first branch of `localFileContents` (`:919`), and `localFileAsync` (`:964`)
use `fileLength` or `Props.length desc`; `copyByPath` needs to accept that value.

Both legacy stubs deliberately collapse operational errors and unsupported
operations into false (`src/copy_stubs.c:73–88`, `:138–150`). False enables
ordinary/range fallback. A comment requiring full success/full failure does not
provide an effect receipt or show that a failed backend left the destination
unchanged. Later fingerprint rejection cannot authorize an unsafe earlier
retry. Additive status entry points should preserve these legacy symbols and
contracts while routing the migrated ordinary callers through strict results.

## Contract to qualify, coordinated with the native adapter owner

The proposed FD entry point is
`Fs.clone_file_status ~expected_length:int64 source destination`. Its raw result
has eight fields: status, completed `int64`, backend, phase, optional mapped Unix
error, effect, decline scope and native error code `int64`. These are a
whole-file protocol with their own tags; a range progress tuple must not decode
as authority for this operation.

The portable layer must validate the request and raw result. Success means a
positive, complete whole-file clone of exactly the expected EOF, on regular,
distinct objects, into an empty writable non-append output at native offset
zero. The native FD adapter preserves source and destination cursors; the
`Copy` caller explicitly advances/reconciles its output channel to expected EOF
before declaring completion. An empty valid FD request can be `No_work`, which
attests neither sharing nor a native clone syscall.

The ordinary `Copy` optimization has a narrower caller gate: logical input must
still be at zero. Buffered native read-ahead may put the source FD elsewhere;
preserve that native position and the unread channel buffer. Actually consumed
logical input, pending output, nonempty output, or nonzero logical/native output
position skips the whole-file optimization and retains ordinary DATA copying.
This eligibility decision is separate from the strict primitive: an explicit
invalid native request remains a terminal preflight failure.

The output must have actual exclusive/private creation or an adopted producer
ownership witness. An empty regular singly linked output is insufficient.
In particular, the legacy `O_EXCL`-unsupported compatibility opening with
`O_TRUNC` (`src/copy.ml:382–388`) does not establish exclusive ownership and is
ineligible for whole-file optimization by empty stat alone.

Only an explicit supported-platform/kernel/filesystem/cross-device decline
with zero completion and verified no effect permits fallback. Each permitted
native errno must be tied to its actual backend and phase. EINVAL, EBADF, EIO,
ENOSPC, permission errors and unknown native errors must not become declines
because they appear in an old compatibility list. Any failed verification,
indeterminate effect, malformed receipt or unexpected exception is terminal.
Whole-file cloning has no qualified partial-prefix fallback contract.

The path entry point needs a different ownership shape. A successful exclusive
creation must return an owned output and its **actual creation parent**, plus a
held source witness or equivalent source binding sufficient for postchecks.
Its completed byte count alone cannot qualify the destination name, cleanup,
producer adoption or publication. The exact path result representation is
still the native owner's design decision; tests should enforce the ownership
contract rather than depend on an unfinished tuple layout.

The coordinated path proposal resolves zero length with an explicit untouched
`Empty_source` eligibility decline, so the ordinary copier performs exclusive
empty-file creation. This is separate from platform/filesystem support evidence.
Returning completed zero while the destination remains absent is invalid.
Any alternative future empty-created outcome would need namespace effect and
ownership witnesses, without claiming shared data blocks.

The coordinated positive path result transfers the output witness and actual
creation parent. If it does not transfer a source descriptor, its native source
binding/postcheck contract and caller's subsequent source validation must be
explicit. Every failure closes newly owned descriptors and reports primary
and cleanup codes plus any residual namespace effect; a residual pathname
alone must not authorize a new cleanup or copy attempt.

Following the source-symlink counterexample, the named-creation core will receive
a held regular source resolved by the caller's approved ordinary DATA policy.
It must not silently impose a different final-source no-follow policy. The
coordinated native core borrows both source and actual-parent FDs from a
preallocated facade, and closes neither. It owns newly opened internal/output
descriptors and transfers its admitted output witness on success. The facade
closes its transient source only after native settlement, transfers its actual
parent with output on success, and closes transient source/parent once on
failure or decline. Caller/channel FDs are borrowed, never ownership-transferred;
cleanup must not later close their reused integers. The legacy boolean symbol
keeps its original `CLONE_NOFOLLOW` behavior, and the separate data-only stage
API retains its existing constraints.

`copyBoundClone` is also used to clone an older basis before reconstruction.
That workflow may intentionally start with an EOF different from the new target
length. Do not apply the source-copy expected EOF rule blindly to every basis
clone, and do not replace the legacy path metadata profile with the data-only
`clone_stage_handles` profile. Existing `clone_path` keeps the clonefile metadata
behavior; strict source-copy tests must preserve that distinction.

## Independent fixtures and decisive oracles

Use an isolated, compiler-matched full `Copy` source fixture similar to
`tests/test_clone_bound_range.py`, with the new status primitives as the only
private replacement seams. Poison **both** old boolean primitives and count
calls, so tests cannot accidentally exercise the legacy route. Keep the actual
channels, bounded fallback, producer checks and publication owners in use.

The synthetic whole-clone adapter should copy source bytes through independent
exact-offset fixture I/O, preserve both native cursors, and record each call's
FD identities, EOFs, positions and expected length. A separate byte oracle
checks complete source/destination files and a subsequent literal append; it
must not infer correctness from returned status, progress callbacks or hashes
computed by the adapter itself. Synthetic success is not physical-sharing proof.

For path ownership, capture original source, output and parent identities before
injecting mutations. Observe actual opened descriptors, parent-relative names,
old live-file bytes, adversary-created collision/replacement bytes, and kernel
FD counts. Cleanup must remove only the file created by this operation, never
an entry merely having its old pathname. Directory descriptors and adopted
channel descriptors must each close once, including failed result handoff.

The first native ABI qualification on this macOS host should use small own
temporary files only. The FD primitive's platform-unavailable path can still
qualify arguments, descriptor preflight, effect/cursor preservation and the raw
ABI. Linux syscall behavior requires separately labeled injected simulation or
a later real Linux run; neither demonstrates native Linux/ZFS/ReFS support here.
The existing user goal authorizes own disposable private APFS temporary-file
controls. Later real macOS path qualification still waits for a source freeze
and resource coordination; it requires no new permission by implication and
does not authorize touching Photo/cache/production data.

## Cases that can falsify the design

| Case | Independent observation and required result |
| --- | --- |
| Source 4,097 bytes, declared EOF 4,096; converse short source | No clone/fallback completion, no `notify 4096`, and no temporary-candidate rename. Preserve exact mismatch/error context. |
| Nonempty source, declared zero | Reject before native cloning; never label a nonempty whole source `No_work`. |
| Both regular files empty and distinct | FD `No_work` leaves bytes/cursors unchanged; path `Empty_source` declines without creation, then ordinary exclusive creation produces the empty owned destination. No sharing claim. |
| Exact positive success with preserved native cursors | Output bytes/EOF equal source exactly; `pos_out` and native output cursor equal expected EOF after the caller returns. Immediate `output_string "!"` appends at EOF instead of overwriting byte zero. Source logical/native cursors and unread buffered bytes remain unchanged. |
| Buffered source prefetch with logical input zero | Establish and independently assert logical zero with a different native read-ahead position; eligible cloning preserves both observations and the exact next unread input byte. Do not seek the source to expected EOF merely for symmetry. |
| Actually consumed logical input | Whole-source optimization makes no native clone call; compare resulting ordinary DATA bytes/positions/progress with the unchanged ordinary copying path. Raw strict FD cloning retains its separate arbitrary native-source-position contract. |
| Pending buffered output literal or nonempty/nonzero logical/native output | Skip whole-file optimization, preserving the normal flush and ordinary copy behavior. The whole clone must not replace the flushed literal or existing bytes. A direct strict API request with invalid destination remains terminal, never an implicit decline/fallback grant. |
| Empty output created through compatibility `O_TRUNC` rather than exclusive/adopted ownership | Structural EOF/regularity/link checks cannot grant ownership. No whole clone call; ordinary copying remains available. Contrast an actual `O_EXCL` creation/adopted producer witness to prove eligibility requires the owner, not matching stat fields. |
| Unreadable source; dest preexisting content, positive offset, O_APPEND, read-only, nonregular, or aliased source inode | No whole-file syscall or sharing success. Same inode through two descriptors/hardlinks is still an alias; empty EOF and link count alone do not prove private ownership. |
| Valid known no-effect scoped decline | Exactly one attempted clone, no changed bytes/EOF/cursors/properties, then exactly one authorized bounded ordinary/range fallback. `off` invokes no clone seam; retain the documented eligibility semantics of `require`. |
| EINVAL/ESPIPE/ENOTSOCK/EIO/ENOSPC/EACCES/EBADF/unknown native code returned as failure | No fallback, retry, success notification or rename, even when EOF remains zero. Preserve backend, phase, mapped error and full native code. |
| Backend writes bytes or extends EOF, then returns an operational error or an indeterminate decline | Candidate remains failed. Independent unknown-extra-byte/EOF oracle proves that the caller did not reset, truncate, overwrite or retry it as ordinary fallback. Preserve the original failure and cleanup diagnostics. |
| Clone syscall succeeds, then source size/stamp/identity or destination EOF/identity/link/flags changes before verification | Terminal failure after mutation; no fallback. A claimed full count is not a valid success receipt when its required postconditions fail. |
| Bad tags/count/effect/scope/context | Unknown tag, negative/oversized count, short “whole success,” success with errno, decline with progress, operational errno disguised as unsupported, or contradiction between native code/backend/phase/effect all reject without fallback. Include full Int64 edge values. |
| Progress callback/position reconciliation throws after native completion | No native retry and no fallback; original exception survives. The owned candidate stays unpublished and all handles settle. Notify completion only after fresh postconditions and required channel reconciliation. |
| Source pathname replaced while original FD remains open | Do not relabel the held old source as the fresh pathname. Recheck the qualified path/binding contract; preserve source witness and fail if the captured source identity changed. Stable stat stamps are change detectors, not immutable-content proof. |
| Legitimate source symlink selected by the ordinary traversal policy | The old path clone uses `CLONE_NOFOLLOW`, while its false branch can reach ordinary `Fs.open_in_bin`. The strict named core uses the caller-resolved regular source FD; verify ordinary resolved-source bytes/properties and once-only descriptor cleanup. Separately reject a source-kind/identity race. |
| Destination collision, symlink, hardlink or parent/path replacement | Exclusive creation never overwrites an entry. Parent-relative postchecks/cleanup use captured witnesses. Missing/rebound names or missing identity remain terminal after creation, not permission for absolute-path fallback. |
| Failure allocating/opening/adopting/returning ownership after creation | No hidden creation or FD leak. A created-but-not-returned candidate must be identity-cleaned or explicitly reported as unresolved creation residue, without granting renewed pathname cleanup authority. Cleanup failure does not replace the primary error or permit copying over it. |
| Legacy metadata profile | Synthetic user xattr/resource-fork/metadata sentinels survive the strict ordinary path clone as required by the legacy profile; planned property/fork finishing still runs. Data-only staging behavior is tested separately. |

Native failure classification must be qualified with syscall-call counts as
well as statuses. A before-syscall preflight failure has no data mutation; an
error after entering a mutating clone syscall is conservatively indeterminate
unless that backend/phase has a separately justified no-effect guarantee.
Preserving EOF or a cursor alone does not establish no effect on bytes,
allocation, metadata or namespace.

## Strong negative controls and evidence

1. Restore only success handling to `notify len`, removing explicit output
   reconciliation. The independent following-literal and cached/native cursor
   oracle must fail despite correct cloned bytes before that literal.
2. Restore only unchecked expected EOF. A preserving-cursor adapter clones an
   extra source byte and reports true/full success; the independent destination
   EOF/no-publication oracle must fail despite a matching progress counter.
3. Change only a returned operational EINVAL/indeterminate failure into a
   no-effect decline. An adapter first writes an unreported extra byte; the
   independent fallback-call/write oracle must fail even if the eventual
   ordinary byte copy appears correct.
4. Restore only pathname-based cleanup after a creation-parent or final-name
   replacement. The captured replacement-file identity/bytes must survive;
   removal of that entry is the designated negative failure.

Keep successful controls and mutations separate. Retain exact frozen source,
generated snapshot inputs, privately transformed source, compiler version/hash,
commands, object/native-source/binary/log hashes, exits, fixture failures and
per-case byte/FD/position observations. Run sequential stock/OxCaml qualification
after an explicit production freeze. Existing range/status/adoption/publication
controls are adjacent regressions; they do not establish this whole-file
contract or native sharing. Final content/property/source/publication validation
remains required after a successful clone receipt.
