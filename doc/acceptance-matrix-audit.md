# Required acceptance matrix: scope audit

This maps the twelve requirements in `SOL.md` to existing receipt scopes. It is a source/receipt audit, not a new execution or independent implementation review. Every row remains partially qualified. Hashing a receipt below does not revalidate its historical production source or expand its claims.

| Requirement | Existing scoped evidence | Still open |
| --- | --- | --- |
| 1. Exactness | Independent SDE/SDR vectors, complement/full hashes, scoped synthetic materialization, exact CLI/no-op controls. [conformance](../tests/semantic/conformance/qualification-20261013.json), [qualification](../tests/qualification/shared-functional-actual-20261016.json) | Full source-selected fork/property state across all supported filesystem and publication families is not established by kernel vectors. |
| 2. Container coverage | Synthetic classic TIFF/BigTIFF in both byte orders, embedded CR graph and independently placed protected values; narrow standard JPEG XMP profile. [dng_profile_v1](../tests/dng_profile_v1/qualification-20261013.json), [jpeg](../tests/jpeg/qualification.json) | Representative real-camera corpus, broader private tag/layout strata and photographic validity are not established. Unsupported layouts use ordinary exact transfer. |
| 3. Malformed input | Finite malformed directories, bounded graph/count/extent handling, wire rejection vectors and JPEG fill bounds. [dng_profile_v1](../tests/dng_profile_v1/qualification-20261013.json), [conformance](../tests/semantic/conformance/qualification-20261013.json), [jpeg](../tests/jpeg/fill-bound-qualification.json) | No automatic fuzz/sanitizer campaign or whole-process parser RSS qualification. User-run fuzz workflows remain separate. |
| 4. Integrity | Full/complement identities and corrupt wire proofs; generated SDK raw-digest controls and exact production receiving/merge pilots. [conformance](../tests/semantic/conformance/qualification-20261013.json), [qualification](../tests/qualification/sdk-live-merge-v1-actual-return-20261015.json) | Real-camera SDK corpus, decoded pixel/encoding distinctions and universal Adobe validation are not inferred. Preview fidelity is Photo-owned evidence, not semantic-DNG integrity proof. |
| 5. Concurrent modification | Retained regular-file producer witness, stable target/source binding, cooperative namespace guards and seeded canceled worker apply controls. [qualification](../tests/qualification/retained-producer-publication-20261013.json), [workers](../tests/workers/seeded-apply-stress-qualification.json) | No atomic namespace compare-and-swap against hostile writers, reliable mount-incarnation detection, persistent OOM or universal async fault coverage. |
| 6. Failure and recovery | Scoped native/Files/CLI publication faults, validator settlement, two-receiver merge rejection/retry and owned process cleanup. [qualification](../tests/qualification/retained-producer-publication-20261013.json), [validation_settlement](../tests/validation_settlement/qualification-20261013.json), [dng_merge](../tests/dng_merge/qualification.json) | Not a complete clone/write/properties/flush/rename/archive fault cross-product or power-loss durability proof. Additional-name/directory/legacy families and abrupt owner-SIGKILL remain distinct. |
| 7. Filesystem behavior | Owned APFS clone contracts plus private cross-volume fallback/exact/no-op controls and existing property/publication fixtures. [whole_file_clone](../tests/whole_file_clone/qualification.json), [qualification](../tests/qualification/whole-file-clone-integration-20261014.json), [cross_volume](../tests/cross_volume/qualification.json) | No new Linux/ZFS/ReFS runtime, physical allocation/write-amplification, mount-loss, independent-device throughput or exhaustive fork/ACL/sparse/compression coverage. |
| 8. Compatibility | Stock/Ox builds and same-host wire controls; archive roundtrip through installed unmodified2.53.5, missing-base refusal and later merge recovery. [archive_downgrade](../tests/archive_downgrade/qualification.json), [qualification](../tests/qualification/shared-functional-actual-20261016.json) | Not complete GUI/platform/monitor/build or every profile/ignore/property/cancellation combination. Historical receipts retain their exact source snapshots. |
| 9. Parallelism and resource accounting | Checked worker closures, seeded apply/cancellation parity, endpoint-local filesystem job gates and actual standing8 shared ownership/functional controls. [checked_worker](../tests/checked_worker/qualification.json), [workers](../tests/workers/seeded-apply-stress-qualification.json), [io_admission](../tests/io_admission/runtime-qualification-20261013.json), [qualification](../tests/qualification/shared-entrypoints-actual-20261016.json), [qualification](../tests/qualification/shared-functional-actual-20261016.json) | No hard whole-tree RSS/FD/CPU cap, physical-device shared IO lanes, arbitrary native thread fanout or race-sanitizer qualification. st_dev is not a physical disk identity. |
| 10. Semantic merge | Conservative opt-in fixed-region scalar reconciliation, compact common-base cache controls, archive downgrade/refusal and generated SDK receiving/merge. [dng_reconcile](../tests/dng_reconcile/qualification.json), [dng_merge](../tests/dng_merge/qualification.json), [sdk_container_receive](../tests/sdk_container_receive/quota-merge-qualification.json), [archive_downgrade](../tests/archive_downgrade/qualification.json), [qualification](../tests/qualification/sdk-live-merge-v1-actual-return-20261015.json) | No general RDF/Bag/Seq/Alt/qualifier/rendering merge, packet growth or distributed atomic two-replica commit. Unsupported shape/unknown edits must preserve conflict, not imply safe semantic equivalence. |
| 11. Generic cloned transfer | Upstream reuse, strict whole-file clone, receiver-basis ordinary-file path, scoped range adapter and exact/no-op generated comparisons. [whole_file_clone](../tests/whole_file_clone/qualification.json), [whole-file-clone-integration-20261014](../tests/qualification/whole-file-clone-integration-20261014.json), [cross_volume](../tests/cross_volume/qualification.json), [shared-functional-actual-20261016](../tests/qualification/shared-functional-actual-20261016.json), [native-copy-range-integration-20261013](../tests/qualification/native-copy-range-integration-20261013.json), [native_copy_range](../tests/native_copy_range/typed-context-qualification.json) | Not filesystem-wide capability caching/mount incarnation, universal alignment/partial-effect/native-backend qualification or physical sharing proof. Failed timed part3 remains incomplete. |
| 12. Adobe invocation and CPU accounting | Synthetic receive-path/gate/companion lifecycle coverage, generated real SDK live merge receiving and scoped shared CPU accounting. [validation_paths](../tests/validation_paths/qualification-20261013.json), [qualification](../tests/qualification/validation-companion-integration-20261013.json), [validation_settlement](../tests/validation_settlement/qualification-20261013.json), [qualification](../tests/qualification/sdk-live-merge-v1-actual-return-20261015.json), [qualification](../tests/qualification/shared-functional-actual-20261016.json) | No all-scanned validation feature, representative camera corpus, experimental SDK OS-thread/scaling/RSS/cancellation qualification or full mixed ExifTool/hash/Adobe workload proof. Each new SDK slot remains separately coordinated. |

The [machine-readable map](../tests/qualification/acceptance-scope-audit-20261016.json) pins the selected receipt documents. Older intermediate checkpoints are not silently promoted to their successors. In particular, producer-handoff, native publication and source/GUI checks keep their own limitations.

Next practical gate: bounded copy-only real-camera DNG eligibility and exact receiving, using explicitly coordinated verified private copies. Do not read Photo-owned payloads or invoke Adobe merely because a prior native window ended. SDK validation, exact encoded-byte identity, decoded samples, rendered appearance and preview reuse remain separate identities.

An optional generated-fixture property-removal successor matrix is source-prepared
(`SYNC_PROPERTY_REMOVAL_CONTROLS=1` on the exact-admitted shared IO route).
It checks named xattr/native resource-fork removal, readonly mode, retained old
reader bytes/properties and unchanged no-op epochs. The CPU-only dispatcher
refuses this route. [Source controls](../tests/qualification/property-journal-source-controls-actual-20261016.json)
cover eight four-byte Darwin fixtures, seven fake-call journal cases and the
existing admission/lifecycle controls. This is not actual property receiving
qualification. Each invocation now persists intent before dispatch and its
returned outcome before row verification, with file and directory fsync. Missing
outcomes remain unknown; neither a journal entry nor a nonzero outcome proves
settlement. Failed partial-matrix release and actual property-transfer controls
remain to be qualified before scheduling the new IO run. Historical admitted
source pins and completed runs are unchanged.

Its v1 attempt failed on the first seed's CLI argument parsing, before any
server creation: [preserved failure/recovery](../tests/qualification/shared-property-failed-actual-20261016.json).
No rows completed, and no property receiving pass is claimed. The original
idle retention owner was stopped only after independent no-server/client/group
proof; actual parent exit137 and absence of original-parent worker wait4 are
explicit. All resources were independently reacquired/closed and Root adopted
recovery. [V2](shared-property-io-request-v2.json) fixes `-xattrs=true` and adds
an explicit no-server proof branch, with [actual Python peer/dispatcher controls](../tests/qualification/property-v2-source-lifecycle-actual-20261016.json).
Only a full pinned no-creation frame is accepted; null server PID alone is not
evidence. V1 is consumed; V2 needs a fresh admission and has never run.

A separate [journal-prefix source qualification](../tests/qualification/journal-prefix-source-controls-actual-20261016.json)
now distinguishes known nonzero call settlement from functional success. Its
pure audit requires ordered intent/outcome bindings, client and supervisor
group-before-reap proofs, server exit/PID/command binding and joined input pump.
Missing server creation evidence remains unknown. The dispatcher now uses this
audit for explicitly failed results, then independently settles its aggregate
worker and requires its actual nonzero exit before closing leases. Complete
results retain the full 54-call functional audit. [Fake-owner integration controls](../tests/qualification/failed-sync-dispatch-source-controls-actual-20261016.json)
cover known failed-prefix release, unknown-call retention before reap, and
contradictory successful worker-exit retention. Actual failed sync-call lifecycle
integration remains unqualified; these controls do not authorize an IO run.

The [actual Python-peer lifecycle control](../tests/qualification/journal-peer-lifecycle-actual-20261016.json)
exercises the real loopback proxy and measure wrapper with two tiny original
Python peers: exit0 and deliberate exit7. Both retain client/supervisor/server
settlement receipts through journal persistence and a later verification-failure
record. The containing owner actually exited0 with its group settled and tokens
closed. This component control uses no Unison executable or EXglobal IO and does
not by itself qualify complete dispatcher failed-run release or property receiving.

The subsequent [actual dispatcher/peer control](../tests/qualification/failed-sync-dispatch-peer-actual-20261016.json)
does exercise complete failed-run release: an inner worker performs the real
two-peer component test, writes its failed result and exits7; the actual parent
audits that journal, settles the worker group, closes disposable inner leases,
and returns7. Its outer canonical eight-credit owner then closes normally with
actual terminal0. Admission authentication and canonical physical IO are not
mocked into claims: inner leases are explicitly disposable, and no EXglobal
barrier or Unison binary is used. The pending generated property-transfer
request retains its original execution pins; this is additional evidence only.

The frozen benchmark series stays unchanged: part3 failed/incomplete, mandatory part0 overlap and part3/part5 disclosures retained. Five complete partitions do not establish a full six-part result or clean quiet timing. Routine Adobe-free work can continue in the standing Unison eight-credit lane; no new whole-machine reservation is required for this audit.

Current production sources, including the local profile-inspection identity
guard, also passed fresh serial stock/Ox Dune builds and application selftests:
[actual Dune receipt](../tests/qualification/current-dune-profile-guard-selftests-actual-20261016.json).
Both owners exited0, with worker groups and Unison tokens closed. This updates
build-system evidence only; it does not promote historical receiving receipts
to new source snapshots or qualify the pending property-transfer matrix.
