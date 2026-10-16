# Unchanged-file Adobe validation: implementation work

This is the remaining implementation plan for SOL.md's optional
`adobevalidatescope = received|all-scanned`. The current product implements
receiving validation only. No all-scanned preference, runtime capability or
unchanged-file coverage is claimed by this document. Default received/off
behavior and current source files are unchanged.

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
