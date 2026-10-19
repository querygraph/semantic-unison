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
| 2 Coverage | Current component/worker source bindings, XMP kernel/observation, opaque exact-layout predecessor receiving and conservative refusal contracts. | Named parser mapping is now in final-parser-case-map-20261019.md: both byte orders/classic+BigTIFF,33wire cases,936protected edits and247refusals/compiler. Complete later component/private-field mapping separately. Unknown private meanings remain opaque and are NOT a deployment blocker. No universal camera/pixel claim. |
| 3 Malformed input | Fixed current SDE malformed/binding vectors, constrained range cases and bounded parser ownership controls are retained. | Named parser inventory binds cycles/aliases/count/offset/overflow to actual command/PASS logs. Named XML/truncation boundaries now map to458fixed observation checks/compiler in final-xmp-policy-case-map-20261019.md; arbitrary malformed inputs and full process memory remain outside that proof. User excludes new fuzz/sanitizer campaigns; do not invent a missing campaign or universal malformed-input proof. |
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
planning estimate, not a hard duration or continuous quiet grant. Independent Unison work continues under standing8/8+2 and the canonical
EXglobal barrier. No Photo scheduling hold is active after the explicit drain;
Adobe runtime qualification is deferred to the final phase by user steering.
New18conditionalfda6288a is NOT ACTIVE. Main stays Photo-exclusive.

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


### Current native cross-volume and non-APFS fallback renewed

[Directed twelve-case result](final-private-volume-result-20261019.md) and [actual receipt](../tests/qualification/final-private-volume-v3-actual-20261019.json) bind current stock/Ox binaries to both APFS/HFS+ directions, generic clone auto/off and DNG semantic cloning/fallback. Actual19831/bb1af5/0; all42childgroups closed, image normally detached, independent604d3a/0 audit rehashed36MiB of surviving APFS data and all source/artifact bindings. This closes the actual distinct-logical-volume/non-APFS functional gap, not the prescribed repeated topology benchmark or independent physical-device/sparse/property/network scope. V1/V2 harness failures and recovery137 are explicitly preserved.


### Current native stage property/ABI/sparse binding renewed

[Result](final-native-stage-result-20261019.md) and [actual receipt](../tests/qualification/final-native-stage-v2-actual-20261019.json): both current production native objects,50actual compiler/native/metadata children,46zero+4expected77; owning5267/cfd95f/0/no session. Read-only/snapshot live-mutation isolation, xattr/fork/ACL stripping, FIFO/flags/refusal/error phases/exclusivity/descriptor counts and real sparse1MiB snapshots passed. Independent2a4ba1/0 rehashed2146342B and all source/object/toolchain/command bindings; whole8EXclosed. Earlier sparse-generator prerequisite failure/recovery137 and negative creation methods preserved. This closes native-stage binding, not every end-to-end sync property/compressed/platform/crash case.


### Current default-startup genuine-upstream interoperability

[Actual result](final-default-upstream-result-20261019.md) and [receipt](../tests/qualification/final-default-upstream-peer-actual-20261019.json): current stock/Ox both client/server orientations versus unmodified8772;12calls/36primaryroles normalclosed, exact replicas/source fences/no-op8fields. Owning9111/c2e1e7/0/no session; independent07dc8d/0 raw/pin/shim/FD audit+65536Bfreshpayloadhashes/whole8EXclosed. This renews current default-startup interop, not forcedRPC0/installedoldrelease/archive-roundtrip/actualSSH/performance/semantic or SDK qualification.

### Current installed-old-peer archive round trip

[Actual result](final-archive-roundtrip-result-20261019.md): stock/Ox each ten stages through byte-pinned installed2.53.5, owning29608/8c45ae/0,18zero+2normal designated missing-base exit2,20pairs/60primaryroles closed. Same state/archive roots, old load/update, exact edited variants preserved, explicit known-common restoration and later disjoint merge/noop pass. Independent9841ff/0 re-audited allrawpairs/534source+329production pins/FDidentities/archive records+262144Bfreshfinalreplicas; entire8EX reacquiredclosed. Plan descriptive-field discrepancy and first metadata-audit137 recovery preserved in report, no native replay. RPCv0 is outside the approved scope; realSSH/otherplatform/SDK remain separate.

### Supported-peer scope resolved by explicit user decision

The user explicitly chose upstream’s supported-peer range and dropped the obsolete RPCv0 requirement on2026-10-19. No legacy transport restoration is planned. [Current boundary](final-rpc-version-result-20261019.md) remains actual accept1/refuse0/999 evidence, not v0 fallback. Genuine8772 default interop and installed2.53.5 archive roundtrip remain the tested RPC1 scope; other supported releases are not automatically qualified. Prior mismatch evidence is preserved in the result report. This resolves the product-scope blocker without changing production code.

### Current saved-profile/backup/metadata sync properties

[Actual result](final-sync-properties-result-20261019.md): stock/Ox eachseed/update/noop,28308/7b837c/0,6pairs/18primaryroles normallyclosed. Namedprofiles honorignore/localversionedbackup/symlink; generatedDNG+binary remove selectedxattr/nonemptyfork/mode640→400, exacttimestamps, heldoldreaders preserved; nooptarget8fields andbackupsunchanged. Independent455c91/0 reaudited538source329production/rawpairs/9canonicalbindings+786432Bfreshcurrent/backupbytes+nativeattributes; full8EX reacquiredclosed. V1preentry1/V2fixturefailure+137recovery separatelypreserved/no originalproxywait4 claim. Not allACL/compressed/crash/platform/fullgoalproof.

### Final SDK fixture readiness source successor

[Source readiness](sdk-generated-fixture-readiness-successor-20261019.md): official SDK2768 source archive persistently fetched97807/a2bf20/0 (80509918B/SHA c1d3a545...), distinct ancestry from2724. Source index/license/readme observatione27c2f/0; zero extraction/build/SDK calls. Independent1eb9cb/0 stablearchiveepoch+unchangedqualified2724validator/full8EXclosed. Exact persistent codec/state metadata path policy controls7cdd5e/0 pass; no arbitrary root or payload grant. Existing uncompressed/JPEG bases preserved; JXL/12scalarstates/native finalmerge remain incomplete. Metadata search caps/scopes explicitly retained, not global absence evidence.

### SDK source release identity corrected

[Builder source fix](sdk-current-release-identity-fix-20261019.md): new2768README contains2724history, exposing old substringguard’s falseacceptance. Builder now requires exact firstcurrent2724release; six actualcontrolsa1f0de/0 include actualpreflight2768refusal beforebuildmkdir. OfficialsavedREADME9b2536/0 confirms2768current/2724refused. No SDK/compiler run or validatorreplacement; safeextraction/versioned2768fixture-writerbuild remain pending.

### SDK2768 complete private source extracted

[Source extraction](sdk2768-private-source-unpack-20261019.md): actual7403/0feceb/0, pinned OSunzip46216reaped0/groupabsent,3769files/133855079B and exact bounded ZIPcensus. Independentd725da/0 rereadallsourcehashes/nativeproof/supportpins/canonical9; requiredSDK/XMP/JXLbuildinputs exist, old2724validatorunchanged, full8EXclosed. Sixcontrols a22bdd/0; first fabricatedCRCfixturefailure/recovery137 retained separately. ZERO SDK/compiler/fixture executions. Separate2768fixture-writer-only build and final12states/SDKmatrix remain.

### Separate SDK2768 fixture writer actually built

[Build-only result](sdk2768-fixture-writer-build-20261019.md): owner53680/1939df/0, builder48807 normallyreaped/groupabsent. Newfixture-only path excludesvalidator, binary3a5c9f98/manifest55c2f1d7;233linkedartifacts/226cacheunits/225officialSDK-XMP+onewriter. Independent52950/40a018/0 rechecked1732uniqueheaders+full3769SDKsources/toolpins/artifacts and old2724validator; whole8EXclosed. Tenoriginalcontrolspass0bb271/0, initialfixture-onlytesterrors preserved/normalclosed. Original8GiB estimate understated: modeledcompilerhash lowerbound122959389696B, not physicalIO/measurement/cap. ZERO writer/validator executions; actualJXL/12states/native finalmatrix stillpending.

### Current DNG component/private partition and archive-reference faults renewed

[Actual result](final-dng-component-result-20261019.md) and [receipt](../tests/qualification/final-dng-component-actual-20261019.json): owner38297/b5ca6f/0/no session,76nestedchildren normally reaped/groupsabsent (72zero+4specificnegative2). Each compiler1590component+49layout+8private-refusal checks,29owner-index publication-fault checks; actual schema1/2 inspector reports bound to generated bytes. Both named-record guard ablations failed for the expected reason in private filtered copies, restored afterward; no production fault switch. Independentcbcdaf/0 rehashed565plan/329production pins, eight executables and115712Bgeneratedfixtures, raw PID/group proofs and exact9canonicalidentities; full8EXclosed. This renews component/private-layout and archive-reference primitive evidence, not full receiving/archive-crash/physicalENOSPC/SDK/pixels.

### Current end-to-end clone interruption and recovery renewed

[Actual result](final-clone-interruption-result-20261019.md) and [receipt](../tests/qualification/final-clone-interruption-v3-actual-20261019.json): actual61494/84393d/0/no session;8calls24primaryroles across current stock/Ox, two controlled still-owned serverSIGKILLs only after observed private clone stages. Exact old live destination/open-reader/hardlink preserved, fresh clone recovery gives exact8MiB target on a different inode from partial stage, cleanup and full-identity no-op pass. Independentc160ba/0 reparsed every peer/frame/command,542source329production pins and37748736Bfreshgeneratedbytes; canonical9/full8EX reacquiredclosed. V1hardlink-reader andV2wrong-log-channel harness failures/known-prefix idle-controller137recoveries preserved separately. Not power-loss/all generic clone cases/SDK/photos.

### Current generic clone update and flagged-basis policies renewed

[Actual result](final-clone-sync-result-20261019.md) and [receipt](../tests/qualification/final-clone-sync-actual-20261019.json): owning43369/a6d4ef/0/no session,14cases/compiler/28CLI84primaryroles+4flagmodifier children allsettled. Original sameoffset/prefixinsert-delete/shiftduplicate/literal/shorter-longerEOF each actualreceiverclone/exactbytes; oldhardlink/openreader preserved, cloneoff exact, require-nodump specificnormalrefusal2 witholdtargetpreserved, plannedauto-fallback exact, noops/stagingcleanup pass. Sameoffsetreported2095104logicalbytes preserved, allliteral0, not physicalwrites. Independent2ec05e/0 rehashed545sources329production/13002912Bfreshgeneratedbytes/rawpeer+modifierbindings, exactcanonical9/full8EXclosed. Legacy unmanaged driver not rerun; capability-cache/races/physicalcrash remain separate.

### Current native publication, lease and restored-mtime guards renewed

[Result](final-native-publication-result-20261019.md) and [actual case inventory](final-native-publication-case-inventory-20261019.json): owner74637/dd4390/0/no session, 78 children (74zero+4specific negative2), each compiler177 publication/producer cases in ordinary and timed modes plus21 native CloneLease cases. Independent748b45/0 bound556 source pins/329 production,184 generated artifacts, exact private guard ablations and canonical9/full8EX closure. New exact native-mtime regression53737/fd27be/0: candidate and target same-size mutations with restored mtime/changed ctime refused on both compilers; two private guard-disabled controls fail as expected,12 children all settled. Independentb3f93e/0 bound559 sources/object lineage/native-time tuples and whole8EX closure. No SDK/photos; native primitive scope, not an uncooperative check-to-rename race cure or physical crash durability.

### Photo availability correction — current scheduling policy

The user explicitly requires Photo to remain available for its own work and
Capitola. The earlier blanket Unison drain/handover hold is released, queue
`01a154b6-1a28-7e10-80d3-6913b972dc5d`. Source preparation, CPU-only tests,
audits and report sealing must not hold Photo. Coordinate shared IO/Adobe access
only for a concrete operation ready for immediate dispatch; release after actual
terminal and resource settlement, without an automatic successor. Standing8/8
remains. This changes scheduling, not functional qualification or permissions to
open Photo originals/Main/catalog/cache.

### Capability-cache interpretation and worker-state successor

Source review of `doc/filesystem-capabilities-plan.md` explicitly preserves the
absence of a reusable process-wide capability cache. SOL11's stale capability
hazard is therefore addressed by per-call authoritative kernel results and
fresh CloneLease/owner observations; a successful clone cannot authorize a later
operation, and a per-file refusal must not poison a volume. Actual21 native
lease cases/compiler in the final native-publication receipt cover their named
owner/observation invalidations. They do not prove real mount-incarnation or
unmount/remount behavior. A future reusable cache needs separately qualified
mount-generation bindings; adding a cache just to satisfy a test label would
increase risk and is not planned.

[Worker follow-up](worker-state-followup-20261019.md) freezes a fourteen-call,
both-compiler component/late-delivery/same-size-restored-mtime successor. Eight
current owner controls passed actual0f1e3d/0, CPU00 closed; native execution is
UNSTARTED. No additional worker/parity/race success is claimed from preparation,
and no Photo/Capitola hold exists. Existing broad benchmark and final Adobe
receiving gaps remain open independently.

### Existing parser case inventory now source-bound

[Named map](final-parser-case-map-20261019.md) and
[inventory](final-parser-case-inventory-20261019.json) join all1253cases/compiler
(33inspect+33golden+936opaque+247reject+4sparse) to existing actual88003/d7e7af/0,
6288assertions/compiler, both exact CASE/PASS logs and20nested child settlements.
Metadata-only audit e9c8f2/0, child71201 reaped0/groupabsent/CPU00closed. Initial
fd400b/1 pin refusal preserved; exact historical40809783→currentb4491baf helper
difference is only four timestamp/wait4-usage observations, reverse-hash checked
against both saved snapshots. Parser/fixture/kernel source matches current;
current helper was NOT retroactively used. No new native/SDK/payload/EXIO or
Photo hold; remaining XML/merge/receiving cases stay independently open.

### Public fork identity — user-directed rename

GitHub repository1417214876 was renamed from querygraph/unison to
[querygraph/semantic-unison](https://github.com/querygraph/semantic-unison), still
PUBLIC and a fork of bcpierce00/unison. Actual rename79a30d/0 and independent
readbackdfb9cf/0 preserve repository ID and OPEN DRAFT PR13 (master ←
integration/sol-consolidated-review). The shared local `fork` URL and default
push remote now name semantic-unison; `origin` remains original upstream.
No code push, merge or upstream submission occurred. Historical old-name
receipts remain unchanged. The user-requested
[I-AM-AN-HONEST-WORKING-LLM.md](../I-AM-AN-HONEST-WORKING-LLM.md) states this fork's
AI-assisted approach, credits upstream, respects its contribution boundary,
and distinguishes tested scopes from unfinished qualification.

### Worker late-delivery and exact restored-mtime source mutation closed

[CPU-only actual](final-worker-state-cpu-result-20261019.md): owner88752/cde84c/0,
all14serial children genuinelyreaped/groupsabsent, stock/Ox each126component
checks+explicitqueued-completion success/cancel/shutdown+active same-size source
mutation with exact native mtime restored refused. Independent70570/e8f0ef/0
checked564sources329production/638artifacts/eightprograms/raw14calls and fresh
exactCPU8reacquire/close. NoEX acquired or IO-exclusion claim; routine compiler/
tinyfixture work required no Capitola yield. OriginalEXplancc71c911 stays
UNSTARTED, scheduling request withdrawn. This closes those named unit cases in
SOL5/9; full receiving/path races/SDK/wholematrix limits remain separate.

### Scalar merge and fixed XML requirements source-bound

[Policy map](final-xmp-policy-case-map-20261019.md) binds actual65831/c277e0/0
stock/Ox kernel/observation results to17unchanged source pins, eight metadata
artifacts and exact kernel executable/log/compiled-test bindings. New metadata
actual9cb39c/0 closedCPU00/noEX/no native rerun. Explicit25scalar+343rating
truth/symmetry+4RDFconflict cases and458fixedXML checks/compiler map identical,
disjoint/divergent/delete/RDF/qualifier/rendering/opaque/determinism and named
DTD/entity/truncation/count/depth/size boundaries. No new fuzz, wholeRSS,
container/base recovery or final SDK receiving convergence claim. Those latter
scopes stay open; the packet API alone cannot prove them.
