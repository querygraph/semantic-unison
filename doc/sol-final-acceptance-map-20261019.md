# SOL final acceptance map — 2026-10-19

Goal remains ACTIVE/incomplete. Production candidate971271a8 changes only
`src/semanticRuntime.ml` relative to V6 production513c121a; later work through
508ded42 is test tooling, evidence and documentation. Full current stock/Ox
Make/Dune builds and selftests are recorded. PR13 remains draft; no merge or
production activation is authorized by these results.

The new metadata audit checked21receipts/build records: {'ALL_DIRECT_BINDINGS_MATCH': 9, 'HISTORICAL_OR_MIXED_SOURCE_BINDINGS': 3, 'NO_DIRECT_BINDINGS': 9}. This is explicit
path/hash matching, not a test rerun, an implicit traversal of referenced files
or proof of complete dependency coverage. NO_DIRECT_BINDINGS never means
current. New receiving receipts are joined separately to their pinned plans,
actual tools, current binary/build receipts, raw proxy frames and group closure.
The older cache/warning Runtime differences are superseded for that dependency
by the new current329pin composition receipt; the older originals are preserved.

| SOL requirement | Inspected evidence and proved scope | Remaining closure / limit |
| --- | --- | --- |
| 1 Exactness | Current independent SDE/golden/apply controls; current ranges and clone-backed reconciliation; all ten32MiB cohorts plus first128MiB cohort verify exact outputs, unchanged bases and no-op inode behavior. | Trace the named first/last/zero/multiple packet and fork/property cases to exact current or justified unchanged-source evidence; benchmark byte equality alone does not cover every edge. |
| 2 Coverage | Current component/worker source bindings, XMP kernel/observation, opaque exact-layout predecessor receiving and conservative refusal contracts. | Complete explicit byte-order/IFD/tag/preview/embedded-original/opcode case mapping. Unknown private meanings remain opaque and are NOT a deployment blocker. No universal camera/pixel claim. |
| 3 Malformed input | Fixed current SDE malformed/binding vectors, constrained range cases and bounded parser ownership controls are retained. | Match cycles/alias/count/offset/truncation/XML limits to actual cases and dependencies. User excludes new fuzz/sanitizer campaigns; do not invent a missing campaign or universal malformed-input proof. |
| 4 Integrity | Current SDE/base/hash/opaque guards; current realSDK structure/decode/raw-digestvalid full receiving and no-op scan results. | Current-candidate negative raw-digest/corrupt-output receiving proof and exact opaque/different-encoding counterexample mapping; SDK digest equality is not pixel/semantic equality. |
| 5 Concurrent modification | Current source/worker apply-cancel controls and source/native ownership scopes; frozen V6 property/transport originals retained. | Map receiver/source/symlink/inode/cache/late-completion/mtime-restoration cases. Uncooperative check-to-rename race remains documented, not “eliminated” by a test. |
| 6 Failure/recovery | Current warning/cancel/cache/input-pipeline composition; independent native range errors; preserved actual failed-prefix/recovery receipts. | Explicit clone/pwrite/property/flush/rename/archive/ENOSPC/drop/abort case-to-current-source map. Known recovery is not original-owner normal wait or crash durability. |
| 7 Filesystems | Darwin constrained48cases/compiler including960combination matrix and13ABI cases; V6 actual properties slot18rows54CLI. | Review exact sparse/hardlink/open-reader/fork/xattr/ACL/stash cases and available cross-volume/non-APFS evidence. No inferred APFS physical block savings or new ZFS/ReFS runtime qualification. |
| 8 Compatibility | V6 genuine-upstream12CLI and retained-fork12CLI actual closures, plus source-bound current full builds. CPU ceiling is endpoint-local; archive/RPC code is unchanged by971271a8. | Bind final review candidate and document the V6 source distinction; do not relabel predecessor actual runs as new executions. Finish explicit profiles/archives/platform case mapping. |
| 9 Parallelism | Current configured1/2/4/8 parity/apply controls, four builds and ten actual stock/Ox1/2/4/8/auto cohorts. MixedSDK/ExifTool/hash current probes closed normally. | Larger/workload/topology measurement scope and precise resource limits remain open. Configured bounds are not OS-thread counts, hardRSS or simultaneous whole-tree peaks. |
| 10 Semantic merge | Current XMP scalar-policy/observation tests and nine clone-backed reconciliation controls/compiler,3072returned logical bytes/one write on a private2MiB fixture. | Explicit conflict/delete/Bag/Seq/Alt/qualifier/rendering/unknown/base/convergence mapping and final-candidate receiving merged output. Unsupported compound/rendering merges must refuse, not guess. |
| 11 Generic clones | Upstream reuse remains the production adapter path; current constrained range results; frozen V6 properties/transport and exact ordinary/receiver-clone benchmark rows. | Named prefix/duplicates/allliteral/allmatched/EOF/same-offset/shifted/property/partial-resume/cache-invalid cases need final evidence map. Output extent models do not prove physical writes. |
| 12 Adobe and budgeting | Current mixed2SDK+2ExifTool+32hash tasks; full receiving2CLI4SDK; all-scanned4CLI4SDK with off/noSDK and require/no-transfer; current warning composition and CPU ceiling controls. All actual parents/groups/FDs closed. | Final receiving-path off/warn/require/reuse/resume/merge and negative finding mapping; complete qualified tool/budget/cancel scopes without claiming wholeOS hard caps or corpus/rendering equivalence. |

## Current execution and scheduling

No owned processes or CPU/IO descriptors remain live. The ten32MiB cohorts
passed180rows540CLI. First128MiBstock1 passed18rows54CLI; its saved report is
INCOMPLETE_MATRIX at that size. The remaining29larger cohorts are UNSTARTED.
The first128 empirical checkpoint supports roughly18–30hours/central23hours for
the entire prepared30cohort size matrix by rough byte scaling. This is a
planning estimate, not a hard duration or continuous quiet grant. Further
payload starts await the scheduling review raised by Photo; source work can
continue under standing8/8+2. New18conditionalfda6288a is NOT ACTIVE. Photo
IO/native remains postponed by user steering. Main stays Photo-exclusive.

Other prescribed workloads/topologies and original/upstream performance
comparisons remain separate; completing the larger fixed-XMP matrix would not
by itself prove every row above. Avoid an unbounded requirement to understand
all MakerNotes or all future platforms. Scope unsupported capabilities honestly.

## Evidence entry points

- [Current source audit](sol-current-acceptance-bindings-20261019-v1.json) and
  [actual audit owner](../tests/qualification/sol-current-acceptance-audit-owner-20261019.json).
- [Current build/CPU controls](../tests/qualification/endpoint-cpu-budget-actual-20261018.json),
  [renewed Runtime compositions](../tests/qualification/cpu-ceiling-dependent-composition-actual-20261018.json).
- [SDE](../tests/qualification/current-sde-conformance-actual-20261018.json),
  [ranges](../tests/qualification/current-range-components-actual-20261018.json),
  [XMP](../tests/qualification/current-xmp-kernel-observation-actual-20261018.json),
  [reconciliation](../tests/qualification/current-dng-reconciliation-actual-20261018.json).
- [V6 actual adoption](../tests/qualification/sol-stream-v6-actual-adoption-20261018.json).
- [Mixed current Adobe](../tests/qualification/current-mixed-adobe-actual-20261018.json),
  [full receiving](../tests/qualification/current-sdk-multifile-actual-20261018.json),
  [all-scanned](../tests/qualification/current-all-scanned-adobe-actual-20261018.json).
- [Ten-cohort report](auto-cohort-all10-report-20261018.md),
  [first128 checkpoint](larger128-stock1-checkpoint-20261019.md),
  [larger source plans](auto-cohort-larger-plan-20261019.md).


### Final extended-profile pair renewed,2026-10-19

Actual owning88003/d7e7af/exit0/no session renewed full stock/Ox parser matrix:
1253fixedcases/6288assertions each, allthree designated negative mutations and
four sparse inspector cases each. Twenty nested compiler/metadata/test children
and both runners genuinely reaped with expected exits/group closure; raw logs
and manifests independently hash-bound. Store/Unison8/EXglobal closed.
[Actual receipt](../tests/qualification/final-extended-profile-pair-actual-20261019.json).
This closes the renewed extended-profile execution gap in the older map; it does
not prove arbitrary malformed files, decoded pixels, SDK, transport or the whole
goal. Later component/private forest coverage remains separately scoped.


### Current inherited rsync/native publication qualification

Actual42166/f5665c/exit0/no session qualifies normal/growth/shrink/inherited/
adopt-close/disarm-close/progress-close/progress-cancel on both current stock/Ox
builds.20nestedcompiler/probe calls+runner reaped0/groupsabsent,466linkedartifact
pins and339source/support pins rehashed. Store/Unison8/EXglobalclosed.
[Actual receipt](../tests/qualification/final-rsync-publication-actual-20261019.json).
Actual codec and receiver callback use in-process delivery; not an external
transport claim. Injected unknown native owners/reservations remain retained
until test process exit; process closure does not relabel normal object teardown.
Predecessorv3 refused compiler symlinks beforechild and was independently
recoveryclosed137; preserve that failure separately from this freshv4 pass.

### Many-small actual functional scope,2026-10-19

[Actual1024-file adoption](../tests/qualification/final-many-small-functional-adoption-actual-20261019.json)
records3exact CLI/nine normal peer reaps,1024SDEupdates/524288returned logical
writebytes over32MiBgeneratedtarget and unchangedno-opidentity. Runtimeowner
recovery137 and successfulsaved-evidence offline audit0 are distinct. Not a
repeated/timed/corpus/physical-write claim; new/mixed/repeated workloads remain.

### New/mixed many-file normal owners,2026-10-19

[New-files](../tests/qualification/final-generated-new-files-actual-20261019.json)
and [mixed](../tests/qualification/final-generated-mixed-actual-20261019.json)
now have actual normal owning terminals0, allthreeCLI/ninepeerroles reaped0,
exact1024targethashes/noopidentities and Store/CPU8/EXclosure. Mixed logs show
820SDE+153receiverclones;51additions had no receiverbasis. Singlefunctional
sample per shape, aggregate path counts only, not repeated scaling/quiet timing
or physicalwrites. The prior normalouter-entry gap is closed for these shapes.

### Nonfixed workload functional coverage,2026-10-19

[Seven actualrecipes](../tests/qualification/final-generated-recipes-functional-actual-20261019.json)
close first real receiving coverage for growingXMP, metadata+preview/raw/opaque,
fullreplacement, malformedIFD and unsupported signature. Two2MiBfiles/case,
21CLI/63peerrolesnormal0, oldreaders/exactfreshoutputs/noopidentity and allleases
closed. SDE0/genericreceiverclones2 percase as expected; no photographic validity,
repeated/timed/topology/physicalwrite claim. Fullchange's zero inherited bytes and
full logical model are retained as negative optimization evidence.


### Measured many-small worker1 cohort

[Actual receipt](../tests/qualification/final-many-small-measured-worker1-actual-20261019.json) and [report](final-many-small-worker1-measurements-v2-20261019.md): 36 normal closed owners/108 CLI,6warm+30measured. All targets and no-op fences verified before generated cleanup; retained raw peer evidence re-audited. Ordinary faster in this dataset; clone/SDE reduce modeled logical writes. No physical-write/cold-cache/quiet/scaling claim. Worker3 and other prescribed shapes/topologies remain incomplete.
