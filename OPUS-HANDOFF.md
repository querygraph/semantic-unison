# Unison implementation handoff

## Latest namespace successor — 2026-10-17

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
