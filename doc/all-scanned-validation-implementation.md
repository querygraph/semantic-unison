# Unchanged-file Adobe validation: implementation work

The opt-in `adobevalidatescope = received|all-scanned` path is now implemented.
Received/off remains the default. Current generated-fixture qualification covers
local scan RPCs, private snapshot ownership, policy/failure handling and original
fake protocol-driver execution; it is not real Adobe/camera or remote-process
qualification. See [usage and current scope](all-scanned-validation.md).

The source findings and checkpoint sections below are chronological. Earlier
unimplemented/unavailable statements describe their original checkpoint, not the
current product. Full SOL.md completion is still unproven.

## Source findings

`DngCandidateValidation` selects endpoint-local off/warn/require validation.
`CandidateValidation.before_commit_with_reservation` operates on private
receiving staging trees, identifies formats independently from semantic
eligibility, and shares the existing worker/helper/resource runtime. It is
the correct reusable validation path, but its private-candidate assumption
must remain true.

`Update.findLocal` is synchronous. It enables directory fast checking and can
use watcher subpaths; both can omit otherwise unchanged descendants.
`buildUpdateRec` returns `NoUpdates` for unchanged files, and parent directory
results omit those children. Consequently a post-filter over the returned
update list cannot implement all-scanned coverage. A helper call from the
synchronous recursion also cannot safely await worker admission/settlement.

`Fs.clone_file_status` supplies the existing strict whole-file native clone
adapter. Only a scoped no-effect decline permits ordinary copying; failures
and ambiguous effects must not trigger fallback. `SemanticWorkers` currently
has no isolated whole-file snapshot job. Add that job rather than performing
a long ordinary copy on the RPC/Lwt owner or creating another thread pool.

## Required integration

1. Add a separately negotiated scope capability and strict scope parsing.
   Received remains the default. Off must retain its no-validator usability.
   Active all-scanned requests against an incapable peer must fail explicitly,
   rather than silently claiming unchanged-file coverage. Selection is separate
   from semantic profile enablement and filename-only matching.
2. Collect the actual scan-selected regular-file paths, including unchanged
   files. Bypass watcher/directory pruning when it would omit requested work;
   preserve ignore/follow/case/path-selection semantics. Do not independently
   walk arbitrary descendants outside that selected namespace. Bound retained
   path bookkeeping before allocation; a bounded private spool or incremental
   owner-driven traversal can avoid an unbounded in-memory list. Overflow must
   be reported rather than silently truncating coverage.
3. Implement an admitted snapshot job using retained source descriptors and
   exclusively created private destinations. Reuse strict native cloning, then
   a bounded cancel-aware exact-copy fallback on qualified no-effect declines.
   Keep original path/descriptor epochs fenced across snapshot creation and
   validation. A new snapshot must have a distinct inode and no hard link to
   the original. A no-op plan does not waive snapshot ownership checks.
4. Keep snapshots outside the synchronized namespace, with restrictive private
   parent permissions. Passing an arbitrary helper a live unchanged original
   is prohibited: detecting mutation after hashing would not undo damage.
   Snapshot/helper mutation must fail; original data/properties remain untouched.
   Temp-file removal and descriptor retirement follow actual worker/helper
   settlement, including failed/cancelled and uncertain outcomes.
5. Feed only the private snapshot into the existing format recognition and
   selected companion validator. Preserve the original destination claim for
   recognition/reporting. Avoid nested global admission: the owner holds one
   envelope for manifest/snapshot buffers and declared backend resources, and
   worker/helper tasks share the same CPU and I/O gates. Multi-filesystem
   snapshot copying needs ordered source/destination admission, not two nested
   acquisitions of the same gate. Credits are not whole-process hard caps.
6. Await validation after local scan work and before reporting that root's
   all-scanned phase complete. Keep RPC waits asynchronous; all active tasks
   settle on failure/abort/disconnect. Unchanged-file failures must be visible
   under require/warn policy, without fabricating a transfer or archive update.
   Keep scan bookkeeping and durable archive effects distinct from validation
   completion. Repeated syncs revalidate unchanged files only in explicit
   all-scanned mode; default received no-ops invoke no helper.

## Qualification before the feature is complete

Use original generated fixtures first. Test received/off no-op behavior,
all-scanned unchanged/new/changed files, content recognition without a DNG
suffix, ignored paths, nested unchanged directories, watcher and immutable
directory shortcuts, followed links and path translation. Verify the actual
selected set independently rather than counting fabricated callback entries.

For snapshot isolation, retain old original readers and compare exact bytes,
mode, links and applicable properties before/after a deliberately mutating
fake helper. Cover native-clone decline, partial/failing native operations,
ordinary-copy interruption, source mutation, snapshot mutation, budget refusal,
capture/helper cancellation, disconnect and cleanup uncertainty. A helper's
zero exit does not override invalid/missing protocol evidence. Check all active
groups/resources settle and the second default received sync remains a true
no-op. Keep real SDK validation a separately coordinated finite successor.

The immediate implementation step is the bounded worker snapshot API and its
owned descriptor contract, followed by scan coverage collection and endpoint
integration. Do not expose an enabled all-scanned setting before those parts
are wired and qualified. Private MakN vendor grammar remains separate work;
all-scanned validates DNGs independently of semantic-transfer eligibility.

## Snapshot kernel checkpoint

`src/validationSnapshot.{ml,mli}` now implements the isolated borrowed-FD
materializer. It checks an explicit source-byte budget and distinct, empty,
single-link output before calling the injected existing-clone adapter. Strict
receipt validation permits fallback only after a no-effect decline; native
exceptions/failures/cursor changes/inconsistent effects never select fallback.
The ordinary path writes in <=64KiB chunks with cancellation and EINTR/short-write
handling, hashes the source stream, then independently hashes the full output.
It fences cooperative source metadata across the operation. Read/write output
ownership, path bindings and any stronger native timestamp fences remain caller
responsibilities; no file is created, published, chmodded or retired here.

Stock and Ox component builds and original generated-fixture controls passed,
including empty and64KiB boundaries, budget/same-inode/nonempty refusals, native
exception and typed failure, correct simulated native output, false-success
digest rejection and cancellation. All four compiler/test groups and the outer
controller reaped0, CPU8 closed: actualsession8225/fd198f/0.
[Evidence](../tests/qualification/validation-snapshot-kernel-v2-actual-20261017.json)
preserves the adapter as an explicit test double: no native cloning, SDK,
retained photo or full CLI execution occurred. The earlier control receipt
remains historical.

At that checkpoint the kernel was not yet wired. The subsequent worker/build
integration below supersedes that state; scan coverage is still pending.

## Worker/build integration checkpoint

`SemanticWorkers.snapshot` now uses a typed operation/response and the existing
output-FD duplication, queue transfer and retirement path. Source and destination
filesystem keys are admitted as one union before CPU admission. Snapshot code
binds the same `unison_clone_file_status` primitive/receipt decoder used by
`Fs.clone_file_status`; no second native engine or named-owner protocol was added.
Both descriptors stay borrowed until actual settlement; cancellation suppresses
delivery and does not authorize early staging deletion.

WholeFileClone and ValidationSnapshot now have checked portable interfaces and
explicit Make/Dune mode-filter wiring. Full stock/Ox Make build-only runs passed;
Dune build-only wiring passed on the first version, before the final worker
telemetry/comment correction. Current002 Make builds cover that correction.
All six actual build parents/groups/CPU8 leases closed; no CLI selftests or SDK
were invoked by these build-only slots.

Current production-object controls passed on stock and checked Ox: three exact
131111B snapshots, byte-budget and same-inode refusal, CPU-queued cancellation,
empty worker/CPU/IO ledgers and immutable source bytes. The macOS FD clone
backend declined; all six copies used the bounded ordinary path. This is not
APFS native-sharing evidence. Snapshot jobs intentionally do not emit the outer
reader's zero-byte counter; an ordinary digest still emits131111B. Actual final
owner63473/c1af41/0, outer28224 and four compiler/test children reaped0; CPU8
closed. See [current worker controls](../tests/qualification/validation-snapshot-workers-v2-actual-20261017.json)
and [build closures](../tests/qualification/validation-snapshot-builds-actual-20261017.json).

No retained photo, SDK, catalog or publication operation occurred. This is the
worker primitive, not an enabled all-scanned feature. Next implement the private
staging owner with source/name fences and bounded outer admission, then actual
scan-selected coverage and negotiated scope. Existing worker close-error fault
limits and platform scopes are not expanded by these successful cases.

## Private stage owner checkpoint

`validationStage.{ml,mli}` now provides the owner-loop lifetime primitive:
existing owned0700 parent, read-only source name/descriptor binding, exclusive
0600 stage, native macOS source epoch when supported, cooperative stat fallback
only for exact unsupported-platform ENOSYS. Rebound parents, source names,
source epochs and stage names refuse. Only the disposable path is exposed for
future helper use; owned descriptors are close-on-exec. Parent creation, outer
admission, worker/helper invocation and scan selection are not done here.

Retirement unlinks only the still-bound owned stage and closes independent
descriptors once. Replacements are preserved. A close error retains pre-close
facts in an opaque owner; later getters and retirement preserve that carrier
without probing/retrying the uncertain number. The first caller-supplied failure
can be retained alongside cleanup uncertainty. The eventual asynchronous wrapper
MUST keep admission/FD credits on that carrier rather than throwing through an
auto-releasing callback. A persistent allocation-failure or arbitrary same-UID
namespace attack is not qualified by these finite controls.

Stock/Ox standalone controls passed seven groups each: normal snapshot/private
mutation cleanup, source replacement, stage replacement, preentry refusals,
exclusive-create collision, external source edit and close-error/no-retry
retention. The close control deliberately closes a borrowed descriptor first
(precondition violation), then reuses its numeric slot and proves a second
retirement leaves the new descriptor intact. This is an injected EBADF model,
not a genuinely ambiguous kernel-close experiment. All native test processes
and compiler groups reaped0, CPU8 closed: actual18118/5cfea1/0, outer30366.
[Evidence](../tests/qualification/validation-stage-owner-v2-actual-20261017.json)
preserves the raw four compiler/test outcomes and exact sources. No SDK, photo,
native cloning, Main/cache writes or enabled all-scanned path.

This owner remains separately compiled groundwork. Dune's standard module
discovery will see it on the next build; explicit Make wiring and the actual
CandidateValidation asynchronous staging wrapper remain next. That integration
must handle retained uncertainty before exposing any all-scanned setting.

## Asynchronous staging wrapper checkpoint

`ValidationStageWork.run` now composes the real snapshot queue, original/stage
fences, an owner-side validation callback, independent final stage rehash and
retirement. Its callback receives the disposable candidate pathname and snapshot
report; it must return the promise covering every borrower it starts. Returned
sleeping work is guarded by BorrowedWork before retirement. Cancellation after
validation starts waits for that work, then fails and cleans up. Stage mutation
rejects even when the callback returns success.

The caller must acquire the full outer memory/descriptor envelope first.
Cleanup uncertainty roots the opaque owner and returns an uncompleted promise,
so automatic admission cleanup cannot run. Diagnostic callback failures cannot
release it. No numeric-FD retry, release Boolean or fabricated recovery API is
provided; whole-process closure/coordinated recovery is separate. The future
CandidateValidation entry must provide meaningful retention diagnostics.

Both owner modules are now explicitly linked in Make; Dune discovers them via
its existing standard module set. Current stock/Ox full Make build-only slots
passed/closed, with all production source hashes matching;
[build evidence](../tests/qualification/validation-stage-work-builds-actual-20261017.json).
Current production-object controls passed success, callback failure, mutation,
sleeping callback cancellation and retained cleanup uncertainty on both compilers
(actual76318/f66e06/0, outer34811/four compile-test groups reaped0/CPU8 closed).
[Raw controls](../tests/qualification/validation-stage-work-v2-actual-20261017.json)
explicitly retain one symbolic admission in the injected EBADF case until the
test process exits; no successful callback release is claimed. As before this
injection intentionally violates a borrow precondition, not a genuine ambiguous
OS-close experiment. The first control compile failed because embedded Lwt has
poll rather than state; its actual failed-prefix evidence is preserved, and the
control-only fix did not change production code.

No SDK, photos, catalog, production publication or enabled all-scanned scope.
Next connect selected validators and bounded outer admission in CandidateValidation.
Select formats through held read-only recognition before expensive snapshots,
so a huge non-DNG does not fail a DNG snapshot-size policy. Then implement actual
scan-selected coverage, preference negotiation and no-op/cross-peer controls.

## Current source checkpoint — internal unchanged-file validation

The new `CandidateValidation.unchanged_file` entry is implemented and qualified
against current stock/Ox Make objects. It remains INTERNAL: no all-scanned
preference, negotiated capability, scan traversal, or production activation yet.
`SemanticWorkers.recognize` performs bounded recognition without the existing
Identify operation's whole-file fingerprint. Off opens nothing; a generated
nonmatch larger than the snapshot budget reads only four recognition bytes and
skips hashing/copying/validation. A matched file obeys the snapshot byte budget;
validators receive only its private snapshot. Success, rejection, private
mutation, cancellation, and retained-uncertainty controls passed for both
compilers. The canonical staging Fspath is passed in; this entry never changes
process CWD. The worker Identify fingerprint behavior remains covered.

Actual control owner ec7bac/session38387 -> terminal4df709/exit0/no session;
three controllers/twelve compile-or-test child calls reaped0, groups settled,
Unison00..07 released. Evidence:
`tests/qualification/unchanged-validation-entry-actual-20261017.json`.
Current Make build005 stock and Ox succeeded; stock's original parent handle
85221 was missing on continuation, so its parent terminal is NOT reconstructed
from SHARED-CLOSED. Ox actual47362/ce238f/0/no session. Build004 preceded the
CWD correction and is historical. The stage-work harness now pins itself;
older harness receipts are not retroactively described as self-pinned.
All fixtures generated/private; no SDK, Photo payload, new native sharing,
all-scanned activation, or general legacy FD-fault qualification follows.

Next: exact scan-selected work coverage, private endpoint staging initialization,
followed-link/path policy, scope/capability negotiation and default/no-op tests.
Do not expose all-scanned based only on this internal entry.

User steering: exiftool-rs is being extended separately for dng-compare. Revisit
reuse here after that work is ready; do not install, switch validators, or add
an exiftool-rs dependency now. Existing source review remains historical.

## Current scanner coverage checkpoint

`ValidationPaths` now bounds retained unique endpoint-local file count and total
pathname bytes. Overflow poisons the collector: no partial prefix can be read
or resumed. This does not claim a whole-process RSS or traversal-time hard cap.
`Update.findLocalWithValidation` collects regular files directly during the real
selected scanner traversal, including NoUpdates children, and disables watcher
subpath/directory fast-check coverage omissions. Existing immutable subtrees use
the scanner's same filename/ignore/follow metadata rules to collect coverage
without changing immutable update detection/archive results. A failing bounded
scan unwinds watcher bookkeeping and fingerprint cache state. No user-facing
preference/RPC/feature activates the entry yet.

Current stock/Ox Make002 builds passed and four current-object compiler/test
calls passed over generated private replicas. Actual owner62296/0ed6c7/exit0/no
session, all contained groups reaped0 and CPU8 closed. Unchanged nested files,
modified immutable files, ignored paths, followed file links, overlapping selected
paths, new/changed files, both resource refusals and a subsequent clean scan are
covered. Evidence `tests/qualification/validation-scan-actual-20261017.json`.
Stock001 preceded the watcher cleanup correction and is historical; stock002
15629/6c0d6b/0 and Ox00224575/0abd92/0 match current production code.
Watcher hints were supplied with watch=false; no live watcher helper/protocol
qualification is claimed. Source/fixture only, no Adobe/SDK/Photo payload.

Next endpoint activation must create a private staging directory outside roots,
resolve/fence followed paths without process-CWD mutation, report existing nested
scan errors rather than claim complete coverage, and await admitted private-file
validation before the endpoint scan returns. Add strict received/all-scanned
scope parsing and negotiated capability only with end-to-end default/off/no-op,
old-peer, ignore/follow and failure/cancellation tests. All-scanned remains
unavailable until that integration is qualified; private MakN grammar and broader
native/resource/corpus requirements remain separately open.

## Held-output validation checkpoint

Unchanged-file CandidateValidation now borrows the private stage owner's held
output FD for recognition, reinspection and filesystem admission around execution.
It does not reopen that path through the legacy temporary-descriptor wrappers.
Inspection refuses every other pathname, including the original. StageWork lends
ONLY the disposable output FD, never the original FD; trusted callbacks must read
it without closing/retaining it beyond their actual returned promise. The stage
owner/admission stays live throughout callback settlement and final integrity
checks. Pathname helpers still receive only the private pathname. This is not an
OS-enforced read-only handle or sandbox. Existing received-file wrapper and worker
close-fault limitations are not relabeled as fixed by this change.

Current stock/Ox Make builds passed; actual37127/3ba42a/0 and14865/b9ed28/0.
Two controllers/eight compiler-or-test calls passed under canonical Unison8;
actual60080/a2dead/exit0/no session, all attempted groups reaped0 and tokens closed.
Evidence `tests/qualification/validation-borrowed-output-actual-20261017.json`.
Original fixtures check stage-FD/inode isolation, original-path refusal, held-FD
inspection while the disposable pathname is temporarily moved then restored,
filesystem admission around an original fake execution callback, mutation
rejection, sleeping cancellation and retained uncertainty. The fake execution
callback launches NO subprocess and provides no SDK/helper protocol acceptance.
No Photo payload/source mutation/new native admission.

All-scanned endpoint integration remains pending. The lifetime correction was
needed before enabling it; next implement private endpoint directory ownership,
non-CWD-changing followed-path resolution/fences, strict scope/capability handling,
scan-error propagation and awaited endpoint completion. Do not expose the option
based on the component tests alone. Full SOL.md goal remains active/incomplete.

## Current checkpoint — all-scanned scope implemented

Opt-in `adobevalidatescope = all-scanned` is wired through the existing find RPC,
with new negotiated `dng-validation-all-scanned-v1` capability. Default
`adobevalidate = off` / scope received retains no-op behavior. Selected unchanged,
new, immutable and followed files use the real bounded scanner; ignore rules
remain in force, and errors/overflow reject coverage. Each endpoint captures validator/tool policy ONCE
before enumeration. Reentrant policy changes cannot silently skip later files.
Both started endpoint promises drain on failure. No wire/archive format changed.

`ValidationScanWork` creates a fresh0700 private directory outside supplied local
roots, resolves existing/followed paths without process CWD changes and checks
logical bindings before/after each file. Serial snapshot validation retains the
existing per-file resource envelope. Failed cleanup preserves original errors,
unrelated entries/replacements and pending borrower ownership. Warnings/rejections
name the logical file; helpers still get only the isolated pathname.

`ValidationDescriptor` replaces CandidateValidation's temporary descriptor closer:
one close after actual borrowed work, retained identity/original cause and pending
admission on uncertainty, no numeric retry. Candidate inspection borrows the held
stage FD; separate artifact inspection permits driver/limiter hashes but refuses
original inode aliases. The earlier candidate-only guard was too restrictive for
driver hashing; it is superseded, not actual SDK evidence. Existing other worker /
receiving helper-IO close-fault limitations remain open.

FINAL evidence: `tests/qualification/all-scanned-current-v4-actual-20261017.json`.
Stock/Ox Make AND Dune006 build-only PASS/CLOSED under one sequential controller,
actual20352/3c91d5/0/no session. Four groups/token sets independently closed.
Three current-object controllers/14 compiler-or-test calls and FOUR original fake
protocol-driver subprocesses passed; actual26283/38672b/0/no session. Independent
readback performed1228production-input,1208prefix-source and1946artifact hash
checks (including repeated checks) plus current child/group proofs. Our CPU8
reservations are closed; no EXIO/SDK/Photo-native reservation was taken.
Tests cover require/warn/unavailable driver, active/off/received/repeated no-ops,
missing peer capability/late preference checks, source follow-retarget refusal,
private mutation, captured policy, logical warnings, cleanup residue, cancellation
and actual fake driver/tool inspection. Two injected close-uncertainty carriers
and two admitted loans per endpoint control deliberately remain pending until
that disposable process exits; they are NOT ordinary in-process retirement.

Preserved build005 failure: actual59615/9a9cf0/exit2/no session; Ox guard rejected
an updated interface comment whose checked template had not yet been refreshed.
Failed child/group/tokens closed.006 synchronizes the template and passes both
compilers/build systems. Earlier prototypes/receipts retain their exact sources;
latest qualification supersedes only their current-source claims, no runtime
admission/replay is inferred. All fixtures generated; synthetic helper protocol
raw-digest missing is NOT Adobe raw-digest/decode/pixel evidence.

Next: prepare a fresh source-pinned real SDK all-scanned IO request and qualify
actual remote-process/old-peer combinations/live watcher scopes. No such SDK or
private-camera grant currently exists; do NOT reuse consumed grants. Source-only
MakN vendor/reference grammar work and broader M4-V/M6/corpus/portable-hash work
continue independently. Full SOL.md goal remains ACTIVE/INCOMPLETE.
Usage/contracts: `doc/all-scanned-validation.md`. exiftool-rs reuse remains deferred
until the separate extensions/dng-compare integration is ready; Perl13.59 baseline
and all historical timing/failedpart3/consumed-admission caveats remain preserved.
