# Native clone-stage scratch ownership

Implemented and qualified on 2026-10-13. This document retains the filename of
the reviewed implementation plan. The production change is confined to the
common native engine in `src/copy_stubs.c`; the three ABIs and ML interfaces are
unchanged. All native tests used disposable synthetic APFS files. No Adobe,
Lightroom, Photo payload/catalog/cache/volume or preview operation occurred.

## Problem and implementation

The predecessor engine retained the destination parent, then reserved and
removed a blank scratch file using absolute-path `mkstemps/unlink`. Clones and
opens later used the retained directory. Rebinding the parent pathname could
therefore send reservation/removal to a different directory. Closing the blank
reservation before removal also lost its identity witness. Error cleanup could
blindly unlink a replaced output and close witnesses before removing names.

The common `unsn_clone_stage_impl` now covers all three entry points:

| Entry point | Unchanged success contract |
| --- | --- |
| `unison_clone_stage` | Compatibility option, immutable basis and writable output FDs |
| `unison_clone_stage_status` | Strict decline/error result, basis and output FDs |
| `unison_clone_stage_handles` | Strict result, basis/output and actual creation-parent FDs |

Ordinary `Copy`, local receiver-basis copies, `SemanticSync` and `SemanticRemote`
all use this engine. `StagePublication` and `FinalPublication` remain unchanged.

Creation uses sixteen stack bytes from macOS `arc4random_buf`, thirty-two
lowercase hexadecimal characters and at most 128 attempts. The fixed basename
is `.unison.basis-<32hex>.unison.tmp`, requiring 58 bytes including NUL. It follows
`Os.isTempFile`'s `.unison.` prefix / `.unison.tmp` suffix convention and does
not grow with the destination leaf. Randomness reduces collisions; exclusive
creation establishes reservation ownership.

`openat(parent, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC |
O_NONBLOCK, 0600)` creates the blank reservation through the retained parent.
Only `EEXIST` retries. Every other error propagates immediately; exhaustion is
operational `EEXIST` at `clone_stage: basis reservation`. Collision sentinels
are never removed.

The reservation FD stays held through no-follow identity comparison and
`unlinkat`. It closes only after successful removal. A removal or close failure
prevents cloning. Both later `fclonefileat` calls and all scratch opens/removals
use the retained directory, even when its old pathname has been rebound.

## Admission, cleanup and close ordering

Separate state tracks exclusive reservation ownership, admitted basis/output
ownership and the writable-output handoff. Basis/output admission requires a regular,
singly linked object, matching device/inode across witness and current name,
and the existing source/basis/output distinctness checks. A second no-follow
lookup confirms the output after writable reopen. The writable FD becomes its
cleanup witness before the earlier read witness closes.

Identity comparison uses `fstat(witness)`, no-follow `fstatat(parent, name)` and
a second `fstat(witness)`. Cleanup requires regular kind and matching device /
inode; it permits later extra hardlinks and mode/mtime changes, preserving
other aliases. A missing cleanup leaf can be accepted after the first witness
check, but a bad witness cannot be hidden by missing-name tolerance.

Owned names are removed before closing their witnesses. Every descriptor slot
clears before exactly one close attempt; no failed close is retried. This avoids
closing an unrelated descriptor recycled at the same integer. Source close and
ACL cleanup are settled before deciding error-path output removal. The first
operational errno/phase survives later cleanup failures. A pure clone decline
cannot hide a close or cleanup error. The legacy option keeps its generic error
label; strict ABIs retain detailed native phases.

Normal success returns an unlinked read-only basis, separate writable data-only
output and optionally the actual creation parent. Existing source checks,
ACL/mode/xattr normalization, result constructor numbers and layout remain.
Only first-basis-clone `ENOTSUP/EXDEV/ENOSYS` become the existing scoped declines;
reservation, identity, output/property and cleanup failures are operational.

## Runtime and platform boundary

All OCaml results are rooted and preallocated before native resources. Pending
actions run before ownership begins. Native source/destination/scratch buffers
are allocated before the no-pending blocking section. Released-runtime work
uses only copied strings, native descriptors, stack data and native allocations;
no OCaml callback, allocation or borrowed heap string is used. All buffers /
ACL resources and non-transferred FDs settle before runtime reacquisition.

The existing macOS 10.12 availability branch and non-macOS decline remain.
The bounded collision loop is not a native syscall deadline. No new platform,
mount-incarnation, sharing or performance capability is inferred.

## Qualification and evidence

The [direct fixture](../tests/clone_scratch/README.md) compiles actual production
C and Fs wrappers under private C-only syscall fault wrappers. Each compiler
passes **182 APFS cases / 1,984 assertions**: 61 legacy, 61 strict two-FD and
60 three-FD cases. Tests cover parent rebinding with actual reservation-parent
identity and replacement-directory timestamps, file/symlink/directory collisions,
128-attempt exhaustion, replacement/missing names, admitted/unproven artifacts,
source stability, mutable metadata and aliases, injected failures, real recycled-
FD close sentinels, 254/255-byte leaves, Unicode and relative paths.

Two private source regressions each fail the designated assertion through all
three ABIs on both compilers: restoring actual absolute reservation operations,
and removing only reservation identity comparison. Complete retained inventories
record intentional preserved artifacts. Independent read-only review verified
137 file hashes and 1,776 native artifact entries, reconstructing both mutations
from the frozen source. [The direct receipt](../tests/clone_scratch/qualification-20261013.json)
pins exact sources, compiler/binary/logs and terminal outcomes.

[The integration receipt](../tests/qualification/native-scratch-integration-20261013.json)
pins 315 matching production/package/INSTALL inputs across workspace, fresh
stock/Ox Make and Dune snapshots. Builds/selftests pass both. Strict status,
20 native handles, signal allocation, 86 Copy publication, 40 adoption /
36 old-handoff controls, bound-range and actual local/remote/bidirectional SDE /
old-peer regressions pass. Earlier receipts retain their historical source scope.

## Explicit remaining limits

The clone syscall returns no created FD. The interval before opening/admitting
its result cannot prove object birth if another regular object replaces it
before first open. Failed first admission preserves an unproven leaf. Repeated
witness/unlink failures can preserve a private reservation/basis, and a final
parent-close failure in an otherwise successful two-FD operation can preserve
its linked output after directory authority is lost. Current replacement leaves
and displaced owned aliases are preserved. These are recorded outcomes, not
promises of artifact-free failure.

Check followed by unlink is a cooperative namespace fence, not atomic hostile
compare-and-unlink. Initial ordinary old-temp cleanup remains pathname-based.
Preserved artifacts are not durable quarantine: `Os.childrenOf` may later remove
matching stale temporary files, and a failed basis clone inherits source mtime.
No crash/remount recovery, crash durability, arbitrary asynchronous-success
handoff, actual OOM or exhaustive concurrent schedule is qualified here.
Complete-lifetime FD/memory admission, mount lifecycle, capability caching,
native positional writes and ZFS/ReFS runtime support remain separate work.

## Source pins

Current qualified `src/copy_stubs.c` SHA-256:
`8478e89400128ba53500e3d78e4e8eab854ad744ffc3a886a6d5b037c9d8760b`.
The reviewed predecessor was
`17cdb2b3b31dd0b53a9a1ef1a28588d5d0baa7436f153946fb31df71c310ab4a`;
its line-numbered diagnosis is historical. Current complete source manifests
live in the receipts above. This document releases no external Photo oracle
window or application operation.
