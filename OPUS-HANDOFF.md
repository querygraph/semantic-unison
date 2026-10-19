<!-- CURRENT-UNISON-CHECKPOINT -->
# Current checkpoint — larger workload qualification

Updated UTC 2026-10-19T06:30:19.422171+00:00. Goal ACTIVE and incomplete.

- Active source worktree `/Users/alexy/src/unison-final-adobe-20261019`, branch
  `implementation/final-adobe-qualification` (local SDK-merge source successor).
  The benchmark worktree `/Users/alexy/src/unison-cpu-ceiling-20261018` stays frozen
  for remaining plans; runtime-harness source63fd4c8a, draft review headf6bfd653.
  Production remains `971271a8`; subsequent work is Python test tooling/evidence.
- **No live owned jobs or resource descriptors.** Latest larger128stock1:
  actual52223/3c264e/0/no session, worker97794reaped0/groupempty/CPU8EXclosed.
 18rows54CLI passed. See `doc/larger128-stock1-checkpoint-20261019.md`.
  No replay of consumedc08b51ff;29otherlargercohorts remainunstarted.
- Completed: ten32MiB worker cohorts,180rows540CLI, actualparent/group/FDclosure;
  combined report `doc/auto-cohort-all10-report-20261018.md`.
  Temporary18 ended, standing8Unison/8Photo/2system restored.
- Current Adobe qualification: mixed probes15556/682f67/0; full receiving
  67541/5343fe/0 (2CLI/4SDK); all-scanned45243/e035b2/0 (4CLI/4SDK).
  All actually CLOSED/resources released. Generated inputs only. Raw digests
  valid/decodeSUCCESS/errors0, fourpaddingwarnings retained per SDK call.
- Larger source successor passed46controls; three frozen size indexes under
  `doc/auto-cohort-qualification-larger-{128,512,2048}-v1-20261019`.
  Series82ee83dc covers30plannedcohorts; first128stock1 completed;29 remain unstarted.
  No new18 grant. Conditional `fda6288a` is NOT ACTIVE/admission; activation
  requires all12 shared8 actual closures, PhotoCPU drain and a new ACTIVE record.
- Photo IO/native remains unstarted by user Photo-at-end steering; CPU8 source
  work may continue. Main remains Photo-exclusive. No SDK/Photo job live here.
- First128 actualclosure reached the runtime-estimate review checkpoint. Further
  payload/SDK starts await the operator schedulingreview raisedbyPhoto; source
  work continues. Preliminary
  full30 byte-scaling estimate18–30h (~23h central), not a runtime guarantee or
  continuousquiet grant. Preserve scope/samples; review schedule before blindly
  starting later work. No new fuzz/sanitizer campaigns.
- Remaining: final receiving-path/policy/merge evidence binding, larger and other
  prescribed workload/topology comparisons, explicit platform/resource limits,
  final source/review delivery, then any Photo workflow verification at the end.
  Unknown MakerNotes remain opaque, not a deployment blocker. No production
  activation/upstream submission or PR13 merge authority inferred.

Older checkpoints below are historical; use this checkpoint and actual receipts.
<!-- END-CURRENT-UNISON-CHECKPOINT -->

# Unison implementation handoff


## Consolidated review candidate — latest 2026-10-17

Checkout /Users/alexy/src/unison-sol-review-20261017, branch
integration/sol-consolidated-review, combines all current feature/cache/report,
producer auditor, integration regressions and qualified component-source owner
fix. No GitHub PR merged. Production source initially matched sourceecad82f3; the qualified cold-start
follow-up below subsequently changes Update only.
new merges reconcile navigation and original regression harnesses only. This
section supersedes earlier scattered branch-current statements below; historical
raw/sealed receipts remain unchanged.

Frozen IO-request candidate remains separately at
/Users/alexy/src/unison-sol-integration-20261017 with exact requeste60975f3,
queue01a14991-ce52, admission path
/private/tmp/unison-sol-properties-admission-86df187d7c95.json. Do not substitute
this newer checkout/binary into that request or dispatch without a fresh grant.
No owned job/resource is active. Remaining runtime acceptance needs new IO
coordination; incomplete private fields are not a deployment gate. No full-goal
completion/production activation/benchmark/camera/SDK claim follows from merge.


## Current integration candidate — 2026-10-17

This local branch combines managed-cache/local-report source6b4d5204 (PR11) and
independent RPC auditor sourcea3725eb5/current5f350db6 (PR10). No GitHub PR is
merged, no old run/admission is replayed, no original sealed receipt rewritten.
The code merged without conflicts; only these navigation documents required
combining parallel history. Later paragraphs saying store/namespace/UI are
pending are historical; local opt-in report cache is implemented and qualified
on its exact branch. Remote cache routing remains absent. Candidate validation
is still required before making any combined-source qualification claim.

Current zero owned jobs/resources. Standing8/8 applies. Next inspect required
SOL acceptance against current integrated code/evidence, then run appropriate
current-source checks. No runtime/media/SDK/transport admission is created.

## Latest namespace successor — 2026-10-17

Source ed67f0eb is pushed as draft PR9:
https://github.com/querygraph/unison/pull/9 (base PR8), no merge authorized.

Branch `feat/component-cache-namespace`, sibling worktree
`/Users/alexy/src/unison-component-namespace-20261017`, based on PR8, adds one-use
macOS component-cache-v0 directory provision/open. Fresh refuses EEXIST; reopen
requires trusted device/inode. Actual mkdir survives later sync failure with no
rollback/retry. Scoped synchronous callback rechecks parent/name/FD, closes once
and propagates the same uncertainty carrier; nested failures retain known manifest
and namespace FDs plus all borrowed directories. No production namespace installed.

Current stock/Ox Make/fullselftests/Dune/1272SRCchecks PASS,67namespace+9real-native/
80loader+7real-native checks/compiler plus existing component/DNG/126worker/archive
suites; exact receipt component-cache-namespace-actual-20261017.json and contract
doc/component-cache-namespace.md. All nine workers/groups/token sets closed.
First actual61854/d0ad68/1 intentionally stopped after five passed steps because a
fresh Root RPC grant appeared; after actual RPC closure,18854/f0c867/0 finished
only four unstarted steps. No test replay or competing build during that RPC.

IMPORTANT main RPC admission53a52254 was consumed ONCE meanwhile: actual owner
91491/7ec39a/exit1/no session; all8probe commands0, final auditor KeyError(cancel_reason).
Main frozen342sources remain unchanged; independent Root resource-failure closure
adoption f01c0b94 explicitly released Photo scheduling hold. Main's outside-frozen
saved-only auditor verifies exact producer schemas/8ledgers/expected fixture hashes
in memory/current lstat without payload rehash, original exit1/result preserved;
its separate functional adoption is not inferred. See main OPUS and
doc/component-remote-actual-saved-audit.md there. No replay or old-grant reuse.

Next cache work: durable namespace identity binding, quota-admitted stage creation
and capture/adoption/report routing. This optional cache integration does not make
incomplete MakerNotes a deployment gate. No new media/SDK/transport authorization.

## Latest managed-loader successor — 2026-10-17

Source commit `3d35cf81` is pushed as draft PR8:
https://github.com/querygraph/unison/pull/8 (base PR7). No merge authorized.

Branch `feat/component-cache-loader`, worktree
`/Users/alexy/src/unison-component-loader-20261017`, stacked on PR7, adds strict
macOS digest-leaf metadata opening/authentication/normal-close and retained
uncertainty in DngComponents. `Update.load_component_owner_index` takes trust
from the loaded archive hint; off/missing hints touch no directory. Matching
UIX/UDI and UCR metadata is fully authenticated and loader-owned FDs retire
before successful return. Nested close errors retain known manifest FDs;
original failure and all uncertain identities survive, without numeric retry.
Last-known identity survives a failed final stat. Directory remains borrowed.

Actual parent35813/42bf8f/0/no session: current stock/Ox Make/fullselftests/Dune,
1272SRCchecks,80loader+7unmodified-native checks/compiler, existing56component/
1005checkpoint/27publicationfault/13readerfault/1391DNG/29archivefault/126worker
controls and14archive-probe calls (2compiles+12runtime phases) PASS; all nine workers/groups/
tokens closed. Earlier failed fixture exception expectation and missing owner-only
Ox API annotation preserved, corrected before current evidence. An earlier full
pass predates the final identity-retention fix and is not the current source proof.
See tests/qualification/component-cache-loader-actual-20261017.json and
doc/component-cache-loader.md.

No source-photo/SDK/Adobe/transport or production namespace/write was invoked.
No bootstrap directory, automatic capture/adoption or normal report-path routing
is implemented yet. This is an isolated successor, not a main merge or new IO
admission. Main's342RPC closure remains frozen; latest Root defer was independently
read, no admission/workspace exists at last check, and no current Photo liveness
is inferred from that historical defer receipt.

Latest checkpoint: opt-in all-scanned validation implemented; current stock/Ox Make+Dune and local scan-RPC/fake-driver controls PASS/CLOSED.

<!-- Parallel historical checkpoint retained from RPC auditor branch. -->
## Latest future RPC auditor source — 2026-10-17

Source a3725eb5 is pushed as draft PR10:
https://github.com/querygraph/unison/pull/10, base feat/semantic-dng-oxcaml.
No merge or future transport execution authorized.

Branch feat/component-rpc-producer-audit, worktree
/Users/alexy/src/unison-component-rpc-audit-20261017, based on main a2ddb287,
fixes the actual final-auditor field mismatch for future runs. New independently
pinned producer_schema.py validates REAL separate client/supervisor shapes and
server wait/cancel/pump proof; audit.functional retains raw binding and fresh
synthetic-file SHA readback. Runtime inventory343 here; originalmain342 remains
unchanged, and historicalplan/admission are not repinned/reused.

22coordinator+8readback+6saved control groups PASS, actual batch93347/15fd98/0 and
finalcoordinator9b669b/0/no sessions/allgroupsCPUclosed. Full simulated worker passes
real-shaped receipts; restoring the original lookup reproduces exit1/KeyError.
Current producer AST field extraction, eight historical metadata projections,
mandatory-helper source pin and existing failedprefix/unknown controls qualify
this source fix. All318C/OCaml production files unchanged; no rebuild/liveRPC/
SDK/media/EXIO/new runtime plan or admission. Exact evidence:
tests/qualification/component-rpc-producer-audit-source-actual-20261017.json and
doc/component-rpc-producer-audit-successor.md.

Main consumedV1 and its originalfailedbytes/sealedreferences remain untouched.
Root already separately adopted all8saved functional cases, originalexit1 and
zero new payload reads/replay; f3bc1d0f adoption is reconciled in main. Any current
pending/awaiting message below is historical. No new runtime is required merely
to correct that old report and no successor dispatch is inferred.

## Current actual RPC and namespace state — 2026-10-17

RPC V1 admission53a52254 is CONSUMED, not awaiting dispatch. Actual owner tool
91491/7ec39a/exit1/NOsession, coordinator62256/worker62257: all8probe commands0,
raw8client/supervisor/server/pump settlements pass, workerreaped1/othersabsent,
CPU8+EXIOclosed. Final auditor failed KeyError(cancel_reason): original fabricated
controls added that field but actual client/supervisor producers omit it. Original
WORKER-RESULT completeFALSE/exit1 and OWNER-RETURN088ef9fb remain unchanged.
Independent Root adoption f01c0b94 reparsed8prefixes, freshly reacquired EXIO/Photo8
and explicitly RELEASED scheduling hold. No replay/new grant is authorized.

Saved-only auditor outside frozen342 closure (tests/component_remote/saved_*)
now checks exact producer schemas,8rawledgers/reports/in-run beforeafter hashes,
expected fixture hashes computed IN MEMORY and current16lstat fences. It does NOT
open/re-hash generated payload or turn original ownerexit1 into0. Actual metadata
outputaudit e27a2d/0; six original control groups/13negative-schema variants actual
90276/474f52/0, bothcontainedgroups/CPUclosed. Savedresult d6d94f4c is separate
source-bound functional evidence. Root has now separately adopted all8saved
cases in UNISON-COMPONENT-RPC-V1-SAVED-RECEIPT-FUNCTIONAL-ADOPTION-20261017.json,
with342pins and0payload reads/replay/newadmission. Exact local reconciliation:
tests/qualification/component-remote-root-saved-functional-adoption-20261017.json.
This preserves original exit1 and does not claim a new independent payload hash. See doc/component-remote-actual-saved-audit.md and qualifications
component-remote-actual-saved-audit-20261017.json plus root-closure-adoption.
Main frozen342runtime sources/request/plan remain byte-identical; old slot never
runs again. Next audit tooling fix must be versioned, preserve the original run
and qualify REAL producer schemas, not require a new native run merely for a
reporting correction.
Sealed return: doc/component-remote-return-20261017.json,9590B
SHA2ce13be049b9ede3fab46015d1f1d865145e10d8806c40d34cffc457879f7098.
PR2's description now distinguishes original exit1 from saved-only evidence.

Latest namespace source ed67f0eb is draft PR9
https://github.com/querygraph/unison/pull/9, branch feat/component-cache-namespace,
worktree /Users/alexy/src/unison-component-namespace-20261017, based on PR8.
One-use fixed-child mkdir or trusted dev/inode reopen; retained mkdir effects,
scoped close and nested known/uncertain/all-borrowed directory evidence. Current
stock/Ox Make/fullselftests/Dune/1272SRCchecks,67namespace+9unmodified-native/
80loader+7unmodified-native checks/compiler plus existing suites PASS. Controller
61854/d0ad68/1 stopped safely before next job on fresh RPC admission after5passed
steps; after actualRPCclosed,18854/f0c867/0 completed only4unstartedsteps. All9
workers/groups/token setsclosed. See that branch's component-cache-namespace-
actual-20261017.json and doc/component-cache-namespace.md. No production namespace,
photos/SDK/transport or automatic cache activation. Durable namespace identity
binding and capture/adoption/report routing remain optional cache follow-ons,
not private-field-completeness deployment gates. No merges authorized.

Previous loader successor: `3d35cf81`, draft PR8
https://github.com/querygraph/unison/pull/8, branch `feat/component-cache-loader`,
worktree `/Users/alexy/src/unison-component-loader-20261017`, stacked on PR7.
Strict macOS UIX/UDI/UCR digest-leaf reads now use the actual loaded archive hint
through Update.load_component_owner_index. Borrowed directory, no discovery or
creation; owned leaf FDs close once, with original failure/last-known identity/
known ancestor retention on close uncertainty and no numeric retry/finalizer.
Current stock/Ox Make/fullselftests/Dune and1272SRCchecks passed; percompiler
80loader+7unmodified-native checks and existing component/DNG/126worker suites;
14archive-probe calls (2compiles+12runtime phases). Actual35813/42bf8f/0/no session,
all nine contained workers/groups/tokens closed. Earlier failed fixture exception
expectation and missing Ox owner-only annotation and pre-identity-fix pass are
preserved; current proof uses final002 builds/controls. See that worktree's
component-cache-loader-actual-20261017.json and doc/component-cache-loader.md.
No namespace bootstrap, automatic capture/adoption/normal report routing or
media/SDK/transport/production/power-loss qualification. Main runtime342RPC pins
remain unchanged; that pending RPC slot has since been consumed and closed as
recorded above. Do not reuse its admission or act on historical readiness.

Previous worker successor: `5537ec16`, draft PR7
https://github.com/querygraph/unison/pull/7, branch
`feat/component-owned-worker-refresh`, worktree
`/Users/alexy/src/unison-component-owned-worker-20261017` (stacked on PR6).
Worker refresh now authenticates the retained record against the trusted owner
entry and derives its decoder inventory there. Stock/Ox Make/fullselftests and
116 worker checks/compiler passed, actual67532/754d9e/0/no session; all contained
groups/tokens closed. See that worktree's qualification receipt and handoff.
Subsequent indexed routing also passed current stock/Ox Make/fullselftests/Dune
and126workerchecks/compiler,1272current source checks, actual19704/4509e5/0/no
session; all five contained workers/groups/tokens closed. Exact owner/path/
generation miss or stale entry freshly extracts; a hit authenticates and
refreshes; missing selected record errors and foreign/corrupt records fail
without silent fallback. Changed-input/cancellation controls pass. See
component-indexed-worker-refresh-actual-20261017.json and
doc/component-worker-cache-routing.md in that successor. No media/SDK/transport
or automatic managed namespace selection/normal scan installation claimed.
This remains separate from main's frozen RPC source/admission closure.

User design clarification, 2026-10-17: SOL.md now explicitly separates release
qualification from later field refinement. Qualified pixel/metadata separation
may ship with exact opaque preservation; incomplete small-field mapping is not
a global deployment gate. Immutable decoder/policy revisions compose across
independent components, read only affected regions when input bindings permit,
and recompute dependent roots while retaining old views. Interpretation alone
does not prove stability or authorize hash exclusions. Automatic routing remains
an implementation follow-on; this documentation change authorizes no deployment.

Historical checkpoint: opt-in all-scanned validation implemented; current stock/Ox Make+Dune and local scan-RPC/fake-driver controls PASS/CLOSED.
Older checkpoints below retain their original scopes and pending-state history.
Implementation HEAD before the initial handoff:
`50da86f34fef8b407689d63c4fd021d2bb9e1438`.

## Read this first

Retained old-production-code archive compatibility now PASS/CLOSED on PR6:
actual12014/2441f7/0,13directcalls with currentstock/Ox producers and pre-component-
RPC stock5.2.0 Update/Proplist/nativeobjects from pinnedreceiptf24467a3. Old code
has no newhintregistration/API. Old read preserves exactarchivebytes, rewrite
removes hint; currentcoldreload givescachemiss with immutableUIXpayloadunchanged.
Allgroups/tokensclosed; oldsource/objects/originalCLI hash unchanged. The original
CLI was NOT invoked; no network/fullsync/data-bearingroots/SDK/photos. Test-only
successor; current productionSRC1272pins rebound to priorfourbuilds, not rebuilt.
`tests/qualification/component-archive-legacy-actual-20261017.json`. No automatic
capture/reuse, managednamespace or broad old-version compatibility is implied.

Draft PR6 https://github.com/querygraph/unison/pull/6 is stacked on PR5,
`feat/component-archive-hints` against `feat/component-owner-index`.
Qualified source/evidencef171539b; all owned handles/grants are closed. PR4 and
PR5 remain separate review levels; main frozen342RPC source is unchanged. No
actual old-binary compatibility or automatic cache capture/reuse is claimed.

Archive-hint successor `feat/component-archive-hints` in
`/Users/alexy/src/unison-component-archive-20261017`, based on PR5c372213a, is
qualified. Endpoint-local default-off componentownercache UAX/0 tail afterlegacy
paths; privatekey removed beforelegacypropertyserialization. No format23/version/
feature change. Reference derivation requires normallycompleted publication,
not renameeffectalone; caller settlesFDs before local adoption. Existingarchive
commit persists hint. Missing/malformed/off hints decline without blobdiscovery.
Focused63243/2ab595/0 incl1391DNG+29archivepubfault checks/compiler passed.
StockMake passed in77348/e17590/1; linked001import/002privateUtilsymbol/003missing
maxthreadsPref failedclosed, preserved; test-only fixes, productionunchanged.
Actual stocklinked00458999/8ec8ad/0 and full96641/27b99d/0 PASS/CLOSED. Current
stock/Ox Make/fullselftests/Dunecompile1272SRCpins;56component/1005checkpoint/
27publicationfault/13readerfault/110workerchecks percompiler pass. Both linked
archiveprobes14directcalls/6phases each pass; all8adoptedworkers/groups/tokensclosed.
`tests/qualification/component-archive-hints-actual-20261017.json`, contract
`doc/component-archive-hints.md`. No oldbinary/remote/SDK/media/automaticcapture/
managednamespace/hardwarepowerloss orlegacyclosefault qualification. Main frozen
342RPC untouched/no runtime admission inferred; new source not merged to main.

Manifest storage/publication successor on PR5 qualified. Borrowed-FD UIX write/
read with pre/post-loader stability; owner-only native immutable publication,
one attempt even afterfailedrename, actual-effectgetter. Sourcehelpers open/dup/
close noFDs. Actualfocused56956/e8cf00/0 and full85962/0cfdd3/0 PASS/CLOSED;
initialnativefixture94862/954705/0 preserved, separatefinal negativecompilefiles
qualify cache+manifest contexts. Current56component+1005checkpoint+27publication
fault+13readerfault+1248DNG+110workerchecks/compiler, freshstock/Ox Make/fullselftests/
Dunecompile and1272current sourcepins match. All7observedworkers/groups/tokens
closed. Receipt `tests/qualification/owner-manifest-publication-actual-20261017.json`.
No quota reservation/namespace installation/trusted-state commit/crash-safe pointer/
automaticrouting or actualPhoto/media/SDK/transport. Entry presence and FDsettlement
still owner duties; new native fault scope is underlying unchanged core, not a
separate UIXpostrename injector. Main frozen342RPC unchanged/no runtime grant.

UIX/0 reference-manifest successor on PR5 is qualified. Header80B+32/reference,
max32848B; prior trusted manifestSHA+ownerbinding+exactlimits required before
entry resolution. Each referencedUDI independently digest/canonical/keyorder/
aggregatebudget checked; cancellation and loadererrors propagate without partial
ledger. Existing UDI decoder factored, unchanged UDI wire bytes. Actualfocused
41977/9e212a/0 and full46659/898c87/0 PASS/CLOSED, all7workers/groups/tokensclosed.
Current56component+1005checkpoint+27publicationfault+13readerfault+1234DNG+
110workerchecks/compiler, freshstock/Ox Make/fullselftests/Dunecompile and1272
sourcepins match. DNGcount includes framingvector truncations, not extra cameras.
`tests/qualification/owner-index-manifest-actual-20261017.json`. No filesystem
publication/durability/automaticrouting/archiveauthority, photos, SDK or transport.

Draft PR5 https://github.com/querygraph/unison/pull/5 is stacked on PR4,
`feat/component-owner-index` against `feat/component-cache-input-binding`.
Qualified source/evidence0bfb4c9f; exact current scope and corrected source-rebind
history below. PR4 remains separate/ready, main frozen342RPC untouched. No
owned build/test handles or CPU/IO resources remain; no new runtime admission.

Owner-index successor `feat/component-owner-index` in sibling
`/Users/alexy/src/unison-component-index-20261017` is qualified on PR4 base835df2fc,
leaving PR4 stable/ready. Bounded immutable trusted ledger (1024entries/8MiBencoded
payload pervalue), exactroot/path/currentgeneration selection, pure olddigest
replacement/removal and selected authenticated metadata/fullinput refresh.
No inferred newestgeneration, globalCAS, namespace/persistence/automaticrouting,
archiveadvancement/nativequota refund. Owner serializes adoption/retainedmemory.
Focused14748/ba6934/0 and initialselector48015/b12b44/0 closed. Firstcontroller
23119/d88402/0 had worker001reaped1 on OxMake001 temporarycomment/sourcepin
mismatch; firstseal refused beforewrite/commit. Correctedactual70919/48638c/0,
OxMake002+worker002 PASS/CLOSED. Selectedcurrent stockMake001/OxMake002/bothDune001
1272sourcechecks match. Percompiler56component+1005checkpoint+27publicationfault+
13readerfault+1071DNG+110workerchecks PASS. All7selectedworkers/groups/tokensclosed,
originalfailurepreserved. `tests/qualification/owner-index-actual-20261017.json`.
No SDK/photos/EXIO or RPC; main frozen342 unchanged/no transport grant inferred.

Reader retirement follow-up qualified: read/iter/digest refuse expired readers
BEFORE caller cancellation/iteration code can execute. Focused99430/44f833/0 and
full44086/b80c8b/0 closed. Current56component+1005checkpoint+27publicationfault+
13readerfault+1051DNG+110workerchecks percompiler PASS. Fresh stock/Ox Make+
fullselftests/Dunecompile and1272current sourcepins matched. All7observedworkers,
groups/tokensclosed. Receipt `tests/qualification/reader-retirement-actual-20261017.json`.
PR4 handoff conflict resolved; main reviewed342RPC unchanged/no runtime grant.
No automatic namespace/selection/activation, photos/SDK/transport or merge.

Borrowed positional reader is now qualified: POSIX `with_borrowed_fd` borrows
callerFD without opens/dup/closes or position changes, expires after callback,
bounded64KiB pread with short/EINTR/cancel/EOF/EIO handling. Known-entry tests
borrow record/index readers. Actualfocused4732/5c6873/0, fault32180/55eba7/0,
full60005/7f8b98/0 closed; all7workers/groups/tokensclosed. Percompiler52component+
1005checkpoint+27publicationfault+13readerfault+1051DNG+110workerchecks PASS,
freshstock/Ox Make/fullselftests/Dunecompile1272current sourcepins match. First
modefilter count refusal82216/96d6fa outer0/twoworkers1 preserved closed; exact
native count2->4 corrected, no productionfaultswitch. Evidence
`tests/qualification/borrowed-reader-actual-20261017.json`. Qualified macOS only;
Windows explicitrefusal source/Linux runtime unqualified. Legacy channelcleanup
unchanged. Still no managed namespace/automaticselection/SDK/media/transport.

Partial-knowledge upgrade is now tested through actual authenticated cache reuse:
unsupported replacement invalidates old private descendants while preserving
pixel/full-byte identity and retaining the previous usable checkpoint. Focused
1051DNGchecks/compiler actual8636/1547ac/0 closed; allchildgroups/tokensclosed.
Test-only change, production unchanged;318sourcepins perprior4builds rebound
(no build rerun). Receipt `tests/qualification/dng-cache-partial-upgrade-actual-20261017.json`.
Root RPC readiness request01a148b7-6db0 remains separate; no runtime grant inferred.

Authenticated capture-to-refresh integration is qualified: `with_cache_capture`
requires complete trusted metadata, full-current-input/current-parser verification
and derives decoder provenance only from the owner entry. Focused1047checks per
compiler44609/428946/0 and fullcontroller93249/2fc314/0 closed: stock/Ox Make+
fullselftests/Dunecompile/productionlinked110workerchecks percompiler,1272current
sourcepins match. All6workers/groups/tokensclosed. Receipt
`tests/qualification/dng-cache-reuse-actual-20261017.json`. Orphan/changedinput
refuse beforecallback. No media/SDK/transport/automatic namespace or selection.

Known-entry lookup final record recheck now has targeted race+ablation proof.
Existing readercallback redirects equal-byte record afterrecordauth/duringindex
check; normalcode refusesbeforeresultdelivery. Copied filtered variant removing
onlyfinalrecordcheck reaches exactescaped-resultassertion onstock/Ox. Normal1043
DNGchecks/compiler PASS42365/6e723a/0, worker73695reaped0/groupsabsent/tokensclosed.
Initialdriver expecteduncaughtexit1 instead ofactual2 preserved; corrected only
expectedcode, guardassertionunchanged. Receipt
`tests/qualification/dng-cache-lookup-race-actual-20261017.json`. Production source
unchanged;1272currentSRCpins rebound againstprior4builds, no fullrebuild claim.
Managednamespace opening/automaticselection/recoveryscan remainopen; no SDK/media/EXIO.

Known trusted-entry recovery lookup implemented: actual no-follow presence must
match provided borrowedreaders; nativeFD/name/private/size/epoch checks around
bounded record/index authentication. Complete/record-only/entry-only/missing
classifications; foreignindex, wrongreader and equalbyte symlinkredirect refuse.
No opens/closes/cleanup/scan; resultisnot producerterminal/resourceclosure/current
source eligibility. Focused48730/287b5e/0 and all4builds+workers53905/09f4fb/0 PASS,
allgroups/tokensclosed,1272SRCchecks. Receipt
`tests/qualification/dng-cache-recovery-actual-20261017.json`. Managednamespace
opening/automaticselection/recoveryscan/eviction stillopen; no media/SDK/EXIO/mainpins.

Explicit quota-bound paired capture now implemented. Native admission binds two
fresh distinct empty stages in actual reservednamespace before writes; seal pins
same produceridentities with aggregatebounds. Failed/unsynced reservation cannot
admitpayload. Record/index stage+readback then one-use record-first entry-second
publication; entrycollision preserves record-only orphan/foreigntarget/entrystage/
consumedquota, no replay/refund. No FDopens/closes; caller retains settlement.
Focused52173/4a12f1/0 and all4builds+workers84836/be254d/0 PASS, allgroups/tokensclosed,
1272SRCchecks. Receipt `tests/qualification/dng-cache-capture-actual-20261017.json`.
Managedlookup/recoveryscanning/automaticactivation stillopen; no mainpins/media/SDK/
EXIO. PR3 remains stacked/unmerged; this is metadata capture, not a photo render.

macOS monotonic cache quota API now implemented: borrowed0700directory, identical
immutable no-follow configuration, atomic emptydirectory slots charged2MiB each,
max4096/8GiB; one attempt/ticket, no slot reclamation. Lostconfig over slots and
settings mismatch refuse. Two real processes race finalslot: exactlyone granted,
bothwaited0; injectedpostmkdir directoryEIO retains consumedslot/no replay/refund.
Currentstock/Ox41component+1005checkpoint+26fault+110worker checks/compiler PASS;
all4current Make+selftests/Dune builds PASS,1272SRCchecks. Actualfocused51354/88ab45/0,
fullcontroller86525/7cd749/0, allgroups/tokensclosed. Receipt
`tests/qualification/component-metadata-quota-actual-20261017.json`. Original tiny
fixtures only; no media/SDK/EXIO/mainpins. Managed lookup/routing/recovery remains
unimplemented; quota is conservative payload admission, not physicaldisk/RSS cap.

Separate stacked draft PR now open: https://github.com/querygraph/unison/pull/3,
`feat/component-cache-input-binding` against `feat/semantic-dng-oxcaml`; qualified
code/evidence throughf06f005a. No merge/mainRPC sourcechange. PR explicitly leaves
managed lookup/quota/automatic selection unimplemented and does not grant runtime
transport. All currentbuild/test owners closed; no resources held.

Current owner-entry/source integration qualified:stock/Ox Make+fullselftests and
Dune compile allPASS,1272SRC checks;110production-linked workerchecks/compiler
alsoPASS. Commonactualcontroller41172/e6f14a/0/no session, all5workers/groups/CPU
tokensclosed. Receipt `tests/qualification/dng-owner-entry-current-builds-actual-20261017.json`.
Currentfork handoff/source-review evidence merged into isolatedbranch (ada13312),
documentation/evidence only,0production sourcechanges from that merge. Preparing
separate stacked draft againstfeat/semantic-dng-oxcaml; no mainRPCpinschanged or
automatic cache enabled. Managedlookup/quota and actual newRPC remain open.

UDI/0 entry now has borrowed-FD staging/readback and macOS immutable publication.
CapturedentrySHA verified againstentirestage before nativeexclusive rename; exact
postpublishreadback passes, unrelatedstagebytes/overwrite refuse. Shared bounded
metadatawriter factored; privatepermissions now reject specialmodebits too. Both
DNG/core focused suites passed commoncontroller98587/e40f51/0, allworkers/groups/
tokensclosed; receipt `tests/qualification/dng-owner-entry-publication-actual-20261017.json`.
Preserved preexecPython syntaxrefusal bb6df9/1 acquired0resources. Managednamespace/
lookup/quotas and currentfull-build successor remain open; no media/SDK/EXIO/mainpins.

UDI/0 owner-index entry codec now implemented in DngComponents: root/path/
generation+input+orderedoutcomes bound to checkpoint/recorddigests; trusted-entry
digest required on load, record loading rechecks references and private schemas.
Metadata-only/portable; ComponentHash.checkpoint_root exposes bounded historical
tree without currentinputauthority. Focusedstock/Ox controls passed23340/397bf5/0,
worker45920reaped0/groupsabsent/tokensclosed; entryencode adds0source reads. Receipt
`tests/qualification/dng-owner-entry-actual-20261017.json` includes truncation/tamper/
wrongroot-path-generation/record/provenance controls. Managed owner-index namespace,
atomic entry publication/lookup/quota and full-build successor remain outstanding.
No media/SDK/EXIO/mainRPCpins changed.

Record publisher now has original postrename/pre-sync fault proof plus all4current
builds. Test-onlyfsyncshim (no production switch) proves directoryEIO afterrename
retains published/exactbytes/no replay; stageEIO/EINTR leave unpublished and no
retry. Focused20280/4c5cc4/0:41component+988checkpoint+21nativefaultchecks/compiler;
repeated41setup is not extraindependentcoverage. Currentstock/Ox Make+selftests+
Dune compile allPASS under commonactualcontroller66861/b6ab3a/0,1272productionSRC
checks. Production-linked110workerchecks/compiler alsoPASS89713/f7593d/0. Allgroups/
tokensclosed, no media/SDK/EXIO. Three exact receipts:
`component-record-publication-fault-actual-20261017.json`,
`component-record-publication-builds-actual-20261017.json`,
`component-record-publication-worker-actual-20261017.json` in tests/qualification.
Native record publication is qualified for these originals; persistent owner-index
and automatic diskcache selection remain unimplemented. MainRPCpinsunchanged.

macOS immutable-record publisher now implemented: independently authenticated
readback + borrowedprivate0700directory/0600stage/fullnative/no-followbinding,
stagefsync/exclusiverename/publishedidentitycheck/directoryfsync. No FDopens/dups/
closes/retention; caller owns settlement. Native ticket records rename success
before runtime/postrenameerrors, forbidsreplay, owner-onlynonportableAPI. Focused
stock/Ox41core+988checkpointchecks each PASS58876/7a5f21/0,worker39556reaped0/groups
absent/tokensclosed; extra negativeSafespawnticket control passes. Receipt
`tests/qualification/component-record-publication-actual-20261017.json` preserves
Darwinfeaturemacro and Oxowner-interface failures before finalsuccess. Actualtiny
fixtures only, no media/SDK/EXIO/mainpinschanged. Fullbuilds/postrenamefailure
injection/ownerindex integration still open; no hardwaredurability/productionclaim.

Worker decoder refresh connected: `SemanticWorkers.refresh_components` restores
trusted checkpoint+prioroutcomes, selects currentdecoders offowner, reports reused/
invalidatedIDs and optionally captures refreshedmetadata. Unchangedinventory runs
zero decoders; upgrade runs once within localizedbudget and preservespixels.
Currentstock/Ox fullMake+selftests passed21922/e903fb/0+48701/08525e/0; worker110checks
each passed6404/e45bad/0. Allworkers/groups/CPUtokensclosed;318sourcepins/build checked.
Receipt `tests/qualification/component-worker-refresh-actual-20261017.json`.
No media/SDK/EXIO/mainRPCsourcechanges. Namespace/ownerindex publication and current
Dune successor remain outstanding; no automatic diskcache selection yet.

Sibling composition qualified with actual sequential checkpoint upgrades: A→B and
B→A produce identical checkpointbytes/layoutroots/pixelprojections; initial decoder
order also commutes. Eachstep retains its independent sibling and charges only
8192Bfullverification+130B or5Baffectedwork. Stock/Ox114DNGchecks each passed
15700/95452e/0,worker34661reaped0/groupsabsent/tokensclosed. Receipt
`tests/qualification/dng-decoder-composition-actual-20261017.json`. Production
source unchanged from4a387823; fullbuild successor/index publication still open.

Owner-inventory decoder refresh now implemented: trusted prior outcomes checked
against restored schemas; unchanged targets reused, changed/removed reset;
invalidatedparentpreventsdescendantreuse; currentbindingsapplyparentfirst. Base
fallback schemas preserved so removalcheckpoint restores. Private/opaque leaf
reset nowallowed (needed for decoders returning no children). Stock/Ox103DNGchecks
each PASS80431/99049c/0,worker33969reaped0/groupsabsent/tokensclosed. Receipt
`tests/qualification/dng-decoder-refresh-actual-20261017.json` preserves earlier
narrowpass. Child-onlyupgrade charges8192+113B, parentupgrade8192+243B; no pixel
reread beyond full inputverification. No disk/index publication or currentfullbuild
successor yet. Existing publicationhelpers suppresscloseerrors, so not silently
repurposed for the new retained-ownership store contract. No media/SDK/EXIO.

Worker extraction now supports explicit optional capture_checkpoint (defaultfalse).
Only successful live extraction exports bounded immutable checkpoint metadata;
ordinary observations/restore returnNone, export adds no inputreads. Owner can
retain its digest directly from extraction rather than trusting loaded bytes.
Currentstock/Ox Make+selftests PASS actual76341/586683/0+80217/dea3a3/0; worker
capture→restore controls106checks/compiler PASS53028/f3513e/0, allgroups/tokensclosed.
Receipt `tests/qualification/component-worker-capture-actual-20261017.json`.
Both318production sourcepins rechecked. No media/SDK/EXIO; automatic owner-index/
namespace publication and current Dune successor checks remain outstanding.

Borrowed-descriptor record staging/readback now implemented in ComponentHash.
Fresh empty private0600 singlylinked regular outputs only; bounded writes+fsync+
identity/sizecheck, explicit intendeddigest; bounded reader requires trusteddigest
and ownerbinding. No pathnameopen/FDclose/namespace/indexpublication. Stock/Ox
focused controls passed actual18467/4ae3fb/0, worker29828reaped0/groupsabsent/
tokensclosed; original tiny disposable outputs only. Receipt
`tests/qualification/component-record-storage-actual-20261017.json`. Independent
readback before publication remains caller duty; failedstage staysowned, no retry.
Atomic namespace/owner-index implementation and current full-build successor open.

Persistent-record codec UCR/0 now implemented in ComponentHash: bounded record
contains owner binding/raw checkpoint digest/exactlength/checkpoint, and unpack
requires a separately trusted whole-record digest plus expected owner binding.
Focusedstock/Ox41component+971checkpointchecks/compiler PASS (971includes every
record/checkpoint-vector truncation, not971independentfixtures). Actual9682/5b7669/0,
worker29241reaped0/groupsabsent/tokensclosed. Receipt
`tests/qualification/component-owner-record-actual-20261017.json`. No filesystem
publication/index or automatic persistence yet; full builds for this codec source
remain outstanding. Prior full-build receipts retain their exact historical scope.

Current accumulated cache/worker source now also passes Dune compilation under
stock and Ox:actual36274/4d657c/0 and73981/8cc961/0, both worker groups/tokens
closed,318currentproductionpins rechecked perbuild. Receipt
`tests/qualification/component-cache-dune-actual-20261017.json`. Together with
prior current Make+selftests and102workerchecks/compiler, both build systems are
covered. Persistent store remains unimplemented; its concrete owner trust/index,
atomic publication/quota/crash and uncertain-close contract is now in
`doc/component-checkpoints.md`. Existing merge-base checksums are not same-UID
authentication and must not silently promote arbitrary checkpoint bytes to trust.

Restore-specific lifecycle successor now passes102workerchecks/compiler against
the unchanged qualified stock/Ox production artifacts. New controls cover queued
restore cancellation with zero read reports, changed input, insufficient budget,
invalid digest/negative budget/oversized envelope preentry refusals, borrowed-FD
preservation and successful recovery through filesystem admission. Actual
37203/771174/0; worker26351reaped0/groupsabsent/allCPUtokensclosed. Receipt
`tests/qualification/component-worker-restore-lifecycle-actual-20261017.json`.
No media/SDK/EXIO, production source unchanged from the prior full builds.

Worker restoration is connected: `SemanticWorkers.restore_components` takes bounded
checkpoint bytes and separately trusted owner digest, verifies current input/base
on a worker, returns immutable summaries/no fresh decoder approvals, and follows
existing CPU/IO/descriptor/cancellation settlement. Both current full Make builds
and selftests passed:stock25726/d3c966/0,Ox89779/00509e/0. Production-linked worker
controls91checks/compiler passed62679/94caa6/0; all groups/tokens closed. Receipt
`tests/qualification/component-worker-checkpoint-actual-20261017.json`. No media,
SDK/EXIO or main RPC pin changes. Durable owner store, automatic decoder/cache
selection and Dune successor qualification remain outstanding.

Accumulated checkpoint/DNG restoration/replacement source4d42753b now passes
current full Make builds+selftests on stock5.2.0 and OxCaml, each3semanticworkers.
Actualstock90151/b8a560/0 andOx28025/35ef1b/0; both workers genuinelyreaped0,
othergroupmembersabsent and allUnison8tokensclosed. Rechecked318currentproduction
sourcepins perbuild. Receipt
`tests/qualification/component-cache-integration-make-actual-20261017.json`.
Dune successor checks, automatic decoder provenance selection, persistent owner
store/worker integration and merge into main remain outstanding. No media/SDK/EXIO.

Private decoder replacement now has an explicit DNG API with expected-old-schema
guard, immutable success-only publication and shared private-fragment validation.
Stock/Ox94DNGchecks each/58calls passed, including stale/unsupported retention,
historical-view preservation and localized130B replacement after8192B restore.
Actual91068/d77ad7/0; worker19920reaped0/groupsabsent/tokensclosed. Receipt
`tests/qualification/dng-private-replacement-actual-20261017.json`. No media/SDK/EXIO;
automatic registry comparison/store integration and successor full builds remain.

DNG checkpoint restore is now connected through `DngComponents.with_checkpoint`:
fresh bounded DNG description, owner-authenticated metadata/full-input verification,
current base-partition validation, then live callback. Historical private views
remain explicit; owner decoder-provenance invalidation/store selection are still
outstanding. Focused stock/Ox88DNGchecks each/58calls passed; actual12756/7b2a9c/0,
worker19181reaped0/groupsabsent/tokensclosed. See
`tests/qualification/dng-checkpoint-restore-actual-20261017.json`. No media/SDK/EXIO
or automatic persistence; full builds for this successor still required.

Checkpoint adapter groundwork: `ComponentHash.validate_base` now checks restored
views against the current normalized parser partition without payload reads.
Private/opaque refinements are allowed; altered base geometry/schema/roles and
embedded pixel/standard claims refuse. Focused stock/Ox:41component+461checkpoint
checks each,23calls; actual94856/6f91b4/0, worker18727reaped0/groupsabsent/tokensclosed.
Receipt `tests/qualification/component-checkpoint-base-actual-20261017.json`.
Full builds and DNG provenance/restore/store integration remain outstanding for
this successor; earlier full-build receipts cover their exact historical sources.

Isolated follow-up: frozen DNG decoder bindings now refuse child-before-parent
order before file inspection, including nonadjacent ancestor relations while
allowing textual-prefix siblings. Focused stock/Ox controls pass83checks each,
58contained calls; actual83442/f7df5a/0, worker17995reaped0/groupsabsent/tokensclosed.
Receipt `tests/qualification/dng-decoder-order-actual-20261017.json` preserves the
initial interface-template mismatch failure and corrected successor. No main RPC
source change, media/SDK/EXIO or persistent DNG checkpoint adapter integration.

## CURRENT IN THIS WORKTREE: checkpoint core isolated from reviewed RPC main

Branch `feat/component-cache-input-binding`, worktree
`/Users/alexy/src/unison-component-cache-20261017`, based on mainee9015fc. Main
`/Users/alexy/src/unison` and its342 frozen RPC execution pins remain unchanged.
No RPC admission/review receipt observed during this work; do not dispatch without
the exact Root file/fresh guard. This checkpoint core is NOT integrated into main.

`ComponentHash.checkpoint` exports bounded UCH0 metadata; `with_checkpoint` requires
the owner's prior trusted metadata digest and recognized root schema, validates
canonical geometry and hashes the COMPLETE current input before cached subrange
hashes can reach a fresh session callback. No epoch-only or IO-free reuse; a hash
computed from an untrusted blob is not authenticated provenance. No automatic
store/archive/writer/RPC/worker-cache integration supplied. `reset_private_view`
invalidates one refined private/opaque subtree without reads or loss of raw-byte
coverage, refusing any pixel/standard claim. Old snapshots/unaffected nodes stay
immutable; replacement decoder reads/rechecks only that parent.

Actual focused62449/361452/0/no session:41existing+454checkpointchecks/compiler,
23containedcalls, positive portable immutable checkpoint capture/3negative live
capability captures. Make+selftests stock87017/2f0ab0/0 and Ox8061/883242/0;
Dune compilechecks stock81918/bfd974/0 and Ox12462/24ae26/0. All groups/tokens
closed,1272 current src checks. No EXglobal/SDK/media. Preserved added-control
failure13554/daa76b/outer0/child1 conflated provenance with identical leaf semantics;
final controls distinguish implementation provenance and changed meaning schema.
Receipt `tests/qualification/component-checkpoint-core-actual-20261017.json`43272B
SHAb5e08611d797ad50a8cde78a8adfba0aba32755d5f92080e3ca692b25c256f00.
Contract `doc/component-checkpoints.md`. Still needed: trusted persistent owner
record and publication/recovery, DNG decoder invalidation and worker/cache wiring,
then integration after the frozen RPC window is resolved. Full-input verification
can be avoided only with a separately qualified immutable/preservation witness.

<!-- Parallel historical checkpoint retained from RPC auditor branch. -->
The chronology below retains historical pending states. Current scheduling and
actual consumed-run status above supersede old readiness/absence notices.

Latest isolated integration08b4be45 (metadata merge10ace908) is qualified and
pushed to draftPR4: complete trusted cache capture -> full-current-input/base
verification -> scoped decoderrefresh.1047DNGchecks and110workerchecks percompiler,
freshfourbuilds/fullMakeselftests,1272sourcepins, all sixworkers/tokensclosed.
Main frozen342RPC pins still pass. Fresh readiness
`doc/component-remote-ready-after-cache-reuse-20261017.json`53c00072 sent to Root
queue01a148b7-6db0 requesting exact already-reviewed eightcase transport scheduling.
Workspace/admission absent at that observation; no current grant, dispatch or
Photo liveness inferred. Do not wait on complete MakerNote mapping to deploy a
qualified exact-preserving partial view; automatic cache selection remains open.

Latest user design clarification is recorded in SOL.md under "Rehashing is
incremental refinement": deploy qualified pixel/metadata separation with exact
opaque coverage; version each field refinement, invalidate only its dependency
closure, preserve prior usable views and avoid mandatory archive-wide upgrades.
This is a design requirement, not a new deployment or runtime qualification.

Stacked draft PR4 is open: https://github.com/querygraph/unison/pull/4,
replacing PR3 after a mistaken temporary base-ref push automatically marked it
merged. Base was restored with an exact lease to03f4ef6c; isolated cache source
remains separate. Current reuse integration/evidence is08b4be45,1047DNGchecks
percompiler and fresh four-build/worker qualification as indexed above.
Historical PR3: https://github.com/querygraph/unison/pull/3. PR4 carries

`feat/component-cache-input-binding` against `feat/semantic-dng-oxcaml` (not master).
Current owner entries/staging/publication now have stock/Ox Make+selftests+Dune
and110workerchecks/compiler PASS; all5workers/groups/grants closed underactual
controller41172/e6f14a/0. Isolated receipt
`tests/qualification/dng-owner-entry-current-builds-actual-20261017.json`, code/
evidence f06f005a, handoff a6aed151. Newer isolated quota API6e7c82bd is qualified;
see [current evidence index](doc/current-qualification-status.md). Managedlookup/
recovery/automaticrouting remain open. Main342frozen RPC sourcepins freshly pass checked_plan; requestd0f80794/
pland7a9f46d unchanged, workspace/admission absent. Freshsource readiness
`doc/component-remote-ready-after-cache-builds-20261017.json` requests separate
Root scheduling after explicitIOrelease; does NOT rehashruntimeartifacts, grant
runtime or infer Photo processliveness. No currentlyowned Unison resources.

Latest isolated cache successor is pushed through `e3c60795` on
`feat/component-cache-input-binding`. It now includes worker capture/restore/
decoder refresh, owner-bound record staging/readback and macOS borrowed-FD
exclusive immutable-record publication. Sibling upgrades commute across restored
checkpoints. Current stock/Ox Make+selftests and Dune compile pass; focused
41component+988checkpoint+21originalnativefault checks/compiler and110workerchecks
pass, allgroups/tokensclosed. Postrename directoryEIO retains published state;
stageEIO/EINTR not retried; test shim is absent from production. See isolated
`doc/component-checkpoints.md` and `component-record-publication-*` receipts.
Still not merged into main:342reviewed RPC source pins unchanged. Persistent
trusted owner-index/automatic diskcache selection and actual RPC transport remain
open; no resources held, no media/SDK/transport run or new admission inferred.

Isolated component-cache successor is now pushed through `c55a90de` on
`feat/component-cache-input-binding`. It adds current-parser partition validation,
DNG authenticated restore, explicit guarded private-view replacement and worker
restore through existing resource ownership. Current stock/Ox Make builds and
full selftests pass; focused DNG94checks/compiler, worker102checks/compiler pass.
All actual workers/groups/CPU grants closed. See that branch's qualification
receipts and handoff for exact source scopes. Not merged into main; main's342RPC
source pins remain unchanged. Durable store/automatic decoder selection/Dune
successor checks remain outstanding; no new media/SDK/transport admission inferred.

User design requirement: incomplete mapping of smaller fields does not block a
qualified pixel/metadata-separation release. SOL.md specifies refinements as
versioned component change sets, deterministic sibling composition, localized
invalidation, verified unaffected-hash reuse and atomic new-view publication.
Unknown fields remain exact opaque hashes; this is a design contract, not a claim
that persistent cache/worker integration is finished.

## CURRENT: RPC sources accepted; IO deferred; checkpoint core on isolated branch

Root receipts now independently rehashed/adopted in
`tests/qualification/component-remote-source-review-adoption-20261017.json`1685B
SHA604e49e5da278fcbc0b8a166c331489de4f6c25b84089076dda6844c26d2534b.
Source review64fa9095 accepts342 pins/six prerequisites with no findings. Scheduling
defer681324f5 explicitly prioritizes the operator's Capitola Smart Preview build
owning EXglobal; no runtime admission/Unison hold was created. Do not infer present
process liveness from that historical receipt; only Root's explicit IO release and
fresh exact admission can schedule this run. Standing CPU8/source work allowed.
Main342 pins/plan/argv still unchanged, workspace/admission absent at last check.

Independent cache work is committed/pushed on `feat/component-cache-input-binding`
at569395d9, retained worktree `/Users/alexy/src/unison-component-cache-20261017`
(git-worktree lock is evidence retention only, NOT a resource hold). NOT merged
into main, preserving RPC pins. Generic `ComponentHash` now has bounded checkpoint
metadata export/restore with prior trusted owner digest, recognized root schema
and complete current-file SHA verification; no epoch-only/IO-free shortcut or
automatic store. Private-subtree reset lets replacement decoders rehash their
parent while keeping unrelated pixels and previous snapshots.

Isolated qualification:41existing+454checkpointchecks/compiler (includes every
metadata-vector truncation),23contained calls, portable metadata checkpoint capture
and3negative live-capability captures. Make+selftests actual87017/2f0ab0/0,
8061/883242/0; Dune compilechecks81918/bfd974/0,12462/24ae26/0; focused62449/361452/0.
All groups/Unison8 closed;1272 src checks, no EXglobal/SDK/media. An initial added
test incorrectly equated implementation provenance with leaf meaning; preserved,
then split into provenance/stable-contract/changed-schema assertions. Receipt in
that worktree `tests/qualification/component-checkpoint-core-actual-20261017.json`
43272B SHAb5e08611d797ad50a8cde78a8adfba0aba32755d5f92080e3ca692b25c256f00.
Contract `doc/component-checkpoints.md` there. Next independent work: trusted owner
record/store/recovery, DNG frozen-decoder invalidation and owner/worker cache wiring.
Integrate only after resolving or explicitly superseding the reviewed RPC request;
do not silently invalidate main's342 pins. No own jobs or resource leases active.

## CURRENT: runtime readiness sent; no admission observed yet

Frozen342 runtime pins / pland7a9f46d / requestd0f80794 remain UNCHANGED.
`doc/component-remote-readiness-v1.json`2548B
SHA8b4e7b4183aec81a76a4690e74e8726740ca088b687ac09f4850f95730758687
now asks Root to schedule ONE finite run AFTER source acceptance, superseding only
the earlier source-only coordination intent. Source review/admission not found
at latest read of both legacy Photo and lightroom coordination locations; proposed
admission `/private/tmp/unison-component-remote-admission-v1.json` and workspace
`/private/tmp/u-cr-cf119542138e` absent at readiness observation. Queue01a14837-0d67.
Do not infer a grant; if one arrives, freshcheck exact pins/deadline/unusedworkspace
and execute the existing exact command ONCE, promptly return actual tool terminal.
No resources or Photo hold is created by readiness; standing8/8 remains.

Separate nonruntime `tests/component_remote/readback.py`+`readback_controls.py`
added metadata-only independent readback. Eight original fabricated controls
ACTUAL initialexec4fa3ff/0/NOsession, child6465reaped0/groupsabsent/CPUclosed.
No canonical IO lock, RPC or media; never authenticates parent tool terminal,
rehashes functional inputs or authorizes FD release. Runtime342 pins unchanged.
Receipt `tests/qualification/component-remote-readback-controls-actual-20261017.json`
1771B SHAcbc3c712a03c75a028649db1fdff9e990dbf2a8ac83377df1ff2d92f7ba5b01b.
If Root review finds a source issue, preserve frozenv1 and prepare an immutable
successor; do not mutate reviewed bytes or recreate an admission. Actual RPC
transport and persistent binding still remain unqualified.

## CURRENT: component RPC coordinator frozen for SOURCE REVIEW ONLY

`tests/component_remote/` now contains bounded qualified-close IO, exact plan
contract, inactive generated case, retained call kernel, independent prefix/
functional auditor and one-use parent/worker coordinator. Existing EXglobal then
Unison00..07 only; worker inherits9 descriptions and checks exact canonical IDs
plus policy.300s owner observation/260s new-call horizon/30s call observation;
unknown retains objects/FDs, no broad aggregate kill. Shared direct-child capture
retains close uncertainty and separate proxy owner; old benchmark wrapper is not
used. Intents/raw outcomes precede verification, failed cases stop successors,
pure audit cannot substitute for actual parent terminal or release locks.

Final original disposable/fabricated18controls ACTUAL initialexec3503c7/exit0/
NOsession; direct child4856 actuallyreaped0, groupothersabsent beforeleaderreap.
All direct groups reaped0/othersabsent/Unison8closed; no EXglobal/RPC/SDK/media.
343 source pins matched before/after; runtime closure342 files. Receipt
`tests/qualification/component-remote-coordinator-controls-actual-20261017.json`
43053B SHA16d52c2cad736a21f000effb0797cdb380f27b31d3aec2e0181f761446a1da5b.
Raw result `/private/tmp/unison-component-remote-controls-gdrylkza/RESULT.json`.

Frozen plan `doc/component-remote-plan-v1.json`44341B
SHAd7a9f46d7a5e6da4476ff54409a98ffbe4fa7ea5e64a3727c59dd7bbca77b0ad.
Request `doc/component-remote-request-v1.json`2531B
SHAd0f80794b5fe2eae1f03efcff5a3594a4cb1da5b838d2f8e7ad5b8f6d4af7a49.
Workspace `/private/tmp/u-cr-cf119542138e` is planned/UNSTARTED, no admission yet.
The request is explicitly SOURCE REVIEW ONLY, not runtime-ready grant or Photo
hold; do not dispatch from these files. Ask Root for source review, preserve pins,
then announce readiness before requesting a fresh exact finite IO admission.
No old consumed grant applies. Contract: `doc/component-remote-probe.md`.

## Prior checkpoint: production-linked remote probe built; coordinator pending

`tests/report/remote_probe.ml` now installs real generated roots, negotiates and
propagates preferences, calls the production local/remote component API and
checks supported/unsupported/no-capability/disabled outcomes. Unsupported must
be exact `not TIFF`, not a transport/admission failure. Cleanup attempts every
known root and pool shutdown, retaining original+all cleanup failures. The final
local marker explicitly does not substitute for external client/server waits.

Build-only driver `tests/report/build_remote_probe.py` passed actual41349/c92921/0
NOsession, outerchild1211reaped0/othersabsent/CPUgrantclosed. Ten contained calls:
two stock/Ox production-linked compiles, six exact argc/path/mode refusals and
two offline preference parses. No roots installed/connection/media/SDK/EXIO in
these controls.320 source pins+474 linked artifacts reverified; production src
unchanged from293ee8be. Final raw result directory:
`/private/tmp/unison-component-remote-probes-n_sc3ooj`.
Stock probe SHAae6c322ef69733d67c2c5e7fa2312e93a161813fb81a6df93e60f611020f9ff1;
Ox SHA cf53558789a16c7b0a9240efdc9b44ea1ef45a64e6d53146a928b4b3287d6bd3.
Receipt `tests/qualification/component-remote-probe-build-actual-20261017.json`
40941B SHA8ca7b040e2ac969e6ba9f9fda744463d71657f610b9c7c6d877e8583f1f3d1f9.

`doc/component-remote-probe.md` defines the proposed eight-case matrix and required
external contract. It is NOT a runnable admitted coordinator or scheduling grant.
Next implement owned strict-loopback intent/outcome recording, combined raw
client/supervisor/server/pump/worker/group/FD audit and unknown retention, qualify
disposable failure accounting, then freeze exact command/workspace/pins and seek
fresh Root EXIO admission. No runtime mode was exercised, no new-RPC/mixed-version
claim, no consumed-grant reuse; all resources closed. Persistent binding remains
open independently of this reporting qualification.

## Prior checkpoint: bounded remote component protocol implemented

`semantic-components-v0` / `semanticComponentsV0` now provides a separate SIC/0
path for the fixed empty-decoder DNG component contract. Explicit details remain
off by default. Remote calls require both the new feature and an enabled built-in
DNG profile; replies bind exact contract+fresh32-byte nonce, max2048B, five fixed
role slots. Unsupported views are innerError, malformed wire is outerError.
SIR0/SIR1/SDE bytes and transfer/archive decisions unchanged. Peer hashes never
become local source/preservation capabilities. Source admission spans encoding/
queued output, with no nested core admission; the declared model envelope is
8*1MiB+256KiB estimate, not RSS cap. Spec `doc/component-report-v0.md`.

Current Make+selftests stock17636/f77624/0 and Ox99727/bc9286/0 PASS. Dune compile
checks stock27170/d7d233/0 and Ox84596/1efd9e/0 PASS;1272 production-source checks.
Final report suites stock7161/8e36a6/0 and Ox9480/d24ba2/0 passed25 named controls
each, including independent byte vector/every truncation/substitution/malformed
fields. Linked local/refusal/cache owner controls stock33153/a0c271/0 and
Ox47843/6bea84/0 passed. All groups/Unison8 grants closed; no EXglobal, SDK/media.
Initial Ox codec+Make failures are preserved: partial Buffer.add_string closure
was local when List.iter required global. Explicit function fixed inference;
no portability/ownership annotation weakened.

Receipt `tests/qualification/component-remote-source-actual-20261017.json`47872B
SHAc1d9491f6525c203c3eed4ea1dfd577ef4c5bdf1df60863b02f15b165832f074.
Actual new-command RPC, mixed-version and failure transport trials NOT yet run.
Next prepare a production-linked finite remote probe with existing supervised
loopback server/client journal proofs, freeze current binaries/source/command,
then seek a separate Root EXIO admission. No existing consumed admission applies.
Persistent component-cache identity/dependency binding also remains open; no
complete MakerNote requirement should block otherwise qualified baseline use.

## Prior checkpoint: explicit local component details wired and qualified

The off-default local `semanticcomponents` preference now appends component
comparisons to explicit semantic details with enabled profiles. Existing owner
admission/worker/FD settlement carries a frozen empty decoder set, full-file read
budget equal to opened size, and compact observation plus source stats. Both
base-report and component snapshots enter one-shot stale-display invalidation.
Remote roots refuse explicitly without RPC; ordinary scan/transfer decisions
and SIR0/1 encodings are unchanged. Persistent identity reuse and negotiated
remote component reporting remain open.

Current stock Make+selftests actual18607/872a61/0 and Ox Make+selftests
86930/71c590/0 passed. Dune stock95297/0b5754/0 and Ox54906/66e0ab/0 passed
(Dune compile checks; full selftests ran through Make). All1272 production-source
checks bind current bytes. Final owner controls stock48678/275d19/0 and
Ox16614/d30cd2/0 passed default-off/explicit preference, local hash comparisons,
remote refusal, opaque/pixel separation, source snapshots, unsupported/missing
paths, settled permits and prior one-shot UI-cache controls. All contained groups
reaped and canonical Unison8 grants closed; no EXglobal/Photo media/SDK.

An initial owner control failed because max_payload0 violates existing admission;
its failed child1/group closure is preserved. Positive minimum1 fixed the bounded
summary envelope before the final builds; no broad runtime admission change.
Receipt `tests/qualification/component-owner-local-actual-20261017.json`42356B
SHAe3fe24387cf26d9f6e4cdcb77e0d7795896f73b0e686bfbc51e8e22574ab32a5.
Contract and usage: `doc/component-workers.md`. Next: bounded negotiated remote
component reporting and qualified persistent input/dependency binding, without
turning summaries into transfer/merge authority.

Latest implementation continuation: `SemanticReport.render_components` now
provides a local advisory comparison of explicit versioned component observations.
Exact full bytes are reported independently; unequal schema contracts suppress
component comparisons; omitted/None lanes stay unknown. Five role comparisons
include encoded pixels, standard/private metadata, structural and opaque bytes.
Malformed digests/counts/duplicate lanes refuse, schema text is terminal-escaped.
No wire bytes, RPC/UI dispatch, archive or transfer authority changed. New five
controls plus the existing report suite passed stock actual95503/9475c8/0 and
Ox actual3630/77408e/0, both child groups reaped and canonical CPU grants closed.
Receipt: `tests/qualification/component-report-focused-actual-20261017.json`.
That focused checkpoint preceded the full builds/local wiring recorded above.

Latest user design clarification: separate pixel/metadata hashing is already a
valuable baseline; incomplete mapping of smaller fields must not block otherwise
qualified deployment. SOL.md now explicitly defines progressive-rehash acceptance:
meaning and stability are separate versioned claims; refinements declare affected
IDs/dependencies/old and new roots, compose deterministically across siblings,
retain the prior view on incompatible claims, and invalidate only affected leaves
and ancestors. Unknown bytes remain exact/hash-covered. Old schema roots support
common-version comparison or exact fallback. This is a design update, not a claim
that persistent cross-session reuse or deployment is already qualified.

## CURRENT: typed component worker API qualified and integrated

`SemanticWorkers.components` is now implemented on main via7b900ada, cherry-picked
from tested isolated source9327553e. Explicit owner-frozen decoders and component/
decoder read budget use the existing source FD/domain/CPU/local-filesystem gate
and queue lifecycle. Compact immutable full/layout hashes, five optional counted
role projections, decoder outcomes and original stats cross completion; no
session/reader/snapshot capability escapes. Unsupported returns an explicit
format Error; operational/budget failures fail the job, negative budget refuses
before FD admission. Ordinary jobs do not add a component pass.

Final focused actual86825/c76ad0/0/no session passed87checks/compiler,4 contained
production-linked compile/runtime calls and334 linked artifact pins. Twelve
separately opened FD jobs on configured2worker pool match full/pixel identities;
private refinement runs off owner, read observer on owner. Baseline/refined charges
8192/8321B versus measured delivered8280/8409B include88B DNG geometry. Successful
IO-gated execution, operational failures, negative admission, queued/late cancel,
completed-before-shutdown suppression and descriptor/permit/queue/localIO recovery
passed. This is functional configured-worker parity, not compute overlap/speedup.
Earlier00180checks and00284checks passed/closed with narrower coverage.

Four full builds: Make pair actual38881/087acc/0; Dune+fullselftests(workers3)
pair actual13072/c40426/0. All groups/canonicalUnison8 closed,1272 current compiled
production-source checks matched. No EXglobal/SDK/media/camera/Photo lease used.
Receipt `tests/qualification/component-domain-workers-actual-20261017.json`75212B
SHAf701bc011ca6a40f24a4e4affd00efc93fb5288c271c864bc4a0b0b8443a35cc.
After cherry-pick, all320 qualified source files were byte-rebound to main in
`tests/qualification/component-workers-main-rebind-20261017.json`31585B
SHAb2ab28ca1521538952a4c64cead65753bb3eba2fa4b22faedb00dfefd9457fa3.
Contract: `doc/component-workers.md`.

The isolated checkout/branch is now committed, not unbuilt; retained for evidence.
No jobs/resources active. Main src changed AFTER accepted layout receiving, so
old receiving binaries/receipts remain historical and must not be treated as
fresh source pins or reused grants. Component RPC/UI consumers, persistent reuse/
archive binding and representative real-camera qualification remain open; complete
private grammar is not a baseline deployment gate. Next focus is an owner report
consumer and qualified persistent identity binding, without broadening prior
receiving/SDK/pixel/resource claims.

## CURRENT: layout reschedule actual PASS/CLOSED and independently adopted

Root's distinct scheduling successor `/private/tmp/unison-layout-receiving-admission-rescheduled-80c9c19d3f48.json`
7394B SHAdcc2d5cb9beccc2dc606b1a8c454340797e6eb035913d8cc917dc817ec207758
was dispatched exactly once after fresh request/plan/38sources/sixprereqs/
interpreter/build/unusedworkspace/deadline checks. Guard1792208390.9865868 and
START1792208391.2983081 were BEFORE deadline1792208728.243482. Do NOT call
this consumed run expired-unstarted merely because its deadline is now past.
Owner74328/worker74331; actual owning session11517/initiala15b7d returned
terminal85a4a8/exit0/NOsession. Prompt terminal/release evidence sent Root.

All18 rows/54 CLI seed-update-noop calls completed, stock/Ox×ordinary/receiver
clone/semantic×workers1/2/3. Six semantic rows/twelve updates actually selected
`org.firstpair.dng-layout/0`; generated opaque private references into changed
XMP stayed exact, full donor outputs/old bases/no-op epochs passed. Parent
strict54call audit and independent prefix54/zero-no-creation checks passed;
all38postsourcepins matched/unresolvedempty. Worker74331reaped0/othersabsent,
CPU8+EXglobal closed. No SDK/camera/pixels/physical savings/quiet timing claims.

Workspace `/private/tmp/unison-layout-receiving-rescheduled-80c9c19d3f48`:
OWNER-TERMINAL502B SHAa48d9c8c3365783aaa51d3644a991dd41ea88baa6323c3c2dbd82d97a38ba0d5;
OWNER-RETURN3668B SHA079cf8825eea2a44d2900e4b3989b951673ec405fc44de4b7dcaae702cb86d58.
Metadata-only auditbf505c/1 initially refused Root's reschedule schema; preserved
001REFUSED. Exact unchanged semantic fields and scheduling-only namespace changes
were verified, and an explicitly recorded projection fed the strict v1 auditor.
Root originals/raw evidence unchanged; native execution never repeated.
Independent return audit3082B SHA290afa8f922aa2e6ee86af79bff4e34595d41206809953bd06479ceaf589ce46.

Local qualification `tests/qualification/layout-receiving-rescheduled-actual-20261017.json`
4183B SHA184db278ca5eef73ce1ec99914752e9110dc1641c9a899655bce6b22480b09f7.
Root independently ADOPTED actual terminal transcription/raw functional+process
proofs and freshly acquired/closed EXglobal+Photo8: acceptance1084B
SHA48e864bf524a4027d787f0180ac94bce6fb1d6c186784c4e278ecfb6f211d45e under
`/Users/alexy/src/lightroom/.private/photo/coordination/UNISON-LAYOUT-RESCHEDULE-80c9c19d3f48-ACTUAL-ACCEPTANCE.json`.
Root did NOT personally poll our tool; that distinction is explicit. Adoption
`tests/qualification/layout-receiving-root-adoption-actual-20261017.json`1575B
SHAc22be7827e9bde67d5a37141d1b15df3225867f1d020aa7a9ec17592bfb59138.
No hold, replay or successor. Original209266ba remains expired-unstarted.

## Historical isolated preparation: now superseded by qualification above

To preserve the reviewed receiving source while scheduling was pending, created
owned checkout `/Users/alexy/src/unison-component-workers-20261017`, branch
`feat/dng-component-workers`, based ond8e13624. Only its
`src/semanticWorkers.{ml,mli}` are modified so far; no build/runtime ran there.
The proposed explicit Components operation takes frozen decoders/read budget,
uses existing FD/CPU/IO/cancellation lifecycle and returns compact immutable
projections/outcomes/stats, never session/reader/snapshot capabilities. Its
operational ComponentHash.Invalid errors are intended to fail, not become
unsupported. This code is UNVERIFIED and not in main/draft PR; do not claim it
implemented/qualified yet. Next: focused production-linked worker tests (parallel
parity, read observer, queued/late cancellation, failure/FD/budget settlement)
and stock/Ox builds, then merge only after verification. Same existing canonical
Unison00..07 pool; sibling checkout has real sharedPhoto policy paths. No new
pool, SDK/media/EXIO grant or running process. Main receiving code remained frozen.

## Historical predecessor: V1 issued, then expired unstarted

Root DID issue `/private/tmp/unison-layout-receiving-admission-v1.json`7342B
SHA209266ba0d44d1e588bd1fd50ef1d8df2995f61ab024732e4bfd7de21af261c9,
with Root reviewd9044047 and exact requesta1b0dc64/plan77f87fab/38 code pins.
Issued1792207049.53455, deadline1792207649.53455. Discovery during later source
work at1792207724.68364 was AFTER expiry. Actual preexec guard00c0d2/exit2/no
session refused before executor/CLI/payload/CPU/IO acquisition; original grant
and absent workspace preserved. No runtime parent or worker existed to report.
Owner refusal `/private/tmp/unison-layout-receiving-v1-EXPIRED-OWNER-20261017.json`
920B SHA9d1c46236475c675047869d5c760b11e4564d07e7b7308d2b8ba629bd12ecc59.
Repo `tests/qualification/layout-receiving-v1-expired-actual-20261017.json`
1614B SHA65f778b8bb1c94365b4b32338d3257fdaf48ab2f00d0f143cde981f9a4d4d7c0.

Root notified promptly queue01a147e8-8281 and asked for separately scheduled
fresh successor/workspace, preserving the expired original. DO NOT dispatch
209266ba, extend it or mistake old “not admitted” snapshots below for current
state. Root may independently reschedule; reconcile any existing successor
before preparing/launching another. Poll scheduling metadata promptly during
future source work; late queue delivery is not a reason to miss a known window.
No active Unison runtime/resources; original38 execution pins remain unchanged.

## Latest partial-field decoder prototype: generated DNG nesting qualified

`tools/dng-fields/privateIfdFields.{ml,mli}` creates a trusted compiled child
plugin for up to32 selected ASCII fields in a bounded classic private directory.
The owner supplies byte order and explicit signed parent-relative value-base
translation. Inline/outlined values are checked; selected aliases, invalid
ASCII/count/type/bounds and overflow refuse. Unknown entries and next links are
not followed. Shared reader/budget errors propagate. Schema/code declarations
are framed into provenance, also included in child schemas so private projection
versions change while unrelated pixel hashes/nodes remain unchanged.

It is NOT installed in Unison, a vendor-family router, an actual model-field
mapping or a stability/ignore policy. No real camera/SDK or source-photo reads.
All leftover bytes stay opaque/hash-covered. This is a concrete community/
piecemeal child-decoder mechanism without requiring complete private grammar.
README states address-space, trust, budget and confidence limits explicitly.

Actual final31242/09d1b6/0/no session,47 contained calls,59 original checks per
stock5.2/Ox5.2+ox compiler. Both private byte orders within actual DNG nesting
passed; one first refinement charged6201B (4096 initial +57 decoder +2048 parent
rehash), preserved full SHA and pixel projection/node; separate code-version
branch changes private projection. Earlier00145checks/compiler core-only passed
and is historical. Evidence
`tests/qualification/private-ifd-fields-prototype-actual-20261017.json`9611B
SHAaaaaa9a9bcf5023e4d83bb2a03e907b9960e2b60220aa9c8ef99cddbc8b0fc16.
All owned groups/CPU8 closed; production src and pending receiving38 pins are
untouched. No physical IO/RSS/performance, real-camera or production claim.

## Latest supplement: independent request/raw-log receiving auditor

`tests/layout_receiving_result_audit.py` is a pure post-run consumer outside the
frozen38-source receiving worker closure. It requires the requested layout mode,
packet size (including frozen8192 default), admitted binary/compiler SHA maps,
runner source map and per-call client path consistency; it reruns the existing
strict54-call audit and reparses captured SDE logs for all six semantic rows.
Each must prove two `org.firstpair.dng-layout/0` updates with matching reported
write/payload/window counters. This prevents an optional-mode flag or cached
counter from substituting generic receiving evidence for layout qualification.

Requested and resolved executable paths are retained as observations, with byte
identity bound by admitted SHA. The runner resolves macOS /var and compiler
symlinks; the pure auditor neither re-resolves filesystem names nor claims to
prove physical aliases. The caller still authenticates request/result/raw
process receipts and collects the actual owner terminal separately. The helper
cannot acquire or release resources or grant execution authority.

Final controls actual exec_command185857/exit0/no session:4 unittest methods,
13 original negative mutations; explicit/default packet cases and canonical-name
observations passed. Fake54-call records only, no actual sync/media/SDK/EXIO.
All child/group/CPU8 closed. Evidence
`tests/qualification/layout-receiving-result-audit-controls-actual-20261017.json`
10258B SHAdf82335ffdf07c07af915e617146c26741a449b0a5549d039678fddd0d229012;
helper6081B SHAc36c8cd48d2b2ca33fb88c40b29bca38804ca83750ec884b760e27dea5556a9f.
Earlier001..003 smaller fake controls passed/closed and are retained.

Existing requesta1b0dc64/plan77f87fab and all38 execution pins are unchanged.
Fresh metadata1792206860.263437 observed admission/workspace still absent;
this is scheduling metadata, not a fabricated owner terminal or an admission.
No actual receiving START/resources. Root source-review request remains the
same queued01a147d5-8cd6; supplement does not replace, renew or dispatch it.

## Latest: exact-layout production receiving request prepared, NOT dispatched

New optional `SYNC_LAYOUT_ONLY_CONTROLS=1` routes only through the separately
admitted shared8 `sync-functional` IO job. It uses the existing18 rows/54 CLI
seed-update-noop lifecycle. Original generated DNGs include128 opaque bytes and
an unknown IFD-shaped scalar, both deliberately referencing changed XMP. The
semantic rows must select `org.firstpair.dng-layout/0`; exact output, unchanged
old bases and no-op epochs are checked by the existing runner. Optional audit
checks reject missing/changed private witnesses and wrong profile/update counts.
Default fixtures and property-removal runs remain independent.

Source controls actual93255/bd07e2/0/no session:8 contained calls,197 preference
boundary checks per stock/Ox compiler linked to338 actual production artifacts,
original tiny fixture checks, seven fake layout-audit refusals, exact manual
route and CPU-only refusal controls. All groups/CPU8 closed. Receipt
`tests/qualification/layout-receiving-source-controls-actual-20261017.json`
4359B SHA7db703c799b2df265cf9a665a13d5e184c7dd7ff33b63babbbe50868f9d4981f.
New `tests/dng_layout_preferences.ml` qualifies current all-three-profile alias
and peer capability omission; old v1-only preference fixture remains historical.
These are preference controls, NOT actual old-peer receiving/transport proof.

Fresh Make+full selftests for both stock/Ox actual24573/212cf6/0/no session,
workers3 per endpoint/jobs2/Adobe validation off;950 captured source hashes
matched and all groups/CPU8 closed. Build receipts are under
`/private/tmp/unison-layout-receiving-{stock,ox}-selftest-20261017-001/RESULT.json`.
Repo evidence `tests/qualification/layout-receiving-build-selftests-actual-20261017.json`
3961B SHA72a1d4221d3b1fd6bbe784fb92556317cf32f635d3ea3e23914d7d65d189f7e6.

Fresh exact request `doc/layout-receiving-request-v1.json`10738B
SHAa1b0dc643605c7fcecbfe4952d25cf14df839fae45fbcc82086a9d8e33d1491b,
plan `doc/layout-receiving-plan-v1.json`8889B
SHA77f87fab838911aa98aa3543cd9b9506c6360d4f73177ebdc959cc61e67d57a1;
38 execution pins/six prerequisites. Workspace
`/private/tmp/unison-layout-receiving-2a6cbd4b84be4d9c900b92271b38a530`
and admission `/private/tmp/unison-layout-receiving-admission-v1.json` absent at
preparation. Actual matrix NOT started, no live grants/resources. Root must
publish a fresh exact admission/deadline; use once only after fresh checks.
Limits:Unison00..07+existingEXglobal,300s observation/30s CLI/8GiB conservative
logical planning budget (not measured physical cap), no SDK/media/compiler in
actual matrix. Unknown retains real owners/grants; no replay/automatic successor.
This advances the operation-specific receiving qualification, not complete
camera understanding or semantic merge/rendering authority. Standing8/8 remains.

## Latest: owner-frozen nested DNG dispatch is implemented

`DngComponents.freeze_decoders` now validates up to64 immutable ordered bindings
before file inspection. `with_snapshot` hashes the DNG once and applies private/
opaque parent then child decoders within the same shared-budget session. Every
outcome records target, decoder and implementation SHA. Missing/unsupported
knowledge retains the prior view. Private plugins cannot introduce pixel or
standard roles or target those leaves; operational errors propagate. No registry
mutation, peer code, subprocess capability or persistent skip is added.

Final generated stock/Ox controls actual46167/114660/0/no session passed80 checks
each and58 contained calls. The8192B fixture plus only parent/nested/decoder
reads charged8435B; pixel/standard/full hashes stayed unchanged and the refined
view changed. Duplicate/invalid/provenance/count refusals, distinct outcomes,
operational error propagation and Ox safe-domain capture of the frozen abstract
handle passed. The earlier001/002 controls passed with narrower scopes and are
retained. Four full Make/Dune builds actual78758/ced55a/0/no session passed;
1896 captured source hashes and current binary pins were rechecked. All groups
and Unison8 tokens closed. No real media, SDK or EXglobal IO was used.

Evidence: `tests/qualification/frozen-dng-decoders-actual-20261017.json`,16665B,
SHA392edbe4ecb8dff563c116a0943d1befe8c8a160efd559ff4fd282f4a70d09aa.
The frozen dispatch mechanism is ready; actual vendor modules, component worker/
archive integration and qualified persistent reuse remain open. Complete private
field interpretation is not a baseline deployment gate. The next receiving
qualification should exercise the new exact-layout profile in production paths;
retained-camera/SDK/bulk IO still needs a separately coordinated exact admission.
Older “freeze decoders next” notes below are historical. No active owner/resources.

## Latest DNG component adapter and inspector: generated controls PASS/CLOSED

Current `DngComponents.describe` consumes bounded claims from the existing
DngSemantic graph parser: classic/BigTIFF, both byte orders; inline/outlined
standard/private values; encoded image-unit ranges; structural descriptors and
padding. Unrecognized values conservatively private, unclaimed gaps opaque;
no vendor meaning/stability claim. Physical aliases refuse independently claimed
components; at most480 regions keeps core node/gap accounting bounded. XMP is
optional for observations, existing transfer profile requirements unchanged.
`semantic-inspect --components` now reports full SHA/layout view and five counted
optional role projections. No components means null, never empty-pixel identity.
Value schemas bind type/count/byte order; image lanes cover encoded unit bytes,
not complete raw/preview classification or rendering dependencies/equivalence.

Actual focused80459/a5ba17/0/no session:57 contained calls,68 new DNG checks per
stock/Ox plus49 layout and4scalar/8private strict-profile regressions each;
new JSON and legacy inspector calls passed. Four full Make/Dune builds actual
34054/c92ae0/0/no session,1896 source hashes rechecked. Retained-inspector
launcher builds stock/Ox actual7600/8f2137/0,zero input executions in those build
receipts. All owned groups/CPU8 closed; no real media/SDK/EXglobal acquired.
Receipt `tests/qualification/dng-components-actual-20261017.json`19712B
SHAee43db2e1b7688b49d3da6ce914cd8d563c31d36f597463e53f1babd51e5f06a.
Earlier001 outlined-only and002 inline controls passed/retained as historical;
003 is current integration evidence. No active process/resources/new grant.

Next: owner-frozen actual vendor child decoders and persistent versioned cache
with qualified input/preservation bindings; worker/archive integration and
actual remote/camera qualification remain open. No exhaustive private mapping
release gate; unknown bytes stay exact. Older core-only status below is historic,
not a claim the DNG adapter is still missing. No consumed admission replay.

## Latest incremental component core: implemented and qualified, not DNG-bound yet

New `ComponentHash` MLmodule supplies typedphysicalpartitions/roles, fullSHA plus
schema-boundview/layout hashes andlogicalroleprojections. UnclaimedgapsOpaque;
allbytescovered. Pixel/standardmetadata/privatemetadata/structural/opaque lanes
separate; missingprojectionNone/counts preventconstant-empty-pixelidentity.
Initialonepassfeedsleaf+ancestorcontexts. Refinementrereadsonlyparentspan,
verifiesitsrawSHA, retainsunaffectednodes/pixelhashes andcomposesancestorviews.
Nestedtrustedcompiledplugins receiveparent-boundedreaders/subreaders, shareone
chargedrequestbudget andcarryownerpinnedimplementationSHA provenance. Explicit
unsupported preservesoldopaqueview. No writes/registries/processloading/FDowner
ortransformationauthority. Session/readerexpiry andcross-sessionrefinement refuse.
Callerownsimmutablesnapshot; fstatnotclaimedhostilewriterproof/persistentcache.

Actualfinalstock/Oxfocused77520/8c9155/0/no session:41checks each,22containedcalls,
3expectedOxcompile refusals forescapingsession/snapshot/reader. 8192initial bytes
+onlyparent/nested/decoderreads matchindependentdeliveredstats; pixelnodephysical
reuse, modelversionbranchchangesviewnotpixels, budget/partition/count/depth/
sourcechange/emptyprojection/refusal checksPASS. Twoinitialcompilerfailures
(recordlabelambiguity859460/1, fixtureparenthesesf7d98f/1) preserved/closed;
intermediate003..005passedwithnarrowerAPIs, final006iscurrent.
Fourfullstock/OxMake+Dunebuildowner55663/5c886a/0/no session passed;1880sourcehash
checks/currentbinarypinsmatch, allgroups/CPU8closed. Receipt
`tests/qualification/component-hash-core-actual-20261017.json`9920B
SHAabdf37ef85a6d896e2e44d5ea8927e2299b01c579968619b2b044919f8fe706b.
Contracts/framing `doc/component-hashes.md`. NoSDK/media/EXIO/activeUnisonowner.
StillNOTintegratedDNGfragments/frozennesteddecoderdispatch, publicinspector,
cross-session/persistentcache orsyncidentity. Thosearenext; donotclaimrealcamera
pixel/componenthashingdeployed ormarkfullgoalcomplete. ExistingexactlayoutSDE
source9359215 remainsseparatequalifiedstep, no consumedgrantreuse.

## Latest partial-knowledge transfer implementation: DNG layout profile

`DngLayout` org.firstpair.dng-layout/0 /dng-layout-exact-v0 isimplemented as a
separatelynegotiatedfallback afterstrict1/0 foroptinsemanticdng. Defaultoff stays.
The existingboundedDNGwalk nowhasexplicitlayout_only policy: typedunknown/private
declaredvalueextents acceptedwithoutinterpretinghiddenpointers; all complement
andfullfilebytes hash-covered. Strictprofiles unchanged, noMakerNoteSafetybypass.
Exactplan/materializer stillsameprofile/size/layout/complement+basis/stagecheck+
fullactualdonorSHA. No reloc/ignore/merge/semantic-equivalence authority inferred.
Existingreconcile/cache paths explicitlyonly0/1; no newlayoutentrythere.

ImmutableFormatExtension.span_semantics defaultsOpaque_spans; strictbuiltins
explicitKnown_metadata. Workersconsumefrozenhandleannotation; peerdecodedproof
alwaysOpaque. No wire/archiveencodingchange. CoreclassifyUninterpreted_regions
separateslayoutconfinementfromKnownmetadata; inspector/ownerreportcoveragewarning
updated. Existingstandalone strictclassificationfixtures explicitlylabeltheir
knownmetadata contract. Fullheader/modefilter/Make+Dune integration qualified.

Actualfocusedowner93568/7dddd6/0/no session,43containedmodefilter/compiler/runtime
calls:49layoutchecks/compiler +oldstrict4scalar/8private safetychecks/compiler.
Classic+BigTIFF/bothorders, opaqueLONG/IFD-shapedrefsintoXMP, exactdonorstageSHA,
opaquechangefallback, corrupttargetSHArefusal, noop0writes, nomergeauthority.
Actualfourfullbuildowner74559/0d2fc9/0/no session; stock/Ox Make+Duneallpassed,
1864capturedsourcehashchecks/currentbinarypins match, allgroups/CPU8closed.
Stocklegacykernel+read-onlyinspector actual52614/ebaacf/0 passed; no conformance/
fuzz campaign/SDK/camera/EXIO. Qualification
`tests/qualification/dng-layout-exact-source-actual-20261017.json`6984B
SHAf44cbccabc3dde2357051b71559789f6d6697a0592746416657eae64c05b1e35.
Usage/scope `doc/dng-layout-exact.md`. ThisdoesNOTyetimplementpixelcomponentforest,
nestedchildplugins orincrementalcache. Those and newremote/mixed-version/fault/
separatelyadmittedcamera receivingqualification remainnext, notexhaustiveprivate-
fieldgating. NoactiveUnisonowner/currentresourcehold/newpayloadgrant.

## Latest hash production successor: opt-in EVP with Make/Dune qualification

Opaqueproductionnativecontext +shared `src/semanticHash_evp.h` nowimplemented.
Defaultplatform unchanged; explicit SEMANTIC_HASH_BACKEND=openssl, optional
absoluteSEMANTIC_OPENSSL_INCLUDE/LIB selectinstalledOpenSSL3 viaMake/Dune.
Noinstallation/download/providerfallback. `doc/hash-backends.md` documentsusage.
Makeheaderdependency +Dunegeneratedflagsexecutable/rules qualified. Fourstock/Ox
Make/Dune OpenSSLbuilds +defaultplatformstockDunebuild PASS. Actualmatrixsession
18121/262249/0/no session; worker17617reaped0/groupclosed/CPU8closed. Eleven
configuration/buildchildren (threeexpectedinvalidconfigexits2), allsettled.
Object/configreadback actual97c5f9/0: fivecontainednmchildren verifiedprivateEVP
symbols+EVP_MD_fetch inselectedobjects, CommonCrypto onlyinplatformobject;
2310capturedsourcehashchecks pass. BothproductionOpenSSLcomponent35420/839063/0
anddefaultplatform77359/5103e3/0 passed8calls each (2expectedOxnegativecompiles).
NoSDK/media/EXIO. Receipt
`tests/qualification/openssl-production-backend-actual-20261017.json`.
Initialharnesswrongsavehelper FileExistsError actuale5f933/1 closed; rawfailure
preserved, correctedfreshmatrix succeeded. This closes the previouslyuncommitted
WIP checkpoint below as opt-in macOS qualification, notLinux/Windows/FIPS/RSS/
scaling/defaultbackendreplacement. Next priority: actualhierarchicalpartial-
knowledge/componenthashbaseline, not more exhaustiveprivatefieldgating.

## Authoritative user steering: gradual nested knowledge, deployable partial coverage

User explicitly directs a hierarchy: standardmetadata/pixels first, MakerNotes
learned piecemeal, plugins inside DNG and nested/community subplugins. They then
confirmed separatepixel+metadatahashing is already a deployment win; incomplete
smallerfields mustNOT globally blockdeployment. SOL.md now contains the normative
design: componenthashforest+fullfilehash, opaqueatoms exact/preserved/identity-
participating, per-operation authority, incrementalrefinement/cachedependency
invalidation/lazyboundedrehash withvalidsnapshotbindings. Cannotderivechildhash
fromparentSHA or silentlyignoreunknownfield. CompleteMakerNotegrammar isNOT a
globaldeploymentgate. Strongerignore/merge/relocation capabilities still require
their scopedcontracts. Existingprofilesunchanged; implementation remainsopen.
Expanded architecture/currentSDEmapping `doc/gradual-camera-understanding.md`.
PhotoRoot consultationrequested userexplicitly viaqueues01a14797-40b2 and
01a14798-408d, updateduserdirection01a1479a-52e7; feedbacknotyetreceivedatwriting.
Do not inventRootagreement or makethisconsultation anewapprovalgate.

## Latest camera ACTUAL: model candidate X2D 100C, nine-byte grant consumed

FreshRootadmissiondc44e5ec (2900B) wasfound/revalidated againstfrozenrequest16pins,
plan/prereqs/interpreter/source8fields/deadline/unusedworkspace, dispatchedONCE.
Actualexec_command a6a4ce/exit0/NOsession, owner15830/worker15831,
START1792202424.824716. Exactlyone9bytepread absolute11440:
583244203130304300 => `X2D 100C`. Workerreaped0/othersabsent/CPU8EXclosed,
source16postpins/epochunchanged. NoSDK/sourcehash/copy/Photooriginal/serialfields.
Rawmodeltext narrowsfamilyinvestigation; vendorheader/privategrammar/reference
closure/semanticeligibility remainFALSE. Source/finalhash hierarchy above means
thisgrammaruncertainty neednotblockindependentlyqualifiedpartialcoverage.
Actualterminal immediatelyqueued01a14796-f48b toreleasecoordination. Seal
`tests/qualification/private-maker-model-actual-20261017.json`2831B
SHA47363cb0893502338e505f253c67ad93d7b7774a8de6dde63f276041f008fded;
workspaceOWNERRETURN2500B SHA72cec0b75180f05cc2adab2ca0634dfa1673050651cefd8dfa1d76ebf715f2c3.
No replay; olderprepared/unadmittedsectionbelow is historicalsameconsumedrun.

Parallel source WIP (not partofcamerarequest16pins): productionhashinternalstate
nowopaque, opt-in UNISON_SEMANTIC_HASH_OPENSSL branch andsharedEVPheader prepared;
defaultCommonCrypto/reference behaviorretained. ActualselectedOpenSSL controls
session35420/839063/0 anddefaultplatform controls77359/5103e3/0 closed; each8
containedcompile/runtimecalls incl2expectedOxnegativecompilations. Theseuse
actualproductionSemanticHash objects+commonheader, stock/Ox15vectors andprivate
domainchecks. No shippingMake/Dunebuild/backenddiscovery/nonApplequalification
yet. Sourcechangescurrentlyuncommitted intentionallyseparatefromuserdesigndoc;
nextgoalturn mustfinish/review/versionthem, notclaimshippedbackend. Noactiveowner.

## Latest camera source successor: nine-byte model-field investigation

Prepared, NOT ADMITTED/DISPATCHED: `doc/private-maker-model-request-v1.json`
5848B SHAc95723a648a0dc87a47dd4c6c61b37afb4a6fc83f15a6f62a1b6c6969ebdd803,
plan951B SHA1fcacc02e95cf4e97f029392b9b5b62c796b9998c53383bf31527a8fb9e36411.
Workspace `/private/tmp/unison-private-maker-model-f0c6585afc364ce984c66bba92f1330f`
and `/private/tmp/unison-private-maker-model-admission-v1.json` absent atfreeze.
Exact16executionpins/4prerequisites/qualifiedPython frozen; source8fieldlstat
unchanged withoutpayloadread. One9bytepread absolute11440 (candidateASCII tag21),
not the earlier34byte prospective set; tags96/97 remain unread. Raw9bytes/hex
retained, invalidtext notdecoded; string alone neither identifiesvendor nor
provesprivategrammar. NoSDK/sourcehash/copy/Photooriginal/serial-field reads.
Newtarget private-maker-model has no CPU-only route. IO→Unison00..07, explicit
inherited9FD metadata, worker10s/parent60s observation, unknownretainsno broadkill.
Qualifiedfinallyclose preservesreadfailure+alluncertainidentities/no numericretry;
parent exactresult/actualPID/readbound audit+freshsourceepoch beforeclose.

Actual41syntheticcontrols686520/0/no session and freshdisposable9FD lifecycle
1fffe8/0/no session passed/normalworkerreaped0/groupclosed/disposablewhole-set
reacquired. Exactsource/argv checked_io_request also passed an explicit inert
metadata doublee0a407/0, NOT a realadmission/lock. Source readiness receipt
`tests/qualification/private-maker-model-ready-20261017.json`.
Initialdisposablelifecycle child14181 failedbeforefieldread because shared_binding
targetallowlist omittednewtarget; retainedidle14180 independently source-bound
stopped afterSIGTERMignoredbyretain_forever, scopedSIGKILL14180only. Actualouter
session92188/51d72a/247, direct14180wait-9/groupclosed/CPU8closed. Originalinner
workerwait4 NOTclaimed; rawerror/originalsources/recoverypreconditions preserved.
Correctedallowlist qualifiedbyfreshlifecycle, not replay. First7readercontrols
8aa6e3/0 and intermediate41controls871175/0 alsoclosed; no retainedresources.
The shared_dispatch/shared_binding source successors postdate consumedSDKV2;
its181postpins describe its actualrun, not a new current-source match.

## Latest actual: unchanged-file SDK validation and private camera coverage

All-scanned SDK V2 is CONSUMED_ACTUAL_PASS_CLOSED, not pending. Admission
8dabb077 / workspace `/private/tmp/u-asv-ca5ec3ffcbff` executed once after fresh
guards. Exact own runtime item_completed event at2026-10-17T01:45:04.471Z,
CommandExecution exec-dd42cac5-40a9-47f6-b703-0d1bbd41eae3/process98564,
statuscompleted/exit0 supplies actual parent terminal (not ps or markers).
Owner11083/worker11084, workerreaped0/groupothersabsent/CPU8+EXglobalclosed.
Four CLI/four SDK calls: stock/Ox baseline then all-scanned unchanged validation
on each endpoint; all raw-digestvalid/decodeSUCCESS/errors0/warnings0.
Independent pure parent audit reparsed four raw proxy receipts, exact commands,
helper/path/group joins;181postpins unchanged. Seal
`tests/qualification/all-scanned-sdk-v2-actual-20261017.json` binds10artifacts,
including recovered exact runtime-event source offset/lineSHA. Root notified
queue01a1478b-5406 promptly after terminal recovery. No replay or semantic/pixel/
corpus/timing claim; do not reopen the consumed grant. RequestV1 stays withdrawn.

Camera grammar remains the central open semantic gap. New pure saved-record
analysis (`doc/private-maker-coverage.md`) proves only declared spatial coverage:
33entries/17inline/16outlined, no range overlap,6551/6556bytes represented,
five unclassified one-byte gaps. Seven UNDEFINED values occupy5939bytes;
their contents and inline pointer semantics remain unknown. Seven original
synthetic controls actual3ca2ea/0/no session, worker/group/CPU8closed. An earlier
misplaced -B dispatcher argument refused before child/token entry0a7cc2/1.
No DNG reread. Three candidate ASCII fields total34prospectivebytes for a future
identity investigation, **not** a new read grant or vendor recognition. No
production private allowlist/profile change. Coverage receipt
`tests/qualification/private-maker-coverage-actual-20261017.json`.

Independent maintained-hash component progress: isolated OpenSSL3 EVP candidate
in `tools/portable-hash/` passed stock/Ox generated vectors, four private domain
contexts, GC/state/failure cleanup and expected Ox portability refusals. Final
actualsession29240/734d79/0/no session; all8containedcalls/outerCPU8closed.
InstalledOpenSSL3.6.4/macOS only, zeroSDK/media; not production selected and not
Linux/Windows qualification. Earlier import/Ctestcompiler failures preserved.
Receipt `tests/qualification/portable-evp-component-actual-20261017.json` and
component README state remaining production Make/Dune/backend/platform work.

## Latest transport correction and real peer compatibility

SDK requestv1 f06a74ea is WITHDRAWN UNSTARTED (own attestation; no SDK target
dispatch). Disposition `doc/all-scanned-sdk-request-v1-withdrawn.json` preserves
original request/plan bytes. Root notices queues01a14778-4910 and01a14779-90d9.
No crossed old grant may be dispatched. Actual empty-root testing found two
gaps missed by modeled fixtures: native server receipts do not contain their
own group-leader fence (server inherits proxy group), and sequential phases
reused a retained socket pathname. Both are corrected WITHOUT SDK/media reads.

Proxy now observes native PID/PGID and supervisor PID/PGID before native wait4.
`all_scanned_sdk_groups.py` joins that binding to strict supervisor-group census
before the GROUP LEADER is reaped. Native server is explicitly not group leader;
no fictional native-own-group fields. Baseline/validate use separate socket names.
Current90 inert controls PASS/CLOSED. Four actual current/older-peer empty-root
calls proved exact capability refusal when required and ordinary off success
on stock/Ox; actualbatch48099/663fe5/1 retained the first socket fixture failure,
freshbatch97858/236d74/0 passed. Four ACTUAL current Invoker empty-root calls
also passed using an inert non-executable SDK sentinel, actual29390/973a1f/0.
All client/supervisor/native groups/canonicalCPU8 closed; no canonicalEXIO or SDK.
Receipt `tests/qualification/native-proxy-group-actual-20261017.json`.

First probe wrongly expected native-own-group keys and retained idle6233 despite
actual client6249reaped3/supervisor6248reaped0/native6256reaped0 and strict proxy
group closure. Source-bound empty/no-SDK recovery stopped only idle6233; actual
18796/4fd8fb/247, outerchild6233wait-9/groupclosed/CPU8closed. Runtime nativePGID
was NOT claimed for that first probe. Recovery and exact old script archived;
second socket-reuse failure was ordinary known closed, no retained resource.

FRESH successor request `doc/all-scanned-sdk-request-v2.json`
SHA75d3b9bd03a06a06caf41c5c216ee5dad1ccdc95d5b9138d245fc5316617b03e;
plan `doc/all-scanned-sdk-plan-v2.json`
SHAa89b6c1f9a530a282ac749358aef79016b22fb9397400671e8d29380a705de81.
181sources/6prereqs, metadata checked_plan PASS; borrowed8fields unchanged with
zero payload opened. Workspace `/private/tmp/u-asv-ca5ec3ffcbff`, admission
`/private/tmp/unison-all-scanned-sdk-admission-v2-ca5ec3ffcbff.json` absent atprep.
Same finite4CLI/4singleSDK/8CPU+EXglobal, no18borrow. This request is NOT a grant;
fresh Root admission/deadline and all source/workspace guards remain mandatory.
No actual all-scanned SDK run has occurred. Old-peer loopback negotiation does
not prove arbitrary SSH/network/platform interoperability or close the full goal.
V2 source/scheduling request queued to Photo Root as
`01a14780-0c96-7061-9d1d-d68746774a9c` after pushing91e9658.181pins,
checked_plan/borrowed metadata and absent workspace/admission revalidated first.
This queue grants nothing; wait a fresh exact Root admission and deadline.

## Latest checkpoint — private helper input observations

Current007 stock/Ox Make AND Dune build-only PASS/CLOSED, actual21013/826fd9/0/no
session. Current-object endpoint/unchanged/scan controls plus inert SDK controls
PASS/CLOSED, actual29114/f94d20/0/no session. Four contained controller groups
and CPU8 sets closed;14nested compiler/test calls and4actual original fake
helpers reaped/groupclosed. All4 owner-input records bind candidate SHA/size,
actual helper PID, private stage path and endpoint owner PID. Separate49 inert
SDK controls passed. Independently checked2451source hashes and1946compiled
artifact hashes INCLUDING repeated checks. Receipt:
`tests/qualification/all-scanned-input-current-actual-20261017.json`.
Prior006 build/current-source qualification below is retained historical evidence.

Production `validation-input` debug adds a separate bounded hex pathname record
after supervised execution returns; normal behavior, wire format and existing
process/group framing unchanged. It records the owner context's candidate and
borrowed-output provenance, not kernel argv tracing or hostile sandbox authority.
`all_scanned_sdk_paths.py` rejects absent/duplicate paths, wrong helper/owner/hash,
original-root paths, unavailable/odd/NUL/dot components and unborrowed inputs.
Future SDK plan explicitly enables this opt-in diagnostic; parent/worker join it.
No SDK/retainedcamera/EXIO/nativeUI was invoked by this turn. Future SDK executor,
admission/prefix/FD verification join and real remote run still outstanding.

Outer metadata/failed-prefix checkpoint: `all_scanned_sdk_boundary.py` validates
the exact finite packet, qualified interpreter/compiler labels, authenticated
build/tool manifests, copied transport pins and readonly private source metadata.
`checked_plan` rechecks each captured production source hash; executable hashes
are deliberately left for after IO acquisition. Its bounded document reader uses
the qualified close carrier, including original parse failure + uncertain close.
`all_scanned_sdk_prefix.py` independently audits known failed prefixes without
inventing helper absence or parent/FD closure; contradictory baseline input
records and incomplete helper pairs refuse. Neither function grants admission.
Fifty-nine current inert controls actualb4a9a6/0/no session passed, child/group
and CPU8 closed; no SDK/CLI/camera/EXIO. Receipt
`tests/qualification/all-scanned-sdk-boundary-actual-20261017.json`.
The dispatcher/CLI route, inherited9FD controls and fresh parent verification join
are still NOT wired. Next implement those before freezing a runtime request;
no actual all-scanned SDK admission exists and no old grant may be reused.

One-use entry/dispatcher is NOW wired as `all-scanned-sdk-validate` through
`all_scanned_sdk_entry.py`. No CPU-only route. Exact packet/admission/argv,
existing EXglobal→CPU00..07, inherited9FD guard, post-IO executable hashes,
worker/helper/proxy audits and fresh complete-root verification precede grant
closure. Observation expiry retains the live SDK coordinator; no broad kill.
Source checks and bounded result/proxy reads use qualified close uncertainty.
The shared CPU closer/readers now preserve combined rollback+directory close
identities, original cause and known still-held successful sets; IO preserves
both precise outer roles and upstream pre-close observations.

Latest88 controls actuald787b5/0/no session passed; actual disposable inherited
boundary dc9f5c/0/no session passed with2real Python children, both reaped7 and
groups closed;9FD accepted to deliberate pre-SDK refusal,8FD refused earlier.
All canonical Unison8 outer groups/tokens closed; canonical EXglobal NOT taken.
Receipt `tests/qualification/all-scanned-sdk-entry-actual-20261017.json`.
Preserved failures: first actual launcher used wrong sys.argv offsets, failed
before document/guard/SDK, and retained idle controller3810. Source/census bound
recovery stopped ONLY that controller; actualouter0a6f94/247/no session, its
child3810 wait-9/groupclosed/CPU8closed. Originalinner3811 wait4 NOT claimed.
Exact old launcher reconstructed and SHA-verified against START before archiving.
Named argparse correction passed fresh002/003. One common-pool role-label
regression actual98adf0/1 closed; corrected carrier preserves upstream identity
plus precise outer IO role and current88 tests pass. No SDK/media/clone executed.

Fresh immutable runtime request prepared: `doc/all-scanned-sdk-request-v1.json`
SHAf06a74ea8f0ba22f5b1217507906a44bcb5eecf4fce175332e835943baecc26f;
plan `doc/all-scanned-sdk-plan-v1.json`
SHA983fe658d65601fcdd02acbc947945d8671124f4c47178a8d824b5717ab3e50d.
179source pins/6prerequisites; metadata checked_plan passed and borrowed8fields
unchanged without source payload read. Workspace `/private/tmp/u-asv-30d16e0d4925`
and admission `/private/tmp/unison-all-scanned-sdk-admission-30d16e0d4925.json`
were absent at preparation. Request is NOT admission: wait exact fresh Root
grant/deadline then recheck allpins/workspace and dispatchONCE, no oldslotreuse.
Scope4CLI/4singleSDK, two clone-only equal-root pairs, off baseline then unchanged
all-scanned require;16GiB declaredlogicalnotcap,600s observation/unknownretain,
Unison8+EXglobal/no18borrow. No semantic/pixel/physical sharing/throughput claim.
Exact readiness/source-review request sent to Photo Root queue
`01a14774-94d7-78c2-b6ac-8cf4cd00ab25` after pushingc633902; prequeue179source
pins/checked_plan/source metadata and absent workspace/admission revalidated.
This queue is a REQUEST, not a grant or resource hold. Continue independent source
work while awaiting fresh exact scheduling; do not reuse any historical slot.

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

Next-step source proposal now exists: `tests/all_scanned_sdk_plan.py` and
`doc/all-scanned-sdk-qualification.md`. Two calls/compiler establish an off
baseline then require/all-scanned unchanged validation across the proxy's real
remote-process boundary; four SDK calls total are proposed, NOT executed.
Three pure planner controls passed under Unison8; actual680b9e/exit0/no session,
child93067 reaped0/groupothersabsent and CPU8 closed. No EXIO or SDK was taken.
Receipt: `tests/qualification/all-scanned-sdk-plan-actual-20261017.json`.
The first control launcher omitted its output directory and retained idle CPU
ownership before child construction; source-order/no-child audit preceded exact
owner92929 recovery, actual89e146/137/no session. No worker wait4 is claimed for
that pre-child failure. Fresh002 controls passed; failure evidence is preserved.
Executor/admission/prefix auditor and fresh Root scheduling remain outstanding.

Transport/helper audit checkpoint: `all_scanned_sdk_transport.py` now fences
artifacts and one-use phase intent/outcome ordering; unknown unreturned calls
cannot forge finish. `all_scanned_sdk_audit.py` independently joins the exact
client+server helper pairs and SDK framing while withholding no-transfer,
private-path and resource-release authority. Twelve inert controls actual
8cea50/0/no session passed; child/group/CPU8 closed, no SDK/CLI/EXIO/media.
Receipt `tests/qualification/all-scanned-sdk-transport-actual-20261017.json`.
First batch import-path failure is preserved as actualc03fdf/1/no session with
known child/group/tokens closed; fresh002 fixed imports and003 added returned
failure ordering. Still implement aggregate executor, cloned-root preparation,
no-op/path-isolation and attempted-prefix joins before fresh runtime request.

Complete-call parent join is now implemented in `all_scanned_sdk_parent.py`:
strict four-call compiler/phase order, exact argv/server flags/raw proxy binding,
transport lifetimes, both-endpoint SDK receipts and exact unchanged UI status.
It does not authenticate records, freshly inspect roots, prove helper path
isolation or authorize FD release. Partial results remain refused. The common
journal adds a separate validation profile without relaxing sync profile rules.
Thirty inert controls including journal regressions actual120cc2/0/no session
passed; child94218 reaped0/groupothersabsent/CPU8 closed, no CLI/SDK/EXIO/media.
Receipt `tests/qualification/all-scanned-sdk-parent-actual-20261017.json`.
Next remains aggregate/root-preparation/path evidence and failed-prefix ownership,
then fresh exact runtime request. No actual SDK admission exists for this feature.

Caller-admitted aggregate kernel and clone-only pair preparation now implemented
in `all_scanned_sdk_worker.py` / `all_scanned_sdk_prepare.py`. Source metadata
fenced/no source hash; distinct clones only/no overwrite/copy fallback; clone
hashes checked before transport. Worker records helper/CLI settlement before
verdicts and preserves known failed prefixes separately from retained uncertainty.
Missing helper/group/outcome and nested uncertain-close cases retain ownership;
no later call starts. Native-clone runtime is NOT qualified for this new path.
Forty current inert controls actuala55d9e/0/no session passed, child/group/CPU8
closed. Receipt `tests/qualification/all-scanned-sdk-worker-actual-20261017.json`.
Only original tiny files/injected clone and modeled SDK/proxy frames were used;
no CLI/SDK/EXIO/retained camera access. Earlier001/002 counted imported parent
tests twice;003 removed duplication;004 adds strict server-group uncertainty.
Still implement outer CLI/admission, fresh replica verification, private-stage
path evidence and independently authenticated failed-prefix/FD join; no runtime
request/grant exists yet. Full goal remains active/incomplete.

Fresh pair verification gap closed in the worker: `all_scanned_sdk_verify.py`
is mandatory, no caller-supplied Boolean callback. Preparation now captures
directory epochs; verification joins exact single-file rosters, full file/dir
epochs, distinct inodes, admitted source SHA/size, both hashes and final cross-pair
binding checks. It opens only disposable roots and preserves uncertain-close
carriers; no destructive cleanup. Worker saves initial plus both post-phase proofs.
Forty-six controls actual18b483/0/no session passed; child95780 reaped0/groupabsent,
CPU8 closed. Composition uses real tiny files/injected clone/real verifier six
times with modeled transport/SDK. Receipt
`tests/qualification/all-scanned-sdk-verify-actual-20261017.json`.
No CLI/SDK/nativeclone/EXIO/retainedmedia. Outer executor/admission, authenticated
prefix/verification join, private-stage pathname evidence and fresh exact runtime
request remain next. Parent audit still withholds fresh-byte/release authority.


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


## Perl ExifTool baseline upgraded to 13.59

User requested the same Perl13.59 baseline used by the separate exiftool-rs /
dng-compare work. The current mixed-validation dependency verifier now selects
the private versioned installation recorded in
`doc/exiftool-13.59-installation-v1.json`, and exact246-library-file inventory
`doc/mixed-exiftool-package-inventory-v2.json`. Shared/usr/local/bin/exiftool
and the old13.10 package are untouched. Historical V1 plans, inventories,
source reviews and actual receipts remain unchanged; do not replay them or
relabel13.10 evidence as13.59.

Actual final controls1e11d4/exit0/no session passed16 pure inventory/plan/audit
tests plus two direct ExifTool calls: version13.59 and readonly generated Unicode
XMP with the exact mixed-probe argv. Source/fixture/package fences and all
contained groups settled, CPU8 closed. Evidence:
`tests/qualification/exiftool-13.59-upgrade-v2-actual-20261017.json`.
First upgrade controls95afc8/0 also passed; final successor adds exact executable
path rejection. No SDK, media/photo payload, mixed native rerun or semantic/pixel
qualification. Future mixed runs require current successor source/binary pins
and fresh existing IO scheduling. exiftool-rs itself remains deferred until the
user's extensions and dng-compare integration are ready.


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


**LATEST ACTUAL — slice V1 CONSUMED/CLOSED:** fresh Root admission
/private/tmp/unison-private-maker-slice-admission-v1.json SHA7d914319 was found,
request45c2b707/plan/13sources/9prereqs/interpreter/sourceepoch/deadline/absent
workspace revalidated, executed ONCE. Actual initialexec_command d8fe2f/exit0/
NO session, parent17547/worker17548. Worker reaped0/othersabsent; CPU8+EXglobal
closed/allsourcepins unchanged. Exactly402B requested/received in2preads,33
candidate entries, nextIFDzero; all declared out-of-line extents fit6556B.
No pointed values/inline values/vendor recognition/private closure/semantic
eligibility claim. Source exact8fields unchanged; no source hash/newclone/SDK.
Actual terminal immediately queued01a146d8-8baf before sealing. Saved-result
independent audit rechecked13pins/epoch/recordedcanonical9inodes/unresolvedempty,
no payloadreread. Seal tests/qualification/private-maker-slice-v1-actual-20261017
4213B SHA7b012251; OWNERRETURN3673B SHAf8257b68 plus9directartifacts in
/private/tmp/unison-private-maker-slice-13f46b93c0ed4271af7cc389113808aa.
Sealed notice01a146d9-2eed. Metadata-only seal construction TypeError19bf7b/1
(duplicate schema keyword after OWNERRETURN saved) preserved/corrected; no
runtime/audit/resources repeated. No currenthold; old prepared/pending notes
below are historical, do not replay. Next: vendor-specific grammar/reference
closure source work from saved geometry, then separately qualified profile.
Independent follow-up checked DNG1.7.1 page41: MakerNoteSafety describes EXIF
MakerNote preservation and does not supply private pointer grammar or identify
the MakN vendor. Added focused production-linked tests/semantic/private_safety.ml
and serial stock/Ox runner; four scalar baselines/eight private refusals per
compiler PASS (both profiles/bothorders, explicit safe flag1). Actualsession
30095/5049a3/0, four compiler/test groups plusouter18617 reaped0; CPU8 closed.
Receipt private-safety-actual-20261017.json. No SDK/media/fuzz/production edits.
Pinned MakerNotes Hasselblad branch is only a special-base/unknown-table source
example; do NOT identify the sample from its tag-shape resemblance.
Root actual slice closure and sealed adoption now read/rehashed into
private-maker-slice-v1-root-adoption-20261017.json: actuald8fe2f/0 was adopted
from our owner report, not Root tool polling; Root photoIoWaitActiveFALSE,
33entry/402byte geometry only, no newhold/replay/payload.
Independent M4 work traced missing all-scanned validation: synchronous
Update.findLocal +watcher/directory skips +NoUpdates omission prevent a simple
post-filter hook. Existing CandidateValidation assumes private received stages;
SemanticWorkers has no isolated snapshot job. Source hashes/findings recorded
in all-scanned-source-audit-20261017.json and concrete integration plan in
doc/all-scanned-validation-implementation.md. No new preference or production
feature exposed. Next implementation work: admitted cancel-aware isolated
snapshot worker API using existing clone adapter, then exact scan-selected
coverage and asynchronous endpoint wiring. Keep default received/off/no-op
behavior and originals untouched; no helper may receive a live unchanged file.
This is independent of still-open MakN vendor/reference grammar.
Snapshot kernel implementation checkpoint: src/validationSnapshot.{ml,mli}
now performs borrowed-FD isolated materialization using an injected existing
WholeFileClone adapter, strict no-effect-decline fallback, <=64KiB cancel-aware
copy/short-write+EINTR handling, complete source/output SHA comparison and
cooperative source metadata fences. Budget/alias/nonempty guards precede effects;
no path/create/unlink/close/publication. Caller retains exclusive output/name
ownership and stronger epoch fences; OCaml stat timestamps are not native-ns
attestation. That kernel-only checkpoint is superseded by worker integration
below; all-scanned scan/staging-owner integration is still pending.
Stock/Ox standalone component controls passed (six exact sizes incl0/64KiB
boundaries, budget/alias/nonempty refusal, native exception+typed failure,
correct simulated success and wrong-byte success rejection, cancellation).
Actualsession8225/fd198f/0, outer20205 and four contained calls reaped0/groups
absent, canonicalCPU8 closed. Receipt validation-snapshot-kernel-v2-actual-20261017
(preserves prior first-pass receipt). No nativeclone/SDK/media/fullCLI claims.
Typed worker integration now implemented: SemanticWorkers.snapshot duplicates
outputFD, admits atomic source/destination filesystem-key union beforeCPU,
retains bothduplicates through worker settlement and maps Snapshotted response.
Uses existing unison_clone_file_status nativeprimitive/WholeFileClone decoder,
not a second clone engine. Added portable WholeFileClone/ValidationSnapshot
interfaces and Make/Dune preprocessor wiring; Safe.spawn checked Ox builds pass.
FullMake stock001/244e05/0 +Ox001/4d41bf/0 and Dune stock15d6d4/0+Ox56032a/0
closed. First stock prefix error e9bda0/2 was preentry/no resources; corrected
bin prefix then actualbuilt. Final telemetry fix excludes Snapshot from outer
reader0byte samples; digest observer still131111B. Rebuilt currentMake002
stock701971/0+Ox1da355/0 bothclosed; earlierDune pair covers pre-fix graph only.
Allsix build-only slots closedCPU8/no executable selftest or SDK invocation.
Current production-object stock/Ox worker controls passed: exact3copies each of
131111B, budget/aliasrefusal, CPUqueuedcancel, observers and emptyIO/CPU/worker
ledgers. Allsix nativeFDadapter results declined onmacOS; ordinarycopiedbytes
verified, no APFSsharing claim. Finalactualsession63473/c1af41/0, outer28224+four
compiler/test groups reaped0/CPU8 closed. Receipts validation-snapshot-workers-
v2-actual-20261017 and validation-snapshot-builds-actual-20261017; earlier worker
receipt preserved. No photos/SDK/catalog/publication/nativeUI.
Next concrete implementation: private staging owner, name/sourcefences and
bounded outer admission; then scan-selected coverage and negotiated scope.
Worker close-error/platform fault limits remain explicit; no all-scannedfeature
or full-goal completion is inferred.
Private stage owner now implemented in src/validationStage.{ml,mli}: owned0700
parent, readonlysource name/FD epoch fence (FileObservation native onMac, exact
unsupported-platformENOSYS fallback only), exclusive0600stage, path identity
checks and replacement-preserving one-attempt retirement. Close uncertainty
retains opaqueowner/preclosefacts/originalfailure; getters cannot downgrade it,
no numericclose/probe retries. Caller mustretain outer admission oncarrier.
Standalone stock/Ox7groups passed: normalcopy+private mutation cleanup, source/
stage rebinds, preentry, O_EXCLcollision, external source edit, intentional
borrow-precondition EBADF+numeric-slot reuse/no retry. It is not a genuine
ambiguousOSclose or sameUIDsandbox/OOM qualification. Actualsession18118/5cfea1/0,
outer30366+4containedcompiler/test groups reaped0, canonicalCPU8closed.
Receipt validation-stage-owner-v2-actual-20261017.json, priorv1preserved. No
SDK/photo/nativeclone/Main/cache/publish calls. No enabled all-scannedpath.
That owner-only checkpoint is superseded: ValidationStageWork.run now awaits
actual snapshot work, validates only privatepath via settled callback, rehashes
stage against original snapshot SHA and rechecks source/name fences before
retire. Cancellation never closes sleeping callback borrowers. Cleanupunknown
stronglyrootsopaqueowner and returns permanentlypending work, retaining caller
admission; even throwingdiagnostics cannot release it. No numericFDretry or
callerassertedrecovery. Outer admission is a caller precondition; wrapper does
not selectformats/scans or enableall-scanned.
Both owner modules nowexplicitlyMakewired; Dune standard module discovery
alreadycovers them. Current fullMake stockstage003 actual60053/7cfbba/0 and
Oxstage003 actual69129/c42aad/0 closed, all currentproductionpinsmatch. Receipt
validation-stage-work-builds-actual-20261017.json.
Focused production-object controls initialstockcompile failed Lwt.state API
(embeddedLwt usespoll); actual9a7e58/1/compiler34415reaped2/controller34414reaped1/
CPU8closed preserved in validation-stage-work-actual-20261017.json. No runtime
case executed there. Fixedcontrol only; freshstock/Ox bothPASS actual76318/
f66e06/0, outer34811+4compile/test groups reaped0/CPU8closed. Receipt
validation-stage-work-v2-actual-20261017.json. Cases: success, callbackfailure,
private mutation rejection, sleeping-callback cancellation retaining stage+
admission untilsettled, injectedcleanupEBADF+throwingdiagnostic retains gate.
Unknowncase symbolic admission intentionally1untilactualtestprocessexit, NOT
callbacksettled/creditrelease; all domainworkers joined. No SDK/photos/scan/UI.
Next: CandidateValidation selected-companion/outeradmission entry; held readonly
recognition before expensive snapshots avoids failing huge non-DNG on sizecap.
Then actual scan-selected coverage and negotiatedscope. all-scanned stillOFF/
unavailable. Fullgoal remainsactive; no new runtimeIO/SDK grant inferred.




**Previous mixed runtime (do not replay):** mixedV1 admission00d8de55dd7548b54ee47c4ce9d159d2dacb95285075410d04e98505da399c69
was discovered fresh, exact request3e76df16/plan0fd5d23f/326sources/9prereqs/
interpreter/deadline/unusedworkspace revalidated, then dispatched ONCE. Owning
session59209 initial87a8e5 terminalcedf13/exit0/NO running session; parent8085,
worker8086 actuallyreaped0/othergroupmembersabsent-before-reap. Two stock/Ox
probes/2actualSDKsingle/2readonlyExifTool/32hash tasks passed. Both SDK frames
rawdigestvalid/decodeSUCCESS/errors0/**warnings4 each retained**. Parent source/
disposableclone byte checks and backend2192MiB+64credits passed; CPU8+EXglobal
closed, all326sourcepostpins/borrowed8field epoch unchanged. Actual terminal
sent immediately in Rootqueue01a146c4-af06, no reportsealing resourcehold.
Sealed tests/qualification/mixed-validation-v1-actual-20261017.json63631B
SHAa828f2166927fc5f97b60162850f9f45931973b87ff128a1255b2fb54bdcf20e;
OWNERRETURN3800B SHAe4f15f69d2a31e96f13a2aaa35b58794d84718089f887d5b6e8228039ee4fe24
under /private/tmp/unison-mixed-native-v1-e3d4f770baf243db915be0b3fdc0be9d.
Rawjournal/ownerterminal/parentexit/independentpostaudit+10directpins preserved.
No camera/pixels/corpus/production, quietthroughput/CPUcomputeoverlap/hardcaps
inference. Admission CONSUMED, no retry/successor. Root independent adoption
now verified in mixed-validation-v1-root-adoption-20261017.json: Rootreceipt
6811B SHA4ae4cfbc49720ea5e32a728a67d77ffb7a7e7266182e946938dda908d757bdc8,
actualterminal/worker/resultpins rebound,326sources/raw2probeaudit accepted,
PhotoIOwaitFALSE/no payloadhash byRoot. No currentUnisonresourcehold. Historical pending notes below
do not authorize another dispatch or claim fresh probes remain unexecuted.

The full SOL.md implementation goal is **active and incomplete**. The user
requested this handoff because usage limits are approaching, and requested that
it stay updated. Do not restart completed work or reduce the objective to the
next test. Do not claim completion from a green build, narrow fixture, or receipt.

**Current independent work after mixed acceptance:** pure
tests/private_maker_shape.py candidate geometry diagnostic added (no production
profile change). Saved framing V2 has one6556B payload/originaloffset1404; only
that JSON was read, no new retained payload. New reader bounds classic candidate
IFD tables to256entries/3078requestedbytes, emits tags/types/counts/extent geometry
without inlinevalues/pointedreads, reports outside-payload references. Maker
recognition/private-reference closure/semanticeligibility stay FALSE always.
Five authored-byte controls passed, child10346 reaped0/group absent/CPU8 closed,
actual85eed6/0/no session; receipt private-maker-shape-source-actual-20261017.
The callable slice reader tests/private_maker_slice.py is now implemented:
NOFOLLOW read-only open, exact eight-field inode/name epoch fences before/after
each payload-relative pread, <=3078 requested bytes, sanitized shape output,
and qualified uncertain-close carrier. Five generated-fixture controls passed
(child11747 reaped0/group absent, CPU8 closed; actual2a33db/0/no session).
Receipt: tests/qualification/private-maker-slice-source-actual-20261017.json.
No retained source was opened. Pure tests/private_maker_plan.py now binds the
exact historical clone eight-field identity, payload10990/6556/originalbase1404,
Unison8/EXglobal,10s worker and explicit false semantic/SDK/hash/pointed-read
flags. Exact nine-word worker argv was specified at that checkpoint; the executor
and shared dispatcher route are now implemented as described below. No new
retained-input admission/request has been published. Four plan
controls plus five slice controls passed (child12267 reaped0/group absent/CPU8
closed; owning59b0b6/0). Receipt private-maker-plan-source-actual-20261017.json.
Independent tests/private_maker_audit.py now checks exact report schemas,
sanitized decline reasons, count/table-only read ranges, exact accounting,
TIFF-type extent arithmetic, no inline values and false safety claims. It does
not authenticate payload bytes or confer process/FD release authority. Five
audit controls plus nine plan/slice controls passed, including the exact256-entry
3078-byte boundary; child12640 reaped0/group absent/CPU8 closed, actuald927fb/0.
Receipt private-maker-audit-source-actual-20261017.json.
The tests/private_maker_execute.py worker and manual private-maker-slice route
now require exact shared8+EXglobal admission, frozen plan, actual START parent/
worker IDs and inherited nine canonical descriptor metadata. No external children
are started. Metadata/source/result descriptor closes use the qualified carrier;
uncertainty retains the actual worker, never writes an ordinary failed result.
Parent waits without deadline kill, audits exact worker result and source epoch
before settlement, checks exit consistency, then closes CPU/IO. Report ceiling
256KiB accommodates256sanitized entries; plan/START metadata stays64KiB.
36 disposable/injected controls passed, including combined JSONparse+close
uncertainty, no retry, failed worker, success/audit/reap/release, live retention
and complete/failed-exit contradiction. Final child14610 reaped0/group absent/
CPU8 closed, actual12cea2/0. No canonicalIO acquisition or retained input read.
Receipts private-maker-entry-{source,parent-source,final-source}-actual-20261017
preserve the three progressive source checks; final is current.
Real integrated disposable lifecycle qualification now PASSED: four worker
processes for candidate, parser decline, stale source and injected close
uncertainty. Unknown worker remained actually live with all nine inner locks
busy, no RESULT/SHARED-CLOSED; control-specific acknowledged exit recovered
without any numeric close retry. All worker groups reaped; all inner locks
reacquired; canonical Unison8 outer lease closed. Also fixed plan-close
uncertainty before acquisition to retain the parent; manual argv construction
is now pure and does not open plan metadata. Final38 controls plus4realworkers
passed, actualsession42242/ff73f1/0/no session, children16661/16663reaped0.
Receipt private-maker-integrated-ready-actual-20261017.json includes before/after
source pins; prior lifecycle receipt preserved. No canonicalIO/media reads.
Fresh metadata-only retained clone lstat still equals exact eight-field epoch.
Frozen doc/private-maker-slice-plan-v1.json SHAcd734403 and request-v1.json
now specify one at-most3078B/two-pread run, Unison8+EXglobal,10s worker/60s
parent observation (not hard kill),13executionpins+9prereqs. Workspace
/private/tmp/unison-private-maker-slice-13f46b93c0ed4271af7cc389113808aa and
/private/tmp/unison-private-maker-slice-admission-v1.json remain absent.
No grant or dispatch inferred. Exact request45c2b707/7040B was queued to Photo
01a146d6-31b5; branch pushed throughc7976eb. Pending review is not a resource
hold. Source-only follow-up rehashed the pinned ExifTool13.10 DNG/MakerNotes/Exif
modules against the existing package inventory: vendor handler selection,
LocateIFD and conditional base rules prevent treating a generic in-bounds
classic table as private closure. Receipt private-makn-source-review-20261017
and doc/private-makn-source-review.md capture the next explicit vendor grammar/
reference/overlap requirements. No ExifTool execution/media read, no frozen
request changes. milestone-next-work lead and acceptance row12 now reflect the
completed mixed actual result instead of stale pending status.
That source review/grant subsequently arrived and the slice executed once as
recorded at the top; no pending slice scheduling remains. Continue independent
vendor grammar/reference source work; require fresh coordination for any new
payload scope, then investigate a vendor-specific reference contract from
actual shape evidence. No camera/private input read/admission exists for this
new diagnostic; old grants remain consumed. doc/dng-private-data-next-profile.md
updated. DraftPR2 contains current follow-up; full M1/M4/M6 scope remains open.

Original objective: implement SOL.md by reusing current upstream cloning,
adding general APFS receiver-basis clone updates, DNG semantic extensions/SDE,
optional per-file Adobe validation, and qualified OxCaml coordinated workers;
deliver tested, reviewable code while preserving photos and existing workflows.

**Latest actual milestone:** SDK receiving comparison V1 PASSED/CLOSED ONCE.
Actual owning-tool36282/f540b7 -> terminal0f8d61/exit0/no session, owner87016 /
worker87017. Admissionac55fe28 consumed; never replay. All24CLI/48qualifiedSDK
helpers independently reparsed with raw proxy/client/server/supervisor/pump and
worker/group settlement. All172 execution source pins and borrowed8field epochs
matched; unresolved[]. CPU00..07+EXglobal closed. Actualterminal and post-audit
queued to Photo01a14685-697f and01a14685-fd19; independent Root actual closure is adopted below; no sealing/resource hold. Sealed actual return:
`tests/qualification/sdk-receiving-comparison-v1-actual-20261016.json`.

Report `bench/sync/results/sdk-receiving-comparison-v1-20261016/` preserves all
24ordered rows (4warmups/20measured). Five measured samples/configuration:
stock endpoint1/3 median3.384026/2.503401s; Ox3.364461/2.476375s, descriptive
ratios1.3518/1.3586. SDK protocols all rawdigestvalid/decodeSUCCESS/errors0,
FOUR warnings each retained. Generated-input end-to-end receiving only, includes
hash/transport/staging/startup/SDK; not quiet, causal SDK speedup, pixel/corpus or
production qualification. Offline report ownerd1500e/0 also closed.

**Immediate next task:** continue remaining SOL acceptance/resource/corpus/platform
requirements; Root independent actual comparison closure is adopted below. Do not reconstruct this completed run from old absent snapshots.

**Report preparation:** `bench/report_sdk_receiving_comparison.py` now independently
re-audits comparison receipts before statistics. It preserves exact sample order
and failed prefixes, withholds ratios on incomplete cohorts, and reads stable
owned JSON receipts up to16MiB with qualified close-uncertainty propagation.
Initial five synthetic/disposable controls passed under canonical Unison00..07:
`tests/qualification/sdk-receiving-comparison-report-controls-20261016.json`,
actual owning-tool terminal `d7cc17/exit0/no session`, child85163 reaped0 and
other group members absent before reap; all CPU descriptors closed. Zero SDK,
CLI, retained-input payload, or canonical IO calls. These report-only files are
outside the frozen172-source execution closure. At that preparation checkpoint SDK comparison admission was still pending;
the later actual consumed run is recorded above. These tests grant no execution.

Report successor now exposes callable `main(argv)` and qualifies the complete
24-call synthetic input-to-JSON/Markdown path, exclusive report creation,
duplicate-key/symlink/oversize refusals. Seven controls passed; actual owner
terminal `03792b/exit0/no session`, child85392 reaped0/group others absent,
CPU8 closed. Receipt `sdk-receiving-comparison-report-entry-controls-20261016.json`
preserves this successor separately from the first five-test result. The acceptance
matrix now reflects the already accepted real multi-file SDK run rather than
its obsolete pending state. Fresh metadata-only rehash atUnix1792184033 found
all172 comparison execution pins unchanged, admission/workspace absent.

**Additional resource qualification:** admission suite now has28 groups on both
pinned compilers, including `max_int` saturated ledgers, queued sibling/cancel,
`min_int` cost rejection and exact source/consumer headroom partition.
`tests/qualification/admission-integer-boundaries-actual-20261016.json` records
actual owner88672/1adabb/0/no session; children85752/85812 reaped0 with other
group members absent before reap and CPU8 closed. Serial compiles only, no SDK,
Photo payload or EXIO; arithmetic credits are not hard RSS/FD caps. Production
sources unchanged; test files are outside the frozen172 comparison closure.

**Compact-base recovery qualification:** current production-object storage
suite passes29 cases/compiler, adding two actual cooperative forked writers
competing for one remaining quota entry. Exactly one new readable base and an
exact two-record charge survive; the original base/FD baseline remain intact.
`tests/qualification/compact-cache-concurrent-quota-actual-20261016.json` retains
actual owner5065/365df7/0/no session, children86261/86284 reaped0/groups absent,
CPU8 closed. Production inventory matched each retained build before linking;
zero SDK/Photo payload/canonicalEXIO. This does not force execution overlap or
prove crash durability. Current stock probe/compiler-matched build says5.2.0,
so the current compiler description below is corrected rather than borrowing
historical5.5.1 wording. Frozen172-source request unchanged.

**Interrupted quota state:** successor storage controls now test all79 incomplete
ledger prefixes (length0..78), including empty ledger over retained records.
Every new capture refuses without rewriting the prefix or losing the original
readable base; descriptor baselines hold. Actual owner13248/060692/0/no session,
children86696/86712 reaped0/groups absent, CPU8 closed, both stock/Ox pass.
Receipt `compact-cache-torn-ledger-actual-20261016.json` preserves successor
sources separately. Controlled corrupt inputs are not actual power-loss testing;
uncertain-close lifetime remains unqualified beyond prior explicit scopes.

**Latest mixed-work control:** `tests/workers/run.py --shared-mixed-hash-only`
now uses original actual CPU-hashing helpers (one/two domains) beside parent
worker hash jobs under one HelperSupervisor, budgets1/2/4/6. Stock/Ox each pass
64parenthashes/eighthelpers with exact portable-reference transcripts, actual
helpergroup-before-reap/parentFD baseline closure. Ox test helpers compile through
Safe.spawn (warning retained); production objects unchanged. Actual owner6607 /
72ea0f/0/no session, children88355/88378 reaped0/groups absent/CPU8 closed.
Receipt `shared-mixed-cpu-hash-actual-20261016.json`. No SDK/ExifTool/camera/EXIO,
OSthread/RSS caps or compute-overlap claim; actual mixed external tools remain open.

Root independent comparison adoption is now durable:
`tests/qualification/sdk-receiving-comparison-v1-root-adoption-20261016.json`
binds Root actualclosure04535268. StateCONSUMED_ACTUAL_CLOSED_COORDINATION_RELEASED;
actualterminal/result/workerclosure pins verified. No renewed run or hold.

**Installed ExifTool bridge:** opt-in `tests/supervised_external/run.py
--exiftool /usr/local/bin/exiftool --exiftool-only` now qualifies real readonly
metadata alongside16 worker hashes in each compiler-matched runtime. ExifTool
13.10/config disabled, Rating3/LabelBlue, privateXMP byte/native8field fence,
helper/worker ledger settlement pass24assertions/compiler. Actual owner11684 /
ffac16/0/no session, children89057/89084 reaped0/groups absent, CPU8 closed.
Receipt `shared-exiftool-hash-actual-20261016.json`; scriptSHA before/after and
linked production objects pinned. No SDK/Photo/EXIO or installation/prefchange.
Not full Perl dependency inventory, independently observed ExifTool PID, sampled
CPU overlap, hardlimits or combined Adobe/ExifTool qualification. Default14
synthetic helper cases unchanged; newcase requires explicit installed tool.

**Diagnostic consumer:** `tests/supervised_external/external_records.py` now
strictly bounds log/line/count/UTF8 and canonicalPID/status/CPU/group fields.
Unknown/unobserved never become zero; duplicatehistoricalPIDs do not establish
lifetimes. All records have producer_authenticatedFALSE/resource_releaseFALSE
because helper text can resemble a diagnostic. Six pure groups plus four saved
real-record reparses passed actual0ba874/0/no session, child94391reaped0/group
absent/CPU8closed. Receipt `external-process-parser-actual-20261016.json`.

**User clarification:** OxCaml is usable independently of semantic hashing;
ordinary sync/generic cloning do not require semantic profiles or Adobe.
`doc/oxcaml.md` now states this, preserves the distinction between full compiled
feature modules and runtime enablement, and avoids claiming ordinary-sync
compiler speedup. Shared recipes use ownedUnison8/max2compilerjobs/selftest3
perendpoint. Current stock5.2.0 evidence is distinct from historical5.5.1.

**Mixed-work integration harness:** new `tests/mixed_validation/probe.ml`
composes real DngValidation/SupervisedExternal/SemanticWorkers on one six-credit
runtime, waits all task results, emits raw validator process/group/protocol and
metadata trace, then checks candidate/CPU/child/worker/FD closure. Fake-only
`run_controls.py` passes four success/error combinations per compiler,16original
fake helpers/128workerhashes overall; SDK-error is exit0/errors1 and mustreject,
metadata-error exit7 retains ordinary status while other work settles. Actual
30357/a567f6/0/no session, children95446/95485 reaped0/groups absent/CPU8closed.
Receipt `mixed-validation-fake-controls-actual-20261016.json`. No actual SDK,
ExifTool, Photo/EXIO/receiving/compute-overlap/hardcap qualification. This has NO
native admission route yet: next implement independent prefix auditor, exact
one-use entry/inherited9FD guard and memory/deadline/intent ownership before
preparing real-tool request. Source/method docs in tests/mixed_validation/README.md.

**Mixed independent auditor integrated:** `tests/mixed_validation/audit.py`
now joins exact8argv/candidate/build identity, SDK raw protocol+group/wait,
metadata process and source/version JSON, ownerclosed counters and directprobe
cleanup. Prefix audit separates complete2probes/knownfailedprefix/precallzero/
missingoutcome; continued work after failure or unknown groups refuses. Decimal
metadata versions preserve13.10 versus13.1. No authentication/release authority.
Eight source groups plus eight fresh fake cases across stock/Ox PASS,16fake
helpers/128hashes; actual49452/e2115a/0/no session, children96507/96509/96551
reaped0/groups absent/CPU8closed. Receipt `mixed-validation-audit-integration-actual-20261016.json`;
initial7group e04faf source predecessor retained. No SDK/ExifTool/Photo/EXIO.
That predecessor was CPU-only; the memory-admission successor below supersedes
that limit. Durable nativeentry journal/inherited9FD/oneuse guards and actual
lifecycle qualification remain before requesting native scheduling.

**Mixed backend admission now qualified:** probe acquires one durable production
SemanticAdmission envelope BEFOREcandidateopen: checkedBackendResources addition
SDK2048MiB/8FD +metadata128MiB/8FD +hash/bridge16MiB/48FD =2192MiB/64FD.
Gate6144MiB/256FD, sixCPU+twoowner. Eachinspection checks owner stillheld;
retirement follows all helper/hash/fence settlement. Single-attempt descriptor
close guards prevent numeric retry. Exact held/retired records audited;
legacyCPU-only receipts do not gain memory-accounting qualification.
Nineauditgroups +eightfreshfakecases +two private512MiB prehelperrefusals PASS
stock/Ox; refusal changesonlygate6144->512, zeroledger/FD baseline restored/no
helperPIDledgers. Actual80121/609ad1/0/no session, children97688/97697/97745
reaped0/groups absent/CPU8closed. Receipt `mixed-validation-memory-admission-actual-20261016.json`.
Declaredcredits only, no actualGiBallocation/hardRSS/FD cap/nativeSDK/EXIO grant.
**Journal worker checkpoint:** `tests/mixed_validation/worker.py` now persists
INTENT before launch and raw OUTCOME before audit/input fences, stops successors
after failure, checks deadline headroom before preparation and launch, and turns
publication failure into retained ownership uncertainty. It owns no release
authority. Eight actual callback/durable saved-outcome controls passed,
child99285 reaped0/group absent/Unison8 closed, actual terminal28c503/0/no session.
Receipt `mixed-validation-journal-actual-20261016.json`. Historical fake outcomes
were re-audited, not executed again; no SDK/ExifTool/camera/EXglobal operation.
**Fresh journal/process composition now passed:** `journal_controls.py` uses
the existing qualified private stock/Ox fake probes, checks source/object ancestry
and fresh copied hashes, then runs two success probes and one failed-first probe
through the durable worker. Six fake helpers/48hash tasks; independent actual PID
ledgers, input hash/epoch fences and exact backend envelopes audited. No Ox
successor after first functional failure. Actual child99655 reaped0/group absent,
CPU8 closed; owner session55301/terminal4d83d1/0/no running session. Receipt
`mixed-validation-journal-process-actual-20261016.json`. No SDK/installed
ExifTool/Photo/EXglobal operation. The copied private binaries are control
participants, not a new immutable native build inventory.
**Exact mixed plan source contract now implemented:** `mixed_validation/plan.py`
derives stock-then-Ox argv, requires probe/build/tool/metadata-dependency/input/
ancestry/execution pins and exact eight-field input epoch, fixes Unison8/EXglobal,
120s probe/10s helper observation/2192MiB+64 backend credits and declared2GiB IO
(not physical hard cap). `worker.execute_plan` consumes its argv/version/headroom.
Five plan+eight worker controls actually passed, children404/407 reaped0/groups
absent/CPU8 closed; actual terminal9e19fe/0/no session. Receipt
`mixed-validation-plan-actual-20261016.json`. Pure declarations do not verify
artifact bytes, grant runtime permission or qualify native FD ownership. Prior
fresh-process receipt remains pinned to its earlier worker version.
**Mixed artifact preparation implemented:** `artifacts.py` uses bounded
NOFOLLOW regular/single-link/owned SHA+size+eight-field fences and qualified
close carriers; source media is metadata-only, never an execution inventory
artifact. Each row gets a distinct native-clone-only disposable input, no
fallback/overwrite; clone SHA and identity are checked before/after use.
Five tiny original controls passed (including real native clone/injected close),
child1003 reaped0/group absent/CPU8 closed; actualbf3840/0/no session. Receipt
`mixed-validation-artifacts-actual-20261016.json` preserves initial import
failure60cbd8/1 closed before controls. No SDK/ExifTool/Photo/camera/EXglobal use.
Preparation is callable only: no admission authority or lock acquisition.
**Mixed inherited metadata boundary implemented:** `boundary.py` derives exact
intended execute.py worker argv and binds plan path/SHA/interpreter/workspace to
parent START/PIDs and the existing canonical9FD guard's explicit mixed target.
Shared guard now rejects bool token indexes. Four new injected boundary groups
plus five existing guard groups passed, actual children1380/1383 reaped0/groups
absent/CPU8 closed; terminalc976ae/0/no session. Receipt
`mixed-validation-boundary-actual-20261016.json`. Canonical manifests read only;
no IO locks/SDK/payload/native launch. This is metadata binding, not lock proof,
START authentication or settlement.
**Mixed worker entry now implemented:** execute.py reads bounded SHA-bound plan
metadata with duplicate-key/fence/qualified-close checks, binds actual START and
inherited9FD metadata before preparation, verifies interpreter, and connects
journal/source checks/clone-only inputs/post-fences to actual invoke with nine
inherited guardian descriptions and private UNISON state. Existing journal is
not replaced on failure; unknown ownership retains. Three inert-entry/original
metadata control groups passed, child1778 reaped0/group absent/CPU8 closed;
actual5723b6/0/no session. Receipt `mixed-validation-entry-actual-20261016.json`.
No probes/SDK/ExifTool/media/EXglobal use; no standalone parent/admission mode.
Actual inherited lifecycle and dispatcher qualification remain outstanding.
**Exact source closure and parent prefix now implemented:** inventory.py binds
all current mixed Python/probe code, transitive resource/process/clone/persistence
helpers and production source/build descriptions. execute.checked_plan enforces
exact paths+hashes. Two inventory+three inert entry groups passed, children2130/
2132 closed, actual80b051/0/no session. Receipt mixed-validation-inventory-actual.
parent.py reconstructs exact prefixes/helper settlements/backend envelopes,
rechecks sources/tools/source epoch and hashes invoked disposable clones under
retained IO; actual worker exit is separately bound. Offline check_files=False
explicitly leaves byte verification false; neither mode grants FD release.
Three parent+two inventory groups passed, children2226/2228 closed,
actual91e30c/0/no session. Receipt mixed-validation-parent-actual. No SDK/media/
EXglobal operations; current compiled artifact build linkage remains separate.
**Mixed dispatcher source wiring now implemented:** target mixed-sdk-metadata-hash
requires exact Unison8+EXglobal admission and a nine-word worker argv matching
existing explicit-script conventions (no extra -B position). Parent mode checks
frozen plan/current source closure/unused workspace, shared dispatch rechecks
before launch, records9FD identities, observes298s without broadkill, reparses
prefix/rechecks disposable bytes before reap/close, binds actual worker exit.
No CPU-only route. Package-qualified imports remove sibling plan.py collisions.
Initial regression import failures allclosed/preserved; corrected eight suites/
33groups passed, all8children reaped0/groups absent/CPU8closed, actual session53500/
8f6368/0/no running session. Receipt mixed-validation-dispatch-source-actual.
No SDK/camera/canonicalIO acquired. Actual inherited-process qualification and
immutable compiled-artifact/dependency inventory remain outstanding; no nativegrant.
**Actual disposable inherited-refusal composition now passed:** lifecycle.py
starts two real workers via mixed shared dispatch/private inner flock locks.
Nine descriptors pass guard then deliberately refuse before probe; eight refuse
guard. Source plan/prefix audit real; admission/entry argv/inventory explicit
doubles. Parent now persists SHARED-WORKER-EXIT-AUDIT after actual worker reap.
Workers3552/3554 reaped7/groups absent/inner locks closed+freshly reacquired;
containing3551 reaped0/group absent/outerCPU8 closed, actual06bb6e/0/no session.
Receipt mixed-validation-lifecycle-actual preserves predecessor without separate
exit receipt. No compiledprobe/SDK/ExifTool/Photo/canonicalIO use. Known refusal
composition only; success-probe inheritance/unknown retention remain open.
**Successful inherited-probe composition now passed:** lifecycle --success-controls
uses actual worker/clone-only tiny inputs/compiled stock+Ox probes/four authored
fake helpers/32hash tasks under disposable inherited locks. Raw helper PID ledgers
joined to audits, real parent prefix/bytes/source/exit checks run before closure.
Worker3818/probes/helpers settled; all inner locks closed+reacquired, containing
3817 reaped0/group absent/outerCPU8 closed. Actual66769/99d55b/0/no running session.
Receipt mixed-validation-success-lifecycle-actual embeds8raw metadata artifacts
with pins, preserving true task/parent resource scope. Fake build-id/version are
protocol text, not actual SDK/ExifTool qualification. Admission/entry/inventory
doubles remain; no canonicalIO/Photo/nativegrant. Unknown-retention composition
and compiled/native dependency inventory are still outstanding.
**Unknown-prefix composition now passed:** lifecycle --unknown-controls uses
pinned pre-probe replacement to persist INTENT/noOUTCOME. Real parent audit
refuses and enters retained-owner handler; control intercepts infinite wait only
after genuine retention marker/all9innerlocksbusy/workerunreaped proof. Separate
source-bound no-probe recovery then reaps4190/7/group absent, closes/reacquires
inner locks; containing4189 reaped0/group absent/outerCPU8closed. Actuald81fa2/0/
no session. Receipt mixed-validation-unknown-lifecycle-actual embeds5raw metadata
artifacts and preserves predecessor labeling. Original unknown journal remains,
no normal SHARED-CLOSED/accepted parent proof invented. This is authored-control
recovery only, not permission to release real unknown SDK/helper/FD ownership.
No canonicalIO/probe/SDK/ExifTool/Photo. Source lifecycle success/refusal/unknown
composition now has evidence; fresh compiled/dependency inventory still needed.
**Fresh compiled probes built, not executed:** build.py validates actual current
production build/selftest/compiler pins, records compiler intent/outcome, links
current probe with exact production .cmx/native objects plus .o/.cmi companions,
and rechecks all inputs after link. Stock output /private/tmp/unison-mixed-build-
stock-10a96e53e97d4da6acc3fd070fd607d7/probe SHAf9c30d5dcf317e7f359f38e1510d67afccbe3ef2b0e24931e56cc8f0e8668aa6;
Ox output /private/tmp/unison-mixed-build-ox-a70eace440964e0c8486e65e33647713/probe
SHA2630d74939e71f9b43016df9e56ee3f1370cec46b3f94075d368ea61d4e3c03b.
Actual containing4468/4487 and compilerchildren reaped0/groups absent/CPU8closed;
actual27185/30e59c/0/no running session. Receipt mixed-validation-probe-build-actual.
Both probes UNEXECUTED. No SDK/ExifTool/media/EXglobal. Complete standard-library
inventory explicitly false; existing qualified compiler installation reused.
**Build receipt enforcement now implemented:** build_receipts.py binds planned
probe executable to completed build-only receipt/actual compiler argv+exit+group,
current probe source/qualified production build+selftest/matchingcompiler/exact
declared object+.o+.cmi inventory. Worker checks before probe dispatch; parent
checks before acceptance/release. Current binary/source/object rehashes passed
for BOTH new unexecuted probes plus adversarial mutations;2build+3entry+3parent
groups, actual4897/4899/4901 reaped0/groups absent/CPU8closed, actual3cb65b/0/no
session. Receipt mixed-validation-build-enforcement-actual. No SDK/media/EXIO.
Lifecycle control source now explicitly doubles build receipts, alongside prior
admission/inventory doubles; prior lifecycle evidence remains source-pinned.
Complete standard-library inventory still false, no new execution authorization.
**Metadata inventory captured/enforced:** metadata_dependencies.py pins installed
ExifTool13.10 script+all236packagefiles+root-owned non-writable system Perl5.34
executable. Worker source checks/parent audit enforce. doc/mixed-exiftool-package-
inventory-v1.json49424B SHA f918c0425c87adbc2bd26e6f86e30dc5ed77fc8665c5c4aa22d1c80da142f014.
Actualcapture/recheck child5242/58e027/0 closed;2metadata+3inertentry groups passed
children5325/5327 closed/CPU8closed, actual491c01/0/no session. Receipts metadata-
inventory-actual and metadata-enforcement-actual. No ExifTool command/SDK/media/
EXglobal. Full runtime closure FALSE: OS Perl module search paths/dylibs remain
trusted, not a hermetic runtime claim. Lifecycle source explicitly doubles
package verifier alongside prior build/admission/inventory doubles.
**First mixed native request FROZEN, NOT ADMITTED:** doc/mixed-validation-plan-v1.json
62317B SHA0fd5d23f038930f1d55e535baeef15e76a316d6eb719d3f7cac3b412e2b3f88d;
doc/mixed-validation-request-v1.json45039B SHA3e76df160f2248cd401ef5e9eabdbb82f0b819cca2fa2a9af87578dc7e5e4064.
326executionpins/9prereqs, fresh unexecuted stock/Ox probes, one retained generated
48005534B uncompressed input metadata-only/two clone-only disposable inputs;
2serialSDKv1single+2ExifTool+32hash tasks/Unison8+EXglobal. DeclaredIO raised8GiB
conservatively (not measured/enforced); fivebudget controls actual8c8b0a/0, final
success+unknown composition/buildrecheck/metadata controls actual27349/9b7c25/0
allgroups+CPU8closed. Receipts budget-actual and pre-request-actual.
Workspace /private/tmp/unison-mixed-native-v1-e3d4f770baf243db915be0b3fdc0be9d,
admission /private/tmp/unison-mixed-validation-admission-v1.json both absent at
preparation22a98e/0; no currentUnisonresources. Exactrootrequestcommands/pins in
request. No SDK/ExifTool/media execution. Needs fresh Root review+IO admission,
never auto-dispatch from absence/resource release. Stdlib/systemPerl trust limits
remain false for complete closure.
**User exiftool-rs candidate reviewed source-only:** doc/exiftool-rs-review.md
and source-review-inputs-v1.json pin commit54a885f85692674f362e6256ba8609808d746d5d
(Cargo/license/main/lib downloaded, no execution/build/install). ConcreteCLI
difference: `--` goes through filename fallback rather than ending option parsing;
current frozen Perl argv cannot be swapped unchanged. Crate0.10.0 targetsExifTool
13.59 whereas existingPerl is13.10; retain actual backend/version provenance.
Optional future supervised CLI evaluation described, not a new gate on current
mixed request. No SDK/image/source bytes opened. Latest source-only scheduling
readbackccede4 Unix1792188204: admission/workspace bothabsent; no currentresources.
All326 frozen execution pins remain unchanged by these doc-only artifacts.
**Hash-backend requirement source audit:** current macOS implementation already
selects CommonCrypto via private rooted C contexts/64KiB feeds; portable manual
reference is fallback elsewhere. Fresh source rebind matches all6historical
checked-hash pins on stock+Ox. Receipt hash-backend-source-audit-20261017.json,
actualsource15397d/0 (no test/compiler/media execution). Historicalstock5.5.1 is
not current5.2.0; native+forcedreference controls remain exacthistory, no NIST/
independentcrypto audit claimed. No macOS backend rewrite needed for this gap;
non-Apple maintained-library/platformqualification still open. Acceptance and
next-work docs updated without changing326frozenmixedsources. Latest admission
readback958179 Unix1792188297 bothadmission/workspaceabsent, no resourcesheld.
**Independent hash boundary/state controls added during pending review:** only
tests/checked_hash/test.ml changed (outside326frozenexecutionpins); ten invalid
ranges/domain/min_int/max_int, zero-length edges, rejected-stream preservation
and independent contexts. Actual stock5.2.0/Ox5.2.0+ox pass native+forcedreference,
15vectors/fourdomainsmode, expectedsharedcapture rejections; compilerdo_not_spawn
alertpreserved. Containing6855/6896reaped0/groupsabsent/outerCPU8closed, actual
40896/bd9038/0/no running session. Receipt hash-bounds-current-actual-20261017.
Productionhash unchanged/all326mixedpins verified unchanged. Prior hash source-
audit test.ml binding nowhistorical; don't relabel old5.5.1 result current5.2.0.
No SDK/image/EXIO; no currentUnisonresources.
**Deterministic completed-before-owner worker control passed:** new standalone
tests/workers/late_cancel.ml outside326frozenpins links actual production objects.
Atomicbarrier+W.usage mutex proves completion queued/running0 while ownerLwtloop
stopped; replysleeping/CPU1+IO1+pending1held. Normal delivery succeeds, caller
cancel/shutdown suppress queuedresult, callerFD/sourcefence and allledgers/FDs
settle. Threecases/compiler stock5.2/Ox, actual11412/66fb24/0/no running session,
allcompile/runtimegroupsclosed/CPU8closed. Receipt worker-late-owner-completion-
actual-20261017. Newcompilercompanions initiallyemittedbesidesource thenretained
inOxworkdir; no production/buildobject changed. No SDK/media/canonicalIO or
publicationcommit inference; all326mixedpins reverifiedunchanged.
Next: reconcile Root review/admission against exact request, then actual
fake lifecycle; then fresh real-tool review/scheduling. Production core unchanged.

**Current resources:** zero Unison live jobs/retained grants. Full stock build/
selftests actual87161/b8ddda ->52664d/0/no session and Ox80362/27ce49 ->09fca0/0
both CLOSED; canonicalCPU00..07 released. No EXIO/SDK/Photo operations.

**Current production change:** `src/supervisedExternal.ml` adds opt-in
`external-process` diagnostics after supervised helper settlement: historical
PID/wait/outcome/CPUweight/capturetruncation/retained-group census. No arguments
or output logged, default no group query, APIs and existing exit/cancel policies
unchanged. Final16componentcases/compiler pass against explicit unchanged
production CMI (hash equality checked), actual owner47300/e110a5/0/no session,
children93360/93444 reaped0/groups absent/CPU8closed. Initial73564/32deca overlay
inferredCMI remains preserved with that limitation; runner now copies `.mli`.
Full current Make+CLI selftests pass on stock5.2.0/Ox5.2.0+ox,293production source
pins match each build/current checkout; binarySHA independently checked.
Receipts `external-process-current-interface-actual-20261016.json` and
`external-process-full-cli-actual-20261016.json`. Prior Dune/nativeSDK receipts
retain their historical sources; no SDK replay or current Dune/GUI claim.
Initial fullbuild96cbc5/2 refused missingSTOCK_PREFIX before dispatch; corrected
explicit compiler path used actual87161/newunusednamespace, no startedjobretry.

**Next substantive step:** use these generic helper observations when preparing
one source-reviewed/admitted actual combined ExifTool/hash/SDK workload; no
runtime grant exists. Keep exact per-helper/group/FD proof and unknown retention,
not sampled overlap as settlement. Continue broader SOL/corpus/platform work.

**Git/review:** workspace `/Users/alexy/src/unison`, branch
`feat/semantic-dng-oxcaml`, fork `git@github.com:querygraph/unison.git`.
Pinned selected upstream base: `8772d26a2eb77cfd0cb6da81807e81f24f51044c`.
[PR #1](https://github.com/querygraph/unison/pull/1) **MERGED** into master in
querygraph/unison at2026-10-16T20:47:50Z, by explicit user instruction.
Merged PR head `4af7931c041e7592fc178b78fc190923899c995c` included this handoff.
Actual merge commit `dd35a2a9f2fc62dd9b50e5f9c683bb97cf0f5c6d`.
The feature branch is preserved and fast-forwarded through that merge; the
post-merge handoff checkpoint is published to both fork branches. Nothing was
merged into bcpierce00/unison. The PR base was exactly the pinned upstream base.
The implementation remains unfinished even after integration into fork master.
No upstream PR, maintainer contact, deployment or production-photo mutation is authorized.
Upstream CONTRIBUTING.md rejects LLM submissions; do not confuse our fork work
with permission to submit upstream. No CI checks were reported on this PR;
local scoped qualification must not be called GitHub CI success.

## Maintenance and restart protocol

Keep this document current after material code changes, new frozen requests,
admissions, actual START/terminal, independent acceptance, and before pausing or
handoff. Update the current checkpoint and next task, not just append old states.
Never rewrite sealed raw receipts to make a new story. Historical notices and
source pins retain their original scopes; write explicit successor/addendum
records. Treat delayed START/defer/release messages as historical when a later
actual terminal and acceptance already exist.

On restart:

1. Read this file, SOL.md, current applicable AGENTS.md, and Git status.
2. Check goal state; the user resumed it after a deliberate pause. Do not pause
   autonomously. Do not create a new goal for this same objective.
3. Verify actual current files/receipts rather than trusting this timestamp.
4. Respect the protected untracked files below. Never use broad staging/cleanup.
5. Reconcile the single fresh comparison request/admission/workspace before
   considering execution. Workspace existence means investigate, never replay.
6. Pick concrete work against remaining SOL requirements. A scheduling wait for
   one native test is not a whole-goal blocker while source work remains possible.
7. Update this file and review/acceptance maps when authoritative state changes.

The user strongly prefers autonomous work without repeated permission requests.
Existing authorization persists. SDK/real-payload windows still require exact
Photo Root coordination because both projects share one host and IO barrier.
Do not ask for a new approval for an already admitted identical one-use command.

## Canonical shared-machine protocol

Policy v3, authoritative equal split:

- `/Users/alexy/src/photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json`
- SHA256 `1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352`
- Unison tokens00..07, Photo08..15, system16..17 idle. Older10/6 and4/12 policies
  are historical. Borrowing requires explicit fresh coordination, never inference.
- Compiler jobs at most2 within Unison8. Both loopback endpoints count: default
 3+3 workers +2 owner/orchestration =8. Native/helper inner work counts too.
- Credits are scheduling reservations, not hard OS thread/RSS/physical IO caps.
- Declared memory reservations historically32/64/32GiB are planning, not enforced RSS.

CPU pool (existing only; never recreate):

- `/Users/alexy/Library/Application Support/FirstPair Lightroom Shuttle/cpu-credits-v1`
- Manifest `/Users/alexy/src/photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json`
- SHA256 `4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd`
- Directory dev16777223 inode307122462; cpu00..17 inodes307122463..307122480.

Physical IO pool (sole agreed namespace):

- `/Users/alexy/Library/Application Support/FirstPair Lightroom Shuttle/io-lanes-v1`
- Directory dev16777223 inode307225492; `all-devices.lock` inode307225493.
- Manifest `/Users/alexy/src/photo/preview-generator/SHARED-PHYSICAL-IO-POOL-v1.json`
- 1500B SHA256 `f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636`.
- EX_GLOBAL_ONLY. No qualified physical leaf/device independence. Topology and
  per-device union planning are separate source work. Do not create a second
  physical-io-lanes namespace or repurpose the Photo UI lease (inode304149394).

Acquisition order: IO -> CPU -> separately coordinated native/UI lease, if any.
Open existing no-follow descriptors with exact stable identity checks. Acquire
whole explicit sorted sets nonblocking. On contention close partial acquisition
before waiting/retry. Distinct open descriptions; no LOCK_UN. Hold ownership
through actual child/group settlement. A failed/uncertain close carries all known
and uncertain identities; never retry a numeric FD. Unknown retains owner/FDs.
`close_after_verified_settlement` consumes caller proof; it does not establish it.

Actual owning tool terminal is mandatory. Process absence, aggregate markers,
output EOF, or observation expiry do not prove parent termination. Collect the
owning exec/write_stdin result; once terminal, do not poll/restart that session.
Send actual terminal promptly; report sealing is not a resource-release gate.
SDK ownership uses observation deadlines with retained unknowns, not a generic
outer timeout/broad kill. Never signal guessed or reused PIDs.

## Coordination, tools and preserved files

Qualified interpreter:

`/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14`

SHA256 `56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29`
(18749552B). Use `-B` for controls. Host: Intel macOS,18physical/36logical cores,
128GiB. Current fork requires OCaml5; upstream's old4.x floor is not this branch.
Do not install SDKs/compilers or run automatic fuzz/sanitizers without scope.
No automatic subagent delegation; existing dormant agents are historical.

Authorized Photo Root queue thread: `01a13369-8b68-7aa1-be91-cba984ba269b`.
Our thread: `01a133ca-2639-73c3-8da8-b42902c834fd`.
Use an argv list, e.g. `subprocess.run(['codex','queue','--thread',THREAD,'--message',TEXT], ...)`.
This is authorized cross-project coordination, not permission to send email/Slack.

Authorized fork push: `git push git@github.com:querygraph/unison.git HEAD:feat/semantic-dng-oxcaml`.
Remote `origin` is upstream bcpierce00/unison; do not push there. Tracking refs
can be stale after direct SSH pushes. Check actual remote/PR state when necessary.

Protected untracked files: never stage/edit/delete them:

- `LIGHTROOM-MONITOR-PREVIEW-HANDOFF-20261013.json`
- `PHOTO-OWNER-BRIDGE-RESTORE-5e683f78e8d2454a97cc610429e1e321.json`
- `PHOTO-OWNER-PREVIEW-VALIDATION-CURRENT.json`
- `PHOTO-OWNER-PREVIEW-VALIDATION-CURRENT.json.tmp-61fb2b7d09724a88b42feed0ac167b55`
- `PREVIEW-MASS-ALIGNMENT-FORWARD-20261013.{json,txt}`
- `PREVIEW-ORACLE-CORRECTION-20261013.{json,txt}`
- `PREVIEW-REVIEW-FORWARD-20261013.{json,txt}`

## Architecture and design implemented

Read [the production review map](doc/implementation-review.md),
[SOL.md](SOL.md), [normative SDE draft](doc/semantic-delta-v0.md),
[semantic sync behavior](doc/semantic-sync.md), and
[twelve-row acceptance audit](doc/acceptance-matrix-audit.md).
`doc/milestone-next-work.md` is the detailed evolving queue. Some older docs
retain superseded checkpoints; current code and pinned later actual receipts win.

### Generic clone-aware transfer, independent of DNG

Production units include `wholeFileClone`, `cloneRange`, `cloneLease`, `copyRange`,
C stubs and Copy/Transfer integration. Existing upstream engine is reused;
there is no separate DNG APFS clone engine. Same-volume local transfer prefers
source-to-stage cloning. Generic rsync receiver-basis staging skips inherited
same-offset writes and copies shifted matches from an immutable basis. EOF,
shrink/growth, inserted/deleted prefixes, duplicates, ordinary text/binary files,
clone-off and ordinary fallback are covered by scoped controls.

`clone=auto|off|require`: require is a qualified eligible-update policy, not a
universal promise that every transfer clones. Fake constrained range adapters
exercise richer ZFS/ReFS contracts; no new runtime qualification of those OSes.
Cross-volume APFS/HFS+ controls and property/fork removal/read-only/no-op controls
exist. Clone success is not proof of physical block sharing or write savings.

### Semantic extensions, hashing and exact transfer

`formatExtension`, `formatRecognition`, `semanticFormats`, `semanticDelta`,
`semanticHash`, `semanticFile`, `semanticSync`, `semanticRemote` implement the
format-neutral registry, recognition, bounded proof/wire/planning and materialization.
Static trusted extensions only: peer data never supplies executable extensions.

**Yes, new semantic-transfer hashing is implemented.** SHA-256 identities bind
full base/target bytes, editable metadata regions, and the complete protected
remainder through domain-separated transcripts. Exact region geometry/profile,
nonce/base/target/preservation/old-region proofs are verified. Whole staged output
is verified against source target identity before publication. This is separate
from archive fingerprints and Adobe's raw-image digest. Advisory semantic
observations are not authority to ignore bytes or equate rendered images.
CommonCrypto is the macOS native hash backend, with a separately tested portable
reference elsewhere. Hashing/file contexts are worker-owned with checked native contracts.

SDE/0 and SDR/0 canonical bounded encodings, independent goldens/reference
vectors, strict prefixes/range/count/overflow/nonce/target-proof rejection,
extension registration and a second trivial extension are implemented.
Independent inspection/dry-run tooling reports eligibility/reason/proofs/planned
payload and advisory change classes. Metadata previews are bounded/escaped.

Conservative DNG profiles0/1: classic TIFF/BigTIFF, both byte orders, bounded
IFD/SubIFD/embedded camera-profile graphs and one fixed-position/length XMP
packet. Every noneditable byte is protected. Standard JPEG XMP profile is
separately opt-in. Unknown/private/opaque/layout-growth/rendering/unsupported
changes keep exact ordinary transfer or conflicts, not a permissive whitelist.
Private Adobe/MakN framing/IFD0 locator work is diagnostic and inactive for
eligibility. Actual private camera sample50740 safely declines semantics.

### Publication, properties and reconciliation

Reuse normal fork/property/fingerprint/rename/archive lifecycle. Retained source,
producer, candidate, root/parent/name witnesses and finalization guards bind
cooperative ownership. StagePublication/FinalPublication and caller controls
cover scoped mutation/replacement/sidecar/close/error paths. Preserve legacy
stashing/rename semantics. Fresh lookup+rename is not hostile-writer atomic CAS,
mount-incarnation proof, or power-loss durability.

M5 opt-in scalar XMP reconciliation and compact common metadata bases exist:
verified previous common base, conservative fixed-region allowlist, deterministic
serialization, cache quotas/checksums/fsync, policy mismatch, stale/missing base,
partial two-replica failure/recovery and legacy archive downgrade/refusal. Default
remains exact conflict-preserving synchronization. General RDF/Bag/Seq/Alt/
qualifier/rendering/growing-packet merge is not implemented as permissive merge;
unsupported shapes remain conflicts.

### Optional Adobe validation and workers

`candidateValidators`, `candidateValidation`, `dngCandidateValidation`,
`dngValidation`, `helperSupervisor`, `helperLimiter`, `backendResources` implement
receiving-candidate off/warn/require policy with pinned local tool/build/hash,
strict raw protocol, snapshot/mutation checks, bounded diagnostics, cancellation,
CPU/resource admission and helper/group settlement. Full/fallback/reused/resumed/
merged paths have scoped source/control evidence; representative corpus scope
remains open. Off works without Adobe. Old receivers cannot silently evade
required validation. Optional all-scanned unchanged-file validation is absent;
received-file scope excludes true no-op and rename-only moves.

Qualified v1 driver is single-threaded per file. Experimental capped SDK area-task
host has historical functional1/6/18 and later shared1/2/6 evidence; it remains
separate/uninstalled on production endpoints. Covered allocator amounts are not
whole-process RSS or OS thread caps. Current native comparison uses v1 only.

`semanticWorkers`, mailbox, admission/runtime/IO gates and checked Ox interfaces
run immutable hash/recognition/inspection/delta jobs off-owner. RPC/Lwt/archive/
callbacks remain on the sole event-loop owner. Ox closure is compiled through
Safe.spawn; stock uses corresponding ordinary interfaces. See
`doc/checked-semantic-worker.md` and `doc/production-oxcaml-mode-selection.md`.
Older `doc/semantic-workers.md` text describing the pre-Safe.spawn boundary is
historical, not current acceptance. No unsafe cast/alert suppression is intended.
`semanticworkers=0` auto sizes physical macOS cores (logical fallback); explicit
shared endpoint budgets must be supplied on this shared host.

## Current build/toolchain evidence

Pinned stock compiler `/Users/alexy/.opam/default/bin/ocamlopt` (current retained build and storage probe report5.2.0; earlier5.5.1 evidence is historical), SHA256
`f183dd4bd5c655b56fb87da2d39e01b843a730b6252e8b92fc6989e6f07cfacf`.
Ox `/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt`, SHA256
`e02b8590aa2c05948203befbfef22253282b1799d92f9a32c3878681f1b3e166`.
Never share build artifacts/config between compilers; max2 compile jobs here.

Current Make build/selftest records:

| Compiler | Receipt | Actual tool terminal | Binary SHA256 |
| --- | --- | --- | --- |
| Stock | `/private/tmp/unison-validation-live-full-stock-20261016a/RESULT.json` |14148/447075/0|`1af235b8778d6dd14dfddc245eef98ccac66f4f5c3f350eab5183176de7ab058`|
| Ox | `/private/tmp/unison-validation-live-full-ox-20261016a/RESULT.json` |75001/bd0690/0|`b6f3055536a26418fd79c5e8f95917779ba137d198c12d02d881aafc243c823e`|

Binary paths are in those receipts; `/var/...` aliases must resolve canonically
before exact entry checks. Current inventories each have428 entries,294 production
entries still current; only disclosed nonproduction `tests/workers/test.ml`
differs. Historical inventory remains immutable. New controls must not claim
that changed tests were in old builds. Current Make/Dune+selftest evidence is
indexed in `doc/implementation-review.md`; Dune current receipts include
`tests/qualification/validation-live-current-dune-actual-20261016.json` and
`validation-live-collector-build-actual-20261016.json`.

No material ML/C production changes occurred during the latest comparison
harness work. The conformance shared wrapper now retains child/log ownership on
timed-wait errors; its focused controls are inert-child evidence, not an actual
compiler-timeout recovery. One initial comparison-worker import failure is
preserved; corrected source controls passed. Do not gratuitously rerun the entire
suite when no related production changes warrant it.

## Completed SDK/receiving evidence: do not replay

The exact scope matters more than the word PASS. Fixtures, synthetic protocols,
actual Adobe results, OS observations and Photo previews are different evidence.

### Multi-file receiving V1: most recent actual SDK run

- Workspace `/private/tmp/u-smr-v1-13fc44d676`.
- Actual owner23264, initialf178d0, terminal2004ad, exit0, no running session.
  Owner PID51817, worker51818 reaped0/others absent.
- Admission SHA `7b320b5137f4ae24fd16da9256fcd03386868130cf7c6c7459735182596a234d`
  **CONSUMED ONCE**. Not a grant for the new comparison.
- Two actual stock/Ox receiving seeds, two generated candidates each, four v1
  single-thread SDK calls. Exact received bytes, valid raw digests, decode success,
  errors0/warnings4 each. Positive known-nonterminal spans378621998ns/373058998ns;
  not SDK compute overlap, throughput, pixels, corpus or production qualification.
- 159 execution pins matched at completion; inherited canonical9FDs bound;
  all CLI/client/supervisor/server/pump/helper/worker/group/FD proofs closed.
- Sealed `tests/qualification/sdk-multifile-receiving-v1-actual-20261016.json`:
  5245B SHA `d77595cf0fe392d3ee849e28861b4a38015f089a2bdd8f8033eebb06a1b3f60e`.
- `OWNER-RETURN.json` 5054B SHA
  `3d94056ef4d0fc2b5ebc50a963a35777fdb63ce61b7f3497e6d0ad92389de81e`.
- Root acceptance path `/Users/alexy/src/photo/preview-generator/UNISON-SDK-MULTIFILE-RECEIVING-V1-ACTUAL-ACCEPTANCE-20261016.json`,
  1185B SHA `f3b0707254804c44772d0665ec95a50e3fd4986e94a0ac8b57aba95a9a6ea209`.
  Independent audit SHA `1621c9a1f80e12c7a4b906dae19dddfa104368faef6d18105006e0f7de4ecb0f`;
  Root rehashed4 outputs174044512B under its own actuala268bd/0 closed audit.
- Local adoption `tests/qualification/sdk-multifile-v1-root-adoption-20261016.json`.
  Root metadata-only initial `actual`/`closure` key correction did not repeat runtime.

Current source has since evolved. Preserve the historical159-pin snapshot;
never change old receipts or rerun a consumed admission to match current code.

### Earlier important closed runs

| Scope | Actual owner terminal | Evidence / limit |
| --- | --- | --- |
| Shared SDK host V2 |39043/ef80c4/0|12SDK+62OS probe children; all closed. `sdk-shared-host-v2-actual-20261016.json`; bounded per-process samples, not peaks/tree/hardcaps. Admission735810e6 consumed.|
| Shared SDK host V1 |42215/e48a3d/0|12reference/experimental1/2/6 calls;125 historical source pins. No OS probe inV1.|
| Camera SDK receiving V2 |66811/65a573/0|2seeds/2realSDKcalls on one retained camera-derived copy; valid raw digest/decode/errors0. Not semantic eligibility/corpus.|
| Camera SDK V1 failure |5460/003cbb/137|Pre-SDK budget refusal2048MiB vs512MiB gate. Independent recovery closed;0SDK calls; original worker wait4 NOT claimed.|
| Synthetic concurrent receiving V2 |74146/b2b6ab/0|2CLI/4fake validators; known-live overlap. ZeroSDK. V1 withdrawn unstarted.|
| Camera generic fallback V4 |29392/3b4789/0|6seed/update/no-op calls, clone basis, old readers, exact hashes; explicit semantic decline.|
| SDK live scalar merge |43830/699a51/0|9CLI/6SDK generated codec cases; broader merge/corpus remains open.|
| Generated property V3 |24600/e4fe28/0|18rows54CLI stock/Ox workers1/2/3, forks/xattrs/mode/removal/no-op/old readers; narrow filesystem scope.|

SDK V2 OS observations are reproducible via `bench/report_sdk_observations.py`.
`bench/sdk-shared-host-v2-observations-20261016.{json,md}`: JPEG/JXL samples observed
2/6 threads; short uncompressed samples sometimes only1. Largest sampled RSS
153579520B, not peak/tree RSS. Native CPU units are uncalibrated; probes add overhead.
Prior actual capped-host1/6/18 matrix from2026-10-14 is also valid historical
functional evidence, not missing first SDK qualification. See
`sdk-host-matrix-v1-actual-return-20261014.json` and `sdk-prior-host-scope-review-20261016.json`.

## The exact NEXT comparison request

Prepared and checked, **NOT ADMITTED/NOT DISPATCHED** at2026-10-16T20:43:10Z:

| Item | Exact value |
| --- | --- |
| Request | `doc/sdk-receiving-comparison-request-v1.json` |
| Request bytes/SHA |104886B / `82248f18e67264be108c32e26e15c2a779a765b56298959fed192392cab3ca1b`|
| Plan | `doc/sdk-receiving-comparison-plan-v1.json` |
| Plan bytes/SHA |26961B / `97b458b29efcab162672103393500e7d01b42c8ab4133971e433a568cb2a4854`|
| Future admission | `/private/tmp/unison-sdk-receiving-comparison-admission-v1.json` (absent at last check) |
| Unique workspace | `/private/tmp/u-str-v1-c39d488994` (absent at last check) |
| Exact target | `sdk-receiving-comparison` |
| Sources/prerequisites |172 execution pins /11 prerequisites|
| Schedule | stock/Ox × endpoint workers1/3 ×1warmup+5measured =24serialCLI/48SDKv1single helpers max |
| Ownership | Unison00..07 + existing EXglobal; same8 reserved credits for every row |
| Observations |600sowner/570sworker/120sCLI/90sSDK; pre-row stop if135s headroom absent |
| Other bounds |32GiB declared logical IO (not instrumented/physical hardcap); result JSON16MiB |

Root source/scheduling request queued `01a14673-b0e9-7721-8178-0662ceb03bdc`.
No allocation/extension inferred from queue delivery, Photo release, or this file.

The request contains the exact `launch_argv` with `ROOT_PUBLISHED_SHA_REQUIRED`.
Only substitute the SHA of a separately published valid exact admission.
Fresh-check request/plan/prerequisites/current execution pins/interpreter/build
metadata/unused workspace/start deadline. Worker hashes pinned binaries/tool
AFTER acquiring IO, before calls. If already started, reconcile the existing
handle; never dispatch twice. If expired, refuse and request a distinct fresh
schedule, without editing/replaying the old grant. Unknown retains ownership.

Each row uses native clone-only preparation, no hardlink/full-copy fallback,
no source payload hash/mutation. Same generated uncompressed+JPEG fixtures as
prior qualified runs.1+1+owner2 or3+3+owner2 stays within8. Order rotates by round;
all samples, failed prefixes and source disclosures must be retained.
This is warm end-to-end receiving-validation comparison, including hashing,
transfer/staging and helper startup, not isolated SDK decode throughput.
No quiet/coldcache/physical savings/OSthreadhardcap/RSSpeak/pixel/corpus claim.

### New comparison implementation and evidence

`tests/sdk_throughput/`:

- `plan.py`: pure exact24-row schedule, distinct fresh directories, strict typed
  row matching; bool cannot substitute for integer metadata.
- `transport.py`: reuse qualified one-shot Invoker, exact row command/server flags,
  journal identity1/3 adapter, immutable copied input binding.
- `audit.py`: independent schedule/journal/case/raw-proxy/SDK helper join; full24
  results versus known failed prefix versus unknown intent. No FD release power.
- `worker.py`: retained sequential rows, source fences, intent before launch,
  outcome before byte checks, pre-next-row headroom stop and persisted failures.
- `entry.py`: fixed schema/limits/source set, common strict metadata validator,
  exact one-use admission, actual START/parent/worker/argv/canonical9FD guard,
  under-IO interpreter/binary/tool hashes, native clone-only preparation.
- `tests/shared_dispatch.py`: existing IO->CPU owner; reads only reconstructed
  row proxy directories, independently audits prefix, rechecks input epochs and
  complete left/right hashes before worker reap then CPU/IO close; unknown retains.
- `tests/sdk_host_matrix/shared_binding.py`: target-specific canonical metadata
  guard; no lock/settlement claim from fstat alone.

Actual full fake lifecycle:59736/b5f148/0;24fake clients+24fake servers,
24launcher children+48Python hash helpers, all direct/group/pump receipts and
original tiny bytes checked. ZeroSDK/retained payload/canonical IO.40source
entry/dispatcher/regression groups and two actual FD refusal children passed;
all source hashes rechecked after pause. The nine-FD handoff reaches deliberate
pre-SDK refusal; incomplete handoff refuses before worker, locks close/reacquire.
Receipts `sdk-throughput-*-actual-20261016.json` and README explain exact scopes.
Do not call these fake-process timings an SDK benchmark.

## SDK tools / retained generated inputs

Reference v1 only for the next comparison:

- `/private/tmp/unison-adobe-driver-build/unison-adobe-validator`
- 9017656B SHA `ca49a32bd5980b5cb16e10421d2d7a41542698a49f03a5b50007ff234b432b4a`
- Build `unison-sdk171-2724-v1-single`.
- Manifest `/private/tmp/unison-adobe-driver-build/build-manifest.json`,619B SHA
  `ede0fb503aee112506b8b98b3516df4c5c8b004afc23d73f3bdf7699ea9df87b`.

Experimental host (historical observations only; not installed as endpoint):
`/private/tmp/unison-adobe-area-memory-observed-20261014-v1/unison-adobe-validator-area-memory-unqualified`,
9056800B SHA `12df79747c16a87618d69a6ef16e24351e082be80dc1debed4234798d1f10278`.
Build `unison-sdk171-2724-v3-area-memory-unqualified`; covered allocator1GiB.

Retained generated fixtures (0644, historical full hashes; do not read without
new exact payload admission):

| Fixture under `/private/tmp/unison-receive-pilot-native-prepared-20261014-v2/` | Bytes | SHA256 |
| --- | ---: | --- |
| `uncompressed-original.dng` |48005534|`ace206af69f6a8413cb7cfc5ad263a279a860f30bfcb8f79e764d6970744075e`|
| `jpeg-original.dng` |39016722|`5d710753aeb817118a95a50b829b9d3033afc2a21ac25a6c403bef8f0b93927a`|
| `jxl-original.dng` |38237658|`3696d39bb928d7b013ff33cba05caabbf89fae6359e84c5f1bc26a8ab3c61edf`|

Exact input eight-field epochs are in the frozen plan. Do not rehash source
payload just to refresh a handoff. Clone hashes must match historical expected
SHA under the admitted window. New comparison uses only first two fixtures.

Private camera source (NOT a current grant): Unison copy
`/private/tmp/unison-dng-da-copy-57c830f336da4ef099150958b2f3d666/source-clone.DNG`,
193851848B, inode307228717,0400,nlink1; SHA
`1a4f578ee6f23730afec8495c90b37f5272042331f3375d332a9065ce5bb3ee2`.
Photo's retained source copy is under `coverage-selection-v2/da-source-31982627/`.
No writes/chmod/xattr/link/rename/unlink, original recopy, SDK/renderer access or
fresh payload hash without exact authorization. Private camera eligibility remains
unsupported50740. Earlier framing only read bounded headers, not semantic proof.
Ancestry2450B/2345ed50; SOURCE-COPY1060B/b2e3b13a; job5864B/652e9110.
87b83d62 belongs READONLY-COPY-IDENTITY, not ancestry; do not invent old byte pins.

## Historical timing results and failures

`bench/report_warm512.py`, `bench/report_warm512_distribution.py`, and
`bench/sync/results/warm512-{observed-results-v2,empirical-distribution-v1}.{json,md}`
preserve all88 measured samples across18 configurations. Four/five samples per
configuration; empirical ranks/observed maxima, no population-tail extrapolation.
Frozen source `a6f0b695159b3bdb5c3e73d57c0a54900fe86d6d`, warm4×512MiB synthetic files.
Not current-code/camera/cold/physical IO performance. Parts0/1/2/4/5passed,
part3FAILED/INCOMPLETE; never replace/replay silently.

| Compiler/workers | Ordinary median s | Clone median s | Semantic median s |
| --- | ---: | ---: | ---: |
| stock1 |37.423|36.700|69.659|
| stock6 |37.027|36.344|34.209|
| stock8 |37.028|36.299|34.232|
| Ox1 partial |37.353(n5)|36.980(n4)|71.046(n4)|
| Ox6 |36.490|35.854|35.019|
| Ox8 |36.346|35.664|34.684|

Protocol~806012/806013/51861B; modeled non-inherited logical bytes ordinary2GiB,
clone131072, semantic writes12288. Physical writes unknown. Do not infer physical
sharing or savings from logical counts.

Mandatory part0 overlap addendum:
`bench/sync/results/warm512-part0-timing-overlap-addendum-20261015.json`,6788B SHA
`e311d5f64c8fa5dde2a8e361b3858db367a01c1aaa3b38c5961fe279b7e6b6b5`.
Static objdump overlap Unix1792046929.4774537..1792046988.967324: definite row5,
possible row4 boundary; impact/carryover unknown. Part3 brew/neomutt make overlap
and source review, plus part5 bounded source editing, stay disclosed. No absolute
quiet/timing-clean claim. No exclusion/replacement/rerun authorization.

Part3 actual76640/df5ca2/exit1:16completedrows/49actualCLI closed, generic
expected0 helper marker preserved as failure provenance, not live SDK helpers.
Part4 actual57036/f228d4/0 accepted/released; returne25c3c60; never stale-hold it.
Part5 actual52232/2b05a9/0 accepted/released; returna3cdf6ec. Warm128324CLI
actual34823/c78138/0 closed. **Stopped60597 never replay or reconstruct a missing receipt.**

Other crossed-state traps: canonical IO original241da556 expired unstarted, but
reschedule2519623d actually82843/7efd2e/0 closed/adopted; do not repeat canonical
probe. PrivateDA original77ea9eeb actually77296/c15ad5/0 consumed despite an
incorrect later RETIRED observation; explicit correction adopted. Lifecycle3736/
16df12/0 was one consumed v1 run; v2 withdrawn unstarted. PropertyV1 first seed
failed and independently recovered with17842/c39203/137; original worker wait4
NOT claimed. V2 preexec refused; V3 separately passed. Do not recreate those holds.

## Remaining work, without narrowing the objective

No full acceptance row is established merely by a green component suite.
Use SOL.md's exact requirements, not an invented universal claim or a smaller
fixture-only replacement. Unsupported format/merge cases may correctly refuse;
that differs from proving representative supported coverage.

| Milestone | Next substantive work / limit |
| --- | --- |
| M0 | Keep current toolchain/Make/Dune/CLI evidence tied to production snapshots; no GUI/other-platform inference. |
| M1/M4 | Representative semantic eligibility/private-reference closure and supported corpus strata; preserve exact fallback rather than broadening tags to make one camera pass. |
| M2-G | Broader property/publication/fault combinations, platform guards and honest generic clone telemetry. Existing exact/cross-volume controls are not physical IO proof. |
| M3 | Remaining compatibility/disconnect/restart/cancel/failure combinations; actual old-peer/current behavior must keep exact fallback and archive recovery. |
| M4-V | Comparison V1 now actual24CLI/48SDK PASS/CLOSED with five measurements/configuration; continue mixed real helper/hash accounting, resource/cancellation and representative corpus qualification. No replay. |
| M5 | Required conservative conflict, stale/missing base, partial-two-replica and fault scopes; do not implement arbitrary RDF/rendering merge merely to avoid conflicts. |
| M6 | Complete benchmark/resource evidence, actual bounded mixed work and broader cancellation/platform scope. Samples/reservations are not hard RSS/FD/CPU limits or speedup. |

The twelve-row audit maps exactness, container coverage, malformed input,
integrity, concurrent modification, failure/recovery, filesystem behavior,
compatibility, parallelism/resources, semantic merge, generic cloned transfer,
and Adobe accounting to receipts and open scopes. Broad parser RSS, physical
devices, power loss/hostile CAS, unsupported platforms/corpus and whole-tree caps
remain unproved. Automatic fuzz/sanitizer campaigns were explicitly excluded;
keep user-run tooling/scopes separate, never silently launch them.

## Recently delivered commits and navigation

- `50da86f`: exact comparison request/plan/metadata checkpoint (current pre-handoff HEAD).
- `87f125a`: exact admission/dispatcher/canonical FD integration;40groups+2realchildren.
- `2b46469`: full24-row original-fake process lifecycle.
- `d97f1e5`: comparison worker with pre-row deadline stop.
- `75931e5`: independent exact-row/failed-prefix audit and typed metadata.
- `cbdcb4e`: exact scheduled worker-count/command transport binding.
- `4b928ce`: pure comparison plan + independent multi-file acceptance adoption.
- `1f24502`: conformance child/log retention on timed-wait errors.
- `0d797f8`: actual multi-file SDK receiving PASS/CLOSED.
- `595d77a`, `a161939`: clone uncertainty and tiny native clone controls.
- `7a4880a`: all retained warm512 samples/distribution/provenance.
- `965f7e4`, `6fa4556`: acceptance reconciliation and earlier exact multi-file request.

Detailed docs: `doc/implementation-review.md`, `doc/milestone-next-work.md`,
`doc/acceptance-matrix-audit.md`, `doc/semantic-sync.md`, `doc/oxcaml.md`,
`doc/dng-profile-v0.md`, `doc/dng-profile-v1.md`, `doc/dng-built-in-merge.md`,
`doc/dng-compact-merge-base.md`, `doc/candidate-validators.md`,
`doc/checked-semantic-worker.md`, `doc/resource-admission.md`.
Qualification receipts live under `tests/qualification/` and component suites.
Some historical documents say pending for runs later accepted; reconcile by
exact identity and actual terminal, not by repeating them.

## Fork merge checkpoint

**Current follow-up review:** draft PR2
https://github.com/querygraph/unison/pull/2 opened after actual mixed qualification
and independent Root adoption. Base is **querygraph/unison:master**, observed
4a620ea0160d4ac021c02c8246a3bb41db8acda3; initial PR2 head
a0e0e961cec47f1072aeae12fe90e81ba66f1de9, draft state independently read back.
Only production delta since that base is supervisedExternal.ml's opt-in helper
diagnostics; large remainder is tests/owner harnesses/receipts/reports/docs.
PR1 remains merged history. PR2 is not merged or submitted upstream, and is not
full-goal acceptance. Native mixed admission is already consumed/closed, not a
review prerequisite to rerun. Follow-up work must preserve supported corpus,
platform/failure/compatibility and resource/benchmark open scopes above.

User explicitly requested merging PR #1 during the handoff turn. Completed:

- Handoff/review-navigation commit `4af7931c041e7592fc178b78fc190923899c995c` pushed.
- Exact-head guarded merge via `gh pr merge 1 --repo querygraph/unison --merge
  --match-head-commit 4af7931c041e7592fc178b78fc190923899c995c` returned0.
- GitHub independently read back state MERGED, mergedAt2026-10-16T20:47:50Z,
  merge commit `dd35a2a9f2fc62dd9b50e5f9c683bb97cf0f5c6d`, base master.
- Fetched fork/master and fast-forwarded the preserved local feature branch.
- This post-merge handoff correction is a documentation-only checkpoint; no
  production sources, frozen172 pins, request/admission or payload changed.

Future implementation commits must not be described as updates to an open PR1:
that PR is now merged. Continue on a suitable branch and use a distinct review
when appropriate. No upstream submission or full-goal qualification follows.

## Owner-bound worker refresh successor — 2026-10-17

Separate `feat/component-owned-worker-refresh` adds
`SemanticWorkers.refresh_owned_components`: the worker authenticates a bounded
UCR record against its trusted UDI entry and derives checkpoint digest and full
historical decoder inventory there, then runs existing full-input/current-parser
verification and localized decoder refresh. No independently chosen inventory
can be substituted through this API. It uses existing CPU/IO/cancellation and
FD settlement; it does not open/select cache objects or adopt archive state.

Actual owner67532/754d9e/0/no session: stock/Ox Make/fullselftests plus116 original
worker checks/compiler PASS, all three contained workers/groups/tokens closed.
Corrupt/foreign record rejection, oversized prequeue refusal and unchanged-view
reuse pass. Receipt: tests/qualification/component-owned-worker-refresh-actual-20261017.json.
Dune was not rerun for this successor; no media/SDK/transport. Managed namespace
opening and automatic capture/selection remain next integration work. Main's
frozen RPC sources and separate admission requirements remain unchanged.

## Indexed worker routing — 2026-10-17

The same owned-worker successor now adds `components_indexed`: exact immutable
owner/root/path/generation selection runs inside the worker. Missing/stale entry
freshly extracts; matching entry authenticates its record and refreshes. A missing
selected record reports incomplete metadata, corrupt/foreign evidence fails,
and neither silently triggers extraction. Optional checkpoint capture supports
both routes without publishing or advancing the index/archive. No managed cache
loader or normal report-path installation is claimed.

Actual owner19704/4509e5/0/no session: current stock/Ox Make/fullselftests/Dune,
all five contained workers/groups/tokens closed; current production-source pins
and linked fixture/control artifacts independently rebound. Exact count and pins
are in component-indexed-worker-refresh-actual-20261017.json. Contract:
doc/component-worker-cache-routing.md. Main's reviewed frozen RPC still has no
fresh admission; observed Photo defer is scheduling evidence, not proof of a
currently live owner. No RPC retry/dispatch, media/SDK/transport or physical-read
savings claim follows from these worker controls.


## Managed store successor started — 2026-10-17

Active checkout `/Users/alexy/src/unison-component-store-20261017`, branch
`feat/component-cache-store`, based on PR9 d074fb8b. Source now adds quota-bound
exclusive stage creation for record/entry/manifest, one attempt per role with
actual creation state retained. Returned descriptors are caller-owned immediately;
no post-open allocation/validation/close in the native opener. Added production
namespace controls for private empty files, creation flags and replay refusal.
These changes are UNBUILT/UNTESTED; diff whitespace check alone passed. Next qualify
native/fault paths, then compose owned staging/publication and archive-head CAS.
No payload/SDK/RPC invocation or new resource grant; no active owned job.


Managed-store composition now exists in source: frozen entry/checkpoint/index CAS
preparation, one-use quota-bound stage ownership, pair publication followed by
manifest publication, reference/index access only after all owned scopes return.
Readers retire BEFORE rename; an actual production-linked test caught the initial
reader-live rename error, fixed without weakening file-change checks. A subsequent
control corrected its own reuse of a consumed one-shot namespace ticket by making
an explicit identity-bound fresh read ticket. Failed runs 001/002/003 all closed
workers/groups/tokens; no payload/SDK/transport was involved. Initial stage-only
qualification002 passed both compilers (actual1806/89678c/0). Combined run004 is
being collected; do not infer its result from this preparation note. Fault-injected
store paths, full builds, guarded archive adoption and automatic routing remain
unqualified/incomplete. No production activation or new admission.


Combined managed-store run004 subsequently PASSED: actual92385/ef8c02/exit0/no
session; containedworker79464reaped0/othersabsent/tokensclosed/sourceunchanged.
Both compilers' normal native store publication/cold-load controls pass alongside
existing loader/namespace suites. Exact evidence and raw pins are in
`tests/qualification/component-managed-store-normal-actual-20261017.json`.
No active owned jobs/resources; store fault injection and archive adoption next.


## Store failure qualification and archive guard — 2026-10-17

Composed store close uncertainty at entry/record/manifest/namespace passed both
compilers, then all four open failure positions and every observed sync position
passed. Actual fault-run002 owner35661/d0009b/0/no session; worker80600reaped0/
othersabsent/sourceunchanged/tokensclosed. Native fault wrapper now forwards the
O_CREAT mode argument and accepts managed O_RDWR stages; production has no fault
switch. Exact evidence: component-managed-store-fault-actual-20261017.json.
No retry, failed reference adoption or numeric-FD retry; uncertain descriptors and
known outer scopes remain represented. Tests explicitly close only known retained
FDs after the disposable wrapper has consumed the uncertain FD.

Update.adopt_component_cache_store source now performs loaded-head expected-value
comparison and requires a normally settled store before memory adoption. This
Update integration is NOT compiled/linked/qualified yet; normal archive commit and
automatic report routing remain outstanding. Contract doc/component-managed-store.md.
All test owners/groups/tokens currently closed; no new payload or SDK grant.


## Managed store production build/archive qualification — 2026-10-17

Current stock Make/fullselftests actual83029/a14d82/0 and Ox Make/fullselftests
95059/acef23/0 passed; workers81233/82368 genuinelyreaped0/groupsabsent/tokensclosed.
Production-linked archive controls actual88636/1ca3ca/0, worker83613reaped0/groupsabsent
passed BOTH compilers: unsettled-store refusal, changed-head CAS refusal preserving
old hint, normally settled store adoption, normal archive commit, fresh-process
identity-bound namespace reopening, trusted manifest/entry/record cold reload.
Exact pins: component-managed-store-archive-actual-20261017.json. No SDK/media/
transport or source photos; no live owned jobs/resources. Dune and integrated
normal report automatic capture/reuse remain next work. This supersedes the
previous note that Update adoption was uncompiled, without changing old evidence.


Current stock/Ox Dune compile checks now PASS: actual controller26178/7c4947/0/
no session, stockworker84057 andOxworker85101reaped0/groupsabsent/tokensclosed.
Receipt component-managed-store-dune-actual-20261017.json pins both reports.
Current SemanticRemote inspection still uses fresh uncached components; durable
namespace identity and owner-loop/asynchronous report routing remain explicit
implementation work, detailed in doc/component-managed-store.md. SOL status
updated accordingly. No active owned jobs/resources or payload grant.


## Durable namespace identity implemented — 2026-10-17

Optional UAN/0 fixed152B archive tail now binds namespace device/inode to exact
archive context, owner binding and manifest digest. Normal settled-store adoption
copies identity+reference together; raw legacy setter clears stale identity;
clear removes both; neither private key enters legacy serialized properties.
Missing/malformed/foreign/oversized identity becomes None, not archive reset.

Actual framing/native controls65040/e91a13/0 and full stock/Ox Make+selftests+
production archive persistence controller67113/1fa76a/0 PASSED. All workers86966,
88074,89253 and controls86539 reaped0/groupsabsent/tokensclosed. Fresh-process
store probe now reopens using Update.component_owner_namespace restored FROM
archive, not a separate identity file. Exact pins component-namespace-archive-
actual-20261017.json. Retained old-code new-tail compatibility and Dune still
pending for this successor. Automatic report routing remains incomplete; no
media/SDK/transport or active owned resources.


## Namespace-tail old-code compatibility — 2026-10-17

Actual retained pre-component production Update/Proplist/native objects now read
current stock/Ox archives containing BOTH UAX/UAN tails byte-exact, rewrite them
without either optional hint, leave all three published cache payloads unchanged,
and current code restores the ordinary archive with no manifest/namespace authority.
Actual30670/a9bf3e/0/no session; worker89496 reaped0/groupsabsent/tokensclosed,
13 direct calls settled. Original retained CLI was rehashed, not invoked. Exact
receipt component-store-namespace-legacy-actual-20261017.json. Source/build pins
unchanged; only fixed probe gained an explicit legacy-missing phase. No all-old-
versions/network/platform/media claim. No live owned jobs/resources. Next actual
implementation: endpoint-owner report orchestration with scoped metadata load,
immutable worker await, source/head recheck and optional capture; no synchronous
namespace scope may span that await. Automatic routing is still NOT implemented.


## Endpoint-owner report orchestration — 2026-10-17

Update.inspect_cached_components now loads scoped authenticated index/record,
closes all metadata descriptors before the worker await, runs indexed full-input
inspection with checkpoint capture, rechecks source FD/path and archive head,
skips unchanged-entry publication, or performs owned store and guarded adoption.
Legacy no-identity hints stay cold. Exact-key prior-entry reference supports CAS
across generation changes without granting stale-generation restore authority.

Current stock98891/0a922c/0 andOx40800/3c2be3/0 full Make/selftests PASS; explicit
owner-path controls39802/dd809c/0 and bothcompiler40800/3c2be3/0 PASS: original
8192B DNG automatic capture, repeat unchanged-head reuse, normal archive commit,
fresh-process restore+repeat reuse. All contained workers/groups/tokens closed.
Receipt component-owner-report-actual-20261017.json. This is NOT yet wired into
SemanticRemote/UI; private-parent selection/provisioning, failure/cancellation
race controls and Dune remain. No payload/SDK/transport grant or live resources.


## Report cancellation/head-change qualification — 2026-10-17

Owner orchestration now checks cancellation before parent access and after worker
reply. Original controls prove invalid-parent pre-cancel no access; submitted-job
cancel returnsNone with unchanged head; another owner head change during await
refuses stale report adoption. Stock/Ox full Make/selftests and corrected original
controls PASS; currentactual63987/0e9544/0/no session, worker94018/95262reaped0/
groupsabsent/tokensclosed; correctedstock16994/ecc9a9/0. Initial60471/4d70d6/1
preserved: buildpassed, test wrongly injected through diagnostics AFTER reply;
no production failure relabeled. Receipt component-owner-report-cancellation-
actual-20261017.json. Allresourcesclosed. Explicit owner API remains separate
from unwired SemanticRemote/UI; no payload/SDK/newgrant.


## Draft review checkpoint — 2026-10-17

Qualified source8e84a6a8 is pushed as draft PR11:
https://github.com/querygraph/unison/pull/11, base feat/component-cache-namespace
(PR9). No PR merge/production activation is authorized or claimed. This successor
contains managed store, archive-owned namespace identity, explicit owner report
capture/reuse, and cancellation/head-change fences. UI/SemanticRemote route and
its private-parent asynchronous ownership remain unimplemented; latest Dune does
not cover later identity/report changes. All actual jobs/resources closed.


## Current owner-report Dune gap closed — 2026-10-17

Current-source stock/Ox Dune compile checks PASS actual69606/f7728c/0/no session.
Workers95833/96873 reaped0/groupsabsent/sourceunchanged/tokensclosed. Evidence
component-owner-report-dune-actual-20261017.json supersedes pending-Dune notes
for source8e84a6a8 (later commits metadata only). No report UI activation, media,
SDK or transport run. Next code: explicit async parent-descriptor owner and
local report entry-point integration; outer parent must remain retained on
nested uncertainty. Allactualjobs/resourcesclosed.


## Opt-in local report entry wired — 2026-10-17

UI component details now calls SemanticRemote.observe_components_with_worker
using Update.inspect_configured_components. Existing observe_components API and
remote wire route remain unchanged. Both componentownercache=true and explicit
existing absolute private0700 componentcacheparent are required; optional %ROOT%
root-SHA expansion supports distinct pre-provisioned parents. No recursive mkdir,
discovery, remote cache, production activation or source permission is implied.

New explicit parent owner records before validation, normal closes once, refuses
settlement replay, preserves original cause on close uncertainty and retains known
outer FD on nested uncertainty. No finalizer/numericFDretry. Actual fault/native
controls75816/bd9a22/0; configured stock64824/d9b260/0; Oxbuild+bothdirect-local-
entry controls99167/236a7c/0 PASS; all worker/group/tokens closed. Current stock/Ox
full Make+selftests passed. Direct production SemanticRemote entry (same UIcallback)
proved exact generatedDNG report/capture/repeat/restart/head/cancellation; no manual
GUI session claimed. Receipt component-local-report-route-actual-20261017.json.

Initial stock13845/cb14a4/1 failed source build: invalid string preference API;
fixed send:false and separated observer entry to preserve old caller shape.
Preserved, no tests/source payloads ran there. Dune for this successor pending.
Remote routing and parent path replacement/concurrent-owner stress remain open;
no active owned resources or SDK/media/transport grant.


## Review finding: outer report reservation retention — OPEN

While parent-replacement qualification ran, source review found that generic
SemanticAdmission.with_lease retires on exceptions. A propagated cache ownership
carrier retains its FDs, but that alone does NOT prove the outer report resource
reservation stays held. Before claiming UI uncertainty qualification, add a
component-report-specific held/pending boundary INSIDE with_transaction, retaining
the carrier and reservation until explicit independent settlement. Test actual
cache uncertainty from a disposable invalidated owner descriptor; pending promise,
unchanged admission usage after cancellation, and diagnostic retained carrier.
Do not describe descriptor-only controls as proving outer admission retention.
No actual uncertain FD or retained job currently exists; this is a source finding.


Parent replacement/permissions source now checks before metadata load, after
worker await and between completed store and archive adoption. Configured legacy
no-identity hint bypasses parent opening. Actualstock45168/dc7a41/0; combined
Ox+bothcontrols+bothDune7405/d32134/0 allPASS, allworkers/groups/tokensclosed.
Exactreceipt component-local-parent-replacement-actual-20261017.json. This proves
those refusals/builds, NOT the separately open outer-admission uncertainty issue.
Next fix that held-boundary before broader activation/remote work.


## Outer report admission finding FIXED/QUALIFIED — 2026-10-17

This supersedes the OPEN finding above for the local cache-carrier route. Local
SemanticRemote now retains Cache_ownership_uncertain INSIDE with_transaction via
preallocated held promise/node/link and owner diagnostics. The outer lease cannot
mistake it for an ordinary failed callback and retire credits. Generic admission
policy unchanged; no automatic recovery/numericFDretry/normal-close assertion.

Original production-linked probe produces actual uncertain close after deliberate
private owner-FD invalidation, then tests real local report entry: pending promise,
retained carrier, charged transaction/payload/FD credits unchanged after helper
cancellation, no archive-head mutation. Application admission remains intentionally
held until disposable process exit; external direct child/group wait proves OS
closure, NOT native close or normal application retirement. Both stock/Ox retention
and normal-report controls PASS; stock/Ox Make+selftests/Dune allPASS. Actual68144/
6e0d4a/0 and86411/1de5ba/0/no sessions; allcontainedworkers/groups/tokensclosed.
Receipt component-report-admission-retention-actual-20261017.json. First23717/
e57c75/1 sourcebuildfailure preserved (bundled Lwt.wait returns promise, notpair).
No active uncertain descriptor/resource now. Remote cache route and broaderlegacy
source-FD close audit remain separate; no SDK/media/transport or deployment.

<!-- Parallel historical checkpoint retained from RPC auditor branch. -->

## Isolated implementation pointers — 2026-10-17 storage successor

PR4 https://github.com/querygraph/unison/pull/4 is ready for review on
`feat/component-cache-input-binding`, qualified source835df2fc. PR5
https://github.com/querygraph/unison/pull/5 is a draft stacked on PR4, branch
`feat/component-owner-index`, latest sourcec372213a in sibling
`/Users/alexy/src/unison-component-index-20261017`. Its own OPUS-HANDOFF.md is
current for that successor; these implementations are not merged into this tree.

PR5 now provides bounded trusted root/path/generation selection, UIX/0 reference
manifest import/export and borrowed-FD staging/readback/one-shot macOS immutable
publication. It does not establish managed namespace installation, referenced
entry presence, quota admission/FD settlement, a separately trusted durable
owner-state commit, automatic routing or production activation. Unknown camera
fields remain exact opaque components; incomplete interpretation is not itself
a deployment gate. Existing UDI/0 bytes and main's frozen342RPC pins are unchanged.

Latest exact qualification is the isolated
`tests/qualification/owner-manifest-publication-actual-20261017.json`: focused
56956/e8cf00/0 and full85962/0cfdd3/0 terminal/no sessions, all7adoptedworkers/groups/
tokensclosed. Percompiler56component+1005checkpoint+27publicationfault+13readerfault+
1248DNG+110workerchecks, four current stock/Ox Make/fullselftest/Dune compile builds,
1272sourcechecks. Framing vectors count as controls, not additional camera fixtures.
No media/SDK/transport, production writes or new resource grant. The main prepared
RPC still requires its fresh exact admission; no dispatch follows from this note.


## Current archive-reference successor — 2026-10-17

Draft PR6 https://github.com/querygraph/unison/pull/6, sourcef171539b/metadata
d8cf5566, lives on `feat/component-archive-hints` in sibling
`/Users/alexy/src/unison-component-archive-20261017`, stacked on PR5. PR4/PR5 are
ready review levels; none of this successor is merged into main. See that
branch's current OPUS-HANDOFF.md and `doc/component-archive-hints.md`.

The default-off endpoint-local componentownercache option persists explicit
normally-published manifest references through the normal archive transaction.
Its private property key is removed before legacy payload serialization; UAX/0
is an optional tail after the existing paths map. Archive format23/default-off
serialization/negotiated features are unchanged. Rename+directoryEIO cannot grant
an owner reference. Missing/malformed/off hints never promote self-hashed blobs.
No automatic capture/reuse or managed namespace installation yet; actual old-
CLI compatibility/hardware power-loss/legacy close-fault qualification remain
open. Retained old production-object compatibility is now qualified below.
This is local cache ownership, never common-file reconciliation authority.

Exact isolated evidence `tests/qualification/component-archive-hints-actual-20261017.json`:
focused63243/2ab595/0, full96641/27b99d/0 terminal/no sessions. Current stock/Ox
Make/fullselftests/Dune1272SRCchecks,1391DNG+29archive-publication-fault+110worker
checks/compiler and14linked private archive calls/6phases percompiler pass. All8
adoptedworkers/groups/tokensclosed. Test-only import/symbol/preference setup
failures preserved. No source-file payload, SDK/Adobe, remote process or transfer.
Main frozen342RPC source remains unchanged; exact admission still required.

Archive successor 4d1dcc6f adds actual retained pre-change production-object
reader/writer compatibility evidence, pushed to PR6. Owner12014/2441f7/0 and all13
direct calls settled: old reads preserve exact current stock/Ox archive bytes,
old rewrites drop only the optional hint, the current reader safely misses, and
the manifest payload stays unchanged. Source/artifact pins were independently
rechecked. See that branch's component-archive-legacy-actual-20261017.json.
This does not execute the untouched old CLI or qualify all old releases/network
transfers. Production source and main's frozen RPC closure remain unchanged.


## Integration source checks complete — 2026-10-17

Local mergef5b496f5 combines PR11+PR10 without production source conflicts. All390
tracked production paths equal6b4d5204 and every SRC pin in the final four
stock/Ox Make+selftest/Dune reports rebinds to this candidate. Auditor22+8+6groups
passed actual76033/d65499/0/no session; all3worker/groups/tokensclosed. 46sealed
metadata references and original exactseal2ce13be0 unchanged. Receipt sol-
integration-source-actual-20261017.json. First relative-script launch refused
before worker dispatch; unused output001 preserved, fresh002 ran once.

Updated doc/current-qualification-status.md is current over its historical
scheduling paragraphs. No GitHub merge, media/SDK/RPC/payload/native/benchmark
run or new admission. Next concrete work: twelve-row SOL acceptance evidence
review and material current candidate gaps; do not restart consumed runs or gate
baseline deployment on exhaustive MakerNote meanings. Zero owned resources now.


## Twelve-area acceptance review — 2026-10-17

Created doc/sol-release-readiness-20261017.md and machine-readable selected receipt
source-pin review. Existing implementations and exact historical/current scopes
are mapped to all12requirements; no full-goal completion claim. Old merge receipts
have62changed explicit production bindings, worker scheduling22; no automatic
current execution inference. Zero extracted pins means not rebound, not pass.
Concrete nextsafeaction: current-object original worker apply/cancel regression,
with bounded fixture setup (old driver unconditionally creates unused1GiBsparse
files). Then fresh pinned current transfer/mixed-peer and retained-camera requests
as needed, with newRootIO admission before dispatch. Legacy source-FD cleanup
uncertainty remains a source review item. No camera/SDK/payload opened; no jobs/
resources held. User excludes autonomous fuzz/sanitizer work and exhaustive
MakerNotes are not a deployment gate. Allprioradmissionsremainconsumed.


## Current worker apply regression closed — 2026-10-17

Actual86836/67c190/0/no session links current compiler-matched production objects
and passes seeded apply/cancel on stock andOx; workers16370/16398reaped0/groups
absent/tokensclosed. Sixseeds×4batches×16jobs/compiler; exact completed targets,
cancelled-stage nonpublication, basis/target preservation, permits/queues/descriptor
baselines pass. Unused1GiB sparse files are not created. Receipt integration-
worker-apply-actual-20261017.json has exact observed counts/source/object pins.
Initialstock001/002/003 compile/link failures preserved/closed before applyjobs:
record type ambiguity, missing snapshot dependency, then clone dependency. Test
harness inventory/type/setup changed only; production candidate is unchanged.
No camera/SDK/transport/bulkIO/native grant. Next prepare finite current transfer/
mixed-peer request with exact pins, coordinate freshRootIO; no oldadmissionreuse.


## Fresh integration property IO request published — 2026-10-17

Immutable doc/sol-properties-request-v1.json 57681B SHAe60975f3dff2fc9f95da6aa254d9726550ffbc30bc258591eb5f2a7679f3a787
is queued to PhotoRoot as01a14991-ce52-7ef0-9ff0-ef72b31c058c. Existing qualified
sync-functional property-removal route:18rows/54CLI/generated2MiB inputs/retained
readers<=36, Unison00..07+EXglobal,300sobservation/30sCLI/unknownretains, declared
uninstrumented8GiB. No compiler/SDK/camera/Photo payload/mixed-peer/timing claim.
38execution+318production pins,7prereqs and interpreter/binary/compiler hashes;
manual.command and checked_build metadata checks passed (no target executed).
Workspace /private/tmp/u-sol-properties-86df187d7c95 and proposedadmission
/private/tmp/unison-sol-properties-admission-86df187d7c95.json were absent at
request publication. Root review/grant is not assumed from queue/resource release.
Runtime must use fresh published SHA/deadline once and exact request command; no
oldgrant/retry. No owned jobs/tokens/IO held. Keep this candidate's execution pins
frozen pending review; independent source work should use a sibling successor.


## Independent component source-FD successor — IN PROGRESS 2026-10-17

Checkout /Users/alexy/src/unison-component-source-owner-20261017, branch
fix/component-source-fd-owner, based on frozen integration72a19d9d. Submitted
property request in integration checkout remains unchanged. Latest read at
Unix1792235853 found no admission; no payload/IO run is started or assumed.

Source inspection found legacy held_files cleanup could downgrade source-close
uncertainty. The component inspector now records explicit regular source ownership
before validation, waits for worker completion, closes once, and merges nested
cache uncertainty into retained source ownership. Existing other transfer/inspection
families are unchanged. The component RPC source scope now also holds its outer
admission on the same carrier (wire schema unchanged). Carrier origin can be a
regular file; new cache_origin_descriptor accessor makes that explicit.

Directed stock/Ox native/fault controls actual64616/a62110/0 passed; worker17616
reaped0/groupabsent/tokensclosed. Source-owner EIO retains regular identity and
rejects second close. Full stock build/selftests ACTUALtool68157 now started in
/private/tmp/unison-source-fd-owner-stock-make-20261017-001; collect terminal before
any competing own8 dispatch. Not yet full-build/route qualified, no new SDK/IOgrant.


## Component source owner QUALIFIED — 2026-10-17

Current source successor stock/Ox Make+selftests/Dune, directed regular-source
close uncertainty and normal/retained report controls PASS. Actual68157/f7fcc6/0,
86131/980c64/0,55793/0e866e/0 andauditors57596/22ac80/0/no sessions; allcontained
workers/groups/tokensclosed. All36auditorgroups pass with unchanged wire schema;
no actual new transport. RPC source scope now holds admission on carrier too.
Receipt component-source-fd-owner-actual-20261017.json pins exact objects/sources.

Frozen integration property requeste60975f3 andall38execution+318productionpins
rehashed unchanged AFTER source work; its admission still not inferred. This fix
remains separate, notmergedintofrozencandidate. Other legacy semantic/transfer
cleanup families remain outside this scoped fix; no blanket settlement claim.
Zero owned jobs/resources; no SDK/camera/Photo payload/native/IO dispatch.


Review now OPEN/DRAFT PR12 https://github.com/querygraph/unison/pull/12, exact
qualified sourceecad82f3/base integration/sol-release-candidate. No merge or new
runtime grant. Frozen propertyrequest remains in integration checkout; current
XMP kernel controls there separately passed without production changes. All
owned jobs/resources closed. Continue source work here without modifying the
submitted candidate's execution pins until that scheduling request is settled.

<!-- Parallel integration history retained. -->
Independent source-FD cleanup successor now QUALIFIED ecad82f3 in
/Users/alexy/src/unison-component-source-owner-20261017, branch
fix/component-source-fd-owner. Component reports record regular source ownership
before validation and retain close uncertainty/nested source ownership; RPC source
scope holds admission on the carrier. Current stock/Ox Make+selftests/Dune and
normal/retained report +36auditorcontrols pass; allactualjobs/resourcesclosed.
Exact receipt component-source-fd-owner-actual-20261017.json is in that sibling.
This code has NOT been merged here: property requeste60975f3/all38execution+
318productionpins reverified unchanged. Runtime request remains separately
pending, no payload/admission/hold inferred. Other legacy cleanup families still
require their own scoped review; no blanket source-FD release claim.


## Review publication and current XMP kernel — 2026-10-17

Source-FD fix ecad82f3 now OPEN/DRAFT PR12
https://github.com/querygraph/unison/pull/12, base integration/sol-release-candidate.
Base branch is published at72a19d9d; no GitHub merge. Submitted propertyrequest
pins unchanged; latestmetadata atUnix1792236111 had no admission.

Current integration XMP kernel actual65346/7f6982/0/no session PASS stock5.2.0/Ox:
25scalar+343rating/symmetry+4RDFconflicts; Ox4checked domains+checkedspawn. Both
workers23127/23166reaped0/groupsabsent/tokensclosed. Driver now copies/pins mandatory
EVPheader; no production changes. Receipt integration-xmp-kernel-actual-20261017.json.
This closes current kernel-source reexecution, NOT live merge receiving/SDK.
No active owned resources, no payload/IO admission or replay.


## Current worker pool parity — 2026-10-17

Actual75221/88a8e1/0/no session passes stock/Ox current-production-object64jobs
atconfigured1/2/4/8, queued cancellation, exact hash/proof parity, descriptor/CPU/
queue recovery. Executingcredits cap6+owner2 within standing8. Workers23693/23707
reaped0/groupabsent/tokensclosed. Focusedparity omitsunused1GiBsparsefixtures.
Receipt integration-worker-parity-actual-20261017.json. No newproduction/source
pin changes to pendingpropertyrequest. No IO/SDK/camera/transport invoked; no
speedup/hardthread/RSS/8executing inference. No actualownedjobs/resources now.


## Current standalone inspector readiness — 2026-10-17

Build-only actual84256/0cfdfb/0/no session stock/Ox PASS,0inputopens/0inspectorexec
withinbuild. Mandatory productionEVPheader nowcopied/pinned. Subsequentoriginal
tiny integration actual8c9c05/0 (16calls) andreuse/refusal29cc1b/0 PASS; allcontained
workers/groups/tokensclosed. Strict/layout classifications and separate metadata,
encodedpixels andopaque changes proven by actualJSON/fullhash plusunchangedsource
epochs/bytes. Receipt integration-inspector-ready-actual-20261017.json pinsbuilds,
logs/source/artifacts; no realcamera/SDK/pixel/receiving/runtimeIO grant inferred.

This tooling can support a later separatelyadmitted privatecamera exact plan;
do not use oldconsumedclone/SDK grants or assume profileeligibility. Currentproperty
requeste60975f3 remainsseparatepending, its38execution/318productionpinsunchanged;
tool/harness-only edits are outside that closure. Zeroactualownedresources now.

<!-- Main navigation history retained. -->
## Resume checkpoint — current state on 2026-10-17

This section supersedes earlier pending-RPC and next-step scheduling notes;
historical receipts and sealed documents remain unchanged. User resumed the goal.

- The single component RPC run is consumed and resource-closed: actual owning
  tool91491/7ec39a/exit1/no session. All eight commands settled; the original
  final auditor failed on an invented `cancel_reason` field. Saved-only corrected
  audit and Root narrow functional adoption are recorded in
  `doc/component-remote-root-adoption-addendum-20261017.md`. Preserve original
  exit1 and sealed bytes; do not rerun its admission.
- PR7 (owned/indexed worker refresh), PR8 (managed read loader), and PR9
  (private namespace lifecycle) are implemented and qualified in their isolated
  sibling checkouts. PR9 branch `feat/component-cache-namespace` is at d074fb8b;
  its handoff contains detailed qualification and limits. These are unmerged.
- PR10, `feat/component-rpc-producer-audit` at 5f350db6, is a separate draft
  against this feature branch. It fixes future auditor producer schemas with
  36 original control groups. Main's frozen342-source runtime and old sealed
  return remain unchanged. No new RPC runtime is admitted or necessary merely
  to acknowledge this source correction.
- The next implementation checkout is
  `/Users/alexy/src/unison-component-store-20261017`, branch
  `feat/component-cache-store`, initially at d074fb8b. Only the checkout has
  been created: no store code, tests, build, runtime, or resource reservation
  has started there. Planned work composes bounded capture/staging/publication,
  manifest completion, and guarded archive-head adoption, then automatic
  capture/report routing. Close uncertainty must retain all ownership.
- Remaining release work: finish automatic incremental cache capture/report
  integration; consolidate the unmerged stack into a reviewable candidate;
  run integrated compatibility/failure and supported-scope acceptance checks.
  Exhaustive MakerNote interpretation is not a deployment prerequisite:
  unknown bytes stay exact and hash-covered, with versioned incremental
  refinements and old views retained.
- At this checkpoint no known owned job, CPU token, IO barrier, or admission is
  active. Standing Unison8/Photo8/system2 applies; future payload/SDK/transport
  work needs its own exact coordinated admission. No old grant is reusable.

Keep this main navigation document and the active successor's handoff updated
at substantive implementation/qualification checkpoints. No merge authorization
for PR2 or PR4–PR10 is implied by continuing the goal.


## Managed store checkpoint — 2026-10-17

Successor branch `feat/component-cache-store` in
`/Users/alexy/src/unison-component-store-20261017` is now bf0527b0. Its managed
store composes quota-bound exclusive stage creation, authenticated record/entry
and manifest publication, full owned-descriptor settlement, and guarded in-memory
archive-head adoption. Both stock/Ox Make builds/fullselftests and real production
archive commit/fresh-process cold load passed. Original tiny failure controls
cover four close-uncertainty positions, all four opens and every observed sync;
94 composed failure checks/compiler passed, preserving partial effects and no
adoptable reference on failure. All actual workers/groups/tokens closed.

See that checkout's current OPUS-HANDOFF.md, doc/component-managed-store.md and
component-managed-store-{normal,fault,archive}-actual-20261017.json receipts.
This code remains isolated/unmerged; no PR or production activation is claimed.
Automatic normal report capture/reuse routing and Dune/integrated release checks
remain work. This supersedes the earlier checkout-only pointer, not sealed RPC
or other historical evidence. No payload/SDK/transport/new resource grant occurred.


## Current managed-cache draft PR — 2026-10-17

PR11 https://github.com/querygraph/unison/pull/11 is now OPEN/DRAFT, stacked on
PR9 feat/component-cache-namespace. Qualified source8e84a6a8 in sibling
`/Users/alexy/src/unison-component-store-20261017` includes archive-bound namespace
identity, retained-old-code compatibility, explicit endpoint-owner worker/capture/
reuse orchestration and cancellation/concurrent-head fences. Current source
stock/Ox Make+selftests and original owner-route controls passed; all processes
and grants closed. Source before the later identity/report additions also has
Dune qualification; current-source Dune remains pending. The active successor
handoff has exact source/receipt pointers and preserved failed-control history.

No default SemanticRemote/UI cache routing yet. Its private-parent ownership and
loaded-owner integration remain actual implementation gaps, not camera-knowledge
requirements. No merge, production use, media/SDK read, old admission reuse or
new resource hold follows from the draft. Main's frozen RPC342 and sealed bytes
remain untouched.


## Local report successor current — 2026-10-17

PR11 source is now6b4d5204 (pushed). UI component details has opt-in local cache
routing via explicit private componentcacheparent, owned parent lifetime, configured
path/permission rechecks, capture/reuse/restart and cancellation/head fences. Local
cache uncertainty now keeps both descriptor carrier AND outer report admission
held; actual original probes distinguish application retention until exit from OS
child/group closure. Current stock/Ox Make+selftests/Dune and normal/retained report
controls pass; exact source evidence in sibling store checkout's currenthandoff.
No active owned resources. Earlier navigation saying UI remains unwired is now
historical. Explicit parent provisioning, remote endpoint cache route, broader
legacy source-FD close audit, stack consolidation and final integrated acceptance
remain open. No merge/production/media/SDK/transport grant or full-goal claim.


## Consolidated local candidate — 2026-10-17

Current integration checkout `/Users/alexy/src/unison-sol-integration-20261017`,
branch integration/sol-release-candidate, HEADb3d6ef9d, combines PR11 managed/local
report source6b4d5204 and PR10 independent producer auditor5f350db6. No GitHub PR
merge. All390 tracked production paths unchanged versus qualified cache branch;
all production SRC pins in final stock/Ox Make+selftest/Dune reports rebound.
All36auditorcontrols passed actual76033/d65499/0/no session; allworkers/grants
closed. 46sealedmetadatareferences and originalseal2ce13be0 unchanged. Candidate
receipt sol-integration-source-actual-20261017.json and current qualification index
now replace stale pending-admission/cache-not-wired navigation. Full SOL twelve-row
acceptance review remains next; no media/SDK/RPC/native/benchmark grant or replay.


## Latest review and regression pointers — 2026-10-17

Draft PR12 https://github.com/querygraph/unison/pull/12 now reviews qualified
component source-FD owner sourceecad82f3, metadata66315d9f, against published
integration base72a19d9d; no merge. Independent fix checkout and currenthandoff:
/Users/alexy/src/unison-component-source-owner-20261017. It closes the component
report source-cleanup gap and holds RPC source admission on uncertainty, with
stock/Ox Make+selftests/Dune, directed controls and36auditorgroups passing.

IntegrationlocalHEADc49a26fb adds current bounded worker384job/1255checks each and
current scalar XMP25+343+4controls (Ox4checked domains). Allactualjobs/resources
closed. Frozen source/IOrequeste60975f3 is queued01a14991-ce52 for18row/54CLI property
regression; no admission present atlastread, no runtime dispatch or new grant.
No oldgrantreuse; source/productionpins for that request remain unchanged. The
release readiness document and activeworktree handoffs retain exact evidence and
remaining claims. Broader actual transport/camera work remains separatelyadmitted.


## Consolidated final review source rebound — 2026-10-17

Both local integration merges changed documentation/harnesses only. Every SRC pin
in source-owner stock/Ox Make+selftest/Dune receipts matches this tree. Fresh
standalone inspectors actual46063/73e87f/0/no session built from this tree and all16
original tiny strict/layout/component integration calls pass. Allworkers25192/
25244/25306reaped0/groupsabsent/tokensclosed. Receipt consolidated-review-source-
actual-20261017.json binds exact reports and rebuilt inspector artifacts; no
newproductionCLI/SDK/transport/camera execution. Rootpropertyrequest remains
frozen in separate checkout; no substitution or automatic successor.


## One consolidated review now open — 2026-10-17

Draft PR13 https://github.com/querygraph/unison/pull/13 is the single consolidated
candidate against querygraph/unison:master. Initialsourceheadf188a6a6 includes
qualified sourceowner ecad82f3 and all current integration controls/navigation.
All prior PRs remain separate; no merge/close/replay or production use occurred.
Current source build rebind and freshinspector proof are in consolidated-review-
source-actual-20261017.json. Pending property request remains at its separate
frozen checkout/requeste60975f3; admission required before actualdispatch. No
activeownedresources. Review limitations remain explicit; fullgoalnotcomplete.


## Cold first-report namespace fix — latest 2026-10-17

Actual before-fix control reproduced cancelled first report creating an unadopted
namespace (testworker1, expected-counterexample controller81260/106d7b/0). Cold
NoRef/NoIdentity now inspects with an empty in-memory index first. Cancelled or
unsupported outcomes leave parentempty/hintNone; only fenced successful capture
creates/publishes namespace. Existing trustedcache still loads before await.
Publication-failure orphans remain preserved; no unsafe automatic adoption.

Current stock39713/d7a95e/0 andOx+bothcontrols+bothDune7204/2fd03f/0 PASS, all
workers/groups/tokensclosed. Receipt component-cold-cache-first-failure-actual-
20261017.json pins the preserved failure and fresh successes. This supersedes
source-identical-to-ecad notes for Update; other production files unchanged.
No IO/camera/SDK/transport dispatch. Frozen property request on integration
checkout remains untouched and requires its own exact fresh admission.


## Portable component source cleanup — latest 2026-10-17

Review found regular source owner accidentally reused macOS-only metadata_close.
Now source uses a dedicated POSIX close primitive on Unix, MLUnix.close onWin32;
shared close-once/uncertainty bookkeeping remains, cache publication staysMac-only.
Validation-failure cleanup also uses the portable source backend. No source-open
path/permission or wire contract change.

Directed stock/Ox controls actual78381/a36294/0 include C compiled-U__APPLE__ on
Darwin and6API checks/compiler: normal close, consumed settlement, original cause,
nonregular validation anddescriptorbaseline. Existing native fault/namespace/
store controls pass. Full stock/Ox Make+selftests/Dune and normal/retained report
actual21381/479836/0 PASS; allworkers/groups/tokensclosed. Receipt component-source-
portable-close-actual-20261017.json. NOTLinux/Windowsruntimequalification; noSDK/
camera/transport/IOgrant or activeownedresources. Frozenpropertyrequest unchanged.


## Current review and next work — 2026-10-17

Active consolidated checkout: /Users/alexy/src/unison-sol-review-20261017,
branch integration/sol-consolidated-review, qualified source head5362e000,
draft PR13 against querygraph/unison:master. The portable cleanup and cold-cache
fix above are implemented and qualified; no current merge authorization.

Latest source review found a pending optional-cache capacity issue: a new key at
the owner-index entry/byte limit can raise after successful source inspection.
Next change should preserve the valid report and skip optional capture when the
index cannot admit it, while retaining CAS/authentication for admitted stores.
This fix and focused capacity controls are NOT implemented or qualified yet.
User-facing cache setup/failure documentation also remains to finish.

Frozen property IO request e60975f3 remains in the separate integration checkout;
no fresh admission was present at the last check. Do not dispatch without its
exact fresh grant, or substitute this newer source/binaries. All owned jobs and
resource leases from completed qualification are closed. Standing CPU split8/8/2
remains authoritative. Handoff entries distinguish plans from actual results.


## Optional index capacity — implemented and verified 2026-10-17

This supersedes the pending capacity item above. A pure capacity admission check
now lets a valid inspection return without optional publication when the index
is full. Existing same-key replacements remain admissible if byte bounds fit;
actual stores still require the prior-entry CAS/authentication. Owner API allows
stricter bounded index limits; configured production defaults remain1024/8MiB.

Stock/Ox Make+selftests and focused production-linked capacity controls actual
88578/23fdf5/0 pass. One-entry real owner flow captures first file, returns the
second valid report without changing head/files/reservations. Same-key and byte
capacity checks pass. Both normal-report and retained-ownership controls actual
17325/1c568f/0 pass. All workers/groups/leases closed. Exact evidence recorded in
tests/qualification/component-index-capacity-actual-20261017.json. Manual now
documents opt-in cache setup, exact opaque coverage, capacity/quota and recovery
limits. No SDK/camera/transport execution or new admission; frozen property
request remains separate and unadmitted at last check. Full goal remains active.


## Ordinary semantic-report source ownership — 2026-10-17

Source review found inspect_file still using legacy held_files cleanup, where
an uncertain close could become ordinary Unavailable and retire admission. It
now uses the portable close-once source owner and the retained report carrier
inside its existing transaction/RPC scope. The existing component diagnostic API
also lists these ordinary semantic-report carriers. No wire format change.

Actual58002/c6f825/0/no session: fresh stock/Ox Make+selftests, ordinary semantic
source normal+injected-close controls, cached report write/read and component
uncertainty retention controls allPASS. Disposable copied C source alone uses
close interposition; production has no fault switch. Normal report closes once;
uncertainty stays pending with outer transaction/FD/payload charges and original
uncertain identity, no numeric retry. External child/group closure verified;
retained application reservations intentionally last until disposable exit.
Exact evidence tests/qualification/semantic-report-source-owner-actual-20261017.json.
All owned processes/CPU leases closed, no SDK/camera/transport execution. Legacy
transfer held_files/stage cleanup remains separately to review; do not generalize
this report-only proof. Property admission still absent at1792238193.2699368;
separate frozen request unchanged, no replay or replacement. Fullgoalactive.


## Transfer-source cleanup in progress — 2026-10-17

Current uncommitted successor factors a shared with_owned_source helper and
uses it in make_plan as well as ordinary semantic reports. Source planning now
retains uncertain portable close ownership inside its existing Source RPC scope.
No new wire/API, transport dispatch or IO admission. Exact current stock/Ox
build+selftest and shared-helper report controls are running under actual owning
tool10491; do not infer terminal from logs. Qualification results follow below.
Receiver held_files and StagePublication cleanup remain a separate concrete gap;
doc/transfer-source-ownership-review-20261017.md records the precise current flow
and required combined native/ML evidence. Frozen property request remains separate.

Transfer-source successor qualification now ACTUAL CLOSED10491/286e38/0/no
session. Fresh stock/Ox Make+selftests, exact shared-helper ordinary report
normal+uncertain-close controls, cache write/read and component retained-owner
controls allPASS; every worker/group/CPUlease closed. Receipt semantic-planning-
source-owner-actual-20261017.json pins exact artifacts. make_plan uses that helper
and is compiled/source-reviewed, NOT newly remotely executed. Legacy standalone
source held_files registry removed; receiver candidate registry unchanged.
Receiver native/ML cleanup gap remains, no full-goal completion or IOgrant.


## Native publication explicit-owner backend in progress — 2026-10-17

Current successor adds a distinct StagePublication.owned API; legacy public t
callers remain unchanged. Native carrier rooted before first descriptor retains
every uncertain close and remaining known handles, original native cause and
actual lifecycle phase. Repeated operations refuse with same preallocated carrier;
normal explicit abort/disarm releases the native root. Strict API is not wired
into Copy/SemanticSync/SemanticRemote yet; outer admission integration remains.
Details doc/stage-publication-owned-v1.md.

First controller13859/bfd53d/1 failed after stock owned43checks PASS because the
legacy runner argument was --compiler instead of --ocamlopt; no unknown process
left, all groups/CPU closed. Preserved001. Corrected controller17264/30d895/0
passed43new owned+58legacy tests per stock/Ox compiler, all child/group closures
verified. Fault wrappers only copied disposable C; native unknown application
owners intentionally last until process exit, not claimed normally closed.
Full stock/Ox Make+selftests and Dune are now owned by actualtool23195; final
terminal/qualification receipt follows. No transport/SDK/camera or bulk IO grant.

Native owned backend qualification ACTUAL CLOSED23195/7fb21f/0/no session:
stock/Ox Make+selftests and both Dune builds pass; all workers/groups/CPU leases
closed. Together with corrected17264/30d895/0,43owned+58legacy controls/compiler
pass. Exact receipt stage-publication-owned-backend-actual-20261017.json retains
001failure and002success/binaries/current source pins. Backend ONLY: no production
caller switched and no outer publication-admission qualification yet. Next migrate
caller transaction owners and non-suppressing cleanup together, with composed
fault controls; no transport/camera/SDK grant. Full goal remains active.


## Bound local publication owner migration in progress — 2026-10-17

SemanticSync's bound producer path now uses StagePublication.owned with a
preallocated guard inside its actual transaction reservation. Native uncertainty
retains the original higher-level cause, native carrier and remaining transaction
or loose descriptors; error/connection cleanup cannot release the guard. Legacy
Copy/remote/unbound/raw-pair/channel cleanup is not claimed migrated.

Initial11183/10b447/0 passed new normal/adopt/disarm/callback-close controls on
stock/Ox, but source review then corrected adoption-before-registration ordering
to preserve name cleanup on record allocation failure. That initial source is
superseded without changing its receipts. Current002 builds/controls owned by
actual69137; existing semantic producer handoff harness updated for owned API
and scope parameter, with actual regression run pending. No new transport/Photo
IO/camera/SDK grant; generated8192B fixtures only. Source/prior frozen property
request checkout remains separate, admission still absent at last observation.

Revised local migration002 ACTUAL69137/6e7f13/0: stock/Ox Make+selftests and
normal/adopt-close/disarm-close/callback-close composed controls allPASS. Native
uncertainty retains outer admission plus remaining known descriptors even after
connection cleanup; callback-failure original cause and published output preserved
where appropriate. Scope diagnostics are observations, no cleanup capabilities.
Actual5612/96b9cb/0 existing handoff suite32cases/compiler alsoPASS, including
record/register/adopt-after faults, callback preservation, borrowed cleanup deferral
and FD reuse. Corrected owned adopt instrumentation and internal scope parameter
are in test_semantic_handoff.py. No actual remote transport: its remote unit uses
existing in-process planner delivery. Both tools/groups/CPU leases closed.
Dune stock/Ox current verification is now actualtool2544, pendingterminal.

Local migration full verification ACTUAL CLOSED2544/c41a6f/0: both Dune builds
pass. All previous/current test process groups and CPU leases closed; exact pins
and scope in tests/qualification/local-publication-owned-actual-20261017.json.
Bound SemanticSync producer family now actually migrated and qualified for native
publication uncertainty, including guard/descriptor retention through connection
cleanup. Copy/remote/unbound/raw/channel cleanup remain distinct; no universal
resource-close proof or fresh transport/camera/SDK admission. Fullgoalactive.


## Bound remote receiver migration in progress — 2026-10-17

SemanticRemote bound receiving now mirrors qualified local native ownership:
owned publication, preallocated scope/pending promise inside receiver admission,
loose descriptor retention before adoption, candidate publication-pending/retained
flags, original cause and connection cleanup retention. Copy/unbound/raw/channel
handling remains separate. Current build+fourcomposedcontrols actualowner99104
stilllive; do not infer final outcome from intermediate logs. New remote control
uses two explicit in-process substitutions only (supported predicate and planner
delivery), no actual transport/SDK/Photo payload. Existing producer-handoff
internal create_bound_candidate calls now receive an explicit scope.
Exact new lifecycle and limits: doc/remote-publication-owned-v1.md.

Remote migration ACTUAL99104/933cae/0/no session: stock/Ox Make+selftests and
fourcomposed receiver cases/compiler allPASS. Private copied source replaces only
supported predicate and planner delivery; actual native/SDE/worker paths exercised,
not network transport. Adoption/disarm/callback-close uncertainty stays pending
with outer transaction charges and remaining known descriptors through connection
cleanup. Generatedsource/basis unchanged, original callback cause retained. All
workers/groups/CPU leases for this batch closed. Current handoff32case and both
Dune verification owned by actual50665; finalterminal follows. No fresh IOgrant.

Remote migration full verification ACTUAL50665/ae2ab3/0/no session:32handoff
cases/compiler and stock/Ox Dune pass, all workers/groups/CPU leases closed.
Exact evidence tests/qualification/remote-publication-owned-actual-20261017.json
binds current native/worker/source/controlled-copy artifacts and actual terminal.
Remote bound producer is now migrated for native publication uncertainty, not
actual transport-qualified by these in-process units. Ordinary Copy plus unbound/
raw/channel ownership remains next; actual transport requires separate admission.
No replay/SDK/camera/Photo payload or new bulk IO grant. Fullgoalactive.


## Ordinary bound local clone migration in progress — 2026-10-17

Copy bound local clone helper (source-clone + local receiver-basis APIs) now uses
owned native publication. A preallocated producer guard stays INSIDE actual
TargetBinding.with_producer reservation. Unknown native ownership retains native
carrier, original cause, loose FDs or channel objects. Physical-identity channel
registry guards prevent connection cleanup or close-noerr fallback from closing
those retained objects. Network rsync/native-v0 named/unbound/raw/channel errors
remain separate; not a universal Copy migration.

Actual28281/a1f9c7/0 stock/Ox Make+selftests+first4composed controls/compilerPASS.
Actual89368/0da3c2/0 both DunePASS; also source-only final-caller instrumentation
seam updated so completion log occurs only after known producer success (not
before uncertain pending guard); no actualCLI dispatch. Current expanded6cases
adds actual copyByPath/copyLocalCloned APIs under real admittedTargetBinding tickets,
all8192B original fixtures/source+live metadata fences. Expanded owner terminal
follows; no new SDK/camera/bulkIO grant.

Ordinary bound local expanded verification ACTUAL15866/017f78/0/no session:
6cases/compiler allPASS, including actual copyByPath and copyLocalCloned, normal
guarded producer completion, source/live inode/mode/uid/gid/nlink/size/mtime/ctime
fences, native uncertainty reservation/channel retention through ticket release
and connection cleanup. Initial4case source/build batch preserved; production
source unchanged while expanding controls. All external groups/CPU leases closed.
Exact evidence tests/qualification/copy-bound-owned-actual-20261017.json.
Network rsync clone staging, legacy named-source/unbound and raw/channel close
errors still separate. Future actualCLI instrumentation source-only matched, no
CLI/transport/SDK/Photo payload executed or new IOadmission. Fullgoalactive.


## Guarded rsync receiver ownership — implemented/qualified 2026-10-17

Copy network-rsync staging selects owned publication for modern guarded producer
tickets; legacy/older peers retain original API. Adapter owns raw clone handles
then channels, attaches range lease, preserves EOF flush/truncate/check/publish/
adopt/disarm ordering. New synchronous borrower brackets preprocessing/decoding
and local clone writes. Connection cleanup invalidates lease immediately, defers
native/channel closure until borrowers finish; normal EOF close differs from
interruption. Intrusive active-owner list protects held channel objects and
unlinks known normal owners without allocation; unknown retains producer scope.

Actual24872/ba2f1b/0 stock/Ox Make+selftests+initial5stream+6localcases/compiler;
actual96532/7b6734/0 expanded7stream andbothDune; actual98668/b6bdf1/0 final8stream/
compiler. Source unchanged between control expansions. Normal changed/growth/
shrink/fullyinherited bytes exact; progress hook proves no native close under
decoder borrower and range authority already invalidated. Injected native close
uncertainty retains ticket/channel/resources; nonfaulted cancellation retires
known reservation normally. Source/live bytes+metadata unchanged, all external
workers/groups/CPU leases closed. Unknown application/native objects intentionally
last until disposable process exit, not claimed normally natively closed.

Evidence tests/qualification/rsync-publication-owned-actual-20261017.json and
doc/rsync-publication-owned-v1.md. Tests replace ONLY compressRemotely delivery
with actual in-process codec+receiver callback; NOT actual transport/server/pump
verification. Legacy named/unbound/old-peer and raw/channel close errors remain
next. No new SDK/Photo/camera/bulkIO grant; frozenproperty request still separate
and unadmitted atlastread. Fullgoalactive.


## Current inspector refresh and pending source changes — 2026-10-17

Active worktree: /Users/alexy/src/unison-sol-review-20261017, branch
integration/sol-consolidated-review, draft PR13, last committed183844c3.
Current uncommitted work adds INSPECT_COMPONENTS=1 to the manual inspect-file
command, eight argv-only controls, and updates semantic-inspect documentation.
The strict-profile default remains unchanged; component reports are advisory.

Fresh stock/Ox standalone inspector builds and integration ACTUAL49827/a6d1a4/0
(no session): sixteen complete calls on independent256B original TIFF fixtures
passed component/role/hash and unchanged-source checks. No camera payload opened.
Evidence directories: /private/tmp/unison-current-components-stock-inspector-20261017-001,
/private/tmp/unison-current-components-ox-inspector-20261017-001, and
/private/tmp/unison-current-components-inspector-integration-20261017-001.

The eight new command controls have SHARED-CLOSED evidence in
/private/tmp/unison-inspector-component-command-controls-20261017-001; owning-tool
terminal was truncated from model context and must not be invented from that marker.
Inspect its recorded child result before marking controls passed. Final qualification
JSON, release-readiness refresh and commit remain pending. Documentation currently
references the planned qualification JSON; create it before committing.

Next: finish these source/tiny-fixture controls, refresh the release gap summary,
then prepare a concrete bounded camera component-observation executor/plan for
separate admission. No retained camera payload, SDK or transport permission follows
from the manual flag. Frozen property request remains a separate older-source
request; no grant known at last check. Full goal active, not complete.

Inspector refresh finalized: eight argv controls passed (child reaped0/tokensclosed); owning-tool terminal unavailable after truncated output, explicitly not inferred. Current inspector evidence JSON now exists and pins four evidence directories. Release checklist refreshed to separate candidate transport, camera observation and remaining legacy limits. No camera payload opened; no goal completion claim.


Inspector IO contract source successor: tests/inspector_io_contract.py binds exact
components argv, successful receipt/binary digest, exact26kernel source list and
metadata-only eightfield input identity. shared_dispatch inspect-file IO path
adds these sources to admission and runtime pins. Existing no-IO tiny fixture
entrypoints unchanged. Seven metadata-only controls actual0a0f7d/0/no session
passed under Unison00..07; child reaped/tokensclosed. No camera payload/IO lock.
Evidence inspector-io-contract-controls-20261017.json. NOT ready for payload:
post-run identity fence/result contract and immutable executor/plan remain next.
Frozen property admission still absent at this turn's check; no scheduling hold
inferred and no expired or previous grant reused.

Inspector postcheck now records exact input metadata after worker/group settlement,
before CPU/IO closure. Changed/missing input => known functional exit3 rather than
invented process uncertainty; actual close uncertainty retains existing carrier.
Ten contract/postcheck controls passed actual1e9df2/0/no session under own8, no
EXIO/camera payload. Source plan doc/component-camera-observation-contract-v1.md
records remaining composed dispatcher tests before fresh one-input request.
No camera request/admission issued by this change.


Composed dispatcher lifecycle suite25PASS actual61538/fba2a2/0/no session,
including four inspector cases: unchanged, changed, missing, closeuncertainty.
Fake owners/leases only; no canonical IO qualification implied. Prepared exact
doc/camera-components-request-v1.json for one advisory component observation on
retained Unison clone307228717. Eightfield lstat unchanged; no source payload
opened/hashed. Current stock inspector+26kernel pins, interpreter, dispatcher
closure and four prerequisites pinned; Unison8+EXglobal,300s,declared2GiBread/
16MiBlogs notinstrumented. NO admission/dispatch. Root review/scheduling next.

SOL status consistency review: older checkpoint paragraphs incorrectly still
called worker/archive/persistent-cache integration unimplemented. Corrected to
link separately qualified managed store/namespace/archive/worker routing while
preserving historical receipt scopes and complete-input revalidation limitation.
Added current release-evidence map and operation-specific gradual camera scope.
No pinned camera-request source changed; no payload/CPU/IO job launched.


Current gradual-refinement suite rebound to CURRENT sources: historical43pins
had14changed, so fresh stock/Ox tests run. Combinedattempt64542/f30359/exit1
hit60s wrapper after70recordedcalls; workerTERM/reaped/groupabsent/tokensclosed,
partialresult preserved. Added --compiler-scope stock|ox|both (defaultboth
unchanged) to test driver only, then separatebounded compiler runs PASSED
actual18008/1dfcee/0/no session. Both complete rawRESULTs/current sourcepins
rehashed. Evidence current-gradual-refinement-actual-20261017.json includes
commuting independent private upgrades/preservedpixels/unsupported downgrade/
authenticated restore/archivefault/guard-ablation checks. Generatedtiny only,
no EXIO/SDK/camera. Camera request executionpins unchanged by test-driver edit.

PR review refresh: current-qualification-status now leads with PR13/current
source and scoped evidence instead of historical PR4/integration snapshot. PR13
description refreshed around final behavior/nativeownedcallers/gradualrefinement/
remainingtransport+camera evidence. Forkmasterbase/draft preserved; no merge.
No production or camera-request pinned source changed.

Userguide correction: doc/semantic-sync.md previously suggested8workers at EACH
loopback endpoint (16plusowners), inconsistent with standingUnison8. Example now
3+3+2, buildjobs<=2, canonicaltokens separate from semanticworkers preference.
Historical18/36measurements retained with explicit freshborrow coordination.
Documented actual semanticcomponents/componentownercache/componentcacheparent
names against productiondefinitions; endpoint-localprivateparent/full-source
restore/advisoryencodedpixels limits explicit. Documentationonly, no sourcepins
changed/no camera IO.

Mixed-peer readiness review found test false-positive: --only old-peer without
--old-peer silentlyskipped, unknown--only couldpasszero. Runner now rejects
missingpeer/unknownselector/combinednegative-selection BEFOREcompile/workspace;
main successful result also requires nonempty suite.passed. Seven arg-only
controls actual3ba54a/0/no session PASS under own8. No CLI/compile/IO/transport.
Evidence final-publication-selection-controls-20261017.json. Existing oldpeer
runner subprocess.run(timeout90) lacks current complete client/server/pump/group
proofs, so do NOTdispatch it as a qualified new mixed-peerwindow yet. Need finite
owned transport wrapper/rawledgers before exactcurrentcandidate request. Camera
request sourcepins unchanged; both queuedadmissions absent at turnread.

Mixed-peer source successor begins tests/mixed_peer_compatibility: fixed4directions
(currentstock/Oxclient orserver versusretainedoldstock),3phasesseed/update/noop,
12CLI maximum. Current-only flags nevergo tooldpeer;2+2+2 withinUnison8. Five
command-only controls actualcd7fa7/0/no session passed, inertpaths/no transport.
README lists executor/journal/proxy/rawbinding/knownfailedprefix/fixture/current
build/oldbinary/admission work stillrequired. NO runtimegrant or readyclaim.
Existing camera request pins preserved; no canonicalEXIO/camera/SDK accessed.

Mixed-peer pure auditor implemented: fixed12call prefix/identity/argv/rawproxy/
client-supervisorreaps/servercommand+group/pump proofs; upstreamold/newRPC
startupdialects explicit, exactprecreationframe only (notnullPID). Knownfailed
prefix returnslifecycleonly; nofunctional/parentterminal/FDreleaseauthority.
Nineinitialcontrols5641e7/0 then11expandedcontrols89353e/0 passed, own8closed,
no payload/CLI/EXIO. Evidence mixed-peer-audit-controls-20261017.json. Executor/
rawfileauthentication/functionalchecks/buildpins/admission stillnext. Existing
camera request pinned sources remain unchanged.

Mixed-peer inactiveworker kernel nowusesretained component_remote.call supervisor,
4cases12calls/original8KiBTIFFs/sourcefence/exactreceivedbytes/noopidentity.
JournalINTENTbeforecall/OUTCOMEbeforeaudit, stopsfailedcall, propagatesoriginal
UnresolvedOwnershipcarrier. Fivefake-call/audit flowcontrols d0932e/0 closed
(initial3controls36714a/0 preserved); no actualtransport. Includescorruptoutput
and samebytenoopreplacementnegativechecks. Coordinator/sourcebuildartifactpins/
rawparentreadaudit/sharedtarget/admissionremainnext. Existing camera request
pins unchanged; no camera/SDK/EXIO.

Mixed-peer independentparentreadback implemented: reopensrawproxyframes, real
prefixaudit, complete12call/4case typedstatus/endpointsuccess/exactstagehashes/
finalleftrightbytes+metadata/noopidentity. Failedprefix lifecycleonly. Seven
composedworker+REALauditor/readbacktests withONLYnativecallmock passed actual
37829/9aa4ca/0/no session; own8closed/generated8KiBonly. Evidence mixed-peer-
parent-controls-20261017.json. No transport/EXIO/camera/SDK. Coordinator/build
inventory/freshplan/admission remain; camera request sourcepins unchanged.

Mixed-peer retainedsettlement kernel implemented: observewithoutsignals, read
result+independentrawaudit BEFOREgroupcensus/directwait4; preserveactualnested
uncertaintycarrier+workerreference; livegroup/timeout refusesreap. Knownclosed
result/exit contradictionfunctionalfalse. SixfakeOS/ownercontrols c2c5e1/0
passed; no actualnativewait/census/transport/EXIO. Launch/packet/inheritedFD/
admission/immutablepersistence integration remainsnext, no runtimegrant. Existing
camera request sources remainfrozen unchanged.

Mixed-peerentry sourcewired: freshRootplan/admissiononly, existingEXIOthenCPU8,
oneuseworkspace/packet/snapshots, inherited9canonicalFDverification, artifactSHA
afterIO and currentstock/Oxbuild/selftest/productioninventorybinding. Prelaunch
knownrefusal rollsback; unknowncarrier retainsowner/grants; no numericsclose
retry. WorkerNOcallsframe sourcebound; parentrejectscontradiction. Fakeentry
4initialccf47d/0 then8expanded4deb84/0 andparent9controls21555/e7f1c9/0 passed.
Evidence mixed-peer-entry-controls-20261017.json. NO mixed-peer admission/plan
ortransportexecution yet. Need exactplan/dependency+preflight/persistence/lifecycle
review beforefreshRootrequest; don't executeentry fromthissourcework. Existing
camera request pins unchanged.

Mixed-peer worker preflight corrected: ordinarypacket/FDidentity/artifact/source
refusal before firstJournal now emitsfailedno-call result; closeuncertainty
retainsactualcarrier/no falseknownclosure. Tenentrycontrols02ca03/0 PASSclosed.
Oldpeer candidate75fcllxc/6ecf25c6 SOURCEinspection shows semantic-delta-v0 and
target-binding-producer-v0 PRESENT, semantic-components-v0 absent. Anyselected
runmustclaim EXACTolderfork interop, NOT arbitraryupstream or capability-absent
producerfallback. Stillneed exactplan/sourcecurrentbuildbindingreview before
runtimegrant. No binary executed/payload/EXIO. Camera request unchanged.

Prepared mixed-peer exactplan/requestv1 (notadmitted):383execution/sourcepins,
14prereqs,currentstock/OxsuccessfulMake/selftest/currentproductionsourcebinding,
retainedoldstock6ecf25c6,workspace/private/tmp/u-mp-721ec40a absent. PlanSHA
f3d4f6b471393127bfa890ff05e66b8f440db9033ffd454506e4f827fbf4df37; requestSHA
3fce1144b998673b7fc8ab175510b1e05a1b21027cbf224449b4689359f941b2.
Metadataonlychecked_plan passed446d67/0. Source reviewcaughtoldsemanticworkers
autodefault; OLD_FLAGS nowexplicit2/maxthreads2/validationoff (knownsupported
bythatretainedfork). Fivecommand+nineparentfake-nativecontrols68341/049cb5/0
PASS. Plan sourcepins frozen now; no mixedpeeradmission/runtime. Declared8GiB
IO+1GiBmetadata/logs uninstrumented,4cases12calls/300sobs,8CPU+EXglobal.
No generalupstreamfallback/semantic/pixel/physicalIO/throughputclaim.

Finalverificationpreflight7e5703/0 source/metadatasonly:318currentproductionpins
perstock/Ox build allmatch, recordedbuild/selftest0; camera34executionpins and
mixedpeer383executionpins+allprereqs match. Bothproposedadmissions/workspaces
absent atUnix1792245411.314545; thisownerhasnotdispatched either. Exactrecord
doc/sol-final-verification-state-20261017.json, goal_completeFALSE. No ownedjob/
CPU/IO/nativegrant. Remainingactualtransport/property, exactretainedforkinterop,
cameraadvisorycoverage need freshRootreview/admissions. Do not inventnewsource
work or repeatpassingtests justtostaybusy whilepinsarefrozen; noMakerNotecomplete
interpretation/decodepixels/universalOSRSSclaim isareleaseblocker.


## External blocker after three consecutive checks — 2026-10-17

Current goal remains incomplete. Camera component request queued
01a14a0d-0805-7890-a33f-b489eac5404c and mixed-peer request queued
01a14a25-3f46-7753-8d58-33e13b774312 still have absent admissions/workspaces.
No owned process or Unison resource reservation. Three consecutive goal turns
found the same external scheduling dependency and no remaining independent
implementation action needed before these pinned checks. Goal status blocked,
not user-paused or complete. Resume when Photo Root supplies explicit exact
admission(s); revalidate all pins/deadline/unused workspace, execute once only,
collect actual owning-tool terminal and all group/FD proofs. Never dispatch from
this status note, reuse a consumed grant, or silently repin a reviewed request.
PR13 remains draft, last pushed da839a1e; current sources/pending requests frozen.


## USER-requested exiftool-rs integration implemented — 2026-10-17

User firstrequestedreadonly review, then explicitly said integrateNOW. Actual
localcrate reuse is now tools/exiftool-bridge: pinnedgit3cd699a2 snapshot only
Cargo/src/locales/buildscript(no corpusimages), privateofflineRustbuild jobs2,
actualExifTool::extract_info_from_bytes using inheritedreadonlyFD/no writers.
ExistingDNGinspector run.py optional --exiftool-build combines exact component
summary with nestedMakerNotevendor/fieldtyped observations (duplicates/rationals/
floatbits/binary/struct retained). Output unison-dng-knowledge-observation/1;
engine-bound perfield/vendor hashes compose; exactopaque/full/pixel sourceviews
remainauthoritative. No byte spans inTagAPI => no fabricated bytepartition,
semanticmerge/transfer/cache authority or universalExifToolparity.

ActualRustbuild12692/e7506a/0; API16aaf1/0; CLI47639/491ce5/0; finalAPI+CLI
75387/eea42b/0 PASS: CanonSerialNumber123456vs654321 changesprivatehash/knowledge
whileencodedpixels unchanged, original1KiBDNGs/FIVEunchanged. FivefakeFD/call
faultcontrols7f5341/0 +finalab0ced/0 passed, unknownretention/no numericretry/
knownfailureevidence. Allactualgroups/own8closed; no sourcephotos/retainedcamera/
Adobe/SDK/transport. Externalexiftool-rs checkout UNMODIFIED. Evidence
tests/qualification/exiftool-rs-integration-actual-20261017.json; commands/schema/
limits tools/exiftool-bridge/README.md. Existing componentinspector compiled26
kernel sourcesunchanged; frontendoptionalnewbranchdefaulttested.

Camera requestV1 originalbytespreserved but run.py pin nowSTALE,UNSTARTED; no
admission existed atchange. Root notified queue01a14c24-c7f5-7f51-af23-185fd05db148
DO NOTdispatchunchanged; freshsuccessorneedsbridge/executor/pins/budgetreview.
Mixedpeerrequestsourceclosure excludesrun.py andremainsseparateunchanged. Earlier
goalblockednote is historical externalverification state, not a claim thisnew
explicituserintegration was blocked. Original fullgoal still needs actual scoped
endtoend evidence; no fullgoalcompletion/productiondeployment claim.


## Camera knowledge successor refreshed — 2026-10-17

Mixed-peer goes first unchanged: request `3fce1144b998673b7fc8ab175510b1e05a1b21027cbf224449b4689359f941b2`, 383 execution pins and 14 prerequisites freshly match; admission/workspace absent. No dispatch from this preparation.

Camera V1 remains stale/unstarted and byte-preserved. Fresh `doc/camera-knowledge-request-v2.json` SHA `c576c4424f306afb96f6de2411e0aa3fadea3083ff5d1472ec49241957286779` binds current component inspector plus actual exiftool-rs bridge receipt/binary/revision and 40 execution sources. Separate `tests/inspector_knowledge_entry.py` avoids editing the mixed-peer-pinned manual dispatcher. Exact shared8 + EXglobal admission required; workspace/admission absent. One camera observation, two owned readonly helper calls, 300s worker, three declared source passes within conservative uninstrumented 2GiB logical read budget. No source payload opened during preparation.

19 metadata-only contract controls passed under owned Unison8: actual tool `6e65d2/exit0/no session`; child reaped0/group absent/tokens closed. Qualification `tests/qualification/knowledge-inspector-contract-controls-20261017.json`. Existing exiftool API/CLI/fault controls remain separate evidence. MakerNote views remain advisory, no offsets/merge/transfer authority. Next: Photo Root review/admission after mixed-peer; never reuse V1 or infer permission from resource release.


## Mixed-peer actual failed pre-call — 2026-10-17

Admission SHA1c40c7558617cc70726abfdc4d36e0bdcf2746ab8dc7f04d5468d69c21fb6d69 consumed once after all383 source pins/prerequisites matched. Actual owner427/tool chunk4e7b8e/exit1/no session. Worker445 reaped1/others absent before reap; independent no-call audit attempted0/all settled; IOCPUclosedtrue. Workspace `/private/tmp/u-mp-721ec40a` retains START/CLOSED/WORKER-RESULT and OWNER-TERMINAL. Failure `OSError(62, Too many levels of symbolic links)` before transport; no functionality pass. Photo Root notified promptly; no retry. Source diagnosis/fresh successor needed.


## Mixed-peer compiler preflight fixed, retry V2 prepared

User directed fix and retry, continue autonomously after failures. Cause: build compiler aliases are ocamlopt symlinks, qualified readonly reader intentionally O_NOFOLLOW. V2 binds resolved compiler.opt executable paths in plan, hashes nofollow final targets and rechecks aliases; 12 controls actual a0ee5c/0 closed. Prior fixture failure ee8e32 preserved (test target /var normalization). Fresh request `doc/mixed-peer-request-v2.json` SHA cb84a74a01793c1b0621c5a8965935f64ab8fd5195f431c8d1eb5aa29c4879e2; plan SHA f4292ab55091d351e8487de77ea1b12b9414887bb5ea2ec0396f1d14b9f52aa2,383pins; workspace `/private/tmp/u-mp-3d8529a6`, proposed admission `/private/tmp/unison-mixed-peer-admission-3d8529a6.json`. Fresh Root retry scheduling requested; no old admission replay.


## Mixed-peer V2 recovery and V3 retry — 2026-10-17

V2 compiler fix worked; first client settled before connecting, but call wrapper waited only5s while no-connection proxy owns35s deadline. Worker retained. Rawproxy later proves server_commandNULL before NativeChild/0bytes/pumpjoined. Independent source-bound prefix recovery stopped exact idlePython1712+1695 after group/descendant proof; actual tool60014/9c1af4/137/no session, freshwhole EXIO+Unison8 acquiredclosed. Original worker/proxy wait4 NOT claimed. Proofs in `/private/tmp/u-mp-3d8529a6/INDEPENDENT-RECOVERY-{PROOF,CLOSED}.json`.

Fixed call wrapper saves CLIENT-OUTCOME before waiting fullproxy35s+2s; no signals, unknownretains.22controls actual0d7391/0 passed/closed. Fresh V3 request `doc/mixed-peer-request-v3.json` SHA6f7b6af3c80883bef42a927fe1176ab7be45fce117ae8ee465e59dc537c35529; planSHA0330d3c3afaa113961be9a778dc55994b6c100a740273a59d2db6bd0bbef85dd,383pins. Freshworkspace `/private/tmp/u-mp-5b9e63d0`, proposedadmission `/private/tmp/unison-mixed-peer-admission-5b9e63d0.json`. Rootqueued01a14c72-2a33. V1/V2 preserved consumed; user says continuefixretry, no freezing afterfailure.


## Mixed-peer V3 actual closed; V4 boolean fix retry

Actual V3 owner2825/tool69827/281ea8/exit1/no session normally CLOSED, worker2842 actualreaped1/groupsabsent, client2846actualwait1, no server creation rawproof; IOCPUclosed. Durable CLIENT-OUTCOME proved separate boolean true became thirdpositional argument/profile. Production Uarg.Bool accepts inline=value; fixed CURRENT_FLAGS to `-semanticdng=true`. Sixcontrols actual6eae07/0 passed/closed. FreshV4request d792a716b5e000fdc1cf976f814c8270f928608523d44778cb4477d40bcc7a0c, plan40e36cd26d8d64ca69941e934702eea6ab1ae76f40472d3ad8cc8d3fb235ee8e; workspace `/private/tmp/u-mp-701db8c4`, admission `/private/tmp/unison-mixed-peer-admission-701db8c4.json`; Rootqueued01a14c73-cda9. All earlierattempts preserved, no replay. Brief source-onlydraft/restoration duringV3proxywait disclosed toRoot; noquiettimingclaim.


## Mixed-peer final V4 PASSED/CLOSED

Actualowner3440/tool38627/33bfbc/exit0/no session; worker3457 genuinelyreaped0/othersabsent before reap. Four stock/Ox current-vs-exactretainedoldfork directions completed seed/update/noop,12CLI/rawserver+client+supervisor+pump audits PASS; receivedbytes exact/noop identities preserved. All383postpins match; IOCPUclosed, PhotoRoot notified queue01a14c74-b6da. Receipt `tests/qualification/mixed-peer-actual-20261017.json` binds request/admission/allrawJSON. No arbitraryupstream/absentproducerbinding/camera/SDK/performanceclaim. Earlier3failed attempts preserved; fixes compiler symlink binding, proxy35s wait/clientoutcome persistence, inlineboolean CLI syntax. No automaticretry/successor. Camera knowledgeV2 request remains separate prepared for Rootreview; no camera payload grant.


## Current PR13 transfer/property request prepared

Active goal resumed after mixed-peer PASS. Prepared `doc/pr13-properties-request-v1.json` SHA5216c843388dd02ec9395f6d2ee14d772bc0e31a6aad41ccaebbf4236ea6e0f7: exact current rsync-owned stock/Ox Make+selftest binaries with318productionpins match,38harnesspins, qualified3.14interpreter;18rows54CLI generated2MiB fixtures, ordinary/clone/semantic+propertyremoval/oldreaders/noop,8CPUs+EXglobal,300s observation/30s perCLI/8GiB declared uninstrumented. Workspace `/private/tmp/u-pr13-properties-29c8a6e1`, admission `/private/tmp/unison-pr13-properties-admission-29c8a6e1.json`, absent atpreparation. Source property and budget controls actualtool24067/ccc775/0/no session, allchildreaped0/tokenclosed; receipt `tests/qualification/current-property-source-controls-20261017.json`. manual.command generated with inert64hex placeholder, no dispatch. Rootqueued01a14c82-ca91; request AFTER camera knowledgeV2 ifschedulingpriority. Separate old frozenbaseline property requeste60975f3 remains unchanged, must not substituteitsgrant. CameraV2c576c442 all40pins freshmatch/admissionabsent atlastcheck; no camera payload. No current ownedjobs/resources.


## Current verification audit V2

Previous goal turn classified progress (prepared currentcandidate propertyrequest/sourcecontrols). This turn no admissions yet; refreshed authoritative audit `doc/sol-current-verification-20261017-v2.json` verifies allmixedsealedartifactpins/current318productionpins percompiler/pending40+38sources/PR13OPEN-DRAFT-MERGEABLE with no checks. Nojobs/locks/payload/native in audit. SOL.md leading status nowrecordsactualmixedPASS rather than stale unverified wording; historicalnotes preserved. Camera/property both await exactRootadmission, no dispatch/workspace. Goal remainsACTIVE/incomplete; first resumed scheduling-block observation, not3turnblockedthreshold.


## Camera V3 entry correction before dispatch

CameraV2admission f271f129 arrived, but finalsourceinspection caught missing output.mkdir in dedicatedentry before any dispatch/workspace/payload/lock. Fixed entry createsoneprivate0700directory/refusesreuse;4originalfakeentrycontrols actual3e8655/0 passed/closed. PreservedV2request/admission UNSTARTED, requestedRootwithdraw. FreshV3 `doc/camera-knowledge-request-v3.json` SHA68fe3a83a04a7dab679739177375da5c761566072daf5802d9098003497061d4;40currentpins/samecommand+budgets+builds/input/newworkspace `/private/tmp/unison-camera-knowledge-20261017-f62d7c93`/admission `/private/tmp/unison-camera-knowledge-admission-20261017-f62d7c93.json`. Rootqueued01a14c85-7645. No resources held; previous metadataV2snapshot historical, cameraV2sourcepin nowintentionallystale. Propertiesrequest5216c843 unaffected.


## Camera observation actual CLOSED; PR13 properties actual live

Picked up freshRootreschedule `/private/tmp/unison-camera-knowledge-rescheduled-admission-3fb05f49a6d3.json` SHA260407a7dd5cb5e1f3550179140c1554db4365b749cfbc99acd804662b786905. Exact40source/prereq/interpreter/deadline guards passed. Actual33158/tool26078/09b602/exit0/no session, worker33175reaped0/groupsabsent; twohelpersreaped0/capturesuntruncated;CPU8+EXglobalclosed/source8fieldsunchanged; actualfullSHA matcheshistorical. Exiftool-rs actuallyobserved30MakerNote tags/0warnings; componentparser safeunsupported DNG component region limit (480limit). Not semantic eligibility/completeforest. Receipt `tests/qualification/camera-knowledge-actual-20261017.json` pinsrawprivateoutput but commitsno tagvalues/media. Rootterminalreleasequeue01a14d08-9ca5.

NextPR13propertyadmission arrived and ACTUALSTART owner33847/tool41218/initial8afdb1, c70ad0f9868ba1f7cf506da055ab1a8bb71c604f8e32b46a99314b0b95ebb197; workspace `/private/tmp/u-pr13-properties-29c8a6e1`,38harness+318production/prereqs+deadlinefreshpassed. Standing8+EXglobal, noSDK/camera; stillliveatthisnote. RootSTARTqueue01a14d09-5bd3. Do not alter pinned sources untilterminal; no replay.


## Current PR13 property regression PASSED/CLOSED

Actual33847/tool41218/6e1b75/exit0/no session; worker33869genuinelyreaped0/othersabsent;18rows54CLI allclient/server/supervisor/pumpssettled. Independent sharedaudit reparsePASS; all38harness+318productionpostpins match. Exactdonor/basis/noop, propertyremoval/retainedoldreader/nooppropertiespassed. CPU8+EXglobalclosed; Rootactualreleasequeue01a14d0a-058a. Receipt `tests/qualification/pr13-properties-actual-20261017.json`. Cameraactualsealed `tests/qualification/camera-knowledge-actual-20261017.json` SHA672d7fd5e9614553fdeb68c4bb7156e885862d82217c62226bf1f7adf5300f0b:30MakerNotes/0warnings and fullSHAhistoricalmatch; componentforestunsupported480regionlimit, noteligibilitysuccess. BothjobsDONE/no livehandles/resources. Next substantivegap: boundedcomponentcoverage for strip/tile-rich realDNG, preservingexisting1024core-node/resourcebounds, plus finalacceptancereconciliation; no permission/replay to rereadcamera. User asks fastercoordination: admissions are queued cross-thread and require proactive pickup; sendactualterminalreleasebeforesealing.


## Bounded DNG role-run successor implemented/qualified

Realcamera480region refusal reproduced by original600strip fixture: actualwrapper86439/d1de4c/0 with expectedinnerfailure1. Implemented bounded65536rawclaim collection, rejectaliases first, coalesceONLYtouchingsameroleclaims to<=480leaves under unchanged1024corecap; originalsmallgraphs schema/0unchanged, coalescedroot/1 and orderedmembershipSHA, no holes/roleboundaries bridged. Excessfragmentation/rawcount refuses. tools inspector now reports actualroot.schema insteadofhardcoded/0. Normative scope `doc/dng-component-role-runs.md`; oldcameraunsupportedreceiptunchanged, no newcamera read.

Finalstock+Ox kernel1500checks each and actual600stripCLI schema/1 passed,36stock+39Ox containedcalls under tool35852/cdb031/0/no session. CurrentfullMake+selftests both passed22332/ce36b7/0; Dune BUILDONLY both passed35609/86c608/0; standaloneinspector002both passed24240/afd076/0. InitialOx template-comment mismatch30e3a0/1 preserved/closed, corrected exactcomments without changingmodes. Qualification `tests/qualification/dng-role-runs-actual-20261017.json` SHA496f208fe4af8264efacb001f2acff5de100bf4bc1c4cd5799bb0e595ebac12c. Allactualowners/groups/tokensclosed; noSDK/Photo/media read. Prioractualproperty/mixed runs retain prioradvisory-kernelbaseline, not replayed. Normaltransferparser implementation unchanged (onlycomponent_regions collectioncap and advisorydescribe newpath).

Fresh camera requestV4 `doc/camera-role-runs-request-v4.json` SHA48d1e992c831b4da08d5e044f24d5412af8c15f58119e054e1f0be96fc910cfb queuedRoot01a14d17-04c2. Same193851848B retainedUnisonclone identityfreshmatch/nohash; newstockinspector `/private/tmp/unison-many-unit-stock-inspector-20261017-002/RESULT.json`+samebridge.40pins/3declaredpasses2GiB300s/shared8EX; newworkspace `/private/tmp/unison-camera-role-runs-20261017-4edb027a`, admission `/private/tmp/unison-camera-role-runs-admission-20261017-4edb027a.json` absentatrequest. Need freshRootadmission beforepayload; pickupanddispatchpromptly, neverreuseearlierconsumedgrants. GoalACTIVE/notcomplete.


## Dense field encodings/exact node budget qualified; camera V5 CLOSED

Added /2 fallback ONLY after prior /1 cannot fit: descriptors/offset/padding join trusted parser-classified metadata field encoding; unknown staysprivate/image roles unchanged. /0 and previouslyaccepted/1 preserved. Exact normalized leaf+opaque-gap+root budget <=1024 replaces conservative480leaf estimate, raw65536 unchanged; no gapbridging. Source `doc/dng-component-role-runs.md`; final1540checks/compiler+37stock/40Oxcontainedcalls incl /1,/2CLI and fitting fragmented graph passed tool53260/d31dd0/0. Finalall6builds (stock/Ox Make+selftests, Dune build-only, inspectors) actual59474/0cff8f/0. New currentnodebudget qualification `tests/qualification/dng-field-node-budget-actual-20261017.json` SHA2890d69ab4dab0abd675b776010aff0b5efd9bd0f43e713c004408883fddd03d. Intermediate1536/480leaf qualification7ef433ad retained historical, not current-source rebind.

RootfreshV5request `doc/camera-field-encoding-request-v5.json` SHAe4f2d5a02570fd6f60569265820b5736cc512732abfa55557f8d6e360f523804 admitted d9aae0b56493e0992ba3c86da2b6bcf730722c437874df2aed273438d88c55b3, pickedup promptly. Actualowner95463/tool69896/f488f9/exit0/no session, worker95480reaped0/othersabsent; bothhelpers0/reaped; source8fieldsunchanged/fullSHAhistoricalmatch,30MakerNotes. Components STILLsafeunsupported: actual raw2178/physicalruns1081/fieldruns894/normalizednodes1747 >core1024. No completeforestclaim. CPU8+EXglobalclosed, Rootreleasequeue01a14d32-1f3c. Sealed `tests/qualification/camera-field-encoding-v5-actual-20261017.json`. Allpriorfailures/refusals preserved; no currentjobs/resources/IOrequest.

NEXT concrete sourcework (do notfreeze/replay/reread blindly): measured1747-node case needs explicit bounded largerforest contract. Audit ComponentHash normalization/session/checkpoint code first. Prefer dedicated budgeted API retaining existing default1024, fixed supported large2048 (not globalunbounded increase), carried through session/refine/restore. Keep old UCH/0 checkpoint bound1024/bytesunchanged; version new large metadata UCH/1 with hard2048 and unchanged1MiB bytecap, reject oversized/downgraded encodings. Audit normalized childcount (spec894 but normalized1746) and checkpoint decode bounds. DngComponents/worker/report/inspector consumers must explicitly authorize large budget; do not make genericcore recognize DNG schema strings. DNG chooses existing /0,/1,/2 first; only currentlyunsupported<=2048 shapes get explicit new largeforest schema. Existing accepted hashes must stayunchanged. Add original largegraph snapshot/refine/checkpoint/legacy-decoder/capacity/failure controls; optionalcache capacity must preserve validreport, no broadcatch of uncertainFD errors. Larger budget must be reserved under localresource policy, not peer-selected. Full currentbuilds/sourcecontrols then ONEfresh camera request, not another blindregioncapchange. Alternative stream-only advisory would leave real-file cache/refinement incomplete, so don't silently substitute it for fullforest requirement. Investigate actual APIs before implementing this plan.


## Larger-forest successor implementation in progress

Previous coordination-only turn was no implementation progress; work resumed immediately. Explicit max_nodes API/default1024, session-bound refinement/restore, fixed2048 DNG opt-in and new/3 partitions are implemented. UCH/0 small bytes preserved; UCH/1 large count strict1025..2048; unchanged1MiB metadata bound. Pure checkpoint capacity predicate feeds worker summary so optional cache capacity can skip publication without catching uncertain ownership exceptions. Original generated controls now cover fragmented600 acceptance/1200 refusal, large restore/downgrade/unknownversion/defaultbudget refusal and >1MiB metadata refusal while validhash remains. Stock controls actual97291/759235/0/no session, child67335 reaped0/othersabsent/CPUclosed; Ox controls actual15186 still being collected at this note. No camera read/request/admission/resources owned beyond current own8 controls. Full builds plus worker/cache/refinement qualification remain before fresh exact camera successor. Photo informed queue01a14d3f-f0e3 that it need not wait/reserve resources.


## Explicit larger forest qualified; camera V6 ready — 2026-10-17

Current code now has explicit local max_nodes1..2048, unchanged generic default1024/depth16, inherited session bounds for refinement/base validation/restore. DNG adapters/inspector opt into2048 and newly accepted>1024 physical forests use/3; previously accepted/0/1/2 retained. UCH0 small checkpoint bytes preserved; UCH1 strict1025..2048/countbound, unchanged1MiB cap. Pure bytecapacity check lets actual worker/Update cache path preserve validreport and avoid cachefiles/archivehead mutation; operational errors not swallowed. Generated1590checks each stock/Ox passed, including opaque gaps, over2048 refusal, default refusal, downgrade/unknownversion, DNGadapterrestore, oneleafrefinement/readcharge, >1MiB metadata. All6builds passed stock/Ox Make+selftests+Dune+standaloneinspectors. Actual Make76504/3d51d7/0, finalcontrols+Dune+inspectors97696/8f927d/0, finalcapacity73925/8fdfa1/0 all NOsession and containedchildrenreaped0/othersabsent/CPUclosed. Earlier capacity001 preserved;002 includes comment-onlyfixturelabel correction. Make production318pins current; testfixtures strengthened after snapshots and separately linked/run, not falsely claimed oldsnapshotfixtureidentical.

Qualification `tests/qualification/dng-large-forest-actual-20261017.json` SHA71bf4e930679671fb99eb6159ddea58deee3cba44fa680bd054a93f7e7496cf4. New exactrequest `doc/camera-large-forest-request-v6.json` SHA1663093ec154b5bb437941ca7dc7af916578366062115f5c62722969f0b72f50,40executionpins, same retainedclone/no payloadread during preparation/lstat8fieldsunchanged. Newworkspace `/private/tmp/unison-camera-large-forest-20261017-41b8c72d`, proposedadmission `/private/tmp/unison-camera-large-forest-admission-20261017-41b8c72d.json`, absent at freeze. Same3declaredpasses2GiB300s/shared8EX/unchangedbridge/noSDK/original/copy/writes. Root readyrequest queue01a14d46-bffc; proactively check exactadmission/file/deadline and freshpins, dispatchONCE only with freshgrant. No livejobs/tokens/IOheld. PriorcameraV5 actual1747refusal remainsunchanged; newrealcamera support NOTyetobserved. No reportsealing/resourcehold.


## Camera V6 actually PASSED/CLOSED — proactive admission pickup

Admission appeared during next-turn source audit; immediately stopped prospective upstream preparation, freshchecked exactrequest1663093e/40pins/allprereqs/interpreter/lstat/deadline/unusedworkspace and dispatched ONCE. Admission `/private/tmp/unison-camera-large-forest-admission-20261017-41b8c72d.json` SHAcd3d2d21120084c08fb30ebe6db3c9cb2ca37f7c6bbb7c9aecad3f9af19b6cf4. Actualowner77441/tool94968/initialf2331a/terminal138880/exit0/NOsession. Worker77464reaped0/othersabsent, readonlyhelpers77465+77467 both0/reaped/groupsabsent/capturescomplete, input8fieldsunchanged/40postpinsmatch/CPU8+EXclosed. RootSTART01a14d4a-d29e; immediateactualrelease01a14d4b-3022 BEFOREsealing.

ACTUALcompletephysicalforest dng-physical-partition/3: encodedpixels193682116B/834leafcomponents, standard152235B/37, private6624B/5, structural70B/18, opaque10803B/852; sum193851848B,1747nodesinclroot. HistoricalfullSHA1a4f578e exactlymatches,30MakerNote tags/0warnings unchanged. This establishes bytecoverage/independenttypedviews foronefile, NOTdecodedpixels/rendering/semanticmerge/exhaustivecamera/corpus/receivingauthority. Rawprivatevaluesstayexternal/no payloadcommitted.

Seal `tests/qualification/camera-large-forest-v6-actual-20261017.json`5710B SHA1d0394b85776c33024f0a3e9fbd97c5858b07cd3a466eceda956f16d4031402c. ExternalOWNER-RETURN5449B SHA8759b6607055e4e446ebb983b865d054546b2b4bd4ae7bcdbc114942cfe7d899; OWNER-TERMINAL259B SHA40b7e15a190e9bb7ede9aa13a1482573f402ef18eeb60e30ab6dd3b98b88f1ae. Rootsealqueue01a14d4b-d0b6. Nojobs/resources/pendingcameraadmission; neverreplay.

NEXT substantive acceptance gap identified fromSOLM0/M3: passing mixed12CLI olderfork alreadyhasproducerbinding, so cannotprove genuineupstream/capability-absent fallback. Pinnedupstream8772d26a object exists; `/private/tmp/unison-upstream-clone-audit` is source-only/unbuilt, no qualifiedbaselinebinaryfound. Prepare own8 source/build baseline then a fresh exacttransportplan; no newIO/nativegrant inferred. Prospective builder modification was NOTmade beforeV6started; tree only actualreceipt/docschanges now. Keep frozenoldmixedsuite/results unchanged unless versioning successor; no arbitraryupstreamclaimfromoldmatrix.


## Genuine upstream fallback successor prepared and source-qualified

Added tests/build_source_snapshot.py plus optional build_snapshot --source-revision: full40hex localcommit only, gitarchive/datafilter/member+bytebounds/reservedpathrefusal, records sourceorigin/archiveSHA/exporterSHA; default currenttracked+untracked snapshot behavior retained. OriginalGitfixtures4PASS. Actual unmodified upstream8772d26a stockMake+selftests PASS tool84455/e9ee66/0/no session, child78652reaped0/groupabsent/own8closed; receipt `/private/tmp/unison-genuine-upstream-stock-build-20261017-001/RESULT.json`,196sourcepins rechecked unchanged. No baseline source compatibility patches/nativeSDK/Photo inputs.

Mixedharness successor schema2/peer_contract upstream-8772d26a-v1 passes explicitauthorizedcontract through command/worker/rawauditor/parent/coordinator; upstream receives only maxthreads2, currentflags semanticdng=true/worker2/validationoff/cloneauto. Oldschema1/defaultretainedfork unchanged and historicaloldmatrix remains separate. Upstreamreceipt+exactcommit/archive/source/compiler/binary checked afterIO/beforecalls; genuinebaseline lackssemanticRemote+semanticRuntime. Originalcomposed fixtures prove all12fakecalls/rawbinding/noopchecks underbothcontracts; wrongcontract reinterpretation refuses.70totalcontrols passed across8suites. Firstupstreamfixture5tests failedone case solely /var vs /private compilerpath alias; fixture resolved(), final5+5 actualf8e30f/0. Earlierloop41242/7e5175/1 preserved; allindividualchildren/groups/CPUclosed, no unknownretention. No sourceproduction changes.

Qualification `tests/qualification/genuine-upstream-source-actual-20261017.json`61114B SHA40c10739ecdd76d0b3b4bdf85c1e639480aa3bfb35a36b107db0191e31061327. Frozen384executionpins. Plan `doc/genuine-upstream-peer-plan-v1.json` SHA9072f6a9769fbb1a82b3545a4097b934eaa0e6f733b9877ea8bab76e4ab35d60. Request `doc/genuine-upstream-peer-request-v1.json` SHAc827b08ce54f05023b25e9acdd6330f03f614764d585fb21d328699ec27dc0a2. Newworkspace `/private/tmp/u-mp-b31e7c09`, proposedadmission `/private/tmp/unison-upstream-peer-admission-b31e7c09.json` absent atfreeze. Fourcurrentstock/Ox↔unmodifiedupstream directions seed/update/noop12CLI/generated8KiBonly; own00..07+EX/300sobs30CLI/2GiBdeclarednotinstrumented/noSDK/camera/Photo/original/pixels/performance. Rootfreshschedulingrequest queue01a14d53-8d52; sourcepreparation itself createsNOhold, cameraV6alreadyclosed. Proactivelycheckfreshadmissionbeforeturnend, dispatchoncewithpins/deadline/unusedworkspaceonly. No actualtransportfromthissuccessoryet; no oldgrantreuse.


## Genuine upstream matrix actually PASSED/CLOSED

FreshRootadmission `/private/tmp/unison-upstream-peer-admission-b31e7c09.json` SHA0abefb81ccfc1649c559176a71c01c615ca50450bcd0b49a7f0bf7a2833cac79 appeared while collecting sourcepush; pickedupimmediatelyafterownjobsclosed. Freshrequestc827b08c/plan9072f6a9/384sources/interpreter/prerequisites/unusedworkspace/deadline guards passed; exactexecONCE. Actualowner82309/tool55677/initiale8e3e3/terminal7728f5/exit0/NOsession, worker82424actualreaped0/othersabsentbeforewait. Fourcurrentstock/Ox↔genuineunmodifiedupstream8772d26a directions seed/update/noop12CLI PASS, independentrawclient/supervisor/server/pump proof+exactfixturebytes/sourcefences/noopidentityreparsePASS.384postpinsmatch/allCPU8EXclosed. ImmediateRootreleasequeue01a14d56-04f8 BEFOREsealing. No SDK/Adobe/Photo/camera/pixels/performance/corpus/nextslot.

Seal `tests/qualification/genuine-upstream-peer-actual-20261017.json`17826B SHA2c4d6652220f87c301edb8a44d0fbe168f10adca75bd3cf40df7f7308950fe8d. ExternalOWNER-RETURN17646B SHA789061d3912ed724c5b982d35db81e8c7f320df16046ca9b65016183038062b8; OWNER-TERMINAL239B SHA7785bcf7efadbf12be411b2f3043fbe84b0544bc076831a95fb74f4360aea6b7. Rootsealqueue01a14d56-c422. NO livejobs/resources/pendingIOadmission; bothcameraV6andupstreamcoordinationdone. Originaloldfork12CLI remainsseparatehistoricalpass, genuineupstreamnewmatrixclosesitscapability-absentgap for thisexactpinnedupstream (notallreleases/RPC0).

NEXT finalSOLacceptancereconciliation from current source/evidence; do not claimgoalcompleteuntilall explicitrequirements accounted for. No newnative/transportgrantrequested. Currentuserquestion 'are you donewithPhoto' answeredYES forcamera; subsequentfreshupstreamwindowalsoactualpassed/releasedbeforethisnote. Routineown8source/metadataworkmaycontinue, noPhotoresourcehold.


## Current mixed SDK + ExifTool 13.59 completed; final acceptance audit continues

Actual owner tool65518/terminal7248bd/exit0/no session, owner92232/worker92257. Both stock/Ox generated-input probes passed with two SDK helpers, two ExifTool13.59 calls and32 reported hash tasks. Worker/groups settled, CPU8+EXglobal closed; immediate Photo release01a14d6d-fc1e preceded sealing. Current plan/request V2 and source qualification are retained; admission49b11c28 consumed once. No new Photo permission or resource hold remains. Seal tests/qualification/mixed-validation-v2-actual-20261017.json binds saved raw audits and faithful owning-tool transcription. Metadata-only sealing initially hit duplicate-schema TypeError after writing OWNER-RETURN; corrected only envelope construction, no runtime repeated.

Final directed current-source checks passed: stock/Ox worker parity, SDE conformance, fixed-only DNG profiles and JPEG controls. Standalone runners now include required semanticHash_evp.h in copied inputs. Metadata binding auditor eight tests passed; binding audit V2 excludes test paths and generated projectInfo.ml from production requirements. V1 remains historical with its overly broad path classification. Final control-loop owning-tool terminal was lost in context truncation: SHARED-CLOSED proves child settlements only, so no invented outer terminal is claimed.

Goal remains ACTIVE: reconcile each SOL requirement with current evidence, especially explicit M6 resource/performance requirements; declared budgets are not hard process-tree RSS/CPU/FD limits. No universal camera/pixel/corpus/performance qualification is inferred.


## Current retained-resource lifecycle refreshed

Actual own8 wrapper54247/400762/exit0/no session; stock94099 andOx94319 bothreaped0/groupsabsent/tokensclosed. Seven executions/compiler (normal census, immediate+queued handoff faults and four designated regression rejections) passed against current Make objects,14 relevant sourcepins/compiler rehashed unchanged. Ready7FD/Finalized8FD censuses include process baseline; charged24 descriptor credits persist through deferred release. Evidence tests/qualification/current-resource-lifetime-actual-20261017.json. Synthetic private files only/no SDK/media/EXglobal/Photo reservation. This strengthens current owner accounting evidence; whole-process FD/RSS limits and transient peaks remain unproved. Current helper launcher already supports opt-in per-child hard NOFILE; macOS AS enforcement refuses. Do not implement a global kill/watchdog or relabel accounting as hard memory enforcement. Next develop a concrete safe resource-bound design and benchmark evidence map before altering production resource behavior.


## Optional helper limiter inherited-FD repair implemented and qualified

Found actual source gap in tools/helper-limits/launcher.c: Darwin ignored enumerated close failures and portable fallback could scan INT_MAX. Darwin now refuses target exec on any uncertain close without numeric retry, preserving errno across free; isolated launcher exit settles remaining OS descriptors. Portable fallback refuses infinite or >65536 inherited hard limit before scanning (no silent high-FD skip), accepts EBADF holes, refuses other close errors. Default-off behavior and literal argv/parent limits unchanged. Existing pinned executables not replaced/installed.

Stock/Ox original13 supervisor groups/native NOFILE inheritance/malformed/timeout/cancel/output controls passed, plus4 portable syscall-boundary controls and Darwin close-success-reported-EINTR/target-nonentry. Private old-behavior variants reject designated oracles. Finalactual14293/167d00/0/no session; children95746+95847 reaped0/groupsabsent/CPU8closed. Earlier001/002 successfulcontrols preserved; final003 adds regression negatives. Receipt tests/qualification/helper-limiter-close-actual-20261017.json binds current17sourcepins/compiler and raw commands. No SDK/Photo/media/EXIO or cross-platform-kernel/RSS claim. Fullgoalactive; remaining hard memory/aggregate-FD/performance scope not solved by this repair.


## Bounded semantic RPC ingress implementation in progress

Current src/remote.ml adds endpoint-local raw bounded-command byte/slot limits64MiB/4096, reserves actual length before allocation/read, rejects rather than waits to preserve bidirectional RPC progress, holds through detached request/reply settlement, never resets on connection close with borrowed work. This addresses a real pre-transaction aggregate raw-buffer gap, not process RSS/decoded/header/reply/legacy bounds. Empty receivePacket now skips forbidden zero-length grab rather than asserting.

Initialstocktest001 actual89858/75c5dd/1 closed exposed existing zero-length grab assertion; corrected and both002 passed57959/bae02b/0. Strengthened truncated-read tests003 passed stock97252+Ox97276, actual54098/7f3d02/1 wrapper ONLYbecause subsequentbuild target spelling build-make-stock was not a registered shared target; compiler/build neverstarted in that attempt. Freshcorrect fullMake+selftest loop actualsession35902 initial6903ed LIVE at this note; outputs /private/tmp/unison-rpc-input-full-{stock,ox}-20261017-002. Do not restart if observation times out. Production source not yetcommitted/newtransport not yetqualified; no Photo resourcehold ornativeIOgrant. Before commit collectactualterminal andseal currentcontrols/builds, update this state.


## Bounded semantic RPC ingress PASS/CLOSED

Actualfullbuildwrapper35902/328c77/exit0/no session; stock97417 andOx98542 reaped0/groupsabsent/CPU8closed. BothfullMakebuilds+selftests passed. Finalmetadata-receipted RPCcontrols actual30186/bf7a97/0/no session, stock99823/Ox99842 reaped0/groupsabsent/tokensclosed; current source+linkedobjects pinned in tests/qualification/bounded-rpc-input-actual-20261017.json. Current318-ishproduction source subset checked from each full inventory (exactcount inreceipt); tests added --report so temporary source snapshots and original fixtures are hashbound, not inferred from later checkout.

Default endpoint-local rpcboundedinputbudget64MiB/rpcboundedinputslots4096 enforce raw bounded-command request allocation beforebody read, retained through actual replysettlement; no globalresetonconnclose. Oversize/header-only, empty-slot, exactcapacity, failure/truncation and queuedborrower controls pass. No memory/RSS/header/reply/decoded/legacy cap or newtransportexecution claimed. Earlier89858 stock001 failed zero-grab assertion preserved;002corrected passed;003tests passed butwrapperlaterbadbuildtarget exited1 precompiler; freshfullbuild002 used correct stock-check/ox-check. No livejobs/FDs/PhotoIOhold ornewpermission needed for this sourcechange. Goal remainsACTIVE; benchmark/memory remaining scope not relabeled complete.


## Current cached-worker benchmark build preparation completed

bench/semantic/run.py dependency list was stale before componentHash/DNGcomponents/owned snapshot changes. Added current dependencies and semanticHash_evp.h (header verified/copied, never compiled as object); actual production --build preserves checked CMIs/CMXs. Build-only now saves artifact/source/runner hashes with build_completeTRUE/measurement_completeFALSE and explicit binary paths; defaultworkerconfigs1/2/4/6 fit6+2 inside standing8. Historical1/6/18 and36 reports unchanged.

Final build-only actual72554/f77365/0/no session child1595reaped0/groupsabsent/CPU8closed. BothstockOx probes linkcurrentproductionobjects;56sources+runnerhash verifiedcurrent; retainedworkspace containsNOsynthetic.bin, samplesempty. Qualification tests/qualification/cached-worker-build-actual-20261017.json. Earlier70658/9fef47/0 build001 preserved (sameexplicitconfigs, beforedefault/receiptmetadatafields). No measurement/bulkIO/native/Photo operation orpermissionrequested.

Next concrete prep doc/cached-worker-measurement-preparation-v1.json records48serialbatches/288digests/9GiBrequestedlogicalreads32MiBsyntheticfixture/16GiBdeclarednotphysicalbudget, worker1/2/4/6+owner2 under8. NOTexecutionready/admitted: first addversioned canonicalCPU+EXglobaldispatcher contract+controls thenfreezeexactrequest forPhoto scheduling. No pendingPhotoackgate; sourceimplementationwork remains ours. Goalactive, no resourcesheld.


## Shared cached benchmark exact successor READY, not admitted

Implemented new cached-sha-benchmark dispatcher target with mandatory existing EXglobal+CPU00..07, exact9FD actual parent/worker metadata binding and inheritance to all compiler/native children; raw source/compiled artifacts checked before calls and rechecked before release. Worker environment private HOME/TMPDIR and fixed PATH/locale.300s outer observation retains live unknown,30s individual sample timeout, no automatic retries. Parent independently audits48row schedule/raw numeric invariants and generated executables before actual group wait then CPU/IO close. Failureprefix staysfailed; unknown metadata/FD outcome retains.

Added actual primary-reader counters to hash_bench; originaltwo64B realstock/Ox controls counted128B total, no32MiB matrix executed. Sourcecontrols final41553/da9e3a/0/no session:69unitmethods+manualentrygroups including originalfakecompiler9FDinheritance and inert/disposable composedparent lifecycle. Build/tiny28282/ff8130/0/no session (stock/Oxrealprobes; noSDK/Photo) alsoclosed. Qualification tests/qualification/cached-benchmark-source-actual-20261017.json19138B SHA7f6b8d8c6a1dd41bf38b496ae22bc0d25d99766bd3a80975625a9e266067b880,72executionpins. Originalcommoninspectorfixture was stale; fixedteststub/pinlist only, productioninspectorcheckerunchanged. Firstfixaccidentallyaddedpin tosynctest; corrected, earlier001/002failures preserved; allfinal005suites pass. No resourcesheld.

Actualmetadatafreezer child6514/c7c8e5/exit0/no session CPUclosed. Frozenplan doc/cached-worker-benchmark-plan-v1.json36850B SHA205a263747c1b0aad2083da8547842f6cb772456a192a2475dd4c5ec10802c14 (72sources/163compiled/tool artifacts); request doc/cached-worker-benchmark-request-v1.json13083B SHA2aaa58c11127ec645b0e90f47886b08941d6622e41c2e080c4332381b33d7189. Workspace /private/tmp/unison-cached-sha-20261017-4c7e83d1 and proposedadmission /private/tmp/unison-cached-sha-admission-20261017-4c7e83d1.json absent atfreeze. Fixed48batches/288digests/1,2,4,6workers+2owner,9GiBlogicalreads/16GiBdeclared, generatedonly. Source review/scheduling request Rootqueue01a14d92-f04b.

NEXT proactivelyinspectexactadmissionpath; iffresh exactsource/plan/workspace/deadline match andnoownjobactive dispatch request.launch_argv ONCE replacing ROOT_PUBLISHED_SHA_REQUIRED with actualadmissionSHA. Send actualSTARTtoolhandle and actualterminal+group/FDclosure promptly beforeseal. Do not askduplicategrant orclaimunadmittedwithoutfreshread. Ifnotyetgranted, source/memory-gapworkmaycontinue; no automaticpayload/SDK/borrow. GoalACTIVE, no fullbenchmark/wholeRSS/FD/corpus/fidelity/production claim.


## Cached-worker matrix ACTUALLY PASSED/CLOSED — admission picked up immediately

After readyqueue01a14d92-f04b, exactfreshadmission appeared duringdocswork. Fresh request2aaa58c1/plan205a2637/72source+163artifact/interpreter/workspace/deadline guards allpassed. Admission /private/tmp/unison-cached-sha-admission-20261017-4c7e83d1.json12483B SHA4c9d02f3705b06304cf4a6e2ac040c3a350c6331d610bf7192363aadae78e8f3, originaldeadline1792306491.614403 consumedONCE; no duplicate/replay. Actualowner6967/tool69788/initial33fc30/terminal8ecd8e/exit0/NOsession; worker6983reaped0/othersabsent/CPU8EXclosed/sourcepinsunchanged. ActualSTARTqueue01a14d94-72e5, immediateactualrelease01a14d94-bcdd BEFOREseal. No jobs/resources/sealinghold orpendingadmission.

All48batches/288digests PASS. Actualprimarylogicalreads9663676416B/147456chunks/288observations. Stock/Ox6worker medians2128.4/2127.4MiB/s; CPU/wall~5.94. Sixjob4worker wave imbalance caps idealbusyworkers near3, so don't invent four-core saturation or OSbackgroundcause; no samples discarded/replaced. ProcessRSSmax6164480B, FDsamplepeak30/baselinefinal12; theseareobservationsNOThardcaps/wholechildtree/physicalIO. Report bench/semantic/results/shared-current-20261017.md distinguishes source/hashcachedtiming from sync/network/APFS/SDK/camera/fullgoal.

Seal tests/qualification/cached-worker-benchmark-actual-20261017.json62710B SHA25f3705a90ed8cfcf2c335fbd9972632d19625be9c1f7865c3473b2ccb543512; OWNERRETURN6358B SHA1ffd3cfbdb440a0a9003dbaed8054f0d33f6858d2b2f2203b253cb8cc88de897; OWNERTERMINAL320B SHAfb8f7cf63cf9dd0012fb81bed774081aa5fe461b0e2f3d56aa10cb7f6aaea6df. Rootsealqueue01a14d96-4855. Metadata-onlysavednumericreaudit afterrelease; executablehashesreverified ONLYunderoriginalheldIO parentaudit, no newpayloadreads afterrelease. Source/request/preparation remainimmutablehistoricalpending records, actualseal supersedes their schedulingstate.

Next finalrequirementwork remains broad resource-limit/transfer-performance interpretation; no Photo dependency currently. Do not relabel this cached experiment as fullcorpus/production/end-to-end performance, hardRSS/FD ceilings or fullgoalcompletion. Allnewcode/control/reportfiles pendingcommit/push in activeworktree; don'tdrop untracked tests/cached_benchmark or frozenrequest/plan.


## Compact XMP namespace representation implemented, qualified, all closed

Source src/xmpObservation.ml drops eager expanded-name strings from internal attributes/elements. It retains shared URI/local tokens, validates identical512B limits, compares duplicate attributes by the pair and expands only public property/scalar names. No lower input limit or newly unsupported packet was used. Scalar policy/transcript API and wire profiles unchanged. Original174347B/16384attribute stress remains accepted with independentPython digest. Managed allocation stock26273272→9109544B(65.3%less), Ox24695568→8056032B(67.4%less), measuredGc.allocated_bytes notRSS/heapcap.

Corrected current+Gitbaseline57ec15479a957cfb8f38f6f98c588c2e50b63343 each458directed controls/compiler pass; scalar25+343decision+4conflict controls pass, Ox4Domain.Safe concurrent +portable proof. Fullstock/OxMake+selftests pass. Actualwrapper68048/1d62e4/0/no session; all8children genuinelyreaped/groupsabsent/CPU8closed. Fullnewbuildreceipts /private/tmp/unison-xmp-name-full-{stock,ox}-20261017-001/RESULT.json. Currentqualification tests/qualification/xmp-compact-names-actual-20261017.json76243B SHA80c4f94669a11d73d09b2a0623cfef4f9c230413e82a85f7be67fb59e1775697. No EXIO/SDK/Photo/original/nativeUI.

IMPORTANT honest scopeerror: first runner --fixed-only skipped Python mutationcampaign but inadvertently stillran legacyOCaml512randombytes. Actual25742/f123f4/0 priorfour001runs executed2048randomcases contrarytoexcludedcampaign instruction; rawoutputs retained. I acknowledged/corrected this. Flag nowpassedto nativefixture, guardsrandomloop; corrected002receipts explicitlyrandom_byte_cases0/testargv--fixed-only/Pythonmutationsnull, all458directed cases retained. tests/qualification/xmp-fixed-only-scope-correction-20261017.json preservespriorfiles andsuccessor. NEVERrun XMP runnerwithout--fixed-only on this task (samewarningasDNGprofile). No sanitizer/newrandomcampaignaftercorrection.

Earliercachedbenchmark69788/8ecd8e/0 remainsconsumedclosed/released. Its sourcepostpins were trueATclosure, not unchangedcurrentcheckoutafterthisXMPedit. Snapshotobjects/source files preserved; Rootnotified01a14d9f-48cf oflater sourceactivity/no replay/nohold. Source docs topSOL stalependingcamera/property claims correctedtoactualsealed results; normativefullgoalrequirements unchanged. Nextresource/endtoend-performance requirements remain ACTIVE; no hardRSS/globalFD/completegoal claim. Currentcode/docs/evidence pendingcommit/push; no liveprocess/resource/Photo dependency.


## Saved end-to-end resource reporting added; no new IO/native execution

Prior compact-XMP482cf810 is COMMITTED/PUSHED (actualpush1984/8d36a2/0, PRedit3647/1d7904/0), no pendingbuild/job. Added bench/sync/resource_report.py +8original controls to interpret pinned savedmetadata: per-endpoint wait4 CPU (never sum possiblyoverlapping endpoints), knownplatform RSSbytes, forwardedprotocolbytes, successfulsemanticwrites, outputextentMODELS and nullunknowns. Strictfinite/nonnegative/int64/overflow checks and primaryrecordtotals; CLIrequires inputSHA/newoutput, followsno payload/binaryrefs, infersnoclosure/currentbinding/performanceranking.

Actualmetadataownerexec_command dc9cd9/exit0/no session, children15256controls+15261savedreport reaped0/groupsabsent/CPU8closed/noEXIO. Inputoldproperty RESULT1118924B SHAe62691e3e467416227a30a5c5c9ac84afa13b4e9730907672776471987f43a17 reboundtoseparatepr13-propertyseal; original41218/6e1b75/0 remainshistorical, NOTnew54calls. Sourcecontrollerheada032e57039d89010610774863ff6cd9bfba6401d, notcurrenthead. Report bench/sync/results/property-resource-observations-20261017.json34513B SHAe78cc7c79c09ba4a6d5f7a1eff8c0362bdbeeff7ecceed64ed1bd6ba4d485820 +readable.md; qualification tests/qualification/saved-sync-resource-report-actual-20261017.json.

Savedworker1semantic returnedwrites6144B for2x2MiB/payload16384B, versusordinaryfulloutputMODEL4194304B orcloneMODEL16384B. Semanticprimaryreads12583368B (repeats/nestedexclusions); ordinary/cloneunknownNOTzero. Savedsemanticwall~0.45s vsordinary~0.35s isonefunctionalcall, notlatencyranking; reportretainsunsuccessfulspeedupinsteadinventingbenefit. Currentremainingperfmeasurements concretelyunknown: totalappreads/hash-parse-verify-commitstages/FDqueuepeaks/physicalIO/aggregatetreeRSS. Newreportcode/docs/evidencependingcommit; allresourcesfree,noPhotoack/dependency/grant/replay.


## Current Dune parity also actualclosed

Actual47840/e38f6e/exit0/no session; stock16594+Ox17660 genuinelyreaped0/groupsabsent/CPU8closed. FreshDune CLI builds+selftests pass aftercompactXMP, two compilerjobs/2selftestworkers; noEXIO/SDK/Photo data. Snapshotreceipts /private/tmp/unison-current-dune-{stock,ox}-20261017-002/RESULT.json, sourcepins rehashedcurrent. Qualification tests/qualification/current-dune-cli-actual-20261017.json. CurrentMakewas68048/1d62e4/0; bothbuildsystemsnowqualifythiscoreSource. No livehandles/resources. Savedreport/newDuneproof/docs pendingcommitnext; no newIOadmission/replay or fullgoalcompletion.


## Per-job monotonic completion observations qualified

Added benchmark-only job_completion_seconds in submission order: input open/admission/queue/hash/notification/owner delivery/input close. Production worker interfaces/clocks unchanged. Intervals overlap and are NOT internal hash/parse/verify/commit timings or summed batch walltime. Old cached48batch results remain unchanged/consumed, no bulk rerun or new Photo/IO request.

Actual owning session81465/chunkb15e1a/exit0/no session. Child21077 genuinelyreaped0/othersabsent/CPU8closed; noEXIO. Current stock/Ox benchmark builds passed six original64B controls (workers1/jobs1,workers1/jobs6,workers2/jobs6 percompiler); all26digests/exact1664primaryreadbytes, finite perjob intervals within batch walltime, permits0 and originalFDcounts restored. Evidence tests/qualification/benchmark-job-latency-actual-20261017.json and /private/tmp/unison-job-latency-controls-20261017-001. Tiny queue/delivery differences are observations, not performance/scaling/cause proof. Internalstage timings and hardresourcebounds still OPEN. No liveownedjobs/tokens/Photohold; goal remainsactive.


## Production SDE phase timing added and actual-qualified

SemanticFile opt-in reader-local fixed4stage counters +POSIX CLOCK_MONOTONIC; defaultoff, Windows/clockfailure/backwards/overflow unavailable (no wall fallback). SemanticDelta labels parser+manifest, exactfull/preserved hashing, basis/staging/target verification, changed-window comparison/write. Intervals INCLUSIVE/nested, notsumwall/CPU. Separate staging reader bytes still excludedfromprimarybytecounter although verifyinterval includes theirtime. Atomiccommit/component/legacy/validator/wholeapplication timings stillOPEN. No SDEwire/profile/digestauthority change. Runtime -debug semantic-timings capturesimmutableperjob request, emitsowneronlycompletionstats; existing semantic-reads format/default unchanged. No ownercallback passesworkerboundary.

Actualowning49814/684368/0/no session: stock23806+Ox25247 fullMake+selftests PASS, production-object stage tests25197/26522+existingreadstats25221/26564 PASS; allreaped0/groupsabsent/CPU8closed. Actual19921/b1afe6/0: currentstock/OxSDEwireconformance26664/26713 PASS. Actual77696/649d02/0: deterministic PRIVATEcopiedsource unavailable/backwardsclock controls stock27120/Ox27177, exact64Bhash+readerFDownership preserved/no fabricatedtimings. Initialstock72827/390dcf/0 passed too. NO EXIO/SDK/Photo/camera/newbulk grant, fuzz orsanitizer. No liveownedjobs/resources/Photohold.

Evidence tests/qualification/semantic-phase-observations-actual-20261017.json binds currentproduction sources, fullbuildreceipts/objectlinks/tests/terminalclosures and privatefaultsources. Design doc/semantic-phase-observations-v1.md recordsexactboundaries/exclusions. Previous2322f81f benchmarkcompletiontiming alreadyPUSHED; oldcached48batch/payloadgrantsremainconsumed, notrerun/relabelled. Next actualendtoendtimingmeasurement needs preparedfreshsource/plan/admission; meanwhile commitboundaryandhardaggregatebounds remainavailable sourcework. GoalremainsACTIVE; no completionclaim.


Current follow-up: Dune parity builds/selftests started under owning toolsession40003 (initial0608b5), sequentialstock/Ox max2compilerjobs/CPU8. Do NOT infer terminal from earlier Make49814 closure. No EXIO/Photo holds. Collect sameactualhandle before reportingthisfollowupclosed; sourcecode unchangedafterqualifiedMake.


Dune follow-up ACTUALLY CLOSED40003/1b07b2/0/no session: stock27580+Ox28683 reaped0/othersabsent/CPU8closed; bothDunebuilds+selftests pass current318productionpairs each. Benchmark compatibility ACTUALLY CLOSED76027/9133f5/0/no session: child30261reaped0/othersabsent/CPU8closed; rebuiltagainstnewproductionobjects, sixoriginal64Bcontrols/26digests exact, no bulkmatrix. Finalphasequalification26836B SHAec482a5660c005d2470ed4584dab8a8f7bc25eaa0dc8a6bb83995d8b19e41ce7. Allowninghandlesnowterminal/noresourcesheld. Code/docs/evidence readyforcommit/pushnext; fullgoalincomplete(stagecommit/fullpathmatrix/hardboundsstillopen).


Publication update: implementation2e36e92d COMMITTED/PUSHED (actualpush96731/1f4ccc/0/no session); PR13 description updated69593/ce3adc/0. Photo source-only notice queued01a14dc6-ff82 with exactqualificationec482a56; no ACK/admission gate, no resources held. All earlier pendingcommit/liveDune notes above are historical. Standing8/8unchanged; activegoal nextwork atomiccommit/fullpathmeasurements and hardaggregatebounds, not Photoallowance.


## Bound native publication timing in progress

New optional FinalPublication.publish_timed preallocates diagnosticfloatBEFORE rootedcontextlookup/rename, measures nativechecks/mutex/rename/resultstat/unlock and preservesnativepublishedstate/errorphases. Defaultpublish clocks0. Files -debug semantic-timings selectsit; intervalnotarchivecommit/durability/fulltransferproof. Originalnative+retainedproducer177cases percompiler/mode PASS at /private/tmp/unison-publication-timing-{stock,ox}-{default,timed}-20261017-002, actual95819/b44fa3/0; all4childrenclosed/CPU8closed. Initial001weakerproducer-mode/assertionproof preserved879210/0, notsubstitutedfor002.

InitialfullMake/Dune4builds+selftests ACTUAL59565/f8812a/0 closed againstpre-reviewreportingguard; later source review identified catch-all diagnostic masking too much. Finalsrc/files.ml guardnowonlysuppresses Sys_error/Unix_error/OOM; unrelated/control exceptionspropagate. Exact-source28case/compiler+designatedcatchall regression controls running underactualownertool2576/initial148c2e (mustcollectterminal). Finalfullbuild002script preparedNOTyetstarted. NativeC/APIunchanged byguardcorrection; doNOTclaimold001CLI sourcepins matchfinalFiles. NoEXIO/SDK/Photo/camera slots; standingCPU8sourcecontrols only. New doc/bound-publication-timing-v1.md recordsboundaries/exclusions; qualificationpendingfinalcontrols/builds. Goalactive.


Publication reporter ACTUALLY CLOSED2576/6f2238/0/no session: stock37725/Ox37775 both28exact-source sink/controlcasesPASS, designatedcatchallprivatevariant correctlyFAILS exit2. Allgroups/CPU8closed. FinalFilesguardno longerusesAbortonlywhitelist; unknown/control exceptions propagate unchanged. Fresh finalsourcefullMake/Dune batch ACTUALSTART42143/initialef66d7, sequential2compilerjobs+selftests; stillmustcollectsamehandleterminal. Cohortdirectoriesretainpreparationdate20261017; finalqualificationwillbe bound-publication-timing-actual-20261018.json withactualUTC/retainedpaths. Initial59565/f8812a/0 isclosedhistoricalpre-reviewguardproof, notfinalcurrentFileproof. NoEXIO/Photoowner/SDKslot.


## Bound publication timing final ACTUAL qualification closed

Final002 native177cases/mode/compiler allPASS (106general+71retainedproducer; 708total); clock0default, validinterval, allocationOOMbeforeclock/rename, NaNmissing/backwards, nativeerrorandpostrenameownership/pendingexception protections. Actual95819/b44fa3/0. Exact-source reporter28cases/compiler +designatedcatchallnegativecontrol PASS actual2576/6f2238/0. Finalfullstock/OxMake+Dune+selftests ACTUAL42143/082894/0/no session; all4current318srcpairs match, allchildrenreaped0/groupsabsent/CPU8closed. Initial59565/f8812a/0 priorguardbuilds preservedHISTORICAL, notcurrentFilesproof. No aliveowners/leases/resources, noEXIO/Photo/SDK/camera/bulk invocation.

Qualification tests/qualification/bound-publication-timing-actual-20261018.json 29452B SHA57e25f975f604c33879ca8965a2abd58fe9701dee6a88f47201558404b3179f4. Source docs doc/bound-publication-timing-v1.md. Finalpublish_timed usespreallocatedfloat (BEFORE contextlookup/rename), preservesoriginalnativeerrorandpublishedstate. Defaultunmeasuredpublish remainsclockfree. -debugsemantic-timings Files branch suppressesONLYknownSink/OOM errors, generic/control exceptionspropagate unchanged; eventisnamespacepublicationNOT archive/fulltransfer/durabilitysuccess. Legacy/unboundpathsuntimed. Currentgoal stillACTIVE: wholepathrepeatedstage/commitmatrix,totalread/physicalIO andhardaggregatebounds remainopen. Code/evidence readycommitnext; no Photo allowance blocker, no admissionreplay.


Publication complete: implementation91fc64e5 COMMITTED/PUSHED (actual78780/2c41e0/0/no session), PR13 refreshed48665/c2c9ee/0. Photo source-only notice01a14dd4-f5d9 explicitly no ACK/resourcegate. All earlierlive/pendingcommit notesabove arehistorical; allowners/resourcesclosed, standing8/8unchanged. Nextwork fullsyncphasecollection/repeatedmatrix andhardaggregatebounds; existingpayload/SDK admissionsremainconsumed/no replay. No Photo approval blocker for routine sourcework.


## Sync benchmark phase collector source qualified

bench/sync/phase_stats.py bounds4MiB/65536records, strictfixedtraceformats/ASCIIcanonicalnumbers, separateendpoint/job IDs, refusesduplicates/conflictingunavailable/fieldtype/rawlinessavedcontradictions. Typedrecordsretainrawlines; no sums ofoverlappinginclusivephases/nativepublication. New --measure-semantic-phases +manualMEASURE_SEMANTIC_PHASES=1 optin(defaultoff/referenceoff). RawstreamdiagnosticsjoinedwithNEWLINEboundaries, neverfusepartialstdout/stderr. resource_report validatesrawphasefields andrefusesoldcombined hash_parse_verify_commit_seconds NONnull (partialcoverageisnottotalcommit). Unknown/unavailableNOTzero.

Actualfinalsourcecontrolowner91029/2366d4/0/no session, all9pure/mock suitesclosed/reaped0/groupsabsent/CPU8closed; noEXIO/CLI/compiler/SDK/Photo/camera/payload. Evidence tests/qualification/sync-phase-report-source-actual-20261018.json 20345B SHAb1a178cb7edd0ec67de097494f6167166cde1bcb9c056772c960c945c1c99df4. Sourceinventoriesbounded/componentremote/privatefallback includephaseparser; sharedIOmockcheckexplicitlyrefusesmissingphasepinBEFOREcanonicalpoolread. Historical rawresultsnotedited. RuntimecollectionqualifiedFALSE untilfreshactualcohort. CurrentC/OCamlproductionunchangedfrom91fc64e5; no fullbuildrepeatneededforPython-onlyintegration. Nextpreparefreshpinnedexact18row54CLIgeneratedfixtureIOrequest underUnison8+EXglobal (NOToldgrant/retry), thenbroaderperformance study stillrequired. No livejobs/resources/Photoapprovalwaiting now; code/docs/evidencependingcommit.


Phasecollector source2f849ef0 COMMITTED (runtimeIOstillunadmitted). Prepared onefresh exactgeneratedproperty/trace smoke withtests/sync_phase_prepare.py. Actualmetadataowner92772/7a6cab/0/no session child48429reaped0/groupsabsent/CPU8closed; checkedbothcurrentMakebinary/compilerSHA+318productionpairs andmanualchildargv, prospectiveIOguardonlyINMEMORYfakeManifest(no lock). ZERO runtimeworkspace/admission/Unison/compiler/SDK/Photo/camera/payload invocation; Gitmetadataqueryonly. Evidence tests/qualification/sync-phase-preparation-actual-20261018.json.

Exactrequest doc/sync-phase-collection-request-v1.json 42417B SHA7df330109d3a8bb62de396a3b98d4c65ee2521042fa7949592e16296b5785455; plan doc/sync-phase-collection-plan-v1.json 2698B SHAea06b4ec8b485fac93ff6c769ad95239cce722168e4ece6d529087c8df5b277e. Freshworkspace/private/tmp/u-phase-4adf219c, desiredadmission/private/tmp/unison-sync-phase-admission-v1-4adf219c.json bothABSENTatpreparation. Scope18rows54CLI,2generated2MiBfiles/row, worker1/2/3 perendpoint+2owners≤8/EXglobal, propertyreaders≤36,30sCLI/300sobservation/8GiBdeclarednotinstrumented/unknownretain. Newdiagnosticsprimary+phaseenabled; not5repeatbenchmark. RootfreshIOgrantrequired byexistingpolicy; no oldadmissionreplay/automaticrenewal. Need sendexactpreparedrequestthenfreshguardsandONCEdispatchpromptlyifRootadmits; no extra build/ACK gates. Sourcecode executionclosure nowfrozen pendingactualslot; documentation/preparationcommits mayadvanceHEADwithoutchangingpinnedcode. No resourcesheld.


Sourcebudget correction BEFORE Rootrequest: V1packetpreserved/supersededunstartedBYTHISOWNER (no runtime/Rootrequestsent); explicitmarker doc/sync-phase-collection-v1-source-supersession.json. Runtimebenchhas2Unison-version+4compiler-metadata(-version/-config),2sysctl+1diskutil+1gitmetadataqueries beyond54journaledseed/update/noop clients. ZERO compilation/SDK/Adobe/Photo/camera. Do NOTclaim0compilerprocesscalls; 0buildcalls iscorrect. ActualmetaprepV2owner45634/908fb0/0/no session child50336reaped/groupsabsent/CPU8closed/noIO; evidence tests/qualification/sync-phase-preparation-v2-actual-20261018.json.

CURRENTrequest doc/sync-phase-collection-request-v2.json 42813B SHA1301e937f8cb2c0f0f4c60d03ae7deeb776cdba9a60907fb4963b7b06ec44329; plan doc/sync-phase-collection-plan-v2.json 3030B SHA0f9c293ebbeaa47e014314baab488c14f79570c850eeed71f21af8ce1fde28ae. Freshdesiredadmission/private/tmp/unison-sync-phase-admission-v2-5bca270e.json, workspace/private/tmp/u-phase-5bca270e, bothABSENTfreshly; no Rootgrantyet/schedulingholdinferred. All42execution+318productionpins unchanged; runtimecommandSource2f849ef0 frozen, metadata-preparer changedonlyversion/declarations/namespace. V1requesthash7df33010 preservedNOTcurrent. PushcurrentpacketsandsendV2ONLYtoRootnext, thenconsumeactualfreshgrantpromptlyifissued. No moreoptionalbuildbeforegrantdeadline. OldRootgrantsconsumedunchanged.


CurrentV2packet d5d75806 COMMITTED/PUSHED(actual40216/71067c/0/no session). RootIOrequest DELIVERED queue01a14de6-944c, V2ONLY (1301e937 request/0f9c293e plan), no permission/admission/schedulinghold inferred fromrequest. No actualpayload/syncstarted. WaitforactualRootdecision, recheckEXACTdesiredfile /private/tmp/unison-sync-phase-admission-v2-5bca270e.json andworkspace /private/tmp/u-phase-5bca270e beforeanydispatch; preserveoriginalgrantbytes/deadline. No critical42source/318production edits or optionalfull8jobs while freshgrantawaitsconsumption. Documentationupdatesdonotalterexecutionclosure. Allresourcescurrentlyfree. The firstqueueattemptwasONLYJavaScriptsyntaxerror beforetools/no message; successfulqueue01a14de6 isONErequest, notduplicategrant.


## ACTUAL phase smoke consumed/PASS-CLOSED; rawgroup formatting discovery

Rootadmission77f969a16115d93c36b3a2855f2042cac1b18bb36f81859c8076a0547a887353(9445B) freshdeadline1792309058.796884 appeared; exactsource42/prod318/request1301e937/plan0f9c293e/prereqs/workspace guardsPASS thenONCEexec1792308616.008385. ACTUALtool11873/initial8feeb1 owner53995/worker54012; STARTqueue01a14deb-42b4. ACTUALterminald1710a/exit0/NOsession; worker54012reaped0/groupothersabsent/CPU8+EXglobalclosed/sourcepinsunchanged. Complete18rows54CLI/propertyoldreaders/noop. IMMEDIATEreleasequeue01a14dec-3125 beforesealing; no Source/PhotoIOhold remains. No replayof77f969a1/no successorgrant. Earlierpending/unadmittednotesabove areHISTORICAL.

Named workspace OWNER-TERMINAL/OWNER-RETURN(7e971bdc) faithfulactualtoolproof. OriginalRESULTtypeddiagnosticPARTIAL: Trace.debug prefixes wholeList.iter ONCE, so rawparse/verify/write lines presentbutunprefixed. Strictparsercollectedonlyhash+namespace; NEVERrelabelfullcoverageinoriginalbytes. Disclosedqueue01a14df0-0ab1. Independentnewsource-bound per-stream adjacentgroupdecoder tests4groups +savedRAWauditor actual878c21/0 completed synchronously; bothchildrenreaped0/CPU8closed/noIO. Supplemental bench/sync/results/sync-phase-grouped-observations-v2-20261018.json bindsoriginalRESULTSHA andexactretainedcompiledRuntimeSHA, verifies54journalOutcomes==rows/client/server/supervisor/pumps. Recovers60DERIVEDprefixcontexts withrawline+anchor/index evidence (notoriginallyemittedprefixes); observationsHash36/Parse36/Verify12/Write12/NativePublication36. OriginalRESULT/rawbytes unchanged. All4phasespresentin6semanticrows, inclusive/overlap, NOT5repeatperformance/totalcommit.

Sealed tests/qualification/sync-phase-collection-actual-20261018.json 8626B SHA7489759dfacda3c2b89603b896eea4877b8779384f78e50ffc09145472d19442. Every42source/318prodPIN stillmatched beforefutureemittercorrection; compiledsnapshots retainedforindependentRootadoption. NextFIX Runtimeemitter toputTrace.debugPERphase (andnotemptySome[]prefix), originalsourceformat regression+fullbuilds; no rerunneeded/authorized forconsumedcohort. No livejobs/resources. Keepgoalactive hardbounds/fullpathrepeatedmatrix stillopen.


EmitterFIX nowapplied src/semanticRuntime.ml AFTERsealedconsumedslot: Trace.debug wrapsEACHworkerphase; Some[] emits no strayprefix. Exact-sourcefakeformatter stock/Ox actual29680/3a12b4/0/no session provesall4+unavailable/empty; originalretainedgroupedRuntime compilerparticipant reproducesmissing/phasedmalformedoutput. No SDK/sync. SourceRuntime changedonecurrentproductionpin; doNOTclaimall318unchangedNOW, onlymatchedATclosure/beforefix; retainedoldbuildsourcesbindactualrun/supplement. RootinformedSourceFiximminentqueue01a14df7-95f8. Fresh4fullMake/Dune+selftests ACTUALSTART owning15175/initiald28cb9, max2compilerjobs/CPU8, stillmustcollectsamehandleterminal. No EXIO/Photohold; sourcebuilds maycoexistwithPhoto8. Actualcohort11873/d1710a/0 staysCLOSED/consumed, no replay or newlyadmittedrun. Handoffneedsfinalformatterbuildresultseal/commit/push.


Emittercorrection ACTUALLYQUALIFIED: sourceformatowner29680/3a12b4/0; oldgroupedretainedRuntime reproducesmissingprefixandSome[]strayheader, correctedsourceall4+unavailableparse/Some[]silent onbothcompilers. FullMake/Dune+selftests ACTUAL15175/5b1c74/0/no session; all4childrenreaped0/groupsabsent/CPU8closed/current318sourcepairs eachmatched. No EXIO/Photo/SDK/actualsync rerun. tests/qualification/phase-format-correction-actual-20261018.json 10810B SHA6fe549e749deb56a30dd8c4c1d32f373fce2e6e73f585b90fb647fed5d59a9b3. Newbinaries /private/tmp/unison-phase-format-{make,dune}-{stock,ox}-20261018-001/RESULT.json; olderbinary snapshotsstillbindconsumedrun. FutureadmissionmustfreshpinnewRuntimeSHA/newbinaries; 77f969a1 staysCONSUMED_ONCE. Allresources0, no reportsealinggate. Currentcode/evidence/reportdocs readycommit/pushnext; goalkeepsfullscope(openhardlimits/repeatedfullpathbenchmark).


Finalpublication: 7867609a COMMITTED/PUSHED actual18717/ad6099/0/no session; PR13 refreshed90742/01070d/0. Root source-format/actual-slot reconciliation sent01a14e01-2359; NO newgrant/request/hold. Allslots/toolhandlesnowterminal, CPU8/EXIOfree. Newactual evidence source7489759d +group supplement254ef2c2 +formatterqual6fe549e7; rawRESULTb4d43721 untouched. NativeRuntime sourcechangedonlyAFTERrawsealedclosure; original42+318postpins referexecutionepoch/retainedbuildsnapshots. Oldadmission77f969a1 consumedONCE; anydelayedfreshACK forit isSAMEhistoricalclosedrun, neverdispatch. Nextgoalwork remainshardaggregate resourcebounds andbroaderrepeatedsyncmatrix; no currentPhotoapprovalblocker/sourcehold.

## 2026-10-18 repeated shared benchmark audit successor (source only)

Added bench/sync/timed_shared.py and tests/timed_shared_test.py. Fixed candidate matrix: stock/Ox x ordinary/receiver-clone/semantic x workers1/2/3 x one warmup+five measured repetitions =108rows/324 seed-update-noop CLI; 32MiB x2 generated files, endpoint3+3+owner2 within standing8. Pure auditor binds every journal outcome to its row/triple/directory, consumes strict failed-prefix client/supervisor/server/pump evidence, and keeps missing/malformed phase telemetry separate from known process settlement. It is NOT yet a dispatcher target or execution admission. No benchmark/payload/EXIO/SDK/Photo operation performed.

Original fabricated controls actual synchronous exec e32376/exit0/no session, child67966 reaped0/groupothersabsent; canonical Unison00..07 closed, noIO. Receipt /private/tmp/unison-timed-audit-controls-20261018-001/SHARED-CLOSED.json; stdout/stderr retained there. Four groups: full108/324 with input immutable, missing telemetry vs settled lifecycle, unknown group/INTENT/mismatched row/missing row/typed parameter refusal, separate failed prefix. Next: integrate exact fixed argv admission into manual/shared_dispatch, add admission/dispatcher controls, prepare fresh immutable request using corrected Make builds. No runtime grant requested or inferred; last phase-smoke admission remains consumed. Full goal remains active: hard aggregate RSS/FD and broader benchmark matrix still incomplete.

2026-10-18 sync-timed dispatcher SOURCE integrated: exact manual argv + strict fixed option grammar + current build binary/compiler pins; requires shared8 and fresh EXglobal admission, no CPU-only route. Canonical source inventory includes all bench/sync Python. Parent observes600s/CLI30s; unknown retains, complete/nonzero worker contradiction refuses, failed-prefix324 limit separate from full108rows proof. Missing phase measurements do not manufacture lifecycle uncertainty. No runtime admission/request or actual benchmark yet. No source photos touched.

Five fabricated timed/entrypoint controls actual1fd3e5/exit0/no session child68484 reaped0/groupabsent/CPU8closed/noIO. Existing manual_shared_test + shared_sync_controls actuala96170/exit0/no session children68577+68581 eachreaped0/groupabsent/CPU8closed/noIO. All original fixed controls; no compiler, payload, CLI or canonicalIO test. Exact receipts /private/tmp/unison-timed-dispatch-controls-20261018-001 and /private/tmp/unison-timed-regression-{manual_shared_test,shared_sync_controls}-20261018-001. Minor resource-plan correction aftertests restores functional-only property-reader declaration; timed rejects property mode before command construction. Next immutable preparation request must declare metadata processes, conservative logical IO budget and retained failure accounting, use corrected Make build receipts and fresh workspace, then ask Photo actual finite EXIO scheduling. No current Photo scheduling blocker or held resource. Full hardRSS/FD and broader benchmark requirements remain open.

2026-10-18 repeated sync request frozen: doc/sync-timed-request-v1.json 44103B SHAa569ca98086f1046dc5cdaf419b63559cc37df698c122a58a0d9f69bf9f5bd40; fresh workspace/private/tmp/u-timed-8f2b6c91 and desiredadmission/private/tmp/unison-sync-timed-admission-v1-8f2b6c91.json BOTHABSENT duringprep. Exact corrected Make stock/Ox/current318production checks passed; fixed108rows324CLI32MiB2files/workers1/2/3/warm1/measured5/shared8+EXIO,600s observation30CLI,declared64GiBlogicalIO UNINSTRUMENTED/notphysicalhardlimit. Additional2Unisonversion+4compilermetadata+2sysctl+1diskutil+1git explicitlydeclared; ZERO compilation/SDK/Photo/camera. Metadata-onlypreparer tests/sync_timed_prepare.py actualowner75158/e8f946/exit0/no session, child68890reaped0/groupabsent/CPU8closed/noIO. Seal tests/qualification/sync-timed-preparation-actual-20261018.json; no runtimecreated/dispatch. Next sendexactrequesttoPhoto/freshgrantonly; no oldconsumedphaseadmissionreuse. Do not edit executionclosure or runoptionalfull8job while freshgrantready; dispatch promptlyifactualfreshgrant/pins/namespacevalid. Hardbounds/fullmatrix stillopen.

Exact current repeated request SENT Root queue01a14e0b-7c9d (one request, no grant inferred). Push2250b6cc actual98059/3704df/exit0/no session; commits83de970e+746b20b4+2250b6cc nowremotePR13. Fresh next-action guard check admission/workspace; do not mistake historical phase slot for this new timed request. All jobs/resourcescurrentlyclosed; no reportsealinghold. Await exactgrantdecision without optional full8 build or executionclosure edits.

2026-10-18 current-resource SOURCE review while exacttimedgrantstillABSENT: doc/resource-enforcement-current-20261018.{md,json} pins7currentproductionfiles and finding: SemanticWorkers.close_noerr suppresses Unixcloseerrors beforeordinarycompletion/pending release; SemanticFile normalcloseerrorpropagates but worker mapsUnixerror toordinaryfailure, so plainerrornot retaineduncertainty. NOTobservedleak/previousrunrejection. StrictFD enforcement needs preallocated ownershipcarrier, singlecloseauthority/no numericretry, combinedcauses and retainedjob/credits throughqualifiedboundary, reservebeforedup/native acquisition and wholebaseline audit. Separate hardRSS OScontainment remains open/macOSASrefusalnotRSS enforcement. Existing frozen benchmark execution sources untouched, no build/test/payload/IO operation. Allresourcesfree; repeatedrequesta569ca98 stillawaitsactualRootgrant, not generalgoalblocker.

2026-10-18 actual closeownership CANDIDATE foundation added tests/resource_close/{ownedClose.ml,mli,fixed.ml,run.py,README.md}; NOTlinked production/no current318source or benchmarkexecutionpin changed. Preallocatedgroup exception+slots; adoptoneFD once, closeauthorityconsumedBEFOREcallback, alluncertaincauses retained, settled/uncertain nevernumericretry, ownerretainsgroup. Genericdescriptorfunctor originalfakeints(noObj.magic/noOSclosefaults). Exactstock/Oxcompilercontrols ACTUAL15043/d42658/exit0/no session, controller70116reaped0/groupabsent/ONLYUnison00..02closed/noIO. Serialcompiler1+owner2, no optionalfull8 build, no payload/SDK/Photo. Tests combinedtwofailures/causepreservation/numericreuse-no-retry/idempotentknownclose/empty/duplicateownership/misadoption/crossgroupexception. Qualification tests/qualification/owned-close-candidate-actual-20261018.json. DoesNOTqualifyUnixadapter/workerintegration/hardFD/RSS/concurrentmutation. Nextintegratecarrierthroughworker/nestedreader/ownerreservation on successor source AFTER frozen timedslot disposition; do not mutatecurrentrequestpins. Timedgrantstillpendinglastcheck, noresourcesheld.

2026-10-18 repeated saved-summary implemented tests/sync_timed_summary.py +3originalfixedcontrols; exact fullmatrix lifecycleaudit then resource_report normalization, every108row retained,18warmups outsidefive-measured-sample medians/min/max/nearest-rankp90(themaxwithn5), client/serverCPUseparate/noaddition, missingmetricsunknown/notzero, malformednumberrefusalevenalongsideNone. MetadataJSONonly/SHA-bound/16MiB/duplicatekeyrefusal/exclusivewrite; NOactualsync/payload/ownerreleaseinference. ACTUALfinal1aaf33/exit0/no session child70674reaped0/groupabsent/Unison00..02closed/noIO; earlier6be27b/0 child70621 likewiseclosedpreserved. Seal tests/qualification/sync-timed-summary-controls-actual-20261018.json. All43 outstandinga569ca98 executionpins freshlycheckedunchanged. Newfilesoutsidefrozenbenchmarkclosure; nofreshgrantrequestedbythesecontrols.

Worker integration source followup: SemanticAdmission.with_borrow's failure callback invokesfinish_borrow andwith_lease failure retires; SemanticRuntime cancellationcleanup also releases onfailure. Thus typedcloseexceptionalone inadequate; uncertainworker/reader MUSTretain an unsettled borrowedpromise/job/reservation so ordinaryfailuremapping/drain/shutdowncannotrelease. BorrowedWork.all preservesfirsterroronly, so multipleparticipantuncertainty requires retainedparticipants ratherthan relying solely exception payload. Candidate primitive46529589 isfoundationonly/notfullworkerfix. No productionedit while frozen timedrequest dispositionpending; allresourcesfree.

2026-10-18 candidate borrowed-close bridge implemented tests/resource_close/borrowedClose.{ml,mli}; preparepromisebeforeacquisition, storeoriginaloutcome, closeallonce, uncertainkeepsreplySLEEPING+cause/originaloutcome. CallerMUSTrootcandidateinjobledger; sleepingpromisealoneNOTroot. Norescue/settlementforuncertaininsideprocess. Originalfixedcontrols compile REALcurrentLwt+BorrowedWork andexact extractedSemanticAdmission.finish_borrow/with_borrow functionbodies withfakegate/descriptors; timeronlystub(noobserverfaultpollingclaim). Stock/Ox eachknown/uncertain x success/error/cancel, retirebeforeclose; knownreleaseonce, uncertainretainsborrow/reservation/no repeatedcompletion. ACTUAL9253/f02a66/exit0/no session controller71190reaped0/groupsabsent/ONLYUnison00..02closed/noIO. Qualification tests/qualification/borrowed-close-candidate-actual-20261018.json. Realworker/nestedreader/shutdown/connectioncleanup/OSFD/RSSstillNOTqualified. All43 timedrequestexecutionpinsfreshlymatched; productionnotedited; admissionstillABSENTlastcheck. Noresourcesheld; no additionalIOrequest/replay. Nexttrueworkerintegrationneedsledger+cancellation/shutdownretention, notsimplyreplaceclose_noerr withthrowingclose.

2026-10-18 authoritativeparallelRESOURCEintegrationcheckout /Users/alexy/src/unison-owned-close-integration-20261018 branchimplementation/owned-close-retention HEAD674bfc57/source5826052a, basedonthisbranch5dfcab93. Addsactualsrc/ownedClose(.mlidenticaltestedcandidate)+Makeobjectlist; Duneautomatic. Fullstock+OxMakebuild-only ACTUAL75940/815af7/0/no session, children71982+73100reaped/groupsabsent/ONLYUnison00..02closedaftereach/noIO,serial1compiler, NOselftests/host/SDK/Photo/payload. Seal inISOLATEDcheckout tests/qualification/owned-close-successor-build-actual-20261018.json. NOTworker-integrated/notFD/RSSqualified. Continueworker/nestedreader/pendingledger/cancellation+shutdownretentioninISOLATEDcheckout, preserveMAINsubmittedbenchmarkexecutionpins. DoNOTusethe successorbuildswithcurrentrequesta569ca98 ormergebeforeitsslotdisposition. NewIOgrantstillnotpresentlastcheck/alljobsclosed; no reporthold. Bothworktrees needhandoffsyncaftermeaningfulprogress.

2026-10-18 RESOURCEisolatedbranch advanced3ed8f0ec /Users/alexy/src/unison-owned-close-integration-20261018: realSemanticWorkers input/outputduplicateownershipledger+retainedsleepingreply/sourcecodeintegration; AtomicOwnedClose+immutablelist explicitOxportableOps/functor/typecontracts, Safe.spawnunchanged. FinalpartialunitstockOx typecheck ACTUAL55719/fab6b5/0 controller76072reaped/groupabsent/Unison3closed/noIO. Earliercompilerrejectionspreserved(notpasses); final006all_passedtrue; commentsclarifiedaftertypecheck. NOTfullbuild/actualworkerfault/native/nestedreader/hardFD/RSSqualified. Nextfullbuild+selftests+originalfixedworkerclosefault/cancel/shutdown, nestedSemanticFile integration. MAINexecution43pins unchanged; don'tmerge/useisolatedbinariesinrequesta569ca98. Fullisolatedhandoff/evidence tests/qualification/worker-close-source-typecheck-actual-20261018.json.

2026-10-18 TIMED actualadmission24b1b4e25c4b468a2eb52cff852f8480a356ee0a31daf69d00a461646064b362 appeared; freshrequesta569ca98/plancc797cbe/43exec+318prod/allprereqs/builds/deadline/unusedworkspacePASS. ONCE1792311808.3785632 owner76612/tool53602 initial650bf0 worker76628; STARTqueue01a14e1b-fc0e. ALL108rows324CLI complete/exact/phaseobservationsqualified, rawRESULT6272262B SHA66422ef741e827bf527a4622f4c49e81f25e71ad6aa89e96bec95a1d8b67b437. Parentauditor FAILED call owner group unsettled andretained8+EX: run.py enabledstrictgroupsONLYshared_qualification, notnewtimedtarget. All648directclient/supervisorreceipts rawNULLothermembers but exactonly_owned_leader_zombie_darwin marker; pinnedownership.py eba29bdc checks retainedPIDcensusonlyownzombie thenwait4. Originalstrictrefusal/marker/rawbytesPRESERVED. No retry/newcalls. Source-bound supplement tests/sync_timed_darwin_audit.py actual30de19/0 qualified1296locations(duplicatesinrows+journal), fulltimedmatrixaudits+3negativebadmarkercontrols; doesNOTrewriteoriginalfields.

Independentknownidleownerstopproof: all324rawcalls/sourceboundcensus+worker76628Z/parent76612retainsleep/onlychild+groupentry verifiedtwice; ONLYparentSIGKILL once actual9f6980/0. ACTUALsame-tool53602 terminal301032/exit137/NOsession. Originalworkerwait4byparentNOTclaimed/normalexitNOTclaimed. Recoveryactual164714/0 independentlyworker+groupabsent, freshEXthenCPU00..07wholebundleacquired/knownnochildclosed/43postpins+318produnchanged. PhotoIMMEDIATEreleasequeue01a14e27-6320 BEFOREsealing. StateFUNCTIONAL_MATRIX_COMPLETE_INDEPENDENT_RECOVERY_CLOSED, notnormalparentbatchreap. No resourceholdleft/admissionconsumedONCE/no replay/automatic successor. Workspace /private/tmp/u-timed-8f2b6c91 nowOWNER-RETURN+OWNER-TERMINAL+independentrecoveryproofs; allrawretained.

Savedsummaryactual13908e/0/no session child83715reaped/groupabsent/Unison3closed/noIO; source-derivedview only, rawunchanged. bench/sync/results/shared-timed-32mib-20261018.{json,md}; all18warmups/90measured preserved. Medianupdate stock ordinary1.389s/clone1.365s atworker1; semantic1/2/3=2.399/1.707/1.666s; Ox2.396/1.667/1.663s. Returnedsemanticwrites6144B/primaryreads201327048B, notphysical/completeapplicationreads. NOsemanticwallwin vsordinary/clonehere; noquiet/hardlimits/fullmatrixclaim. Seal tests/qualification/shared-timed-32mib-actual-20261018.json. NEXTFIXfuture run.py strict_group_settlement selection includeCPUboundtimed runs; originalfixedregression/ensureprospectiveparametercheck. NO needrepeatconsumedcohort. Resourcebranch3ed8f0ec actualworkerfaulttestsNOTSTARTED thisturnbecausefreshadmissionprioritized; continueseparatelyafterclosure. AllresourcesFREE.

2026-10-18 futurebenchgroupFIX afteractualsealedrun: bench/sync/run.py dispatch nowstrict_group_settlement=True FORALLprofiles; priorcodegatedonlyshared_qualification so timedrunsproducedNULLboolean despiteDarwinexplicitonlyleadercensus. Newsource regression evaluates EXACTdispatchAST/currentvsretained59f4f4db runnerSHA6d9db060, shared8/timed8/timed18/unboundedprofiles allstrictcurrent, priorfalsefortimed reproduced. Twofixedtestgroups+existingshared_sync_controls ACTUAL5b2916/exit0/no session children84587+84590reaped0/groupsabsent/Unison3closedaftereach/noIO; oneGitmetadataquery/ZEROsync/SDK/payload/rerun. Qualification tests/qualification/sync-strict-group-selection-actual-20261018.json. ThisCHANGES1ofconsumedrequest43executionpins NOW, so oldall43postpins applyATsealedclosure notcurrent; originalraw+retainedsource+request+admission unchanged. CurrentproductionUnison318source/binaries unchanged. DoNOTreplayold24b1b4e toqualifyfix; futurefreshrequestmustpinnewrunner. Resourcebranchworker testsnext; noPhotoresourcehold/no newgrantfromsourcefix.

2026-10-18 RESOURCEisolatedbranch actualworkerqualification ef74f3f5 (worktree /Users/alexy/src/unison-owned-close-integration-20261018). FullstockOxMake+selftests actual73565/6bda06/0, children85041+86194reaped/groupsabsent/CPU8closed;321productionpinsmatchboth. OriginalprivateONEclosecallback substitution actualUnix.close+fdnumberreuse+EIO, 8currentcases +2oldclose-swallow regressions PASS ACTUAL10326/0c52a0/0 controller88611reaped/groupsabsent/CPU3closed/noIO. Duplicatecloseuncertainty retainsreply/pending/CPU throughcancel+shutdown/newworkrefuses; intentionallyfaultedpools settleOSFDsonactualprocessEXIT, notnormalshutdown. Failedhelper/linkattempts retained. Seal ISOLATEDtests/qualification/worker-duplicate-retention-actual-20261018.json SHAe66a391aec473cb9c8a772de55e5c8e81a97c174dbf6a967b3802c083b0e86ea. NOTMERGEDmain; nestedreader/native/pipes/callerFD andhardFD/RSSstillopen; nextnestedSemanticFilecarrier, partialdup/creationfaults,Dune. Allresources0; maintimed24b1b4e consumed/recoveredclosed unchanged.

2026-10-18 RESOURCEisolated successor a3d16fef (laterqualificationaddendumcommitseeisolatedHEAD): nestedSemanticFile close_issue preallocatedbeforedup, singlecloseauthority, identity+closecause+originalerror/nestedcarrierchain; workerexplicitretainsReader_ownership_retained inrootedoutcomeledger. FULLstockOxMake+selftests ACTUAL98636/5c4ea0/0 children90990+92223reaped/groupsabsent/CPU8closed;321pinsmatchboth. Reader+worker16current+4oldregressions PASS7709/8df346/0 controller94461reaped/CPU3closed/noIO. New-sourceworkerdup8current+2oldregressions PASS67623/95cb02/0 controller96115reaped/CPU3closed/noIO. SealISOLATEDtests/qualification/nested-reader-retention-actual-20261018.json SHA3dedaf70b5a99aa519d059ed552445ea8fdd3ff15888ec96b3a81336d18c594d +reader-source-duplicate-regression-actualaddendum. Fault pools settleOSFDsonactualprocessEXITnotnormalshutdown. No SDK/Photo/sourcepayload/IOslot. NOTMERGEDmain; Dune/poolcreation+notificationpipes/nativeCacheownership/synchronouscallers/partialdupfaults/hardFD/RSSnext. AllUnisonresources0; priorTIMED24b1b4e remainsconsumed/recoveredclosed(no replay).

2026-10-18 isolatedRESOURCEcf5d10d8 NOWPUBLISHED forkremoteimplementation/owned-close-retention actual83576/62f80d/exit0/no session, reviewablebutNOTmainmerged. Rootsource/qualificationstatussent01a14e3c-6a9c (noIO/nativegrantrequested); allresourcesfree. Mainstrictgroupfix/oldtimedadmissionunchanged. Nestedreaderbody.+readercausequalified321sources, nextDune/native/pipes/synchronousownerqual beforepromotion.

2026-10-18 RESOURCEbranch b19c845a BOTHstockOxDune+selftests qualifiedexactcurrent321src (matchesMake). ACTUAL25911/d5ea4d/0/no session stock97352/Ox98529reaped/groupsabsent/CPU8closedaftereach/noIO. ISOLATEDtests/qualification/nested-reader-dune-actual-20261018.json SHAa1c16d0cfb465d610d5698884c65c480e1dce05d70da66905ad38153c944a245. Poolcreation/readwritepipe retention STILLnext: newtypedexceptionaloneinsufficientbecauseadmissionfailurecallbacksrelease; addrootedowner-scopeguardINSIDEborrow, inspectactualreturnedpromiseevenobserver-installerror masksclosecarrier, retainbothcauses/classifierfailure/pending; thencreation+pipeledger andoriginalfixedfaults. Sourceorder/doc inISOLATEDdoc/pool-close-retention-successor.md. Allresources0/noPhotohold; resourcebranchnotmainmerged/hardglobalboundsopen.

2026-10-18 isolatedproduction successor /Users/alexy/src/unison-owned-close-integration-20261018 branchimplementation/owned-close-retention createdfrom5dfcab93; sourcecommit5826052a adds testedOwnedClose genericprimitive tosrc andMakeobjectlist (Dune auto discovers). NOTworker-integrated; no claimenforcementjustlinking. Production.ml BYTEIDENTICALtofakedescriptorqualifiedcandidate. FullMakebuild-only stock+Ox(serialjobs1+owner2/Unison00..02) ACTUAL75940/815af7/exit0/no session; stockchild71982/ox73100reaped0/groupsabsent/tokensclosedaftereach/noIO. No selftests/runtime/SDK/Photo/payloadinvocation. Build receipts /private/tmp/unison-close-successor-build-{stock,ox}-20261018-001/RESULT.json; seal tests/qualification/owned-close-successor-build-actual-20261018.json. MAINreviewworktree remainsfrozenforrequesta569ca98; nevermerge/use successorbuilds inthatadmission. Nextactualworker/nestedreaderretentionintegrationinTHISisolatedbranch, qualifyfaults/shutdown/cancel/Oxportablecontracts beforemergeback. MainOPUSmustpointtothisparallelbranchso worknotlost.

2026-10-18 REAL isolatedworkerSOURCE integration nowimplemented (NOTruntimequalified): SemanticWorkers job carriesrootedClosegroup andatomicoriginaloutcome; poolowned_groupsledgerregisteredBEFOREdup; input/outputadoptbeforeoperationrecordallocation. Workercloseallonce, unknown publishesOwnership_retained notnormalresponse; dispatcherkeepsreplySLEEPING, rootsledger+causes/outcome, marksclosing andretainedcount; newsubmitrefuses/shutdownstaysunresolved. Pretransfercloseuncertaintyreturnsperjobpreallocatedsleepingreply; knowncleanupalone removespending/ledger. No numericretry. NestedSemanticFile/readers/nativeadapters/notificationpipes STILLnotintegrated; nohardFD/RSSclaim.

OwnedCloseimplementation upgradedatomicfields+immutablelist (serializedhandoffstillrequired). Initialpartialtypecheck001 stockPASS/OxNONPORTABLE correctlyrejected;002Opsdescriptorcontractmismatch;003stillnonportableexport;004missingmarker;005stockOxPASS afterexplicitportableOps+functorresultsig/typecontracts;006finaloutcomeledgerstockOxPASS. Allrawlogs/resultsretained /private/tmp/unison-worker-close-typecheck-20261018-00{1..6}. FinalACTUAL55719/fab6b5/exit0/no session controller76072reaped0/groupabsent/ONLYUnison00..02closed/noIO,serialcompiler1, no fullbuild/runtime/workerfaulttest. 00110672/3e0bca/0,00226695/2ca8e8/0,00319244/65168b/0,00469621/f63f2f/0,00511698/6a21c2/0 areCONTROLcontroller0 containingexpectedcompilerrejections, notsuccessfulOxbuilds. 006all_passedTRUE, interfacecommentsclarifiedAFTER006; nextfullbuildfreshpins. NewMake/DuneownedClosepreprocess/templatewired; Safe.spawn RETAINED/no suppression. Nextactualfullbuild+selftests+originalworkerFDclosefault/knownnormal/cancellation/shutdowncontrols, firstduplicate/outputconstructorfail coverage, andnestedreaderuncertaintyintegration. No blindmergeintomain; MAINTIMEDrequestclosurestillfrozen/independent.

2026-10-18 MAINtimedslot finishedwhileisolatedworkerfaulttests wereabouttostart; testsNOTstarted. Mainrequest24b1b4e consumed108rows324CLI exact, parentstrictbooleanDarwinreceiptrefusal recoveredactual53602/301032/137, independentfreshEX+CPU8acquire/closeactual164714/0, releasequeue01a14e27-6320. Normalparentworkerwait4NOTclaimed. Maincommit59f4f4db containssealedraw/source-derivedsupplement+savedreport. Resourcebranch remains3ed8f0ec sourcesunchanged; nextfullbuild/realworkerfaults. No activejobs/IOhold. DoNOTusethe successorwithconsumedmaintimedgrant; notimingrepeatneededfor futurestrictgroupflagfix.

2026-10-18 WORKER DUPLICATE RETENTION ACTUALLYQUALIFIED isolatedbranch. Fullstock+OxMake+selftests ACTUAL73565/6bda06/exit0/no session children85041+86194reaped0/groupsabsent/CPU8closedaftereach/noIO; current321srcpins bothmatched. PrivateONEclosecallback substitution inactualSemanticWorkers/OwnedClose; realUnix.close thenUnix.dup2 /dev/null atoldnumber thenEIO, notmockOSsettlementclaim. Final8currentcases stock/Ox (knownnormaldigestshutdown, uncertaininput, dualSnapshotinput/output, failedoperation+uncertaininput) PASS; ensuresreplysleep/pending1/retained1/CPU1, canceldoesnotrelease, shutdownsleep+idempotent/newworkrefuses/replacementFDs live/no numericretry. Faultpools intentionallyleaveunresolved until actualtestPROCESSexit; neverclaimednormalpoolshutdown. Finalsource-pinnedPREfixworker oldclose-swallow logic withzeroobservationalretainedfield compatibility REJECTEDbothcompilers expected-retained-reply. ACTUAL10326/0c52a0/exit0/no session controller88611reaped0/groupsabsent/ONLYCPU3closed/noIO; onecompileratime/noSDK/Photo/payload. Seal tests/qualification/worker-duplicate-retention-actual-20261018.json. Failed001privateOxhelperweaklistannotation,003baselineCmi and004baselineCmxlinkissues preserved;002current8PASSpreserved,005finalall8+2regressionsPASS. NOproductionchangesduringqualification. NestedSemanticFile/native/poolpipe/callerFD closeuncertainty +fullFD/RSSstillOPEN. Nextintegratenestedreader carrier beforemergeback; Duneend-to-end +creation/partialdup-faultscopes stillneeded. AllresourcesCLOSED.

2026-10-18 nestedSemanticFile SOURCE+ACTUALqualified: close_issue preallocatedBEFOREdup withatomicraw/channelownershipstates+historicdescriptor+predupfstatidentity+closecause+originaloperationerror, preallocatedexception. Channeladoptionpostreturnallocationfree; consumecloseauthorityonce; no retryaftererror. Closefailurepreservesoriginalcallback/checkerror andnestedClose_uncertain carrierchain; normalknownfailurestillpropagatesunchanged. SemanticWorkers explicitlycatchesReader_ownership_retained, rootscarrierinjoboutcomeledger, preservesreplySLEEPING/CPU+IO+transactionborrow. Additionalworkerduplicategroupstillclosedonce; dualuncertaintystoreoriginalreaderoutcomeinrootedAtomic. No generalRuntime/synchronouscallerenforcementclaim.

FullstockOxMake+selftests ACTUAL98636/5c4ea0/0/no session children90990+92223reaped0/groupsabsent/CPU8closedaftereach/noIO/current321srcpairsmatch. Privateactualreader+worker fixedsuite ACTUAL7709/8df346/0/no session controller94461reaped0/groupabsent/ONLYCPU3closed/noIO. 16currentcases(6direct+2worker/compiler) +4oldbehaviorregressionsPASS FIRSTATTEMPT. Directedactualcloseafterkernelclose+fdnumberreplacement/typedchannelinstallrefusal; distinctfilenestedcause+identity chain, errorpreservation/selfcycleavoidance/no numericretry; workerretainsreply+pending+CPUthroughcancel/shutdown. RecompiledentiresuffixfromSemanticFiletoWorkers againstprivateimplementation; no cross-cmxassumptionfalseproof. PinnedoldreaderwithdummyAPIcarrierdeclarationsONLY(oldcontrolflowunchanged) rejectsplainUnixcloseerror+oldworkerordinaryfailure. FaultOSFDssettleonactualownedPROCESSexit, notclaimednormalpoolshutdown. Qual tests/qualification/nested-reader-retention-actual-20261018.json. Nativecontexts, DngComponents.Cache_ownership_uncertain mapping, poolcreation/notificationpipe, synchronousreader-caller handling, partialdupconstructorfaults, Dune +hardFD/RSSstillOPEN; no blindmergeback. Existingworkerdupqualificationhistoricalpre-nestedsource; needcombinednew-source regression beforepromotion. AllresourcesCLOSED/noIOorSDKgrantneededforOriginaltinycontrols.

2026-10-18 newnestedsource DUPLICATEregressioncompletedtoo: existing8currentworkerdupcases+2oldregressions reusedagainstNEWreaderstock/Oxbuilds (sourcechangejustifiesrepeat), ACTUAL67623/95cb02/0/no session controller96115reaped0/groupabsent/CPU3closed/noIO. /private/tmp/unison-real-worker-close-faults-20261018-006 allPASS; immutableaddendumtests/qualification/reader-source-duplicate-regression-actual-20261018.json. Combinedcurrent-source normal+selftests/readercarrier+workerdupregressionsnowqualified; notsimultaneousbothhookclassesinonejob yet. Resourcebranch a3d16fef containsactualnestedfix; stillNOTmergedmain/Dune/nativepipe/hardboundsopen. Allresources0; maintainmain+navigationhandoff.

2026-10-18 nestedSOURCE BOTH Dune builds+selftests ACTUAL25911/d5ea4d/exit0/no session; stock97352/Ox98529reaped0/groupsabsent/CPU8closedaftereach/noIO. All321srcpinsmatchMake-qualifiednestedsource. Qual tests/qualification/nested-reader-dune-actual-20261018.json. No SDK/Photo/camera/payload/nativefaults repeated. Sourceunchanged; currentMake+Dune toolchains qualified, notwholeFD/RSS.

NEXTpoolclose prereqsourcefinding in doc/pool-close-retention-successor.md: create_internal suppresses stop/join/pipeclose BEFOREreturning t; ordinarynewtypedexceptionalone wouldstillreleaseSemanticAdmission.with_borrow/with_lease. Need owner-onlyrootedretainedscope INSIDEborrowf, preallocatedneverpromise+evidencenode/cell; captureactualreturnedpromiseerror evenBorrowedWorkfirstobserverinstallerror masksit; preserveboth/retainclassifierfailure/pending. Then preallocatedcreation+Lwtpipeledger preservingdomainhandles/read/writer causes, singlecloseauthority/retainedshutdown, exactfixedfaultqual. Lwt_unix.close maythrowcallbackerrorAFTERUnixclose; APIcannotdistinguishsoconsideruncertain/no numericretry. Rootregistrymustsurvivepoolnotreturned, no blindclear. This is concreteimplementationordering, notimplementedpoolclosure/hardcapclaim. AllresourcesFREE; noPhotoIOschedulingwait/SDKgrantneededforfutureoriginaltinycontrols.

## 2026-10-18 — owner-scope reservation retention successor

Implemented RetainedOwnership in the isolated owned-close branch and wrapped the SemanticRuntime borrowed body, inside admission ownership. Recognized reader/cache close uncertainty roots original evidence and leaves the reply unsettled; an observer-installation error cannot mask the actual borrower failure. Classifier/reporting callback failures cannot release ownership. All guard bookkeeping is prepared before work starts. No reset/release API was added.

Seven fixed scenarios passed on each stock OCaml and OxCaml compiler using actual Lwt/BorrowedWork and extracted admission bodies: success, ordinary failure, synchronous/asynchronous uncertainty, observer masking, classifier failure, reporting callback failure. Actual parent 12854/face4b/exit0/no session; child4451 reaped0/group absence and CPU3 closed. Evidence: tests/qualification/owner-scope-retention-fixed-actual-20261018.json. Tests use a fake admission gate and timer stub, not full Runtime/pool qualification. Full Make/Dune builds, production integration tests and pool creation/shutdown retention remain next; aggregate FD/RSS enforcement and the broader benchmark matrix remain incomplete. No Photo IO/native grant used or requested.

Owner-scope guard production Make builds/selftests now PASS both stock and OxCaml. Actual combined parent83933/bea628/exit0/no session; stockchild4874 and Oxchild6192 each reaped0/other group members absent; eight CPU tokens closed after each, no IO barrier used. Current production source hashes rechecked against each snapshot. Evidence: tests/qualification/owner-scope-retention-make-actual-20261018.json. Runtime singleton post-constructor handoff gap recorded in doc/pool-close-retention-successor.md. Next: linked actual Runtime uncertainty controls and Dune qualification, then pool creation/shutdown lifecycle implementation; no complete M6/FD/RSS claim.

## 2026-10-18 — linked production Runtime retention qualification

Added tests/resource_close/runtime_retained_{run.py,test.ml}. Linked actual stock/Ox Runtime and admission objects with private SemanticFile close-after-kernel-close/FD-number-reuse substitutions; recompiled the dependency suffix to avoid stale implementation assumptions. Twenty-four current cases passed (two real admission paths × six modes × two compilers): known success/error, uncertain success/error, raw FD cleanup after channel-install failure, asynchronous uncertainty. Uncertain cases preserve admission across cancellation/GC and do not retry recycled numeric FDs. Four pre-guard b19c845a Runtime cases fail the designated retained-reply assertion; compatibility shim adds only the diagnostic count API, leaving old failure control flow intact.

Actual parent27302/694ca1/exit0/no session; controller9679 reaped0/other group members absent/CPU3 closed, no IO barrier/SDK/Photo input. Qualification receipt tests/qualification/owner-scope-runtime-retention-actual-20261018.json. Prior001/002 harness failures (missing interface copies, invalid preference names) preserved, both actual closed;003 passed current cases before baseline regression extension. Unknown fault cases terminate at process boundary; no normal runtime shutdown or pool lifecycle claim. Next: Dune current guard qualification, then pool construction/shutdown and runtime singleton handoff retention implementation. Aggregate FD/RSS and broader benchmark matrix still open.

## 2026-10-18 — owner-scope guard Dune qualification

Current guard production sources now pass both stock and OxCaml Dune builds/selftests as well as prior Make builds and linked Runtime faults. Actual owning parent86285/2606a0/exit0/no session; stock12840 and Ox14069 reaped0/other group members absent; full CPU8 sets closed after each, no IO barrier. All323 production source hashes match current source in each build. Evidence tests/qualification/owner-scope-retention-dune-actual-20261018.json.

Pool source review added explicit returned-domain handoff and underlying toolchain allocation boundaries to doc/pool-close-retention-successor.md. Next implementation remains pool pipe/domain lifecycle and singleton handoff; guard qualification does not close those gaps or establish aggregate FD/RSS limits. Broader benchmark/final integration remain open. No resource hold or new Photo admission.

## 2026-10-18 — notification pipe ownership candidate

Implemented src/notificationPipe.ml/.mli, an owner-only prepared pipe ledger with preallocated carrier/link and read/write close callbacks before acquisition. It adopts both raw endpoints immediately, allows a reader wrapper before I/O registration, records pre-close identities or observation errors, consumes each close authority once, preserves original and both endpoint errors, and roots unresolved evidence with optional caller-owner reachability. No retry/reset/release API. Lwt close exceptions conservatively retain even when the kernel may already have closed.

Twelve current fixed candidate controls passed stock/Ox (known raw/wrapped, read-only/write-only/dual/raw+wrapped uncertainty); real close followed by FD recycling and EIO proves repeated cleanup does not close replacements. Actual parent4575/8a0fe6/exit0/no session, controller18680 reaped0/group absence/CPU3 closed/noIO barrier. Prior candidate001 also passed before adding identity observations; both receipts preserved. Evidence tests/qualification/notification-pipe-ledger-actual-20261018.json.

IMPORTANT: candidate not yet in Make object list or wired into SemanticWorkers; existing pool paths remain unchanged. Next integrate ledger through constructor cleanup/pump/shutdown and recognize its carrier in Runtime, then qualify actual pool faults/domain join/creation and singleton handoff. Do not mistake candidate tests for those integrations or aggregate FD/RSS completion. No Photo input/SDK/resource hold.

## 2026-10-18 — actual pool notification-pipe integration

NotificationPipe registered in production Make order and integrated into SemanticWorkers construction, pump and shutdown. Stop/join errors no longer silently clear the published handle list or close a possibly active notifier: they retain lifecycle evidence. Successful joins precede both endpoint closes; close uncertainty keeps pump_done/shutdown sleeping and roots pool evidence. Runtime recognizes the typed pipe carrier. This does not yet solve singleton post-constructor handoff or qualify join-error/partial handle publication paths.

Both stock/Ox Make+selftests PASS; actual parent87768/56e260/exit0/no session, children21748/23144 reaped0/groupsabsent/CPU8 closed each; all325 production source hashes match. Twelve linked actual-pool controls PASS: known shutdown/read/write/both uncertainty plus constructor failure before domain start and after domain start before wrapper installation. Parent27195/611a1a/exit0/no session, controller25115 reaped0/groupabsence/CPU3closed/noIO. Real closes followed by EIO and FD recycling preserve both endpoint errors, original failure, and repeated-shutdown retention without numeric retry. Earlier001/002 harness link-order failures preserved, both knownclosed before fault execution. Evidence tests/qualification/pool-pipe-integration-actual-20261018.json.

Next: domain-join/stop fault controls and constructor handoff retention, current integrated Dune and queued-borrower regression; aggregate FD/RSS and broader benchmark/final integration still incomplete. No Photo input/native/SDK/IO grant used; all owned test resources closed.

## 2026-10-18 — runtime pool handoff and stop/join faults

Added SemanticWorkers.retain_unsettled and guarded Runtime post-constructor observer/tracing/singleton publication. An unresolved constructor/publication latches the exact carrier before propagating, so repeated get cannot start another pool. Existing pool root keeps domains and pipe ledger reachable; new submissions revoked. This is retained ownership, not automatic resource recovery.

Current stock/Ox Make+selftests PASS actual parent59376/4b61bd/exit0/no session; children25944/27170 reaped0/groupsabsent/CPU8closed;325 production source pins match each. Fourteen actual lifecycle fault controls PASS (creation+shutdown stop failures and join failures before/after real join; runtime handoff). Four old-runtime/no-latch variants fail designated assertions. Fault parent9432/2b6748/exit0/no session/controller29264reaped0/groupsabsent/CPU3closed/noIO. Pipe endpoints remain open and are never retried on uncertain lifecycle; repeated shutdown reuses its sleeping promise and does not rerun lifecycle actions. Unknown domains in fault controls settle only at actual process exit. Evidence tests/qualification/pool-lifecycle-handoff-actual-20261018.json.

Next: partial returned-domain publication boundary, current Dune qualification and queued borrower regression, then aggregate FD/RSS enforcement. Full benchmark/final integration remain open. No Photo payload/SDK/IO grant used; all owned processes and CPU token scopes closed.

## 2026-10-18 — preallocated returned-domain ownership

Integrated DomainOwner slots into pool creation/cleanup/shutdown. All slots/carriers exist before pipe/spawn; adoption records the actual returned unit-domain handle without Some/list allocation. Private typed/checked monomorphic GC-root slot (Obj.repr, only Held read via Obj.obj) never interprets its empty placeholder. Each join authority consumed once; arrays retain every handle/cause, join_all attempts held slots and never retries uncertain/joined slots. Removed allocating domain-list publication and local-handle fallback. This does not promise recovery for toolchain Domain.spawn internals before returning.

Current stock/Ox Make+selftests PASS actual parent54479/0e5fc3/exit0/no session, children30947/32079 reaped0/groupabsence/CPU8closed;327 source pins match. Eighteen lifecycle cases and two direct slot participants PASS stock/Ox, plus four designated Runtime old/no-latch rejections; first/second-publication faults join all returned handles and known-close pipes. Direct controls verify empty state never interpreted, duplicate adopt refused, known repeated joins, and adoption allocation counters equal measurement-only baseline. Actual parent11410/db8868/exit0/no session, controller33912reaped0/groupabsence/CPU4closed/noIO. Failed001 test mode-filter refusal preserved and closed; fixed only private test rewrite, no production filter relaxation. Evidence tests/qualification/domain-owner-publication-actual-20261018.json.

Next: current Dune builds, queued/cancelled borrower and duplicate/reader regression under this pool source, then aggregate FD/RSS admission/enforcement. Full goal remains active; no source Photo/SDK/IO grant used and no resources held.

## 2026-10-18 — current Dune, queue/cancellation and close regressions

Current stock/Ox Dune builds+selftests PASS (same327 production hashes as Make). Actual parent39017/72025a/exit0/no session; stock34907/Ox36032 reaped0/groupabsence/CPU8 closed each. Eight new actual queued-pool controls PASS stock/Ox: held CPU gate, held IO gate, running cancellation, shutdown while recognizer blocked on Atomic barrier. Queued cancellation closes only its own duplicate; active CPU/device/read descriptors stay owned until callback exits. Known joins/pipe shutdown restore independent phase FD census, source identity and all admission ledgers. Parent44436/a086b2/exit0/no session/controller37408reaped0/groupabsence/CPU3closed/noIO.

Thirty original fixed duplicate/reader controls also PASS current pool (8+2 duplicate and16+4 reader current/historical participants). Parent70470/279fe5/exit0/no session/controller37987reaped0/groupabsence/CPU3closed/noIO. Old worker API compatibility adds only an uncalled retain_unsettled binding; baseline close control flow unchanged. First wrapper attempt outside repo was correctly refused before token acquisition, preserved001/f857e9/1; canonical repository wrapper002 passed. Evidence tests/qualification/current-pool-dune-regressions-actual-20261018.json.

Current pool ownership code is qualified across both build systems and these fixed scopes; hard aggregate FD/RSS enforcement remains unproven. Next derive exact SOL M6 requirements/current supported OS controls before implementing the remaining resource limits, then broader benchmark/final integration. No new camera/SDK/Photo grant/resources.

## 2026-10-18 — opt-in main endpoint hard FD enforcement

Added explicit native --unison-endpoint-limits-v1 mode to fresh launcher: closes/verifies inherited extra FDs, lowers soft+hard RLIMIT_NOFILE/readback, then execs the whole Unison endpoint. Existing helper v1 semantics/default Unison unchanged. Endpoint second budget denotes requested hard RSS and positive requests refuse125 before target entry (no unsupported RLIMIT_RSS/AS/estimate substitution); RSS0 is explicitly unenforced. No installed limiter/pin replaced. Contract doc/endpoint-resource-enforcement.md.

Actual stock/Ox CLI+selftests PASS under hardFD96. Native same-process pre-exec oracle verifies soft/hard96,93 extra opens→EMFILE and raise-to97 EPERM before execUnison. RSS-positive marker target never entered. Parent2117/4ffa50/exit0/no session/controller39720reaped0/groupabsence/CPU8closed/noIO; outer owner limits unchanged. Original helper suite both compilers PASS13native controls each plus inheritedFD/close-fault/old-behavior/malformed/address-refusal controls; parent63655/24be90/0/controller40062reaped0/groupsabsent/CPU4closed/noIO. Evidence tests/qualification/endpoint-fd-enforcement-actual-20261018.json.

This advances actual full-endpoint per-process FD enforcement, NOT one group-wide FD allowance, hard RSS, per-acquisition complete accounting or full M6. Default existing workflows remain unchanged and supported exact paths usable. Next implement/qualify supported memory containment or explicit platform capability boundaries, aggregate descendant budgets and remaining acquisition accounting; broader benchmarks/final integration remain open. No camera/SDK/Photo/publisher input or current hold.

## 2026-10-18 — scheduling I/O descriptor close/lease gap fixed

During memory/resource review found SemanticRuntime.with_io_file still swallowed Unix.close errors and closed its scheduling descriptor only AFTER IoAdmission released its device credit. Fixed using NotificationPipe ledger single-read adoption (absent writer never closed), preallocated retention and nested callback guards. Close now happens inside the admitted borrower; close uncertainty keeps device+transaction reservations unsettled. Nested unknown errors also root the outer scheduling descriptor without closing it; original operation/close/preidentity evidence preserved. Known results/errors/cancellation close once and release normally.

Stock/Ox Make+selftests PASS actual parent21399/f8e5b0/exit0/no session/children41410+42584reaped0/groupabsence/CPU8closed;327 source hashes match. Twelve actual Runtime I/O-scope cases PASS (known/error/activecancel/close/error+close/nestedunknown), plus four pre-fix006ab439 Runtime comparisons reject designated assertions. Fault parent93220/0c6fc4/exit0/no session/controller44749reaped0/groupabsence/CPU3closed/noIO. Prior001current12pass parent14115/6deae4/0 preserved;002addedbaselinerejections. Evidence tests/qualification/runtime-io-scope-retention-actual-20261018.json.

Memory review only: installed SDK exposes task_set_phys_footprint_limit in Mach task.h/task.defs, but no runtime call/enforcement or RSS equivalence qualified. Endpoint RSS refusal remains authoritative. Next audit remaining descriptor/native wrapper paths and current Dune regression before claiming aggregate enforcement; RSS/descendant caps and broader benchmarks remain open. No Photo/SDK/native preview activity or resources held.

## 2026-10-18 — memory capability observation and remote cleanup inventory

Actual bounded original Mach self-task probe completed/closed: baseline touched32MiB and returned0; self-limit16MiB call returned8/KERN_NO_ACCESS and exited0 before allocation. Installed SDK task.h/task.defs/kern_return.h pinned. Scope self-task only, two serial child waits, no other PID/config/nativeSDK. Actual containing tool74c74b/exit0/no session/controller46018reaped0/groupabsence/CPU3closed/noIO; direct children46022/46023 returned0. Physical footprint observations are not RSS/peaks/inheritance/tree containment; endpoint hard RSS refusal remains unchanged. Evidence tests/qualification/self-footprint-capability-actual-20261018.json, tools/process-containment/{footprint_probe.c,probe.py,README.md}.

Source audit confirms ValidationDescriptor.with_file ALREADY retains close uncertainty; no false plain-close finding there. Remaining concrete gaps in SemanticRemote held_files/loose descriptors/nonces and CandidateValidation directory cleanup documented with current source pins in doc/resource-followup-audit-20261018.md. Next prepare raw-pair/single ownership before clone API returns, retain all cleanup errors and stage-name owner/borrowed leases without unlink/retry on uncertainty, then actual fixed source-scoped controls. Opaque directory acquisition and process-tree/RSS enforcement stay separate. No evidence of prior successful-run leaks is inferred. Goal active; no current resources/admission/Photo hold.

## 2026-10-18 — prepared remote staging pair owner

SemanticRemote now prepares pair/held-stage metadata and scope links BEFORE clone-stage acquisition, adopts raw basis/output immediately, and uses single-attempt close ledger instead of list-loop close_noerr. Close uncertainty marks/roots remote scope and prevents registry/connection cleanup from unlinking stage or retiring transaction. Bound path closes pair before native abort/name cleanup; raw uncertainty skips native abort. Nested recognized ownership carriers retain parent pair/borrowed lifetime. Diagnostic list excludes known-closed/uncertain raw numbers; pair ledger exposes separate identities/causes. Independently consumed native parent, nonce and directory owners remain pending, not relabeled complete. Contract doc/remote-staging-pair-ownership.md.

Stock/Ox Make+selftests PASS actual parent52020/e7605f/exit0/no session/children52206+53729reaped0/groupsabsent/CPU8closed;327 production pins match. Twenty-four actual receiver unit controls PASS parent74145/339939/0/controller55788reaped0/groupsabsent/CPU4closed; generated8192B DNG, real APFS/SDE/native publication, in-process planner/no actual transport/SDK. Read/write/both close errors including before-kernel settlement, record/registry/callback errors, preserved private stage/source/basis, charged admission and no retries under connection cleanup all verified. Existing8native publication controls PASS parent58535/fb245a/0/controller56616reaped0/groupsabsent/CPU4closed; callback-close diagnostics now correctly show pair already known closed before independent native abort uncertainty.

Two failed stock builds001/002 (record label ambiguity) preserved/closed; added explicit type annotations and successful stock typecheck ebcc53/0 before final003build. Evidence tests/qualification/remote-staging-pair-actual-20261018.json. Next native-parent consumption/loose-parent ledger, nonce/directory ownership, current Dune/regression, then aggregate FD/RSS/memory and wider benchmarks/final integration. No Photo/SDK/camera/original or new execution admission; all owned resources closed.

## 2026-10-18 — nonce single-close owner

SemanticRemote.nonce now prepares buffer, descriptor ledger/carrier and callbacks before /dev/urandom open; adopts immediately and preserves original read error plus uncertain close. No numeric retry. Typed close carrier reaches Runtime guard, keeping transaction charged rather than becoming ordinary failed-result release. Known32-byte nonce, EINTR retry, empty/failed read cleanup remain normal; no new RNG/authentication claim.

Stock/Ox Make+selftests PASS actual parent64503/d955a9/exit0/no session, children57772/58899 reaped0/groupabsence/CPU8closed;327 source hashes match. Fourteen fixed exact-body controls PASS stock/Ox linked with actual Runtime/admission/ledger; six old1663ec98 nonce-body variants fail designated retention assertion. Parent45175/c02452/exit0/no session/controller60280reaped0/groupabsence/CPU3closed/noIO. Faults include pre-close failure, kernel-close/recycled number, original read+close failure, and known descriptor census. Evidence tests/qualification/nonce-owner-actual-20261018.json.

Pinned next design doc/native-parent-handoff-successor.md: existing native adopt can reject before consuming parent, so false ML boolean cannot prove transfer. Proposes separate tracked API/abstract single-use preallocated consumed acknowledgement at exact C ownership boundary, read by cleanup even on continuation setup failure; old ABI unchanged. NOT implemented/qualified yet. Parent/directory ownership, current Dune/regressions, aggregate FD/RSS and broader benchmark/final integration remain open. All resources closed/no Photo/SDK/camera read/admission.

## 2026-10-18 — tracked native parent API component

Added abstract single-attempt StagePublication.parent_handoff (prepared false acknowledgement, no caller reset/forge API), parent_consumed and adopt_owned_tracked. Versioned C unison_stage_publication_adopt_tracked_v1 shares the existing adopt body but marks consumption AFTER strict pre-entry rejection and BEFORE native ownership/blocking/close/error. Immediate boolean store has no allocation/poll/write barrier requirement. Existing three-arg adopt ABI/behavior unchanged; generic stub leaves ack false and refuses. Source is owner-loop scoped, not a hostile ML/C sandbox.

Stock/Ox Make+selftests PASS parent19925/7c0b10/exit0/no session, children62561/63760reaped0/groupabsence/CPU8closed;327sourcepinsmatch. Fourteen real-native componentcases PASS: known transfer, ordinary consumed failure, pre-entry rejection unconsumed, post-entry close failure before/after kernel settlement, repeat refusal and post-call error acknowledgement. Two early-mark variants fail designated assertion; two private generic-branch compile/link/refusal controls PASS (simulated generic branch on Darwin, NOT other OS runtime qualification). Parent18834/e77e8c/0/controller66832reaped0/groupabsence/CPU3closed/noIO. Prior component001/31376/834f5d/0 also passed before generic extension. Original owned+legacy controls PASS parent75960/2326ff/0/controller65957reaped0/groupabsence/CPU3closed. Evidence tests/qualification/tracked-parent-api-actual-20261018.json.

Next integrate SemanticRemote parent ledger with abstract native acknowledgement, checking it in cleanup itself even if postcall bookkeeping fails; caller is STILL UNTRACKED/UNQUALIFIED today. Then directory ownership, current Dune/regression, aggregate FD/RSS/memory and broader benchmark/final integration. No SDK/Photo/camera/payload/admission; all resources closed.

## 2026-10-18 — actual remote native-parent caller integration

SemanticRemote now prepares the parent ledger/abstract handoff before clone-stage acquisition, adopts all returned handles immediately, and invokes adopt_owned_tracked. Cleanup reads the native acknowledgement directly, so a consumed parent is never closed locally even if the post-call continuation fails. A false acknowledgement retains the local close authority; before/after-kernel close uncertainty preserves original/parent/pair causes and blocks native abort/unlink/retry. Post-acquisition interruption roots all returned handles instead of continuing adoption. Transferred ownership is explicitly distinct from known OS closure.

Final stock/Ox Make AND Dune builds+selftests PASS actual parent30786/2147c2/exit0/no session; four build children78122/79405/81243/82683 reaped0/groupsabsent/CPU8closed, all327 production hashes current. Initial Dune70546/1c8f75/1 duplicate files-label warning preserved; corrected internal publication.staging_files label without suppressing warning. Earlier pre-rename Make/fault receipts remain historical, not substituted for final source checks.

Final16 actual caller cases PASS stock/Ox,2 intentionally always-transferred consumers reject designated pre-entry assertion;24 pair-close and8 native-publication regressions PASS. Actual parent29653/4a1407/exit0/no session; controllers84351/85503/86089reaped0/groupsabsent/CPU4closed/noIO. Controls use original8192B generated DNGs, real native adoption/APFS publication with in-process planner, no actual transport/SDK/Photo/camera payload. Preentry/interrupted and uncertain-close cases retain transaction/name/descriptor owners without repeated numeric close; process exit settlement is not claimed normal native teardown. Known pre-call failure may leave an unadopted recoverable private stage, not a general name-cleanup proof. Evidence tests/qualification/remote-parent-caller-actual-20261018.json, doc/native-parent-handoff-successor.md.

Resource branch implementation/owned-close-retention remains isolated pending final consolidated integration; no PR merge or deployment claimed. Next concrete gap is opaque directory acquisition/closedir ownership through actual CandidateValidation borrower, then complete aggregate FD/RSS/memory enforcement/accounting and broader SOL benchmark/final integration. Goal active, no Photo approval blocker/current owned jobs or resource holds; standing8/8 remains. Incomplete MakerNote meaning remains a gradual refinement, not a deployment gate.

## 2026-10-18 — prepared opaque directories and actual validation-tree ownership

Added DirectoryOwner before System_generic: preallocated owner/carrier/link/callback record before Unix.opendir, typed opaque GC-root adoption without Some allocation, single-attempt closedir, original operation+close causes and acquisition path retained. No numeric FD/inode invented, no retry/reset/uncertain-release API. System/Fs.with_directory preserves the existing dir_handle record and scopes all callback/publication failures. Windows wildcard checks retained; Windows fsmonitor link order includes the new dependency. CandidateValidation enumeration uses that scope; complete tree promise is guarded even with legacy unadmitted manifests. Positive Runtime admission recognizes the carrier; standalone guard itself acquires no credits.

Final stock/Ox Make+Dune/selftests PASS on329 current production hashes. Actual build parent24471/1439af/0/no session, four children93952/95163/96562/97719 reaped0/groupabsence/CPU8closed. All26 actual directory cases+4designated bad variants PASS, Windows Core/wrapper compiled on Darwin only. Both fixed in-process tree suites PASS (kernel14 each, normal/nested pass/reject/cancel/fresh-pass, old-budget negative and enumeration cancellation/removed-check). Existing Runtime IO12+4negatives/reader24+4negatives/pool20+4negatives pass. Remaining-control parent67451/d4706b/0/no session closed; stock directory child99165 passed0 within parent13332/55d9ae/1 whose later unrelated historical fixture failed. This outer exit1 is NOT relabelled success. Evidence tests/qualification/directory-owner-actual-20261018.json and doc/opaque-directory-ownership.md.

Preserved initial harness pathname collision, synchronous negative assertion, combined60s timeout (child91992 SIGTERM/reaped/groupabsence), and two stale historical fixture failures. Split compiler suites within unchanged60s windows; no production workaround. Historical Runtime fixtures add only an uncalled interface export. Old tree comparison adds destination field compatibility and actual old interface; budget rejection precedes context use. All failed/current groups and CPU scopes closed; no EXglobal/Photo/camera/SDK/transport work or admission. Generic-banner text is not a claim each single-compiler participant ran both compilers; per-record compiler identities define scope.

Next concrete review: complete legacy Os.childrenOf and Files.get_files_in_directory borrower/error cleanup; the prepared underlying System wrapper does not qualify every consumer. Unix stub failures before returning an opaque handle remain its boundary; Windows source/signature compilation is not native Windows runtime/link proof. Then aggregate descendant FD/RSS/memory and full acquisition/baseline accounting, broader SOL benchmarks and final consolidated integration. Resource branch implementation/owned-close-retention isolated, no PR merge/deployment/whole-goal completion. Goal active; no current jobs/resource/Photo scheduling hold; standing8/8 remains.

## 2026-10-18 — actual legacy Os/Files directory consumer cleanup

Os.allChildrenOf now uses Fs.with_directory with a prepared entered-callback flag: only acquisition ENOENT gives legacy empty listing; post-entry readdir ENOENT remains an error. Files.get_files_in_directory scopes all non-EOF failures through System.with_directory; sorting/filtering and public interfaces unchanged. Actual Os.childrenOf/Files.ls are linked/tested through real Runtime admission+I/O borrowers, not extracted-only helper mocks.

Stock/Ox Make+Dune/selftests allPASS on329 current production hashes; actual parent94684/30aaac/0/no session, children7341/8484/9901/11053reaped0/groupsabsent/CPU8closed.48currentcases+4historical whole-module designated rejections pass: names/missing/open-vs-readENOENT/original errors/publication and before/after-close uncertainty/repeated cleanup/unchanged tiny files. Unknowns retain actual Runtime transaction+device scopes and outer scheduling owner; process exit is not normal closedir proof. Source/test4 credits/noEXIO/SDK/Photo/camera/transport. Evidence tests/qualification/directory-consumers-actual-20261018.json.

Stock child13328 passed0 within parent54978/004276/1 (later separate Ox combined comparison exceeded unchanged60s and child14382 wasTERM/reaped/groupabsent/tokensclosed). This mixed outer exit1 is not relabelled pass. Fresh splitOx parent1273/2a2e9f/0/no session; children15835/16684/17690 allreaped0/groupsabsent/CPU4closed. Pre-split driver faithfully preserved with exact stock runtime sourceSHA. Initial test field-label compile11306/939a57/1 preserved/closed before cases. All current/failure resource scopes closed, no report hold.

Broader source search now pinned in doc/owned-resource-remaining-inventory-20261018.json. Next prioritize local SemanticSync pair/source/list/native-parent and borrowed transaction cleanup (still separate from qualified Remote); then joint SemanticMergeCache directory/quota/record/temp-name ownership. Solaris FEN raw directory callback is a separate legacy/platform finding, not a fabricated failure/new runtime gate. Fspath opendir text is commented history. Aggregate FD/RSS/full acquisition-baseline accounting, broader SOL benchmarks and final consolidated integration remain open. No new admission/Photo blocker; standing8/8 continues, goal active. Resource branch remains isolated; no PR merge/deployment/full completion.

## 2026-10-18 — actual local async transaction, parent and full producer ownership

Production SemanticSync async now prepares pair/source slots, original/interrupted errors and scope links before clone/source acquisition. No post-open descriptor list allocation. Legacy name owned only after creation; all independent closes attempted once, original+pair+source causes retained, raw uncertainty prevents unlink/native abort and keeps admission pending. Bound parent uses actual abstract tracked native acknowledgement, no pre-call boolean guess. Known raw pair/source close precedes native abort. Complete workers AND synchronous producer execute inside borrowed lifetime, including callback inner event-loop/connection cleanup; nested typed uncertainty retains all descriptors/name. Synchronous reference/capture/scalar merge are not relabelled qualified.

Stock/Ox Make+selftests actual67553/1a2981/0/no session (21495/22780reaped0), Dune+selftests90618/3b9053/0/no session (26538/27715reaped0), all329 production hashes current. Final74 directed cases+2deliberate close-swallowing rejections,8native-publication cases,64actual final-publication handoff regressions PASS actual55130/5c7902/0/no session; fourcontrollers29338/29667/30001/30058 reaped0/groupsabsent/CPU4closed. Prior72cases+2rejections3320/6d97b6/0 preserved before extra nested-uncertainty case, same production source. AllbuildCPU8/2compilerjobs scopes closed; noEXIO/SDK/Photo/camera/actualtransport/newadmission. Evidence tests/qualification/local-transaction-owner-actual-20261018.json and doc/local-transaction-ownership.md.

Known paths restore FD census; interrupted/uncertain stages preserve bytes, credits and owner evidence through repeated connection cleanup/GC. Unknown fixture ownership settles at process exit, not normal native teardown. Callback ordinary failure now proves raw pair/source already known closed before independent native-abort uncertainty; other native uncertainties retain actual held slots. Constructor handoff tests refreshed to prepared owners (local record failure pre-acquisition, remote bound record failure post-adoption); actual final publisher witnesses, original callback errors, replacement/rebind sentinels, unregister failures and FD reuse remain checked. Remote planner is in-process only. Unconsumed parent known pre-call failure may preserve an unadopted recoverable stage; no blanket name-cleanup claim.

Next concrete fix: Remote producer is still outside borrowed_with_publication (and classifier predates DirectoryOwner); local fix must be mirrored with active-callback/nested borrower controls, not inferred from these successful remote handoffs. Then separate compact-base capture/scalar-merge FD ownership plus joint cache directory/quota/record/temp-name retention. Immutable doc/owned-resource-remaining-inventory-20261018-v2.json pins scope and predecessor. Solaris FEN is separate legacy/platform finding. Aggregate descendant FD/RSS/full acquisition-baseline accounting, wider benchmarks/final consolidated integration remain open. Goal active/no pause/Photo approval blocker; resources0/standing8/8, no PR merge/deployment/full completion.

## 2026-10-18 — actual remote complete producer lifetime and directory carrier

Remote publish/producer/disarm now execute inside borrowed_with_publication, so synchronous callback inner event-loop cleanup marks closing without prematurely closing raw pair/native name. Original callback errors remain terminal. Added DirectoryOwner.Uncertain to the borrowed classifier: global admission retention alone is insufficient if inner candidate cleanup already closed/unlinked its working stage.

Current stock/Ox Make+Dune/selftests PASS329productionpins actualparent15712/76dc3e/0/no session, fourchildren34173/35346/36705/37862reaped0/groupsabsent/CPU8closed. Directed8currentcases+4designatedrejections PASS actual42952/ee7b4f/0/no session/controllers39252/39771reaped0/CPU4closed. Normal/cancel-active-callback/actualEBADFfilecarrier/kernelclose-then-EIOdirectorycarrier qualify pair/name/transaction retention and no retries. Exact oldRemote65de6192 closes active callback FD and fails designated assertion; removing onlyDirectoryOwner classifier loses stage borrower despite global admission uncertainty. These are actual raw/native effects, not synthetic fabricated settlement flags.

24pair+8native+64finalpublisherhandoff regressions PASS actual76941/7cd338/0/no session/controllers40721/41277/41346reaped0/groupsabsent/CPU4closed. All8+24+8+64=104positivecases plus4counterexamples, noSDK/Photo/camera/actualtransport/EXIO; generated8192BDNGs/in-processplanner only. Knowncases restoreFDcensus; unknownfixture owners end at actualprocessExit, not ordinarynative teardown. Alljobs/resourcesclosed. Evidence tests/qualification/remote-producer-actual-20261018.json and doc/remote-producer-lifetime.md.

Local and remote producer ownership checkpoints now separatelyqualified. Next: separate compact-base capture/scalar-merge descriptor owners and joint cache directory/quota/record/temp-name retention (doc/owned-resource-remaining-inventory-20261018-v3.json preserves predecessors). Aggregate descendant FD/RSS/full baseline accounting, broader benchmarks/platformstatus/final integration remain open. Goalactive/noPhotoapprovalblocker/no currentreservation, standing8/8. Resourcebranchisolated; no PR merge/deployment/fullcompletion.


## 2026-10-18 — prepared capture/scalar-merge input scopes

SemanticSync compact-base capture now prepares one opaque read slot; scalar merge prepares four (saved base absent on compact-cache hit). All owner/link/error storage exists before acquisition; descriptor adoption follows open, no post-open descriptor-list allocation. Independent slots close once; original failures, multiple close causes/preclose identities and full transaction admission remain retained on uncertainty. No historic numeric-FD retry, including kernel-close/recycle. Scope forensic accessors added; output name ownership stays with caller.

Stock/Ox Make+selftests actual14599/7c6b1a/0/no session; Dune+selftests91989/413edd/0/no session, all329 production hashes matched each. Directed40positive helper controls+2designated close-swallowing rejections actual56838/0e852c/0;34full merge acquisition/explicit-exception regressions92760/5c3a9c/0;6full capture/saved-base/cache-hit operations85204/ff8921/0, all no-session. Both compilers exact disjoint-XMP output and source immutability/FD+transaction+CPU+worker+IO settlement passed. All contained groups reaped/othersabsent/canonicalCPU4or8closed; noEXIO/Photo/SDK/camera/realtransport. Unknown fixture owners end at process exit, not normal in-process cleanup.

Initial parser-failed stock build001 (29989/429fac/1), harness fixture-name collision001 (86431/404ded/0 with child46948exit1), and pipeline003 CPU-contention refusal preserved. No positive claim from those failures; source/harness corrected into fresh successors. Pipeline003 did not launch because own Dune8 still held tokens; missing-CLOSED harness assumption failed, then004 ran only after actualDune terminal. Evidence tests/qualification/input-owners-actual-20261018.json; contract doc/capture-merge-input-ownership.md. No current resources held; standing8/8.

Next: joint SemanticMergeCache directory/quota/record/temp-name retention; current change does not convert ordinary cache internal close failures into typed uncertainty. Synchronous reference remains test-only/separate; inventoryv4 preservesv3. Aggregate descendant FD/RSS/full baseline accounting, broader benchmarks/platformstatus and final integration still open. Goal active, no Photo approval blocker, isolated resource branch only/no PR13 merge/deployment/full completion.


## 2026-10-18 — joint compact-base cache ownership and future-work refusal

SemanticMergeCache now roots one complete operation scope before cache acquisition. File and opaque-directory nodes link before opens; known resource lifecycles stay unchanged. Ordinary failure records original errors and attempts all independent closes; combined close errors retain every per-resource cause. Nested uncertain scans keep known outer-directory/quota ownership. Existing NotificationPipe scope-anchor carrier propagates through Runtime and async capture/scalar-merge without becoming a cache miss or releasing admission. Further enabled cache calls refuse before acquisition while any cache owner is retained.

Temporary opening/name evidence exists before O_EXCL; post-adoption interruption reconciles the created inode before close. Normal cleanup checks dev/inode before unlink; failed/unobserved identity, replacement or unlink uncertainty retains the name journal and is never retried. Quota format/nonblocking lock/capacity/monotonic charge/no-eviction behavior preserved. Same-UID cooperative private-state boundary, not hostile-path atomic isolation, aggregate FD/RSS or physical allocation cap.

Current stock+Ox Make/selftests and full regression parent73641/19b95f/0/no session; stock+Ox Dune/selftests2252/06f40f/0/no session; all329 production hashes current for all4builds. Final directed parent67914/868295/0/no session (controllers66876/67192reaped0/groupsabsent/CPU4closed). 40joint scenarios +12acquired-exception +58storage/quota +6full capture/saved-base/cache-hit +34merge-error/exception =150named positive scenarios;4designated negative rejections (two close-swallowing, two pre-adoption leaks). Storage scenarios include79torn-ledger prefixes/compiler. Combined quota+directory original failures, actual before/after-kernel closes/FD recycling, unlink ambiguity/replacement, interrupted temporary acquisition, full async outer retention and refusal of subsequent cache operations all covered. Unknown fixtures end at process exit, not normal in-process teardown. No camera/SDK/Photo/actualtransport/EXIO; all canonicalCPU4/8groups nowclosed.

Evidence tests/qualification/merge-cache-joint-actual-20261018.json; contract doc/merge-cache-joint-ownership.md. Earlier directed harness failures preserved: partial swallowing counterexample still retained through final backstop; nonexistent Lwt.map; absent-path fixture realpath before admission. Corrected into distinct source/control successors; no production retry/grant involved. Initial/pre-guard Make/Dune/test reports preserved; final source/checks explicitly pinned. Final002 directed report corrects controlled-directory SHA labeling and records good/bad binary identities, same test worker behavior as source-current001.

Inventoryv5 preserves v4 and closes the identified production capture/merge-cache ownership inventory item. Synchronous test/reference and Solaris legacy/platform findings remain explicitly separate; aggregate descendant FD/RSS/full acquisition-baseline accounting, broader benchmarks/platform status, and final consolidated integration/review remain open. Goal active/no Photo scheduling blocker/no held resources/standing8/8; isolated resource branch only, no PR13 merge/deployment/full-completion claim.


## 2026-10-18 — fixed worker infrastructure accounted before acquisition

Added SemanticAdmission.create_with_baseline and an accounting snapshot separating fixed, workspace, total and peak reserved planning costs. Fixed costs are subtracted before source-headroom/workspace grants and remain reserved for the gate lifetime. The original create and usage stay zero-baseline/workspace-only. Runtime reserves its two notification-pipe descriptors and 4096-byte completion-buffer payload before pool construction; the pump uses the same buffer-size constant. Existing 32-descriptor / 17 MiB minimum workspace preferences still work, with declared combined capacities of 34 descriptors / 17 MiB plus 4096 bytes. Default 512 workspace descriptors now explicitly declare 514 including this infrastructure. This is accounting, not an OS cap or complete process baseline.

Initial actual native census, parent23299/22bc6c/0/no session, found FD counts 3→5→3 with 1/2/4 workers on both compilers. Its old private probe source/binary are pinned separately, not relabelled as current. Current controls verify preflight opens no descriptors, simultaneous consumer24/source8 progress before pool startup, one-time baseline reservation, exact shutdown census, persistent planning allowance and overflow refusal before acquisition. Removing only the Runtime baseline debit fails a designated assertion. Both compilers pass 32 admission component tests (four new baseline groups), four Runtime scenarios and one designated omission rejection each.

Actual Make/selftest parent7183/ea50e2/0; Runtime baseline parent97084/31dcd5/0; native-lifecycle/retained regressions67753/e1d484/0; Dune/selftests37539/6bb9f9/0, all no-session. All four builds match all329 current production inputs. Lifecycle regressions retain 8 positive groups/58 assertions and4 designated counterexamples per compiler; retained-borrower regressions retain12 positive cases and2 historical counterexamples per compiler. Component parent25957/fea800/0; its existing runner deletes unit binaries, so only source/compiler/control output is sealed, without inventing a binary pin. The first regression controller92039/65e90b/1 is preserved: six positive lifecycle groups and the early-release counterexample ran, then a stale nested-borrow mutation anchor named f instead of current guarded. Refreshed only that anchor/replacement, keeping the classifier, and qualified fresh002. Old Runtime participant also gets an explicitly uncalled refusal binding for the new snapshot API, without changing its historic retention behavior.

Evidence: tests/qualification/fixed-infrastructure-accounting-actual-20261018.json. Contract: doc/fixed-semantic-infrastructure-accounting.md and resource-admission.md. Inventoryv6 preservesv5. All owned groups/processes reaped, CPU4/8 tokens closed, no EXglobal/SDK/Photo/camera/real transport work. Source branches and handoffs remain separate from consolidated PR13; no merge/deployment or whole-goal completion.

Still open: remaining baseline/acquisition families (domain runtime, transport/logging/UI, mailbox/heap metadata, transient native probes, legacy paths and helpers), aggregate descendant FD/RSS containment/capability policy, broader benchmark matrix and final consolidated integration/review. Fixed payload credits and sampled phase census do not satisfy hard RSS or whole-process FD requirements. Goal active; no Photo scheduling blocker or current resource hold; standing8/8.


## 2026-10-18 — framed decoder preallocation and bounded RPC expansion

Found and fixed a concrete Umarshal ordering gap: strings and bigarrays allocated a length-prefixed payload before verifying that the received frame contained it. A tiny malformed frame could request a much larger allocation. Private per-decode input contexts now validate offsets, the eight-byte declared payload header, remaining bytes and variable payload lengths before allocation/native copying. Subtraction avoids offset overflow before unsafe bigarray blits. Negative collections refuse. Valid encodings and prefix decoding inside valid frames remain compatible; malformed/truncated framing previously ignored now rejects.

Additive bounded bytearray/channel entry points track selected builtin allocation charges and collection elements across nested codecs, with non-allocating counter updates. Builtin buffer/string/list-spine charges are explicit; user conversions/property-map callbacks, framing/context/heap headers, recursion factory/depth and full RSS remain excluded. Ordinary legacy decoders do not impose collection expansion budgets; streaming input still needs a separate hostile outer-frame policy. Bounded RPC registrations now decode arguments/results with65536+8*frame_limit charged bytes and1024+4*frame_limit elements per decode. Scoped arguments can decode twice with separate limits. This is a local decoded-expansion policy, not a new wire encoding, global memory reservation or hard cap.

Current Make/selftest+directed parent68928/db17aa/0/no session, Dune/selftest91402/5dc305/0/no session, endpoint preference35589/6f9b78/0/no session; all329production hashes match each of4builds. Both compilers pass233library checks: old/new writer bytes, decode/re-encode through bytes/bigarrays/bounded readers, consecutive stream frames, malformed offsets/truncation/huge inner claims, exact byte/element limits, nested counts and invalid policies. Current AND reference variable-allocation sites have private safety guards; current errors must occur before those guards, while old dcaa1e08 string decoding reaches its designated guarded allocation. No huge allocation or unsafe reference-offset test is executed.

In-process RPC controls cover scoped/unscoped argument refusal, bounded normal result, header inner-length refusal, raw request retention through queued error-reply consumption, existing dynamic result/frame/input/output/connection cleanup. Removing only bounded decoders from the registration must fail a designated assertion on a finite2000unit request. Explicit compiler selection added to endpoint preference controls; all existing outgoing/incoming/alias/profile precedence checks pass. Reports retain RPC positive/negative source and binary identities when requested. No real transport/SDK/Photo/camera/EXglobal IO or benchmark run; CPU4/8 groups all reaped/closed.

Evidence tests/qualification/framed-decoder-bounds-actual-20261018.json; contract doc/framed-decoder-bounds.md; immutable remaining inventoryv7 preservesv6. Earlier narrower successful probes/builds are preserved, not relabelled current; final source and safety guards/stronger roundtrips are explicitly pinned.

Still open: shared/legacy outer RPC frame allocation caps, aggregate decoded-object reservation through queued work/replies, remaining metadata/conversion/depth and acquisition/baseline families, aggregate descendant FD/RSS containment/capability policy, broader benchmark matrix and final consolidated integration/review. Default channel input whose outer header itself lies is not globally bounded by the inner preflight. No whole-goal completion, production deployment, PR13 merge or new payload admission. Goal active, no current resource hold or Photo scheduling blocker; standing8/8.


## 2026-10-18 — independent shared RPC header admission

Shared RPC headers now reserve a slot before reading even their length prefix, then raw bytes before allocating the payload. Endpoint-local defaults: rpcheadermaxbytes8MiB, rpcheaderinputbudget16MiB, rpcheaderinputslots256 (maximum65536). Limits validate before input; current policy may tighten a pending acquisition. No wire encoding change. Separate header allowance permits header/reply progress while bounded-body credits are full. Fresh per-receive tickets release on malformed decode, allocation failure and actual read settlement/disconnect; no CPU/body wait added. Legacy body/result/stream frames and startup negotiation remain separate.

Both compilers pass exact cap/route, idle-prefix slots, policy tightening, injected preallocation rollback, malformed header, byte/slot exhaustion, independent body-budget progress, endpoint preference omission/poison refusal and existing bounded RPC regressions. Private old-route/old-decoder participants fail designated assertions with allocation guards; no huge allocation or actual network/SDK/Photo/camera operation. All four Make/Dune builds match329 current production hashes and pass selftests; explicit-compiler endpoint controls pass. Actual Make/direct-controls parent20877/e66753/0/no session. Final Dune/preferences parent92811 authentic retained runtime item_completed2026-10-18T13:33:47.243Z statuscompleted/exit0; later handle missing, not inferred from ps. All eight contained controllers reaped0/groupsabsent/CPU tokensclosed; no EXglobal. Initial001 predecessors preserved, not relabelled source-current.

Evidence tests/qualification/rpc-header-input-actual-20261018.json; contract doc/rpc-header-input-limits.md; inventoryv8 preservesv7. This bounds selected raw headers, not decoded-object aggregate retention, recursion/conversion/metadata, process-tree FD/RSS or every legacy frame. Next: remaining startup/legacy frame policies and decoded-object reservation, remaining acquisition/baseline families, aggregate descendant FD/RSS capability policy, broader benchmark matrix and final consolidated integration/review. No current resource hold or Photo scheduling blocker; standing8/8. Resource branch remains separate from PR13; goal active, no merge/deployment/full-completion claim.


## 2026-10-18 — bounded startup fields and shared input reservation

Committed predecessor287c916a header checkpoint is pushed. Successor startup policy rpcstartupmaxbytes defaults65536, endpoint-local/peer-proof. It counts every field byte including ignoredCR and separators, refuses a missing delimiter at the exact boundary without waiting for another byte, uses a fixed-size bytearray and reserves twice the field maximum plus one shared header/startup slot before allocation/input. Fixed-length startup and legacy magic packet also bounded/reserved; header single-frame cap remains independent. Actual borrowed read settlement governs release; no waiting on body/CPU credits. Policies captured per field; not a timeout. Empty fixed/buffered diagnostic reads now return empty instead of calling positive-length-only grab. Valid CR/separator/OK/NOK/version/magic bytes preserved. Connection prefetch/diagnostic peek remains fixed16384 and outside this charge; decoded results/version lists/exceptions can outlive raw allowance.

Both compilers pass current directed controls including exact boundaries, allCR, missing delimiter, malformed/empty diagnostics, preallocation failure rollback, byte/slot refusal before input, actual disconnect, endpoint preference isolation and old delimiter-cap omission rejection on nine original bytes. Existing header-route/decoder designated counterexamples remain independent; no large allocation/unsafe old-buffer write. Directed actual4658/4fe0d9/0/no session. Final current Make+Dune+selftest+endpoint preference parent62988/b97215/0/no session, all four builds match329current production hashes. All eight contained controllers reaped0/groupsabsent/sourcepinsunchanged/CPU4or8closed; no EXglobal/Photo/camera/SDK/actualtransport or benchmark.

Two fixture failures preserved: first001 configured1MiB shared budget below8MiB header cap, correctly refused (86004/fd02c1 parent0 but child1, no functional pass); directed003 expected synchronous allocation exception instead of failed promise (63958/c6ac53/1). Fixture policies/await corrected into004; no production error weakening. Initial001 builds and002 controls passed before final empty-read fix and are explicitly historical.

Evidence tests/qualification/rpc-startup-input-actual-20261018.json; contract doc/rpc-startup-input-limits.md; inventoryv9 preservesv8. Next: legacy unbounded body/result/stream frame policy, aggregate decoded-object reservation, remaining acquisition/baseline families, aggregate descendant FD/RSS capability policy, broader benchmarks and final consolidated integration/review. Goal active, standing8/8/no current resource hold or Photo scheduling blocker. No PR13 merge, deployment, full-goal completion, new SDK/payload grant or automatic successor.


## 2026-10-18 — finite common outer RPC frame policy

Added endpoint-local rpcpacketmaxbytes default268435456(256MiB) to the shared packet reader. Captured before prefix input, checked before reserve callback/body allocation/read; minimum with every explicit command/header/startup cap. Applies to formerly unbounded legacy request, unregistered-limit normal result and stream branches as well as bounded readers. Zero-length frames and valid wire encodings preserved. No unbounded/off setting; deliberately larger archive frames require raising the local limit. No profile/installation/peer change. Policies are positive integers; bigarray payloads are not limited by OCaml string-size ceiling. This avoids an invalid default on32bit; max_int policy tested only with an empty payload, NOT32bit execution/large allocation.

Both compilers pass exact/zero size, global-vs-explicit minima, invalid policy, refusal before reservation callback, all three actual legacy oversize routes and successful legacy request/result/stream handlers, plus endpoint preference isolation. Only-global-cap-omission participant reaches private preallocation guard and fails the designated assertion; decoder/header-route/startup negatives remain independently checked. Current parent87581/c2fc66/0/no session includes directed controls, all stock/Ox Make+Dune+selftests and endpoint controls. All four builds match329current production inputs; all eight controllers reaped0/groupsabsent/tokensclosed/sourcepinsunchanged. No EXglobal/SDK/camera/Photo/actualtransport or performance operation.

Earlier001/002 directed runs and initial001Make/Dune/prefs(38539/b04fb8/0) passed before removing the inappropriate string-size validation; preserved, not relabelled current. Final003 controls include safe positive-large-policy regression and actual valid legacy routes. Evidence tests/qualification/rpc-outer-frame-actual-20261018.json; contract doc/rpc-outer-frame-limits.md; inventoryv10 preservesv9.

Outer per-frame limits are NOT aggregate admission: legacy work/consumer promises can retain multiple raw frames and decoded values; raw header/startup tickets do not cover retained exceptions/version lists. Next: aggregate packet/decoded lifetimes and remaining baseline/acquisition families, descendant FD/RSS/platform capability, broader benchmarks and final consolidated integration/review. Goal active, no current held resources/Photo scheduling blocker, standing8/8. Resource branch remains separate from consolidated draft PR13; no merge/deployment/full-completion/new payload grant or automatic successor.


## 2026-10-18 — aggregate raw request/stream and reply ownership

Incoming bodies now use endpoint-local rpcrequestinputbudget256MiB for legacy+bounded requests/streams and independent rpcreplyinputbudget256MiB. rpcbodyinputslots256 applies to EACH lane (max65536). Slots precede even incomplete prefixes; exact byte grants precede body allocation. Nonwaiting refusal; header/startup and reply service progress independent of full requests. Existing bounded64MiB/4096slots remain an overlapping subset, not additional raw allocations to sum. A fresh ticket roots payload until release. Detached request scope includes actual handler, marshaling/queued reply; streams include queued abort; reply promises hold owned packets through scheduling yield and synchronous decode. Already-arrived replies are abandoned after actual waiter settlement if outgoing send fails. Preallocated Return precedes handoff observer dispatch; exceptions at/after transfer intent cannot release potentially-live consumers.

Core ownership carriers keep raw AND bounded-subset charges via RetainedOwnership.guard; stream uncertainty is not translated to ordinary abort. Owner-loop pure classifier registration supports types defined after Remote; SemanticRuntime registers its existing semantic-file/component-cache predicate at initialization. Direct raw tests use a synthetic child carrier, not an actual semantic-file fault in that receive stack. Actual current Runtime reader-fault regressions remain separately qualified. Arbitrary unregistered exceptions are not automatically recognized; existing qualified enclosing scopes still apply.

Current direct parent76246/87aa0a/0/no session: both compilers pass live detached work/connectionclose, actual queued legacy output success/failure, reply arrival before send failure, empty/prefix/exact byte limits, allocation/reserve failure, decode cleanup, independent reply/header progress, actual observer exception after handoff, normal blocked-urgent stream abort and typed retaining guards. Nine designated negative participants/compiler (four frame/decode/startup predecessors plus five new ownership mutations) fail intended assertions. Synthetic retained tail keeps3rawbytes/3requestslots/1boundedbyte+slot/3guardentries and reachable payloads until test process exit; no directory/nativeFD acquired, no fabricated in-process teardown.

Final Make+Dune/selftest/endpoint parent55775/5fad85/0/no session; all four builds match329current production hashes. Runtime retained-reader and baseline parent6454/745d64/0/no session:12positive reader scenarios+2historical negative rejections/compiler, fixed FD census3→5→3 for1/2/4workers and overflow-before-acquisition preserved. All12 canonicalCPU4/8controllers reaped0/groupsabsent/sourcepinsunchanged/tokensclosed; no EXglobal/Photo/camera/SDK/actualtransport. Unknown native-reader fixtures also terminate at process exit, not in-process closure.

Preserved fixture003 failure: normal-write pause does not block Urgent; use actual unfinished output action, then settle it after queue closure. Preserved005 overall failure: positive ran, but registry-omission negative lost its only inferred type constraint and failed compilation; explicit (exn->bool) registry annotation fixes the mutation without weakening behavior. Narrow initial001/002/004 passes are historical. Evidence tests/qualification/rpc-body-input-actual-20261018.json; contract doc/rpc-body-input-lifetimes.md; inventoryv11 preservesv10.

Still open: aggregate decoded-object/conversion/outbound retention and remaining metadata/receiver/acquisition/baseline families, descendant FD/RSS capability policy, broader benchmarks and final consolidated integration/review. Raw defaults512MiB+separate16MiBheader/startup allowance are not hard RSS, measured peaks or a complete semantic/whole-process budget. Goal active/no current resource or Photo scheduling hold/standing8/8. Resource branch remains isolated; no PR13 merge/deployment/full completion or new payload authority. Consolidated HEAD5a3d4077 has8extra qualification/test-lifecycle commits; resource branch was34ahead before this checkpoint. Source integration is next alongside remaining resource work; do not repeat already consumed admissions.


## 2026-10-18 — consolidated resource review candidate

New authoritative integration worktree /Users/alexy/src/unison-sol-resource-review-20261018, branch integration/sol-resource-consolidated-20261018, merges review5a3d4077 with resource26fd666a. Only OPUS-HANDOFF.md conflicted; both histories retained. Production src/build configuration is identical to26fd666a. Four retained stock/Ox Make+Dune receipts each match all572recorded inputs (329production); binary/compilerSHA freshly verified. Reused exact builds/selftests, not a fresh compilation claim. PR13/oldreview/resource branches not merged or rewritten.

Fresh combined controls: stock/Ox in-processRPC9designated negatives each, strict group selection, shared-sync pure lifecycle and saved-summary controls pass. Firstdriver36710/547ea9/1/no session contains five passes+onefailed metadata audit (passed derived summary instead of raw input). Corrected actual95c6f8/exit0/no session audits exact6272262B historicalraw and reproduces592744Bsummary byte-identically; no benchmark/sync/native/SDK/Photo operation repeated. Sixsuccessful plus onefailed containedgroups allreaped/CPU3or4closed/noEXglobal. Retained synthetic RPC logical owners end at process exit, not fabricated in-process teardown.

Evidence tests/qualification/sol-resource-consolidation-actual-20261018.json; current full-scope map doc/sol-release-readiness-20261018.md preserves all12SOL acceptance areas and substantive M6 FD/RSS/performance gaps. Historical warm32MiB parent53602/301032/137 independent recovery and original workerwait4notclaimed remain unchanged; all rawbytes/samples preserved. No quiet/currentbenchmark relabel or newadmission.

Next: freeze/publish this review branch, prepare fresh generated-property/mixed-peer IO qualification for current ownership/RPC source and coordinate exactfinitePhoto window beforedispatch; continue aggregate decoded/outbound/baseline and supported whole-tree FD/RSS work. No fullgoalcompletion/PR13merge/production activation/sourcephoto writes; standing8/8/2/noresourcehold. Oldworktrees retained; use new integration branch for continuation.


## 2026-10-18 — fresh combined-candidate IO requests prepared

Integration merge b6904f65 published. During request preparation, retained-peer full400-source plan reached67794B and correctly refused the64KiB metadata reader. Partial upstream-v1 plan/request and retained-v1 plan are preserved with doc/sol-resource-requalification-v1-PREPARATION-REFUSED.json; no owner/admission/locks or transport executed. Explicit mixed-peer plan read now permits256KiB, while canonical IO pool/admission callers retain64KiB default. Same owner/nlink/identity/SHA/qualified-close rules; no source pins discarded and no new canonical lock probe. Invalid metadata limits refuse before open.

Actual81unit methods passed:15disposable IO/reader methods plus66mixed-peer methods across7suites. First5410da/exit1/no session contains successful owned-JSON child55227/reaped0 and subsequent python-m argv refused before child/tokens; corrected repository scripts15304/190166/0/no session allreaped/CPU3closed. Evidence tests/qualification/mixed-peer-plan-capacity-actual-20261018.json SHA01b18bb21fa6a037dd03f80bf65d105b5df757c753a908f54e84e59173641a66. Native329sources/buildinputs unchanged; existing binaries retained.

Fresh source-only bundle doc/sol-resource-requalification-requests-v2.json SHA3b49e39e392ad2287ca22dc8ed8b517696566b21efb9db814e10eef2198718f3 contains: genuineupstream requestab99d702/plan9d89fc86, retainedfork request41f86b36/plana1d27dda (400executionpins each/4cases12CLIeach); property request49b97ea4 (43executionpins+329productionpins/18rows54CLI/two2MiBfixtures). Allmetadata checked with actual entry.checked_plan/manual.command/checked_build; property checked_io_request used only an in-memory inert control, never wrote a fake Rootadmission. Canonical manifest metadata read only/no locks. All3namespaces/admissions absent at preparation; no dispatch/SDK/Photo/camera/nativeUI/compiler/quiet/18borrow or implicit successor. Exact futureRootadmission required separately for each; recommendedmixed-upstreamfirst.

Source baseline field b6904f65 is the integration commit; metadata executor cap successor and exact400/43source closures are pinned by v2plans plus the81method qualification. The source/request publishing commit follows; do not treat a frozen hash as filesystem immutability or use v1partial proposals. User-facing default stays8/8/2 and no current owned CPU/IO/native job exists. Next coordinate one finite IO run at a time, return actual owning-toolterminal promptly, retain unknowns, continue remaining full-goal work; no PR13merge or production activation.


## 2026-10-18 — published requalification bundle sent to Photo

Source/request commit203dc1f1 pushed on integration/sol-resource-consolidated-20261018. Sent exact bundle3b49e39e and genuineupstream-first request to PhotoRoot queue01a14f8b-8a04-71c2-a0f0-121ed4565994 (thread01a13369-8b68-7aa1-be91-cba984ba269b). Durable tests/qualification/sol-resource-requalification-queued-20261018.json records the actual successful queue command, not a runtime grant. No current Unison owned jobs/tokens/IO/native reservation; all3proposed namespaces/admissions absent just before notification. Root must separately review/publish fresh exact admission/deadline; no waiting hold or automatic successor inferred. All400mixed execution pins/43property execution pins remain frozen in this worktree; source-only future work can use a separate successor branch while admissions are pending. ReturnactualSTART/terminal promptly if admitted, freshguard/no replay.


## 2026-10-18: decoded preallocation admission checkpoint

Source successor `/Users/alexy/src/unison-decoded-input-20261018`, branch
`implementation/decoded-input-accounting`, adds caller-owned incremental
reservation to all three bounded Umarshal input forms. Stock/Ox final controls:
78 checks and two negative mutation participants each; private allocation-site
witness rejects late reservation. Existing 233 bounds controls/compiler pass.
Four Make/Dune builds/selftests passed, all production inventory hashes still
match; only the subsequently strengthened test probe differs. Actual final
control parent runtime event61031 completed0; build owner17390/db16d4/0.
Initial fixture failure21992/c7b291/1 preserved. Evidence
`tests/qualification/umarshal-accounting-hooks-actual-20261018.json`
SHA b19ea41353210839aea90ab9e64f864f34728e579e4cb130b68a86abffa8884c.
See `doc/decoded-allocation-accounting-hooks.md` for scope and remaining work.
This is NOT yet RPC aggregate decoded-lifetime integration or hard RSS/heap
containment. Next implement explicit decoded owners through handler/result
lifetimes; never refund merely at decode return or rely on root finalizers.
Frozen IO candidate9d9dccc0 and its three requests remain separate/unchanged;
no new admission observed at last check, no dispatch/replay. Full SOL goal
active/incomplete. Standing8/8 continues, no Photo resource hold inferred.


### 2026-10-18 current continuation: one decoded argument per scoped RPC

Active source worktree remains `unison-decoded-input-20261018`. Decoder hook
checkpoint c2459bf2 is pushed. Current uncommitted Remote successor unifies the
server scope and handler under one decoded argument, keeping dispatch/marshal/
queued-output consumption inside the scope continuation. This removes duplicate
argument expansion and establishes the point for the forthcoming decoded owner;
no aggregate decoded lifetime cap is claimed yet.

Actual stock/Ox RPC controls parent15118/0fc241/0/no session passed full existing
bounds/header/startup/packet/body/retention suites plus new mutable-value identity
and conversion-count checks. Double-decode mutation fails the designated witness.
Initial stock001 fixture expected the handler exception text but the normal RPC
exception path serialized it first; corrected post-dispatch count witness in002,
original001/fc36ff/1 and all closed resources preserved. Full Make/Dune build
successor is live owner97888, not yet a build pass. The preceding launch aa4ee4/1
refused wrong compiler prefix before shared_dispatch entry/any compiler/token;
empty stock-check001 preserved, corrected `/bin` prefix uses002 workspaces.
No IO admissions observed; frozen candidate9d9dccc0 remains unchanged.


### 2026-10-18 single-decode RPC successor actually qualified

All four stock/Ox Make+Dune build/selftests now PASS/CLOSED actual controller
97888/6fbef2/exit0/no session. Direct children70163,71299,72421,73666 reaped0,
other group members absent and CPU8 descriptors closed after each. Every recorded
source input and retained binary hash matches current source. Both actual RPC
suites pass (15118/0fc241/0); added double-decode participant rejected alongside
existing framing/header/startup/packet/body/uncertainty controls. Initial test
witness diagnostic failure and compiler-prefix preentry refusal are preserved.
Evidence `tests/qualification/rpc-single-argument-decode-actual-20261018.json`
SHA 24aec771672e449aaa75b701e9cbf3622e377e94194c291c2aba541daaeb7b8a.

Next implement explicit bounded-request decoded owners using the new server
continuation, with finite aggregate slots/selected bytes/elements and retained
partial debits through actual handler+queued-output settlement. Caller result
leases, legacy decoded expansion, arbitrary retained conversions and full heap/
RSS remain open; do not label this refactor aggregate memory enforcement.
No current build/test/EXIO owner from this checkpoint. Three frozen candidate
requests remain separate, no admission observed at latest check; never alter or
replay them. Full goal active/incomplete; standing Unison8/Photo8/system2.


## 2026-10-18 bounded decoded-argument aggregate owner in progress

Active source branch remains implementation/decoded-input-accounting after
8c44d239. Current uncommitted Remote adds rpcdecodedrequestbudget256MiB,
rpcdecodedrequestelements1048576 and rpcdecodedrequestslots256/max65536.
Bounded registrations decode through an independent nonwaiting slot/selected
byte/element owner, with overflow-safe debit and explicit decoded-value root
through scope/handler/queued output. Typed or classifier uncertainty roots a
preallocated retention link and value; selected counters are not full heap/RSS.
Legacy args, client result leases, conversions/metadata/outbound still open.

Initial source+typed-owner suites actual24531/fc10ef/0 passed stock/Ox. Expanded
three mutation controls (bypass, early release, classifier off) actual17063/
041769/0 passed both compilers. Added compound/policy/overflow and multiple
classifier-failure roots; stock003 failed its OLD registered-classifier mutation
because the new classifier fixture ran earlier than its designated witness.
Production positive passed; original24596/b5f938/1 and receipts preserved. Fixed
fixture ordering (old raw-body retained tests before new decoded-owner tests).
Final tests currently live controller55497, stock77685 passed/closed, Ox active.
No build pass claimed yet for this owner successor; next full Make/Dune builds.
No Unison EXIO or SDK/Photo payload. Frozen9d9dccc0 requests untouched; latest
all three admission paths absent. Standing8/8, goal active/incomplete.


## 2026-10-18 bounded decoded argument owner actually qualified

Four current stock/Ox Make+Dune builds/selftests PASS, parent95366/5e1525/0/no
session, children78405/79551/80678/81968 reaped0/groups absent/tokens closed.
All575recorded source inputs per build and binary hashes match current source.
Final direct RPC suites55497/0b5c22/0 passed stock/Ox, 13 designated negatives
per compiler incl bypass/early-release/classifier-off. Explicit weak-value roots
survive typed/classifier-failure uncertainty; selected charges remain retained.
Fixed targeted Remote waiter/timer/socket controls84801/fbfbbe/0 passed seven
cases/compiler (stock84900/Ox85352 reaped0/groups absent/CPU4closed). These test
current Remote directly, not a new full semantic report/native qualification.
Initial two stale unrelated fixture preflights and one early post-gate assertion
are preserved in001/002/003; corrected004 waits actual promise settlement.
No production change was made to fix these fixture failures. New rpc_test.ml is
an independent test input added after CLI builds, not a production CLI source.

Evidence tests/qualification/rpc-decoded-request-owner-actual-20261018.json SHA
1124df8cd2d98430828bf34c9312d2709d537a185812fd79f076ed8c9d933c45. Inventoryv12 and decoder-owner doc updated. No live owner/EXIO/Photo resource
from this checkpoint. Bounded requests now own aggregate selected byte/element/
slot charges through queued replies. Legacy args/streams, client result leases,
conversion/global escapes, baseline/outbound and full FD/RSS/acceptance remain
OPEN. Full SOL goal active, not complete. Next source work should extend legacy
request decoding and establish explicit client-result ownership; do not shrink
completion to the bounded subset. Frozen IO candidate9d9dccc0 requests unchanged,
no admission observed; no replay. Standing Unison8/Photo8/system2 continues.


## 2026-10-18 ordinary legacy RPC argument owner extension in progress

Active implementation/decoded-input-accounting after ec232931 now routes ordinary
registerServerCmd arguments (and Host/Root wrappers) through the SAME selected
byte/element/slot owner as bounded commands. The legacy decoder uses finite owner
policy limits directly; it does NOT guess a raw-frame expansion ratio. Existing
codecs/tags/valid wire encoding remain unchanged. Custom stream decoders, client
result leases, conversion/global escapes, baseline/outbound/full heap/RSS remain
open. No final-goal completion claim.

Actual direct suites63763/67aa61/0/no session passed stock/Ox,14designated negative
participants/compiler (new ordinary-registration owner bypass included). Original
legacy+bouned mixed queued requests share one budget; valid compact2000-unit
collection passes while malformed/element-refused legacy input does not dispatch.
Full four-build controller74223 currently active under Unison8; no EXIO. Keep
production/test sources fixed while it runs. Frozen9d9dccc0 requests unchanged;
three admission paths absent at latest read, no IO grant/dispatch/hold inferred.


## 2026-10-18 ordinary legacy decoded argument ownership qualified

Regular registerServerCmd (therefore Host/Root wrappers) now uses the same
selected-cost owner as bounded commands. Local legacy limits come directly from
finite owner policy, not a guessed encoded expansion ratio. Tags/wire unchanged;
large valid legacy requests may explicitly refuse under configured admission.
No unbounded fallback or full heap/RSS/compatibility-matrix claim.

Actual direct suites63763/67aa61/0/no session passed14negative participants per
compiler; valid compact2000-unit legacy collection and mixed legacy/bounded
slot contention covered. Four current Make/Dune+selftests74223/5de746/0 closed,
children87664/88799/89880/91096 reaped0/groups absent/tokens closed. Current
recorded source inventories/binary hashes match. Fixed shared-owner waiter
checks16224/ee868b/0 closed (stock92394/Ox92843), seven cases/compiler through
bounded registration, no separate legacy transport/native test inferred.
Evidence tests/qualification/rpc-legacy-decoded-owner-actual-20261018.json SHA
8df0166c9661fce2b71faa07a472791170128576fc4e57c5774302b9393a60c1. Inventoryv13/decoder doc updated. All owned resources from this checkpoint
closed; no EXIO was acquired. Frozen candidate9d9dccc0 exact IO requests still
separate/unmodified; latest admission paths absent, no dispatch/replay/hold.

Next actual work: explicit client-result owner/consumer scope and its production
semantic call-site lifetimes; audit custom streaming's raw-buffer views/fixed
metadata; continue outbound/baseline and supported whole-tree FD/RSS work. Do not
pretend arguments close result lifetimes or arbitrary conversion/global escapes.
Full SOL goal remains active/incomplete. Standing8/8/system2 unchanged.


## 2026-10-18 streaming token preflight work IN PROGRESS (not committed)

Active decoded-input branch40354237 has uncommitted Remote.decodeInt five-byte
range guard, Copy raw-view codec ordering and Transfer complete token-slice
syntax preflight, checked basis ranges/fallback counts/short reads. New original
tests/transfer_instruction_bounds compile exact integer/Copy fragments plus full
Transfer, private guards before old mutations' invalid accesses/writes. Actual
112checks/compiler+5mutation participants in27903/f6bebd/0; RPC regressions14each
98471/b9e05a/0 passed. No actual transport/native clone/SDK/Photo/EXIO used.

IMPORTANT review finding BEFORE SEAL: the new rsync copy ELSE branch lacks
explicit begin/end after inserted read-count guard; multi-buffer copies can
reach an extra outer write. Must FIX, add >8192-byte block test, and requalify.
Also replace blanket blockSize>max_int/255 refusal with per-block count check
(k>max_int/blockSize) to preserve valid large single-block/EOF behavior. These
are not yet fixed because full build controller19823 is live; finish its owned
jobs normally before changing production source. Do NOT seal those intermediate
builds as final. Current stock Make/Dune passed but behavioral gap remains.
Next tests: valid24576-byte block group, short read after first8192 valid bytes,
nonzero view tests alreadypass. Current token tests may miss else grouping bug.

All three frozen9d9dccc0 IO request admission files remain absent at last read;
no newIO grant/hold. Fullgoalactive; standing8/8. Keep handoff explicit untilfixed.


### Streaming follow-up: review findings FIXED, final builds running

Intermediate controller19823/64e1a2/0 genuinelyclosed all4builds, no runtime
dispatch. Those source artifacts are superseded, NOT final behavioral proof.
After closure, fixed rsync else grouping with begin/end; replaced blanket large
blockSize cap with per-token k>max_int/blockSize overflow guard. Added24576B
block copy and actual later-chunk truncation test plus guarded negative for the
wrong grouping and missed full-buffer read check. Final direct controls118checks
and7negativeparticipants/compiler ACTUAL42252/c847ce/0/no session, stock3674/Ox3878
reaped0/groupsabsent/CPU4closed. Current finalbuildcontroller2609 LIVE usesfresh
002workspaces, max8credits/2compilerjobs, noEXIO. Do not claim all finalbuilds until
actualterminal. EarlierRPC14negative controls/compiler98471/b9e05a/0 covered same
Remote/Copy guards; Transfer-only grouping/arithmetic changed afterward and is
covered by final118tests. Full finalproduction source differsfrom intermediate.

Next source finding to handle after this checkpoint: Copy passes srcFileSize to
output creation/EOF clone length check but current Transfer generic/rsync token
steps do not receive a per-file remaining-output bound. Audit/implement that
before claiming write-amplification control; actual output publication guards
stillapply, no observed payload exploit or newcurrentadmission. Then client
result leases/customstream fixedmetadata and otherbaseline/FD/RSS remain open.


## 2026-10-18 stream integer/token/basis checks final qualified checkpoint

Source findings fixed before sealing: multi-buffer else grouping now explicit,
actual block-count overflow checked without blanket refusal of large valid
single-block/EOF sizes. Final production inputs match all four stock/Ox Make+
Dune/selftest snapshots002; ACTUAL2609/f506ba/0/no session, children4298/5442/6535/
7774 reaped0/groups absent/CPU8closed. Intermediate19823 builds remain superseded,
not used as final proof. Final118direct checks+7guarded mutations/compiler actual
42252/c847ce/0 closed; currentRemote RPC14negative regressions98471/b9e05a/0closed.
Multi-buffer24576B, partial/full fallback, receiver-basis skip callback, nonzero
views, malformed syntax and actual later short-read covered on disposable data.
No native clone/transport/SDK/Photo/original payload/EXIO operation inferred.

Evidence tests/qualification/transfer-token-framing-actual-20261018.json SHA
a972850d24b4487a52bce631a7a3a63eeacc6d7dabdfedb60eff2906c95594a1. Source doc stream-instruction-framing.md and inventoryv14 retain exact scope
and intermediate review failures. No current owner/resource hold from checkpoint.
Next implement cumulative per-file output bound using Copy srcFileSize/actual
append position (no repeated valid-block amplification); then client-result
lifetimes and remaining streaming workspace/baseline/whole-tree FD/RSS. Full
SOL goal ACTIVE/INCOMPLETE. Frozen9d9dccc0 threeIOrequests remain unchanged and
no admission observed; no new dispatch/automatic retry/quiet exception. 8/8 stays.


## 2026-10-18 cumulative output allowance IN PROGRESS

Active b48e0ca7 successor adds opaque owner-loop Transfer.output_limit. Copy
creates it once before lazy FDs: expected total minus DATA_APPEND prefix; RESS
counts payload, not physical header offset. Complete-frame logical counts
include block skips; overrun/short EOF refused before token writes/callbacks,
charges never refunded after IO failure. Exact EOF fences further payload.
Added pure check_output_limit at both Copy decompressor entries BEFORE lazy
basis/output opening; final unit/source-binding assertions cover this placement.
No native settlement/publication/physical IO/RSS claim from the counter.

Initial builds33297/4f5211/0 closed with correct basic counter before final
pre-open EOF check; superseded by current final31433 build controller (LIVE,
fresh002workspaces). Final direct tests32053/f3bf41/0/no session passed163checks
and9guardednegativeparticipants/compiler, stock17302/Ox17632 reaped0/CPU4closed.
Actual multi-packet generic+rsync, resumed generic, resource-header offsets,
full/partial callbacks, skips and no-refund/late EOF covered. No transport,
SDK/Photo/original/nativeclone/EXIO invoked. Keep production/test sources fixed
until finalbuildcontrollercloses. Next client-result lifetimes/custom stream
workspace/baseline/full FD/RSS and remainingSOLmatrix. Frozen9d9dccc0 requests
unchanged; last3admissionpathsabsent, no dispatch/replay/resourcehold inferred.


## 2026-10-18 caller-bound cumulative output allowance qualified

Final source now includes pure logical-end checks at both Copy decompressor
entries BEFORE lazy basis/output opening. All four current stock/Ox Make+Dune
build/selftests actual31433/c41bab/0/no session PASSED/CLOSED; children18255/19374/
20496/21670 reaped0/groups absent/CPU8closed. All recorded source inputs/binary
hashes match current source. Earlier33297 initial build group is superseded,
not substituted for final guards. Direct controls32053/f3bf41/0 passed163checks
and9guardednegativeparticipants/compiler, stock17302/Ox17632 groups/CPU4closed.

Opaque allowance shared across all frame calls counts logical materialization
(including block skips), not physical writes. Expected total minus append prefix;
resource header offsets excluded. Overrun/short EOF refuse before token writes
or copy callbacks, no refund after IO failure, exact EOF prevents further work.
Copy helper/call/pre-open placements pinned by source assertions and full builds.
Actual multi-packet generic/rsync, resumed and resource-offset encoders tested on
original disposable <=80KiB fixture files. No actual transport, APFS syscall,
SDK/Photo/original payload, EXIO, physical-budget or publication proof inferred.
Evidence tests/qualification/transfer-output-allowance-actual-20261018.json SHA
087e84b33992e0e7f5c4ed02d33098075795faf257d100280c7d82a93602d2ff. Inventoryv15/framing doc/readiness updated. No live Unison owner/resources
from checkpoint. Next client-result consumption leases; custom stream tighter
frame/workspace/baseline and full FD/RSS/current fullSOL acceptance still OPEN.
Frozen9d9dccc0 exactthreeIOrequests remain unchanged/unadmitted at last read; no
replay/newgrant/hold from source work. Full goal ACTIVE/INCOMPLETE, standing8/8.


## 2026-10-18 declared custom stream frame cap IN PROGRESS

Active 2f07b21c successor adds registerStreamCmd ?maxPayload with separate str/
args body caps and registration overflow checks; both receive routes enforce
before body allocation. Copy declares producer65500+fileID5 bytes; current tags
=>65535stream/65536fallback. Optional None custom behavior unchanged. Aliased
Transfer.maxInstructionBytes derives from actual queue; no variable custom heap/
workspace or hardRSS claim. Initial20219/1e7491/1 failed/closed because test guard
was below precedingheader, production unchanged. Corrected payload fixture and
fallback negative mutation retains registry but bypasses routing, so each old
hazard reaches its intended allocation guard.

Final controls83415/633315/0/no session: stockRPC24464/tokens24767 andOxRPC25061/
tokens25490 reaped0/groupsabsent/CPU4closed.16RPCnegatives+167tokenchecks9negatives
percompiler allPASS. Current full4buildcontroller20985 LIVE, stock26165/27282 and
OxMake28364 closed0; OxDune pending. Do not claimfinalparentclosedyet. NoEXIO,
SDK/Photo/original/nativecloning or transport. Frozen9d9dccc0 IOrequests unchanged,
3admissionpathsabsent atlastcheck. Future source: explicit client-result lifetime,
custom workspace/baseline; concrete Remote metadata registries (receivers and
streamError retained error values) need finite ownership/quotas before full M6.
Goalactive/incomplete, standing8/8, no automatic newIOgrant/replay.


## 2026-10-18 production stream/fallback body cap qualified

Current source declares maxPayload on custom registerStreamCmd and derives
separate role-specific caps. Copy uses producer65500+fileID5 =>65535stream/
65536fallback bytes, both checked before raw body allocation. Optional no-limit
custom registration unchanged. Constructoroverflow refused before registry
mutation; custom workspace/heap/unknown command metadata are NOT covered.

Actual fullbuilds20985/b37653/0/no session PASS/CLOSED; children26165/27282/28364/
29545 reaped0/groups absent/CPU8closed. All recorded current source/binary hashes
match. Final controls83415/633315/0 closed: stockRPC24464/tokens24767, OxRPC25061/
tokens25490 reaped0/groupsabsent/CPU4closed;16RPCnegativeparticipants +167transfer
checks9mutations/compiler. Initial guard-below-header fixture20219/1e7491/1 kept
failedclosed; corrected fixture only, no production weakening/rerun of any grant.
Evidence tests/qualification/stream-command-input-cap-actual-20261018.json SHA
361ac49f3333b8913d8487728da9ef72efe4e32c44a47986ac4453146225427d. Inventoryv16/framing/readiness updated. No current Unison resources/EXIO.
Next source work: client-result consumption ownership and bounded persistent
RPC metadata (receivers/streamError values), custom workspace/baseline and hard
FD/RSS/platform/completeSOL acceptance stillopen. No current full-goal claim.
Frozen9d9dccc0 exactthreeIOrequests unchanged;3admissionpaths absent atlastcheck,
no dispatch/replay or fabricated Photo hold. Standing8/8/system2 unchanged.

## 2026-10-18 pending RPC waiter admission — controls closed, full builds active

Uncommitted successor in implementation/decoded-input-accounting adds endpoint-local
rpcpendingreplyslots (default256, maximum65536). It refuses a full registry before
request marshaling and checks again before insertion; duplicate IDs cannot replace
an existing waiter. This bounds pending entries only, not decoded client results,
outbound bytes, full heap or RSS.

Actual grouped stock/Ox control owner72498/7af596/exit0/no session collected.
All ten family controllers in /private/tmp/unison-pending-reply-{stock,ox}-
{framing,body,decoded,stream,pending}-20261018-004 report passed, child0, tokensclosed.
The union covers19 negative participants/compiler plus the positive suite.
Earlier fixture failures001/002 and incomplete Ox003 at the60s wrapper limit are
preserved; grouped004 changes test scheduling, not production limits.

Full stock/Ox Make+Dune/selftest controller is ACTUALLY LIVE session12717, initial
chunk285bcd. Sequential max2compiler jobs under Unison00..07 only; no EXIO/SDK.
Do not restart it or infer terminal from files/process absence. Poll actual handle.
Final evidence/commit and inventory successor still pending these checks.

## 2026-10-18 pending RPC waiter limit qualified

Actual full build controller12717/006f9f/exit0/no session collected: stock/Ox
Make+Dune/selftests all0; all recorded input/compiler/executable hashes match.
Grouped controls72498/7af596/0/no session: ten childgroups reaped0/othersabsent,
CPU4closed,19 designated negatives/compiler plus positive fixtures. CPU8closed
after every build; no Unison EXIO/SDK/Photo payload owner.

Evidence tests/qualification/rpc-pending-reply-slots-actual-20261018.json
67061B SHA4656b34fbe4292099dfa3c1a4d53758a61bf9ce3d6964ca539341e36be8c1d0f.
Inventoryv17 and doc/rpc-pending-waiters.md retain exact limits: pending entries
only, no client result/error/outbound/fullheap/RSS guarantee. All earlier failed
fixtures and incomplete Ox003 are preserved; no grants replayed.
Next: explicit decoded client-result lifetime API/caller migration and stream
error retention. Frozen9d9dccc0 IO requests remain separate; no final SOL claim.

## 2026-10-18 scoped decoded client-result successor — qualification active

Uncommitted source adds registerBoundedServerCmdWithResultScope and independent
rpcdecodedresultbudget/elements/slots, explicit value roots through actual client
consumer settlement, known partial-debit cleanup and recognized-uncertainty
retention. Four semantic bounded callers migrated without wire change. Converted
reports/plans and legacy result escapes remain separately owned/open; no complete
heap/RSS or full SOL claim. Design: doc/rpc-scoped-client-results.md.

Actual focused controls6659/bf199a/0 (positive stock) and28657/900e33/0 (stock+Ox,
five designated negatives/compiler) closed/reaped/groupsabsent/CPU4closed. Small
preference-help wording clarified afterward, so final source regression union
still required; no earlier hashes silently treated as unchanged.

Full stock/Ox Make+Dune/selftest controller ACTUALLY STARTED session37362, initial
chunk11b919, max2compiler jobs inside Unison00..07; do not duplicate it. Final
build terminal, complete grouped regression, evidence/commit remain pending.
No EXIO/SDK/Photo payload owner. Three frozen candidate admission files absent
at pre-build check; exact old execution sources/requests remain untouched.

Scoped-result full builds ACTUALLY CLOSED: controller37362/e35c53/exit0/no
session, all four stock/Ox Make+Dune+selftests passed, each CPU8closed. Final
current-source regression controller ACTUALLY STARTED session57811/initialf3d212:
six finite groups/compiler (framing/body/decoded/stream/pending/result), expected
24 designated negatives/compiler. Source/executable rehash+evidence stillpending.
Do not repeat that live controller. No EXIO/SDK/Photo payload owner.

Regression controller57811/384644/exit1/no session CLOSED: stockframing passed,
stockbody failed at its old registered-classifier mutant because the newly
inserted result uncertainty fixture ran before that mutant's intended body
witness. Both containedgroups reaped/tokensclosed; no resourceunknown. Preserved
003 evidence. Only test composition reordered body-retained before result-input;
production unchanged. Fresh final controller71721/initial8500b0 ACTUALLY LIVE,
same six groups/compiler in namespaceunison-result-scope-*-*-20261018-004.
Do not poll/repeat dead57811. Full four production builds remain valid; their
recorded test-runner hash differs by this explicit fixture-only reordering, so
no all-input-unchanged claim. Final source/production/binary checks pending.

## 2026-10-18 scoped client-result API and semantic migrations qualified

Actual final controller71721/b151aa/exit0/no session:12groups reaped0/othersabsent/
CPU4closed;24 designated negatives/compiler and all positive fixtures passed.
Fullbuild37362/e35c53/0 actualclosed: four stock/Ox Make+Dune+selftests, all580
recorded inputs/compiler/binary hashes verified current; eachCPU8closed.
Correction to earlier test-delta note: Python fixture runner is NOT in those580
recorded build inputs, so all recorded inputs DO match; final control evidence
separately pins current runner+MLfixtures. No build repetition needed.

Evidence tests/qualification/rpc-scoped-client-results-actual-20261018.json
86775B SHAf7d149929bef0b36d4c11cf523c7396009e457751c67fbaa4c49e77fcd6b3cde.
Additive registerBoundedServerCmdWithResultScope independent resultlane defaults
256MiB/1048576elements/256owners (max65536); explicit roots through actualconsumer
settlement/knownpartialcleanup/recognizeduncertaintyretention. Four semantic
bounded callers migrated withoutwirechange. Legacy APIs unchanged; converted
reports/plans/globalescapes remain separate, no heap/RSS/SDK/transport/fullgoal
claim. Inventoryv18 and scoped-result doc current. Earlier focused evidence and
failed fixture-order003 preserved. No Unison owner/CPU/EXIO resources held.
Next substantive source gaps: retained streamError values, legacy clientresult/
converted-object lifetime, outbound/baseline/containment and final SOL acceptance.
Frozen9d9dccc0 exact IOrequests remain separate; no replay or automatic grant.

## 2026-10-18 retained stream error successor — controls active

Uncommitted source adds streamerror count/selected-known-string limits spanning
stored entries and actual queued ping borrowers; reset skips borrowed entries,
known settlement releasesonce and recognizeduncertainty retains preparedroot.
Standardexceptionexactcauses/abortbehavior preserved; customunknownpayloadexn
propagatesexactearly instead of unboundedpersistent storage. See streamerror doc.

Failedclosed attempts preserved: stock001/d33fe2/1 (test passed Umarshalcodec
to customstream API instead of marshalingFunctions); controller31925/17d8a2/1
stock002 caught Failure-string abort compatibility omission; production corrected
to account standard known exception fields. Controller75616/7ba312/1 stock003
passed positive+6mutants, final duplicateborrow mutant needed actual Lwt result
observation rather than syncignore; fixture corrected only. Each child reaped/
groupabsent/CPU4closed, no unknownnative/EXIO/SDK/Photo payload owner.

Current controller11022/initial5bc20b is ACTUALLY LIVE stock+Ox sevenmutants; stock
passed. Do not repeat. Full four current builds/finalallfamily regressions and
evidence/commit remain pending; prior d5f092d2 committed+forkpushed unchanged.

Stream-error focused controller11022/13fef4/exit0/no session ACTUALLY CLOSED:
stock49804/Ox49949 reaped0/groupsabsent/CPU4closed, seven designated mutants each.
Final full-build+regression controller ACTUALLY STARTED session70244, initial
chunk51376f. It sequentially runs four Make/Dune+selftests underUnison8 then
seven groups/compiler underUnison4, namespacesunison-stream-errors-*-20261018-001
(builds) andunison-stream-errors-*-*-20261018-005(controls), expected31 negatives/
compiler. Do NOT duplicate active70244. No EXIO/SDK/Photo payload operations.

The old processStream uncertainty-branch omission mutant became redundant because
new unknown-payload fallback rethrows the same uncertain exception. Replaced it
with explicit uncertainty-to-abort mutation; designated raw-body loss witness
unchanged. Final source/tests pinned only after this change. Full builds/results/
sourcechecks/evidence/commit stillpending. Three frozen Rootadmission paths absent
at dispatch; controller checks between finite jobs and stops ifanyappears.

## 2026-10-18 retained stream errors qualified — no resources held

Actual combined controller70244/3c4cb2/exit0/no session collected. All four stock/
Ox Make+Dune+selftests passed; all581 recorded inputs/compiler/binary hashes match.
Fourteen final groups passed positive suites+31 designated negatives/compiler;
each child reaped0/othersabsent and CPU8or4closed. No EXIO/SDK/Photo payload owner.

Evidence tests/qualification/rpc-stream-error-ownership-actual-20261018.json
110931B SHA6938cb4c1a6eb029b3291173c50a1e465c990f43a2bc11911022ea541c039be7.
Inventoryv19 and stream-error doc current. Default256owners+8MiB known string
fields include stored entries and actual ping borrowers; exact standard exception
causes/abort behavior preserved; custom unknown payloads propagate exactearly.
Disconnect only releases unborrowedtableentries; typeduncertainty roots charges.
Earlier001/002/003 failures and004focusedruns preserved, final005coverscurrent
source+stronger direct uncertainty-to-abort mutation. No fullheap/RSS claim.

Next priority: source-pinned mixed upstream/retainedfork and generated-property
IO qualification for this CURRENT successor. Old frozen9d9dccc0/v2requests stay
unchanged historicalproposals, not current source qualification. Fresh request/
workspace/pins/Root scheduling required before payload; no automaticSDK/native
backend grant. Other legacy result/conversion/outbound/baseline/containment and
complete SOL acceptance remain open; goal active/not blocked. Standing8/8.

## 2026-10-18 CURRENT456776d8 fresh IO requests V3 prepared, NOT admitted

Frozen execution candidate now implementation/decoded-input-accounting source
456776d8 (fork pushed); no execution-source edits while V3 under review.
Index doc/sol-current-requalification-requests-v3.json3170B
SHA2e9adb6ba0a9a71a65312641443f3eef46ecc95404002a9cb3ce36f47bf801b0.
Metadata preflight c619a0/0: both exact checked_plan400pins; property exact
manual.command/checked_build+43execution329production+in-memory IO admission check
passed. Canonical manifest metadata read real; sentinel admission read only was
mocked, no locks/liveadmission/worker/transport/SDK/Photo payload created.

Upstream request doc/sol-current-upstream-request-v3.json2262B
SHA63e3a22a3cceb3cb72f4801d14e0b773f7393978ebdf988e8025467edc63e783,
plan092af1c8/62351B; workspace/private/tmp/u-mp-595b8390, admission
/private/tmp/unison-current-upstream-admission-595b8390.json.
Retainedfork request doc/sol-current-retained-fork-request-v3.json2287B
SHA88004d1a9dc5e8a1b13c92b27c66eeefb576eed8fdb7a25a85229bb5383aa1b0,
plan3a734566/66068B; workspace/private/tmp/u-mp-585e3781, admission
/private/tmp/unison-current-retained-fork-admission-585e3781.json.
Properties request doc/sol-current-properties-request-v3.json44806B
SHA57d0d7d150d537d4afc216f42daff169fccf1d2f4833135f2443962d946d6e85;
workspace/private/tmp/u-current-properties-6d3b576a, admission
/private/tmp/unison-current-properties-admission-6d3b576a.json.
Recommended serial upstream thenretainedfork thenproperties, each separatefresh
RootexactSHA/deadline. Existing12CLI/12CLI/54CLI limits preserved; Unison00..07
+EXglobal only, noSDK/Adobe/camera/Photo/nativeUI/compiler/quietperformance/18grant.

All3oldV2admission+workspace paths absent at fresh metadata observation. Old
unadmitted SOURCE PROPOSALS now superseded/donotschedule via
doc/sol-resource-v2-source-proposals-superseded-20261018.json2306B
SHAd41f5314b5a5f2e334c959c6b33a28341ee28f4058b31a4d0c205624570b7920.
Originalbytespreserved, no admissioncancel/rewrite or inventedownerterminal.
Two metadata-only prep refusals preserved:7947ad/1 (SHAplaceholder invalid for
command construction),89c629/1 (mock wrong importmodule); corrected preflight
uses valid inertSHA and only mocks sentinel at definingmodule. Neither dispatched
anything or acquiredpool. Do not call these runtime failures or Rootrefusals.
Goalactive, legacy result/conversion/outbound/baseline/containment remain work.

Fresh V3 requests actually queued to Photo Root:01a15029-3b55-73b1-83ec-4eaa48f358cc, tool e9c57e/0. Durable doc/sol-current-requalification-v3-QUEUED.json. No runtimegrant or hold. Metadata commit02259bdd forkpushed; execution source456776d8 unchanged.

## 2026-10-18 outbound successor source work isolated

CURRENT SOURCE DEVELOPMENT worktree /Users/alexy/src/unison-outbound-accounting-20261018,
branch implementation/outbound-accounting, starts fromf6472dc2. No source edits
in frozen /Users/alexy/src/unison-decoded-input-20261018 execution closure while
V3requests under review. Its execution456776d8/builds and metadataf647 stayvalid.
No current ownedprocess/CPU/EXIO lease. Source audit/design only in
doc/rpc-outbound-ownership-design.md: queue retention needs independent finite
credits; producer serialization must reserve BEFORE allocating, separately;
logical slice bytes != backing/heap/RSS. Immediate performOutput can drain other
queued actions, so its returned promise is not earliest own-action settlement.
Need distinct active/queued/drop/uncertain lifetimes and urgent control lane.

V3 Root grants remain separate required runtime scheduling. Check exact three
paths from frozen doc/sol-current-requalification-requests-v3.json; run any valid
one-use command from FROZEN cwd/argv, never this mutable successor. Rootqueue
01a15029-3b55-73b1-83ec-4eaa48f358cc; no automatic payload or SDK grant.

## 2026-10-18 concrete outbound slice bug found and fixed — controls active

ACTIVEworktree /Users/alexy/src/unison-outbound-accounting-20261018, branch
implementation/outbound-accounting, uncommitted production fix. Source original
fillBuffer2 takes absolute end but fillBuffer passes count. Original7B golden
(__abc__,2,3) ACTUALLY rejected at designated witness: controller63737/1cf438/0
(expected-rejection), child59647reaped1/groupabsent/CPU4closed, workspace
/private/tmp/unison-output-slice-old-stock-20261018-001 preserved. Same code is
in genuine upstream8772; no upstream patch/submission prepared (fork only).

V3 source proposals DEFERRED/doNOTdispatch viaRootqueue01a1502e-bad1-7f60-932a-e5850af12d94,
queue tool36f0f7/0; durable doc/sol-current-v3-source-deferral-output-slices-20261018.json
pins frozenindex/observations without rewriting its bytes. No RootIOhold asked.
Any crossed V3grant must be refused unstarted; no known-bug run. Fresh fixed
source/request/workspaces needed after qualification.

Fix converts count to checked end, validates complete slice list before first
copy AND each dump before queuing, checked cumulative counts, zero-length noflush.
No outbound resource budget yet implemented/claimed; serialization preallocation,
queued ownership/urgent allowance/backing retention remain next.

First fixed controller80271/997cce/exit1 closed child60214reaped1/tokensclosed: main
positive program passed incl actual privatepipe across3bufferboundaries, but
whole-list mutant surfaced failedLwt promise rather than sync exception. Fixture
now actually awaits that failedwork before checking earlierprefix unchanged;
production unchanged. Fresh focused controller41645/initial8e6979 ACTUALLY LIVE,
stock thenOx, namespaceunison-output-slices-{stock,ox}-20261018-002,8mutants/compiler.
Do not repeat active41645. Full4builds+39negativeunion stillpending, no runtime
transport/SDK/Photo payload/EXIO or fullgoalclaim. Existing main/frozenhandoffs
remain historical; this successor carries authoritative active source state.

Output-slice focused controller41645/18e0dd/exit0/no session ACTUALLY CLOSED:
stock60531/Ox60701 reaped0/groupsabsent/CPU4closed,8mutants/compiler. Stronger
actual production queue+maybeFlush coverage then added, with ledger of returned
flush promises (no state inference or duplicate flushing). Current controller
89352/d9dbb6/exit0/no session ACTUALLY CLOSED: stock61256/Ox61418 reaped0/groups
absent/CPU4closed,8mutants each plus exact49161B pipe output for directfill/normal/
idle/urgent, each across3bufferboundaries. Before cleanup, actual writer/reader
and every returned production maybeFlush promise are awaited. No copied/mocked
write primitive. Pure range/overflow/full-empty/invalid-list prequeue controls pass.

ACTUAL fullbuild+regression controller STARTED session24512, initial5b0b5b, nowlive.
Four stock/Ox Make+Dune+selftests sequentialUnison8/max2compiler jobs, then8groups
percompiler sequentialUnison4 (39designated negatives expected). Buildnamespace
/private/tmp/unison-output-slices-{stock,ox}-{check,dune-check}-20261018-001;
finalcontrols/private/tmp/unison-output-slices-{stock,ox}-{framing,body,decoded,stream,pending,result,errors,outbound}-20261018-004.
Do not duplicate24512 or inferterminal from resultfiles/ps. Fullhash verification,
finalevidence/commit and fixed-sourcefresh IO requests stillpending. No SDK/Adobe/
Photo payload/EXIO used; ownCPUonly. V3 requests remain SOURCEDEFERRED (queue
01a1502e-bad1) regardless of anycrossedgrant; no knownbugsource dispatch/replay.

## 2026-10-18 exact outbound slice fix QUALIFIED — resources closed

ACTUAL combined controller24512/2a3485/exit0/no session. All four stock/Ox
Make+Dune+selftests and16current controlgroups passed;39 designated negatives/
compiler. Each build/control child reaped0/othersabsent/CPU8or4closed. All582
recorded inputs/compiler/binary hashes plus final tested-source hashes match.
No current owner/EXIO/SDK/Photo payload or nativeUI use.

Evidence tests/qualification/rpc-output-slices-actual-20261018.json133778B
SHAbf2cc59f8d820776444d33b248c8476e63545c25d07dfb2059fa72fd62e82f71.
Original failing7B golden63737/1cf438/0(expected rejection) with child59647/1
+old exact source+generated program hashes preserved; NOT original functionalpass.
Fixed001 observer-fixture failure80271/997cce/1 preserved;002focused41645/18e0dd/0
and strengthened00389352/d9dbb6/0 passed before final004union.
Actual4route privatepipe49,161B comparedexact, 3bufferboundaries, production
maybeFlush returnedpromises captured/awaitedbeforeonce-only independentcleanup.

Count is converted to checked end; whole-list validation happens before anycopy
and dump prequeue; checked cumulative arithmetic; empty slice doesnotforceflush.
This is byte correctness/validation only. Queued-owner/bytes, pre-serialization
allocation, backingstore/heap/RSS accounting remain substantive open work.
Inventoryv20/readiness/outputslice doc updated. V3source requests explicitly
deferred viaqueue01a1502e-bad1; preserve oldfiles and refuse anycrossedgrant
unstarted. Next fixed-source V4 requests need newpins/workspaces/RootIOreview,
never dispatch oldknownbugsource. Goalactive/fullscopeunchanged.

## 2026-10-18 FIXED72560ca4 fresh V4 IO requests prepared NOT admitted

Freeze /Users/alexy/src/unison-outbound-accounting-20261018 execution closure at
72560ca4 while V4underreview; newsourcework must use a successorworktree. Actual
metadata preflight8eafb1/0: both checked_plan400pins and property checked_build/
manual.command+43execution329production+in-memory checked_io_request passed.
No admission/locks/child/payload/SDK/Photo call created. Finalqualified source
72560ca4 forkpushed; no current owner/CPU/IO resources held.

Index doc/sol-fixed-requalification-requests-v4.json2983B
SHAbf54dd3e064d0a27bbc0a31df50d2c5b18223cec9f17e43a76571c79f230171c.
Upstream request doc/sol-fixed-upstream-request-v4.json2303B
SHA2da25af93ad8b3b88cade5fdce9e3b9eb47b6653792262417f0154d25cfa1c06;
plan4d1cec93/64973B, workspace/private/tmp/u-mp-8948b228, admission
/private/tmp/unison-fixed-upstream-admission-8948b228.json.
Retainedfork request doc/sol-fixed-retained-fork-request-v4.json2328B
SHAb5372c5a4432771708902d6065c4b49399a65c353fc871fd0ebd7eb851399160;
planf02840ef/68762B, workspace/private/tmp/u-mp-4bc2f1b7, admission
/private/tmp/unison-fixed-retained-fork-admission-4bc2f1b7.json.
Properties request doc/sol-fixed-properties-request-v4.json45274B
SHA6c0a27727376d162d500e80b0fb7d62af265bab4392d5a355e5d35d008e8c942;
workspace/private/tmp/u-fixed-properties-a446dbf4, admission
/private/tmp/unison-fixed-properties-admission-a446dbf4.json.

All3V4admission/workspace absent atfreshcheck; recommendedserial upstream then
retainedfork thenproperties, each separateexactfreshRootgrant/deadline. Limits
unchanged12/12/54CLI, Unison00..07+existingEXglobal only, noSDK/Adobe/camera/Photo/
UI/compiler/performance/retry/automatic successor/18borrow. V3 sourceproposals
remain deferredqueue01a1502e-bad1, originalbytesunchanged; doNOTdispatch crossed
V3grant or oldV2. Only fresh fixedV4 can be scheduled. EntireSOLgoal stillactive.

Fixed V4 requests ACTUALLY queued:01a15045-55f3-7762-9e16-57271a54d029, queue tool9f063d/0; durable doc/sol-fixed-requalification-v4-QUEUED.json. Source72560ca4, metadata4d480dc3. No grant/dispatch/hold; source frozen while under review. Next source development must use a successor worktree.

## 2026-10-18 output-queue ownership successor isolated

ACTIVE SOURCE DEVELOPMENT worktree /Users/alexy/src/unison-output-queue-20261018,
branch implementation/output-queue-ownership, starts18c9b822. Frozen V4 runtime
candidate /Users/alexy/src/unison-outbound-accounting-20261018 remains source
72560ca4, metadata18c9b822, executionpins unchanged. No current ownedjob/tokens/
EXIO/SDK/Photo operation. Git push of frozenmetadata collected39221/515206/0.

Next source work follows doc/rpc-outbound-ownership-design.md: independent queued
logical-byte/owner admission (urgent lane separate), actual active vs queued/drop
settlement, explicit roots on uncertainty; then producer pre-serialization
allocation ownership. Logical slice bytes alone are NOT backing storage or RSS.
Do not mutate frozen source while V4 under Rootreview; exact source/grants live in
frozen doc/sol-fixed-requalification-requests-v4.json. Any admitted one-use command
must run from frozen argv/cwd afterfreshpins/deadline/unused checks, never this
mutable successor. V3deferred/V2superseded remain unstarted byus; no replay.

Source audit follow-up to verify (not yet a tested finding): processStream's
exception-filter body_unresolved invokes registered predicates before outer
RetainedOwnership.guard. A throwing predicate might replace original failure
before outer classification; check original+classifier cause/identity retention
with an original controlled example before claiming coverage. Current scoped
result/argument guards directly classify inside RetainedOwnership; don't assume
that proves every stream/filter path. Preserve supported pure-classifier contract.
Goal remainsfullSOL active; no fullpipeline/production/performance claim.

## 2026-10-18 selected output queue ownership implemented — final validation LIVE

ACTIVE /Users/alexy/src/unison-output-queue-20261018 branchimplementation/output-queue-ownership.
Uncommitted normal/idle selectedbytes512MiB/parts65536/slots256 and independent
urgent65536B/parts2048/slots256 (maxslots65536); endpointlocal. Actual consumer
settlement clearsowner payload and releasescredit; unrelated later draining
cannotkeep originalchunklist through queueclosure. Known queuedcancel releases,
activeconsumer remainscharged untilactualsettlement; typed/classifieruncertainty
roots value+charges. Finalreserve rechecks afterpreparation; lostadmissionrace
keeps priorqueuedwork intact; unstarted schedulerfailure failsqueue ratherthan
stalling unavailablequeue. Known unadmittedcleanup clears payload withoutdebit.

Not pre-serialization allocation/backing/calleralias/baseline/allheap/RSS bounds.
Producer mustawait actualreturnedoperationbeforereuse. See rpc-output-queue-ownership.md.
Moved existing bodyclassifier definitions earlier (sameadditiveAPI) for dumpguard.
Generic scheduler/flow-control fixedactions remain separate baseline.

Controls history (all CPU4groupsclosed, noEXIO/SDK/Photo payload):
66824/3f8312/0 positive stock child73748passed. Direct620827/1 child74385failed
fixture syntax(witnesswith); fixed testonly.58923/79ff42/1 stock74557passed, Ox74728
weak-root assertionfailed because caller-local liveness differed. Non-inlined
returning factory keeps sameweakassertion;25528/cce855/0 children75351/75518passed
8mutants each, productionunchanged. Recheckadded:11451/fdfbc1/0 children76235/76419
passed9, then testhelper changed toaccept sync OR alreadyfailedpromise refusal;
whole-policy mutants now omit BOTH checks (actualovercommit), not just stricterror
channel. Finalfocused45971/c5c7db/0 children76853/77040passed9 each.

ACTUAL finalfullbuild+regression controller NOWLIVE session2868 initial83714a.
Fourstock/Ox Make+Dune+selftests underUnison8/max2compilerjobs, then9groups/compiler
underUnison4 expected48negativeparticipants. Buildnamespaces
/private/tmp/unison-output-owners-{stock,ox}-{check,dune-check}-20261018-001;
controls/private/tmp/unison-output-owners-{stock,ox}-{framing,body,decoded,stream,pending,result,errors,outbound,queue}-20261018-007.
Do not duplicate2868; collectactualterminal viahandle, never inferfromfiles/ps.
Finalsource inactiveknowncleanup changedafterfocused006, so finalfullsuite is
requiredbeforeevidence/commit. Controller checks frozenV4admissionpaths before
each sourcejob; ifanyarrives itstops afterpreviousactualjobclosure forreconcile.

Frozen V4candidate remains /Users/alexy/src/unison-outbound-accounting-20261018
source72560ca4 metadata18c9b822; never altered. Rootqueue01a15045-55f3 pending.
All3V4admission/workspacepaths absent atprebuildcheckb97bd7. No payload dispatch,
SDKgrant, IOhold, 18borrow or finalSOLclaim. Further sourcework here only.

Final output-owner controller2868 stillACTUALLY LIVE (latest57d971). Allfour
stock/Ox Make+Dune+selftests reported0/tokensclosed; finalregression began and
stockframing/body groups reported0. Fullparentterminal and all48negative/compiler
union remainpending. No sourcechanges afterlaunch. Poll2868, doNOTduplicate.

## 2026-10-18 selected output queue ownership QUALIFIED

ACTUAL combined controller2868/d911f0/exit0/no session collected. Fourstock/Ox
Make+Dune+selftests and18finalgroups passed;48 designated negatives/compiler.
All583 recorded inputs/compiler/binary hashes and finaltested-source hashes
match. Each build/control child reaped0/groupsabsent/CPU8or4closed. No current
owner/CPU/EXIO/SDK/Photo payload/nativeUI resource.

Evidence tests/qualification/rpc-output-queue-owners-actual-20261018.json182551B
SHAe1ac4f0ea937fb4e5a6407ecfe4652d6a14e647af40065c6d7f9863cdbe783f1.
Normal/idle512MiB/65536parts/256owners; urgent65536B/2048parts/256owners; maxslots
65536. Measuresbeforequeue andauthoritativelyrechecks afterpreparation. Known
unstartedreservationrefusal doesn'tpoisonpriorqueue; schedulerfailurefails
queueinstead ofstalling unavailable. Actualconsume clearslist/credits before
unrelateddrain; droppedqueuedworksettlesknownfailure, activeworknotrevokedby
queuefailure. Typed/classifieruncertainty roots exactpayload+credits.

Preserved001positive66824/3f8312/0;002syntax620827/1;00358923/79ff42/1 (stockpassed,
Oxcaller-localweaklivenessfailed);00425528/cce855/0 with returningnoninlinefactory
andunchangedweakassertion;00511451/fdfbc1/0 afterrecheck;00645971/c5c7db/0 accepts
syncORfailedpromise and whole-policy mutants removebothchecks.007finalcurrent
source includes inactiveknowncleanupclearpayload; no earlierhash falselyreused.

Inventoryv21/readiness/queueownershipdoc updated. Not encoded allocation BEFORE
serialization, backing/calleraliases/baseline/allheap/RSS or actualtransport/full
SOL acceptance. Existing Umarshal sizing pass itself allocates payload copies;
nextproducer scope must addressthat, notjust reserveaftermeasurement.

FrozenV4 /Users/alexy/src/unison-outbound-accounting-20261018 source72560ca4+
metadata18c9b822 unchanged; Rootqueue01a15045-55f3 and exact3paths in index remain
separate. Checkactualfreshgrants beforeoptionalnewwork; no V3/V2replay. Next
sourcework cancontinue butmustnotmutatefrozenRootclosure. Goalactivefullscope.

Qualified source4c4f305d forkpush issued; Photo progress notice ACTUALLY queued01a1506a-ed6d-7b32-933b-783fec05790e (tool50ae53/0). FrozenV4 not repinned; no newgrant requested. Last3V4admission/workspace read allabsent.

## 2026-10-18 encoder slice prerequisite (source successor, not frozen V4)

Previous status turn was no progress; resumed source work. marshal_to_bytearray
now validates source slices on BOTH passes and checks payload+header overflow
before result allocation; second-pass destination check uses subtraction rather
than overflow-prone addition. Original tiny private-codec controls cover six
invalid slice forms, second-pass size drift, and valid nonzero slice bytes.
Actual controller98620/50f495/exit0/no session; stock and Ox controls under
Unison4 each closed child0/groupabsence/CPUclosed. Receipts:
/private/tmp/unison-encoder-slice-{stock,ox}-20261018-001/SHARED-CLOSED.json.
No EXIO/Photo/SDK/transport. New tests/umarshal_accounting/encoder_slices.py.
This is a narrow unsafe-copy prerequisite; sizing still allocates payload copies,
producer reservation/output-context design remains NEXT, no allocation/RSS claim.
Full builds/regressions and guarded omission participants for this new change
remain pending; do not promote into frozen V4. V4 admissions were absent at this
turn's fresh metadata check. Existing source4c4f qualification remains historical
and does NOT qualify these new edits. Goal active, no resource held.


## 2026-10-18 builtin encoder measuring sink implemented (not fully qualified)

Previous turn made source/test progress. Internal output context now separates
measure-only count from actual byte sink. char/int32/int64/string/bytearray
builtin sizing avoids Bytes.create/of_string payload buffers; compound codecs
propagate context unchanged. This is NOT allocation-free whole execution:
closures/boxing/traversal/conversion callbacks remain, and actual serialization
still allocates scratch/payload copies pending producer reservation integration.
Public abstract codec API and valid wire representation unchanged by design.
Bounds prerequisite from previous turn retained on both measurement fallback
and actual copy paths, cumulative header overflow checked before result allocate.

Original tests/umarshal_accounting/encoder_slices.py wraps Bytes to reject
builtin sizing allocations, checks composite wire parity +8 malformed/valid
slice/size cases, compiles against actual mli, and requires omission participant
to fail with sizing-allocated-bytes witness. Actual004 controller72412/3685ad/0
(no session), stock/Ox closures under /private/tmp/unison-encoder-sizing-{stock,ox}-20261018-004.
Preserved002 controllerb8ee6e/1: fixture omitted prod3 conversion args, no prod
change needed;00347105/15d96c/0 passed before interface/mutant additions.
Existing decoder accounting78controls+2 omission/order participants also passed
both compilers controller62353/d08ecc/0, namespaces
/private/tmp/unison-encoder-sizing-decode-{stock,ox}-20261018-001.
All contained children reaped0/groups absent/Unison4closed; no EXIO acquired.
Evidence tests/qualification/umarshal-encoder-sizing-directed-20261018.json pins
current source/test/mli+four SHARED-CLOSED receipts. Full Make/Dune/selftest and
RPC private-source controls pending BEFORE promotion/commit. Next: reservation
BEFORE result/scratch allocation, partial buffer publish/root lifetime, then
producer integration. Frozen V4 unchanged; no payload admission/dispatch.


## 2026-10-18 builtin encoder allocation hook qualified; RPC integration next

Current source adds internal measure/write output context and additive
Umarshal.marshal_to_bytearray_accounted. Measures builtin wire lengths without
payload scratch, validates slices on both passes/checked header sum, reserves
selected cumulative result/header/builtin scratch BEFORE allocation, publishes
partial result BEFORE header copy/secondpass. Caller retains claims/root on all
failure and releases after actual settlement; no library refund/retry. Local
budget then external admission; original callback exceptions preserved. This
is NOT conversion/closure/boxing/traversal/depth/allheap/RSS accounting, nor RPC
producer integration. Bytearray scratch conservatively fullpayload charged.

Actual final directed controller53369/e7e1b3/0/no session: stock/Ox positives,
measurement-omitted and scratch-reservation-omitted participants correctly fail;
9 slice/overflow/drift/valid checks plus sizing/wireparity/local+aggregate refusal/
partialresult/callbackfailure ordering. Prior17042/3ecdf0/0 also passed before
explicit max_int headeroverflow check added in final002. Preserve earlier
sizing002 fixture failure,003/004 and accounted001 scope; no raw overwrite.

Actual full controller74532/b602f2/0/no session, four stock/Ox Make+Dune+selftests
PASS; all583 recorded source inputs plus compiler/binary hashes match current.
Focused regressions99178/c969b8/0/no session: decoder78+2 omission/order controls,
outbound8 and queue9 negatives/compiler plus positives PASS. All contained
children0/groupsabsent/CPU4or8closed. No EXIO/SDK/Photo/nativeUI or live job.
Evidence tests/qualification/umarshal-encoder-accounted-actual-20261018.json
278514B SHA0eca648159038ad66898b98b8f53cec46611d320ebf94bf696c13b2868b55b81;
remaining inventoryv22. Earlier sizing-directed receipt is historical prehook,
not falsely repinned. Goal remains full SOL active/incomplete.

NEXT: explicit producer message owner/slot before serialization, retain published
partial arrays+charges through actual dump consumer and recognized uncertainty.
Stateless marshalFunction/curried server replies must not lose that debit. Scope
synchronous encoder context ONLY over builder (never asynchronous serverwork),
or prefer explicit envelope; preserve request/reply/stream/urgent cancellation
and queued actual-consumer lifetime. Add directed lifetime tests, then qualify.
Frozen V4 candidate source72560ca4/metadata18c9b822 unchanged; all3 admissionpaths
freshly absent842688. No IO dispatch/Rootgrant inferred; old V3/V2 deferred.


Latest source successor c48f92eb in /Users/alexy/src/unison-output-queue-20261018
adds qualified measuring/accounted builtin encoder hooks (NOT RPC producer owner
integration). Four stock/Ox Make+Dune+selftests plus directed/accounting/output
regressions closed; actual build74532/b602f2/0, regression99178/c969b8/0, final
encoder53369/e7e1b3/0. Evidence0eca648159038ad66898b98b8f53cec46611d320ebf94bf696c13b2868b55b81.
Source-only Photo notice queued01a1507c-83e7-76f0-a877-269e2fb3fc1e/c0302f0.
Frozen V4source72560ca4/metadata18c9b822 unchanged; last3admissions absent.
Next actual work is explicit RPC producer partial-buffer/charge owner through
actual queue consumption, then whole-goal remaining acceptance. No live jobs or
IO/CPU holds. An erroneous push to origin was rejected361691/128 (403), no
upstream change; actual fork remote is querygraph/unison. Use `git push fork`,
NEVER origin, for these fork-only branches.

## 2026-10-18 RPC producer integration source + initial controls

Previous turn was progress (c48f92eb qualified additive encoder hook). New source
in this worktree now wraps standard command request/reply/exception and stream
builders in with_produced_output. Separate normal/idle512MiB/256slots/65536roots,
urgent65536bytes/256slots/2048roots; typed original uncertainty/classifier carrier
prepared before slot admission; current encoder context restored synchronously,
never left installed over server async work. marshalV1 prepares root/link before
accounted encoder call; publish is nonallocating store. Charges/root clear at
actual own consumer, not unrelated later drain; known queued refusal/drop clears
once, unknown retains. Client pending reply registration after successful build
retained, known failure audits actual registered waiter only. Other raw/string
send/custom/caller/tag/ID/connection/backing/heap/RSS remain outside scope.
See doc/rpc-producer-ownership.md for exact policy and integration boundary.

Initial stock001 controller43412/821d02/1 preserved: positive and unaccounted
participant passed; omitted-context mutant hit earlier inactive-owner guard
rather than expected later assertion. Test witness corrected to actual guard,
production unchanged. Added actual own-consumer/later-drain control + omission.
Focused002 actual controller62483/5049e9/0/no session; both stock/Ox positives and
4omissions PASS, children reaped0/groupsabsent/CPU4closed. Synthetic typed unknown
fixtures acquire no actual Directory FD; selected roots persist to processexit.

CURRENT fullbuild controller9872 initial329149 ACTUALLY LIVE (225924), stock
Make+selftests passed/closed; remaining stockDune/OxMake/OxDune in sequence under
Unison8/max2compilerjobs. Do not duplicate, collect actualterminal via handle.
Source frozen after launch; after fullbuild run all10old/new negative families
per compiler against current snapshots, each separateCPU4group <=60s. Full source
qualification NOT yet claimed. Existing frozenV4src72560/metadata18c9b822 unchanged.
Fresh3grantpaths allabsent1e16ee; status request queued01a15082-f049/34ee980.
Controller checks admissions before each optionalbuild; no EXIO/SDK/Photo/native
resource held. Goal fullscope active. Forkpush c48f92eb actual14000/2d806f/0.


RPC producer fullbuild controller9872/4e7e5a/0/no session ACTUALLY CLOSED:
stock/Ox Make+Dune+selftests allPASS, 584input/compiler/binary hashes matched
013cae before later test-only correction. Production sources unchanged.
Regression003 controller73404/c9e9f1/1: stockframing/body passed, decoded fixture
needle matched both newproducer and olddecoded guards. Narrowed decoder-only
mutation context, no productionedit. Regression004 controller98802/b0a7fb/1:
stockframing/body/decoded/stream passed; pending-preflight mutant nowreturns
failedLwt instead ofsync raising, fixture onlycaughtsync so earlier cap assertion
fired. Fixed tests/remote_pending_limits.ml to poll returnedpromise aswell.
This one NONPRODUCTION fixture nowdiffers from recorded584 buildinputs; do not
claimall584current. Allproduction/compiler/binary inputs remainexact; final
controls compilecurrent fixture separately. No original reports overwritten.

CURRENT regression controller79448 initial5a0489 ACTUALLY LIVE (4e55bb), stock
remaining6families allpassed; Oxframing/body/decoded/stream/pending/result passed,
errors/outbound/queue/encoder pending. Namespaces
/private/tmp/unison-rpc-encoder-{stock,ox}-{family}-20261018-005, exceptstockfirst4
reused from004 unchangedproduction qualifiedcounterexamples. EachCPU4groupknown
closed before next; no EXIO or Photo activity. CollectACTUALterminal; no restart.
After success evidence mustexplicitlypin both testvariants and the single
nonproduction584input discrepancy, not infer whole-treebyteidentity. All3RootV4
admissions stillabsent df28cc. No fullproducerqualificationclaim untilterminal.


## 2026-10-18 producer inactive-classifier correction; FINAL CONTROLLER LIVE

Initial complete RPC union actual79448/3fa481/0/no session passed all20group
union (stockfirst4from004, rest005) against pre-correction production. Current
production was then audited for failed pre-admission ownership. Original tiny
counterexample actual24221/2e9399/0 wrapper (child1 expected) proves a throwing
classifier changed no-slot-acquired refusal into uncharged retained pending.
Namespace /private/tmp/unison-rpc-encoder-inactive-original-20261018-001; allCPU4/
groupclosed, no real uncertainFD. Preserve this original failure/evidence.

Source corrected producer Retained guard to classify only while enc_active.
Before admission/after own consumption there is no producer resource to retain.
New finalfixture +5th inactive-classification omission participant actual focused
19779/55c6de/0/no session stock+Ox006 PASS; no RootIO/SDK/Photo work. Prior broad
source qualified results are HISTORICAL pre-this-production-fix, not current.

CURRENT ACTUAL fullfinal controller89158 initial4e2d62 is LIVE. Never duplicate.
Sequence: four stock/Ox Make+Dune+selftests underUnison8/max2compilerjobs, build
namespaces /private/tmp/unison-rpc-encoder-{stock,ox}-{check,dune-check}-20261018-002;
then10families/compiler underCPU4 (framing/body/decoded/stream/pending/result/
errors/outbound/queue/encoder), namespaces
/private/tmp/unison-rpc-encoder-{stock,ox}-{family}-20261018-007.
Expect53negative/compiler (48old+5producer); verify actualunion count/evidence.
Controller freezes remote.ml+runner+encoder/pendingfixture hashes, checks3V4
admissionpaths beforeeachjob, verifies all584buildinputs/compiler/binary hashes
atend. Current pendingfixture is included in NEW snapshots, so earlier single
nonproductioninput variance should not recur. Allsource frozen after launch.
Pollactual89158 until terminal; capture exactchunk/exit/no-session. If failure,
inspect actualrawcause and fix/newnamespace, never replayRootpayload grants.
Only after finalpass write qualification evidence/inventoryv23/readiness+SOL,
commit and push FORK (querygraph, notorigin), send qualifiedsource notice toPhoto.
Do not mergePR13 or alter frozenV4/source72560+metadata18c9b822. Three exactV4
grantpaths absent7ce4d0. No EXIO/SDK/Photo/nativeUI hold; actual CPU build4/8
held only through current sourcejob settlement. Fullgoalactive/incomplete.


## 2026-10-18 stream classifier original-cause correction IN PROGRESS

Previous V5 metadata preparation was progress; original3V5admissionpaths all
absent cc8b6b/a975b7, frozen producer-qualified worktree2e24a0fc remainsunchanged.
Separate /Users/alexy/src/unison-stream-classifier-20261018 branch
implementation/stream-classifier-ownership createdfromb8c67465 (c46373/0).

Concrete original counterexample11298/2f5449/0 wrapper, expectedsourcechild1:
/private/tmp/unison-stream-classifier-original-20261018-001. Rawdiagnostic
stream-classifier id15110 pendingfalse/raw3/3/retaineddelta0/cachedfalse shows
processStream exception-filter classifier replaced original and rawticketreleased.
No actual Directory/nativeFD acquired; allpurecontrol CPU4/groupclosed.

Fix changes processStream classification from exceptionfilter to prepared
RetainedOwnership.guard BEFORE ordinary error caching/abort. Invokes sync stream
handler once, leaves existing preflight outsideguard. Newtests distinguish custom
and knownstandard classified errors, original+classifier cause, exactweakrawbody
root acrossconnectionclose, and ordinaryunregisteredcustom unchanged release.
No decodedcustomarg/workspace/heap/RSS claim. Body-stream oldnegative nowmutates
newguard backtoabort; two newparticipants reintroduce throwingfilter or omit
classification (knownstandard marker would enterordinarycache).

Actualfocused90137/873342/0/no session: stock/Ox body+stream-classifier002 PASS,
5oldbody+2newnegatives/compiler plusallpositive controls. No EXIO/SDK/Photo/UI.
Disclosure ACTUALLY queued01a150a5-3afd-7ef3-978f-4ea0545fb189/e8dc520; does not
silently rewrite V5 or grant anypayload. OrdinarygeneratedV5 wire/propertyscope
is distinct from unqualifiedclassifierfault boundary; Root mustreconcile review.

CURRENT fullfinal controller99377 initialc97b58 ACTUALLY LIVE (9d493a); allfour
stock/Ox Make+Dune+selftests passed/closed. Builds
/private/tmp/unison-stream-classifier-{stock,ox}-{check,dune-check}-20261018-001.
Next11families/compiler (old10+stream-classifier), controls
/private/tmp/unison-stream-classifier-{stock,ox}-{family}-20261018-003.
Expected55negative/compiler (53old+2new); verifyactualcounts. Controllerchecks3V5
admissionpaths beforeeachjob and finalallsource/compiler/binary hashes; doNOT
restart. Source frozen afterlaunch. Poll99377 actualterminal; notpsinference.
Watch old stream-error-preflight fixture: sync-only catch mayneed poll for a
failedpromise from intentionallybrokenpreflight. Ifactualfailureconfirms, fix
fixtureonly anddeclareuncompiledtestdifference ifreusingunchangedproduction
builds; don'tfalselyclaimallinputssame or redoCPUworkwithoutcause.

Afterpass writeactualevidence/inventoryv24/readiness/SOL/handoff; no commit/push
ofunqualifiedsourceyet. Then refreshcurrent-sourceIOrequests separately instead
ofmutatingfrozenV5. Remaininggeneric/customstreamarg decodedworkspace/legacy
baseline/platform/resource/transport/performance/fullgoal acceptance open.
Goalactive; ownlive sourcequalification CPU4/8only, no PhotoIOhold.


Stream classifier fullcontroller99377 ACTUAL61baed/exit1/no session: allfour
builds/selftests andstockfirst6families passed, then errors preflight mutant hit
sync-only testcatch (DESIGNATED full stream table ignored). Predictedfixture
channel issue confirmed actuald34924; corrected remote_stream_errors.ml to poll
returnedpromise aswell. PRODUCTION unchanged; preserveallfailedrawlogs.

CURRENT resume72746 initialb2bfb8 ACTUALLY LIVE (de67a9). Stockremaining5families
allpassed; Oxthroughqueue passed, encoder+stream-classifier pending. Uses same
fourqualifiedproduction snapshots, finalcontrols004 (stockfirst6reuse003).
Allfour buildinput tables haveONEdeclared NONPRODUCTION fixture difference
 tests/remote_stream_errors.ml; current probescompileit separately. No false
all585inputsmatch claim; unchangedproduction/compiler/binary can be reused
without gratuitous rebuild. Resume verifies exactlythatdifference atitsend.
Poll72746 ACTUALterminal, no retryofsamejob. No EXIO/SDK/Photo/nativeUI resources.
V5 frozen2e24a0fc source stillunchanged; grants absent7edea3. Finalsource docs
rpc-stream-classifier-ownership.md added; fullqualification stillpending.


## 2026-10-18 stream-classifier current production QUALIFIED

Actualresume72746/c5db4c/exit0/no session collected. FourMake/Dune+selftests all
passed (originalfull99377/61baed/1 stopped atfixture mutation only), finalunion
55negative/compiler across22groups: stockfirst6from003, remainingstock5+allOx11
from004. Allproduction/compiler/binary hashes match; exactly ONE uncompiled
nonproduction tests/remote_stream_errors.ml fixture changed afterbuilds (sync vs
failedpromisecatch), explicitlydeclared andcompiled separately in finalcontrols.
No false all585currentinput claim. Original11298/2f5449/0 counterexample preserved.

Evidence tests/qualification/rpc-stream-classifier-actual-20261018.json527340B
SHA57c11c9133b2b761b8dccc351730cc868e4e2f13830f16eb66be0d01a6adf1b7.
Inventoryv24/readiness/SOL/newstreamdoc current. Allcontainedgroups/reaps/CPU4or8
closed; synthetic memoryretention untilprocessexit, no actualDirectory/nativeFD
uncertainty, no EXIO/SDK/Photo/UI operation/resource. Fullgoalactive/incomplete.

Frozen V5candidate2e24a0fc remainsUNMODIFIED but its sourceproposals nowDEFERRED
forconfirmedpublic classifiercontractgap predatingfix. New durabledeferral here:
doc/sol-producer-v5-source-deferral-stream-classifier-20261018.json. All6V5paths
admission/workspace freshlyabsent, authorneverdispatched. No fabricatedhistorical
parentterminal; crossedgrant/START mustreconcile. Do NOTblindlyrun V5/oldV4/V3/V2.
Next: commit/push qualifiedsuccessor, prepare fresh exactcurrent-source V6plans
usingcurrentbinaries/productionpins andrequestRootfiniteIO; no automaticgrant or
newsourcepolicy/resource gate. Then prioritize actualcompatibility/properties and
acceptance consolidation instead of treating positiveoldwire as fullfaultproof.


## 2026-10-18 qualified stream classifier source513c121a published

Actualsourcecommitac7fb3/0; qualifiedproduction513c121a on
implementation/stream-classifier-ownership at /Users/alexy/src/unison-stream-classifier-20261018.
Fullcurrentproduction+correctedfixture regressionunion parent72746/c5db4c/0/no
session;55negative/compiler. All4nativebuild/selftests passed; nativeproduction/
compiler/binary hashes exact, one explicitlydeclared UNCOMPILED tests/remote_stream_errors.ml
fixture changed afterbuilds, separatelycompiled underbothcompilers. Allgroups/
CPU4or8closed; no EXIO/SDK/Photo/nativeUI or actualuncertainDirectoryFDs.
Evidence57c11c9133b2b761b8dccc351730cc868e4e2f13830f16eb66be0d01a6adf1b7,
527340B tests/qualification/rpc-stream-classifier-actual-20261018.json.
Inventoryv24/SOL/readiness/newdoccurrent, fullgoalnotcomplete.

Photo notice ACTUALLYqueued01a150b1-5cb8-7190-9386-cde1692ac850/ebbb040:
V5sourceproposalsdb616795 DEFERRED forconfirmedpublicclassifiercontractgap;
oldfrozen2e24a0fc untouched. Durabledeferral here
 doc/sol-producer-v5-source-deferral-stream-classifier-20261018.json.
All6oldV5admission/workspacepaths freshabsent atreceiptcreation, authornoV5dispatch.
No source-derived fakeparentterminal; contrarycrossedgrant/START mustreconcile.
No schedulinghold, no payloadnewgrant/replay inferred. V4already superseded,
V3/V2deferred. Currentfixnowqualifiesfailureboundary formerlyonlysourcenote.

NEXT: prepare ONEfreshcurrent-sourceV6 frozen requestset usingcurrentstock/Ox
builds /private/tmp/unison-stream-classifier-{stock,ox}-check-20261018-001/RESULT.json,
source513c121a, proof57c11c91. PreserveV5/V4files and consumedolderRootgrants.
Exactseparateupstream/retainedfork/properties Rootgrants beforeanyIO. Prioritize
these actualcompatibility/transfer checks +fullacceptancemap; no further optional
microextensions on a frozen runtimecandidate. No livequalificationjobs remain.


## 2026-10-18 CURRENT V6 IO requests queued; candidate fixed

Frozen /Users/alexy/src/unison-stream-qualified-20261018 branch
integration/sol-stream-qualified-20261018 metadataHEAD5cc96102/sourcebase63e4b947/
production513c121a. Do NOT edit this frozen worktree even for queue notes;
further handoff notes go outside it. Actualmetadatapreparation ad5352/0;
source400pins checked_plan bothpass; properties43execution329production pins+
manual.command/checked_build+INMEMORYadmissionchecker pass. Realcanonicalmetadata,
zero admissionfile/workspace/locks/process/payload. Current binaries from
/private/tmp/unison-stream-classifier-{stock,ox}-check-20261018-001/RESULT.json;
oneuncompiledfixture difference explicitly recorded inproof57c11c91, not hidden.

Exactindex doc/sol-stream-requalification-requests-v6.json2710B
SHA3fa0df6e7be8ffefe66939a1d55d19b9857edf29d496b8b2d8013d6a09e35085.
Upstream requestc991cc24/plan7260365a,workspace/private/tmp/u-mp-0c5fe64a,
admission/private/tmp/unison-stream-upstream-admission-0c5fe64a.json.
Retainedfork request36a77b87/planb5f430ad,workspace/private/tmp/u-mp-86195f02,
admission/private/tmp/unison-stream-retained-fork-admission-86195f02.json.
Each4generated8KiBcases12CLI/400sources/300obs30CLI/2+2endpoints+owner2<=8;
genuineupstream8772d26a extension-absent and oldersemantic-capablefork DISTINCT.
Properties request4ef4c673,workspace/private/tmp/u-props-362476bc,
admission/private/tmp/unison-stream-properties-admission-362476bc.json:
18rows54CLI/two2MiBfixtures/3+3+owner2=8/300obs30CLI/8GiBdeclarednotcap/
36readersmax. Exactargv/env inrequests; each needsseparateRootfreshSHA/deadline.
No SDK/Adobe/camera/Photo/nativeUI/compiler/performance/quiet/18borrow/retry or
automatic successor. V5source-deferred confirmedclassifiergap, V4superseded,
originalbytesunchanged. Contrarycrossedgrant/START mustreconcile; neverreplay.

Actualforkpush60462/9b47ac/0/no session. Rootrequest ACTUALLYqueued
01a150b4-62ea-7ca1-ba19-56376210b6b7 (1c7179/0). Outsidefreeze queue receipt:
/Users/alexy/src/unison-stream-classifier-20261018/doc/sol-stream-requalification-v6-QUEUED.json.
All3newadmissionpaths freshABSENT3f1cda, no runtimeSTART/workspace/SourceIOhold.
No ownlivejobs/resources. Standing8/8 unchanged; fullgoalactive/incomplete.
Next prioritizeactualcurrent-source compatibility/property grants and acceptance
consolidation; keep runtimecandidate fixed instead of unrequestedmicroextensions.


## 2026-10-18 acceptance rebind audit: concrete next work

Previous V6prep turn was progress. Fresh3V6admissions absent665242; no actualjob
or resourcewait claim from absence. Frozenstream-qualified5cc96102 unchanged.
Actualmetadataaudit8d6c0c/0/no session underUnison4, child/group/tokensclosed,
no EXIO/SDK/Photo/nativeUI.23 receipts checked plus4 explicitworkerstepresult
pins rehashed BEFOREuse. Audit doc/sol-acceptance-source-bindings-current-20261018.json,
actions doc/sol-current-acceptance-audit-summary-20261018.json.

Four oldactualworkerparity/apply results each53pins,38matches15changedcurrent
production files. Do NOTclaimcurrent1/2/4/8 or384-job apply from those historical
receipts. Renew with current actual nativeobjects, tests/workers/run.py, original
64-byte fixtures, configured1/2/4/8 but activeexecutionmax6+owner2=8 asoriginal.
No sourcefunctionrewrite/microextension required; source/syntheticstandinggrant
permits these tinyoriginalcontrols, not bulkIO/SDK/media. Inspect exact runner
argv/API BEFORElaunch and useactualsourceguard/canonicaltokens. RootV6candidate
code MUST NOT change. Allpriorfailed/consumedruns remain preserved, no replay.

Mergecacheold jointproof5sourcesmatch but semanticRuntime changed; inspect/renew
current-object composition ifneeded. Summaries withzero directbindings are
UNBOUND, not automaticallycurrent nor proof thatoldactualbehaviorfailed. Current
streamclassifierproof matches329directpins but no implicitSDK/camera/transport
adoption. Keep all12requirements, excludeuser-prohibitednewfuzz campaign, retain
legacy/platform limitations ratherthan endlesscleanupmigration. Nextpriorities:
actualV6compat/propertygrants, currentworkerparity/apply, acceptanceconsolidation.
Goalnotcomplete/notpaused/notblocked; no currentownedjob/resources.


## 2026-10-18 actualCURRENT worker parity/apply gap renewed

Audit aaf778e5 identified15changed production dependencies in historical worker
results. Fresh stockparity001 actualceddce/1 failed LINK beforeworker/fixturegen:
missingOwnedClose/DomainOwner/NotificationPipe currentimplementations. AllCPU8/
groupclosed, rawstderrpreserved. Fixed ONLY tests/workers/run.py dependencies:
StagePublication+Cstub, OwnedClose, DomainOwner, NotificationPipe; actualmatched
CMI/CMX/O objects copied fromcurrentproductionbuild, source/interfacehashchecked.
FrozenV6root5cc96102/source329+execution400 UNCHANGED (runnernotinV6closure).

Actual freshcontroller10119/8132d5/0/no session. Fourpositive sourcejobs under
Unison8 closed allgroups/children0/tokens. New namespaces
/private/tmp/unison-current-worker-{parity,apply}-{stock,ox}-20261018-002.
Parity64original64-byte jobs/compiler, configured1/2/4/8 activecpu1/2/4/6 +owner2;
8configured !=8simultaneous. Apply384jobs/compiler over6seeds:192completed/
192cancelled/0late_cancel/1255checks. Doesnotprovewhere cancellationoccurred.
Unused1GiBsparsefixtures absent, tinygeneratedDNG/probe prep only, noPhoto/SDK/
EXglobal/nativeUI/transport/performance. Source/linkobject/binary/logpins verified.
Only actual--build mode qualified, not standalone no-build portable compilation.

Evidence tests/qualification/current-worker-parity-apply-actual-20261018.json
103197B SHA2fe83118dca46ef70195971e00f9f9933cf4fb77ab2ad8bb8be89c131b3e30d8.
Prior audit remainsimmutablehistorical; this closes its worker gap for stated
currentobjectscope, not allother12area evidence. Mainhand off receives pointer.
Next: actualV6upstream/fork/property grants; inspect semanticRuntime dependency
for jointcache composition; remainingcurrentmerge/fault/platform/acceptance map.
No ownlivejobs/resources. V6 stillnotadmitted atlastread665242; dofreshcheckpaths
beforeoptionalwork. Keep frozenV6candidate fixed. Goal fullscopeactive/incomplete.


## 2026-10-18 current cache/runtime composition gap renewed

Fresh3V6admissions absent155023; frozenstream-qualified5cc96102 unchanged.
Exact runtime oldreceipt SHA6ed5055e matchedgit ancestor4b9e7e67 (not guessed
26fd parent: firstcomparisonfalse, then exacthistorylookupf24c75). Currentdelta
fixedpipeline baselineaccounting+resourceaccessor+latepureRemote classifier
registration, no cacheformat change. Old5matchingcachefiles didNOTautomatically
adopt oldruntime closure; renewedactualcurrent-object compositioninstead.

Actualcontroller78905/c3aeda/0/no session. Sixjobs stock/Ox joint,pipeline,
merge-errors underCPU4 each: allpassed/reaped0/groupsabsent/tokensclosed.
Namespaces /private/tmp/unison-current-cache-{joint,pipeline,merge-errors}-
{stock,ox}-20261018-001. Joint20scenarios+1designatedreject/compiler; asynccapture/
savedbase/cachedscalarmerge exact/sourceunchanged; merge-error propagation.
Private64KiBgeneratedDNG/state only, no SDK/Photo/transport/EXglobal/nativeUI.
REAL privatefile/opaqueDirectory close uncertainty deliberately persists until
actualprobeprocessexit, NOT normalinprocesscloseproof andno numericFDretry.

Evidence tests/qualification/current-cache-runtime-composition-actual-20261018.json
248951B SHA8f26bcfbcf1dc54de90a4a84e3a4c9809027f3e6484f96b337b8cf40381b0782.
Allcurrent329production/compiler/binary matcheschecked, controlledcache binaries
pinned. Only metadata/evidence/docs added; no newprod or V6runtimeclosurechange.
Audit oldgapremainsimmutablehistorical; this qualifiesstatedcompositioncurrent.
Nextpriorities actualV6upstream/fork/property grants +remainingacceptancemap,
notuniversalcleanupmigration. Goalactive/incomplete, no ownedlivejobs/resources.


## 2026-10-18 current XMP kernel and fixed observation renewed

Actual controller65831 initial7dcb8a terminalc277e0/exit0/no session. Four
original source controls stock/Ox kernel+fixed observation passed; all children
reaped0/groups absent/CPU8 closed per SHARED-CLOSED. Ox kernel four concurrent
domains; fixed observation random byte cases0/XML mutation campaign disabled.
Current source pins independently compared. This renews evidence after changed
xmpObservation/semantic_mode_filter dependencies; no production edit, SDK,
Photo, transport, EXglobal, pixel or performance qualification. Evidence:
tests/qualification/current-xmp-kernel-observation-actual-20261018.json
SHA f5b505b1df817cd5a82b8b445f1f22a71f399809cb0f0b784587c7d19364e126 . Frozen V6 candidate unchanged; its three admissions absent
at preceding fresh check. Next actual V6 compatibility/property grants and
remaining requirement-by-requirement acceptance consolidation. Goal active and
incomplete; no owned live jobs/resources.


## 2026-10-18 readiness historical/current distinction corrected

Readiness now leads with current production513c121a/frozenV6 candidate5cc96102
and exact four current qualification hashes. Its older “current” compatibility
and property statements are explicitly historical, not latest-source behavior.
Three V6 admissions freshly absent; no dispatch/hold inferred. Immediate runtime
work remains three separate V6 grants; M6 limits remain explicit. No prod edits,
new test executions or resource acquisitions in this documentation update.


## 2026-10-18 current fixed SDE conformance renewed

Actual controller3582/9768d4/exit0/no session, initial596b01. Stock and Ox
compiled current source and passed existing independent fixed wire goldens,
malformed/binding cases, local synthetic exact apply/source preservation.
Each child reaped0/groups absent/CPU4 closed; source snapshots rehashed exact.
No fuzz/sanitizer/SDK/Photo/transport/EXglobal/performance controls. Evidence
tests/qualification/current-sde-conformance-actual-20261018.json SHA 00a274ab3554ecd2013799e791b894a3b30d182738126384349c63cf9006bf78.
FrozenV6 production/runtime untouched; actual three transport/property grants
still needed, plus remaining M6 resource/platform/performance verification.
Goal active/incomplete; no owned live jobs/resources.


## 2026-10-18 saved benchmark read/write/transport distributions

Added separate directional protocol/read/write/model/unknown distributions to
existing timed summary. Four directed tests add86c/0 and saved-only actual
2adb9d/0 passed; both child/group/CPU4 closed. All108 historical rows retained,
no synchronization or payload repeated; raw66422ef7 unchanged. Evidence
tests/qualification/timed-resource-distributions-actual-20261018.json SHA 07cedbf7bef8ea0c805b25d81cc421b3161205b5127c4a2f725d50513c6a6737.
Report bench/sync/results/shared-timed-resource-distributions-20261018.md;
physical/application totals remainunknown, modeledextents notwrites. No general
speedup/currentcandidate/quietclaim. FrozenV6 unchanged, goal stillactive.


## 2026-10-18 current range components renewed

Historical range evidence had changed current copyRange/copy/C dependencies.
Actualcontroller6994/96a5a8/exit0/no session(initial404879) passed fourjobs:
stock/Ox native typed+two private negatives+13macOS ABI groups and constrained
48cases including960-combination matrix/compiler. Allchildwait0/groupsabsent/
CPU4closed, exactsourcepinsbeforeafter. Evidence
tests/qualification/current-range-components-actual-20261018.json SHA fcfc6d25cd5d843cb3d311d3454e824a3ddab3b64e3322a48c2ad71eda0715d2.
NoPhoto/SDK/Adobe/EXglobal/fulltransport/physicalsharing/otherplatformruntime
claim. FrozenV6 stillunchanged; fullcurrenttransferworkflow remainspending
its separate compatibility/property admissions. No ownedlivejobs/resources.


## 2026-10-18 current exact DNG reconciliation/materialization renewed

Fixed source runner dependency: tests/dng_reconcile/run.py now copies required
semanticHash_evp.h into isolated compiler snapshot (no production edits).
Actualcontroller5070/c3ff40/exit0/no session(initiald4fe44) passed stock/Ox
9originalcontrols each, private2MiB generated fixtures+distinctDarwinclone stage.
Independenttargetexact/sourceunchanged, returned3072logicalbytes/1write; opaque/
stalebasis/competing/peer-onlybase/invalidnonce refusals passed. Allchildwait0/
groupsabsent/CPU4closed. Evidence
tests/qualification/current-dng-reconciliation-actual-20261018.json SHA d14806d5e8fde9d4d67243d09525990710bc209da2de83cf4e742aad6f7b8186.
NoRPC/receiving/archive-baseauthority/SDK/Photo/EXglobal/physicalsavingsclaim.
FrozenV6candidate untouched, threeadmissions absentatfreshread; actualcurrent
transport/property remainsnext. Goalactive/incomplete/noownedlivejobs.


## 2026-10-18 current optional publication admission renewed

Actualcontroller1667/c0652d/exit0/no session(initial93e8b0) passed stock/Ox
fixed require/warn oversized refusals, fitting/off reservations, negative
declarations and exact oldguard rejection against currentRuntime+matched
productionobjects. All329productionpins matchcurrent; object/testpins rehashed.
Bothchildwait0/groupsabsent/CPU4closed. Nohelper/SDK/payload/CLI/Photo/EXglobal.
Evidence tests/qualification/current-publication-admission-actual-20261018.json
SHA 3e4d9fd1aace53ba6505c036b1f18ef541f33f1389764e8627b850217191eb7c. This renews narrowed admission behavior only, not actual
SDK receiving or globalhardRSS. FrozenV6 untouched; actualcompat/property
requests stillpending. Goalactive/incomplete; noownedlivejobs/resources.


## 2026-10-18 current validation warning/cancellation composition renewed

Actualcontroller64856/6cfc28/exit0/no session(initial016fdc) passed all11
fixed cases eachstock/Ox, actualselectedhandler/currentlinkedgraph withprivate
worker observations. warn findingonce/outside dispatch/pumprearmed, pass/require/
off-nohelper, inspection/mutation/activecancel/deliverycancel/abort/printererror
controls passed. Synthetichelpers reportedreaped beforecompanionreturn; owning
group/childwait0/CPU4closed. Sourcegraph/testpins rehashed current. Evidence
tests/qualification/current-validation-warning-actual-20261018.json SHA c4fb967f8074b56ee37edc1cb4829fd2bf0a7460d9a27dd4b33d76dc79022dae.
CLIexplicitlySKIPPED/noAdobe/SDK/Photo/EXglobal/nativeUI; oldnegativecontrols
notrerun here. FrozenV6 untouched/currentreceiving remainsseparate. Goalactive
and incomplete; noownedlivejobs/resources.


## 2026-10-18 build instructions corrected to standing8

Found outdated local-build-and-tests.md recommending rawfourjob build and
18credits asshareddefault. Replacedwithqualifiedmanual shared8/atmost2compiler
jobs and3+3selftestworkers+2owner; freshoutputs/actualterminal distinction,
SDK/EXIOcoordination andhistoricalfuzz tooling scopeexplicit. FourMake/Dune
stock/Ox dry-run commandderivations actual6e9f3e/0 checked jobs2/selftest3 and
buildsystemselection; nochildren/tokens/workspaces acquiredcreated. Evidence
tests/qualification/shared-build-documentation-dry-run-20261018.json SHA 4e7b3a98a8b32710f36fb51b5591b38ba297875f39d7b7128caccd388fb5678b.
No production/frozenV6 edits or newruntimegrant. Ordinary/clone success-write
counters remain unavailable; existing skip totals and output model are not
syscall counters. Do not relabel them. Goalactive/incomplete/noownedlivejobs.


## 2026-10-18 selected current worker FFI source audit

Reviewed current SHA/CommonCrypto+explicitEVP, positionalborrow read/write and
monotonic clock primitives with exactML/C/header/mode sourcepins. Updated
foreign-boundary-audit.md to mark oldtableshistorical and recordEVPownedcleanup.
No found heapaccess while released in selected positional primitives; hashing
holds runtime. Context/FD callerexclusive lifetime remainsmanualprecondition.
Evidence doc/worker-ffi-source-review-20261018.json SHA eb9b639c0cc2215cb213afca91b00ee2c343f2172d29968a067b048cdcbc2adf.
Other functions in sameCfile are explicitlyNOTreviewed by pinning file; remaining
namespace/quota/clone/publication/inherited/provider audits stayseparate.
No runtimes/tests/tokens/SDK/Photo operation, no production/frozenV6change.
Goalactive/incomplete; V6transport/property grants stillneeded.


## 2026-10-18 snapshot FFI trace and owner compiler boundary

Reviewed exactSnapshot worker→borrowedFDclone path. MacOS FD adapterpreflights
thennoeffectdeclines; namedAPFSclone separate, no mistakenFDcloneclaim.
Added originalcompileonly3probes: privatehash accepted, exactownerrecord/
cacheparent APIs rejectednonportable. Finalactual9870b7/0, child/group/CPU4
closed; no generatedprogram linked/run/pathopened. Initial0015f4abe/0 preserved,
002tightenedexactnameddiagnostic oracle. Evidence
tests/qualification/worker-ffi-owner-boundary-actual-20261018.json SHA ce0c75ce5177d524c28eec0f912652536346c72f50dd3afa40b6c5511cbb9f89.
Source doc/worker-snapshot-ffi-source-review-20261018.json pinsselectedreview,
notallreachableC/thirdparty/platform audit. No production/frozenV6changes,
SDK/Photo/EXglobal use or currentresources. Goalactive/incomplete.


## 2026-10-18 first-party built-in worker native reachability mapped

Currentmanualpaths map all implemented workeroperationfamilies to3leafmodules/
9nativebindings; declarationinventory checkedexact, source25filespinned. Reviews
cover firstparty SHA/file/timing/FDclone contracts. Ownernamespace/quota/
publication isexcludedfromworkerclaim, notblindlyauditedviawholefilehash.
Explicittrustedruntime/Unix/provider/customplugin boundariesremain, noautomatic
callgraph/racesanitizer/fullM6claim. Map doc/worker-native-call-map-20261018.json
SHA 435639179bc087f48e09d2096c447a477caca87d7d19f5ab686e68c49dbb3153. No tests/children/tokens/IO used, no production/frozenV6change.
All3V6requesthashesfreshmatch/admissions+workspacesabsent(actuala0958e); no
transportdispatchinferred. Goalactive/incomplete; nextmainaction V6freshgrants.


## 2026-10-18 draft PR13 source refresh

FreshGitHubread b9a605 showeddraftPR13head236e7f99 (masterbase) behind current
RPC/worker/cache fixes. Remoteheadcb7de0 confirmed236e7f99; both it and local
review5a3d4077 are ancestors of current source. All329productionbindings match
currentMake and frozenV6 exactly. Refreshingdrafthead by normalfastforwardonly,
no force/merge/checkout of historicalreviewworktree. Durable body
doc/pr13-current-review-20261018.md separatescurrent sourcecontrols frompending
V6transport andhistoricalSDK/camera/benchmarks. FrozenV6bytes unchanged, no new
runtimeadmission/claim. Fullgoalactive/incomplete; no ownedlivejobs/resources.

Actual draftrefresh completed: push b9d7bd/0, gh edit/readback d02fc5/0;
PR13 OPEN/DRAFT/masterbase/headad042761, bodyexactfilematchverified. Publication
receipt doc/pr13-current-review-publication-20261018.json. No merge/deploy or
newruntime/IO/CPU ownership. Active source contains followingmetadata only.


## 2026-10-18 blocked audit: exact V6 runtime admission absent

Three consecutive goal turns rechecked the same external scheduling blocker
(actual7109d6,ea96d0,154b5d); all3admissions/workspaces remainedabsent. Existing
requesthashes unchanged; no activeprocess or verified-livewait claimed. Photo
status request queued01a150dd-1dd3-79f2-b912-999506bc709d. No dispatchedV6run,
retry, implicitpermission, newresourcehold or secondrequest. Next meaningful
end-to-end action requires exactfreshPhoto admission or concrete reviewfinding.
Do not add repeated unrelatedcontrols merelytokeepactivityrunning.

Fullgoal remainsincomplete; current code/sourcecontrols anddraftPR13 preserved.
PR13draftmaster/headad042761 (latestsourcefollowupmetadata on implementation
branch5ee9f194), production513c121a, frozenV6candidate5cc96102. ExistingM6
resource/platform/performance limitations remainopen; blocked is notcomplete or
userpaused. No ownedlivejobs/CPU/IO/native resources. This note precedes the
goal-status blocked transition; resume reconciles actualnewstate beforedispatch.


## 2026-10-18 resumed: all V6 requests ACTUALLY PASSED/CLOSED

User resumedgoal andidentifiedPhotoRootPID37018. Fresh9cbcef observedall3
admissions/workspacesEXIST, superseding oldabsence/blockedaudit. Noexpired
redispatch. Root executedeachonce underseparateexactadmission:
upstreambe81c79b tool67161/cf10d6/0 owner97061/worker97077;
retained59c4fc41 tool90976/15836f/0 owner97287/worker97288;
properties1876867b tool21124/88509b/0 owner97612/worker97613.
Allterminaltranscriptions arePhotoRootpersonallycollected, notournewtoolpoll.

Independentmetadataaudit actual7db183/0 verifies45returnreferencepins, both
12callrawproxyaudits,4case/functionals perpeer, generatedfixtureSHA/noopidentity,
18rows54callpropertyaudit+prefix+outcomebinding,43execution329productionpins;
allworkerreaped0/groupsabsent/CPU+IOclosed. No payload/rerun/newresources.
Evidence tests/qualification/sol-stream-v6-actual-adoption-20261018.json SHA 035f9c9da18996e31cb0dd9266a0d07db9d6a1fddde6fad4a1ac242e71f45837.
Priorblocked/admissionabsence records remainhistorical; no currentwaitinggate.
FullgoalACTIVE/incomplete, next substantiveM6 resource/performance completion
planning/implementation ratherthanrepeatV6. Do notwaitforuserorclaimnewSDKgrant.


## 2026-10-18 endpoint CPU ceiling implemented and qualified

Activeworktree /Users/alexy/src/unison-cpu-ceiling-20261018 branch
implementation/endpoint-cpu-ceiling, basee3896900. New semanticcpubudget0
defaultunchanged orpositive min(selectedCPU,ceiling), sameexisting worker/helper
owner, no tokenpoolcreation orOSthread/RSS claim. This enablesbudgetedauto
comparison1/2/4/8/auto withoutautoselectingallhostcoresoutsideendpointgrant.
SourcechangeonlysemanticRuntime.ml; publicinterface unchanged.

Originalstockcontrol0014952/274e02/1 CLOSED: over-budget rejection isfailedLwt
promise, fixtureinitiallydidnotrun it. Fixedfixture002controller49929/7b61b2/0
stock+Ox11cases/ignoredceilingnegativepass; maximum2idleworkerdomains, uncapped
autocaseonlymetadata/nohost-sizedpool. Full4Make/Dune+selftestcontroller96224/
ca29d5/0,no session, all586inputpinsmatchperbuild; groups/CPU8closed. Evidence
tests/qualification/endpoint-cpu-budget-actual-20261018.json SHA 9fd71a8e75a5029f1789d4354ab444f8af4ecc186fb1e8916c06a979ee3f4a3e.
NoEXglobal/nativeSDK/payload/Photo work, nextactualtransport/timingrequires
separatelycoordinatedwindow. FrozenV6 candidate5cc96102 andits3PASS/CLOSED
runs untouched/consumed; priorblockednotes superseded. GoalACTIVE/incomplete,
no waitingforuser, noownedlivejobs/resources. Nextsubstantivework benchmark
auto-label/effectivebudget support/sourceplanning thenexplicitPhotoIOcoordination
whenappropriate; preservePhoto catalogwide5Kpriority/PID37018/session45622.


## 2026-10-18 benchmark explicit auto label/CPU budget source ready

Active endpoint-cpu-ceiling sourcebranch now adds bench/sync/worker_config.py
and run.py optional --endpoint-cpu-budget; --workers accepts labeledauto only
withceiling/currentendpoints/explicitloopbackbound. No silent8→3 clipping in
benchlabels; runtimecanclipbutbenchmarkrefusesmisleadingcomparison. Both
endpoints receivecap; params saveconservativeboundbeforeinitialsave. Fixed
qualification/legacypartition overrides refuse; oldintegerflags unchanged.

Actuald46957/0 threeCPU4controljobsclosed:5newtests(9mainargumentcases),15
existingbudgetadmissions/refusals,6artifactpincontrols. Initial6c602d/1 CLOSED:
testexpected1savewhilepreparerwrites2; fixedexpectation+initialrecorddeclaration
placement, failedbytespreserved. No binary/transport/compiler/payload/EXglobal.
Evidence tests/qualification/benchmark-auto-budget-source-actual-20261018.json
SHA 4c2b786950e2325d727bdac64b8264c7a5d979ec185264006b3e47300a8fed7a. Sourceonly, notactualauto-matrixqualification; needsversioned
plan/auditor/owner andfutureexplicitIOcoordination. Full586compiledinputproofs
from971271a8 remainunchanged; benchmarkPython notcompiledintoCLI. Photo
catalogwide5Kpriority unchanged; no resourcesheld/goalnotblocked.


### 2026-10-18 — versioned auto cohort auditor source controls

Added bench/sync/auto_cohort.py: one compiler/selector cohort, 1/2/4/8/auto,
18 rows/54 calls. Distinguishes endpoint permit upper bound, declared peak
and reserved credits (8 or explicit future 18 borrow). Audits strict attempted
prefix lifecycle separately from complete functional rows, binds nested outcomes,
rejects unknown/reordered/cross-cohort evidence. Never authorizes FD release or
claims actual parent terminal, command-policy authentication or measurements.
Historical journal entrypoints retain their 1/2/3 default.
Actual 1f9863/0 and ad0061/0: directed new controls plus existing timed-shared
regression; both children reaped0/groups absent/CPU4 closed, no EXIO/payload.
Evidence tests/qualification/auto-cohort-source-actual-20261018.json.
Next: exact argv/parameter/artifact binding and dispatcher owner integration,
then fresh coordinated IO qualification. Photo catalog-wide5K priority untouched.


### 2026-10-18 — auto cohort exact launch/declaration binding
Added exact launch builder/checker and audit_bound to auto_cohort: one pinned
compiler/binary declaration, explicit endpoint ceiling8, 32MiB×8 generatedfiles,
1warm+5measured per3modes, 30s CLI observation, client flag tail checks.
Actual66a082/0 original directed controls passed; child54049 reaped0/groupabsent,
CPU4closed/no EXIO. Evidence auto-cohort-bindings-actual-20261018.json.
No admission or actual benchmark. Remaining: server flag/whole client command
namespace binding, authenticated immutable plan/artifact checks under IO, and
dispatcher owner integration before fresh coordinated matrix. Auto upperbound
is not observed domain count; reserved18 requires fresh Photo coordination.


### 2026-10-18 — full cohort client/server command binding
Bound full client argv (bothroots/launcher/servercmd/fixedflags) and server argv
(exact -server __new-rpc-mode plus selectedflags), lexical canonical fixture
root, unique rowdirectories and same-directory seed/update/noop. Actual516ab2/0
and268326/0 controls passed; finalchild54431 reaped0/groupabsent/CPU4closed.
No transport/EXIO/Photo payload. Evidence auto-cohort-commands-actual-20261018.json.
Next is authenticated plan/current artifact hashing and actual dispatcher owner
integration. These pureaudits alone never authorize release or establishparentexit.


### 2026-10-18 — cohort immutable plan schema
Added cohort_plan.py pure exact schema: source/prerequisite SHA inventories,
qualifiedartifact declarations, exact generated argv, private nonceworkspace,
900s owner/30s CLI observation, 32GiB declared logical IO (not enforced),
CPU8/18 exactindexes and explicit temporaryborrow requirement. All5selectors
and10directed refusal variants passed actualbb514c/0; child54716 reaped0/group
absent/CPU4closed/no EXIO. Evidence auto-cohort-plan-actual-20261018.json.
Not current-file authentication or dispatch qualification. Next integrate stable
metadata reads/current source+artifact checks and retained worker owner; do not
request Photo quiet18 before exact executor/failedprefix closure is reviewable.


### 2026-10-18 — cohort bounded authentication
Added checked_metadata authenticating planSHA/duplicate-freeJSON/current trusted
sourceinventory/prerequisite bytes and runner location. Separate verify_artifacts
hashes interpreter/binary/compiler only when futureowner already owns admittedIO.
Uses existing cached_benchmark bounded epoch-fenced reader/qualified close carrier.
Actualdfc1fe/0+a1db9e/0 generatedtinyfile controls and carrierpropagationPASS;
lastchild55021reaped0/groupabsent/CPU4closed/noEXIO/realbinary/Photo payload.
Carrieridentity, uncertainFDrecords and originalcause preserved, no readretry.
Evidence auto-cohort-auth-actual-20261018.json. Not runtimequalified; reviewed
fixedinventory+productionbuild binding+actual dispatcher/retainedowner stillneeded.


### 2026-10-18 — current production build binding
Added independent production inventory enumeration (current329 matches qualified
receipt329 by metadata) and strict successful build/selftest/artifact receipt
binding plus current sourcehash verification. Fixed execution inventory includes
benchmarkPython and qualified close/owner dependencies; removed two nonexistent
namespace __init__ entries foundduringmanualread, actualexistencecontrol added.
Actual03a54f/0+80eb6c/0 directedgeneratedfixtures PASS; lastchild55574 reaped0
/groupabsent/CPU4closed/noEXIO. Evidence auto-cohort-build-binding-actual-20261018.json.
Next remains actual retained-owner/dispatcher integration and finite lifecycle
controls; no runtimegrant/fullbenchmarkqualified claim.


### 2026-10-18 — retained shared8 cohort owner integration
Added tests/cohort_entry.py / sync-auto-cohort target to established dispatcher.
Exact admitted worker/plan/workspace; actual inheritedcanonical9FD/parentbinding;
afterIOartifacthash/current329productionbuildbinding pre/post; original failure
record, source-bound prebenchmarkzero-call path; postentrymissingjournal UNKNOWN
retains; complete/failedprefix auditedbeforeworkerreap andCPUthenIOclose.
Plan schema2 adds authenticated build_receipt. Actual installed compiler alias
ocamlopt→ocamlopt.opt resolved against historicalreceipt; canonicalexecutable
paths required. Larger4/8/auto cohorts refused byshared8 entry, need separately
coordinated18borrowowner; no silent clipping.
Actual8aadce/0,86b30e/0,02d83e/0,f21a64/0 controlsPASS: new owner/plan/cohort,
legacy timed/manual/binding regressions; inertdispatcher sixcases success/failure/
unknown/live/exitcontradiction/closeuncertainty, onlyouterCPU4 real. Allchildren
reaped0/groupsabsent/CPUclosed/noEXIO/transport/SDK/Photo payload. Evidence
tests/qualification/auto-cohort-owner-source-actual-20261018.json.
Runtime transport stillUNQUALIFIED; next finiteactualshared8 cohort and reviewed
18borrowowner forfull1/2/4/8/auto matrix. User scheduling change: requested Photo
finishliveoperationnormally thenholdnewIO/Adobe; queue01a15276-c403 delivered,
actualPhotozero-resourcehandoffnotyetclaimed. CanqualifyAdobedirectlyhereafter
actualhandoff, finalPhotoworkflowlast. No needfinalPhotoallowanceasgoalblocker.


### 2026-10-18 — explicit temporary18 cohort owner source
Extended ONLY sync-auto-cohort with explicit same-admission temporary_borrow
argument: freshRootpublishedexacttarget/command/workspace/deadline18 grant, exact
policySHA/token00..17, pinned independentlyreviewedcoordinationreceipt, restore
standingpolicydeclaration. Authorizationcheckedbeforeacquisition+beforelaunch.
Actualcanonical19FD metadata binding onlyforcohort18; all othertargets remain8.
No pool or policyfilescreated/rewritten; no idlecoreinference/autogrant.
Directed original controls actual2ce390/0+b59403/0 PASS including8/18 inert
success/failedprefix/unknown/live/exitcontradiction/uncertainclose paths plus
legacy lifecycle/binding/timed/plan. AllouterCPU4childrenreaped0/groupsabsent/
tokensclosed; NOactualEXIO/18borrow/transport/SDK/Photopayload. Evidence
auto-cohort-borrow-source-actual-20261018.json. Next metadatafreeze/request and
finiteactualcohorts afterPhotoactualhandoff. User askedPhotoworklast; no need
waitforPhoto toexecuteAdobe onourbehalf, but actualcurrentownerclosure still
required beforeIO. Goalactive/no ownresourcesheld.


### 2026-10-18 — ten exact auto cohort requests prepared
Prepared doc/auto-cohort-qualification-v1-20261018/INDEX.json (12796B,
SHAd23d4744ee421e47767118a88f4038c6eedf3a36bfcdbd46fb1c558cabf655c5).
Allstock/Ox×1/2/4/8/auto:10cohorts,planned180rows/540CLI/30warm+150measured.
53currentexecutionpins perplan; existingqualifiedendpointCPUstock/Ox build
receipts and prerequisitesauthenticated; executableSHAdeclarationscopiedfrom
receipts, NOTfreshbinary/compilerpayloadhashbeforeIO. Current329production
sourceinventory exactmetadata compared earlier, runtimewillhashinsideIOowner.
Metadata-onlyfreezer actual17cc9c/0 child59880reaped0/groupabsent/CPU4closed,
all10checked_metadataPASS; e1ef15/0 verifiedall10workspacesABSENT. No admission
created/no transport/SDK/EXIO/borrow. Evidence auto-cohort-freeze-actual-20261018.json.
Photo schedulinghandofffollow-up01a1527f-87c0 sentexactindex: userwantsPhotoIO
last, directUnisonAdobequalificationafteractualdrain. Noactualhandoffinferred;
next executeexactfinitecohortsonlyaftercurrentPhotoresourceclosureconfirmed.
Default8/8unchanged; largercohortrequiresseparatetemporary18authorization.


### Scheduling correction after cohort freeze
Photo reported NEWbulk256 START69656/41f53d controller60081 afterourdrainrequests.
Treat actualcurrentEXIO+Photo8 ownership as live untilPhotoactualterminal; NOT
paused/handedoff. Queue01a15280-658f explicitlyreconciles user'sPhotoIO-last
steering: drainnormalcheckpoint ifsupported, do notcancelunsafepublication or
liveowner, finishatomicadmitted256ifrequired, HOLDsuccessors thenactualclosure.
No UnisonIO/Adobe/18borrow dispatched; sourceworkunderown8continues. Frozen10
cohortrequests stillUNADMITTED/unused, sourcepinsunchanged.


### 2026-10-18 — completion audit and changed-Runtime renewals
Current 14receipt explicit-pin audit actual48a315/0/child61565closed found worker/
XMP/SDE/range/reconciliation matchingpins, but cacheRuntime and warningRuntime
changed solelybyCPUceiling. Oldzero-bindingcamera/SDK/transport summaries not
promotedtocurrent. Renewed exact6CPU-only controls stock/Ox currentqualified
builds: cachejoint20scenarios+designatednegative, asynchronous64KiBpipeline,
11warning/cancellationcases each (--skip-cli; synthetichelperonly). Actualowner
59806/68e562/0/no session, all6childrenreaped0/groupsabsent/CPU4closed.
Evidence cpu-ceiling-dependent-composition-actual-20261018.json containscurrent
329sourcepins perstep, rawresults/closures/artifactpins; deliberatelyretained
cacheuncertainty endsattestprocessexit, notnormalinprocesscleanup. NoSDK/
transport/EXIO/Photo payload. No production/frozenrequest sourcechanged.
New doc/sol-completion-checklist-current.md recordsfullM0..M6/12area closure
work; tenplannedcohorts alone doNOTcomplete fullsize/workload/topologymatrix.
HardRSS remainsunavailable/refuses, notenforced; native/pixel/corpusclaims
remainseparate. Next actualcohorts+directAdobeafterPhotoactualhandoff; meanwhile
noownresourcesheld/goalactive.


### 2026-10-18 — ten-cohort saved report preparation
Added tests/cohort_report.py outsidefrozenruntimeclosure. Pure/reportCLI accepts
pinned plan/resultJSONmetadata; all10×18rows expected, missingcohorts explicitly
listed, knownfailedprefixes retainrowindexes+originalfailure/nopass, unknown
refuses. Five measuredsamples kept/warmups onlydistributionexcluded; directional
protocol/read/write/model/CPU/RSS separate, physicalIOunknown staysunknown.
One-worker ratios descriptiveonly; rawbytes remainauthenticatedinputfiles.
Originalcontrol14870a/1 pretestimportpathmissing CLOSED, fixed7d7247/0 then
addeddisposableCLIroundtrip/hashrefusal e0ac07/0. All3childrenreaped/groupsabsent/
CPU4closed/noEXIO. Evidence auto-cohort-report-controls-actual-20261018.json.
All53frozencohortexecutionsourcepins stillMATCH; no planrepin/admission/run.
Photo bulk256actualhandoffstillrequired; own8source/reportworkcontinues.


### 2026-10-18 — direct Adobe successor prepared/current probes built
Built exact stock/Ox mixedprobes fromcurrentqualifiedCPUceilingCMX graph, actual
50303/aae501/0/no session; rootchildren65297/65309 reaped0/groupsabsent/CPU4
closed, compilerchildproofs inrawbuildreceipts. ZEROprobe/SDKcalls.
Metadata preparation09e8e9/1 foundmissinghistoricalSDKbuildmanifest (no plan
created/no dispatch); recovered619exactbytes from2a05c4bf schema/driverSHA+
recordedqualification fields, matchesindependenthistoricalSHAede0fb503aee...
Newdoc/adobe-sdk171-retained-build-manifest.json only; oldtmpnamespaceNOTrecreated.
SDKsourcetreeabsent, no SDKrebuildclaim; retainedbinarymustfreshhashinsideSDKIO.
Successor doc/mixed-validation-current-cpu-ceiling-request-v1.json
SHAf9c93745d873b5dc4f1c84381d74ebd4583ef1b93c0a9b1449bffeb805a689c9,
planb054d77e/362sources, twoSDKv1single+twoExiftool13.59+32hash tasks. Source
checked, input8fields unchanged by lstatONLY; no newpayloadhash. UNADMITTED.
Evidence current-mixed-probe-builds-actual-20261018.json.
ActualPhotohandoff received/adopted:69656/bc04d0/137 recoveryclosed (NOTsuccess),
receipt7546b5521f83f452493ec01f0d13dc0043dfc290007bbc446bc00342412768d8,
fresh4bca1e/0 entirebundlefree; PhotoNEWIO/nativeheld, MainstillPhotoexclusive.
Userdirectqualificationnowinprogress: stock1actualtool22685/f83404, parent66497/
worker66520, admissione5f4a2e4, workspace941741d1619946e1b45f876ad800c0c6.
EXglobal+Unison8held untilactualparentterminal+all54call/group/FDaudit.
Metadata/sourceinspectionduringrun disclosed; no quiettimingclaim. NoSDK/
18borrow. MUSTcollect22685actualterminal; doNOTreplaythisconsumedslot.


### Actual stock1 cohort PASS/CLOSED — no stale hold
Direct owningtool22685 initialf83404 terminala005f2/exit0/NOsession personally
collected; worker66520genuinelyreaped0/othersabsent, CPU8+EXIOclosed/all53source
pinsunchanged. 18rows54CLI exact/normalnestedsettlements; no errors. New
OWNER-TERMINAL+OWNER-RETURN sealedworkspace941741d1619946e1b45f876ad800c0c6;
return ebc9c0106842b136ac12156d0ad9ff8e44b15b7b59ed024b8cea977a27fc7668.
Evidence tests/qualification/auto-cohort-stock1-actual-20261018.json.
Admissione5f4a2e4 CONSUMED_ONCE/no replay. Rootactualclosurenotice01a15290-b30c
sentBEFOREsealing. Prior runningnotesabovehistorical; no currentownresources.
Measured5sampleupdate medians ordinary4.92975s/receiverclone4.87450s/semantic
9.01267s; no semanticwall-speedup claim. Minor sourcemetadata/Gitwritesdisclosed,
notquiet. 3warm+15measured retained, raw1987945B unchanged.
Next separateOx1/stock2/Ox2 shared8 cohorts underuserhandoff; NOTautomaticreuse
ofstock1grant. Larger18cohorts requireexplicitborrowcoordination (requested
01a1528f-7385, notyetgranted). DirectmixedAdobe requestf9c93745 remainsUNADMITTED
andnoSDKexecuted. MainstaysPhoto-exclusive. Goalactive.


### Ox1 actual PASS/CLOSED; largercohort coordination active, no18borrowyet
Actualtool29564 initialed00c9 terminal058ffe/0/NOsession, parent69144/worker69160.
18rows54CLIexact, workerreaped0/groupsabsent/CPU8+EXIOclosed/source53unchanged.
Admission2404e206 CONSUMED_ONCE. Rootpromptclosurenotice01a15296-ad41 sent
BEFOREseal. OWNERRETURN15ee828d57c2f08763bad00329608a2521db491aad0f5130a406910998a6cebb
workspacebc8512209b3f4f3aa2b164c0af4c2595. Evidenceauto-cohort-ox1-actual-20261018.json.
Saved-onlyactualreport568f1a/0: 36rows6groups/8cohortsmissing, immutableJSON+
Markdown doc/auto-cohort-one-worker-pair-report-20261018.*; rawhashes/no exclusions.
Additionalstock1savedreportab08d8/0 alsoINCOMPLETE, nopayloadrerun.
RootACTIVEcoordinationreceipt nowexists17436B
/Users/alexy/src/lightroom/.private/photo/coordination/UNISON-TEMPORARY18-SIX-COHORTS-ACTIVE-20261019.json
SHA84ced3064bf8f1f66025f6a3a6511118272d332306f64be845f49406c91e3f58;
conditional a6da6a97 NEVERauthority. Active permitsONLYsix stock/Ox4/8/auto with
freshpercohortadmissions, exact00..17/policy1dbe12eb/restorestandingtrue. Root
reviewedexact6plans/requests andasksall4shared8closuresforadoptionbeforefirst18.
No18START/leaseyet. Finishstock2/Ox2 next undernewoneuseshared8admissions;
thenpublishall4actualproofs. Photo holdsALLnewjobs exceptinertedits/metadata;
MainremainsPhoto-exclusive. Nootherownjobs/resourcesactive.


### Stock2 and Ox2 actual PASS/CLOSED — all4shared8 complete
Stock2 actual26570/5a6b6b→c6f903/0/no session parent71776/worker71792;
Ox2 actual43971/661920→70c1b8/0/no session parent73527/worker73544. Both
18rows54CLI exact, workerreaped0/othersabsent/CPU8EXclosed/53sourcepinsunchanged.
Freshadmissions238a31f3 and2decf4b1 eachCONSUMED_ONCE; no retry/replay.
PromptRootclosurenotices01a1529c-e200+01a152a2-31ea BEFOREseals. Returns
stock2170e70df01254de9cfc0faf1adf37be1639dc398570139e984ebceb7311bd34f;
Ox29f6c592448e30f7b38e28ebe457067d143c3b8ec1b485f389be22db518ffc488.
Actualevidenceauto-cohort-stock2/ox2-actual-20261018.json.
All4shared8proofindex doc/auto-cohort-four-shared8-actual-closure-20261018.json
SHA44895383308d9775858fb8568c9aabe4863b404b9098470a7a9b93986a867afa;
72rows216CLI/12warm+60measured; everydirectartifacthashrechecked.
RootALL4metadataadoptionreceived (savedterminals+aggregate+216nestedcalls, NOT
independentfullrawreaudit). ACTIVE84ced306 conditionmet; maypublishfresh
individual18admissions forONLYsixfrozenstock/Ox4/8/auto, serial/nooverlap.
PhotoALLnewjobshold, MainstillPhoto-exclusive. No18STARTyet/noownresources.
Saved-onlyff0f61/0 report12groups/6missing preserved all72rowrefs, nooutliers
removed. doc/auto-cohort-four-shared8-report-20261018.json/.md. Descriptive
semantic1→2wallratios1.481stock/1.464Ox only; no causal/quiet/physicalclaim.
Next first18stock4 freshadmission mustpinACTIVE84ced306, exact00..17/policy
1dbe12eb/restorestandingtrue andcurrentunusedrequest. DirectSDKrequestf9c93745
stillUNADMITTED, noSDK/Main/nativePhotocall. Goalactive.


### First temporary18 cohort stock4 ACTUAL PASS/CLOSED
Freshadmission3e586f24 (5956e4d18f9c4f3a9cf53fa99c52aed5) boundexactACTIVE
84ced306 andall4adoptiona226261e +current53pins/unusedworkspace. Actualtool
37134 initial3045ce terminal0e82ac/exit0/NOsession, parent76082/worker76100.
Workspace85e328936afa4f16b400115248b99c88 actualSTART18tokens+19inheritedFDs.
18rows54CLIexact/nested54auditPASS, workerreaped0/groupsabsent/CPU18EXclosed.
Rootpromptactualnotice01a152a9-a6ad BEFOREseal; no pernextcohortACK needed.
Freshpostclose2359a6/0 EX→all18 bundle reacquired+close_unstarted(no children),
proof0b2a90e22cc669411d24c35fca6f0c3cba647383600777d8e071f894e22a5701.
OWNERRETURN13b8a5f00312ca2b4629514418c9de2626c3fd06627252f639c3482e0d213a5d;
evidenceauto-cohort-stock4-actual-20261018.json. Sourcepinsunchanged, noSDK/
Photo/Main/compiler work/policyrewrite. Allcurrentownleasesclosed, butPhoto
coordinatedserieshold persists throughsix; fullstanding8/8+2 restorationreport
onlyafterseries. Firstof6closed/5of10total (90rows270CLI), remaininghigher
Ox4,stock8,Ox8,stockauto,Oxauto UNSTARTED. NextOx4fresh exactadmission directly
underACTIVE84ced306; Rootexplicitlysaidno further percohortACK wait/replay.


### Ox4 temporary18 ACTUAL PASS/CLOSED
Actual54329/923568→e08bd5/0/no session,parent78745/worker78761;18rows54CLI
exact,auditedworkerreaped0/groupsabsent/CPU18EXclosed/source53unchanged.
Workspacee4ba98011a8d4909a52b1246579e51de,admission56178224consumedonce.
OWNER-RETURN 754cff65973d420cd6e344c05d60b7d934488ee48baef17d5e70e0e3fd6effd5; evidenceauto-cohort-ox4-actual-20261018.json.
PromptPhotoqueue01a152b1-50bc BEFOREseal. Sixof10cohorts/108rows324CLI closed;
remainingstock8,Ox8,stockauto,Oxauto freshserial underACTIVE84ced306.
Serieshold continues,no SDK/Main/compiler dispatch or finalstandingrestorationyet.


### Stock8 temporary18 ACTUAL PASS/CLOSED
Actual16900/5d127d→dc6d60/0/no session,parent80746/worker80762;18rows54CLI exact,workerreaped0/groupsabsent/CPU18EXclosed/source53unchanged.
Workspace16fdad99a19b4ae0a280559ace5563ec,admission07869063consumedonce.
OWNER-RETURN 4fbb0f1498e7fe2833947e4a93a3fd44f3e0af7e4e4b592096c1d1c8c5b53970; evidenceauto-cohort-stock8-actual-20261018.json.
Sevenof10/126rows378CLI closed; Ox8/stockauto/Oxauto remain.
SeriesholdACTIVE84 continues,noSDK/Main/compiler/finalrestoreyet.
Preexecpublisher1fa37c/1 refused metadata equality(extra bytesfield) BEFOREadmission/workspace; comparison corrected, runtime sources unchanged.
Postclosuresealer c2ff35/1 refused zerobyte stderr in nonempty metadata reader; hash corrected from savedbytes, no runtime repeated.


### Ox8 temporary18 ACTUAL PASS/CLOSED
Actual22458/b0ce77→d16f39/0/no session,parent82759/worker82782;18rows54CLI exact,workerreaped0/groupsabsent/CPU18EXclosed/source53unchanged.
Workspace02f27a5d1e7f43d59f7f1fddbc5378ec,admission4ddd20bbconsumedonce.
OWNER-RETURN 670cbdaf314b82b5789a604cb48a67cd728225bf41a6fc27bf03ccbdd86f3490; evidenceauto-cohort-ox8-actual-20261018.json.
Eightof10/144rows432CLI closed; stockauto/Oxauto remain freshserial.
SeriesholdACTIVE84 continues,noSDK/Main/compiler/finalrestoreyet.


### Stockauto temporary18 ACTUAL PASS/CLOSED
Actual49709/f0118e→336e2d/0/no session,parent84404/worker84420;18rows54CLI exact,workerreaped0/groupsabsent/CPU18EXclosed/source53unchanged.
Workspace9e8c29a61f17489bb375fa6b4f3e4a13,admission3df77beeconsumedonce.
OWNER-RETURN f7f9006e4cf638b40e06cca4a0bc7d94207d06952da8a120caed9baf009a18e2; evidenceauto-cohort-stockauto-actual-20261018.json.
Nineof10/162rows486CLI closed; finalOxauto remains freshserial.
SeriesholdACTIVE84 continues,noSDK/Main/compiler/finalrestoreyet.


### All ten cohorts ACTUAL PASS/CLOSED; temporary18 ended
FinalOxauto48415/0a7bbd→ca24cc/0/NOsession,parent86053/worker86072.
All180rows540CLI/30warm+150measured, everyactualparent0 and worker/group/FDclosure.
Finalreturn30b22a74; all10savedreferences independently rehashed fac32c/0.
Actualclosureindex doc/auto-cohort-all10-actual-closure-20261018.json SHAb93e1d31.
FinalnochildEX→whole18 reacquire/close26284d/0, proofe61fc193; no inventedchildsettlement.
EXPLICIT STANDING8Unison/8Photo/2system RESTORED; policyfileunchanged/no next18grant.
Photo notifiedpromptly01a152c4-e50b andexactrestoration01a152c5-86e9.
Saved-onlyreport46da89/0 FULL_GENERATED_MATRIX, all30groups preserved; humanreport
doc/auto-cohort-all10-report-20261018.md. Descriptive semantic1→8 ratios2.258stock/2.291Ox;
notcausal/OSquiet/physicalIO/corpus/fullSOLproof. Largerworkloads stillopen.
DirectAdobe readiness3ec347/0 checked362sources+generatedinputepoch/unusedworkspace,
noSDK/mediaopened. Exactrequestf9c93745/planb054d77e pathsin doc/mixed-validation-current-cpu-ceiling-{request,plan}-v1.json.
Next freshUnison8+EX SDK/ExifTool/hash admission; PhotoCPU8source mayresume,
Photo nativeSDKbulkIO pause continues through separate directqualification, MainstillPhoto-exclusive.


### Current direct Adobe/ExifTool/hash ACTUAL PASS/CLOSED
Ownertool15556/557bdc→682f67/0/NOsession,parent89542/worker89558;
freshadmissiondb1b955cconsumedonce,workspaceunison-mixed-current-cpu-ceiling-3cff5cf671d44f31b072f7617c091136.
Two currentstock/Oxproductionlinkedprobes,2SDKv1single+2ExifTool13.59helpers/32hash tasks.
SDKstructurevalid/decodesuccess/rawdigestvalid/errors0/warnings4edgepadding each;
allreportedhelperwait/groupsclosed/probewait0/workerreaped0/CPU8EXclosed.
362sourcescurrent/parentheldIOtool/build/clonebytesreverified; borrowedgeneratedsource8fieldsunchanged.
Evidence tests/qualification/current-mixed-adobe-actual-20261018.json; OWNERRETURN17d4509f6757ef852e9224dc1e11e88341599754646a4378d1f8ee68fa2f28dd.
PromptPhotoactualrelease01a152c7-2e87; no reportsealinghold. ALLownjobs/resourcesclosed,
standing8/8+2. UserPhoto-at-end steering continues: noPhotoMain/original/SDKgrantreuse.
This closes currentmixedcomposition only; finalreceivingoff/warn/require+largerworkloads/edges/reviewremain.


### Current actual SDK full receiving PASS/CLOSED
Freshrequestbad8a4e3/plan4440adcf, admission56968be1 consumedonce;
actual67541/5a4c41→5343fe/0/NOsession,parent91837/worker91853.
Workspace/private/tmp/u-smr-current-9e2e489b:2fullreceivingCLI/4realSDKsinglehelpers,
2generatedencodings/twocompilers; receivedbytesexact, rawdigestvalid/decodeSUCCESS/errors0
(4edgepaddingwarnings each preserved). Raw2proxyframes independentlyreboundtoaudit.
Workerreaped0/groupsabsent/Unison8EXclosed,169harnesspostpinsunchanged;
329productionpins/currentbuildbindingscheckedpreexec, SDK/binarieshashedinsideheldIO.
Evidencecurrent-sdk-multifile-actual-20261018.json, OWNERRETURN419ad9d2b60206a99d0c84d7a245cf8b9db65ca4ce88655608cdc08fcfec244b.
PromptPhotoactualrelease01a152ca-82d7; no sealgate, userPhotoIO-at-end stillcurrent.
NoMain/original/pixels/corpus/computeoverlap/production inference.
Next finalreceivingpath/policy matrix andlargerworkloadsourceprep, noautoSDKdispatch.


### Current all-scanned actual PASS/CLOSED
Generated48MBreadonlyclone preparedb47398/0(nochildren/Unison8EXclosed),
fixture/private/tmp/u-asv-fixture-ea3c7dda, hash0daa233d/no borrowedsourcehash.
Request7a77563e/planad740cd8, admissionf362b72bconsumedonce.
Actual45243/895aac→e035b2/0/NOsession,parent94382/worker94398,
workspace/private/tmp/u-asv-current-d84a0085.4CLI(2offnoSDK+2requireall-scanned
noops/4realSDKhelpers) currentstock/Ox, exactno-transferstatuses; rawdigestvalid
/decodeSUCCESS/errors0/warnings4preserved. Raw4proxyframes independentlybound.
Workerreaped0/groupsabsent/Unison8EXclosed/191postpinsunchanged; currentproduction329
checkedinexistingownerbuildbinding. OWNERRETURN8c1f3ff3985182c76fff7c827f0d7c46343c8593ce0565fdae43a6f525b60e09;
evidencecurrent-all-scanned-adobe-actual-20261018.json. PromptPhotoactualrelease01a152ce-89cc.
V1requesttargettypo supersededUNSTARTED;47e4fc metadata-relativepathguard refusedbeforeV2write;
71ce11 createdcorrectabsoluteV2, no originalrequest/admissionreused/runtimefailure.
Allownjobs/FDsclosed;PhotoIO-at-endstillheldperuser,CPU8sourceindependent.
Nextpolicy/pathmatrixsourceaudit/largerworkloads, no automaticSDKgrant.


### Larger workload SOURCE successor prepared; no payload dispatch yet
No production change:971271a8 binaries/current329 source pins remain. New nested
cohort/2 dimensions128×4,512×4,2048×2, preserving exactoldcohort/1 and plan/2.
Limits derive7200owner/180CLI, unknownretains, declared4TiBlogicalnotphysicalcap.
Shared1/2need8;4/8/auto neednew18coordination(notconsumedACTIVE84).
Actual52559a/0 original46controls passed; realonePythonchildreaped0/groupempty,
outerCPU4closed. Ownerinline reusedclose_unstarted after actualsettlement;
childproofwasreal, notno-childclaim; futureownersuseexplicitproof-bearingclose.
Three frozenindexes/30cohorts540rows1620CLI SOURCEONLY under doc/auto-cohort-qualification-larger-*-v1-20261019/.
Series82ee83dc:doc/auto-cohort-larger-series-prepared-20261019.json; no admissions.
Legacyreportactual4e051e/0 re-auditsall180savedrows/no rerun, originalrawunchanged.
Receipt tests/qualification/auto-cohort-larger-legacy-report-actual-20261019.json.
Newtests/source/lifecycle scope documented doc/auto-cohort-larger-plan-20261019.md.
Photoqueue01a152d4-baed receivesfinitechecklist/new18request; no extraACKforclosedruns.
Allownjobs/resourcesclosed. UserPhotoIO-at-endhold remains;CPU8sourceindependent.
Nextfirst128stock1 freshshared8guard/admission; no18untilfreshPhoto coordination.
CurrentSDKfull67541/5343fe/0 +allscanned45243/e035b2/0 source/harness scope preserved
asactualpriorruns, not relabeled to this subsequent Python-only harness commit.


### LIVE larger128 stock1 — do not replay
Actual ownertool52223/initial91798e, parent97775/worker97794, workspace
/private/tmp/unison-auto-cohort-18d2fe7b45df433ba9fb2ca9def4cb3f.
Fresh admission/private/tmp/unison-larger128-stock1-admission-9facb61ba14340c99dee08d14e2aaff7.json
SHAc08b51ff0668cd600000ae18def1ada1bcfbe75da3f22f2c2ca868e7fef0e985,
request4235fbe6, 128MiBx4/18rows54CLI/7200sOBSERVATION180CLI. StandingUnison00..07+EXonly,
noSDK/camera/Main/18borrow. Last actual write_stdin c31ea4 retained session52223,
not terminal. Must poll SAME handle; report source does not prove parentclosure.
Do not edit frozen Python execution sources while live. Docs/metadata only.
Photo receivesactualSTART01a152d7-8d8b and practicalestimate01a152d8-7d16.
Photo source-reviewed all30newplans; newconditional18record
/Users/alexy/src/lightroom/.private/photo/coordination/UNISON-LARGER18-COHORTS-CONDITIONAL-20261019.json
SHAfda6288a6cd634067aa5d0d2596282c84c542f42889a68818c5b1de60d2fa84c
is NOT ACTIVE/admission/borrowauthority. All12shared8 mustactualclose, PhotoCPUdrain,
thennewACTIVEbefore18borrow. Old84six-cohortcoordinationconsumed/NEVERreuse.
Planning: old10 START→savedterminal intervals sum~3215s, includespoll/seal latency.
Simplecorpusbyteprojection forlarger30~23h (rough18–30h),notruntimeguarantee;
7200sperownerisobservationnotestimate. REVIEWCHECKPOINT afterthisfirst128actualclosure
before blindlydispatchingmorepayload; calibrateestimate/orderwithoutdiscardingrequiredsamples.
PhotoIO/native remainsUNSTARTEDperuserPhoto-at-end; CPU8source maycontinue.
No mutualACKwaitgate forclosedhistoricalruns. Goalincomplete/active.


### CHECKPOINT reached: first128 stock1 ACTUAL PASS/CLOSED
Ownertool52223/91798e→3c264e/exit0/NOsession,97775parent/97794worker.
18rows54CLIexact/nestedPASS/workerreaped0/groupempty/CPU8EXclosed/53postpinsunchanged.
Admissionc08b51ff consumedonce, workspace18d2fe7b45df433ba9fb2ca9def4cb3f;
OWNERRETURN0daeec580f42f65f8d62fed8c7af1ff45d54df7219845a1ee6762401010e187a.
Evidence tests/qualification/larger128-stock1-actual-20261019.json.
Saved-only reporte3f21b/0 INCOMPLETE_MATRIX/18rows,9sizecohortsmissing.
Medianupdatesordinary11.266858/clone9.801000/semantic18.823947seconds,
5measuredsamples each preserved. FinalRESULTmtime-START653.10s;sum54CLIwalls425.48s;
terminaltranscription706.10s includespoll/seallatency, notpreciseworker/hardwall.
Source-onlyhumaninterpretation doc/larger128-stock1-checkpoint-20261019.md.
Promptactualcheckpoint01a152e1-7a28; timing/seal01a152e2-ab9d. Allownjobs/FDsCLOSED;
no furtherpayload/SDKstarts until operator schedulingreview alreadyraisedbyPhoto.
Preliminaryfull30projection18–30h/central23h remainsrough, notcontinuousquietgrant.
PhotoIO/native remainsUNSTARTEDperuserat-end pendingoperatorchoice, CPU8sourceokay.
New18conditionalfda6288a remainsNOTACTIVE; allother29largercohorts UNSTARTED.
Continueindependent source/finalacceptancework, GOALACTIVE, no replay/goalpause.


### Final acceptance source audit and review package
Actualmetadataauditd87e99/0:21receipts/buildrecords;9direct-all-match,
3historical/mixed,9no-directbindings. Fullcurrentstock/Oxbuildreceipts329pinsmatch;
no-direct SDKreceipts require explicitplan/build/raw joins, notautomaticpromotion.
Currentcomposition329pin receipt supersedesoldRuntime cache/warning dependency scope.
Newdoc doc/sol-final-acceptance-map-20261019.md mapsall12requirements withremaininggaps;
not a completionclaim/rewrittenobjective. Audits/owner/actualtool filespreserved.
Read-onlyGitHubcheck1d2e12/0:PR13 OPEN DRAFT/baseforkmaster/heade3896900,
so current CPUfeature/evidence not yetinreviewbranch. Source-only forkpublish
anddraftbodyupdate authorized; no merge/upstreampush/productionactivation.
Allpayload/nativeSDK remains atfirst128checkpoint pendingoperatorscheduling,
noactiveownjobs/FDs; source-delivery/audit workcontinues standing8/8.


### Fork draft review refreshed; no merge
Atomic source-only forkpush actual45392/72e265→ebb27c/0/no session,
head04cdb11be6617882307579dc88e0ef9082133896 published to both implementation and
integration/sol-consolidated-review. Source Git child/group reaped0 before CPU4+EX close.
No hooks/pre-push executable existed; pack thread1. No media/SDK/benchmark job.
PR13 body actual19654/e9ce23→95fccf/0; independent readbackdee1c2/0
confirms OPEN DRAFT/baseforkmaster/head04cdb11b. No upstream push or merge.
Evidence tests/qualification/draft-review-source-publish-actual-20261019.json.
PR text readability corrected separately (spaces/reader-facing final sentence),
not a runtime change; follow-up docpublish may update sourcehead again.
All resources/jobs currentlyclosed; payload/native remains at schedulingcheckpoint.


### Active source worktree moved; benchmark candidate remains frozen
NewSDKsourceworktree /Users/alexy/src/unison-final-adobe-20261019,
branchimplementation/final-adobe-qualification fromf6bfd653. Worktree creation
actual17096/466616→486ad7/0/no session, Git child/group reaped0/CPU4EXclosed;
source checkout only, no compiler/SDK/media. OldCPU-ceilingworktree andall29
remaininglarger execution/requestpins stayunchanged, conditionalfda stillNOTACTIVE.
CurrentSDKmerge pureplan+original3tests/10refusals PASSEDactual2e015a/0;
childreaped0/groupempty/CPU4closed. tests/sdk_merge_receiving/{plan.py,plan_test.py,README.md}.
Exact9calls/3codecs/6SDKdeclared, stockclientOxserver,2+2+2creditsinside8;
6144MiBpayload/64FDaccounting, nothardRSS/OSthreads. NOworker/entry/freezer/
admission/request yet; runtimeNOTREADY, no realSDK called or previousgrantreuse.
Legacymergerunner cannotbe blindlyrepinned: media preflight outsideIO and old
abortingaggregate/4-credit model require currentretained-ownercomposition.
Next implement metadata-only manifest/input binding, clone-only preparation,
exactjournal transport/known-prefix+helper audits/uncertainty controls. Review
observation-expiry behavior before using a cancelling CLI timeout with nativehelpers.
UserPhotoIO-at-end/operatorcheckpoint for furtherpayload remains; source work
continues. DraftPR13 headf6bfd653/OPEN DRAFT remains tested published candidate;
this newpartialsourcebranch is local and not merged/pushed into review yet.
Noownlivejobs/resources. FullgoalACTIVE/incomplete; no goalpause orblockedclaim.


### SDK merge source-input binding controls and changed temporary state
Pure inputs.py+inputs_test.py added: exact12readonly states/8field metadata/UID/
noalias/privatepath/scalargeometry. Combined5tests/24negativevariants actual38b070/0
passed; childreaped0/groupempty/CPU4closed, noSDK/media/IOpool. Evidence
current-sdk-merge-input-controls-20261019.json. No runtime entry/worker exists yet.
Metadata join actual325e54/1 FAILED beforepayload: oldPREPARED.json nowmissing,
oldprepared directoryempty; originalgenerated sourcefiles alsoabsent. Earlier
2d36e9 sawmanifest/all12statespresent; causeunknown, notourdeletion and noPhotooriginals.
Current metadata d51540/692d5a/f8cc1d confirms recent48MBreadonly and39MBJPEG
copies+qualifiedSDKbinary stillpresent. See sdk-merge-retained-input-metadata-20261019.json.
Source-onlypreservationproposal doc/sdk-generated-fixture-preservation-plan-v1-20261019.json
SHAc69109ad:2nativeclonesonly/persistentFirstPairUnisonstore/hashnewclones87022256B,
256MiBdeclared/60s/CPU4EX/noSDKbenchmark/sourcehash/sourceFIVEchanges. UNADMITTED;
exactexecutor+controls/schedulingexception beforeexecution. Rootqueue01a1530d-c1e2.
No competingpool/oldnamespace recreation, no restoredmanifestguessing; JXL/state
recovery orregeneration remainsneeded. Continue sourceworker/auditsindependently;
noactiveowner/resources, no goalpause/blockedclaim. Old30benchplansstillfrozen.

## SDK merge successor: ordered failure accounting — 2026-10-19

New source `tests/sdk_merge_receiving/ledger.py` preserves intent before terminal
references, refuses reordered/repeated calls or successors after failure, and
keeps unfinished intents unresolved. Successful updates require two distinct
endpoint helper references; seed/no-op require zero. Failed calls may reference
0/1/2 helpers but never infer noncreation or authorize resource release. Every
report still requires independent raw process/helper and worker/FD audits.

Ten original inert tests passed under canonical Unison CPU00..03; child24686
actually reaped0/group-empty and all four tokens closed. Actual owner tool chunk
106069/exit0/no session. No IO pool, media, transport, SDK or compiler invocation.
Receipt: `tests/qualification/current-sdk-merge-ledger-controls-20261019.json`.
This completes source failure-accounting controls, not the executor or runtime
qualification. Missing older generated fixture states remain a separate input
recovery task; no historical fixture or admission was recreated.

## SDK merge kernel and helper auditor — 2026-10-19

Active source worktree `/Users/alexy/src/unison-final-adobe-20261019` now contains
`tests/sdk_merge_receiving/worker.py` and `helpers.py`: intent-before-invocation,
independent transport/output adapter boundaries, strict two-endpoint SDK frame
and retained-group parsing, unchanged nested uncertainty carriers, and no release
authority. Failures after dispatch retain original cause/outcome/ledger instead
of becoming an ordinary failed-prefix release. No real transport adapter or
native CLI/admission is provided yet; this is not a runtime-ready successor.

Combined18 original inert controls passed actual toold78078/exit0/no session;
child25376 reaped0/group-empty then canonicalCPU00..03 closed. Earlier helper
controls cf7510/0 likewise closed. Receipts `tests/qualification/current-sdk-merge-
worker-controls-20261019.json` and `current-sdk-merge-helper-controls-20261019.json`
record outputs/source pins. Zero SDK/media/IO-pool/transport/compiler invocation.
Next: retained real transport/raw evidence binding, then fixture recovery and
owned freezer/admission. Historical input loss remains unknown; no source photos
or historical tmp namespaces were changed. No further benchmark/native starts
from these source controls; goal remains incomplete and active.

## Split retained child lifecycle — 2026-10-19

`tests/sdk_host_matrix/shared_child.py` now exposes `start()` returning an owned
handle whose captures drain immediately, and `finish()` which observes/group-
audits/reaps without signals. Existing `invoke()` composes both. This enables a
proxy to run concurrently with a client without leaving its output undrained.
Invalid observation inputs after launch raise the retained child/capture carrier;
finish attempts are one-use, with no uncertain FD numeric retry. No real merge
transport/proxy or native admission has been wired yet.

Actual initial combined controls failed a stale nested-carrier assertion, and
controller25899 retainedCPU00..03. Its wrapper failed to persist the captured
outcome before retention; original worker wait4 is not reconstructed or claimed.
Diagnostic e5908d (child26085 reaped1/group-empty, CPU04..07 closed) isolated the
stale expectation: shared_io_pool intentionally preserves the original inner
observation beneath the more precise outer capture identity. Test now verifies
both, without weakening descriptor retention. Successor6a2907/exit0/no session
passed30 controls; child26236 reaped0/group-empty and CPU04..07 closed. Tiny Python
children only, no SDK/media/Unison/canonicalIO/compiler.

Independent source-bound idle-controller recovery observed no descendants or
other group members before exactPID-onlySIGKILL; original owning tool24504 then
returned4d2122/exit137/no session (not normal exit). Final5f7059/0 freshly acquired
and closed allUnison00..07. All resources closed. Three versioned qualification
receipts `current-sdk-merge-split-child-{controls,initial-recovery,final-closure}-
20261019.json` preserve pass/failure/recovery separately. No payload/native run
or repeated old admission. Next: retained proxy and actual transport evidence
bindings, authenticated fixtures, owned freezer/admission, then native qualification.

## Retained merge proxy/transport source kernels — 2026-10-19

Active source worktree `/Users/alexy/src/unison-final-adobe-20261019` now has
`tests/sdk_merge_receiving/proxy.py` and `transport.py`. The proxy bounds buffers,
forwards protocol EOF, separately observes normal native terminal/reap, and never
sends cancellation signals. Errors retain native/socket/FD owners and preserve
nested descriptor uncertainty. Paired transport starts/drains both peers before
finishing, retains both handles on either failure, and returns separately read
raw proxy evidence for independent auditing. No standalone runtime/native entry
is provided and no resource release authority is claimed.

Ten original controls passed e62099/exit0/no session, child27330 reaped0/group-
empty and canonicalCPU00..03 closed; earlier five proxy controls4bf241/0 likewise
closed child27037. Six generated socketpair/pipe bytes only; native Popen and
paired-process cases are inert doubles. No SDK/DNG/Unison/compiler/canonicalIO.
Receipts: `tests/qualification/current-sdk-merge-{proxy,transport}-controls-
20261019.json`. No native paired execution or Adobe functionality is newly
qualified. Next raw-receipt binding/worker adapter, input recovery and immutable
owned freezer/admission; missing old generated fixtures are not silently replaced.
Goal stays active/incomplete; no runtime grant or resource hold from source work.

## Merge raw evidence binding and worker transport adapter — 2026-10-19

`/Users/alexy/src/unison-final-adobe-20261019/tests/sdk_merge_receiving/evidence.py`
now binds exact stock/Ox/proxy commands, both normal peer/group records, typed
PID/counter/EOF fields and independently read raw proxy bytes (duplicate keys
refused). Raw helper process/group lines are hashed as ledger references.
`bound_call.py` composes retained pair/read/persist/bind and preserves uncertainty
on audit or persistence failure. Final executor must independently re-read saved
evidence for its audit callback; no-op audit is not qualified. Proxy control
header is now exact current RPC invocation BEFORE native process creation;
additional server arguments cannot be silently executed then rejected afterward.

Actual61734c/0/no session:36 original source controls passed, child28620 reaped0/
group-empty, CPU00..03 closed. Six generated socket/pipe bytes and fabricated
native/process evidence only; no SDK/media/Unison/compiler/canonicalIO. Full
receipt `tests/qualification/current-sdk-merge-bound-evidence-controls-20261019.json`.
This advances the retained executor, not runtime qualification. Next exact
owned writer/freezer/entry wiring, generated input recovery and actual paired
transport qualification before immutable native admission. Goal remains active;
no resources held or new Photo/native/payload starts from source qualification.

## Owned evidence store + complete fabricated worker wiring — 2026-10-19

Final Adobe source branch now has `tests/sdk_merge_receiving/store.py` and
`journal.py`: pinned0700 directory FD, one-use0600 bounded records, file+directory
fsync, before/after-close publication inode fences, strict independent reads,
combined uncertainty carrier and no numeric retry. Worker callbacks now write
pair evidence and independently re-read/rebind its hash before accepting each
outcome.19 immutable events record allnine pair pins for independent parent
reparse; neither store nor journal authorizes resource release.

Actual0d5774/exit0/no session passed nine original controls, child30248 reaped0/
group-empty thenCPU00..03 closed. This includes an allnine-call FABRICATED worker
sequence with real tiny private JSON evidence, substituted-output refusal,
write+close and directory-close uncertainty injections, directory/name swaps,
links/modes/nonregular input refusal. No real SDK/native/Unison/media/compiler/
canonicalIO; originalfd8fe0/0 eight-case receipt retained, finalv2 adds name-race
fence. Receipts `tests/qualification/current-sdk-merge-durable-evidence-controls
[-v2]-20261019.json`. No actual uncertain OS close occurred in injected controls.
Remaining before native qualification: exact owned entry/freezer/launcher wiring,
authenticated generated input recovery and real paired transport qualification.
This advances validation harness/source only, not new production functionality.
Goal remains active/incomplete; no resources held and no new payload dispatch.

## Launcher + actual retained original-process pair qualified — 2026-10-19

Active finalAdobe branch now has thread-free `sdk_merge_receiving/launcher.py`
and a real original-Python pair control. Exact RPC header, bounded forwarding,
normal server/client/proxy settlement and raw-evidence binding work together.
Actualb9e9c7/exit0/no session:four controls PASS, client32666/proxy32665/original
Pythonserver32667/controller32664 actualreaped0, groups empty, allcaptured/socket/
directory owners closed thenCPU00..03 closed. Actual internal observations in
client+proxy match allfour canonical CPU device/inode pairs (307122463..466 on
dev16777223), parent identities unchanged. No SDK/Unison/media/compiler/
canonicalIO; pair payload abc→ABC (six protocol bytes). Source artifacts and
proof retained `/private/tmp/u-mgp-2gurkr37/PAIR-PROOF.json`3745B
SHAc036ce5724299ffee1baebe1d4285146acd51fc386cae0a2e2dedc8ca17b5284.
Receipt `tests/qualification/current-sdk-merge-original-pair-controls-v2-20261019.json`.
First979341/0 proof preserved separately; v2 added child descriptor observations
and used fresh namespace, not a repeated native admission. Allresources closed.
Remaining: production owned entry/freezer/admission, generated fixture recovery
and actual Unison+Adobe merge matrix. Process control does not prove native
merge/functionality. Goal active/incomplete; no current owner/resource hold.

## Exact native admission contract + metadata preflight — 2026-10-19

Final Adobe branch adds `sdk_merge_receiving/admission.py` and `metadata.py`.
Packet declarations bind both builds/compilers, qualified SDK and interpreter,
twelve typed input states/manifest ancestry, exact source inventories and
standing8/EXglobal budgets. Pure admission checking requires owner-derived worker
argv, exact request/plan/source maps, fresh finite start deadline and nonce;
never renews/replays or borrows18. Metadata preflight hashes current source/JSON
receipts, joins actual build/selftest declarations to current production, and
lstat-fences DNG states without opening DNG or executable payload. Actual artifact
and clone hashes still require admitted IO ownership. `entry.py` is specified
but NOT implemented/runnable yet; no runtime packet/admission is frozen here.

Actualbc3b95/exit0/no session:11 original controls PASS, child34478 reaped0/group-
empty, CPU00..03 closed. Original reader doubles reject artifact/media opens.
Earlierd3b8c1/0 nine contract controls preserved separately. No SDK/native/Unison/
compiler/canonicalIO/media run or grant. Qualification receipt `tests/qualification/
current-sdk-merge-preflight-controls-20261019.json`. Current SDK executable still
exists by lstat; oldfixture-writer binary was freshly observed absent97a466, no
artifact opened/rehash or replacement inferred. No historical SDK source tree
or generated JXL/state files were recreated. Next owner entry/freezer wiring,
authenticated fixture recovery and native matrix. Goal active/incomplete.

## Parent merge owner lifecycle source controls — 2026-10-19

`tests/sdk_merge_receiving/owner.py` now composes atomic one-use mkdir, exact
admission, existing EXglobal→CPU NB bundle, IO-owned artifact callback, retained
worker start/inherited nineFDs, actual parent/worker records, independent external
audit and directory→CPU→IO close order. Failed start attempts (even ordinary
constructor errors) retain resources; only known no-start failures can take the
preentry-close path. CPU-close uncertainty retains IO and remaining known FDs.
No CLI/actual runtime callbacks/native admission is provided yet.

Actual2b088a/exit0/no session:13 original owner/admission/preflight controls PASS,
child35658 reaped0/group-empty, outerCPU00..03 closed. All tested pool/child/auditor
interfaces inert, metadata records original/private/disposable. No canonicalIO,
SDK, Unison, media, compiler or new grant. Receipt `tests/qualification/current-
sdk-merge-owner-controls-20261019.json`. Next actual resource binding, native
worker fixture/runtime callbacks, entry/freezer and authenticated input recovery
before final native matrix. Goal active/incomplete; no active jobs/resources.

## Generated-state runtime data callbacks — 2026-10-19

Final Adobe branch now has `tests/sdk_merge_receiving/data.py`: native-clone-only
seed/update installation into disposable receiving files using existing
fclonefileat primitive, readonly retained-source epoch fences, distinct-inode
check before chmod, disposable clone hash+epoch fences, guarded atomic install,
full receiving output hashes and no-staging check. Noop requires unchanged bytes
and all eight identity fields. No source hash/write or copy fallback in native
path; injected test backend explicitly reports unknown source-hash-byte count.

Actual80cd7a/exit0/no session:15 original data/input/worker controls PASS, child
36753 reaped0/group-empty, CPU00..03 closed. Data fixtures arbitrary64-byte strings,
not DNGs; no real native clone/SDK/Unison/camera/compiler/canonicalIO. Receipt
`tests/qualification/current-sdk-merge-data-controls-20261019.json`. Actual
retained-source epochs preserved across the successful simulatednine phases.
Next native entry/resource-binding/script/freezer composition and authenticated
fixture recovery before actual merge qualification. Goal remains incomplete.

Completion-checklist re-audit confirmed SOL explicitly requires representative
sizes/other workloads/topologies and final receiving case mapping; not all closed
by current generated cohorts or pure tests. No extra exhaustive MakerNote gate.
Fresh GitHub metadata baa847/0 confirms PR13 OPEN DRAFT, headf6bfd653 againstfork
master; it includes CPU-ceiling source, but this new Adobe harness branch remains
local. Corrected stale checklist statement that CPU ceiling was absent. No merge,
push, runtime grant or payload dispatch occurred from that metadata readback.

## Runtime composition + actual descriptor guards — 2026-10-19

`tests/sdk_merge_receiving/runtime.py` now composes data/clone callbacks, private
home/tmp/archive state, generated one-use shims, per-call artifact hashes, saved
phase deadlines, retained transport, journal, helper and output checks. Result
records allnine preparation pins so parent can independently re-open exact phase
configs. `child_entry.py` checks proxy's real worker parent and canonical9FD
metadata, records it, serves/writes frame, and retains on unknown with complete
saved uncertainty diagnostics (no fstat/retry of uncertain numbers). Shared
binding explicitly permits current-sdk-merge at8 only; metadata inspection still
never asserts lock grant or resource release. Top-level entry/freezer and parent
auditor are NOT yet implemented/runnable.

Actuald061b3/exit0/no session:13 focused controls PASS, child39847 reaped0/group-
empty/CPU00..03closed. Final1ad668/0 two runtime controls PASS after adding nine
prepared-record pins, child40194 reaped0/group-empty/CPU4closed. Native transport/
SDK/artifacts are fabricated; data are arbitrary64-byte strings. No canonicalIO
lock, native clone, SDK/Unison/compiler/media or new grant. Earlier27-case
d2404b/0 preserved; focused successor removes duplicated inherited data cases.
Receipts `tests/qualification/current-sdk-merge-runtime-controls{-v2,-v3}-20261019.json`.
Next top-level entry+independent parent audit/freezer, then fixture recovery and
actual native qualification. Goal active/incomplete; these controls hold nothing.

## Independent native parent audit implemented — 2026-10-19

`tests/sdk_merge_receiving/parent.py` now independently reparses allnine raw
client/proxy/server/helper records, reconstructs the exact19 durable event
snapshots, checks SDK candidate/build/report bindings and six helpers, clone
backend/source/byte records, shim hashes, worker/proxy9FD observations and no-op
identity. Default final callbacks metadata-fence allretained inputs and freshly
hash allsix owned private finaloutputs while parent retainsIO. Return never
claims owning-tool terminal, semantic eligibility or pixel comparison. Incomplete
runs refuse rather than taking an ordinary failed-prefix release path.

Owner now records monotonic observationdeadline and createsOWNER-START-READY
onlyafter immutable START publication completes. Future entry must honor that
marker before reading, avoiding a read of a partially written START file.

Actual1e54ea/exit0/no session:two original parent tests/eight named refusal
variants PASS, child44726 reaped0/group-empty/CPU4closed; allsource/native/helper
evidence fabricated and final readers injected. Initial104b6b/0 passed parent+
sevenowner regressions, child43843 closed. NoSDK/nativeclone/Unison/media/
compiler/canonicalIO/newgrant. Receipts `tests/qualification/current-sdk-merge-
parent-controls[-v2]-20261019.json`. Next top-level entry/freezer and authenticated
generated fixture recovery, then actual native qualification. Goal active and
incomplete; these controls own no remaining resources.

## Native merge entry and immutable metadata freezer now runnable — 2026-10-19

New final-Adobebranch files: `entry.py`(owner/worker/check-plan), `inventory.py`,
`artifacts.py`, `freeze.py` under `tests/sdk_merge_receiving`. They connect current
metadata/source inventories and exact admission to existing canonical pools,
retained owner/worker/runtime and independent parent audit. Worker final closes
retain nine inheritedFDs on metadata-directory uncertainty and never resurrect
already-closed numeric slots on partial resource close. Metadata-only freezer
creates immutable plan/request/index from authenticated JSON and lstat/source
pins; it never opens DNG/executable payload or mints an admission. Artifact byte
hashes stay inside ownedIO. No currently valid real generated-input packet was
frozen: tests use fabricated source/SDK/build data and remove their private JSON.

Actual7e0b63/0/no session:12 focused controlsPASS, child50107 reaped0/group-empty/
CPU4closed. ActualCLI7e5dfa/0: entry+freezer help49060/49062 exit0; native missing-
admission refusal49064 exit1 BEFOREplanmetadata, allchildwaits/group/captures/
CPU4closed. Sourcebootstrap fix verified via actual file launches. Earlier
dde5d3/e1da74/f0fc20 controls preserved. Receipts `tests/qualification/current-
sdk-merge-{entry,freeze,freeze-v2,cli,entry-freeze}-controls-20261019.json` (exact
filenames in qualification directory). No SDK/Unison/media/compiler/IO pool or
newgrant; native-source composition is implemented but NOT actually qualified.

Next actionable dependency: authenticated input recovery/regeneration (oldJXL
and12scalarstates missing; two recent generated originals/validator previously
observed surviving; fixture-writer absent). Preserve allhistorical receipts and
oldnamespaces; no fabricated fixture substitution. Then real freeze+fresh exact
IO coordination/admission, native matrix, independent evidence adoption. Other
SOL benchmark/workload/case-mapping requirements remain; goalactive/incomplete.


## 2026-10-19 — Photo IO last; final scalar case mapping

User steering: finish Unison source/tests/acceptance first, direct Unison Adobe
qualification last; Photo is not an execution intermediary. Standing8/8 stays.
No new Photo pause/IO grant or native dispatch inferred. Prior response was a
plan only; this continuation made concrete saved-evidence progress.

New source worktree doc/sol-xmp-final-case-map-20261019.md maps conflicts,
delete/edit, Bag/Seq/Alt, qualifiers, rendering/unknown refusal, exact opaque
preservation, scalar symmetry, stale/peer-only base, nonce, and exact DNG
materialization. Fresh audit d3e301/exit0 checked104 explicit source bindings
and16 saved artifacts: all match. JSON: doc/sol-xmp-final-case-bindings-20261019.json.
This is not a test rerun/transitive-runtime proof/receiving pass; archive authority
and actual final native merge remain open. Entry/freezer source composition
already implemented at3db68092; checklist wording corrected. Next generic clone
and parser case mapping; authenticated three-codec fixture recovery remains
required before final Adobe phase. No owned jobs/resources started. GoalACTIVE.

Scheduling update from Photo Root: newer user steering lets Photo go first.
Hold NEW EXIO/native/SDK/benchmark starts; standingUnison8 source work may
continue. No currently owned Unison IO/process, preservation remains unadmitted
and unstarted. This supersedes local execution ordering while Photo runs.


## 2026-10-19 — Clone/range final case mapping and evidence gaps

New doc/sol-clone-final-case-map-20261019.md maps geometry, short progress,
unsupported/errors, indeterminate effects, immutable shifted/duplicate bases,
volume/alias/EOF/binding changes and cancellation to actual test bodies. Fresh
metadata audit ab4513/0: all60 current range source bindings and18 saved artifacts
match. JSON saved as doc/sol-clone-final-case-bindings-20261019.json.
Important: old transfer-output receipt0/5 pins current; later stream-cap6/9
including currentcopy/transfer/probe/run. Remote dependencies differ; do not
relabel as full final execution. Inherited-rsync predecessor and legacyclone
filesystem case integration still need scoped binding/renewal. No test/native
run, payload read, CPU/IO lease or production edit. Photo-goes-first hold remains
for new IO/native; own8 source work continues. GoalACTIVE/incomplete.


## 2026-10-19 — Actual final transfer controls renewed, both compilers

Committed successor runner replaces subprocess timeout/kill with shared_child
owned observation, bounded capture, actual direct/group proof and retained
ownership on uncertainty. No production edit. Actual10579/f819e0→6aaca5/exit0/
NOsession, controller53811, stockrunner53827/Ox54304 reaped0/groupempty.
167positive checks/compiler +9designated negative participants/compiler; each
runner60real compile/probe calls, all120 actualreaped/groupssettled. CPU00..03
closed; noEXglobal/SDK/Photo/transport/nativeclone, <=80KiB originalfixtures.
All329currentproductionpins matched both buildreceipts and direct runnerpins
unchanged. Receipt tests/qualification/final-transfer-controls-actual-20261019.json;
workspace/private/tmp/unison-final-transfer-controls-ejq52ux8. This renews token
framing/output allowance with final current remote fragment and transfer/copy
source, not final inherited-rsync publication/transport/corpus proof. Photo
goesfirst IOhold unchanged, no liveUnisonjobs/resources. Next inherited-rsync
source/binding closure; actualnative clones defer until PhotoIOreleased.


## 2026-10-19 — DNG parser fixed-case inventory and SDE evidence mapping

Photo reported bulk resume actual49291/030390; newEXIO/native/SDK/benchmark
remain held; own8sourcecontrols permitted. No Photo release inferred.
Current DNG map doc/sol-dng-final-case-map-20261019.md traces TIFF/BigTIFF/order,
graph/pixels/previews/original/opcode/ICC, cycles/aliases/counts/sparse/highoffset
and SDE bindings. Fresh saved audit:82current SDE sourcepins+4savedartifacts
match (127commands2224asserts/compiler original actual3582/9768d4/0).
In-memory existingfixtures:33valid/247invalid/27525120generatedlogicalbytes,
NOTparserexecution/refusalproof; nofiles/native/SDK/photo/sparse. Initialhelper
fe0909/1 usedmissingclose_unstarted method/nochildren; preservedfailure. Fresh
successor96ce3f/0 reacquiredCPU00..03andqualifiedclose_descriptors succeeded.
JSON inventories under doc/sol-dng-{fixed-case-inventory,final-case-bindings}-
20261019.json. Extendedprofile/latercomponent parser actualbindings stillneed
renewal/scopedmapping, not universallyqualified by SDE evidence. Allownjobs/
resourcesclosed. GoalACTIVE, continue source work while Photo goesfirst.


## 2026-10-19 — Extended-parser runner ready for owned final qualification

Source-only successor removes subprocess timeout kills/check_output from
DNGprofile/1 runner; compiler metadata+compile+test all use observed owned
groups and capture actual cleanup. Log write/fsync/close qualified; combined
write/close uncertainty preserves original and child outcome, no numeric retry.
TopUnresolvedretains owner/evidence. Kept ALL fixed +3negative mutations +4sparse
cases; no narrowing to easier subset. Generic fixtures import collision found
actualdf33cb/1 before execution, fixed namespaced dng_profile_v1.fixtures.
Eightoriginalinjected controls+actualCLIhelp f63f6b/0/no session, children58776/
58778 actualreaped0/groupempty, CPU00..03closed/noEXIO/native/parser/compiler.
All4mutation anchors validated current source without compiling. Receipt
tests/qualification/extended-profile-owned-controls-actual-20261019.json.
Full actual extended-parser run stillpending PhotoIOrelease; no new admission
or payload/SDKstart. Earlier inventory runnerpin is historical afterthis edit;
fixture data/test bodies unchanged. GoalACTIVE; no liveownedresources.


## 2026-10-19 — Full extended-parser pair prepared, not dispatched

Source review of owned runner found no additional process/log boundary gap.
New doc/final-extended-profile-pair-plan-v1-20261019.json freezes33sourcepins,
qualifiedPython and both ocamlopt.opt SHAs, exactfullcommands+absentworkspace.
Percompiler1253fixed cases (source-derivedcount), all3negative mutations, all4
sparseoffsetcases retained; serial1compiler insideUnison8+EXglobal. Nofixed-only
substitution/newfuzz. Exactpins rechecked by preparation7a82d3/0. No executable,
sparsefixture, IO/CPUreservation or admission created. CompanionMD explains
actualouterterminal/group/FDclosure and retainunknown/no signals. Photo49291
bulk goesfirst; no newIO/native/SDK/benchmark before actual release. Goalactive;
other source/case/workload closure can continue.


## 2026-10-19 — Generated SDK fixture recovery source research

OfficialAdobeSDKpage nowlabels1.7.1build2768/Oct13, whereas qualifiedbinary is
2724v1single. Website mutable latest download is notexactoldsource restoration.
HEADgo/dng_sdk actual38da64 metadataonlyreturned403; no body/archive downloaded.
IMPORTANTCORRECTION: retainedmanifest source_sha256=15d505... hashes driver.cpp,
NOT SDKsource tree; confirmed current/predecessorbuild.py. Do notauthenticate
SDKarchive/tree with it. New JSON doc/sdk-generated-fixture-source-recovery-
review-v1-20261019.json records freshlstat/absence and exactresearchscope.
Preferred2724source/library recovery; alternative explicitlypinnedreviewednew
fixture-onlygenerator/newbytes+ancestry withsame6000x4000/all3codecs, preserved
validator, freshqualification. Neither source acquired/buildadmitted. Builder
default12→2compilerjobs, READMEcommands12/4→2; exact2724guard unchanged. AST
checkd73d1f/0, noSDK/compiler/payload. PhotoIOpriority unchanged; allownjobs/
resources0. Goalactive; authenticJXL/12states recovery stillopen, notPhoto gate.

Fresh8c8851/0 correction: SDK root DOESexist as survivingfive-subdirectory
skeleton. ExactReadMe/license/dng_host.h/JXLCMakeLists allABSENT. Missingusable
source is not missingdirectory; recordcurrentmetadata ratherthanoldshorthand.


## 2026-10-19 — Optional Adobe policy cases source-bound to current evidence

New doc/sol-validation-policy-final-map-20261019.md maps elevenexact warning/
cancel/inspection/mutation/require/offcases percompiler. Fresh audit5cab47/0
and saved JSONchecks match329production+212linkedsource+5testpins/compiler,
8savedartifactpins and22individualcaseloghashes. Originalactual59806/68e562/0
unchanged; no newhelpers/native/SDK/Photo/IO. Missingrawdigest maypermitstructure/
decode but remainsMISSING, notdigestvalid. Warn neverrelaxes candidate/tool
change, cancellation/abort orwarningprinterfailure. RealSDK negative findings/
reuse-resume-merge pathmapping remainsseparate/open. Receiptindex doc/sol-
validation-policy-final-bindings-20261019.json. Photo49291bulkprioritycontinues;
noownedresources, goalactive. Next exactreceivingpath/negative matrix source
readiness or filesystemcasebindings; no bulk/native dispatch.
