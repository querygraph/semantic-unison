# Native clone-stage scratch ownership: next implementation slice

Status: source-only proposal, 2026-10-13. No production implementation, fixture,
native benchmark, Photo operation or Adobe invocation was performed for this
plan. The current I/O gate and its qualification receipts remain unchanged.

## Problem and exact seams

All three public native clone-stage entry points use
`src/copy_stubs.c:unsn_clone_stage_impl`:

- `unison_clone_stage`: compatibility option, two returned descriptors.
- `unison_clone_stage_status`: strict decline/error result, two descriptors.
- `unison_clone_stage_handles`: strict result, three descriptors including the
  actual directory used for creation.

At the inspected source, the engine opens the destination parent at line 556,
then uses absolute-path `mkstemps(scratch, ...)` at 560 and `unlink(scratch)` at
565. Later clones and opens use `fclonefileat/openat` against the held parent.
Rebinding the pathname can therefore place the reservation/removal in a
different directory from the actual clone. It also closes the reservation FD
before removing the name, losing the witness that could distinguish a
replacement leaf.

Production callers are:

| Caller | Native path |
| --- | --- |
| `Copy` regular receiver stage, around lines 718/1322 | handles ABI, then `StagePublication.adopt` |
| `Copy` local receiver-basis producer, around 799 | strict two-FD ABI |
| `SemanticSync` bound candidate, around 194 | handles ABI, then stage adoption |
| `SemanticSync` synchronous/legacy async candidate, around 20/240 | strict two-FD ABI |
| `SemanticRemote` bound/legacy candidate, around 196/253 | corresponding handles/two-FD ABI |

`StagePublication` and `FinalPublication` do not create this reservation. Their
`name_matches_witness` / `remove_owned_name` helpers show the required held-FD,
no-follow lookup pattern. Keep their already-qualified implementations and the
ML interfaces unchanged. Implement the narrow fix within `copy_stubs.c`; its
three ABIs automatically cover the callers above.

## Chosen creation flow

Retain a real reservation object so the existing reservation/removal phases
remain meaningful. Generate a bounded private basename and create it with
`openat(parent, ..., O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC |
O_NONBLOCK, 0600)`. No scratch filesystem operation uses an absolute pathname.

Use 16 stack bytes from macOS `arc4random_buf`, encode them into 32 lowercase
hexadecimal characters, and allow at most 128 attempts. Regenerate only after
`EEXIST`; propagate every other error immediately. Exhaustion reports `EEXIST`
at the existing `clone_stage: basis reservation` phase. Randomness reduces
collisions; exclusive creation supplies ownership. The basename is never a
peer-provided identifier or a security token.

A fixed internal basename such as
`.unison-basis-<32hex>.unison.tmp` avoids making eligibility depend on the
destination leaf plus a longer random suffix. Keep its maximum length explicit
and below the supported macOS name limit. The internal name is neither wire nor
archive schema. Allocate its small native buffer before entering the blocking
section, retaining the existing `scratch = malloc(...)` ownership ordering and
the pending-signal fixture's meaningful allocation site. The buffer can contain
only the basename. Replace glob-specific leak assertions with exact disposable
directory inventories or a fixture-recorded generated name.

After successful `openat`, retain `reserve` through all admission and removal
checks. Verify its regular kind and the current no-follow leaf against its held
identity. Remove the matching name using `unlinkat(parent, scratch_name, 0)`;
only then close the reservation descriptor and create the basis clone into the
now-absent relative name. Clear the descriptor slot before calling `close`, and
never retry a close that returned an error. An initial removal failure prevents
any basis/output clone or permissive fallback.

This keeps the normal source/basis/output separation and property normalization
unchanged. A successful clone-stage result still returns an unlinked immutable
basis descriptor, a separate writable output descriptor, and optionally the
actual parent. It supplies no physical-block telemetry or crash durability.

## Reservation state and cleanup authority

Separate reservation ownership from cloned-basis ownership; one Boolean called
`scratch_exists` is insufficient to describe both kinds of object. A useful
local state machine is:

| State | Owned native resource | Permitted name action |
| --- | --- | --- |
| No reservation | none | collision retry; never remove the collided leaf |
| Reservation held | `reserve >= 0`, created exclusively in `parent` | remove only the leaf currently matching `reserve` |
| Reservation unlinked | `reserve >= 0`, name no longer owned | close the cleared FD slot; never remove a newly installed leaf |
| Basis clone created, unopened | clone succeeded but no admitted basis witness yet | preserve an unproven/replaced leaf; do not reuse the old reservation witness |
| Basis held | admitted basis FD, current scratch leaf | remove only the leaf currently matching that held basis |
| Basis unlinked | basis FD, no scratch name | transfer/close FD according to existing ABI ownership |

Implement a small private helper for identity-bound relative removal. It uses
`fstat(witness)`, `fstatat(parent, name, ..., AT_SYMLINK_NOFOLLOW)` and a second
`fstat(witness)`. Require regular kind and matching device/inode throughout.
The held FD prevents inode reuse for the witness. A symlink or different inode
is `EBUSY`; lookup errors remain errors. The primary removal requires the leaf
to exist; cleanup can accept `ENOENT` as already absent.

Admission can require a singly linked private object; cleanup should permit
unlinking the matching owned leaf if another hardlink subsequently exists,
preserving that other alias. Do not use size/mode/mtime as persistent ownership
authority: planned native property work can change them. Directory timestamp
changes from sibling operations also do not invalidate the held parent.

Attempt identity-bound cleanup before closing the witness. Clear each named
ownership flag after successful removal, and clear each FD slot before close.
Close all owned descriptors and free all buffers even when removal fails.
Keep the first operational error and phase; a later cleanup error must not
replace it. A cleanup failure without an earlier error must not turn into a
successful return or an unsupported decline. Preserve replacement leaves and
report any remaining private artifact as an explicit qualification limit.

An exclusive clone syscall does not return its created FD. The interval before
opening/admitting the basis is therefore a separate first-admission limit.
If opening or witnessing it fails, do not invent ownership from the earlier
blank reservation or blindly unlink a current leaf. This can leave an unproven
private artifact; it is preferable to deleting a replacement. Qualify and
document that outcome. This slice must not claim hostile namespace CAS or
arbitrary crash recovery.

The current engine also blindly removes `name` under `created` on an output
failure, and closes some witnesses before its scratch cleanup. When changing
the cleanup order, do not silently promote `created` into an identity proof.
Use a still-held admitted output witness where one exists. The unproven output
creation/open interval and the initial ordinary old-temp pathname cleanup are
separate limits; either qualify a corresponding identity-safe native cleanup
in this slice or keep them explicitly open. No `StagePublication` or
`FinalPublication` refactor is needed to fix the reservation itself.

## Errors, platform behavior and C boundary

Keep all OCaml constructor numbers, tuple layouts and ML interfaces unchanged.
Keep `Platform_unavailable`, source-kind/source-flag and basis-clone
`ENOTSUP`/`EXDEV`/`ENOSYS` decline classification at their current scopes.
Reservation, removal, witness, source instability, output-clone and property
errors remain operational failures. In particular, `EIO`, `ENOSPC`, `EACCES`,
`EMFILE`, `EBADF`, collisions and replacement `EBUSY` never authorize ordinary
fallback. Preserve existing primary phase strings where the operation remains:
`basis reservation`, `reservation removal`, `basis clone`, `basis open`,
`basis identity`, `basis unlink`. Add explicit witness/cleanup phases only when
needed. The compatibility ABI continues to use its generic `clone_stage` error
label; strict ABIs keep detailed phases.

Keep the current macOS availability branch and non-macOS platform decline. Do
not add UUID requirements or introduce a new filesystem capability assumption.
Verify the selected Darwin headers declare the randomness/exclusive-open APIs
under the same SDK/compiler configuration; do not infer new platform support.

Preserve preallocation of OCaml result blocks before any native resources,
`caml_process_pending_actions` before native ownership, the no-pending blocking
section, and buffer/ACL/FD cleanup before runtime reacquisition. Released-runtime
work touches only copied native strings, stack data and native resources. No
OCaml allocation, callback, exception helper or borrowed heap-string access is
permitted while released. A bounded collision loop is not an OS deadline.

## Direct qualification for the implementation turn

Use private native fixtures patterned on `tests/clone_handles/fixture.c`: wrap
selected calls or insert C-only hooks in a private source copy. Compile with
each matched compiler and execute only disposable synthetic APFS fixtures.
Production must have no test preference, environment hook or exported fault API.

| Control | Required result |
| --- | --- |
| Normal success through all three ABIs | exact independent basis/output bytes, basis `nlink=0`, output `nlink=1`, correct modes/flags, optional actual parent, no scratch entry or FD leak |
| Rebind destination pathname after parent open | reservation, removal and clones stay under the held parent; replacement directory inventory is untouched |
| Deterministic first-name collisions (file, symlink, directory) | preserve collision sentinels; bounded regeneration; valid later attempt succeeds |
| 128 collisions | terminate promptly with operational `EEXIST` at reservation; no collided name removed |
| Replace reservation leaf before initial removal | `EBUSY`, no clone call, foreign leaf preserved, reserve FD closed; displaced reservation artifact explicitly recorded |
| Remove reservation leaf before initial removal | operational missing-leaf result, no clone call, all owned FDs close |
| Inject reservation open `EIO`/`ENOSPC`/`EACCES`/`EMFILE` | preserve exact errno/phase, no unsupported decline or fallback, no cleanup of foreign names |
| Inject reservation stat/removal failure | first errno/phase preserved; identity-bound cleanup succeeds when possible; repeat-failure artifacts recorded without blind unlink |
| Inject basis-clone scoped decline | existing decline class, reservation already removed, source and output unchanged |
| Inject basis-open/first-witness failure | all FDs close; do not blindly remove an unproven or replaced basis leaf |
| Replace admitted basis before final unlink/cleanup | preserve foreign leaf, fail or preserve original primary error, no descriptor leak |
| Inject output clone/property failure | source unchanged; scratch cleanup uses held basis; output cleanup follows its documented witness authority |
| Reused FD sentinel after a close error | cleared slots prevent a second close from affecting the sentinel |
| Existing pending-signal allocation control | current path owns zero buffers; old-release control retains its documented leak, with any changed allocation count explicitly repinned |

Two private negative controls should fail designated assertions: restore the
absolute `mkstemps/unlink` sequence for the held-parent-rebinding fixture; remove
only the reservation identity check for the replacement-leaf fixture. These
demonstrate that the tests detect the actual defects rather than merely compile
the new helper. Record exact source/mutation/compiler/binary/log pins and terminal
exit results. First prove direct native controls, then rerun current clone
status/handles/publication and synthetic ordinary/local/remote transfer cases.
Refresh isolated Make/Dune builds and the dependent qualification receipts only
after production source is frozen. No SDK/preview oracle is needed for this fix.

## Inspected source pins

| File | SHA-256 |
| --- | --- |
| `src/copy_stubs.c` | `17cdb2b3b31dd0b53a9a1ef1a28588d5d0baa7436f153946fb31df71c310ab4a` |
| `src/fs.ml` | `31c00b85a1ae1fc350c914b58a6f584386e17a30fd98e2840323dbe24ee7d763` |
| `src/fs.mli` | `5ab6513cb1a379d632849935f223c4facd57b2ddc002349aca6f27ecf68523c7` |
| `src/stagePublication_stubs.c` | `f292e14692347583ae42a5ca4ee3bf0181f9f00446feccabbdbe927b31610474` |
| `src/finalPublication_stubs.c` | `0ec93d78d3c94a8e1dc613f84f47577f2f93f689a76ee6657cb52cbd9088b238` |
| `src/copy.ml` | `825b0fd8b721cdcf24715924746e676807bdf109b1a9dc477dd4d5f7a9cc0082` |
| `src/semanticSync.ml` | `e8e2b14042ea9b8785f08a987c37929978d5067485ab1c32210c44a8120a27b3` |
| `src/semanticRemote.ml` | `0dec71478fea4d1a34bb02482f0b21d21f0df15d8576bb764da6316f65203d9b` |

Before implementing, verify these pins against the current source and retain
any later qualification changes. This document authorizes no external Photo
oracle, application operation, cache publication or production-data mutation.
