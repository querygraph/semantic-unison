# Sol implementation handoff: clone-aware Unison, DNG semantics, and OxCaml

**Status:** Implementation started with Astra, 2026-10-12. The user switched to Sol xhigh on 2026-10-13; the handoff has been reviewed and continuation is active. Keep this file current as code and evidence change. The architecture below is a contract, not a claim that every milestone is implemented. No production photos have been changed or deployment performed.

## Current checkpoint — 2026-10-15

PhotoV45 actualclosed/released. Canonical lock-only [fresh v4 request](doc/shared-physical-io-canonical-probe-request-v4.json)
prepared after verifying ALLv3source pins unchanged and priorworkspaceabsent.
Driver/backend/limits unchanged; NEWworkspace+admissionpath prevents expired
241da556reuse. Actualpriorguard2df62f/1 createdNOprobe/IOlock/CPUtokens.
Currentv4source-onlyNOTadmitted/dispatched; no resourcehold or auto-successor.

Actual [private-tag local clone controls](tests/qualification/private-tag-local-source-clone-actual-20261016.json)
PASS/CLOSED:8cases(stock/Ox×classicLE/BE×cloneoff/auto),24actualCLIwait0,
exactmetadatachangedoutput/priorreceiverinode preserved/no-opFIVEstable. Owner81876
actuald5cea4/0/group81879reaped0/othersabsent/tokens00..07closed. Source review
corrected initialtest routing errors: cloneoff bypassessemantic; auto localAPFS
whole-sourceclone wins BEFOREsemantic inspection, independentofopaque50740.
No receiverbasisfallback/semanticeligibility proof, no Photo/privatecamera/SDK/
compiler/physicalIO/timing claim. Failedtestassumptions andclosures preserved.
`private-dng-local-clone` manualtarget added; puremapping/budgetbbd2f5/0closed.
Transport-separated fallback remains a distinct nextcoretest; expiredcanonical
admission remainsunstarted, freshscheduling requestedqueue01a1425e-57a3.

Canonicalprobev3 admission241da556 expired before execution: [guard receipt](tests/qualification/canonical-io-probe-v3-expired-unstarted-20261016.json)
actual2df62f/1/no session, deadlineassertion beforeexec. Workspace absent, no
START/worker/contender/IOlock/CPUtokens; no canonical test actually ran. Root
notified queue01a1425d-0e61; zeroUnisonresourcesheld, no reuse/autorefresh.
Frozenv3source75401072 unchanged; fresh separate scheduling needed ifresumed.

The realcamera tag50740 gap now has a [spec/source-backed profile-successor prerequisite](doc/dng-private-data-next-profile.md):
new original `DngPrivateData` Adobe/MakN framing module, NOT activated in profiles0/1.
[Stock/Ox47checks each](tests/qualification/dng-private-framing-actual-20261016.json)
manualtarget actuala4a593/0 CLOSED/group80040reaped0/othersabsent/CPU00..07closed;
entrypoint controls1f3a05/0 CLOSED. Strict-docstring/testwarnings in earlier runs
fixed with failures preserved. Bounded64MiB/256section framing recognizes only
knownheaders; virtual64MiB block reads20headerbytes/no body. Embedded maker
self-containment still needs separate closed-reference policy before newprofile
registration; no source-private/camera payload reread/SDK/native/canonicalIO.
This is groundwork for real DNG coverage, NOT camera semantic eligibility or
whole-goalcompletion. Currentcamera50740 remains ordinary exactfallback.

[Crossed privateDA retirement reconciliation](tests/qualification/private-dng-crossed-retirement-reconciliation-20261016.json):
actualSTART1792113844.2988029 under77ea9eeb/owner77296/c15ad5/0 preceded
Rootretirement1792113887.3426728. Later ROOT_RETIRED_UNEXERCISED marker preserved
unchanged as crossed observation; actual one-use execution/closure is not undone.
Root sent exact correction receipts; no replay/newadmission/resourcehold. Current
canonicalprobe isv3/backendcombined-failurefix736cac5, oldv2deferhistorical.

Combined IOclose failures fixed in source successor: UnresolvedIOOwnership carries
ALLuncertainFD pre-close identities plus known-open FDs/original cause, even ordinary
refusal+directoryclose or rollbackclose+directoryclose. No post-uncertain fstat/numeric
retry. [12disposable+4inert controls](tests/qualification/shared-io-combined-failure-successor-actual-20261016.json)
9ae1a3/0+d1573a/0 CLOSED/groupsreaped/tokens00..07closed. Inherited-holder test
now records explicit actualREADY→parentcopytransfer(child_settled=false)→actualwait0,
never fabricated settlement while live. Canonical [probe v3](doc/shared-physical-io-canonical-qualification-plan-v3.json)
keeps ALLparent FD copies until group settlement; [consumer v2](doc/shared-physical-io-consumer-contract-v2.json)
pins updated backend/unknown-log carrier. Earlier source plans remain immutable
historical/unstarted; v3 needs exact Root admission before any canonical IOtest.
No canonical IO lock, DNG/SDK/Adobe/payload operation or new pool created.

Namespace reconciliation is explicit in immutable [proposal v3](doc/shared-physical-io-proposal-v3.json):
adopt Root io-lanes-v1/manifestf7b55398/directory307225492/barrier307225493 ONLY.
Alternate v2 physical-io-lanes-v1 suggestion is superseded and MUST NOT be created.
Backend/consumer contract already pinned actual existing namespace; canonical
qualification remains outstanding, EX_GLOBAL_ONLY/no lanes. Root provisioning
is not a runtime grant, and completed manual privateDAcontrol is not IO backend
qualification. Topology freshness contract remains separate source-only review.

ACTUAL first real-camera private DA [clone/inspection control](tests/qualification/private-dng-clone-inspection-actual-20261016.json)
CLOSED under explicit one-use manual IO admission77ea9eeb/plan c29d92ec. Owner77296
actualinitialterminalc15ad5/0/no session; worker77297reaped0/othersabsent, stock
wrapper77298wait0 thenOx77302wait0, CPU00..07closed/unresolvedabsent. Clone
193851848B distinctinode307228717/0400/nlink1 hashes1a4f578e (sole cloneSHApass),
source FIVE/mode/nlink unchanged. BOTH inspectors return identical UNSUPPORTED
TIFFtag50740 opaque/privategraph. Integrity+crosscompileragreement PASS, camera
semantic eligibility NOTqualified; exact ordinary fallback remains required. No
inspector fullhash claim on unsupported result, no receiving/SDK/Adobe/pixels/
publication/sharedblock measurement. Admission consumed, no retries/successors.
Canonical IO probe still unexecuted; manual window does not qualify backend.

The canonical EX_GLOBAL lock-only [probe v2](doc/shared-physical-io-canonical-qualification-plan-v2.json)
now has exact source/interpreter/command/workspace pins. Parent retains IO+CPU
FDs through group settlement; one fresh independent contender must busy before
CPU entry; after actual settlement/close, one fresh whole bundle reacquires.
This replaces v1 canonical inheritance idea with retained-parent bounded ownership;
disposable inheritance remains qualified separately, not newly canonical.
[Four inert admission controls](tests/qualification/canonical-io-probe-inert-controls-actual-20261016.json)
86540f/0 CLOSED/tokens00..07closed; no canonical IO lock opened. Root source/budget
ACK naming older privateDNGbe25 is NOT admission to currentc29 executor; current
ancestry2450B/2345ed50 pin and uninstrumented8GiB acceptance retained.
Receipt-name correction:87b83d62... identifies READONLY-COPY-IDENTITY.json, NOT
SOURCE-COPY-ANCESTRY.json. Earlier ancestry2449B observation has no historical
hash restated or inferred. Current SOURCE-COPYb2e3b13a/job652e9110 pins remain
as supplied; this wording correction adds no test/payload gate or runtime grant.
Payload executor IO integration/phase-deadline successor remains next after
actual canonical qualification. No source payload/SDK/native access.

Root provisioned the SOLE actual `io-lanes-v1` namespace/barrier, manifestSHA
f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636,
EX_GLOBAL_ONLY/no device lanes. The [joint consumer contract](doc/shared-physical-io-consumer-contract-v1.json)
explicitly adopts this namespace; later v2 physical-io-lanes path suggestion is
unprovisioned/historical, not a second pool. New `tests/shared_io_pool.py` backend
opens existing pinned files only, full NB IO→CPU rollback, close-only/unknown
retention; no topology/nativeUI hook/production dispatcher integration.
[Ten disposable lifecycle controls](tests/qualification/shared-io-disposable-controls-actual-20261016.json)
01e671/0 CLOSED under00..07, group reaped/othersabsent/tokensclosed: independent
child contention, inheritance, lateCPU rollback, replacement/missing/alias refusals
and close-uncertainty injection. No canonical IO file opened.
[Five-case canonical qualification plan](doc/shared-physical-io-canonical-qualification-plan-v1.json)
prepared, NOT admitted/started; exact driver/command still needs freeze/review.
Manifest provisioning is not payload or SDK permission.

Joint physical-IO [source successor v2](doc/shared-physical-io-proposal-v2.json)
uses Root-requested `physical-io-lanes-v1` plus proposed Root workspace manifest;
no pool provisioned. IO→CPU→existing native/UI full nonblocking rollback, stable
physical IDs/fresh oldest observation/mount+boot/change refusal are required.
[Actual six metadata commands](tests/qualification/topology-metadata-actual-20261016.json)
owner75007/session2715/7e617c/0 CLOSED:398869B bounded raw diskutil/ioreg output,
all direct waits0/group75008reaped0/othersabsent/tokens00..07closed. QuasarUUID
matches; TenHFS+ observed. Physical leaves/provider remain UNQUALIFIED, so no
disjoint-device claim; global fallback/refusal only. No media/DNG/SDK/nativePhoto
payload, pool creation, dispatcher integration claim or private-DNG IO grant.

The private DA control now has an exact [v2 command/source plan](doc/dng-private-copy-plan-v2.json)
and `tests/private_dng_copy.py` owner/worker, still NOT payload-admitted. Requires
fresh Root disk-IO receipt bound to plan/command/deadline and explicit acceptance
of uninstrumented inspector budget. Clone-only/no fallback, source FIVE+0400+nlink1
unchanged, distinct private inode+historical SHA, serial prebuilt stock/Ox; no SDK.
Requested logical payload reads8783786440B (193851848 clonehash +8GiB inspectors),
600s worker/group; preflight outside ceiling, source userspace reads0, physical
clone/IO bytes unknown. [Five metadata-only refusals](tests/qualification/private-dng-plan-controls-actual-20261016.json)
2ec280/0 PASS/CLOSED under00..07, group reaped/tokens closed. No DNG opened,
clonefile/native path not yet runtime-qualified, no receiving/publication claim.

Photo supplied one private DA DNG candidate as metadata-only handoff. The
[bounded clone/inspection plan](doc/dng-private-copy-plan-v1.json) pins ancestry,
source identity and an exact fresh private destination. Preparation verified only
three metadata receipt pins; no DNG payload opened. Clone-only/no copy fallback,
destination SHA verification, sequential stock/Ox observations, source preservation
and explicit IO coordination are required. Inspector read budget is a conservative
request, not an instrumented syscall cap; executor/IO admission remain pending.
No receiving, SDK, pixel or production qualification is inferred.

Physical IO coordination now has a concrete [source protocol](doc/shared-physical-io.md)
and pure planner. Known jobs require sharedglobalbarrier+exclusive complete
physical-member union; unknown/changed/unqualified topology requires EXCLUSIVE
samebarrier, preventing false independence. IOthenCPU nonblocking wholebundle
rollback/retainedunknown lifecycle proposed; no peer-dependent RPC waits while
holding a per-phase IOlease. [Ten pure controls](tests/qualification/shared-io-source-ready-20261016.json)
fb8786/0 PASS/CLOSED under00..07; sourcepinsunchanged/groupreaped/tokensclosed.
No device discovery, liveIOpool, kernelIOlocking, SDK/Photo payload or native
operation. Jointnamespace/manifest and lifecycle/topology qualification remain
pending; existing productionIoAdmission is still endpoint-localst_dev only.
CPUdispatcher already qualified8da1cc6; user/Root's bothV9shared6 closures do not
imply OSthread/RSS/physicalIO/fullrun qualification or a UnisonSDK grant.


Actual [stock/Ox reused-inspector synthetic pair](tests/qualification/inspector-reuse-synthetic-actual-20261016.json)
PASSED/CLOSED: completed parentterminals407ea5/0 and99b987/0/no sessions,
strict containing groups reaped0/othermembersabsent/sourcepinsunchanged,
canonical00..07closed. Both prebuilt inspectors executed once without compiler
lookup/rebuild. Identical reports for independent256B DNGgoldens match16Bpacket,
full/complementhashes, editable region and SDR199B/SDE279Bsizes. No actual
receiving/publication or realcamera/validXML claim; synthetic packet observation
correctly says unsupported XMP root while exact-byte classification remains valid.
No SDK/Adobe/Photo data. Root received closure/candidate reminder queue01a14230-15c9;
no permission to open Photo-owned copies was inferred.


Reusable inspection now has `--use-build` and the owned `inspect-file` target:
checks bounded local build receipt, current19-file kernel source pins, private
workspace/binary binding and binary SHA before forwarding arguments, with no
compiler lookup/rebuild. [Eight inert-artifact methods and shared command controls](tests/qualification/inspector-reuse-controls-actual-20261016.json)
PASS/CLOSED: finalparentterminals b07ee8/0 and218c68/0, tokens00..07closed;
earlier2ba30f/0+d247a2/0 runs retained. Final target/driver/common source pins
were recorded and rechecked unchanged. Execution was
mocked; no real inspector, SDK/Adobe or Photo payload was invoked. This is API/
artifact-control qualification only. Real-copy candidate/ancestry/IO coordination
and actual receiving remain pending; no new native-Photo grant inferred from
Root's completed DA recognition. Trusted local receipts are not peer-code trust.


A [twelve-row acceptance scope audit](doc/acceptance-matrix-audit.md) now maps
all required matrix categories to40 pinned supporting receipt references.
Every row remains PARTIALLY_QUALIFIED. This is existing-document/source review,
not new runtime execution, source-snapshot parity revalidation, independent
implementation review or whole-goal completion. It keeps real-camera/SDK,
power-loss/abrupt-owner, hardmemory/physicalIO and platform gaps explicit, and
avoids promoting intermediate producer/publication receipts to newer scopes.
No Photo/Adobe/payload/test dispatch during Root's shared native slot.


Shared owner startup additionally refuses unsupported Python ownership primitives
before pool access, avoiding a pointless retained grant when the interpreter
cannot supervise anything. [Actual pure guard controls](tests/qualification/shared-owner-preflight-actual-20261016.json)
41ad96/0 pass with compiler/inspector/SDK activity0. Runtime unknown-outcome
retention remains unchanged. No whole-machine allocation or new Photo authority.


Real-camera copy-only qualification preparation found/fixed a usable-tool bug:
the standalone inspector build omitted xmpMerge despite current SemanticDelta's
dependency. New retained `--build-only --report` and shared `inspect-stock`/
`inspect-ox` entrypoints compile once without opening an input. [Both compiler
builds](tests/qualification/inspector-build-only-actual-20261016.json) PASS/CLOSED:
stock55065/dc8308/0, Ox36559/52457c/0, allgroups/tokens00..07closed; onecompiler
perbuild, inspector executions0. [Pure command controls](tests/qualification/inspector-command-controls-actual-20261016.json)
ac6dc7/0 pass, including pre-workspace/input refusals. No Photo/Adobe/SDK/payload
access; Root notified queue01a1421e-e92c. Requested existing verified privatecopy
candidate/ancestry and later IO coordination from Photo queue01a1421b-047e; no
payload authorization inferred or read performed. Real-camera eligibility,
exact receiving and SDK validation remain distinct pending gates.


Latest [standing8 shared functional qualification](tests/qualification/shared-functional-actual-20261016.json)
PASSED/CLOSED: actualtool15884/672587/exit0/no session,18rows54CLI, stock/Ox
ordinary/receiver-clone/semantic with workers1/2/3. Two private2MiB files perrow;
maximum3+3+2=8. All108 client/supervisor strict group censuses and54server/pump
receipts passed; exactoutput/basis/noop/cleanup preserved. Runner63782 actually
reaped0 after independent server audit; canonical00..07 closed, Photo08..15
untouched. Pure budget/receipt controls b93c2e/0+23b261/0 passed, including refusal
of malformed strict census before wait4 and separation from timed audit. Root
notified queue01a14216-e221. This closes the shared-sync wiring gap in the earlier
checkpoint below; no quiet timing, hardCPU/RSS, physical IO lane or production
corpus claim. Frozen timing series unchanged. Next goal work can use the ordinary
standing lane; SDK/Photo native ownership remains separate.


Shared entry points now own canonical Unison tokens for build-only and pure
parser controls. [Actual inheritance/dispatcher qualification](tests/qualification/shared-entrypoints-actual-20261016.json):
final ten disposable controls PASS (including child-inherited lock retention and
receipt-write failure retention); real shared parser and command-budget controls
PASS; stock Make build-only with jobs2 PASS, owner57789/30f8d3/exit0/no session.
All owned groups were observed without other members before actual wait4; all
tokens closed. Photo08..15 untouched; Root notified queue01a14211-f272. No built
Unison executable or Adobe invoked. Shared sync remains explicitly unconnected:
its separately-sessioned servers need independent closure receipts before token
release. Physical IO lanes/memory and shared performance remain unqualified.
`SHARED_CPU_CREDITS=8 make -f tests/Makefile stock-build` now uses retained
ownership (STOCK_PREFIX required); build-only and parser scopes only.


Standing8/8 transition: [eight disposable-pool controls](tests/qualification/shared-pool-controls-actual-20261016.json)
now PASSED/CLOSED under actual canonical Unison00..07 ownership. Owner61132,
child61134, actual tool terminal3e0f5f/exit0/no session; child group cleanup
preceded wait4 and token closure. Tests cover late-token contention rollback,
unknown settlement retention, indeterminate-close nonretry, directory-close
failure retention, replacement refusal and unpinned-policy refusal. Photo was
notified through parent queue01a1420e-5278. This supersedes the untested status
of the earlier primitive source preparation below. General build/sync dispatcher,
inherited-child contention and memory/physical-device IO qualification remain
pending. No new benchmark, SDK or Lightroom work ran.


Latest [frozen Oxworker8 part5](bench/sync/results/warm512-frozen-part5-actual-return-20261015.json)
PASSED/CLOSED: actualowner52232/2b05a9/exit0/no session; aggregate51654
reaped0/others absent in2070.618s, independent18rows54CLI client/server/supervisor
auditPASS, SDKhelpers0/unresolved empty/fixturesremoved. All14execution21runner
pins unchanged and frozenHEADclean. Ordinary/clone/semantic medians
36.346/35.664/34.684s; semantic about4.6% below ordinary here, no broadcompiler
speedup claim. Five source-activity disclosures pinned (bothowners); exactrow
impact unknown/no absolutequiet timing. Part3 stays FAILED/INCOMPLETE and
part0e311d5f6 remains mandatory; no complete six-part claim. Root sent actual
closure;18released on Unison side, no benchmark/native successor. Next is
post-slot source/token qualification under standing8/8, not another18hold.

Exact authoritative shared policy now Rootv3 SHA1dbe12eb: standing8/8/2,
Unison00..07/Photo08..15/16..17idle, memory32/64/32GiB. Both priorCPU splits
are historical. [Token primitive source preparation](tests/qualification/shared-token-source-preparation-20261015.json)
originally added tests/shared_cpu_pool.py as untested/unconnected source: pinned bounded
manifest, existingprivateinode-boundpool only, nonblocking ascending explicit
set, partial-acquisition close, no LOCK_UN or automaticerrorunlock. Unknown
settlement/close retainsowner; release consumes caller's actualsettlement
attestation, does not prove it. Livepool neveropened/locked, no test/build/native.
Sourceworkdisclosed in currentpart5 workspace; frozenrun remains same18grant,
livehandle52232. Postclosure: source/refusal controls, realtwo-owner/inheritance/
rollback/unknownlifecycle, dispatcherowner integration, worker3defaultsupport,
physicalIO/memory admission and sharedfunctional qualification. No capability
claim from tokenfile labels or source alone.

LATEST USER CPU agreement supersedes older proposals: equal8Unison/8Photo/2OS.
[Equal8 source preparation](tests/qualification/shared-equal8-source-integration-20261015.json)
pins precedingRootv2 pool/lifecycle contract while explicitly superseding its
4/12CPU fields. Proposed stable token ranges0..7Unison/8..15Photo/16..17idle.
Manualshared ceiling8/compilerjobs<=2 plus2owner; new --shared-qualification
keeps workers1/2 perendpoint plus2owner(max6declared) inside8. Old functional
4credit accounting without owner budget is not silently claimed equivalent.
Updated source/refusal scripts NOT RUN during currentpart5; source/doc/queue work
only, disclosed in part5workspace. Currentfrozenpart5 remains LIVE52232 under
existing18grant, no shrink/preemption/redispatch. Commonpool FD integration,
IO/memory admission and finite contention/sharedruntime qualification still
pending; labels are not locks/OSCPU/RSS caps. No test/build/native process started.

Root shared-policy successor adopted as SOURCE ONLY:
`SHARED-DEVELOPMENT-RESOURCE-POLICY-v1.json` SHA2924dc03 (Unison10=4+4+2,
Photo6=4+2,OS2; memory32/64/32GiB). [Source integration](tests/qualification/shared-policy-v1-source-integration-20261015.json)
pins policy/commonexistingpool and changed dispatcher/run.py. New
`--orchestration-cpu-credits` counts owner/hash/transport INSIDE explicitloopback
budget; sharedmanual ceiling10/compilerjobs<=2 plus2owner, functional2+2+2.
Dry-run resourceplan names Unisontokenindexes0..9 and32GiB reservation while
explicitly flagging token acquisition/memory enforcement/deviceIO unresolved.
Two updated pure-control scripts are PREPARED NOT RUN during part5 quietslot.
No compiler/native/qualification executed; boundedsourcework disclosure saved
in part5workspace, unknown rowimpact/noabsolutequietclaim. Frozena6f0b695 untouched.
After actualclosure: source/refusal checks, exactsetinode-bound nonblocking
commonpool integration, partial-lock release, retainedowner failures, physicalIO
lanes/memoryadmission and finite sharedqualification. No runtimegrant inferred.

Shared entrypoint implementation: `SHARED_CPU_CREDITS=1..4` in tests/manual.py
admits compile-only stock-build/ox-build (defaultJOBS=min2,grant; reject excess),
reviewed pure targets and four-credit sync-functional (both endpoints counted).
Other test targets refuse this mode until budgeted; legacy nonshared behavior
unchanged. New build-only receipts do not replace build+selftest qualification.
[Four pure selections/seven refusals](tests/qualification/shared-entrypoints-pure-controls-20261015.json)
pass without compiler/child/output creation. Standing4/12+2 policy/commonpool ACK
still pending; this is a local command-budget guard, no global token or OS cap.
No runtime grant, Photo lease use, benchmark or build executed.

User scheduling correction: ordinary development should share Morrobay with
Photo, rather than make all progress depend on exclusive18 benchmarks.
[Shared-machine proposal](doc/shared-machine-policy.md) queued to Photo Root:
Unison4/Photo12/headroom2; serial Unison buildsJOBS2, functional loopback
workers1/2 with both endpoints counted within4. Pending standing ACK and common
token-pool integration, not an active grant or preemption of retained recovery.
Photo's inspected native adapter currently claims all18 even at small thread
targets; its owner must qualify reduced grants before concurrent rendering.
SDK/Lightroom/IO ownership remains separate. Shared timing is background-contended;
quiet peak-concurrency experiments stay exceptional, not a whole-goal blocker.

Prepared remaining [unrun frozen warm512 part5 request](bench/sync/results/warm512-frozen-part5-prepared-request-20261015.json):
OxCamlworker8/three modes/18rows54CLI, proposed18quietcredits/7200s. Fresh clean
a6f0b695/14execution21runner/evidence pins checked; workspace/allocation/output
absent. Queued for LATER Root scheduling after actual Photo recovery closure;
**unallocated/unstarted**, no release inferred from source preparation. Passed
part4 acceptance pinned; failedpart3 and brew/review/part0e311d5f6 caveats stay
preserved. Frozen200ms remains unchanged, no policy substitution/retry/fullmatrix
claim. Photo retains its own current recovery window; no Unison job or credits.

Latest [frozen Oxworker6 part4](bench/sync/results/warm512-frozen-part4-actual-return-20261015.json)
PASSED/CLOSED: owner57036/f228d4/exit0/no session; aggregate30613 reaped0/others
absent in2082.230s, independent18rows/54CLI client/server/supervisor auditPASS,
SDKhelpers0/unresolved empty. All14execution/21runner hashes unchanged, frozen
200ms policy retained. Ordinary/clone/semantic medians36.490/35.854/35.019s;
semantic about4% below ordinary here, but slightly above stockworker6's34.209s
separate-slot result, no compiler-speedup claim. Resource closure sent to Root,
18released on Unison side. Part3 remains failed/incomplete; part5 unrun, no
full six-part/clean-cohort/physicalIO qualification. No successor allocated.

Consumed [frozen warm512 part4 request](bench/sync/results/warm512-frozen-part4-prepared-request-20261015.json):
OxCamlworker6/three modes/18rows54CLI, proposed18quietcredits/7200s. Source
a6f0b695 and14execution/21runner hashes rechecked; workspace/allocation/output
absent at preparation. Subsequently allocated/executed once as recorded above. Part3
remains failed/incomplete with resource-only acceptance and brew/review caveats;
no retry/replacement or full-six-part claim. Frozen cohort still uses200ms
EOF grace; separately qualified main2s successor is not silently substituted.
Future late settlement must still fail closed. Part0e311d5f6 remains mandatory.
Photo's V36 scope is separate and genuinely closed; its release is not a Unison
runtime allocation. No compiler/SDK/Photo/benchmark process runs here.

Root independently accepted the single settlement lifecycle run, all12postpins
and resource closure; onecredit released. [Immutable allocation reconciliation](bench/sync/results/native-settlement-allocation-reconciliation-20261015.json)
keeps actual dispatch's v1 reference distinct from separately published v2
allocation and v2-named Root acceptance. Command/workspace/limits were identical;
all12superset hashes checked, one execution only. Original sealed return stays
unchanged; no synchronized cross-session creation/delivery ordering is inferred.
No false claim of a separately observed v2 dispatch, replay or new hold. Photo
V27 pending; Unison successors remain unallocated.

Actual [settlement lifecycle return](bench/sync/results/native-settlement-lifecycle-actual-return-20261015.json)
PASSED/CLOSED: owner3736/16df12/exit0/no session; aggregate1705 reaped0/others
absent in2.387s. Six direct original Python children prove delayed normal exit,
legacy short-grace refusal, fault TERM, TERM-ignore KILL, nonzero exit and expired
normal budget; each independently ECHILD. Actual proxy delayed echo also passes
client/supervisor/group/server/pump closure. Seven cases/nine original children,
no unresolved markers, all12source pins unchanged. Fresh allocation10b7a29a
explicitly authorized the earlier v1 command; v2's identical command/limits and
two extra transitive pins were additionally checked. Root sent actual closure,
onecredit released on Unison side. No benchmark/SDK/Photo/compiler or automatic
successor. This qualifies the harness lifecycle successor, not historical part3
cause, its missing rows or throughput. Frozen old cohort remains untouched.

Prepared [settlement lifecycle v2 request](bench/sync/results/native-settlement-lifecycle-request-v2-20261015.json)
for seven finite original-Python cases: six direct child policies plus the actual
proxy delayed-echo client/server/supervisor path. OneCPU/45s retained aggregate
(maximum60), no compiler/SDK/Unison binary/Photo/timing. Exact command and12
transitive source pins queued to Root, then executed under the fresh explicit
allocation recorded above. Earlier preparation was in-memory syntax only. V1 was
withdrawn unstarted because two transitive imports were missing from its pin
inventory; latest explicit allocation subsequently authorized that same command
with all12pins freshly checked. V2 leaves command/cases/limits unchanged. Fake children cannot prove
historical part3 cause or restore its incomplete matrix; no retry authorized.

Post-failure source successor: proxy normal EOF settlement now allows up to2s
capped by the remaining protocol deadline, rather than sharing the200ms TERM
grace. Known faults still signal TERM immediately; the old NativeChild default
is unchanged. Timeout policy and actual settlement wall time enter receipts.
[Six pure mocked policy controls](bench/sync/results/native-settlement-policy-source-controls-20261015.json)
pass, with no real child/signal/compiler/native invocation. Actual delayed-exit,
hung/fault and caller-settlement controls remain required before new timing.
This is main-source-only: frozen a6f0b69514execution/21runner pins rechecked
unchanged, failed part3 raw/marker retained. It neither proves the failure's
cause nor repairs/replays part3. Root independently accepted failed-part3
resource closure; all18released, no successor runtime allocated.

Latest runtime: [frozen Oxworker1 part3 FAILED/INCOMPLETE](bench/sync/results/warm512-frozen-part3-failed-return-20261015.json).
Actual owner76640/df5ca2/exit1/no session; aggregate88119 reaped1/others absent
in2113.568s. Sixteen completed rows pass exactness/basis/noop (48CLI). The
next seed's client/server returned0 but supervisor returned70: server failed
to settle within post-output-EOF grace; retained server cancellation reason
is preserved, server later reaped0 without hard kill. Independent49CLI audit
proves all clients/supervisors/servers reaped and input pumps joined. Fixtures
removed. Conservative EXTERNAL-HELPERS-UNRESOLVED expected_calls0 marker stays
preserved; actual resource evidence is separate from that generic failed-worker
marker and from functional success. Root sent actual closure,18released on
Unison side; no retry/successor or completed-part claim. Homebrew neomutt/make
activity observed during timing and reviewer-stop timing disclosed; no causal
claim about the failure, no clean timing, final medians or sample replacement.

Consumed preparation: [frozen warm512 part3](bench/sync/results/warm512-frozen-part3-prepared-request-20261015.json),
the first OxCaml512 partition (worker1/three modes/18rows54CLI). Fresh clean
detached a6f0b695/14execution+21runner hashes and accepted part2 predecessor
verified; workspace/allocation/output absent. Queued to Photo Root for a fresh
18credit/7200s scheduling decision, then admitted and executed once as above. Root independently
accepted part2 actual closure and sealed return; all18credits are released.
No old admission reuse, SDK/compiler dispatch or automatic successor. Mandatory
part0e311d5f6 timing disclosure remains with the series.

Latest runtime: [frozen warm512 part2](bench/sync/results/warm512-frozen-part2-actual-return-20261015.json)
PASSED/CLOSED, actual owner55681/d32adc/exit0/no session; aggregate81032
reaped/others absent in2052.876s. Independent18row/54CLI client/server/supervisor
audit passes, zero SDK helpers expected, unresolved empty. Source14/runner21
hashes remain matched to detached a6f0b695. Stockworker8 ordinary/clone/semantic
medians37.028/36.299/34.232s; semantic6/8worker medians are nearly identical
for four files. Parts0..2 complete the stock half only; Ox512/full six-part,
physical I/O and broader performance remain open. Mandatory part0e311d5f6
timing disclosure persists. Closure queued to Photo Root;18credits released
on Unison side, no successor allocated or started.

Consumed runtime preparation: [frozen warm512 part2 request](bench/sync/results/warm512-frozen-part2-prepared-request-20261015.json)
pins stockworker8/three modes/18rows54CLI, the same detached a6f0b695 cohort,
and independently accepted part1 predecessor. All14execution/21runner hashes
rechecked; unique workspace/allocation/output absent. Request queued to Photo
Root for scheduling and subsequently admitted/executed once as recorded above;
no SDK/compiler/native job remains running. Do not replay this request.
Goal reactivated by user; full qualification remains incomplete. Part1 actual
closure and sealed return are now independently accepted by Photo Root, with
all18credits released; no stale resource hold remains.

Timing correction: warm512 part0 has a disclosed59.49s CPU/disk overlap.
Functional/ownership checks pass, but it is not an uncontaminated quiet timing
run. [Addendum](bench/sync/results/warm512-part0-timing-overlap-addendum-20261015.json)
flags measured1 semantic definitely and measured1 receiver-clone tail possibly.
All original samples/return hashes and medians remain unchanged; no rerun.

Latest runtime: [frozen warm512 part1](bench/sync/results/warm512-frozen-part1-actual-return-20261015.json)
PASSED/CLOSED, actual owner89135/96b778/0,18rows/54sync invocations, aggregate69503
reaped/others absent in2059.198s; no unresolved markers. All18credits released on
the Unison side; sealed actual closure queued to Photo Root. Exact detached
a6f0b695 source and all14execution/21runner pins remained unchanged. Stockworker6
ordinary/clone/semantic medians37.027/36.344/34.209s. This completes parts0 and1,
not the full six-part512MiB stock/Ox matrix. Part0's timing addendum remains
mandatory; do not claim a clean full cohort. No successor allocated or started.

Current stock/Ox full Make+selftests,41 helper groups per compiler and five
receiving diagnostic cases per compiler pass. Generic APFS/SDE/DNG/optional
validator implementation is present; the full goal is NOT complete. The latest
[current qualification index](doc/current-qualification-status.md) lists remaining
corpus, native-resource, acceptance-matrix and performance qualification.

The separately admitted [six-call live SDK merge](tests/qualification/sdk-live-merge-v1-actual-return-20261015.json)
now PASSED/CLOSED: actual owner43830/699a51/0,9CLI runs/six SDK validations,
stock-client/Ox-server,32.486s aggregate. Independent retained readback passes;
Root independent acceptance5b9235bc is adopted. Admission is consumed, not reusable.
All Unison allocations are closed. The newly user-authorized/Root-allocated
[warm128 v5 benchmark](bench/sync/results/warm-128-v5-actual-return-20261015.json)
PASSED/CLOSED: actual owner34823/c78138/0,18warmups+90measured rows,324CLI
settlements and aggregate12254 reaped in3426.064s. All18 credits released;
no successor/SDK/Photo operation follows. At8workers, Ox semantic median9.212s
versus ordinary9.609s; semantic writes12,288 logical bytes across four128MiB
files. Physical writes, broader corpus/platform and other benchmark sizes remain
unqualified. See [measurement interpretation](bench/sync/README.md).
Earlier entries below are
historical evidence and must not override a newer pinned checkpoint.

Finite lifecycle qualification is now [PASSED/CLOSED](bench/sync/results/bounded-lifecycle-qualification-20261015.json):
actual owner46880/86b330/0, eight fake-child/worker cases, whole wrapper6.528s
within the one-credit/60s allocation. All actual children/workers were reaped;
no active ownership remains. Expected negative-fixture markers are preserved
and scoped in the receipt. A wrapper syntax preflight failed before any test
was dispatched; the corrected wrapper ran the admitted cases once.
This does not repair the missing historical interrupted-client receipt for
stopped benchmark60597. Benchmark v4 remains UNADMITTED; no compiler, SDK,
Photo, timing run or successor is authorized by this completed allocation.

The previously source-only [warm128 v5 request](bench/sync/results/warm-128-v5-prepared-request-20261015.json)
now binds fresh plan/source/build/binary pins, first128MiB x4 only, and the
7200s aggregate owner plus324 CLI/server settlement audit. The plan references
actual fake-lifecycle evidence separately from full-batch runtime qualification.
It subsequently ran once under explicit user authorization and fresh Root allocation;
the actual result is linked above. The prepared plan itself remains immutable.
Preparing that plan performed only file hashing/JSON work, not builds or tests.

## Live implementation handoff

* Exact512MiB cohort source retained (2026-10-15): created/locked detached
  worktree `/private/tmp/unison-warm512-source-a6f0b695` at the actual part0
  runtime revisiona6f0b695. All21 runner hashes match the captured manifest,
  tracked source is clean, and stock/Ox receipt/source checks pass without
  invoking binaries/compilers. [Snapshot record](bench/sync/results/warm512-source-snapshot-20261015.json).
  This preserves strict cross-part provenance despite report commits in the
  main checkout; do not weaken repository/runner comparisons or replay part0.
  Fresh [part1 request](bench/sync/results/warm512-frozen-part1-prepared-request-20261015.json)
  uses that retained source/plan, stockworker6/three modes/18rows/54syncCLI only.
  It is UNALLOCATED/UNSTARTED, no credits held or successor automatically run.
  Part0's timing contamination addendum is mandatory for any series publication.
  Worktree lock prevents accidental git removal, not edits; fresh byte checks
  remain necessary. Native scheduling still belongs to Photo Root.


* Timing overlap disclosure (2026-10-15): Root reported static disassembler54583
  active conservativelyUnix1792046929.4774537..1792046988.967324, output91,279,134B,
  owner57433/2b183a/143 closed. Preserved its pinned receipt and immutable
  [analysis addendum](bench/sync/results/warm512-part0-timing-overlap-addendum-20261015.json).
  Dated Unison logs show measured1 semantic seed propagation and early timed
  update inside that interval. Preceding measured1 receiver-clone update ended
  earlier, but its uninstrumented post-noop tail/next-fixture boundary could
  overlap, so it is conservatively flagged. Entire run's quiet-timing claim is
  withdrawn; possible cache carryover/impact magnitude unknown. All18 raw rows,
  five samples/mode, original hashes and summaries are preserved, no exclusions,
  retry or replacement. Resource closure/exactness remain passed and18released.
  Carry this sidecar with any future combined-series performance publication.

* Actual warm512 first part PASSED/CLOSED (2026-10-15): fresh allocationf9b954a2
  ran once, actual owner74730/c65a5b/exit0, aggregate52671 closed/reaped/others
  absent in2293.507s, no unresolved markers. All18rows/54 synchronization CLI
  receipts passed;18credits released and Root notified. [Raw data](bench/sync/results/warm-512MiB-4files-part0-20261015.json),
  [sealed return](bench/sync/results/warm512-v9-part0-actual-return-20261015.json).
  Stock worker1 medians: ordinary37.423s, clone36.700s, semantic69.659s.
  Semantic writes12,288 logical bytes across2GiB, but is slower sequentially.
  No parallel/Ox512MiB claim; other five parts and single2GiB transfer remain
  unrun. The old unallocated v9 notes below are superseded ONLY for this part;
  allocation consumed, no successor authorized. Preserve this part's exact
  repository/runner snapshot for subsequent separately scheduled parts so the
  strict full-series provenance audit can remain meaningful after report commits.


* Offline partition report command (2026-10-15): `merge_partitions.py` accepts
  six stable bounded regular JSON inputs and creates a new report exclusively.
  It verifies full108-row/324CLI accounting, recomputes summaries and records
  exact input hashes; it never invokes Unison or releases CPU/native ownership.
  Eight artifact refusals and historical positive reconstruction pass, including
  existing-output preservation, duplicate/missing/oversized/nonregular/changed
  inputs and malformed JSON. [Evidence](bench/sync/results/offline-partition-merge-controls-20261015.json).
  Actual parent-tool terminal and aggregate closures remain separately required
  for every runtime part. Pending v9 execution source pins/plan still verify;
  unused offline helper additions do not alter the controller dependency set.
  No partition started, no credits held, Photo migration scheduling respected.


* Allocated partition result binding (2026-10-15): the worker's completed
  result must now match its allocated partition index, workload dimensions and
  exact54CLI count. Previously independent part validity alone did not bind the
  declared result back to the selected index. Pure coverage passes35 refusals,
  including wrong-index/dimensions/count, plus existing parser/selection checks.
  [Evidence](bench/sync/results/partition-result-binding-pure-controls-20261015.json).
  Fresh v9 [first512MiB part request](bench/sync/results/warm512-v9-part0-prepared-request-20261015.json)
  binds final source/build/plan pins. It is UNALLOCATED/UNSTARTED and only covers
  stock worker1 across three modes; all six parts remain necessary for the full
  matrix. No new core/native/compiler/SDK/timing job or credits held. Photo's
  migration reservation has not been treated as released.


* Partition runner/controller wiring (2026-10-15): `run.py --partition0..5`
  selects one exact label/worker slice, three modes and all five repetitions.
  The bounded owner requires a fresh partition-specific allocation/state/index,
 54CLI limit and unique workspace; it never starts a successor. Full larger
  batches flagged beyond the planning ceiling require partition selection.
  Shared fixture dimension admission now allows2048MiB (previous512MiB limit
  contradicted that unexecuted plan), retaining8GiB corpus/TIFF32 bounds.
  Actual CLI parsing is checked through a mocked metadata boundary; six invalid
  CLI cases and17 selection/dimension/allocation refusals pass without native
  calls. Planner partition counts/unique outputs and historical whole/merge
  audits also pass. [Source qualification](bench/sync/results/partition-execution-source-qualification-20261015.json)
  pins fresh v8; no actual partition/2GiB transfer, SDK, compiler or benchmark
  ran. Photo's exclusive migration slot remains respected; no credits held.


* Partition accounting kernel (2026-10-15): six exact label/worker parts each
  cover all three modes, one warmup/five measured repetitions,18rows/54CLI.
  Pure merger reconstructs all108rows/324CLI only when every part, current
  provenance and every row settlement match; partials cannot pass full audit.
  Summaries are recomputed and per-window observations preserved. Historical
  readback plus26 refusal cases pass, and prior216CLI audit/14 refusal controls
  still pass. [Evidence](bench/sync/results/partition-accounting-pure-controls-20261015.json).
  Execution selection/owner/preparer wiring and actual per-part native closure
  remain pending; no new measurements or scheduling allocation. Source review
  also found runner max512MiB contradicts the unexecuted2048MiB plan; fix/test
  this admission before presenting that workload as executable. v7 is historical
  source preparation and will need fresh pins after partition wiring.


* Larger-workload duration planning (2026-10-15): pure planner controls pass
  after binding the actual3426.064s warm128 reference. Simple byte scaling
  estimates512MiB x4 at13704s and2048MiB x2 at27409s, beyond the current7200s
  owner ceiling. These are heuristics, not measured bounds. The
  [prepared v7 plan](bench/sync/results/larger-batch-duration-preparation-20261015.json)
  explicitly flags partition review; no larger run/allocation is requested or
  started. Next work must preserve all18 configurations/five repetitions/324CLI
  proof accounting across bounded parts rather than silently shrink the matrix.
  Source/build/binary pins were refreshed; pure checks invoked no compiler or
  benchmark. The completed128 batch and its consumed allocation stay immutable.


* Aggregate setup failure settlement (2026-10-15, SOURCE ONLY): preparation
  now includes both readiness-pipe acquisitions and stdout/stderr flush inside
  the pre-fork cleanup guard. Previously a second-pipe or flush exception could
  leak already acquired descriptors; a close failure could skip siblings and
  replace the original fork exception. Cleanup now attempts every acquired
  slot and rethrows the original exception. Six finite mocked acquisition,
  flush, fork and cleanup-failure regressions are prepared in
  `tests/sdk_container_receive/aggregate_setup_test.py` were left unexecuted
  during Photo's exclusive18 MOV repair. After actual release, all six mocks
  and the supported-interpreter plus ten capability-refusal controls passed
  (actual terminal062b40/exit0); [pure evidence](tests/qualification/aggregate-setup-pure-controls-20261015.json).
  No real test descriptor, worker, compiler, SDK, Photo or benchmark was invoked.
  Mock close attempts are not native FD/reap qualification. Earlier runtime
  evidence retains its historical source pins; future runs need current pins.

* Aggregate interpreter preflight (2026-10-15): source review found that direct
  `OwnedGroup.__new__` bypassed its constructor's waitid/WNOWAIT support check.
  The aggregate now checks retained observation/reap/session APIs before any
  pathname, marker, pipe or fork. Pure missing-capability controls demonstrate
  refusal before resource acquisition; no child, compiler, SDK, Photo or timing
  successor is invoked. The completed warm128 allocation remains consumed and
  its historical source pins unchanged. User-run `aggregate-preflight` target
  reproduces this check; supported API presence does not prove another platform.

* Manual lifecycle entry points (2026-10-15): added `interrupted-receipts` and
  `aggregate-lifecycle` to `tests/Makefile`/`tests/manual.py`, selecting the exact
  already-qualified scripts with literal argv and runner-owned workspaces.
  This is source preparation only; the new dispatcher routes have not been
  executed under the current successor hold. The underlying eight-case actual
  qualification remains pinned separately. No timing admission or replay.

* Acceptance audit refresh (2026-10-15): the detailed implementation audit now
  labels its October14 snapshot as historical and links superseding SDK live
  merge, typed whole-clone, cross-volume and lifecycle evidence. This closes
  stale descriptions, not broader camera/performance/platform gates. No timing
  allocation appeared in the scheduling readback; no successor was dispatched.

* Source-only usage review (2026-10-15): reviewed registry negotiation,
  exact/complement proof separation, clone-range prefix validation and physical
  CPU selection. No runtime qualification is added by this review. The
  [usage guide](doc/semantic-sync.md) now explains per-endpoint CPU budgets
  (two local peers do not share a machine-wide permit pool) and the implemented
  opt-in retained-group diagnostic, including unknown/unobserved outcomes.
  No core source, build, test or native dispatch changed; successor hold remains.

* Benchmark failure settlement (2026-10-14): each validation job now records
  its first observed error and cancels peers immediately, rather than waiting
  for an aggregate's ordered observation. BorrowedWork drains all submitted
  promises before closing descriptors/pool and reporting the first error.
  SIGTERM/SIGINT only set an atomic flag; the owner timer cancels helpers and
  an active batch deadline triggers the same settlement. Synthetic helpers
  exercise rejection beside a TERM-ignoring peer, deadline, signal and fresh
  success; no SDK was invoked. Draft SDK pilot coordination was withdrawn:
  fresh-fixture work is 13 SDK calls, and the whole fixture-plus-batch deadline
  remains to be implemented. No queue acceptance or earlier preview release
  authorizes native work. Photo ownership remains unchanged.
  Stock/Ox actual-object builds each pass five synthetic cases with all helper
  PIDs absent after return and unchanged inputs.
  [Settlement evidence](tests/adobe_bench_settlement/qualification.json),
  [withdrawal](tests/qualification/sdk-pilot-request-withdrawn-20261014.json).

* Real cross-volume filesystem checkpoint (2026-10-14): stock/Ox each pass six
  local CLI rows across a privately created HFS+ image and internal APFS roots:
  ordinary clone-auto/off and semantic DNG-auto in both directions. Exact bytes,
  old-hardlink preservation and no-op receiver inode/bytes pass all 12 rows.
  APFS ordinary receivers inherit 1,966,080/2,097,152 logical bytes; DNG-shaped
  edits select semantic materialization. HFS+ receiving declines cloning and
  completes ordinary exact fallback. The guarded local producer now emits its
  actual inherited-byte counter, previously available only on the legacy path.
  Unicode path handling passes; this is not broad case/property qualification.
  The owned image is detached and independently absent before completion.
  Both logical volumes share backing storage: no physical-device throughput,
  sharing, crash or mount-incarnation proof is claimed. No Photo/Adobe access.
  Fresh Make/Dune builds+selftests pass on stock/Ox. Independent retained-log
  readback records 3,072 logical semantic bytes/one write attempt from an
  8,192-byte packet, without physical-write or allocation proof.
  [Test and scope](tests/cross_volume/README.md),
  [evidence](tests/cross_volume/qualification.json).

* Native benchmark preparation correction (2026-10-14): Adobe-core benchmark
  dependencies now include the checked mailbox. OxCaml requires compiler-matched
  actual Make core objects, verified against snapshot/compiler/binary/source
  pins; build-only retains the executable/log and a separate build result.
  Stock and Ox builds pass without SDK linking, fixture generation, validation
  or benchmark execution. Default worker budgets are 1/6/18 under an explicit
  18-credit allowance. The coordination wait now precedes *all* SDK fixture and
  validation calls, with a deadline. An absent-marker actual wrapper control
  times out before fixtures; missing/mismatched production builds and oversized
  CPU budgets reject. A marker is caller CPU coordination, not Photo/Lightroom
  admission. SDK runtime/thread/resource/performance qualification remains open.
  [Instructions](bench/adobe/README.md),
  [build/control pins](bench/adobe/results/current-core-build-handoff-20261014.json).

* DNG backend admission integration (2026-10-14): the actual companion registers
  its caller-inclusive `adobevalidatorthreads` and optional endpoint-local
  `adobevalidatorworkspace` MiB estimate with the generic resource planner.
  Positive workspace or multi-lane declarations are pinned for the process;
  default one-lane/zero-estimate behavior preserves legacy policy toggles.
  Stock/Ox each pass eight real loopback cases, including before-stage oversized
  memory/CPU rejection, invalid declarations, off behavior and a two-lane
  directory helper under the 8 MiB budget. All fixture originals remain unchanged.
  This is core accounting with synthetic protocol helpers, not SDK thread/RSS
  compliance. Production v1 still requires one thread; experimental protocols
  remain unavailable. Fresh Make/Dune builds+selftests and all 21 existing
  receiving regressions pass on both compilers. Warn does not bypass an
  oversized resource declaration.
  [Contract](doc/backend-resource-interop-v0.md),
  [qualification](tests/dng_backend_resources/qualification.json).

* SDK object-cache correction (2026-10-14): builder object reuse now checks
  compiler/options/environment, compiler-discovered source/transitive/system
  header contents and object contents rather than modification times. Inputs
  changed during compilation reject the output; an interrupted/corrupt receipt
  cannot validate a partial object. Thirteen actual clang controls on owned
  original C pass, including restored timestamps, escaped dependency paths,
  changed flags, corrupt object/receipt, missing dependency file and retry.
  The actual current builder recompiles a changed transitive header while its
  exact previous function retains the stale object. This is build-component
  proof only: no SDK linking, initialization, validation or photo access occurred.
  JPEG XL CMake caching, SDK runtime and uncooperative-writer atomicity are not
  upgraded by this result.
  [Evidence](tests/native_object_cache/qualification.json).

* Local build/run separation (2026-10-14): `tests/build_snapshot.py` now supports
  Make or Dune and saves source/compiler/binary pins plus actual build/self-test
  exits in its retained snapshot. [Local commands](doc/local-build-and-tests.md)
  collect CLI, deterministic codec, sanitizer and separately chosen benchmark
  entry points. The current full directory receiving matrix passes stock/Ox,
  including missing-stage rejection and all ten CLI tree cases. No new fuzz,
  Adobe, native preview or performance campaign is implied.
  Fresh Make/Dune CLI builds+selftests pass on stock and OxCaml;
  [build/matrix evidence](tests/qualification/local-build-handoff-20261014.json)
  preserves the actual sources/outcomes and metadata-only builder revision.

* Native-helper sanitizer build handoff (2026-10-14): independent deterministic
  codec tests support `--sanitize address,undefined --build-only`. Both actual
  compilers build complete test executables; native object symbol readback
  verifies ASan/UBSan instrumentation and executable linkage resolves to the
  installed clang sanitizer runtime. Recovery is disabled. No sanitizer test
  executable was run in this checkpoint; runtime/negative-control qualification
  stays open. OCaml/runtime code remains unsanitized.
  [Run instructions](tests/semantic/conformance/README.md).

* Missing-stage admission correction (2026-10-14): the opt-in manifest-memory
  precheck converts an initial Unix `lstat` failure to `Util.Transient`, matching
  later tree inspection. The actual compiled participant passes absent-stage
  rejection before admission plus same-process success/rejection/cancellation/
  retry on stock/Ox, for both one-lane and two-lane backends. No helper runs and
  no credits remain held for the absent candidate.
  [Focused evidence](tests/validation_tree_limits/missing-staging-qualification.json).
  Fresh full Make CLI builds and self-tests pass on both compilers; the receipt
  pins each resulting binary and self-test log. Broader acceptance remains open.

* Parser test execution handoff (2026-10-14): a read-only synthetic AFL target
  and separate `--build-only` mode are available in
  [the test handoff](tests/semantic/fuzz/README.md). Stock instrumentation emits
  actual coverage; the five-second SDE preparation probe completed 907 executions
  and found 13 new corpus entries/123 edges, with no saved crashes/hangs. This
  preliminary result does not close malformed-input acceptance. OxCaml's
  compiler-selected target builds; no OxCaml campaign is claimed. Native C
  sanitizers, failure-oracle controls, sustained campaigns and the full profile
  matrix remain open. macOS settings are unchanged. Further automated campaigns
  were deferred after reported service access interruptions; the user requested
  a build/run separation to execute tests locally. The independent deterministic
  codec suite passes 127 cases/2,033 assertions on each installed compiler.
  No Adobe/Photo operations or production source changes in this checkpoint.

* Nested-backend workspace sizing (2026-10-14): admitted directory parallelism
  now divides the shared CPU budget by the largest selected backend's caller-
  inclusive lane declaration. For 18 cores this plans 18 one-lane, six three-
  lane or one 18-lane invocation; SDK runtime thread compliance remains separate.
  Stock/Ox each pass 17 declaration/resource controls and five compiled-backend
  receiving cases. A two-lane backend holds both permits using a single 7 MiB
  envelope under an 8 MiB cap. The exact previous CandidateValidation requests
  12 MiB and fails the designated oracle. Legacy and nested same-process
  success/rejection/cancellation/retry all settle their ledgers with unchanged
  originals. Make/Dune+selftests and the tree receiving matrix pass per compiler.
  [Successor pins](tests/validation_tree_limits/nested-workspaces-qualification.json).
  This is synthetic admission/permit proof, not actual SDK performance, thread
  compliance or full M4-V/M6 completion. No Adobe/Photo invocation.

* Estimated directory memory admission (2026-10-14): opt-in endpoint-local
  `validationtreememory` reserves two retained-manifest estimates and parallel
  per-file workspaces before enumeration. A local gate partitions held credits;
  children never acquire another global lease. Regular publication includes the
  two estimates even if validation is off, and budget changes require restart.
  Scans cap the retained estimate: 1,024 bytes per discovered entry plus eight
  times path/serialized property/symlink bytes. Stock/Ox pass 14 tree-boundary
  checks, 16 resource/declaration controls, ten actual tree receiving cases,
  one-parent compiled-backend accounting, two concurrent synthetic helpers,
  and same-process success/rejection/cancellation/retry with zero residual
  ledgers. Make/Dune+selftests and all 21 receiving regressions pass per compiler.
  [Contract](doc/validation-tree-limits.md),
  [successor pins](tests/validation_tree_limits/memory-qualification.json).
  Estimates do not enforce transient property/native/SDK allocation or RSS;
  directory pre-creation admission and actual experimental SDK runtime remain
  open. Zero preserves default behavior. No Adobe/Photo invocation or full
  M4-V/M6 completion is claimed.

* Receiving directory manifest controls (2026-10-14): opt-in endpoint-local
  `validationtreeentries` and `validationtreepathbytes` now cap discovered
  entries and cumulative relative path bytes before name buffering/Path
  construction. Zero retains existing unlimited behavior. Every directory read
  checks cancellation and closes its handle on failure. Stock/Ox each pass
  eight arithmetic/boundary checks, seven actual CLI cases (including require/
  warn rejection before helpers, endpoint isolation and hidden helper mutation)
  and a native-read cancellation/close probe; Make/Dune builds+selftests and all
  21 existing receiving cases pass on both compilers. Removing only the checkpoint
  reproduces its failure. [Contract](doc/validation-tree-limits.md),
  [qualification](tests/validation_tree_limits/qualification.json).
  Structural counts do not bound properties, SDK heaps or RSS. Manifest memory
  reservation and complete directory pre-creation admission remain open; this
  does not complete M6. Source photos/Adobe/Lightroom are untouched.

* Backend activation admission correction (2026-10-14): declarations alone did
  not prevent a previously disabled resource-bearing validator from becoming
  active after staging, potentially borrowing space reserved for retained
  metadata. Its enabled/disabled participation is now pinned along with its
  resource plan; transitions require process restart. Legacy resource-free
  validators retain policy toggles. Stock/Ox each pass 15 actual-object controls
  and the compiled-backend cases; Make/Dune builds+selftests and all 21 receiving
  regressions pass per compiler. The exact previous implementation fails the
  independent late-activation oracle; the new implementation rejects it.
  [Successor qualification](tests/backend_resources/participation-qualification.json)
  preserves the first admission receipt as historical evidence. No Adobe or
  Photo invocation, SDK/RSS enforcement or full M4-V/M6 completion is claimed.

* M4-V generic backend resource admission (2026-10-14): trusted validators now
  declare immutable CPU, covered/uncovered byte and descriptor requirements.
  Regular-file publication reserves the componentwise maximum sequential
  backend workspace in its existing envelope before staging. Validation borrows
  it without a second debit; direct validation admits its complete cost.
  Each backend receives its own exact declaration. First enabled selection pins
  a declaration through disable/re-enable; changes require process restart.
  Stock/Ox Make and Dune builds/selftests pass, as do 13 declaration/borrow
  controls, three actual compiled-plugin receiving cases per compiler and all
  21 existing receiving-path cases and 11 warning/cancellation controls per
  compiler. The warning harness now follows actual reordered dependencies and
  uses the production OxCaml selector rather than recompiling stock interfaces.
  [Contract](doc/backend-resource-interop-v0.md),
  [qualification](tests/backend_resources/qualification.json).
  These are accounting declarations, not SDK/RSS enforcement. Production Adobe
  v1 is unchanged. Full staged-directory admission, actual experimental SDK
  runtime/codec/nested-CPU parity and whole-process memory remain open; full
  M4-V/M6 is not complete. No Adobe/Photo/native preview work was invoked.

* M4-V pluggable backend memory source (2026-10-14): generic native Budget
  owns a shared covered-allocation quota independent of Adobe. Injected adapter
  copies share capacity. Adobe's allocator adapts Allocate/Malloc/Free, charging
  wrapper/header and SDK physical padding, preserving alignment/overflow and
  returning null through codec C callbacks. Buffers retain state; failed
  construction/malloc retires credits. Three normal/AVX/sanitized runs each pass
  39 controls/50000 concurrent attempts, including held18-lane pressure and
  two adapters sharing one pool; private capacity-negative and1000 malloc-failure
  rollbacks pass. Actual SDK1.7.1 headers compile allfour driver modes without
  linking/initializing Adobe. Separate source-only memory/area-memory argv,
  build IDs/artifacts/manifests remain unavailable to production v1.
  [Generic contract](doc/backend-resource-interop-v0.md),
  [evidence](tests/sdk_memory/qualification.json). This bounds covered requested
  backing allocations, not RSS/whole SDK heaps: memory_data/XMP/ordinary heaps/
  stacks remain outside. Core worst-case backend memory-plan reservations are
  integrated as above; actual SDK runtime/codec parity remains pending and full
  M4-V/M6 stays open.
  No Adobe invocation, Photo read, renderer or preview ownership change.

* M6 child resource limits (2026-10-14): opt-in endpoint-local
  `helperdescriptors` and pinned native `helperlimiter` now apply hard per-process
  limits to supervised copy/merge/diff and selected DNG validators. The fresh
  native launcher closes inherited extra FDs, lowers soft+hard limits and execs
  the original literal argv/environment in the same PID/group; parent limits
  remain unchanged. Shared worker SHA/identity checks surround settled execution
  and reject pin mutation even under warn. Stock/Ox native controls and all21
  receiving paths prove actual hard caps; independent endpoint64/32 settings
  persist. First closefrom compile failed and is retained; bounded Darwin own-FD
  enumeration is the tested successor. [Usage](tools/helper-limits/README.md),
  [evidence](tests/helper_limits/qualification.json). macOS rejects the tested
  RLIMIT_AS request before target exec; RSS/address-space enforcement remains
  unqualified. Windows requested limits reject; default zero retains baseline.
  Aggregate descendant/parent FD and memory bounds, actual capped SDK scaling
  and full M6/M4-V remain open. No Adobe/Photo/preview invocation.

* M5 opt-in built-in merge integration (2026-10-14): the explicit existing
  rule `merge = Name *.dng -> unison:dng-xmp-scalars/0` now selects the scalar
  policy. `backupcurrent` captures the common full version through Stasher;
  current previous-archive fingerprints bind the copied base independently
  before checked worker inspection/materialization. One exact artifact uses
  normal merge copyBack and both receiving validation gates. Actual stock/Ox
  loopback tests cover disjoint/swapped convergence, competing/deleted/unknown/
  image changes, resource forks, missing/stale base, disabled/mismatched policy
  and first/second
  receiver rejection. Second-receiver failure preserves its old bytes after
  first commit; fresh retry proves exact convergence with both gates.
  Make/Dune build+selftests and existing21 receiving-path regressions pass.
  [Usage/scope](doc/dng-built-in-merge.md), [pins](tests/dng_merge/qualification.json).
  Default remains disabled. Saved bases are full optional backups, not yet a
  metadata-only cache; general structures/growth and broader M5 remain open.
  No Adobe/Photo invocation or preview ownership change.

* M5 fixed-region DNG materialization (2026-10-14): trusted full-packet proofs
  now construct an exact three-way target and SDE plan after live-left
  revalidation. OxCaml workers dispatch this operation with existing borrowed-FD,
  cancellation and shared-credit ownership. Native private clone staging preserves
  all payload bytes; independent expected output matches. Stock/Ox direct controls,
  29-case actual-object workers, 127-command/2033-assertion conformance and
  JPEG/DNG/positional-write/21 receiving controls pass. Four Make/Dune CLI
  builds/selftests pass. [Scope](doc/dng-three-way-materialization.md),
  [evidence](tests/dng_reconcile/qualification.json). Automatic merging remains
  disabled in that materialization-only slice; the successor integration above
  adds explicit policy selection and archive-bound commit/recovery. Full M5 stays open. No Photo or Adobe work.

* M5 scalar packet kernel (2026-10-14): explicit policy
  org.firstpair.xmp-scalars-three-way/0 captures lossless Rating/Label attribute
  spans through the bounded parser. Exact non-allowlisted shell bytes must match;
  scalar one-sided/equal/disjoint edits converge deterministically, while
  competing values, deletion/addition, namespace/unknown/rendering/structural
  changes decline. Output is capped at1MiB. Stock runs25 controls; Ox executes
  all25 in four checked domains. Existing968 observer and1029 independent XML
  mutation checks pass per compiler. [Policy](doc/xmp-three-way-policy-v0.md),
  [pins](tests/xmp_merge/qualification.json). This kernel does not yet enable
  file merges: trusted archive-base capture, generalized container growth,
  two-replica staging/validation and failure recovery remain M5 work. No photos
  or Adobe/Lightroom are accessed.

* Checked full-sync performance (2026-10-14): stock/Ox actual CLI binaries bind
  all349 frozen inputs. The warm same-host matrix passes72 rows/576 exact file
  updates with old hardlinks, no-op inode stability and native/process/fixture
  cleanup. Eight32MiB files, per-endpoint budgets1/6 (max12 combined credits),
  one warmup and five measured repeats compare ordinary/receiver-clone/semantic.
  Ox median seconds at6:4.121/4.150/4.788; semantic1 is9.269. Semantic writes
  24KiB/eight attempts per256MiB row; generic non-inherited model64KiB. This
  reduces logical writes but does not outperform ordinary warm-cache transfer.
  [Results/scope](bench/sync/README.md), [audit](bench/sync/results/checked-worker-performance-audit-20261014.json).
  Harness rejects over-budget/low-capacity setups and removes each accepted
  corpus before the next. Physical writes, internal stages, global ceilings,
  real links and remaining SDK/M5/M6 gates stay open; no Adobe/Photo invocation.

* Checked worker cached-path measurement (2026-10-14): actual production objects
  from77234c5 run serially at1/6/18 workers with matched CommonCrypto backends.
  Median throughput stock363.4/1985.8/4782.5MiB/s and
  Ox365.5/2039.1/4941.1MiB/s;18/1 scaling13.16x/13.52x. Ranges overlap, so no
  Ox-specific speedup is established. All864 hashlib-checked results and24
  batches settle descriptors/CPU. RSS and sampled FD peaks are measured;
  independent native/external RSS control agrees exactly. [Scope](bench/semantic/README.md),
  [pins](bench/semantic/results/checked-worker-qualification-20261014.json).
  Cached hashing is not full sync, SDK or pure-compute performance. Hard global
  ceilings and full M6 remain open; no Photo/Adobe work.

* Checked production worker integration (2026-10-14): OxCaml now compiles the
  actual worker closure with Safe.spawn. Immutable extension/recognition handles,
  XMP observations and worker-safe delta operations have portable/contended
  contracts; registry and owner state remain nonportable. Stopping/running/peak
  fields are atomic, retaining the condition/mutex protocol. Stock behavior and
  the single shared CPU/helper pool remain intact. [Scope](doc/checked-semantic-worker.md),
  [evidence](tests/checked_worker/qualification.json). Actual compiled-object
  worker tests, checked negative captures and fresh Make/Dune CLI selftests
  qualify this boundary. Full native/resource/performance M6, M4-V and M5 remain
  open; Photo Root retains preview ownership and no Adobe/Photo invocation occurs.

* Production component mode selection (2026-10-14): Make and Dune now compile
  SemanticFile/Hash/Mailbox against their checked interfaces on OxCaml and select
  the five audited native contracts. Actual compiled exports link and execute
  with Safe.spawn; mutable mailbox payload capture rejects. Stock source remains
  byte-identical. Four fresh CLI builds/selftests pass, along with selector
  rejection controls and receiving regressions. Existing Make configuration
  upgrade preserves all320 compiled objects. [Scope](doc/production-oxcaml-mode-selection.md),
  [evidence](tests/mode_build/qualification.json). Full worker extension/counter
  portability is superseded by the checked-worker integration above; resource
  bounds and full M6 remain open; no Photo/Adobe invocation.

* Checked file component (2026-10-14): portable File/Hash interfaces and two
  audited native file contracts compile and run in four actual checked OxCaml
  domains, with stock runtime parity. Exact read/iteration/hash/cancellation,
  positional write/cursor/bounds/flags and full output/descriptor settlement pass;
  shared reader/writer/chunk captures reject. [Scope](doc/checked-semantic-file.md),
  [pins](tests/checked_file/qualification.json). Make+Dune CLI/selftests pass.
  File algorithms are unchanged; the newer worker integration closes the
  extension/counter compiler gate, while full M6 remains open. Kernel borrowing/native ownership are
  manual contracts, not mode proof; no Photo/Adobe operations.

* Checked hash component (2026-10-14): fallback round constants use an
  immutable lookup. A checked OxCaml interface and three explicitly audited
  native portability contracts pass native and forced-reference hashlib controls
  in four actual domains; shared contexts/bytes captures reject. [Scope](doc/checked-semantic-hash.md),
  [pins](tests/checked_hash/qualification.json). Current stock/Ox Make+Dune CLI,
  selftests and semantic kernel regressions pass. Cached-string9-sample CPU
  reference ratios new/old0.995 stock/1.006 Ox do not establish a speedup.
  Production checked-interface selection and worker portability are now
  integrated; full native/resource/performance M6 remains open;
  no Adobe/Photo invocation or full M6 completion is claimed.

* Runtime mailbox integration (2026-10-14): worker jobs and completions now
  use bounded atomic SemanticMailbox queues with max_pending admission covering
  outstanding receipts. Actual paused-owner pressure proves queued completion
  retains CPU/transaction ownership, rejects overflow and settles/closes cleanly.
  Stock/Ox each pass3840 hash/inspection jobs,384 apply jobs,39 waiter-settlement
  scenarios,21 FD controls/117 assertions plus three adapted historical guard
  negatives,21 actual receive cases and14 shared-helper controls. Fresh Make and
  Dune CLI/selftests and DNG/JPEG receiving regressions pass. [Evidence](tests/workers/mailbox-integration-qualification.json).
  At that mailbox-only stage Safe.spawn substitution still rejected. The newer
  extension/counter slice now compiles the actual closure; native/resource/
  performance M6 remains open. No Photo/Adobe invocation.

* POSIX external command supervision (2026-10-14): external copy, merge and
  diff now use `SupervisedExternal` and the exact shared SDK/domain CPU owner.
  Helper-only initialization starts no worker domains; later runtime startup
  reuses that supervisor. Endpoint-local thread weight/deadline/per-stream
  capture limits are documented in the
  [contract](doc/supervised-external-commands.md). Original argv[0], argument
  boundaries, shell command text and inherited environment are retained.
  Cancellation/signals/timeout/output overflow settle before failure. Copy
  now rejects nonzero exit before publication; a genuine previous-binary
  negative published a fully written candidate after exit 7. Failed temporaries
  remain subject to ordinary exact resume policy, not a rollback guarantee.
  The [qualification](tests/supervised_external/qualification.json) records
  fourteen real helper cases / 84 checks, four actual copy controls plus a
  previous-binary negative, existing receiving/ownership/settlement and
  publication checks on stock/OxCaml. No Adobe/Photo/native UI/benchmark was
  invoked. This is root-owned evidence. Declared weights do not restrict
  arbitrary inner parallelism; Windows stays explicitly legacy/unsupervised.
  Hard child memory/global FD ceilings and broader M4-V/M5/M6 remain open.

* Guarded obsolete staging cleanup (2026-10-14): normal producer staging and
  receiver-clone scratch cleanup now use the prepared native parent binding,
  rather than `Os.exists` followed by recursive pathname removal. The new
  local operation captures/rechecks full no-follow stat facts, rejects live
  target aliases by physical identity, and unlinks only an authorized singly
  linked regular leaf through the held parent. It opens/reads/chmods no old
  payload, preserving mode-000 cleanup. A metadata-open prototype failed that
  permission case and is retained separately. Producer-owned/resumed objects
  remain descriptor-bound; unexpected kinds/links/sidecars are preserved,
  without operational fallback. See the [contract](doc/obsolete-staging-cleanup.md)
  and [qualification](tests/obsolete_cleanup/qualification.json). Native
  controls, real Copy/CLI controls, publication compatibility and build checks
  retain exact compiler/source scope: **22 cases / 83 assertions plus one
  native negative**, **two actual Copy/CLI positives plus one wrong-parent
  negative**, and **79 actual Files/CLI cases including both old-peer
  directions per compiler**. Stock/Ox Make and Dune builds/selftests pass;
  final alias fencing is a recorded incremental follow-on to clean snapshots.
  All 330 frozen production inputs match both final Make trees. This is root-owned review, not a new
  independent-agent acceptance. Cooperative stat/name fencing is not inode
  pinning or atomic compare-and-unlink. Legacy/unbound cleanup, directory and
  auxiliary families, other-platform runtime, complete resource limits and
  M4-V/M5/M6 remain open. Preview finalization stays with Photo Root.

* Photo Root's BIG candidate notice (2026-10-14, saved metadata only):
  image `86582588`, root `86582590`, settings `86582602`, UUID
  `5CEF3706-E96B-4DBB-83A5-965DFB4BE71C`, digest
  `288e8496c12fb4f21b95c6a3568761aa`, orientation AB. Reported native FINAL
  AdobeRGB nonproxy crop is **5976×3992**, ladder 320/747/1494/2988/5976,
  highest 7,842,663 bytes and ladder 10,071,969 bytes. Monitor-fit planning
  is approximately 4311.42×2880, beyond the next lower 2988×1996 level.
  Preserve the actual native highest name/geometry; no registered 5120 level
  was found. The original Photo owner is sealing its metadata receipt.
  Fresh owning Main/current identity/native rows/physical bytes/decode
  geometry remain native-slot prerequisites. This is not Unison's independent
  qualification or authorization to move files. The small 2272 control stays
  first; BIG needs a separately admitted Root storage slot after recipe and
  lifecycle gates, within eight sources/sixteen states/eighteen credits.
  Preview design and execution remain owned by Photo Root.

* DNG warning delivery follow-on (2026-10-14): permitted findings now use the
  user-interface warning channel after an owner-loop yield, preventing a
  nested remote/UI wait from holding the hash completion pump. Abort/context
  cancellation checks bracket delivery, while candidate ownership stays
  retained. Stock and OxCaml each pass eleven actual-companion cases / 105
  assertions, two designated negatives and three complete client/server
  receive controls with logging disabled. Exact staged bytes are independently
  bound by the synthetic helper; `warn` emits one warning and publishes,
  `require` rejects, and `off` invokes no helper. Four verbatim macOS OCaml
  route cases and six Foundation-only filter cases plus two parent negatives
  pass per compiler. Mac batch warnings use the transient status field and
  bypass the `reconitems` filter; persistent/painted GUI visibility remains
  unqualified. Fresh Make/Dune builds/selftests and full macOS source compiler
  checks pass both compilers. See the
  [qualification](tests/validation_warning/qualification.json) and separate
  independent review. No Adobe/Photo/native UI invocation or performance
  claim follows. Hard SDK memory limits, unsupervised external copy/merge
  helpers, initial old-temp cleanup and complete resource lifetimes remain
  substantive core work; broader M4-V/M5/M6 acceptance stays open.

* User-confirmed scope (2026-10-14): Photo Root and the original
  `/root/preview_implementation` own final preview design, generators,
  Lightroom qualification, Ten/Quasar placement and publisher recovery.
  Coordinate through the Photo parent `codex queue` route and consume the
  resulting versioned interface/evidence here. Unison implementation remains
  focused on semantic format extensions, DNG receiving validation, general
  clone-aware filesystem support and OxCaml workers. Preview integration does
  not block independent core work. Existing finite native-window and
  production-publication admission boundaries remain unchanged; this scope
  agreement releases no native call, publisher or full generator run.

* Empty native private-cache lifecycle actually passed and closed
  (2026-10-14): the **05:32:25 UTC** current pointer supersedes delayed
  source-only notices. Root's sealed return packet `0dadea0f` records three
  callbacks, one construction/normal close and zero preview loads/rendering.
  Our [outcome audit](doc/preview-empty-cache-constructor-outcome-20261014.json)
  verifies eleven proof and ten source/review pins, four NEW observer removals,
  all five FileStore empty states, nil deletion task, exact distinct private
  objects/paths, native Auto release, post-close private-family descriptor
  absence, separate closed schema13/schema1 zero-row readback and genuine
  helper/menu/admission/lease closure. Production references/paths and owning
  Main observations match. Preference scalars were copied once; the runtime
  production guard proves preference-table identity, not separately observed
  equality of every scalar afterward. This qualifies the successful EMPTY
  private native mechanism. It does not qualify partial-failure recovery,
  populated RootPixels, authored recipe recognition, cold private preview
  reuse, Library/UI, Quasar, renderer or full run. Next: independently publish
  the preserved-control Ten recipe while its private family is closed, read
  back committed rows before fresh private opening, then separately admit
  highest/lower/current-map/private-path native recognition. No replay of the
  completed constructor or previous native controls follows from old messages.

* Earlier private cache prerequisite source review (2026-10-14): the
  [review](doc/preview-private-cache-constructor-review-20261014.json) accepts
  the inspected existing-server-thread `PreviewCache.makeForPath` mechanism
  for one EMPTY owned Ten root, conditional on fresh Root admission. At that
  source checkpoint no constructor had run; the later actual outcome above
  supplies separate runtime proof. Require four NEW observer
  removals, deletionTask nil, all five FileStore empty/zero conditions, exact
  private paths/distinct objects, one normal close and independent closed
  schema13/schema1 readback. Construction creates stores before its returned
  cache table; partial construction has no observed rollback. Close is
  sequential and may skip later stores on failure. These outcomes retain
  Root's coordinator/lease and unresolved recovery ownership. Empty auxiliary
  state does not qualify the populated RootPixels recipe. Preserve the sealed
  recipe gate; the same-process isolated route needs a separate mapping from
  app-close/open to CLOSED private-family publication and fresh private cache
  admission. Later private native reuse differs from Library/UI recognition
  and app restart. Source citation corrections are recorded separately.
  Original renderer/publisher ownership and native-window authority remain
  with Photo Root; all Unison work here is source/interface review.

* Quasar priority and earlier planning (user, 2026-10-14): Photo Root received the request to
  finish native recognition of the independently authored Ten-only recipe and
  then admit the bounded split-storage matrix. The earlier pointer at
  **05:03:29 UTC** says the original owner is preparing an executable and
  independent review for an **empty private Ten-only cache constructor/close**
  prerequisite; no new native or production-publisher window is released.
  Private recipe source/recovery is ready, with eleven recovery cases and
  eleven invalid holds; this remains separate from native use. The small
  2272×1704 control can prove storage mechanics. A representative current
  large-source/crop key must separately exercise a justified monitor-scale
  native ladder level, rather than claiming that small control proves 5120
  coverage. Native fixture/lifecycle qualification determines readiness;
  there is no evidence-based wall-clock ETA yet. Parent coordination works
  through `codex queue`; the stale local MCP HTTP endpoint at port 51114 has
  no listener and is unnecessary for this restored route. No process restart,
  native replay or transport/security alteration repaired that route.

* Exact next finite publisher test: [Ten-only offline registration](doc/preview-offline-registration-test-plan.md)
  reuses control `10031592` and six preserved JPEGs in a Root-qualified private
  native catalog/cache fixture. Target metadata must be absent before the
  independent closed-cache writer; committed rows and bytes must be observed
  before native reopening can repair them. Fresh fixture owner admission then
  verifies highest **2272×1704 / 646453 bytes** and the accepted lower request
  **640×640**, expecting **1136×852 / 251034 bytes** while rows stay current.
  One actual absent or populated RootPixels template is enough for this case,
  not for all auxiliary states. Native fixture/root selection is an open
  prerequisite: existing helpers bind the active processor's stores. No
  production deletion, registration replay, legacy conversion or rendering
  substitutes for authored metadata. Passing establishes that finite recipe's
  native compatibility, before separately admitted recovery/Quasar tests.
  The 04:13:54 UTC current pointer confirms both earlier native passes and the
  original publisher task running; its dated desktop observation is locked,
  with no new native/production publisher release. The older Root PLAN text
  listing highest recognition as next has been flagged through the queue.

* Coordination rule: read Photo's mutable
  [current-state pointer](PHOTO-OWNER-PREVIEW-VALIDATION-CURRENT.json) first.
  Its dated result pointers and specific qualification fields take precedence
  over delayed messages about earlier attempts. The 2026-10-14 04:07:50 UTC
  pointer confirms the post-restart highest pass and closed slot; Photo's
  independent review `90a8ab70` and Root acceptance `76b49782` agree with our
  sealed review below. Mixed historical fields do not establish current
  desktop, process or window readiness. Keep highest/monitor qualification
  separate; a 03:18 desktop observation is historical. Fresh Root admission
  still governs every new native/storage slot. No repeated registration or
  test follows from a delayed status message. The next gate remains the
  original owner's closed-cache metadata/recovery recipe, with the existing
  split-storage matrix separately admitted after that recipe is qualified.

* Post-restart highest gate accepted (2026-10-14): original Photo owner ran
  control `10031592` in Classic PID 40020 with a fresh admitted nonce. Both
  LOAD/RELOAD explicitly selected and decoded **2272×1704**, level 6,
  **646453 bytes**, with actual `full`/absent-height/absent-scale policy.
  Twelve returned LEVEL records match current rows/digest and
  `final`/`AdobeRGB`/`AB`; six raw mapping stages are current/direct stored AB,
  including before the first authored load. Separate pre/post read-only rows
  and seven retained file identity/hash arrays match. This proves observed
  registration/mapping availability across restart, not uninterrupted physical
  row history under autonomous startup/background work. Zero registration
  replay; five owned callbacks closed, helper/menu restored, nonce withdrawn
  and kernel lease availability observed. The
  [outcome](doc/preview-native-highest-outcome-20261013.json) and
  [independent review](doc/preview-native-highest-independent-review-20261013.json)
  preserve 51 declared / 46 unique source/log/JSON/module pin checks and actual
  raw-record acceptance. Earlier sealed requests/receipts stay unchanged.
  Next gate: original owner qualifies an independently authored Ten-only
  closed-cache metadata/recovery recipe from preserved native JPEGs, then
  native reopen/load/readback. Native `touchPyramid` success does not qualify
  that offline publisher. Root retains all native/storage ownership and
  catalog-writer deferral; Unison makes no competing invocation. Quasar split,
  large-crop monitor/1:1, pixel color fidelity, standalone rendering, power-loss
  durability and full-run admission remain unqualified.


* Photo Root drives native and storage validation; the original preview owner
  retains rendering/publication. The [remaining-gates review](doc/preview-validation-gates-20261013.md)
  adds returned LEVEL quality/profile/orientation checks on both highest loads
  because source logs them without gating all fields. It preserves the sealed
  exact highest request and adds no competing job. The later
  [split-storage matrix](doc/preview-split-storage-test-plan.md) is source-only
  and requires successful highest recognition plus Root's qualified offline
  publisher/recovery admission. Native rewrite/trim/unavailable-target/restart
  behavior is distinct from symlink reading. Prior native slot stays closed;
  no preview readiness or renderer fidelity is inferred from a pure-read ping.

* Earlier highest request under the preview-validation priority: the exact
  [queued request](doc/preview-post-restart-highest-request-20261013.json)
  reuses original Photo owner's control `10031592` in the restarted process:
  `HIGHEST_REGISTERED`, width `full`, absent height/scale, and explicit unique
  row selection for **2272×1704**. Both LOAD/RELOAD must decode that highest
  object and rebind fresh Main, raw mapping, level rows, positive sizes and
  preserved header/profile fields. Capture current raw mapping before the
  first LOAD to claim mapping survived restart; repaired post-load mappings
  qualify less. Quiet success has five callbacks/two loads, while reviewed
  busy/drain branches permit twenty-one callbacks/ten loads; fresh Root
  admission must cover actual source bounds and retain outstanding work beyond
  deadline expiry. No registration replay or additional
  restart is requested. Fresh owner/lease/nonce/deadline admission is required;
  the previously held preparation stays closed. The owner's later metadata
  reports a separately released pure-read readiness ping, which authorizes no
  preview/render/writer work and proves no actual preview result. Source-only
  final highest review pins 39 cases; older `VALIDATION.json` records an
  intermediate 36-case revision. Queue delivery was accepted; its pending
  event is now closed by the post-restart outcome above. Original ownership
  stays with Photo; Unison makes no Adobe/cache/media invocation. Quasar,
  monitor/1:1 and renderer fidelity retain separate gates. Core whole-clone
  implementation remains available after this priority review.


* Earlier pre-restart native-preview baseline (reviewed 2026-10-14): the original Photo
  owner completed control `10031592` with one native registration and two
  native LOAD/RELOAD passes before restart. Each selected and decoded
  **1136×852**, with fresh current identity/orientation at all six raw
  BEFORE_LOAD/POST_LOAD/POST_DECODE observations. Six registered levels have
  positive exact disk sizes; a separate read-only connection observed committed
  rows and the current mapping. Seven retained files were independently unchanged
  and six preserved JPEG sections passed independent full decode. The highest
  **2272×1704** level has registration/independent-codec proof only, not native
  selected-decode proof. See the [outcome](doc/preview-finite-oracle-outcome-20261013.json)
  and [independent metadata review](doc/preview-native-one-control-independent-review-20261013.json).
  Eight owned callbacks returned, helpers restored, coordinator exited normally
  and the canonical lease was released; this does not assert global Lightroom
  quiescence. After Root's restart, the cold/highest test stopped before native
  entry when the desktop relocked. The latest owner observation at 03:30 UTC
  reports Classic PID 40020, no pending request and no headless ping release.
  Cold/highest recognition, monitor/1:1, Quasar split/mount-loss, faithful
  rendering and production publication remain unqualified. Original renderer/
  publisher ownership stays with `/root/preview_implementation`; Unison reviews
  metadata through the parent queue and launches no competing native work.

* Whole-file clone implementation is qualified for the bounded core scope
  (2026-10-14):
  `WholeFileClone` validates separate typed Int64 receipts; ordinary `Copy`
  uses strict named/FD APIs instead of the unchanged compatibility booleans.
  Named macOS creation retains a custom native ownership carrier, follows the
  selected regular DATA source, checks fresh source binding and publishes an
  owned intermediate through `StagePublication`. Captured EOF reaches all
  source-copy branches; the sized data-only stage is separate from unsized
  receiver-basis reconstruction. FD cloning preserves source read-ahead and
  reconciles output before progress or later literals. Exclusive/adopted
  provenance gates cloning; compatibility O_TRUNC opening cannot supply it.
  Initial matched stock/Ox Make/selftests passed as retained pre-close-fix
  trials. Source review then found Unix.close could dispatch pending work
  before the OS close after an ML owner flag was cleared. A native slot close
  now disarms and closes once without intervening pending dispatch; its saved
  error is raised only after settlement. Final **332-source** refreeze passes
  Make/selftest and clean Dune/selftest on stock **5.5.1** and Ox **5.2.0+ox**.
  Both compilers pass **60 fixed groups / 536 assertions**, five designated
  negative controls and seven existing clone regressions each. Normal native
  controls use the unchanged compiled C object; edited native code is restricted
  to explicit fault controls. Actual nodump-source fallback, source/basis EOF
  distinction, output continuation, exclusive/O_TRUNC provenance, source-name
  retargeting, parent/name replacement and cleanup ownership are covered.
  The uniform signal fixture observes real nonraising signal delivery, then
  raises an ordinary synchronous C fault. Ox rejects arbitrary Fault.Primary
  signal exceptions; retained fatal fixture trials qualify that policy, not
  general asynchronous exception handling. No private Sys.with_async_exns guard
  was added. [Component evidence](tests/whole_file_clone/qualification.json)
  and [integration evidence](tests/qualification/whole-file-clone-integration-20261014.json)
  preserve successful and failed trials, source/object/binary/log pins and
  limits; the [independent fixture/receipt review](tests/qualification/whole-file-clone-independent-review-20261014.json)
  accepts both final packages and preserves the earlier signal-policy failures.
  Native Linux/Windows/BSD execution, physical allocation, performance,
  hostile namespace races, arbitrary open-return interruption and existing
  three-handle stage ABI limits remain unqualified. No Photo/Adobe operation
  was part of these core tests. The [proposal](doc/whole-file-clone-status-proposal.md) and
  [test plan](doc/whole-file-clone-status-test-plan.md) remain historical design
  artifacts. Previously tested core checkpoint `aa53e3a` is pushed.

* Earlier Photo renewal (received 03:03 UTC): the
  [Root renewal at 02:14:39 UTC](doc/preview-finite-oracle-resumption-20261013.json)
  reopened the original owner's finite slot after unlock at 02:13:58 UTC,
  using the same coordinator PID 18036 / tool session 37295 and Classic PID
  2844. Prior denied requests were unsubmitted, with no replay. This delayed
  admission receipt proved no outcome or current readiness. The completed
  outcome and closure above now supersede its pending state; cold/highest
  continuation remains separately coordinated.

* Earlier Photo suspension (sealed 2026-10-14 02:12 UTC, read 02:18 UTC):
  the finite native window suspended after actual desktop relock. The
  [suspension/closure pins](doc/preview-finite-oracle-suspension-20261013.json)
  record all five helper attempts terminal/restored, three registration
  attempts returning `WAIT_FOR_MAIN_CATALOG`, and zero native registration
  entry or UI/Main/cache mutation. Coordinator PID 18036 retains the canonical
  Photo lease with zero active native CPU credits. The six-file independent
  byte/full-decode verifier passed; native recognition remains unproved.
  At that receipt, the exact mapping/load/decode packet remained pending and
  Root required actual unlock revalidation and renewed owner admission. The
  later renewal above supersedes that admission state. Neither receipt proves
  native recognition. Unison's completed isolated synthetic qualification is
  separate from the preview slot and has no Adobe/cache invocation.

* Receiving/report settlement checkpoint (2026-10-13): source
  extends guarded returned-work settlement through Runtime admission/I/O,
  companion recognition/validation, candidate fences, directory consumers,
  report loans and the selected Copy/Files/TargetBinding publication owners.
  `BorrowedWork.all` records every launched promise before later launches and
  joins; finite launch/observer failures drain all launched participants,
  preserve the first observed error and stop directory consumers via the
  preallocated error hook. DNG post-execution fences now use an independent
  execution-start flag, so a lost child receipt cannot bypass candidate/tool
  rechecks under warn. RPC output guards reach the actual write/fill/flush
  promises and suppress a second reply after output starts. Stock OCaml 5.5.1
  and OxCaml 5.2.0+ox Make and clean Dune builds/selftests match 331 inputs
  across five source sets (1,655 comparisons). Each compiler passes 98 new
  focused controls: 28 real-child/aggregate cases (422 explicit assertions),
  three actual Files/directory receiving cases and 67 Runtime/report/loan/RPC
  controls. Fourteen designated negatives per compiler have distinct exact
  parent-participant, full-parent, legacy-iterator and private-group provenance.
  Receiving rejections preserve original live bytes/inodes and typed archived
  fingerprints, then exact retry succeeds. Output failure retains an exact
  packet prefix without appending another reply. Both compilers also pass
  all twelve existing suites: workers/helpers/I/O, receiving/publication,
  semantic remote/meaning/reports, details/bounds/reconnect and producer handoff.
  Component receipts preserve eight fixture-only trials and explain the removed
  blocking child-ready CLI case; no owner-loop pumping substitutes for dispatch.
  See the [contract](doc/returned-work-settlement.md),
  [Runtime/report component](tests/runtime_settlement/qualification-20261013.json),
  [validation/receiving component](tests/validation_settlement/qualification-20261013.json)
  and [integration](tests/qualification/validation-report-settlement-integration-20261013.json).
  Production source stayed frozen through all executions.
  [Independent execution acceptance](tests/qualification/validation-report-settlement-independent-review-20261013.json)
  is recorded separately before publication. Legacy transfer
  internals, External/region schedulers, recursive Files orchestration,
  input/handshake scheduling, watchdog timers, TargetBinding preparation and
  delayed `Lwt.connect` retain separate limits. This is functional/resource
  ownership qualification with synthetic files, not real Adobe/camera-corpus,
  Lightroom recognition, Quasar placement, throughput or complete FD/RSS proof.
  The whole-clone boolean API gap remains next core work. Earlier checkpoint
  receipts below retain their own frozen source and do not qualify this source.

* Earlier native-preview release (2026-10-13, verified 2026-10-14
  02:04 UTC): Lightroom access is restored and the formal Photo Root
  [finite-window release](../photo/native-access-restored-59cae9953316406886d124d25ebe9be7/FINITE-ORACLE-WINDOW.json)
  binds current PID 2844 and the original `/root/preview_implementation` owner.
  Its SHA-256 is `fe84dacb6f1d1df114c5bd28c2c01158f139a531945bf04349cf5a9d6e972874`.
  Maximum eight sources / sixteen logical states share eighteen CPU credits.
  The owner starts preserved control `10031592`; independent file verification
  is underway. The release supersedes the earlier access/clearance receipts'
  unreleased state for this specific owner-controlled slot. Unison has no parallel
  Adobe/cache operation or preview output. Our exact evidence request was
  queued to Photo parent thread `01a13369-8b68-7aa1-be91-cba984ba269b` for
  forwarding: current parent UUID/digest, raw mapping before/after load,
  native-effective orientation, level digest/decoded geometry, positive
  size/stable bytes, current-versus-stale fallback, commit visibility and
  independent file identity. Direct queue input to the child was rejected
  by the app server; the parent queue accepted delivery. Await the owner's
  completion/closure packet and source pins. The follow-up exact request and
  accepted queue delivery are preserved in the
  [coordination receipt](doc/preview-finite-oracle-request-20261013.json).
  Cold restart is separately
  coordinated; Quasar mount-loss qualification is outside this slot.
  Queue delivery and formal release are not a successful native test receipt,
  renderer proof, full-run authorization or Unison-owned window.

* Earlier returned-worker settlement checkpoint `2059949` (2026-10-13): source uses
  `BorrowedWork.try_bind` at CPU, I/O, submit and response-mapping boundaries.
  Two observer-installation failures previously could report failure while a
  dispatched domain still held descriptors, retiring its surrounding workspace
  and filesystem credits. The guard preserves the first error and drains the
  actual returned promise before cleanup, with one observer retry followed by
  owner-loop polling. I/O ownership retires at ledger publication. Each compiler
  passes 39 actual-domain cases across six captured guard boundaries, underlying
  success/failure/cancellation, queued CPU/I/O and finite polling-timer failures.
  Private parent `9fbfc00` participant binaries reproduce early retirement under
  an independent live-worker/FD/admission oracle. Make and clean Dune builds /
  selftests match 331 inputs on stock/OxCaml. Both compilers also pass 27 worker,
  37 helper, 20 I/O, 36 helper-ownership, 20 descriptor-ownership, 21 receiving
  and 79 publication controls, with designated CPU/fairness negatives. The
  [contract](doc/returned-work-settlement.md) and [integration receipt](tests/qualification/worker-settlement-integration-20261013.json)
  retain the frozen source and execution evidence; independent acceptance is
  recorded separately. Persistent OOM, delayed legacy promise connections, pre-return
  admission/dispatch failures and independent work thrown before a promise is
  returned remain separate. The whole-clone boolean API gap is still open.

* Strict native-range continuation (2026-10-13): production range copying now
  uses additive `Fs.copy_file_status` / `CopyRange.run_native`, retaining legacy
  ABI/source and its compatibility loop. Explicit backend/phase/prefix/error/
  effect/scope results replace ambiguous errno fallback. Operational failures,
  indeterminate effects and contradictory fields stop; only verified scoped
  declines permit bounded suffix copying. Linux no longer hides EBADF behind
  sendfile; Solaris partial errors retain both prefix and failure. The Windows
  source path requests exact aligned extents without an extra cluster and
  settles IOCTLs with one transient event; other-platform runtime qualification
  remains open. Ordinary local fallback now copies only remaining bytes and
  reconciles buffered/native channel positions. See [native-copy-range.md](doc/native-copy-range.md).
* Native-range qualification: stock/Ox Make and clean Dune builds/selftests
  match 329 production/package/INSTALL inputs. Both compilers pass sixteen typed
  groups, thirteen actual macOS ABI groups, fourteen complete production-caller
  groups and three designated private negatives each. The existing eleven
  legacy range groups pass unchanged. Ordinary clone, receiving validation and
  Files publication regressions are bound in the [integration receipt](tests/qualification/native-copy-range-integration-20261013.json)
  with separate independent acceptance. macOS still provides no native range
  sharing through this API; whole-file basis/stage reuse remains. Linux/BSD/
  Solaris/ReFS execution, Windows append-wrapper and event-close behavior,
  measured physical sharing/performance, complete resource limits and crash
  qualification remain open. No Adobe/Photo or preview invocation occurred.

* Receiving-validation continuation (2026-10-13): core now accepts separately
  registered `CandidateValidator.S` companions and dispatches immutable content
  recognizers through typed workers. The single DNG companion covers v0/v1
  transfer profiles and ordinary fallback, independently of semantic enablement
  or eligibility. Bounded classic/BigTIFF IFD0 recognition selects renamed DNGs,
  no-XMP/private/future-version claims and checked uncertainty; `.dng` remains a
  forced claim. Unmatched files avoid full hashing. Operational errors and
  candidate pre-inspection failures reject even under warn. Recognition, initial
  full hashing and sequential callbacks retain one 1 MiB / nine-FD loan;
  descriptor ownership closes before helper execution. See
  [candidate-validators.md](doc/candidate-validators.md).
* Validation compatibility is now `dng-validation-v1`, with no v0 alias.
  Both warn and require refuse old suffix-only peers before transfer; off keeps
  ordinary compatibility. Receiver selection repeats the capability guard and
  captures endpoint-local tool settings. Adding another compiled companion
  requires registration, not a receiving-core dispatch edit; an isolated TOY0
  companion qualifies this path without installing a production format.
* Validation checkpoint at `941b99f`: stock OCaml 5.5.1 and installed OxCaml 5.2.0+ox Make
  and clean Dune builds/selftests match 328 production/package/INSTALL inputs.
  Each compiler passes 28 new actual receiving cases, seven focused Identify
  groups, 37 helper groups, two local/remote warn pre-inspection EIO cases,
  endpoint configuration/old-v0 refusal controls and nonblocking FIFO controls.
  The unchanged 21 receiving-validation and 79 Files publication regressions
  also pass each compiler. Actual v0 binaries reproduce the renamed-DNG bypass;
  the new feature rejects that peer contract. Fault receipts decode actual
  format-23 named archive nodes and preserve old full content fingerprints;
  raw archive/container or receiver-node equality is not claimed. The
  [integration receipt](tests/qualification/validation-companion-integration-20261013.json)
  binds source/build/test artifacts; its separate independent review records
  acceptance. Tests use synthetic files and Adobe-free helpers, with no new
  Adobe, Photo, preview-generator or native Lightroom operation. Real SDK/camera
  receiving coverage, complete resource limits and throughput remain open.

* Latest Photo coordination (2026-10-13): private v3 metadata staging is complete
  against 905,928 Lux images / 895,491 current still keys. The
  [alignment receipt](../photo/mass-preview-alignment-current-20261013-v3/COMPLETE.json),
  [summary](../photo/mass-preview-alignment-current-20261013-v3/SUMMARY.json)
  and [owner handoff](../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/HANDOFF.json)
  replace v2 pending-revalidation counts: 966,181 regular files, 9,178,878,944,015
  bytes; 961,208 unchanged full identities, 4,822 new paths, 151 changed
  identities and 344 previously observed files absent. Candidate roster is
  156,253 keys / 156,255 images: 146,476 explicit-root legacy, 984 old-format
  identity-bound and 8,793 modern filename-only keys. All 987 former header
  holds are metadata-resolved, including three fresh strict-header cases.
  All 4,299 registered target sizes are positive/matching; 1,338 current-native
  keys have captured exact associations/orientations. Native decode, source
  freshness, committed recognition, restart and monitor adequacy remain separate.
  Preserve all 55 mapped native deletion markers; the owner reports native
  queue exclusion and no added unregistered-candidate hold. RootPixels metadata,
  48,046 face crops and 3,411 motion thumbnails contribute no ordinary monitor
  coverage. Known standalone gaps are 485,185 other-digest and 252,676 no-file
  keys: 737,861 known keys lack exact-current retained standalone files;
  39 empty digests remain unknown. This is not a proved regeneration count.
  All 156,253 candidate sets remain production-admitted=false.
  Registration gaps, alias-only gaps, conflicts, stale edits and build gaps
  stay separate; retained-byte reuse does not require a new-renderer benchmark
  or Quasar split qualification to classify and stage it. The older 761,466-key
  full-monitor / 134,582 late-gap capacity models remain historical. The final
  [geometry packet](../photo/mass-preview-jpeg-geometry-planning-20261013-v1/RETURN-PACKET.json)
  (SHA-256 `cf29ca2d407a9c67f286a92e686ce06cf052e0322ee92852b0ad0bdacdd00437`)
  and [publication](../photo/completed-preview-geometry-publication-324918754b8644e3ba5f5ef8b40d428f/COMPLETE.json)
  close all requested passes: 39,982 modern files, 4,299 native targets and
  147,460 highest legacy sections, totaling 191,741 files/sections and
  6,308,224 returned marker/SOF bytes. All readers closed; zero framing holds,
  dimension mismatches or observed identity drift. Returned bytes do not measure
  physical disk amplification. No payload hashes/copies, pixel decode,
  registration or native invocation occurred. Stored-crop/proxy/quality and
  provisional 5120x2880 fit remain conditional planning, not current edits,
  actual crop/orientation, decoded integrity, native level selection or 1:1 proof.
  Preserve the 67 missing-container historical records as absent-file context;
  1,469 modern alternatives beside qualified legacy containers were outside the
  inspected modern cohort. See [integration](doc/preview-design-integration.md).
  At that geometry snapshot, control `10031592` was uninvoked and desktop/
  native access was unavailable. The later one-control outcome at the top of
  this handoff proves committed registration and selected-tier native reuse;
  its slot is closed. Highest/post-restart loading now needs fresh Root
  admission under the published request, with original owner retained.
  Shared eighteen-credit ceiling and Quasar/Ten placement persist. The
  ORIGINAL renderer/publisher owner's
  [durable acknowledgment](../photo/mass-preview-alignment-publication-66241f91142d4992a7333c88d2a8ba22/ORIGINAL-PREVIEW-OWNER-ACKNOWLEDGED.json)
  pins the mass handoff, v3 receipts, modern geometry and compiled interface
  proof. The [ABI assessment](../photo/preview-generator/abi-layout-qualification-20261013T223153Z/ASSESSMENT.json)
  and completion hashes were verified from JSON receipts: eight C/Rust structs,
  56 fields / 172 metrics and 15 synthetic signatures agree on this x86_64 LP64
  target; genuine OxCaml 5.2.0+ox allocating C-stub transport passes. Carry full
  uint64 in Int64 bit containers with explicit unsigned handling, signed status
  in Int32, with field bounds and checked size/offset conversion before I/O or
  allocation; never assume OCaml-record/C-struct layout equality. This is synthetic
  project-interface proof, not a private Adobe ABI, renderer/runtime/fidelity
  qualification or benchmark. That same ORIGINAL owner has now
  [durably acknowledged the final closed geometry](../photo/completed-preview-geometry-publication-324918754b8644e3ba5f5ef8b40d428f/ORIGINAL-PREVIEW-OWNER-ACKNOWLEDGED.json),
  6,728 bytes, SHA-256
  `f66ed2f48cdc1d29793a17a195a09b571c8569d1669e7e12b38fe6bf10e46f5e`.
  Its seventeen verified artifact pins bind source/interface acceptance only;
  renderer/publisher ownership is retained. The finite native window remains
  UNRELEASED, with no fresh receiver/publication admission or oracle readiness.
  Local relay history remains in
  PREVIEW-MASS-ALIGNMENT-FORWARD-20261013.json. No production writes,
  payload hashes/copies, competing publisher or full-run admission occurred.
  Cleanup review protects the exact-version Atlas/Bumer archives formerly
  under delete; preserve them in placement/migration manifests and budgets.

* Extended DNG continuation (2026-10-13): separately negotiated
  `org.firstpair.dng-xmp/1` / `dng-xmp-v1` adds BigTIFF and bounded embedded
  CR camera-profile graphs in both byte orders. Each CR blob keeps its own
  classic layout, endian and relative header base. Headers, tables and values
  are protected against XMP aliasing; unsigned64, count/product/base arithmetic
  is checked before conversion or reads. Camera tags/types have a discrete
  baseline policy; modern/private graphs remain explicit fallback. The single
  fixed out-of-line XMP packet and complete complement/target proofs remain.
  v0 keeps its accepted subset and canonical goldens; malformed diagnostic
  strings can differ after earlier relative-offset rejection. See
  [dng-profile-v1.md](doc/dng-profile-v1.md).
* v1 preference propagation preserves BOOL/STRING_LIST CLI types, local values
  and legacy wire bytes. The client expands `semanticdng` into known IDs,
  filters the final common capabilities, and explicitly sends the shorthand
  bool as false to clear stale receiver state. Legacy incoming bool decoding
  remains. Explicit v1-only selection falls back ordinarily at a v0-only peer;
  the alias/mixed selection can use v0. The supported CLI has at most one
  remote root; two-remote attempts are expected rejection controls, while
  linked preference tests exercise intersection/reuse state separately.
* v1 qualification: final Make stock `unison-build-zf3o8io7`, Ox
  `unison-build-85enmyly`, and clean Dune `unison-dng-v1-clean-dune-kidej9gv`
  pass builds/selftests with all 318 production/package/INSTALL inputs
  matching workspace and four snapshots; generated Make dependencies match
  separately. Both compilers pass 1,091 direct cases / 5,534 assertions and
  three designated private regressions, including four real sparse >4 GiB
  inspector/read cases (no large-file hash/transfer claim). Routing passes
  21 actual sync scenarios, 162 preference checks and four mixed-compiler v1
  receive updates per compiler; opaque/layout fallback and no-op inodes pass.
  All 79 Files publication / 21 synthetic receiving-validation cases,
  20 worker groups (18 v1 domains, 36 inspections and 18 exact applications),
  14 CLI report cases and existing remote/minimum-budget/old-peer checks pass
  both. Unchanged v0 conformance passes 127 commands / 2,033 assertions each.
  Direct/routing/combined receipts and separate independent acceptance are
  under `tests/dng_profile_v1/` and `tests/qualification/`. SDK sources were
  read/pinned only. Representative DNG/camera/Adobe/Lightroom corpus, numerical
  profile validity, modern profile graph support, storage/performance and
  full resource limits remain open; no Photo or Adobe invocation occurred.

* Retained-resource continuation (2026-10-13): production target setup now
  acquires a caller-owned Consumer reservation before native proof preparation.
  The registry retains it through Ready/Producing/Finalized/Committing, including
  the five-descriptor gap after producer return. Close native ownership before
  retirement. Explicit Copy/SDE and serialized validation loans use the same
  envelope, including legacy work handoff; no nested Consumer admission wait.
  Sources retain separate service headroom through reply marshal/output. The
  selected consumer envelope is 24 descriptor credits and max(1 MiB,
  8 * enabled payload limit + 256 KiB); Source uses eight credits. DNG needs at
  least two transaction slots, 32 descriptor credits and its consumer/source
  buffer allowance (17 MiB fits). Ordinary proof admission stays independent
  of worker-pool initialization. Design: [resource-admission.md](doc/resource-admission.md).
* Resource checkpoint qualification at `ebcfec6`: Make stock `unison-build-yrkxtl7v` and Ox
  `unison-build-h42l15o6`, plus clean Dune `unison-resource-clean-dune-d2fvgsa1`,
  pass builds/selftests with 316 production/package/INSTALL inputs matching
  the workspace at that freeze and all four snapshots. Generated dependencies match both Make
  outputs separately. Both compilers pass 26 admission groups / 16 finite-fault
  groups with four private negatives, 106 unchanged registry groups with two
  negatives, 20 early-FD groups / 110 assertions with three leak negatives,
  36 helper groups / 211 assertions with four negatives, 19 worker and 33 helper
  regressions, and 13 exact-function nonce groups with two negatives. Native
  actual-publication census passes eight groups / 58 assertions and four
  designated rejections per compiler, including immediate/queued token-handoff
  failure after native preparation. All 79 Files publication and 21 synthetic
  validation receive cases, 24-key bidirectional/old-peer SDE, five nonblocking
  paths and six I/O-runtime scenarios / 107 assertions also pass both. Component
  receipts are under `tests/{admission_faults,fd_ownership,helper_ownership,
  nonce_ownership,resource_lifetime}/`; the combined receipt is
  `tests/qualification/resource-lifetime-integration-20261013.json`. A separate
  independent review records artifact/source acceptance; final aggregate review
  supersedes its initial pending portions.
* Resource limits remain open: 24 is a conservative selected-path envelope,
  not an exact native peak or complete process FD/RSS policy. Phase-boundary
  census does not sample hidden native transients. Pool/transport/legacy
  baselines and OS descriptor limits, raw/decoded RPC ingress, XML expansion,
  manifests, native/child allocations and broader post-dispatch recovery need
  further work. An allocation failure in an outer Files waiter can abandon an
  indexed Ready owner whose credits stay held until session teardown. Persistent
  allocator exhaustion, arbitrary post-worker-queue failures and uncertain OS
  close/reap settlement remain unqualified. No physical-write/performance claim,
  SDK/Lightroom invocation, Photo access or preview publication occurred. The
  external finite oracle window remains unreleased independently of this work.

* Positional-write continuation (2026-10-13): `SemanticFile.writer` is an abstract
  borrow of an admitted private output; it allocates no descriptor. POSIX
  admission rejects read-only/append mode, nonregular and multiply linked files
  once per writer, including unchanged plans. Each later attempt checks slice /
  int64/native-offset bounds, copies at most 64 KiB into native stack storage and
  issues one `pwrite` while the runtime is released without pending dispatch.
  ML computes absolute offsets from successful progress, checks cancellation,
  retries EINTR at that offset and rejects zero/invalid progress. Operational
  failures do not choose another backend. Existing FD ownership, stable flags
  and exclusive output access remain required; no extra ownership lease is
  invented. Windows retains its legacy seek/write backend with kind/link checks.
* Fresh positional-write builds: stock Make `unison-build-n18n0eou`, Ox Make
  `unison-build-yft6dgn_` and Dune 3.22.2 `unison-dune-positional-yj9ms_5y` pass
  builds/selftests with all 316 production/package/INSTALL inputs matching the
  workspace and both compiler snapshots. Kernels, 127 independent conformance
  commands / 2,033 assertions, 19 worker / 15 report groups, actual local/remote /
  24-key bidirectional/old-peer SDE and all 79 full `Files` cases pass both
  compilers. Dedicated direct controls also pass 59 native/application cases /
  1,070 assertions plus two artificial invalid-progress and three forced legacy-
  backend controls, for 64 positive cases / 1,131 assertions per compiler.
  Three private source regressions detect seek/write position changes, removed
  append admission and a released heap pointer. Independent read-only review
  checked 492 hashes and 238 retained native artifact entries. Evidence is
  `tests/positional_write/qualification-20261013.json`. Actual local/remote
  receivers pass four partial-write cases across both compilers: a real 64 KiB
  prefix followed by EIO preserves old live bytes/inode, discards staging and
  retries exactly; the next no-op preserves the successful inode. Archive
  checks are raw fingerprint-byte observations, not decoded node authority.
  Eight finite cleanup controls pass. The owner retains the client PID through
  group cleanup before reaping and settles both captures, preserving primary
  errors. Independent artifact review accepts all 316 inputs across five source
  locations and 4,841 integration hash comparisons. Integration evidence is
  `tests/qualification/positional-write-integration-20261013.json`; its initial
  audit-pending status is superseded by the separate acceptance receipt
  `tests/positional_write/independent-review-20261013.json`.
* Position scope: each native write preserves its shared FD position; proof
  reads and final hashing can still change that position during the complete
  materializer. Logical bytes count returned successful writes, and attempts
  include EINTR. Neither attests physical writes/sharing, crash durability or
  elapsed speedup. A borrow requires no concurrent FD close or status-flag
  change. Complete-lifetime FD/memory limits and platform/runtime qualification
  remain open; the new native buffer is a bounded per-call stack cost.

* Native scratch continuation (2026-10-13): the common three-ABI clone engine
  now creates its blank reservation through the retained destination parent,
  using bounded exclusive `openat`, rather than an absolute-path `mkstemps`.
  Its fixed `.unison.basis-<32hex>.unison.tmp` basename follows Unison's normal
  temporary-file convention and supports full-length destination leaves.
  Reservation, basis and admitted output removal require a still-held witness
  and matching no-follow device/inode lookup. Cleanup precedes witness close;
  descriptor slots clear before a single close attempt. Primary operational
  errors survive cleanup, and close failures cannot become permissive declines.
  The three result layouts, source checks and scoped clone declines are unchanged.
* Scratch checkpoint qualification: both compilers pass 182 real APFS cases /
  1,984 assertions, including parent-path rebinding, bounded collisions,
  replaced/missing names, error cleanup and actual recycled-FD close sentinels.
  Both private regressions fail the designated checks through all three ABIs.
  Independent read-only review verified 137 file hashes and 1,776 retained
  artifact entries. Fresh Make stock `unison-build-18qqtcuk` and Ox
  `unison-build-ksmidizw`, plus Dune 3.22.2 in
  `unison-dune-scratch-drdljmjz`, pass builds/selftests with all 315
  production/package/INSTALL inputs matching. Current strict/handles/signal,
  86 Copy-publication, 40 adoption/36 old-handoff controls, bound-range,
  local/remote/bidirectional SDE and old-peer regressions pass both compilers.
  Evidence: `tests/clone_scratch/qualification-20261013.json` and
  `tests/qualification/native-scratch-integration-20261013.json`. The full
  actual `Files` caller also passes all 79 cases per compiler with no exclusions;
  its receipt is `tests/qualification/native-scratch-final-files-20261013.json`.
* Scratch scope: clone syscalls return no created FD, so opening/admitting
  their result still has a first-admission interval. Failed first admission,
  repeated witness/removal errors and a late parent-close failure can preserve
  artifacts. Replaced leaves are preserved; check/unlink is a cooperative fence,
  not atomic hostile namespace protection. These artifacts are not durable
  quarantine: existing pathname-based old-temp cleanup remains separate and
  may later remove matching stale temporary files. Initial old-temp cleanup,
  mount-lifecycle invalidation, complete-lifetime resource limits, physical
  storage effects and crash recovery remain open. Design and limits are in
  [native-scratch-next.md](doc/native-scratch-next.md).

* Filesystem execution continuation (2026-10-13): production `IoAdmission`
  is shared by OxCaml domain jobs and supervised validator execution. Endpoint-
  local `semanticvolumejobs = 0` preserves the configured CPU ceiling; a positive
  value bounds each filesystem device independently. Fresh held-FD device keys
  are deduplicated and atomically admitted for source/output before domain slots
  and CPU permits. Earlier overlapping requests retain fairness; disjoint keys
  may progress. I/O waiters consume no execution slots or CPU permits. No I/O
  lease spans RPC waits or the whole validation/transaction: helper pre/post
  hashes run outside the actual-child lease. Active worker/child settlement and
  cancellation release their credits exactly once. Generic library constructors
  retain compatibility; the production runtime supplies the shared gate.
* Filesystem-execution checkpoint qualification: Make stock `unison-build-9jpxa20z` and Ox
  `unison-build-6x7ciag6`, plus Dune 3.22.2 in
  `unison-dune-io-final-g3zdqdrg`, pass builds/selftests with 315 matching
  production/package/INSTALL inputs. Both compilers pass 19 actual worker groups,
  33 helper groups, 20 gate groups / 243 assertions and six linked-runtime
  scenarios / 107 assertions. Fairness and post-open ownership negative controls
  detect their intended regressions. Runtime tests exercise the real preference's
  wire omission, malformed incoming-value protection, endpoint file/CLI precedence,
  default CPU-based ceiling, negative rejection, active/queued cancellation,
  prompt FIFO/directory rejection and held-FD cleanup. Source review closed the
  first ownership-closure allocation gap. Current ordinary cloning on both,
  Ox remote/bidirectional/old-peer SDE and stock local/remote/SIR0 observations
  pass. Combined evidence is `tests/qualification/io-execution-20261013.json`.
* Receiving-path acceptance is now qualified with Adobe-free helpers: 21 actual
  CLI cases per compiler at one filesystem execution credit on both endpoints
  cover completed/partial stage resumption, local hint reuse, external copies,
  configured generated merges, first/second receiver failures, exact retries,
  child timeout/reaping, client-receiver SIGINT and observed serial directory
  helper overlap. A second merge receiver's failure can leave the first committed;
  retry remains a merge conflict, recaptures current inputs and revalidates both
  fresh results. No distributed atomic-merge claim. Pin/argv/full-candidate receipt
  checks and helper mutation fences remain enforced. Evidence is
  `tests/validation_paths/qualification-20261013.json`; actual SDK/corpus reruns
  remain separate and the external oracle window is still unreleased.
* Bounded actual sync measurements now qualify 13 rows / 39 CLI invocations
  using the current 315-input stock/Ox snapshots plus preserved original 2.53.5.
  `bench/sync/` compares ordinary receiver copying, receiver APFS clones and DNG
  semantic clones through an owned loopback transport; independent exact bytes /
  hashes, unchanged hardlinked old bases, inode-stable no-ops, empty staging and
  native/server/client settlement pass. For two 2 MiB files, ordinary output
  model is 4 MiB, receiver non-inherited model 16 KiB, and completed semantic
  logical writes 6 KiB / two write attempts. Whole-protocol traffic was 34,080 /
  34,081 / about 30,300 bytes respectively. Returned write bytes are measured;
  generic output is modeled, and neither attests physical writes/sharing.
  One warm sample with startup/bridge overhead supports no elapsed/worker/Ox
  gain. Forced capture/pump/deadline/client-timeout/crashed-supervisor controls
  now qualify guarded cleanup; catastrophic supervisor loss records native PID
  absence without inventing native-owner reap proof. CPU budgets remain per
  endpoint, not one machine-wide cap for both same-host processes. Raw receipts
  and exact source provenance are in `bench/sync/results/`; the broader SOL
  performance matrix, physical storage, aggregate RSS and SDK work remain open.
* Historical sync benchmark materialization uses exclusive borrowed output descriptors with
  `Unix.LargeFile.lseek` and short-write/EINTR-safe `Unix.write_substring`, rather
  than a native `pwrite` syscall. Logical-byte counters accumulate successful
  returned bytes; call counters include attempts/retries. Do not describe these
  receipts as syscall-level `pwrite` telemetry. The newer POSIX positional-write
  implementation above has separate source and qualification evidence; it does
  not reinterpret or replace those historical elapsed measurements.
* Resource scope remains explicit: device keys are ephemeral per-process
  accounting, not mount incarnations, physical disks or cross-process budgets.
  The integer key representation is qualified on this 64-bit macOS host.
  Ordinary copy system calls, native SDK allocations and unrelated programs are
  outside this gate. Historical eight-credit transfer admission undercounted bound semantic
  publication paths and omitted retained target proofs. The retained 24-credit
  implementation above supersedes that callback-only lifetime; nine validation
  credits now describe a workspace loan within its bound envelope. Complete
  process/memory policy and measured real storage limits remain required. No Photo payload,
  catalog/cache/volume access, Adobe invocation or preview publisher occurred.

* Semantic observation continuation (2026-10-13): immutable format handles now
  optionally declare bounded field observations with versioned schemas and
  descriptive/rendering/identity/workflow/opaque categories. Explicit report
  requests interpret complete retained packets in OxCaml workers; ordinary
  transfers keep their existing inspection path and cost. DNG's bounded
  namespace-aware XMP subset hashes exact attribute/subtree encodings plus
  namespace context. It reports potential property meaning without RDF value
  canonicalization, rendered-pixel identity, archived-base inference or merge
  authority. Camera Raw nested masks/AI are included in their property's full
  subtree. Unknown/unsupported structures remain explicit. `semantic-inspect-v1`
  adds bounded SIR/1 properties while SIR/0/SDE/0/SDR/0 bytes and exact archive /
  conflict decisions remain unchanged; previous SIR/0 peers still report bytes.
  The diagnostic inspector JSON is version `unison-semantic-inspect/1`.
* Current observation qualification: 968 focused XMP checks and 1,029 independent
  XML mutations per compiler, all 797 malformed mutations rejected, three
  parser negative controls per compiler; 15 report codec/bounds/display groups;
  eleven actual local/remote CLI cases per compiler including a previous SIR/0
  peer; a second registration-only format declares workflow fields through
  unchanged dispatch and passes both directions. Independent review closed
  anonymous-subject conflation, unsupported Description XML qualifiers and
  truncation of the advisory explanation. Fresh Make stock `unison-build-hjv53vmp`
  and Ox `unison-build-9ukegu58` plus Dune 3.22.2 stock/Ox build/selftest pass.
  All 313 production/package/INSTALL inputs match. Current remote SDE /
  24-file bidirectional / upstream old-peer and legacy CLI report reruns pass.
  Scope, source/test/binary/log pins are in
  `tests/qualification/semantic-observation-20261013.json`; the normative contract
  is `doc/semantic-observation-v1.md`.
* Independent SDE/SDR conformance now has exact checked-in LE/BE DNG and multi-
  region base/target/request/envelope goldens, independent Python preservation
  transcript and codec, 83 pinned wire/boundary vectors and private nonce /
  preservation-domain negative controls. Both compilers pass 127 commands /
  2,033 assertions, including 1,836 strict-prefix rejections and exact
  materialization. `tests/semantic/conformance/qualification-20261013.json`
  preserves the preceding source receipt; no wire-schema change occurred.
* Explicitly capped SDK area-task host source is implemented under a separate
  experimental artifact/build ID/argv protocol, unavailable to current Unison
  callers. Default v1/threads1 still delegates the known SDK reference path.
  Both modes compile against actual SDK 1.7.1/2724 headers without linking or
  executing Adobe code. The Adobe-free scheduler passes 789 assertions,
  ASan/UBSan and a nesting-cap negative control; independent source review
  accepts capped geometry/Start/index/join/Finish and lifetime ordering.
  Nested area/codec work reserves one runnable CPU thread; native JXL may retain
  idle OS threads, so resident threads/memory remain unqualified. Custom sniffer
  notifications and one-thread reference concurrent-entry behavior retain
  explicit limits. Real SDK parity, codecs, cancellation, thread/RSS peaks and
  performance must be qualified before versioned caller support enables this
  mode. Receipts are under `tests/area_scheduler/`; no SDK/preview invocation,
  Photo payload/catalog/cache access or benchmark was performed in this slice.

* Latest Photo coordination (2026-10-13, repair receipt 15:47:03 UTC): owner
  reopened Lux in stable Classic PID 2844; desktop locked at 15:29:55 UTC /
  08:29:55 PDT. Startup/menu continuation awaits unlock. Receiver generation-2
  acceptance and verified Accessibility persist; the earlier PID 10536/start /
  Lux Main-FD/transport/startup observations are historical, not fresh PID 2844
  bindings. External finite oracle window remains unreleased and the original
  Photo `preview_implementation` task retains renderer/publisher ownership.
  Root will coordinate actual readiness after catalog repairs.
* Photo completed catalog-only JPG removal (8,050 images, 25 folders, one root,
  zero physical operations), two exact 1524 relocations/old-branch removal,
  April–June 2016 grouping and 34 inventoried same-volume quarantines.
  Date1540 filesystem repair completed 74 renames, 70 date patches and two
  movie-XMP repairs, reusing 74 rollback clones; preserved-identity catalog
  reconciliation remains pending. Migration1348 preflight closed before any
  move on 1,372 observed filename/import-source shadow rows; its exact typed
  deletion V3 successor is sealed and independently source-reviewed. These
  are Photo-root operations reported in `~/src/photo/catalog-repair-progress-20261013.json`,
  not operations performed by Unison.
* [The accepted finite source packet](../photo/preview-generator/oracle-source-v1/SOURCE-READY-FINAL.json)
  (15:32:27 UTC, SHA-256 `f00803009328ef1ce67b4f3e635ef79527d512f6066845475cd5bf73d59a1f92`)
  bounds the complete recursive photographic dependency graph to eight distinct
  inputs and all logical states, including negative/pilot variants, to sixteen.
  Four groups/six states are historical seeds; current source/settings/dependency
  identities must be recaptured after repairs. Adopt synchronous typed host /
  backend ownership and exactly-once result release. Backend alone reserves
  one atomic CPU/memory lease; scheduler bids do not reserve twice. All engine,
  backend, codec and helper threads/processes share the global 18-credit ceiling,
  with lease lifetime through encoding/validation, child settlement and result
  release. Initial capability is one in-flight call per host; native threading
  and 1/6/18 configurations remain unqualified. The header was accepted as an
  uncompiled project interface; the later pinned ABI assessment records actual
  C/Rust layout/signature witnesses and synthetic OxCaml C-stub transport,
  not a qualified private Adobe ABI or host/backend runtime.
  Private initialization/rendering
  signatures remain noncallable. This packet authorizes no generator build,
  benchmark, native invocation, production publication or full run. Details are
  incorporated into `doc/preview-design-integration.md`.

* Retained-producer follow-on is implemented and qualified (2026-10-13).
  `Copy.fileBound` and separately negotiated `target-binding-producer-v0` /
  `transferFileBoundV0` retain actual output descriptors through data, forks,
  properties, final hashing, source checking, validation and live publication.
  APFS/semantic stages hand over their still-open output before relinquishing
  creator ownership. Existing remote resumes are admitted through the held
  parent before full/prefix hashing; append writers must match before chmod or
  writes. Invalid prefixes restart through the same admitted inode. Commit
  reuses the frozen witness and its actual fingerprint without named reattachment.
  Receiver ticket ownership is local even when its source transport is remote.
* Current qualification: native 170, registry 105, semantic worker handoff 32
  cases per compiler; actual CLI caller 79 per compiler with no exclusions.
  The original identical-byte/new-inode replacement regression now rejects
  the replacement while preserving the foreign candidate, old live object and
  archives, then completes an exact retry. Twelve resume cases and three actual
  semantic producers cover all placements. Both stock caller negative controls
  detect the intended resolution/live-cleanup failures; native and registry
  negative controls pass both compilers. Independent review found and closed
  an unregister-allocation cleanup gap; worker deferral and reused-FD safety
  are included in the 32-case suite.
* Fresh Make snapshots stock `unison-build-bsb4op45` and Ox
  `unison-build-vs8_6edo` pass builds/selftests. Dune 3.22.2 builds/selftests
  pass both in `unison-dune-retained-producer-qcyowr6e`. All 311 production /
  package / INSTALL inputs match current source and both build systems.
  [The retained-producer receipt](tests/qualification/retained-producer-publication-20261013.json)
  pins current source, tests, binaries, logs and caller evidence. Current Ox
  remote SDE / 24-file bidirectional / old-peer reruns pass. Generic APFS and
  synthetic validation receipts retain their preceding source scope; no new
  Adobe SDK or preview invocation, production data change or performance claim.
* Remaining ownership limits: direct exclusive creation can preserve an unproven
  temp leaf if first adoption fails; initial old-temp pathname cleanup and a
  descriptor-relative resource-fork / AppleDouble creator remain separate
  contracts. Additional-name families retain explicit legacy behavior.
  Cooperative held-parent checks do not prove hostile inode compare-and-swap,
  mount incarnation, crash durability or global/per-volume adaptive admission.
* Working branch: `feat/semantic-dng-oxcaml`, based on upstream `8772d26a2eb77cfd0cb6da81807e81f24f51044c`. Original local `master` at `375ea3ad` is preserved. The user-authorized implementation checkpoint is committed as `2a05c4bf3ffffe4380ad7743c490992b2179f332` and pushed to [querygraph/unison](https://github.com/querygraph/unison/tree/feat/semantic-dng-oxcaml), verified through SSH and the GitHub branch API. The fork was created because it did not yet exist; `fork` uses SSH and this branch tracks it. Deployment has not been performed. No production photographs were changed.
* Publication scope: the checkpoint contains the tested implementation, owned design/handoff, tests, benchmark receipts and scoped qualification manifests. All 306 production inputs and 14 pinned qualification test files in the staged checkpoint match the publication receipt. External coordination receipts remain local. The retained-producer follow-on adds `FinalPublication`/`TargetBinding`, Copy/Files and semantic stage handoffs, build wiring and independent native/registry/worker/caller controls. Its current qualification is recorded above. The earlier pre-producer draft and its reproduced gap retain their historical source pins; they are superseded by this qualified follow-on for the regular-file scope.
* Current goal tracker: `active`, verified again during the user's status
  request on 2026-10-13. The user resumed the goal after the earlier unexplained
  `blocked` observation at 12:32:21 UTC; root and the participating agents had
  reported no goal-state mutation. Implementation continues with the final
  live-file binding slice below. The external preview oracle window remains
  unreleased independently of this goal's active state.
* Implemented: stock/OxCaml compatibility fixes; general APFS private basis/staging clones and same-offset receiver write skipping; bounded DNG parser and complete SHA-256 preservation proof; experimental SDE/0/SDR/0 codecs; negotiated remote and local semantic transfer with ordinary fallback; typed domain workers sharing a CPU budget with external helpers; optional precommit Adobe validation. This is a working first implementation, not completion of all milestones below.
* Ownership at the switch: the Astra agents completed the pure extension/workers, APFS/local/remote integration, and helper/Adobe driver work. Root continues integration and documentation under Sol. Sol completed the cached-hash comparison, endpoint-local validator settings, production resource admission, physical-core automatic worker budget and resource-boundary review, including fixes/regressions for connection teardown.
* Native standard OCaml 5.5.1 and OxCaml 5.2.0+ox builds/selftests pass. A stock→Ox→stock archive smoke test passed. Use `python3 tests/build_snapshot.py --compiler-prefix /absolute/compiler/bin --selftest` to build current uncommitted source in isolation; shared-tree ignored artifacts are not evidence. See `doc/oxcaml.md` for compiler constraints.
* Semantic kernel suites pass both compilers: hashlib differential SHA vectors, TIFF byte orders, exact materialization, stale/same-inode rejection, opaque trailers, alias/cycle/duplicate/unknown/private structures, request binding, truncation/corruption and 2,000 randomized inputs. Parser eligibility is intentionally narrow; unsupported files use ordinary transfer.
* APFS native descriptor/property suites and remote rsync suites pass, covering shifted matches, shrink/grow, hardlinks, clone policies, interruption/retry, xattrs/resource forks/ACL clearing, and read-only source descriptors. ACL removal and staging chmod now operate on a held descriptor. A same-UID hostile namespace is not a sandboxed threat model. See `tests/CLONE.md`.
* Direct local tests exercise the cross-volume producer without mounting a volume. Production local copying now prefers a direct source clone and otherwise uses asynchronous source/basis proof and materialization jobs. Its 32 MiB fixture checks concurrent proofs, owner-loop responsiveness, exact output and cancellation/error cleanup. This does not establish a measured real cross-volume speedup.
* Remote SDE works in both directions; opaque/layout changes and unmodified v2.53.5 peers fall back. `semanticPlanV0` has per-command request/reply limits before body allocation and bounded fields. Retained proof plus fresh nonce binds responses. Shared legacy RPC headers remain outside those limits. Normative current wire format: `doc/semantic-delta-v0.md`.
* Typed workers passed 36-domain/72-hash and proof/materialization tests on both compilers, including shared permits, cancellation, mutation and descriptor lifetime. `SemanticRuntime` owns the singleton per-process budget. Legacy Lwt/RPC/archive state stays on its owner. The Domain.spawn boundary is manually audited and retains OxCaml safety alerts; it is not compiler-proved portable. This branch requires OCaml 5/OxCaml, and all-core correctness tests are not throughput claims.
* `Files.renameLocal` validates private receiving candidates before destination checks, rename and archive changes. A newly received directory uses bounded parallel consumers under the same CPU budget. Validation covers `.dng` files independently of semantic eligibility. Finalized data/resource forks are checked against the expected archive where available. Rename-only moves and unchanged/property-only files are outside received-content validation; no validator is given a live moved inode.
* Helper/validation suites pass 32 synthetic cases on both compilers. Connection teardown now synchronously kills/reaps helpers without another owner-loop tick; worker cancellation reaches its Atomic flag immediately. Cleanup resources use stable physical identity, avoiding mutable structural hash keys. The actual Adobe SDK 1.7.1 build 2724 driver passes 14 controls, including lossless JPEG and JPEG XL DNG decoding, old/new/both/missing raw digests, malformed XMP and corruption failures that return exit zero. See `tools/adobe-validator/README.md`. The pinned local build is `/private/tmp/unison-adobe-driver-build`; read its manifest for the pin. SDK source is external and no Lightroom UI parity is claimed. The initial driver reserves one CPU thread per file; audited JXL total-thread semantics also give one. Multiple files share the available core budget.
* Pre-Sol-fix combined native snapshots pass builds/selftests: OxCaml `unison-build-excxxg1_` and stock `unison-build-7pouvz0t` under the host temporary directory. Actual Adobe receive-gate tests pass on that Ox binary: new file, remote XMP patch, four corruption rejections retaining the destination, recovery, and a 36-file directory. Command: `python3 tests/test_adobe_sync.py --unison /absolute/build/src/unison --sdk-build /private/tmp/unison-adobe-driver-build`. Stock and Ox synthetic precommit suites pass; that Ox snapshot also covers cleanup failure and quarantine. Full clone/local/remote/old-peer/framing/generic-format suites passed the preceding `unison-build-njghu6yj`. The newer endpoint/admission changes require combined requalification. See `tests/README.md` for commands.
* Generic production dispatch is complete: `SemanticFormats.register` selects trusted immutable handles by `semanticprofile` and negotiated capability; the DNG shorthand remains. A registration-only second synthetic format passes local and both remote directions. No format-specific branch is needed in the worker/transfer machinery. `tools/semantic-inspect` provides read-only JSON classification, extents, hashes, payload size and fallback reasons; tests pass both compilers.
* Validation now snapshots the entire private candidate tree before any helper and checks it after all helpers settle, including hidden/temp names, types, symlink targets, stat identity and configured properties/resource forks. Mutation rejects under require and warn. Rejected staging is moved to a fresh quarantine name before deletion, so failed cleanup cannot poison normal resume. Tests cover hidden injection, late sibling chmod, symlink replacement, old live destination preservation, slow-helper settlement, and an immutable injected child surviving quarantine while a clean retry succeeds. This is an integrity fence for trusted local helpers, not a hostile same-UID sandbox or atomic filesystem transaction.
* Dune 3.22.2 text builds/selftests also pass stock and Ox. Fixed a pre-existing Dune omission by linking only the selftest initializer archive into the text executable; GUI configuration is unchanged and unbuilt. `src/.depend` has been regenerated. Practical usage is in `doc/semantic-sync.md`.
* Endpoint-local validation configuration is implemented: `Prefs.makeEndpointLocal` omits outgoing settings and ignores incoming values before decoding, including aliases. Each endpoint loads optional `endpoint.prf`; only validator executable, pin, build ID, thread count and timeout are allowed there. Sync policy remains transmitted. Stock `unison-build-t2dsic9a` and Ox `unison-build-gi6oltc3` pass builds/selftests and new preference/configuration regressions, including distinct tools on the two hosts, malformed/legacy incoming settings, reverse direction, missing/pin-mismatch rejection and old-peer feature rejection. Existing stock validation tests also pass. The real SDK integration test now gives the receiver its own configuration directory.
* Admission is implemented: three fixed two-transaction regions became one owner-loop resource gate, separate from CPU permits. Profile payload declarations (DNG 1 MiB) are enforced before packet copying; estimated payload/descriptor credits are reserved before opening/cloning. Source leases cover RPC response marshaling and output consumption. Consumers leave one worst-profile source reservation available for bidirectional progress; per-request response allocation uses the selected profile bound. All 11 deterministic admission tests pass stock/Ox, including cancellation reentrancy and source headroom. Eight local candidates exceed the old proof-concurrency limit; 24 independent remote SDE transfers split between both directions pass under both 26 MiB/24-FD and 17 MiB/16-FD budgets, with exact results and clean retries. Mixed actual domains/weighted helpers share their CPU budget correctly.
* Resource review found and fixed connection-lifetime leaks: queued replies and outstanding RPC consumers now fail on teardown, and output failure never appends a second reply. Generic Lwt closes detach and settle registered I/O before descriptor reuse, and write-readiness completion removes the correct queue entry. Ten isolated close/reuse tests pass both compilers; the original implementation fails the first regression. RPC tests use actual blocked pipes and queued replies, check released scopes and dynamic allocation bounds, and pass both compilers. Socket-server cleanup drains replies waiting for a half-duplex token and sweeps resources even if a close continuation raises. The persistent-server regression passes stock/Ox: withhold the write token until two 1 MiB source replies hold all 17 MiB/16-FD capacity and a third waits, disconnect, reconnect to the same server PID, then complete three exact replies with zero remaining credits. Removing only the server output-stop call reproduces the retained-credit leak in a private negative-control build.
* Previous combined Make checkpoint: stock `unison-build-tvjy_dzv` and Ox `unison-build-mv26_zvm` pass native builds/selftests. Ox is refreshed through the final socket-server cleanup fix and passes local/eight-candidate, generic-format, remote/bidirectional/old-peer, general APFS clone, RPC scopes/limits, endpoint preferences, distinct validator configuration, synthetic validation/tree/quarantine, and actual Adobe SDK receive-gate suites. The actual SDK test covers new files, XMP patches, four corruption rejections preserving the destination, recovery and 36 received files. Stock covers admission/kernel/workers/mixed helpers, local/multicandidate, bidirectional remote, helper validation and RPC scopes. The corresponding Dune 3.22.2 builds/selftests pass both compilers; logs and exact source manifest are in host-temp `unison-dune-final-spg_sa2g`. The persistent-server regression also passes both compilers, with a negative control reproducing the fixed leak. Current-source qualification after reporting and sparse writes is recorded below.
* Cached SHA benchmark artifacts are in `bench/semantic/`: stock/Ox throughput at 36 workers was 5694.2/5679.3 MiB/s, about 15.8× the one-worker result, with no demonstrated OxCaml-specific gain. A separate 18-versus-36 comparison measured 4709.8/4617.5 MiB/s at 18 and 5175.9/5103.4 at 36 (about 10% higher). Both runs used one cached 64 MiB synthetic file, 72 jobs per batch, one warmup and five measured repetitions. Results vary with ordinary host activity; CPU/wall counts logical CPU equivalents, not physical cores. This is neither a sync/APFS nor an Adobe throughput benchmark. After the user highlighted 18 physical/36 logical CPUs, automatic macOS sizing now selects physical cores (18 here), with explicit `semanticworkers = 36` available. Runtime debug output reports detected counts and effective limits. The separately measured Adobe validation-core comparison is recorded below.
* Earlier next-work plan, superseded by the newer checkpoints above: regular-file final live publication now binds the logical root, followed target and retained finalized producer; independent SDE/SDR vectors and per-filesystem execution admission are also qualified. Intermediate publication, held-object observation, borrowed leases, nonblocking opens and typed range-copy hardening retain their receipts. Keep passing reporting, sparse-write, endpoint/admission and teardown regressions. Remaining work includes complete-lifetime FD/memory bounds, initial old-temp cleanup, lifecycle/native range contracts, broader DNG coverage, optional semantic reconciliation, representative production transfer/crash measurements, platform/GUI qualification and the remaining acceptance matrix in `doc/implementation-status.md`. JPEG remains a planned second profile.
* New user requirement, 2026-10-13: support separable Lightroom preview placement in the architecture. Monitor-target renditions for the 5120×2880 display belong on Quasar; other sizes and cache databases remain on Ten. The catalog/renderer Codex owns native registration and rendering qualification. Its handoff is `LIGHTROOM-MONITOR-PREVIEW-HANDOFF-20261013.json`; design references are under `~/src/photo/preview-generator/`. The contracts are in `doc/component-placement-v0.md` and `doc/lightroom-preview-placement.md`: logical component identity, local placement, filesystem capabilities and recoverable multi-volume publication are independent of same-file SDE/0. Modern per-level JPEGs and legacy packed `.lrprev` are distinguished, as are native 5120-long-edge, monitor-fit and original 1:1 geometry. Publication/group runtime remains unimplemented and native link/rewrite/registration qualification belongs to the catalog session.
* Current storage update: Quasar is now 8 TB APFS, UUID `E31B795D-FA19-4938-97E2-B6ED56A7C78F`; read-only diskutil/statvfs verification at 2026-10-13 10:05:17 UTC gives 7.200061 TB after an illustrative 10% total-capacity reserve. Ten remains Journaled HFS+, UUID `F807D30D-753C-3975-A919-AB63DECC389A`, budget 8.336401 TB under that model. The prior 6 TB HFS+ Quasar identity, 5.399 TB budget, earlier RAID/member mapping and combined evacuation estimates are historical. Do not repeat formatting or inherit old capability/binding generations from the mount name. The change happened outside this thread; no formatting, data movement, catalog edit or application stop occurred here. Optional Ten migration remains separate, with a complete manifest and fresh topology/capacity gates in `doc/preview-storage-migration.md`.
* Sparse metadata writes are qualified: fixed-layout materialization skips identical absolute 4 KiB comparison windows, clips writes to editable extents, combines adjacent changed windows and returns actual logical-write/syscall counters. No SDE wire change or weaker verification. Sparse/first/last/disjoint/adjacent/unchanged/full/multiple-region cases pass stock/Ox, including 262,150-byte packets where an interior one-byte edit writes 4,096 bytes. These are logical writes, not physical APFS allocations. Immutable worker and owner reports expose the counters; existing unit-returning APIs remain compatible. Current Ox local/multicandidate, remote/bidirectional/old-peer and actual Adobe receive-gate suites pass again.
* Generic lazy UI observations are implemented: bounded negotiated SIR/0 summaries expose current-replica hashes, classifications, fallback reasons and escaped/truncated metadata samples. Explicit Diff/details inspect enabled profiles without default tree hashing; formatters consume a one-shot observation without RPC/hash work and recheck at most two local path stamps. Filename suffix hints are advisory and do not filter transfer eligibility or prevent renamed DNG recognition. Archive/conflict decisions remain exact-byte based, with no base-history or rendering-equivalence claim. Both compilers pass report/codec tests (including 2,000 malformed inputs), 14 real CLI scenarios each, old-peer fallback, one-shot/stale/row/symlink/disconnect details tests, and a second generic format's local/remote annotations. Fresh native snapshots `unison-build-_t1yqi9z` and `unison-build-k553ql8w` build/selftest; all 291 production source files match the refreshed Ox build. Fresh Dune builds/selftests also pass stock `unison-dune-stock-vq2b5snf` and Ox `unison-dune-ox-by4p3dlz`, with production inputs matching the live tree. The normative observation protocol is `doc/semantic-report-v0.md`.
* A further lifecycle review reproduced two late-completion bugs and fixed them: worker observer exceptions now settle all detached siblings and rearm the persistent pump before surfacing the error; old disconnected RPC requests suppress only their expected terminal failure after their work settles. New worker tests pass both compilers and RPC tests preserve unrelated failures. Independent private negative controls reproduce both former failures; fixed harnesses complete new jobs, shutdown, and a later-session request without leaked credits.
* Actual SDK validation-core benchmark is complete: deterministic 6000×4000, 16-bit CFA fixtures are qualified through the pinned driver: uncompressed 45.8 MiB, lossless JPEG 37.2 MiB and JPEG XL 36.5 MiB. Positive and corrupted-digest controls pass; fixture-only rebuilding preserves the validator executable/pin/manifest. `bench/adobe/` exercises production validation, hash workers, weighted helper permits and resource admission. Five 72-file measured batches per parallel configuration gave 18→36-worker medians of 16.46→16.97 files/s uncompressed (+3.1%), 13.56→15.22 JPEG (+12.3%) and 5.39→5.98 JXL (+10.9%). The single 72-file serial controls were 1.25/1.08/0.43 files/s. Total CPU per batch increased 69–79% at 36; 18 remains the balanced default and 36 an explicit throughput option. All 42 batches and 2,811 measured/warmup receipts passed with zero final credits. Raw receipts, source/fixture/compiler/SDK hashes, topology and declared uncontrolled user background work are in `bench/adobe/results/macos-x86_64-18-vs-36.json`; interpretation is in `bench/adobe/README.md`. Team builds were idle, and sources matched at measurement completion before subsequent hardening. This is cached synthetic validation-core evidence, not full-sync, physical-storage, Lightroom UI or OxCaml-specific performance. No catalog/photos are read or changed.
* Post-benchmark native hardening: clone-stage OCaml result blocks are allocated before acquiring native resources, removing the success-path OOM allocation exposure by inspection; allocation fault injection remains unqualified. Source/private-file opens are nonblocking before regular-file checks, and private basis/output checks require separate singly linked regular inodes before permission changes. Stock/Ox native FIFO, immutable-basis, exclusive-output, ACL/xattr/resource-fork and flagged-file fixtures pass in `/private/tmp/unison-clone-hardening-stock-s313ti8y` and `/private/tmp/unison-clone-hardening-ox-ga0t1eey`. The old native source reproduces a FIFO-open timeout in `/private/tmp/unison-clone-fifo-negative-jnnysix2`. Corresponding ML owner opens are nonblocking; all five FIFO paths (sync/async source, source planner, validator candidate and executable pin) reject promptly with clean resources and usable exact follow-up on stock/Ox. Private old-open controls reproduce all five timeouts on both compilers. Trusted staging-directory assumptions still apply; these checks do not defeat an arbitrary same-UID namespace adversary. `doc/foreign-boundary-audit.md` records the manual audit and unresolved OS/ABI/fault limits.
* Filesystem outcome slice delivered: `CopyRange` now carries exact completed prefixes, copied/unreported success, compatibility-unsupported status and operational failure. `Copy.copyFileRange` uses it, permits exact suffix fallback only for classified unsupported acceleration, and propagates EIO/ENOSPC/permissions/EBADF. Zero/invalid progress fails; notification/cancellation errors are outside native classification and cannot trigger fallback. Eleven injected-step cases pass stock/Ox. Legacy EINVAL/ESPIPE/ENOTSOCK compatibility remains explicit; native range adapters still need precise results to narrow these conventions. The strict APFS and constrained planner additions below close further parts of `doc/filesystem-capabilities-plan.md`; mounted-generation observations and production planner integration remain open.
* Current combined qualification after those fixes: Make snapshots stock `unison-build-zkko4cdm` and Ox `unison-build-6pkjg_pp` build/selftest; 207 `src` ML/MLI/C/H inputs match the Ox snapshot and dependencies are refreshed. Ordinary clone-transfer integration passes both compilers, including shift/duplicate/grow/shrink/no-op/off/flags/interruption. Ox additionally passes local producer/semantic/multicandidate/cancellation/generic format, remote/bidirectional/old-peer SDE and actual Adobe receive-gate suites. Fresh Dune 3.22.2 text builds/selftests pass both compilers in host-temp `unison-dune-copyrange-final-i8pdgv4z/{stock,ox}`; verification and source manifests are retained. No production source changed after these snapshots.

* Explicit Astra preview coordination received and integrated, 2026-10-13: `doc/preview-design-integration.md` records the reviewed four-stage architecture, exact dependency bundle/renderer/publication interface proposals, modern native format, lifecycle/recovery gates and current capacity. The new local `/root/preview_generators` integration-review task acknowledged the handoff; the existing photo-session `/root/preview_implementation` remains implementation owner. A direct queue to its unloaded sub-agent was rejected by the app server, so the complete review/findings were queued successfully through the Lightroom takeover parent for forwarding (receipt `PREVIEW-REVIEW-FORWARD-20261013.json`, exact message `.txt`). No faithful standalone current-edits backend is qualified: the inspected DNG SDK render path does not consume the complete CRS/mask/AI contract, and Camera Raw host interfaces still need independent initialization/ABI/ownership/threading and matched pre-JPEG proof. Both standalone Rust/OxCaml engines may share a qualified backend/codec, count native threads within 18 CPU credits and benchmark matched 1/6/18 compute-only/end-to-end before a full run. Policy B's 134,582-key newer gap allowances 1.837200 TB Quasar + 0.828267 TB Ten fit the planning budgets; full 761,466-key Quasar allowance 9.100375 TB still exceeds 7.200061 despite mean 4.009232 TB. Native allocation evidence remains required. The takeover session owns Lux adoption and finite oracles; current oracle readiness is recorded in the correction below. No Adobe invocations, Photo payload reads/heavy benchmarks, production Main/cache/volume writes or application stops are performed by this integration. The stale serialized `getServerHandle()` wording was corrected; the later owner receipt qualifies existing-server entry/callback transport while current-content and publication gates remain.

* Oracle evidence correction confirmed, 2026-10-13: installed Classic 15.6 per-level Preview objects carry digest but no UUID; never require or synthesize `level.uuid`. Bind whole-pyramid UUID/digest to current Main, retain expected dimensions from matching native PyramidLevel rows before decode, then compare actual decoded dimensions and level digest afterward. Orientation comes from the captured current Main/native ImageCacheEntry mapping, not an invented PyramidLevel orientation column. Positive registered `fileSize` must equal stable actual disk bytes; mismatch fails evidence and absent/zero/unknown stays unqualified. Native stale fallback is `lastCacheEntryForImage(imageId)`, subject to the same current binding. Source review is `~/src/photo/NATIVE-DIRECT-PREVIEW-INDEPENDENT-REVIEW-20261013.md`; the owned integration/placement docs incorporate its post-native deadline and candidate-versus-durable evidence distinctions. This changes the oracle contract, not Quasar/Ten placement. The takeover owner now reports Lux accepted/adopted and open in stable 15.6. The subsequent owner receipt verifies helper access and transport; the finite native registration/load/restart window remains owner-controlled and closed. Preparation/adoption receipts authorize no full preview-generator run. Our preview integration task acknowledged this correction.

* Earlier takeover status before the current Photo repair update, 2026-10-13: the user/root confirms Quasar APFS 8 TB/new UUID and existing Policy B capacity evidence. The full 761,466-key mean (4.009232 TB) and summed per-photo P95 (6.006848 TB) fit the 7.200061 TB planning budget; the conservative 9.100375 TB allowance does not. Representative native output/allocation batches remain required before a full run. Stable Classic 15.6 Lux is running, all seven performance phases pass on autostart and Cloud UI reports Synced/Pause Syncing. Existing PreviewServer entry/callback transport is separately qualified; standalone rendering, native registration/load/restart and split availability remain unqualified, with finite oracles controlled by the takeover root. Ten retains its 9.18 TB cache on HFS+; cross-volume recovery and native symlink lifecycle gates remain. This Unison task makes no independent live-cache changes.
* Portable filesystem generalization implemented: `CloneRange` streams aligned head/interior/tail operations, separates native-whole/composed-whole/range support, checks fresh injected owner/backend/source/destination identities and generations before every operation and completion, and validates exact contiguous progress. Only known-prefix unsupported sharing can copy the remaining suffix; operational errors, indeterminate mutation, stale bindings and malformed claims stop. Independent stock/Ox tests pass 48 named cases including 960 geometry combinations, immutable-basis reconstruction, write-count/sentinel checks and bounded cancellation of a huge request. These trusted endpoint-local records and injected observations are not native remount detection, a capability cache or a production range sink. No new ZFS/ReFS runtime qualification is claimed.
* Strict APFS stage result implemented: `Fs.clone_stage_status` and the legacy option ABI share one native transaction. Production Copy and local/remote semantic consumers use explicit shared-stage or scoped platform/source-kind/source-flags/cross-device/unsupported results; operational errors preserve their native phase and never become declines. Nonregular bases fail promptly. Both compilers pass direct native ABI/scope/phase/exclusivity/FD tests. Combined Make builds/selftests and synthetic ordinary/local/remote/old-peer/actual Adobe receive-gate checks pass; final source qualification is being refreshed after the resource-cleanup review. Owned-name cleanup is best effort and crash/fault recovery remains unqualified.
* Native pending-signal cleanup hardened: dispatch pending callbacks before native ownership, enter a no-pending blocking section and free all path/attribute buffers before reacquiring the runtime. An independent private counter/injected-Sys.Break test passes stock/Ox: corrected declined-stage path owns zero buffers, while an old-release negative control leaks exactly three; source and descriptor counts remain unchanged. Pinned Ox uses `Sys.with_async_exns` for the fixture's asynchronous Break catch. This qualifies that C buffer window, not arbitrary successful-result asynchronous ownership, OS deadlines or crash cleanup.
* Build metadata corrected: this fork's domain workers require OCaml 5, so both opam packages and INSTALL now declare 5.0 instead of upstream's stale 4.08 floor. The pending-action/no-pending C APIs are also unavailable at 4.08. Qualified text compilers remain stock 5.5.1 and pinned Ox5.2; the floor is not evidence of builds on every newer version or GUI/platform qualification. Old compiled peers retain negotiated fallback.
* Final combined build checkpoint for this slice: Make stock `unison-build-dcdkibew` and Ox `unison-build-dcmedl_v` build/selftest with 214 ML/MLI/C/H/parser/build/package/INSTALL inputs matching the live tree; root `.depend` refreshed from the Ox snapshot. Dune3.22.2 stock/Ox builds/selftests pass in `unison-dune-clonerange-final-ug5mj0pq`, with all 298 broader production/package/INSTALL inputs matching frozen and post-build manifests. Ordinary transfers pass both compilers. Ox local producer/semantic/multicandidate/cancellation/generic dispatch, remote/bidirectional/old-peer transfer, actual Adobe receive gate, 14 SIR CLI/old-peer cases and all five FIFO paths pass on these final binaries. Source remained frozen through qualification. Evidence and source/test hashes are in `tests/qualification/filesystem-20261013.json`; no benchmark claim comes from these runs.
* Descriptor adoption guards qualified: Copy channel creation/registration, sync ownership-closure initialization, async transaction/candidate creation/registration, source FD retention and remote source/report holders protect synchronous failures before workers borrow. Retained failed registry entries are marked empty/closed before best-effort removal, preventing recycled-FD closure. Independent private fault tests pass 40 current cases per compiler, while 36 old-handoff controls per compiler reproduce prior descriptor leaks. They check real FD/stage cleanup, original exceptions/source preservation, reused sentinel survival, exact follow-up and settled credits. Explicit synchronous Out_of_memory injection is not actual heap exhaustion; arbitrary asynchronous ownership remains unqualified. Rsync uses the tested common adoption helper; its subsequent Some-ref rollback is source-reviewed/normal-integration-tested without separate fault injection.
* Native binding design review is now implemented by the observer/lease slice below: one fixed-buffer held-FD observer (`fstat`, `fstatfs`, separately validated volume-UUID attributes) plus an abstract transaction-local owner lease. Volume attributes must not be combined with file identity attributes: current XNU can substitute the mount's root vnode for volume queries. Native file/volume identity is distinct from owner generation; public UUID/fsid/inode/write-count fields do not prove a mount incarnation. Fresh held-directory/path/stage checks and parent-relative publication remain separate precommit work. Synthetic replacement/dup2/invalidation/error/buffer tests are qualified; no capability cache or Photo mount operations. See `doc/filesystem-capabilities-plan.md` for limits and the next slice.
* Newer native readiness receipt read during continuation: `~/src/photo/preview-unison-coordination-20261013/RECEIVER-AND-ORACLE-READINESS.json`, 2026-10-13 10:45:07 UTC, reports helper access verified, all seven performance phases passed and existing `activePreviewServer().previewServer.server` entry/callback proof. This supersedes the earlier helper/transport-under-qualification status, not the remaining native-content gates. The external oracle window remains explicitly closed (desktop relocked/root sequence owns access), and heavy Photo benchmarks and production publication remain unauthorized. Three converted legacy controls preserve 18 JPEGs exactly but lack terminal native metadata; reviewed one-control registration source has not been invoked and load/cold recognition is pending. Standalone current-edits rendering remains unqualified. Unison performs no independent native/cache mutation.

* The latest native preview correction is authoritative for placement: read
  `~/src/photo/preview-registration-findings-20261013/FINDINGS.json`. Native conversion
  preserved all 18 JPEG sections from three controls, but all three remain
  unregistered; terminal rows are absent for six inspected keys. Existing transport
  is qualified, while prepared one-control `touchPyramid` registration is unexecuted
  and requires actual preserved current UUID/digest/header plus absent Pyramid,
  levels and mappings. The live store owns its persistent native Auto savepoint;
  never author commit/rollback/flush. Preserved JPEGs may use external AgHg AdobeRGB
  without embedded ICC, so bind actual profile provenance/dependencies. Critically,
  installed-loader source checks highest registered file existence/mtime for smaller
  level requests: missing Quasar may block Ten lower levels. Treat it as required
  for affected pyramids until root-owned native mount-loss fallback qualification;
  do not promise lower-tier independence. Split layout, offline publisher and journal
  remain; desktop unlock/oracle window and full-run gates remain. Photo-parent
  forwarding and original preview-task acknowledgment were recorded for the earlier
  handoff (10:45:49 UTC); the newer forwarding status is below. No native/cache/volume
  mutation was performed here.

* Historical oracle-contract coordination: preview work here remains interface/review
  only. The ORIGINAL photo-session renderer/publisher task has ACKNOWLEDGED the
  exact corrected oracle contract, read the independent review and audited the
  pinned direct-probe source. Canonical acknowledgment/source pins are in
  `~/src/photo/preview-unison-coordination-20261013/ORACLE-CONTRACT-CORRECTION-ACKNOWLEDGED.json`.
  This supersedes the earlier pending-correction acknowledgment status and does
  not release the oracle window. The readiness receipt binds completed
  Smart/core acceptance (both exit0, no skips/failures; acceptance SHA256
  `9d2be438ea619913ace0ddb1da7626d736a8a504a6a19597d5b22768fb4a526e`),
  active Morrobay generation2, historical PID10536/start, Lux MainFD and owner identity,
  Helper Accessibility ALREADY GRANTED AND VERIFIED, all seven startup phases
  and the first full automatic renewal passed. No grant is pending.
  EXTERNAL ORACLE WINDOW NOT RELEASED: desktop relocked/root sequence pending.
  Await explicit root-issued finite-window release; no heavy Photo benchmark,
  external Adobe invocation or production publisher starts here. The native
  one-control registration source passed25 independent transport/registration
  tests but is uninvoked; recognition and cold restart remain unresolved. Stable
  Classic15.6/Lux/PID10536 was the process bound by that earlier receipt;
  the latest Photo repair receipt reports PID2844. ABI
  investigation stays source-only under the original photo implementation
  owner; no full generator run.

* Native filesystem continuation: `FileObservation` now collects full-width
  device/inode/filesystem/volume identities, size/link/flag constraints and
  nanosecond timestamps from held macOS descriptors, validates separately
  requested fixed-size volume UUID attributes, and rechecks file facts. Native
  errors retain phase; missing/zero UUID is explicit absence. It owns no FDs or
  native allocation and changes no offsets. `CloneLease` provides an abstract
  endpoint owner epoch, fresh paired observation fences and a borrowed-FD bridge
  to `CloneRange`; source stamp changes stop while destination write timestamps
  are permitted. Independent 11 native/parser and 21 native/injected lease cases
  pass stock 5.5.1/Ox 5.2. No immutable-byte, true mount-incarnation or pathname
  publication guarantee follows from these observations.
* Production receiver-rsync integration now pre-establishes private output EOF,
  enrolls the immutable basis/output, rechecks bindings per packet and at EOF,
  and executes shifted matches through `CloneLease`/`CloneRange`. APFS advertises
  no native range-share capability; bounded copying retains exact unsupported
  acceleration fallback inside the copy adapter. Partial/errors become
  indeterminate and fail without retry. Flushed actual FD positions detect quiet
  fallback EOF; channel positions are reconciled after native copying. Static
  lease cleanup invalidates before channel cleanup on connection teardown.
  Initial missing UUID discards the private stage and uses ordinary auto copying;
  mid/final loss is terminal. Source-clone, local producer and SDE paths retain
  their previous mechanisms; native leases are currently integrated into the
  ordinary receiver-rsync path only.
* New Make snapshots stock `unison-build-v2izyqvq` and Ox `unison-build-tpvddl2b`
  build/selftest. Fresh Dune3.22.2 snapshots `unison-dune-observer-final-3wkxzfq0`
  build/selftest on both with 303 matching production/package/INSTALL inputs.
  Ordinary clone sync passes both; Ox local producer/semantic/multicandidate,
  cancellation, remote/bidirectional and old-peer fallback pass. The adoption
  harness's old-control regex now preserves new helpers; all 40 current and 36
  old-handoff controls pass per compiler. Focused actual bound-range adapter
  tests pass 9 groups/27 scenarios on both compilers, covering exact shifted
  offsets, short progress, unsupported suffix copying, quiet EOF, operational
  failures, invalid progress, both endpoint bindings and channel mismatches. A
  stock negative control detects removed channel-position reconciliation. Root
  verified all 303 production inputs against both Make snapshots and Dune, and
  refreshed `.depend` from the qualified Ox snapshot. Evidence is pinned in
  `tests/qualification/filesystem-observer-20261013.json`. No external Adobe invocation or Photo
  payload/catalog/cache/volume work is part of this continuation.
* Preview source-only review found a current ImageCacheEntry orientation
  comparison gap and forwarded it to the existing photo parent for the ORIGINAL
  owner (message `01a13521-01df-7dd0-98de-8393b0af6c79`). The gap is now CLOSED
  IN SOURCE by that original owner and independently accepted. The canonical
  ACK was subsequently updated at 12:14:41 UTC, binding the source correction
  binding fresh raw POST_DECODE ImageCacheEntry imageId/current UUID/current
  digest before comparing native-effective orientation with captured Main and
  decoded pixels. Raw values and native nil/false-to-AB defaults remain explicit;
  a stale pre-load row does not block a valid current post-load mapping. Source
  SHA256 is `82c88b6612818c2f62fc22b42b840273ceaca1208813d8da7a755f7a771d8556`.
  The owner reports 48 mock/source cases, an independent rerun of all 23 mapping
  cases and unarmed syntax preparation. Root source acceptance is
  `~/src/photo/preview-orientation-source-review-20261013/ROOT-ACCEPTANCE.json`;
  `mappingCorrectionNativeVerified` remains false. See
  `doc/preview-oracle-source-audit-20261013.md` for the original finding and
  follow-up. Accessibility is already granted/verified; desktop was last
  observed locked, not rechecked by this source review. The finite external
  window remains unreleased, with no new operational hold or release inferred.
  Native preview work stays source/interface-only under the existing owner.

* Intermediate publication slice is implemented and qualified. Additive
  `Fs.clone_stage_handles` retains the actual creation parent with basis/output,
  preserving both existing two-FD ABIs; 20 native cases pass both compilers.
  `StagePublication` owns a rooted finalizable native context, held directories
  and a CLOEXEC stage witness. Fresh directory/name bindings precede exclusive
  stage-to-normal-temp rename; native ownership switches before post-rename
  exception delivery. Identity-bound cleanup uses the captured parent and
  witness, including after channel adoption fails. Directory identity ignores
  mutable size/link/timestamp facts; separate/followed parents, search-only
  permissions, sibling changes and foreign sentinels are qualified. Single-link
  admission prevents modifying an aliased stage; cleanup removes only our name.
  All 58 native publication/classifier cases pass stock/Ox. Four extra steady
  owned descriptors remain a resource constraint for future scheduling work.
* Root receiver integration passes 86 production-caller cases per compiler:
  actual rsync compression/decompression through EOF, creation-parent rebinding,
  adoption/channel/registration/Some-ref failures, post-rename/pre-disarm errors,
  collisions, foreign sentinels and reference-FD reuse. Missing/unsupported
  identity can decline only during preparation before stage creation; auto uses
  ordinary copying and require fails. Operational/malformed/stale and every
  later-phase error remain terminal. Ordinary reference inputs now open
  nonblocking, require regular files and protect descriptor/channel handoffs,
  so early optimization decline cannot expose a FIFO-open hang. A stock private
  negative control detects removed caller publication cleanup.
* Fresh Make snapshots stock `unison-build-eiyawftj` and Ox
  `unison-build-e0r79j3i` build/selftest. Dune 3.22.2 stock/Ox builds/selftests
  pass in `unison-dune-publication-final-evu31q2x`, with all 306 production inputs
  matching. Ordinary clone sync, 9-group/27-scenario bound-range tests and
  40-current/36-old adoption controls pass both; Ox local/semantic/multicandidate,
  cancellation and remote/bidirectional/old-peer suites pass. Production caller
  logs are retained in `/private/tmp/unison-copy-publication-rrq0dcep` (stock)
  and `/private/tmp/unison-copy-publication-4zzia424` (Ox). Source/test hashes and
  scope are in `tests/qualification/filesystem-publication-20261013.json`.
  This historical receipt qualifies the intermediate stage-to-temp boundary.
  Later checkpoints above qualify regular-file logical-root/followed-target
  binding, final live `Files.renameLocal` and descriptor-relative native scratch.
  Initial old-temp pathname cleanup remains separate work.
  No new SDK invocation, preview operation, Photo/cache/volume work or benchmark.

* Historical final-live implementation plan (superseded for the qualified regular-file scope above) following the source review in `doc/filesystem-capabilities-plan.md`.
  Enroll logical root/follow/effective workdir bindings at endpoint-local target
  setup, carry only a negotiated opaque nonce remotely, and attach the finalized
  candidate witness after forks/properties/paranoid verification. Validation
  must retain a proof across helpers; accepted target identity and root mapping
  must survive backups and the final rename. Preserve ordinary replacement,
  conflict retargeting, directory transactions and AppleDouble behavior. A first
  regular-file guard cannot qualify those other transactions automatically.
  Post-publish failure must suppress archive advancement and reconcile without
  deleting live output. This is source review for subsequent implementation,
  not a completed gate or new native-preview authorization.

* Historical pre-producer final-live draft: `FinalPublication` pins the logical-root/effective
  directories and candidate/target parents, freezes the singly linked regular
  candidate and accepted live object, publishes through held parents and checks
  live readback before archive advancement. Native state becomes Published
  before post-rename errors; cleanup never unlinks published live output.
  Default macOS native forks remain supported when both AppleDouble names are
  proved absent; actual sidecars, move-first directories and conflict retargets
  retain explicit legacy handling. Quarantine precedes rejection deletion when
  the OS permits rename; truly immutable rename failure remains explicit.
  Native tests pass 99 cases and a mutated-publication negative control per
  compiler; source/log pins are in `tests/final_publication/qualification-20261013.json`.
* `TargetBinding` implements negotiated additive setup/rename commands with
  connection/session/root/path/policy-bound, single-use 256-bit tickets. Its
  128-slot registry reserves before native opens and defers borrowed cleanup
  until helpers settle. Fifty focused cases and premature-close negative
  controls pass both compilers. Files holds separate 64-transaction requester
  admission before setup through commit: streaming's ordinary 1000-thread limit
  otherwise permits too many retained directory proofs. These proof descriptors
  are outside `semanticdescriptorbudget`; adaptive/global FD integration remains
  required. Legacy RPC schemas and archive format remain unchanged.
* Combined pre-producer checkpoint: stock `unison-build-xyp54mfd` and Ox
  `unison-build-b0ky8p03` build/selftest, with all 311 production inputs matching
  at that source freeze. Subsequent producer-retention changes are unqualified
  by those binaries. Ordinary clone suites pass both. Current Ox synthetic
  validation and remote/bidirectional/old-peer suites pass. The actual Files
  caller harness passes 62 cases per compiler with two identity controls
  explicitly excluded, separately reproduced as the open producer gap. No new SDK or Photo invocation.
* The predecessor caller audit found the producer-handoff gap now closed by the qualified continuation above. Every current
  materializer closes its data output before final properties/paranoid checking;
  the draft reopens the completed candidate at rename entry. Bound commits now
  recheck expected archive fingerprints even with Adobe validation off, but
  identical-byte replacement before attachment can still be adopted. Existing
  Fileinfo inode stamps retain only 30 bits and may be disabled; they cannot
  substitute for an original full-width producer witness. Retain the actual
  producer descriptor/creation parent, permit planned writes/properties, freeze
  after finalization, and bind paranoid/source verification and rename to that
  same object. Additive bound-copy plumbing must cover all receiving paths.
  The actual caller control reproduced identical-byte replacement being published
  with archive advancement (inodes 304353566 to 304353567); retained evidence is
  `/private/tmp/unison-final-caller-85p9_y0_/case-1/`. Scoped receipts are
  `tests/qualification/final-publication-{draft,caller}-20261013.json`.
  The caller harness is `tests/test_final_publication.py`; its later command-
  bookkeeping syntax typo was corrected and AST parsing passes, without
  relabeling earlier evidence or claiming a rerun. Caller negative controls
  were not run. Keep this slice unqualified and uncommitted until its
  remaining controls pass. Native and registry owners are now implementing
  mutable producer-FD adoption and producer/finalized/commit phases under
  `doc/finalized-candidate-handoff-plan.md`; Copy/Files integration follows.
  Late unwitnessed AppleDouble siblings must be preserved/reported, not blindly
  deleted as owned candidate data. The implementation goal remains active.

## JPEG extension design note

JPEG is a good second profile: application marker segments can carry Exif, XMP, IPTC and ICC data separately from the compressed scans and decoding tables. Adobe XMP uses identified APP1 segments, with a separate chunked Extended XMP representation; ICC profiles use identified APP2 segments. Marker number alone is not enough to classify contents. Exif includes TIFF offsets and possibly a thumbnail. Orientation, colour interpretation/profiles, gain maps, and editing instructions affect presentation, so unchanged compressed samples do not mean unchanged rendering.

Start a future `jpeg-xmp-fixed/0` profile with one ordinary, bounded XMP APP1 packet at the same offset and size in both files. Preserve and hash every other byte, including marker framing, tables, scans, unknown APP segments, and trailing data. Decline Extended XMP, duplicate/ambiguous packets, malformed marker streams, and layouts not covered by the parser until implemented deliberately. A JPEG parser must handle entropy-byte stuffing, restart markers, multiple/progressive scans, and post-scan markers; it cannot find metadata by searching arbitrary compressed bytes for marker-looking sequences. MPF/MPO offsets, auxiliary images, gain maps and JUMBF/C2PA content require explicit treatment before structural edits or claims about authenticity/rendering equivalence.

For same-size metadata edits, APFS can retain shared image blocks while private staging changes metadata. When metadata grows and shifts the image stream, the compressed image may still be reusable without recompression, but APFS whole-file cloning cannot generally preserve sharing at arbitrary shifted byte offsets. SDE/0's same-offset WRITE profile must fall back; a future relocation-capable envelope can reduce network traffic without promising proportional local physical-write savings. Exact target reconstruction and all-complement proof remain mandatory.

Sources: [Adobe XMP storage specification](https://github.com/adobe/XMP-Toolkit-SDK/blob/main/docs/XMPSpecificationPart3.pdf), [CIPA Exif standards](https://www.cipa.jp/e/std/std-sec.html), [ICC specification, annex B.4](https://www.color.org/specification/ICC1v43_2010-12.pdf). This is a proposed profile, not shipped JPEG support.

## Objective and architectural decision

Extend Unison in two independent directions: a filesystem capability layer for efficient copies/updates of clonable files, and versioned, format-aware change classification and transfer planning. Improve APFS behavior for **ordinary files as well as DNG**, reusing upstream cloning code and preserving extension points for ZFS and ReFS. Implement DNG as the first semantic extension: distinguish embedded XMP edits from changes to the rest of the TIFF/DNG container; when proved safe, clone the destination locally and patch only the changed metadata ranges. Add a directly invokable **Adobe validation option for each received DNG**, including files transferred through ordinary fallback. Preserve exact-byte convergence, existing synchronization/conflict behavior, filesystem properties, and source/destination change detection. Port the application core to a pinned OxCaml compiler; route all helper invocations through a bounded OxCaml supervisor that can use all available CPU cores while accounting for SDK internal parallelism.

The user also requested research into existing systems, a diff standard if needed, and examination of Lightroom validation and the recreated Lightroom fingerprint work. Existing standards already solve binary deltas and other systems already support semantic merging. **Newer upstream Unison also already contains reflink/range-copy work absent from this local checkout. Reuse it before creating a competing filesystem layer.** Propose **Semantic Delta Envelope, SDE/0, an experimental interoperability profile**, rather than claiming to invent binary diff or semantic synchronization. Reuse Unison's existing rsync transfer when the extension cannot prove eligibility. VCDIFF is an existing option for future portable patch payloads.

The first DNG profile is deliberately narrow and useful: one embedded XMP packet at the same offset and length in source and destination, with every byte outside that packet proved identical. This avoids TIFF serialization and permits metadata writes on a cloned destination. Growing, relocated, ambiguous, unsupported, or structurally changed files use ordinary exact-byte transfer. Later milestones expand eligibility and add conservative semantic reconciliation. Completing only a parser, only a wrapper around dng-compare, or only a compiler switch does not complete the full goal.

The architecture also separates **logical components from physical placement**. A Lightroom asset can reference several independently identified preview renditions, with monitor-target payloads on Quasar and other levels/catalog-cache metadata on Ten. Volume paths, references and capacity policy are endpoint-local deployment decisions, while UUID, current develop digest, rendition dimensions/orientation and content identities describe the component. A group spanning volumes needs publication/recovery semantics of its own; a single-file SDE/0 plan or an atomic rename on one filesystem does not supply them. The other catalog Codex qualifies native preview rows, renderer provenance and link rewrite behavior. Monitor-fit bounds of 5120×2880 do not mean every JPEG is exactly that size or that it is Lightroom's original-resolution 1:1 image. Filename long-edge values alone cannot prove current-content identity.

**Three different identities must remain separate:**

1. `byte_identity`: identity of the entire data fork, plus Unison's separate resource-fork/properties machinery. SDE requires whole-file SHA-256 in addition to Unison's historical fullfingerprint; the general clone optimization with legacy peers retains stock fullfingerprint guarantees. Exact reconstruction remains the convergence contract.
2. `preserved_identity`: strong, offset-bound hashes covering *all* bytes outside explicitly editable regions. This authorizes preserving destination bytes while replacing metadata.
3. `semantic_identity`: profile-specific identities for raw samples, rendering instructions, descriptive metadata, and opaque/container content. These explain changes and can support explicitly enabled reconciliation; they never stand in for byte identity.

Changing XMP can change the rendered photograph. DNG is not simply immutable pixels plus harmless descriptive XML. A raw-image digest alone does not prove that camera profiles, opcodes, previews, embedded originals, maker data, TIFF structure, unknown tags, or unreferenced trailing bytes can be discarded.

## Inspected baselines and reproducibility

| Item | Observed baseline |
| --- | --- |
| Unison checkout | `/Users/alexy/src/unison`, upstream commit `375ea3ad2cace8584c508ef463332066d85e1d4e`; clean before this document |
| Newer upstream checked during final review | master `8772d26a2eb77cfd0cb6da81807e81f24f51044c`; release v2.53.8 (2025-11-05) explicitly added reflinking; this is separate from the local build baseline |
| dng-compare inspected runtime checkout | `/Users/alexy/dng-compare`, commit `67a7ee397caf80ee98de8da8a31c76e3263e895f`; clean; original source analysis refers to this checkout; preserved in place |
| dng-compare canonical public checkout | `/Users/alexy/src/dng-compare`, commit `cab85e42ab5f5f6b463a201273ce8ee2dc27c85d`; clean; newly cloned through SSH; use for future source improvements |
| Lightroom research checkout | `/Users/alexy/src/lightroom`, firstpair/lightroom commit `a0256087009d7c58f7df8643c977f4d0918215bf` |
| Host | Intel/x86_64 macOS 15.7.9, build 24G830; measured 18 physical / 36 logical CPUs |
| Existing OxCaml | `/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt.opt`, reports `5.2.0+ox`, Flambda 2, runtime5, multidomain, stack allocation; `tsan=false` |
| Toolchain separation | Default `ocamlc` reports 5.5.1; use explicit `opam exec --switch=5.2.0+ox -- ...`, never infer compiler from PATH |
| Build | Make is the upstream packaging path; `dune-project` declares Dune 2.3; Dune exists in the OxCaml switch even though absent from default PATH |

Read the applicable `AGENTS.md` files again at implementation start in case instructions have changed. None were found in the inspected checkout/ancestry during design. Recheck Git state before editing; preserve unrelated user work. Use disposable fixtures and isolated build outputs. Do not run mutation experiments on Bumer or personal photo libraries.

The new canonical dng-compare public checkout has its own `AGENTS.md`, read during finalization. It requires `uv` for Python, verification of its pinned Rust toolchain/edition, explicit stock-OCaml versus OxCaml claims, disposable synthetic tests, preservation of failed receipts/source-stability gates, and exclusion of private inventories/reports/binaries/credentials from Git. Its publication rules apply only when publication is actually requested. Re-read these instructions before changing that repository. The public and home-runtime Git histories are distinct/disjoint; do not blindly merge or rebase one onto the other. Keep home runtime files and private data intact.

Both the canonical dng-compare and normal Lightroom checkout now use their `git@github.com:firstpair/...` SSH origins. SSH authentication and read access were verified from a fresh interactive shell after the user's separate setup request; the home dng-compare checkout also received its SSH remote without source-file changes. No credentials or private-key material belong in this handoff or either repository. Future source improvements should target the canonical `~/src` checkouts.

## What the existing code establishes

### Unison integration seams

References below are to the pinned Unison baseline; line numbers will move during implementation.

| Concern | Concrete seam and consequence |
| --- | --- |
| Full file fingerprint | `src/fingerprint.ml:22,37`: `Fingerprint.t` is a string; `Digest.channel` hashes whole bytes. Do not replace it with a DNG raw digest. |
| Archive shape | `src/update.ml:46,61`: archive format 23 and `ArchiveFile (Props.t, Os.fullfingerprint, Fileinfo.stamp, Osx.ressStamp)`. `archive251`/converters are compatibility contracts. |
| Scan/change detection | `src/update.ml:1693` `checkContentsChange`; `src/fpcache.ml:283`; `src/os.ml:262` `safeFingerprint`. Existing fast checking is based on filesystem observations; a format plugin cannot silently strengthen their meaning. |
| Common update representation | `src/common.ml:104`: `ContentsSame` / `ContentsUpdated`. Keep these byte-level statuses unchanged in the first release; carry semantic annotations separately. |
| Conflict reconciliation | `src/recon.ml:711`: equal full fingerprints can converge; otherwise two changed files conflict or enter the configured merge path. Add semantic policy here only after classification and base handling are implemented. |
| Remote data transfer | `src/copy.ml:697` `transferFileContents`; `:802` `reallyTransferFile`; `:1057` `transferFileLocal`. Attempt semantic planning before allocating/opening the ordinary data-fork output. |
| Local-local transfer | `src/copy.ml:460` `localFile`, and `:1182` `file`: **local-local sync bypasses the remote transfer routine**. It needs the same semantic plan/materialization path. A patch only in `transferFileLocal` misses this use case. |
| Final verification | `src/copy.ml:245` `paranoidCheck`, `:40` source-change check, `:1182` common completion handling. Retain these and add SHA-256 validation for SDE plans. |
| Forks and properties | `src/copy.ml:776` resource fork/props finalization, `:366` `setFileinfo`; `src/osx.ml`, `src/props.ml`, `src/fileinfo.ml`. Cloning is not a replacement for applying source properties and clearing stale destination state. |
| Commit and archive | `src/files.ml:407` `renameLocal`: destination recheck, normal rename/stashing, archive update last. `:757` completes destination then source archive. Reuse this lifecycle. |
| Destination recheck | `src/update.ml:3146` `checkNoUpdates` forces a non-fast scan. Do not remove this read because APFS cloning succeeded. |
| Current race limitation | `src/files.ml:395` explicitly documents the check-to-rename race. Atomic pathname replacement is not compare-and-swap against an uncooperative editor. |
| Feature negotiation | `src/features.mli:33`, `src/negotiate.ml:70`, `src/remote.ml:345,786`: negotiate named capabilities; RPC v1 uses Umarshal, while v0 has legacy compiler-sensitive conversions. |
| Existing transfer optimization | `src/transfer.ml:317` rsync; `src/copy.ml:541` enabled by default. It reduces wire bytes but reconstructs a temporary output by writing its contents. |
| Existing extension-like facilities | `src/files.ml:975` and `doc/unison-manual.tex:1594` external merge with archived base; `src/copy.ml:878` external copy program. These are useful prior art, not a semantic identity/materialization contract. |
| Build wiring | `src/Makefile.OCaml:224` explicit OCaml module order, `:259` C objects; `src/dune` foreign stubs and local `lwt_lib`. Update both build descriptions. |
| Tests | `src/test.ml`, root `Makefile:26`: existing selftest is `./src/unison -ui text -selftest`. Add isolated fixture/unit targets as necessary without making tests traverse real roots. |

**Current-upstream correction:** the table describes the 2024 local baseline, not all Unison versions. Upstream v2.53.8 release notes explicitly introduce reflinking. A pinned source audit at master `8772d26a2eb77cfd0cb6da81807e81f24f51044c` found:

* `src/transfer.ml:471` already exposes `rsyncDecompress ?copyFn`; `src/copy.ml:784` supplies the range-copy callback, and `src/transfer.ml:363` uses power-of-two blocks.
* `src/fs.ml:71` exposes clone/copy adapters. `src/copy.ml:390` has partial-range fallback, `:418` tries descriptor cloning, and local copies at `:460` try path cloning.
* `src/copy_stubs.c:71` already calls Apple `clonefile`; `:136` supports Linux `FICLONE`; `:186` uses Linux range-copy/sendfile paths; `:219` supports FreeBSD range copy; `:354` implements Windows `FSCTL_DUPLICATE_EXTENTS_TO_FILE` with cluster/sparse/EOF handling. Apple range copying falls through to unsupported at `:452`.

Therefore **APFS whole-file clone and ReFS range cloning already exist upstream**. The specific additional APFS optimization is to seed output from a receiver-basis whole clone and retain same-offset unchanged regions during rsync, plus semantic DNG planning. Reuse/backport `Fs.clone_path`, `Fs.clone_file`, `Fs.copy_file`, their native stubs and the receiver callback. Do not claim general reflink-aware Unison or its Windows backend is new work. Existing boolean clone results suppress errors and broad range-copy fallback catches Unix errors; enriching result/error observability needs an explicit compatibility review. These are source findings, not runtime qualification of those backends. Pinned clone used for audit: `/private/tmp/unison-upstream-clone-audit`.

M0 must compare both versions and choose a reviewed implementation base. Prefer an isolated implementation branch based on the pinned newer upstream if compatibility and local project constraints permit; otherwise backport the smallest relevant upstream commits with attribution. Preserve the original checkout and user work, and re-pin all integration references after selecting the base. The verified build results below apply only to `375ea3ad`, not newer upstream. Re-run build/compatibility tests after adopting upstream code.

### dng-compare reuse and limits

Use its fixture knowledge, raw-block extraction ideas, report schemas, tool supervision, and strong byte-verification workflow. Preserve provenance and versioning. Inspect its licenses before copying code; otherwise reimplement from the documented behavior and public specifications.

The source findings below were established against home-runtime commit `67a7ee3`. A final comparison against canonical public commit `cab85e4` found the other referenced core sources byte-identical, with four reviewed differences: `portable_metadata.py` adds output-root separation checks, bounded batch size and phase locking; `preserve_apo.py` adds output containment, locking, positive rate validation and a legacy-ledger option; `rust-scanner/src/main.rs` retains the inspected TIFF/raw/XMP logic but returns failure when work is incomplete/unverified; and `Makefile` adopts `uv`, locked Cargo dependencies and standard OCaml by default. Historical `-oxcaml` output names do not prove that the public default build uses OxCaml. These safer workflow wrappers do not make selected metadata reports a complete preservation proof. Recheck line numbers against the selected public commit before editing.

The inspected Rust comparator traverses next-IFD/SubIFD links and selects raw/encoding/XMP fields. It does not establish preservation of the complete EXIF/GPS/private graph or all container bytes. Its equality result is useful evidence about selected content, not permission to overwrite everything else. Disposable synthetic tests during design changed an opaque trailer: the comparator still reported raw equality, auxiliary equality, zero exposed embedded/layout changes, and, in the stronger case, equal length, while full bytes differed. Keep the same-length `opaque-A` versus `opaque-B` case as a regression fixture.

`dng-metadata.rs` is an ExifTool reporting pipeline, not a TIFF/XMP serializer. Its report-oriented cache/resume and field handling are unsuitable as an authoritative synchronization cache without redesign: row-count-only batch reuse can go stale; duplicate field identities can be collapsed; process exit status and input stability require stronger validation. The Python path has stronger source/version stamps but still exposes selected metadata rather than all bytes.

The existing `metadata_extract_oxcaml.ml` is an OxCaml-built process supervisor using `Unix.create_process` and `Unix.select`; it is not evidence of a domain-safe shared-memory engine. `byte_verify_oxcaml.ml` wraps xdelta3 and checks reconstructed SHA-256. Reuse these lessons rather than introducing a second binary-delta algorithm.

Historical local reports contain substantial raw-equal/metadata-different populations. They motivate benchmarking but do not establish safe patch eligibility or a live speedup: selected-field equality and an absence of reported layout differences are incomplete preservation proofs.

### Lightroom validation and fingerprint research

The public firstpair/lightroom repository distinguishes native original-file matching, Adobe DNG raw digests, and full-file SHA-256 (`docs/firstpair-lightroom-repair.md:402–440`). It documents fingerprint recipes and oracle requirements; the recreated engines are not included in that public checkout. Additional local worker sources were located under `/Users/alexy/lrc-fingerprint-worker-20261005/crate/src/` and `/Users/alexy/lrc-fingerprint-proof-worker-20261005/crate/src/`.

Treat these as separate validation/identity layers. Lightroom's DNG validation and SDK validation can detect particular consistency or raw-content problems; a successful result does not prove that metadata, opaque bytes, previews, or the entire file match another replica. A stored `RawImageDigest`/`NewRawImageDigest` tag is an assertion inside an editable file until recomputed against the appropriate data. Adobe DNG 1.7.1 specifies different algorithms for these tags; do not interchange them or equate either with Lightroom's native original matcher.

Use the recreated workers as differential oracles only for the formats, metadata strata, and algorithms their tests actually cover. Preserve exact byte-order, sample-width, layout, opcode/profile, compression, and algorithm-version distinctions. The production SDE eligibility proof must remain independently correct even when a Lightroom-style digest is unavailable, unsupported, or wrong. Detailed verified Lightroom findings and validation references are recorded in the addendum below.

## Extension contract

### Core owns safety, extension owns interpretation

Start with a statically registered OCaml module interface and the built-in DNG implementation. This is an actual extension point: independent format modules can register a profile, probe, inspect, classify, and propose a plan without editing Unison's fingerprint/reconciliation machinery. Compile-time registration avoids distributing native compiler-specific plugins over a synchronization connection. A versioned local helper protocol may be added later; it must implement the same limited contract.

Conceptual interface; translate this into normal compiling types, not these exact names if dependency ordering requires a split:

```ocaml
module type FORMAT_EXTENSION = sig
  val profile : Profile.t  (* id, schema version, policy version, limits *)
  val probe : Readonly_file.t -> [ `Unsupported | `Candidate ]
  val inspect : Readonly_file.t -> (Manifest.t, Unsupported.t) result
  val classify : base:Manifest.t option -> Manifest.t -> Change.t
  val plan_exact : base:Manifest.t -> target:Manifest.t -> Plan_proposal.t option
  val reconcile : base:Metadata.t option -> left:Metadata.t -> right:Metadata.t
    -> Policy.t -> [ `Conflict of Reason.t | `Use_left | `Use_right
                  | `Merged of Metadata.t ]
end
```

`Readonly_file.t` is an opaque core-managed handle with checked bounded reads and a stability token, not a path the plugin can reinterpret. The core opens regular files, bounds arithmetic and allocations, hashes actual bytes, validates all extents, enforces resource limits, negotiates capabilities, owns output creation, performs writes, verifies results, applies properties, and commits. The plugin returns data, never a shell command, destination path, arbitrary write handle, or authority to mutate a live file.

A compiled plugin is trusted local code, not a security sandbox. Treat remote manifests/plans and file contents as untrusted input. If local out-of-process helpers are later supported, choose an explicit local executable by configuration, use bounded framed messages, pass read-only descriptors where supported, enforce timeouts, and validate their output identically. Never auto-install a plugin, fetch code by profile ID, or execute a command supplied by the peer.

Suggested classifications:

* `Exact_same` (full byte identity).
* `Xmp_packet_changed` with sublabels `descriptive`, `rendering`, `mixed`, or `unknown` when a supported secure parser can justify them.
* `Image_payload_changed` (sample/encoded payload distinction explicit).
* `Container_or_opaque_changed` (including layout, unknown content, embedded original, preview).
* `Unsupported` / `Invalid` / `Unstable`, with bounded diagnostics and deterministic fallback policy.

Labels are explanatory, not equivalence declarations. Unknown namespaces, camera-specific data, and rendering settings are significant by default. No mtime-based last-writer-wins rule, ignored metadata list, or XMP normalization is silently enabled.

### Candidate selection and limits

Select candidates by user-configured path rule and magic/DNG version inspection; an extension alone is insufficient. Proposed preferences: `semantic = dng` (off by default until qualified), `semanticpolicy = exact` (default), `clone = auto|off|require` (general filesystem policy, auto after qualification), `workers = auto|N`, `semanticreport = true|false`. Final naming should follow upstream conventions. `require` means fail that optimized attempt clearly when cloning is unavailable; it must not silently mutate the destination in place. The general `clone` policy applies even when semantic plugins are disabled. Production `workers=auto` targets the machine's available CPU budget; one-worker execution remains the reference/testing mode.

Implemented v0 limits are documented in `doc/dng-profile-v0.md` and `doc/semantic-delta-v0.md`: checked signed-64-bit file arithmetic; 256 visited plus queued IFDs; 16,384 total entries; 65,536 image extents per field; 131,072 protected extents; one DNG XMP packet up to 1 MiB. The generic envelope allows up to 64 regions, at most 1 MiB each and 16 MiB total payload. These supersede the larger initial design estimates. A valid larger file can fall back. Do not allocate from an unchecked TIFF count or XML entity expansion. No network/entity resolution; v0 can transfer opaque XMP bytes without interpreting XML.

## General filesystem capability layer: APFS now, ZFS/ReFS later

This is an independent Unison improvement, not a facility available only to semantic plugins. The DNG planner, existing rsync decompressor, local file-copy path, and moved-file reuse can all use the same staged-output backend. A filesystem can support cheap whole-file clone without arbitrary range clone; model these separately. Neither shared-block ancestry nor a filesystem's name establishes that two files contain equal bytes.

### Adapter contract

Extend the selected upstream filesystem-copy abstraction with `Fsclone`/`Clone_sink` responsibilities below the semantic layer; use existing upstream names when they already provide these contracts. Capabilities are checked against open files, directory handles, actual volumes and operation parameters, not a string test for `APFS`, `ZFS`, or `ReFS`. Describe:

* Native whole-file clone, composed whole-file clone, and range clone as separate optional capabilities.
* Destination creation/absence requirements, same-volume/cross-dataset restrictions, range alignment, maximum range length, EOF-extension prerequisites, overlap limits, sparse/integrity/encryption compatibility, and attribute side effects.
* Results `Shared`, `Copied`, `Unsupported`, or an actual retryable/fatal error, including any completed prefix. A successful copy API call alone must not increment a shared-block counter.
* Capability cache scope (mounted volume plus generation) and per-file checks. Runtime operation results are authoritative; unsupported/cross-device permits fallback, while ENOSPC/EIO/permissions/concurrent mutation are handled as errors.

Only the staging file is mutable. Core owns an explicit `basis_role = Source | Receiver_previous_version` and a stability proof. A held descriptor pins an inode but **does not freeze its bytes**. Prefer a private receiver-basis snapshot clone: compute rsync signatures from that stable basis, create the output clone from the same basis, and use the immutable basis for all later source-range reads. This costs another cheap clone but avoids generating signatures from one state and applying blocks from another. If private snapshots cannot be obtained, retain the existing guarded transfer semantics and full output verification; do not assume descriptor ownership implies immutability. Cloned read-only modes, ACLs or flags may obstruct staging writes: apply only the necessary temporary writable treatment to the private staging inode, then restore intended source properties. Never relax the live basis/destination's permissions or flags to make cloning work.

APFS backend: prefer `fclonefileat` from a held regular-file descriptor into an exclusive name in a pinned destination parent directory, subject to OS availability checks. `CLONE_NOFOLLOW` does not by itself reject symlinks; open/validate a regular source safely. Public APFS `clonefile` provides whole-file cloning, not a general changed-block map or arbitrary range-clone API. Use exact error reporting rather than a best-effort copy API that silently converts a clone to a full copy.

### Generic rsync materialization

In the local baseline, `src/transfer.ml:466–512` writes every literal and reads/writes every matched block. New upstream already provides a block-copy callback and fallback; extend/reuse it rather than duplicating it. The required sink contract has a logical output cursor and operations `literal`, `copy_from_basis`, and `finish`. Keep a sequential reference sink. Add any missing whole-file-clone/inherited-range behavior for verified receiver-basis clones:

1. For a matched block, the original basis offset is `block_number * block_size`. Skip data I/O only when that offset equals the current output cursor, the complete range is inside inherited valid length, and the output clone still contains the inherited bytes there. Advance the cursor and logical progress even though no data is written.
2. For a shifted match, copy from the **immutable basis descriptor**, or use a supported range-clone operation into the staging file. Never skip a shifted block and never read the evolving output as the basis. Insertions, deletions and duplicate block matches make this distinction essential.
3. Write literal bytes at the cursor normally. Coalesce adjacent compatible operations. Do not mix buffered `out_channel` output with uncoordinated descriptor `pwrite`/seek/range-clone operations.
4. At EOF, require exactly the declared target length and truncate/extend to that length safely. Hash the entire staged target and perform existing fingerprint verification. A shorter target must not retain the old suffix.

Local-baseline rsync block lengths are not filesystem-aligned; newer upstream's power-of-two sizing improves opportunities but does not prove alignment for every backend. A range-clone backend must split aligned interiors from copied head/tail regions when valid, or decline range cloning when source/destination alignment residues differ. Do not assume rsync block size equals APFS/ZFS/ReFS block size. Monotonic output construction is an invariant of the skip optimization; if a future sink allows out-of-order writes, it must track overwritten inherited intervals explicitly.

The initial same-offset skip optimization needs **no new peer wire protocol** because existing rsync tokens already identify basis block positions. It works with an unmodified source peer when all receiver-local basis checks hold, retaining stock Unison's fullfingerprint verification guarantees. A legacy peer does not supply whole-file SHA-256; do not pretend the receiver can independently check a source SHA-256 it never received. A negotiated general-transfer strong-hash feature can add that assurance later; if a configured policy requires it, use a qualified negotiated path or decline optimization. SDE always requires its separately negotiated SHA-256 identities. Its negotiation is needed for planning/classification, not because cloning itself needs semantic metadata.

### Local copies and recovery

For a local same-volume source-to-destination copy, cloning the **source** directly to staging can avoid the copy even for new files. Verify the staged source clone and source stability, then apply normal properties/commit. This is distinct from a receiver-basis clone used for rsync tokens. A source clone must never be interpreted as a receiver-basis clone. Consider moved-file reuse through this layer as well.

For local cross-volume updates, clone the receiver's old file on its own volume and use a local rsync/planned-delta producer or a bounded comparison producer feeding the same sink. The current local-local `copyContents` always copies, so generic network-sink changes alone are insufficient. Choose/reuse the delta producer after measuring its extra reads; do not implement a second unbounded diff engine.

Give cloned staging a distinct output-open mode: the existing `src/copy.ml:326` creation path uses `O_EXCL` and a fallback `O_TRUNC`; neither is the correct way to reopen a newly created clone. Likewise, `localFileContents` removes ordinary stale temporary files. Separate these paths explicitly. Initially exclude `DATA_APPEND`/partial-prefix resume from clone optimization and rebuild transaction-owned staging after interruption. Any later resume format must bind exact basis identity, target identity/length, backend mode and completed ranges. A stale clone is not a trustworthy transferred prefix.

Preserve Unison's property/fork, backup/stash, verification and archive behavior for every backend. Copy-on-write sharing is an allocation technique, not an independent backup against underlying device failure or a substitute for end-to-end integrity checks.

### Future adapters, research constraints

**OpenZFS:** block cloning depends on implementation/version, enabled pool features/tunables, compatible records/encryption, and the OS operation used. Query/attempt the real operation; `copy_file_range` can copy rather than share. Pin and qualify Linux/FreeBSD backends independently. Feature enablement is not authorization to assume every ZFS file supports reflink; dirty-data handling can also affect latency. Native macOS OpenZFS needs its own investigation.

**ReFS:** reuse and audit the already present upstream `FSCTL_DUPLICATE_EXTENTS_TO_FILE` implementation. Ranges require alignment, compatible integrity/sparse state, the same volume, pre-established destination EOF, and bounded lengths; same-file overlap is restricted. A composed whole-file clone needs chunking and an exact copied tail when required. Extent cloning does not automatically reproduce all streams, ACLs or attributes. Qualify the Windows filesystem backend independently of native Windows OxCaml availability.

Preserve existing upstream backend functionality during refactoring, and make unsupported extensions report that honestly. Do not claim additional ZFS/ReFS qualification merely because an interface or inherited implementation exists. Acceptance now includes a fake aligned range backend to test chunking, tails, incompatible residues, partial errors and fallback; new platform claims require actual platform tests.

## DNG profile and exact-byte algorithm

### Parser profile `org.firstpair.dng-xmp/0`

Support a documented subset of classic TIFF/DNG first, both byte orders, including inline and out-of-line typed values and explicit known IFD links. Prove the tag 700 packet range and the structural bounds needed to exclude overlap/aliasing. Recognize DNG by the appropriate version tags, not just `.dng`. Reject cycles, impossible counts, out-of-file extents, ambiguous duplicate XMP tags, XMP aliasing structural or known non-XMP extents, unsupported layouts, and integer overflow. BigTIFF and additional unusual DNG versions/layouts are fallback until separately qualified.

Preserve unknown tags and all gaps/trailers exactly. Unknown/private structures are never rewritten. If an opaque structure makes the proposed editable region's ownership ambiguous, decline the fast path. Ordinary exact-byte transfer remains possible; an invalid parser input must never authorize a semantic patch. Parsing validity is not a claim to implement all of Adobe's DNG validation.

For v0, require matching total length and an unambiguous same-offset, same-length XMP packet on both sides. Require every byte in `[0, file_length)` outside this packet to match. This includes TIFF headers/IFD entries, raw payload, previews, original raw, maker data, unknown tags, unused gaps, and trailing bytes. XMP count and offset changes therefore fall back in v0. The envelope carries the complete packet; the implemented materializer compares absolute 4 KiB windows, clips them to the packet boundary, skips identical windows and coalesces adjacent changed windows. It verifies the exact target afterward and reports actual logical bytes written and write attempts. This reduces application writes without promising a particular physical APFS allocation size.

Define the preservation proof without canonical TIFF serialization:

```text
packet = [xmp_offset, xmp_offset + xmp_length)
preserved_extents = complement(packet, [0, file_length))
preserved_identity = SHA256("SDE/0-preserved\0" || u64(file_length) ||
  u64(region_count) || ordered_regions(u64(offset), u64(length)) ||
  ordered_complement(u64(offset), u64(length), actual_extent_bytes))
```

The normative transcript is in `doc/semantic-delta-v0.md`; profile identity is bound separately in the plan. Use big-endian u64 fields and include empty complementary intervals. Hash every extent; do not compare a lossy metadata report. The source and destination independently compute this identity from their actual opened files. They also compute SHA-256 of their complete data forks. This is O(file size) read work. It can be fused with other hashing passes later; do not pretend a cached raw digest eliminates it.

### Transfer transaction

1. **Select:** both peers advertise the exact profile/schema; policy permits it; source and destination are regular files; destination exists. New files and unsupported peers use existing transfer.
2. **Stabilize inputs:** core opens source and receiver base, records device/inode/size/mtime/ctime and relevant fork/property state, and uses those same handles during inspection/hashing. Recheck after reads. An APFS clone can provide a stable receiver-base snapshot; it must be bound to the base identity actually negotiated. A source clone/snapshot is an optional supported optimization, not an assumption on remote/non-APFS filesystems.
3. **Describe base:** receiver sends a bounded manifest containing base size/SHA-256, XMP range and digest, preserved identity, profile version, and transaction nonce. No filenames from this message are used to create output paths.
4. **Plan at source:** source validates compatible layout and preserved identity, emits target size/SHA-256, exact replacement packet bytes and checksums, and binds them to the receiver's base identity/nonce. A missing proof is a normal fallback, not an ignored mismatch.
5. **Materialize privately:** core makes a fresh temporary destination in the final destination directory/volume. On APFS, clone the receiver's validated base using a supported clone API. Clone destination must not exist. Open the new inode read/write without truncation and patch only authorized ranges with short-write/EINTR-safe `pwrite` loops. Never open the live destination with write intent. No `O_TRUNC` after cloning.
6. **Verify staged data:** check full target data-fork SHA-256 and size against the source proposal, recompute the preserved proof/validate parser invariants, and verify base preconditions against the base actually cloned. Hash/checksum mismatches are errors; fallback must not conceal corruption.
7. **Finalize filesystem state and verify complete file:** apply the ordinary source permissions, ownership policy, ACLs, xattrs, Finder info, resource forks and timestamps according to Unison preferences. Explicitly account for inherited cloned attrs and an old resource fork that should be empty. Do not treat a cloned destination xattr as a source property. Then run existing `paranoidCheck` over the completed data/resource forks and the normal property checks; recheck source stability and its Unison scan fingerprint. No unverified fork mutation follows this step. A changed source aborts/retries the item.
8. **Validate and commit:** invoke the configured Adobe validator through the common receiving-candidate hook described below. After successful required validation, flush the staged file as required by the chosen durability policy, perform the existing destination `checkNoUpdates`, and enter the normal `Files.renameLocal`/stashing/archive lifecycle. Recheck pathname-to-inode identity immediately before replacement. Archive updates happen only after successful commit. Mark uncertain entries for rescan after interruption.
9. **Recover:** a temporary file is uncommitted until verified and renamed. An interrupted patch must not be treated as an ordinary valid resumable prefix. Delete/rebuild only transaction-owned staging files, or reuse one only after complete target verification. Keep partial SDE state in a separate transaction namespace so the existing prefix resumer cannot misinterpret it.

Errors such as unsupported clone/EXDEV can select ordinary transfer before any live mutation. ENOSPC, I/O errors, instability, or failed verification leave the live target and its archive unchanged and report a failed item; avoid an endless full-copy retry when disk space is exhausted. All file descriptors, registrations, and temporary files need cancellation/connection-close cleanup.

On filesystems without cloning, use normal Unison transfer by default. Copying the entire base and then applying a small patch can reduce wire traffic but does not reduce local writes, and may be worse than existing rsync. Such a backend requires separate measured justification.

### APFS guarantees and limits

APFS clone-on-write shares backing extents until a clone is modified. Same-volume clone eligibility must be tested at the destination, regardless of source volume or whether transfer is local or remote. Never assume a volume called Bumer is APFS. Cloning can fail, and writes to a successful clone can still fail for lack of space.

The application can promise that it issues writes only to chosen logical ranges on the clone. It cannot promise a particular physical block size, one disk write per XML edit, zero allocation, or a speed multiplier. APFS allocation, filesystem metadata, caches, compression, and storage firmware affect actual work. Reuse source/destination proofs and verification reads only when correctness is demonstrated, not simply to improve benchmark numbers.

A design-time disposable APFS probe confirmed: a clone has a different inode, a byte patch leaves its source unchanged, and atomic rename makes the new pathname visible while an existing open descriptor and hardlink still expose the old inode. This is expected snapshot/rename behavior. Implementation tests now qualify multiply linked destinations with Unison's existing replace-by-rename behavior: the selected pathname receives the verified new inode, and other aliases keep the old bytes. The fast path permits this case; it does not preserve hardlink relationships across the replacement.

Atomic rename protects readers from seeing a partially patched file. It does not make the preceding verification and replacement atomic with respect to a third-party writer. Keep the existing race checks, minimize the interval, and document that stronger guarantees need cooperative locking or a stable filesystem/application snapshot. Advisory locks alone do not solve uncooperative edits. Do not claim ACID or power-loss durability from rename alone; exercise fsync/parent-directory handling and macOS `F_FULLFSYNC` policy separately if that stronger durability is offered.

## Direct Adobe validation option

This is required product functionality, not merely an offline test oracle. Add a receiving-candidate validation hook owned by core and supplied by the DNG extension. It must run for every selected DNG about to be committed: metadata patch, APFS clone, stock rsync/full-copy fallback, new file, moved-file reuse, resumed completed staging, external-copy result, and generated merge result. Each receiving replica validates its own finalized candidate. Place the hook after data/resource forks and source-selected metadata are complete and before rename/archive, at a shared lifecycle point so optimized-path failure cannot bypass validation. `adobevalidate` is independent of whether semantic transfer is enabled or the DNG qualifies for an SDE profile; disabling optimization must not disable requested validation.

Proposed preferences: `adobevalidate = off|warn|require` (off until user selects it; recommend require for requested validation), `adobevalidator = /absolute/local/path`, plus pinned tool/build identity, adapter version, timeout, bounded diagnostic output, memory limit and scheduling configuration. Optional `adobevalidatescope = received|all-scanned` defaults to received; all-scanned explicitly checks otherwise unchanged DNGs too. Validate unchanged files through a private snapshot/staged copy or a qualified read-only-descriptor SDK driver. Never pass a live unchanged file to an arbitrary pathname-based helper relying on a post-hash to detect mutation; detection would not undo it. `warn` is a visible user-selected permissive policy, never an implicit fallback from require.

Support a qualified build of Adobe SDK `dng_validate` or a small SDK-backed validation driver. Official SDK information observed during design identifies DNG SDK 1.7.1 build 2724. Historical Adobe-authored `dng_validate.cpp` parses a DNG, reads stage-1 data, verifies its raw digest and constructs later image stages by default. **Qualify the exact current binary and its output/exit behavior before defining success.** Inspected Adobe-authored SDK source shows a raw digest mismatch can call `ReportError`, which prints diagnostics without throwing, and the CLI can still exit zero. Thus exit zero or “Validation complete” is not sufficient. Require a pinned build with validation/reporting enabled, validate negative controls, and either capture structured error counters in an SDK driver or use a strictly qualified diagnostic parser. Ambiguous/unknown/truncated diagnostics cannot become pass.

Use an explicit argv allowlist and one absolute staging-file argument, with no shell. Exclude output/conversion modes such as `-dng`, `-tif`, or stage-image output options. Open inputs read-only in a custom driver; record and check candidate size/identity and full SHA-256 before/after validation so a misconfigured helper cannot silently mutate an approved candidate. Bounded logs must never be mistaken for an unambiguous pass when truncated. Timeout, signal, crash, unknown result format, unavailable binary, unsupported requested algorithm, invalid structure or confirmed digest mismatch blocks commit under require. Missing an optional embedded digest is reported separately; it does not itself make a valid DNG corrupt. Define any stricter “digest must exist” policy separately.

Record candidate SHA-256, tool SHA-256/build, argv/adapter version, algorithm/tag, source snapshot identity, structured structural/decode/digest statuses, exit/signal and capped diagnostics. Validation receipts are invalid after candidate mutation. No reuse across tools/profiles/flags or merely matching raw digest. Byte-transfer verification remains mandatory even when Adobe validation succeeds. Do not claim Lightroom UI Validate parity; this option directly invokes an independently qualified Adobe SDK validator.

The implemented feature is `dng-validation-v1`; negotiate support and the requested policy before propagation and recheck at receiver companion selection. Version zero advertised suffix-only selection; it cannot promise content recognition and is not an alias. Both warn and require fail clearly on an old/unqualified peer before transfer. The receiver chooses its own explicitly configured local executable; a remote peer cannot supply a command path to execute. Require rejects a missing tool. Operational candidate-inspection failures and candidate changes reject even under warn. A non-APFS or non-SDE transfer can still satisfy validation. For merge results both receiving sides must honor their validation policy before committing their own candidates; existing non-atomic two-replica recovery semantics still apply.

All validator invocations use the OxCaml supervisor and shared CPU/memory/I/O budget described below. ExifTool and other helpers use the same scheduling path. A supported current Adobe SDK/tool license may constrain distribution; make this an optional locally configured dependency and review the exact SDK license before bundling code/binaries. SDK absence must not disable ordinary Unison or the exact DNG extension when validation is off.

## Semantic reconciliation beyond transfer optimization

The extension must eventually influence how changes are *described and reconciled*, not only how bytes travel. Do this without making the initial archive unsafe.

**First release:** an XMP-only edit is still a byte change, displayed as “DNG XMP changed” with its eligible patch size. One-side edits propagate exactly. Both-side edits retain existing conflicts unless the full bytes match. An image-changing edit can never disappear because selected metadata or a raw digest happens to match.

**Later opt-in `xmp-three-way` policy:** store a lossless base XMP packet and profile-specific parsed representation after successful common synchronization, bound to the archive generation, full file identity, preserved identity, policy version, and parser version. Treat this as an optional base cache: if absent, stale, untrusted, or incompatible, refuse auto-merge and show a conflict. Do not infer a base from whichever replica was scanned first. Two-way comparison is insufficient for deletion detection and genuine concurrent edits.

Use expanded RDF names, preserve qualifiers and unknown constructs, and define treatment of RDF Bag/Seq/Alt, language alternatives, absent versus empty values, numeric spellings and arrays before enabling each field. XML canonicalization alone is not XMP/RDF semantic equality. Unknown namespaces remain opaque conflict units. Conservatively group related rendering properties into one conflict unit. The initial auto-merge allowlist should be very small and justified by fixtures; it must never merge conflicting crop/orientation/develop parameters merely because XML property names differ.

Three-way rules: one side changed from base -> take it; both made the same supported semantic change -> converge; disjoint independently mergeable fields -> compose only under explicit policy; deletion versus update or competing rendering/unknown changes -> conflict. Filesystem property conflicts retain existing rules. An XMP-only edit on one side and a non-XMP/image change on the other is a conflict by default: transplanting develop settings onto different pixels can be wrong.

Generate **one deterministic exact target artifact**, validate it, then send those same bytes to both sides through normal guarded commits. Verify/stash both old versions as the existing merge lifecycle requires. The result cannot be “equivalent but indefinitely different” files with unchanged byte fingerprints. Partial two-replica merge failure follows Unison's recovery semantics and must be tested; there is no distributed atomic transaction.

True non-byte convergence (different full files declared synchronized) would require per-replica byte identities plus a common semantic base, new archive/reconciliation invariants, explicit capability/policy negotiation, and downgrade protection. It is not required for useful semantic extensions and is **out of scope for the first implementation**. Do not smuggle it into `Fingerprint.equal`, `ContentsSame`, or `RawImageDigest` handling. If later requested, design it as a separate archive-format feature with migration/rollback tests.

### Growing XMP and layout-changing files

Milestone 1 does not invent unused padding. Only bytes actually owned by a parsed, validated packet are writable. A later, separately assigned profile version can allow changed count/offset cells, a grown packet in proved reusable space, or append-and-repoint, provided every changed structural field is explicitly accounted for and all unchanged bytes retain exact source layout. The target is still the source's exact byte sequence; do not append an equivalent packet in a different place and pretend it is the source.

For arbitrary reserialization, raw payload may move and cheap clone patching may be impossible. Plan exact COPY/ADD ranges with an existing delta engine or use stock rsync. A semantic match can help locate reusable content, but every target byte still needs provenance and final verification. Bounds checks, alias analysis, opaque-byte preservation, and exact target tests gate each broader profile.

## SDE/0 experimental format and protocol draft

### Prior art and reason for an envelope

| Existing mechanism | What it supplies | Remaining need here |
| --- | --- | --- |
| Unison/rsync, including newer upstream reflink hooks | Proven byte-oriented matched-block transfer and existing range-copy optimization | DNG semantic profiles and any missing APFS whole-clone/preserve-range staging |
| RFC 3284 VCDIFF / xdelta | Standard binary delta representation | Versioned semantic profile, preservation obligations, policy and commit contract |
| Git attributes/diff/merge drivers | Path-selected interpretation and three-way merge | Synchronization/archive integration; textconv is display-only and one-way |
| SQLite Session | Row-aware changesets and conflict handling | Arbitrary externally edited TIFF containers and opaque-byte preservation |
| Automerge | Semantic document history/sync for its data model | Existing Lightroom/DNG files are not Automerge documents |
| RFC 6902 / RFC 5261 | JSON/XML structural patch operations | DNG byte layout, RDF semantics, exact reconstruction, stale-base and filesystem handling |
| Syncthing BEP | Block-based file synchronization | Format-specific semantics and local clone patch materialization |

The survey did not identify a drop-in public contract covering this complete combination. That is a scoped research finding, not proof of novelty or an assertion that no other system can do semantic sync. Name the specification experimental, publish conformance fixtures, and invite review before calling it a standard.

### Required envelope

Implement the normative schema in `doc/semantic-delta-v0.md`, with byte-level examples and rejection cases. The following is the design shape, not a finalized wire encoding:

```text
format: "SDE"
version: 0
profile: "org.firstpair.dng-xmp/0"
policy: "exact"
hash: "sha256"
nonce: bounded per-transaction identifier
base:   { length: u64, whole_digest: bytes32 }
target: { length: u64, whole_digest: bytes32 }
preserved: { ordered_extents, offset_bound_digest: bytes32 }
classification: "xmp-packet-changed"  # informative; no authority by itself
operations:
  WRITE { offset: u64, length: u64, old_digest: bytes32,
          new_digest: bytes32, payload: bytes[length] }
```

V0 is same-length, non-overlapping WRITE operations over a clone of the named base; the ordered complement is implicitly retained at the same offsets. No inserts, truncates, file paths, symlinks, executable commands, external URLs, or recursive patch chains. All file bytes are covered exactly once by WRITE ranges or preserved ranges. Receiver validates that every WRITE lies within the profile-authorized XMP region. Sort order is normative; reject duplicate/overlapping operations, impossible lengths and unknown mandatory fields/profile versions. Specify zero-length cases, hash domain encoding and maximum message/packet/operation sizes. Chunk large payload transport into bounded frames; do not allocate from peer-supplied totals.

The implemented format has one canonical fixed binary encoding with checked big-endian integers, specified in `doc/semantic-delta-v0.md`; v0 has no optional fields or TLV extensions. Unison carries this same SDE/0 string and SDR/0 request in a distinct bounded RPC. Per-command body limits are enforced before allocation, and inner strings have independent limits. The current envelope is retained in bounded memory rather than streamed incrementally. Do not introduce a second representation or canonical JSON hash without a separately specified version and conformance tests.

Hashes protect integrity and bind a plan to its base; they do not authenticate an untrusted peer. Rely on Unison's configured trusted connection/security model, and validate all lengths/ranges even from authenticated peers. Keep the existing legacy fullfingerprint for archive compatibility; SDE adds SHA-256 rather than silently changing MD5-based historical archive identities.

Register features such as `semantic-delta-v0` and `dng-xmp-v0` with `arcFormatChange=false`. Exchange profile/policy versions explicitly. Only invoke new RPC commands when both endpoints advertise support and the negotiated RPC encoding is qualified; RPC v0 peers fall back. Avoid changing existing command payloads and `convV0` types. New RPCs should have distinct names and bounded decoders. APFS availability is a destination-local capability, not a requirement that both peers run macOS.

No first-release archive format bump is necessary: exact target bytes preserve existing archive invariants. Optional classification caches are disposable and keyed by full identity plus parser/schema version, never just path, mtime, row count, or raw digest. Any future authoritative semantic archive change must declare `arcFormatChange=true`, audit archive naming/loading/hash logic, preserve or intentionally migrate historical formats, and prohibit silent downgrade.

## OxCaml port and bounded parallelism

### Port the core first, optimize demonstrated hot paths second

The current code is OCaml; a useful OxCaml rewrite means compiling and qualifying the complete CLI/core with OxCaml, then refactoring performance-critical code to use its capabilities. It does not require mechanically rewriting every unchanged module. Retain the original synchronization algorithm and protocol invariants. Maintain a sequential reference backend for parity tests and an ordinary OCaml build where feasible. **Historical baseline:** the unmodified checkout failed under the installed OxCaml at the `Safelist.mem` modality mismatch. Compatibility fixes and the complete current CLI now build and pass selftests with both compilers; see the live evidence and `doc/oxcaml.md`. This supersedes the design-time blocker, without claiming compiler-proved domain safety or a compiler-only speedup.

Start with the already installed `5.2.0+ox` switch. Record compiler configuration and package lock/snapshot in the benchmark artifact. Upstream OxCaml currently reports an OCaml 5.4 base, while installation documentation still describes `5.2.0+ox`. Current upstream support emphasizes x86-64/arm64 Linux and arm64 macOS; x86 macOS “may still work.” The local Intel toolchain works as an installed compiler, but a fresh upstream upgrade needs separate qualification. No native Windows OxCaml guarantee is made.

Build all OCaml artifacts, C stubs, and linked dependencies with the selected compiler in separate output directories. Do not reuse `.cmi`, `.cmx`, or prebuilt runtime-dependent objects from another switch. Qualify CLI/core first; GTK/native macOS GUI, filesystem monitors, and Windows compatibility builds need their own matrix. Do not replace vendored Lwt merely because `oxcaml-lwt` is installed.

### Ownership model

Keep Unison's existing Lwt event loop as the sole owner of mutable synchronization state: promises/waiters, RPC registries/message IDs/receivers, archive tables, feature/preferences state, progress callbacks, cancellation registration, and final commits. The vendored Lwt is not proven domain-safe (`src/lwt/lwt.ml:11–31`, `src/lwt/generic/lwt_unix_impl.ml:25,61`). Remote registries (`src/remote.ml:721,916,1025`) and archive caches (`src/update.ml:675,729,742`) also require single-owner access.

Workers receive immutable job descriptions and independently owned read-only descriptors/buffers. Initial parallel jobs: DNG inspection, range hashing, whole-file strong hashing, and pure plan construction. Use `pread` or independent descriptors, not shared seek positions. Return immutable results through an audited bounded completion queue plus a wakeup descriptor; the event-loop owner drains it and calls `Lwt.wakeup`. A worker must never directly mutate an archive or call into legacy Lwt/RPC/UI code.

The user explicitly requests efficient helper invocation and use of all cores. **Production defaults to `semanticworkers = 0` (automatic), using the physical-core count on macOS and the available logical count as a portable fallback**; an explicit positive value overrides the budget. This host reports 18 physical and 36 logical CPUs via `sysctl -n hw.physicalcpu hw.logicalcpu`; do not hardcode either count. The 18-versus-36 cached-hash comparison found about 10% more throughput at 36, supporting 18 as a balanced default with 36 available for throughput experiments. Adobe decoding needs its own benchmark. One-worker mode is the sequential reference/test control. Expose detected and effective capacity. Route every Adobe, ExifTool or other helper invocation through a bounded OxCaml supervisor. Spawn/reap/cancel processes asynchronously, drain stdout/stderr concurrently into bounded buffers, and return immutable completion records to the owner loop. Do not allocate a blocked OCaml domain just to wait for each child. Domain CPU tasks and external-process CPU reservations draw from one global budget. Transaction payload/descriptor credits are implemented estimates; per-volume I/O, actual RSS and external child memory caps remain separate work.

Account for nested parallelism: a single-threaded helper reserves one CPU permit; an explicitly configured K-thread SDK worker reserves K; a whole-machine native worker can reserve the whole budget. Do not launch one internally all-core validator per core. Prefer a qualified SDK driver with an explicit thread cap or documented control; if the stock executable's inner parallelism is unknown, characterize it or run one budget-reserving process until it is known. Measurements determine whether multiple single-thread SDK jobs or fewer multi-thread jobs achieve better throughput. Expose effective process/domain/native-thread counts and scheduling stalls. Using all cores means making CPU capacity available under this accounting, not forcing every core busy while storage or dependency constraints make that wasteful.

The Adobe-authored SDK implementation inspected during design has `dng_host::PerformAreaTaskThreads` returning 1 and `dng_area_task::Perform` using one thread; the host documentation identifies overriding area-task dispatch as the multiprocessing extension point. A task's `MaxThreads` capacity does not mean the stock CLI creates those threads, and no `--threads` CLI switch was established. Do not invent that option or assume the existence of `NewRawImageDigest` implies actual parallel execution. Multiple qualified single-thread jobs use many cores across files. To use many cores for one large DNG where SDK stages support it, implement and test the explicit-thread-count SDK host wrapper, including task lifecycle, cancellation and transitive codec behavior; reserve that count from the same OxCaml budget. Record SDK version/build flags and actual observed threads. The AOSP copies inspected establish source mechanics only; some Android builds disable XMP/JXL and are not proposed as the user's full Adobe validator.

Benchmark 1/2/4/8 and auto, including mixed hashing/ExifTool/Adobe workloads. Bound jobs, open descriptors, memory, in-flight manifest bytes, and I/O per volume separately. An HDD may become slower with parallel reads even when CPU utilization rises. Cancellation uses explicit tokens and process-group cleanup; discard late results by transaction generation, close owned descriptors, and never allow an obsolete result to authorize a commit.

Use OxCaml portable/contended annotations and the pinned parallel library APIs after proving sequential parity. Unboxed offset/length records, local allocation for short-lived parse structures, and vectorized/checksum loops are candidate optimizations, not assumptions. Read/parse/hash fusion can save passes but must produce byte-for-byte identical digests and maintain stable-handle checks. Do not parallelize ordinary incremental SHA-256 by concatenating chunk hashes; whole SHA-256 and a separately specified tree hash are different algorithms.

Audit every C function executed by workers for GC roots, globals, ownership, bounds, exception paths, runtime release/reacquisition, and platform ABI behavior. Copy/root buffers before releasing the runtime as required; never access OCaml heap values while the runtime is released. Existing OCaml 5 compatibility macros do not establish domain safety. The installed compiler reports TSAN disabled; do not claim a race-sanitizer result without a separately supported instrumented build.

## Implementation map and milestones

Suggested responsibility split; first reuse newer upstream's existing range-copy modules/hooks, then adjust names/order to avoid duplicate APIs and dependency cycles. Keep policy/IO/format concerns separate.

| New or changed file | Responsibility |
| --- | --- |
| `src/fsclone.{ml,mli}`, `src/fsclone_stubs.c` | Filesystem capability adapter, APFS whole-file clone now; precise future range-clone contract |
| `src/clone_sink.{ml,mli}`, `src/transfer.ml` | Generic reference/clone output sinks, cursor tracking, same-offset skip, shifted-range copy, exact EOF |
| `src/semantic_types.{ml,mli}` | Immutable profile, extent, identity, classification, proposal and limits types; no RPC/archive dependencies |
| `src/semantic_registry.{ml,mli}` | Registration, path selection, profile/version compatibility |
| `src/dng.{ml,mli}` | Bounded TIFF/DNG parser and XMP-region discovery |
| `src/dng_semantics.{ml,mli}` | DNG profile; complete preservation partition; later XMP semantic rules |
| `src/semantic_hash.{ml,mli}` | SHA-256/extent proof API using a maintained audited implementation; checked streaming reads |
| `src/semantic_delta.{ml,mli}` | SDE validation, exact plan generation, encodings/conformance |
| `src/semantic_io.{ml,mli}` | Stable handles, temporary staging, patching, cleanup, verification |
| `src/semantic_io` using `Fsclone` | Reuse general clone/positional-I/O layer; do not duplicate an APFS implementation inside DNG |
| `src/semantic_remote.{ml,mli}` | New negotiated RPCs, bounded manifests/payload streams |
| `src/semantic_workers.{ml,mli}` | Sequential and OxCaml worker backends; owner-thread completions |
| `src/file_validator.{ml,mli}`, `src/adobe_validate.{ml,mli}` | Shared post-materialization/precommit hook; qualified Adobe SDK/CLI adapter and receipts |
| `src/helper_supervisor.{ml,mli}` | Bounded helper launch/output/cancel lifecycle and global CPU permits including SDK inner threads |
| `src/copy.ml` | Shared local/remote optimization hook, standard fallback and finalization |
| `src/files.ml` | Keep guarded commit; narrowly add transaction revalidation hooks if required |
| `src/update.ml`, `src/recon.ml`, UI modules | Optional classification annotations; later explicit semantic reconcile integration |
| `src/Makefile.OCaml`, `src/dune`, build docs | Both build systems, pinned OxCaml/sequential targets, platform guards |
| `doc/semantic-delta-v0.md` | Normative experimental protocol, profiles, security and conformance |
| `tests/semantic/`, `bench/semantic/` | Synthetic/public fixtures, adversarial/failure tests, reproducible measurements |

**M0 — Upstream reuse, baseline and qualification.** Inspect pinned current-upstream reflink/range-copy work, decide and document rebase versus minimal backport in an isolated implementation branch, and re-pin integration references. Build/run tests for the selected base with stock OCaml and pinned OxCaml. Record compiler/platform/build settings, binary versions, expected pre-existing failures, and baseline sync behavior. Import or generate legally distributable tiny fixtures; do not commit personal photographs or private report paths/content. Acceptance: no duplicated upstream clone engine; reproducible commands and clean separation of build outputs; cross-binary baseline archive/wire smoke test.

**M1 — Pure semantic kernel and draft spec.** Implement bounded parser, complete preservation partition, SHA-256 identities, registry interface, sequential planner and standalone SDE decoder/validator. No live-file writes. Add a developer inspection/dry-run command that reports classification, eligibility/reason, planned logical bytes and verification cost. Acceptance: adversarial fixtures rejected safely; opaque-trailer counterexample detected; deterministic manifests; exact SDE vectors round-trip in the canonical encoding, standalone and inside bounded RPC framing; a second trivial test extension exercises registration without special-casing DNG in core.

**M2 — Local APFS exact patch path.** Clone receiver to staging, apply fixed-range XMP patch, verify, and reuse normal property/commit lifecycle. Cover the local-local bypass explicitly. Acceptance: whole output matches source byte-for-byte; original target unchanged on injected failure; logical bytes written are limited to planned ranges; clone unavailable/disabled behavior correct; all existing selftests pass. Instrument syscall-level logical writes; do not infer physical amplification from file size.

**M2-G — General APFS-aware Unison (required user scope; implement before M2).** Reuse/extend the filesystem adapter and generic clone sink, source-to-staging local clone, receiver-basis rsync same-offset skip, shifted-match copying, and a local cross-volume producer using the same sink. DNG must consume this filesystem layer. Acceptance: ordinary binary/text files benefit without a DNG plugin; inserted/deleted prefixes and duplicate blocks remain exact; target shrink/growth is correct; baseline peers still work; clone-off matches stock output; resource-fork/properties and cancellation remain correct. Add the fake constrained range adapter to test the richer ZFS/ReFS capability contract; preserve existing upstream backends without claiming new runtime qualification for them.

**M3 — Remote negotiation and fallback.** Add negotiated profile/RPC transport; reuse exactly the local materializer. Acceptance: modified/modified, modified/upstream, upstream/modified, local-local and SSH-local combinations; unsupported/old peers use baseline behavior; malformed envelopes cannot escape roots or allocate unbounded memory; disconnect/restart/cancel leaves valid archives and recoverable staging. Remote source and APFS receiver should benefit even when source filesystem cannot clone.

**M4-V — Direct Adobe validation and helper scheduling (required).** Qualify a pinned Adobe SDK validator/driver, add the receiving-candidate hook and `off|warn|require` policy, negotiate required receiver enforcement, and route all helpers through the shared bounded OxCaml supervisor with explicit native-thread budgeting. Acceptance: every receiving path including new/full-fallback/resumed/reused/merged DNG invokes the option; require rejects a corrupt-digest fixture even if the tool exits zero; absent optional digest differs from invalid/mismatch; crashes/timeouts/mutations/truncated diagnostics fail safely; cancellation reaps children; mixed CPU/helper jobs can use the available core budget without unbounded nested threads. Qualify multi-file single-thread throughput and the explicitly capped SDK area-task wrapper for one-large-file scaling where supported. Validation off leaves baseline behavior usable without Adobe installed. This milestone can proceed alongside M2/M3 and must not be reduced to fixture-only validation.

**M4 — Change reporting and broader DNG coverage.** Expose trustworthy semantic labels and fallback reasons, maintain independent Lightroom/Adobe oracle fixtures, and add layout-changing profile versions only with exact-byte proofs. Acceptance: XMP growth/relocation either produces exact source bytes or uses ordinary transfer; image/rendering/opaque changes are never mislabeled safe; supported corpus strata pass byte checks and configured validation.

**M5 — Conservative opt-in semantic reconciliation.** Add optional base metadata capture and a narrowly specified three-way XMP policy. Reuse existing merge staging/commit behavior, preserving originals and producing one exact result. Acceptance: same/disjoint/conflicting/deletion/rendering/unknown namespace cases, stale/missing base, partial two-replica failure, policy mismatch, deterministic serialization, and rollback/downgrade behavior. Default remains exact, conflict-preserving sync.

**M6 — OxCaml data-path rewrite and qualification.** Run full CLI/core on pinned OxCaml, introduce bounded workers and selected measured representation improvements, audit C stubs, and document platform/GUI status. Acceptance: sequential/parallel results identical, mixed compiler archive/wire tests pass, cancellation and randomized scheduling stress pass, descriptor/RSS limits hold, complete benchmark report distinguishes read/write/network/CPU effects. A compiler-only rebuild is an intermediate milestone, not proof of performance improvement or parallel safety.

Deliver generic APFS-aware transfer and a usable exact DNG extension after M2-G/M3 even while M4–M6 continue. Keep each milestone reviewable and runnable. Do not mix an unbounded whole-codebase rewrite with the first correctness-critical transfer change.

## Required acceptance matrix

1. **Exactness:** same-offset/same-count packet edits, packet unchanged, multiple edits, first/last packet byte, zero/edge sizes; final file SHA-256 and byte comparison equal source. Preserve all complement bytes and the source-selected fork/property state.
2. **Coverage:** both TIFF byte orders; inline/out-of-line values; multiple IFDs/SubIFDs; EXIF/GPS/private tags; tiles/strips; previews; embedded originals; opcode/profile/rendering changes; unknown tags and opaque trailers. Unsupported cases must fall back deterministically.
3. **Malformed input:** cycles, aliasing, duplicate packet ambiguity, huge counts, overflow, truncation, invalid offsets/types, XML bombs if parsing XML; bounded time/memory and no writes to live target. Fuzz parser and SDE decoder with sanitizer-qualified C helpers where available.
4. **Integrity:** stale stored DNG raw digest, same raw digest/different metadata, same decoded pixels/different encoding, altered opaque bytes, wrong target/base hashes, corrupt payload, overlap/range escape. Never commit on digest failure.
5. **Concurrent modification:** source changes during inspection/transfer; receiver changes before clone/during verification/before rename; pathname replaced with symlink; inode replacement; mtime restored with changed bytes; cache made stale; canceled worker returns late. Explain the remaining uncooperative-writer check/rename race rather than writing a test that claims to eliminate it.
6. **Failure/recovery:** inject errors after clone, mid-pwrite, before/after verification, property setting, flush, rename, and archive update; ENOSPC; permission denied; connection drop; abort; process kill. Each live path is old or a verified new file, never a partial packet; archives are either committed or trigger correct recovery/rescan. Existing rename/stash failure semantics remain accounted for.
7. **Filesystem behavior:** APFS same/different volumes, no clone support, read-only files, sparse/compressed files if supported, destination hardlinks, open readers, symlinks, case/Unicode path handling, nonempty-to-empty resource forks, xattrs/ACL removal, permissions/timestamps, stashing/backups. No silent inherited-clone property leakage.
8. **Compatibility:** archive round-trip before/after extension use; extension disabled; old peer/new peer both directions; RPC v0 fallback; compiler switch; platform guard builds; existing profiles, ignore rules, merges and cancellation. First-release archives must remain readable by baseline Unison.
9. **Parallelism:** sequential vs 1/2/4/8 worker parity, randomized task completion/cancellation, one busy volume, independent volumes, bounded memory/descriptors/queues, no legacy global-state access from workers. Run relevant race instrumentation only where actually supported.
10. **Semantic merge:** same edit on both sides, disjoint allowlisted descriptive fields, same field divergent edits, delete/update, Bag/Seq/Alt/qualifiers, rendering cross-field conflicts, unknown namespaces, image change plus XMP change, missing/stale base, and deterministic one-artifact convergence.
11. **Generic cloned transfer:** non-DNG same-size local edit; inserted/deleted prefix; duplicate blocks matched at a different offset; all-literal and all-matched streams; shorter/longer target; STRING→skip→range-copy→STRING transitions; same-volume source clone versus receiver-basis clone; immutable-basis lifetime; partial-resume exclusion; capability cache invalidation; range-alignment/tail and partial-operation errors. Second synchronization must be a true no-op.
12. **Adobe invocation and CPU accounting:** off/warn/require on every receiving path; old receiver; binary absent/changed; valid/missing/mismatched digest; unsupported/raw decode failure; warning versus error text; truncated output; timeout/crash/signal; mutated candidate; all-scanned no-op scope; child cancellation/zombies; multiple internally parallel SDK processes; mixed ExifTool/hash/Adobe workload; worker auto fills available CPU budget without oversubscription and respects memory/volume limits. Independent source review, synthetic tests, real-corpus validation and native-oracle qualification remain separately reported.

## Benchmark plan and honest performance claims

Use generated fixtures and a consented/copy-only representative corpus. Record baseline hashes before each run and verify output after every run. Publish toolchain commit, hardware, OS/filesystem/volume topology, file-size/packet-size distribution, compressibility, cache state, source/destination location, limits and exact commands. Store machine-readable measurements plus a short interpretation, including unsuccessful optimizations.

Compare: the pinned local original; selected newer upstream with its existing reflink/range-copy behavior; minimally compatibility-fixed selected upstream compiled with pinned OxCaml (record actual fixes); generic APFS improvements with semantic plugins disabled; new sequential DNG extension with cloning off/on; new OxCaml extension with 1/2/4/8 workers. This separates already available upstream improvements, compiler gains, algorithm changes, general clone materialization, DNG semantics and concurrency. Include same-volume and cross-volume local sync, remote sync over a documented link, non-APFS receiver fallback, cold/warm caches, and HDD/SSD where available. Do not silently compare a cold baseline with a warm optimized run.

Workloads: no changes; fixed-size XMP edit in 32/128/512 MiB and multi-GiB files; larger/growing XMP; metadata plus preview/raw/opaque change; full content change; thousands of small files; malformed/unsupported files; new files; concurrent editor; mostly eligible mixed corpus. Use at least five measured repetitions after declared warmups, report median and tail distribution, and retain raw samples. For small sample counts report quantiles cautiously.

Measure wall time, CPU time, peak RSS, peak descriptors/queue depth, bytes read at application level, logical write bytes, transmitted bytes, clone success/fallback counts/reasons, hash/parse/verify/commit stage timings, and filesystem/storage write telemetry where obtainable. APFS physical allocation/shared-extent accounting is not equivalent to logical file size or proof of physical write count. State measurement limitations.

Expected hypothesis, not a promise: eligible APFS updates substantially reduce destination logical writes and transfer bytes; full validation still reads large files, so wall time may remain bounded by hashing/storage bandwidth. The initial implementation can be worthwhile even without a large elapsed-time speedup. A faster profile that skips verification needs a separately stated trust model and is not enabled by default. Do not set a speedup target that encourages weakening preservation checks.

## Defaults, open questions, and handoff checklist

Proceed with these defaults unless actual fixtures invalidate them: exact convergence; general clone adapter independent of semantics; fixed-range XMP profile first; SHA-256 plus existing archive fingerprints; statically registered extensions; no raw decoding needed for transfer eligibility; APFS clone auto with ordinary fallback; no auto-merge until an explicit policy is selected; production auto CPU budgeting with a sequential reference; no production-photo mutation; existing archive format retained. Adobe validation is a directly invokable optional precommit step and may decode raw data when selected. Reuse upstream ZFS-related OS primitives/ReFS backend and add constrained mock tests; claim new platform qualification only after testing it.

Open questions are implementation investigations, not reasons to block basic work: measured fraction of fixed-layout XMP changes; appropriate SHA-256 library and license/build burden; exact macOS clone API/FD binding supported by target deployment; intended durability tier; useful XMP merge allowlist; broader TIFF/BigTIFF coverage; pinned OxCaml package availability on other machines; native GUI dependencies. Resolve them with fixtures, small experiments and documented choices. Only ask the user when the answer changes desired behavior or authorizes real-data deployment.

At Sol session start:

* Read this file, recheck instructions/Git status, and preserve the pinned design baseline.
* Continue the implementation stage under the user's original goal authorization. The design/handoff subgoal is complete; inspect session goal state before creating or updating tracking so a completed design goal is not confused with finished implementation.
* Continue from the live implementation handoff above; do not restart completed M0–M3 work. Read current code and test evidence before choosing the next milestone.
* Keep a concise milestone log with evidence, discovered constraints and remaining work.
* Run existing selftests and the relevant new tests after each material change; avoid gratuitous repeated full runs.
* Finish with code, draft spec, fixtures, reproducible benchmarks and clear compatibility/platform limits. Do not claim APFS physical block savings or semantic correctness from raw-image digest equality.

## Primary sources

Sources checked during design; local source findings are pinned above. Verify moving toolchain documentation again before upgrading dependencies.

* [Adobe DNG 1.7.1 specification](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf): TIFF/DNG tags and raw digest definitions, including RawImageDigest/NewRawImageDigest.
* [Adobe XMP specifications](https://developer.adobe.com/xmp/docs/xmp-specifications/): data model, XML serialization, storage and reconciliation specifications.
* [Adobe DNG SDK](https://www.adobe.com/support/downloads/dng/dng_sdk.html): optional validator/SDK distribution and version information; qualify a pinned actual tool build and its license.
* Adobe-authored SDK source mirrors: [validator](https://android.googlesource.com/platform/external/dng_sdk/+/6b5cf2a88ebd2b099e56d0d4717e962772ff9067/source/dng_validate.cpp), [host](https://android.googlesource.com/platform/external/dng_sdk/+/68764928faa1d15f76bbf8f03c6e630c570a4354/source/dng_host.cpp), [area-task dispatch](https://android.googlesource.com/platform/external/dng_sdk/+/refs/heads/android14-prebuilt-test/source/dng_area_task.cpp), [error reporting](https://android.googlesource.com/platform/external/dng_sdk/+/refs/heads/android14-prebuilt-test/source/dng_exceptions.cpp), and [raw digest validation](https://android.googlesource.com/platform/external/dng_sdk/+/refs/heads/android12-qpr1-release/source/dng_negative.cpp). These establish specific source behavior; qualify the actual installed current SDK build separately.
* [Apple About APFS](https://developer.apple.com/documentation/foundation/about-apple-file-system), [clonefile manpage](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/man/man2/clonefile.2), [copyfile manpage](https://github.com/apple-oss-distributions/copyfile/blob/main/copyfile.3), [rename](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/man/man2/rename.2), and [fsync](https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/man/man2/fsync.2): clone, metadata, replacement and durability behavior. Local SDK `sys/clonefile.h:33–51` was also inspected.
* [OpenZFS block cloning](https://openzfs.github.io/openzfs-docs/Basic%20Concepts/Data%20Storage/Block%20Cloning.html), [OpenZFS 2.3 tunables](https://openzfs.github.io/openzfs-docs/man/v2.3/4/zfs.4.html#zfs_bclone_enabled), and [pool features](https://openzfs.github.io/openzfs-docs/man/v2.3/7/zpool-features.7.html): version/operation-specific restrictions and enablement.
* [Microsoft ReFS block cloning](https://learn.microsoft.com/en-us/windows/win32/fileio/block-cloning) and [FSCTL_DUPLICATE_EXTENTS_TO_FILE](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ni-winioctl-fsctl_duplicate_extents_to_file): range API and platform restrictions.
* [ExifTool options](https://exiftool.org/exiftool_pod2.html): temporary rewrite/overwrite behavior; “in place” does not establish sparse range writes.
* [rsync technical report](https://rsync.samba.org/tech_report/): matched byte-block reconstruction.
* [Unison v2.53.8 release](https://github.com/bcpierce00/unison/releases/tag/v2.53.8), [pinned newer transfer.ml](https://github.com/bcpierce00/unison/blob/8772d26a2eb77cfd0cb6da81807e81f24f51044c/src/transfer.ml), and [pinned newer copy.ml](https://github.com/bcpierce00/unison/blob/8772d26a2eb77cfd0cb6da81807e81f24f51044c/src/copy.ml): existing reflink/range-copy work that must be assessed before implementation.
* [Pinned upstream native copy backends](https://github.com/bcpierce00/unison/blob/8772d26a2eb77cfd0cb6da81807e81f24f51044c/src/copy_stubs.c) and [Fs adapters](https://github.com/bcpierce00/unison/blob/8772d26a2eb77cfd0cb6da81807e81f24f51044c/src/fs.ml): existing APFS/Linux/FreeBSD/ReFS implementations, distinct from the local 2024 baseline.
* [RFC 3284 VCDIFF](https://www.rfc-editor.org/info/rfc3284/) and [xdelta](https://github.com/jmacd/xdelta): existing generic binary delta format/implementation.
* [Git attributes](https://git-scm.com/docs/gitattributes/): custom diff/merge drivers and one-way textconv limits.
* [SQLite Session introduction](https://www.sqlite.org/sessionintro.html): structured changesets and conflicts.
* [Automerge concepts](https://automerge.org/docs/reference/concepts/): semantic document/history synchronization.
* [Syncthing BEP](https://docs.syncthing.net/specs/bep-v1.html): block-based synchronization protocol.
* [RFC 6902 JSON Patch](https://www.rfc-editor.org/info/rfc6902/) and [RFC 5261 XML Patch](https://www.rfc-editor.org/info/rfc5261/): structured patch prior art.
* [OxCaml](https://oxcaml.org/), [installation](https://oxcaml.org/get-oxcaml/), [upstream README](https://github.com/oxcaml/oxcaml/blob/main/README.md), and [parallelism tutorial](https://oxcaml.org/documentation/tutorials/intro-to-parallelism-part-1/): compatibility, platform and concurrency constraints.
* [OCaml C interface manual](https://ocaml.org/manual/5.4/intfc.html): runtime/heap constraints for foreign calls; check corresponding pinned-version behavior during implementation.

## Design-review addendum

**Verified build baseline and OxCaml blocker.** Unchanged stock source built successfully with OCaml 5.5.1 using `make -C src tui -j4 TOOL_PREFIX=/usr/local/bin/` in `/private/tmp/unison-ocaml-baseline-19wiagcy`. Its `UNISON=/private/tmp/unison-ocaml-baseline-test-state ./src/unison -ui text -selftest` passed with exit 0 and `Success :-)`; user archives were not used. Logs: `/private/tmp/unison-ocaml-baseline-build.log` and `/private/tmp/unison-ocaml-baseline-selftest.log`.

An independent source copy in `/private/tmp/unison-oxcaml-design-39j0mce6` failed under `make -C src tui -j4 TOOL_PREFIX=/Users/alexy/.opam/5.2.0+ox/bin/` at `ubase/safelist.ml:164` against `safelist.mli:23`. Inferred `mem : 'a @ local -> 'a list @ local -> bool` did not match the declared `'a -> 'a list -> bool`. The preceding C stubs built. Log: `/private/tmp/unison-oxcaml-design-build.log`. No implementation fix or OxCaml Unison selftest was performed as part of this design probe. This is source-compatibility work for M0, not a missing compiler-installation issue.

**Recreated Lightroom engines: source evidence, not execution qualification.** `lrc-fingerprint-worker-20261005/crate/src/native.rs:8–38` constructs a version-specific native matcher wrapper from a recomputed raw digest, model, rational crop fields and opcode suffix. `pixel_digest.rs:22–26,55–110` supports bounded classic TIFF, unsigned single-plane CFA/LinearRaw and specific bit depths/compressions; `:381–423` implements the ordered 256×256 tile digest path. `:124–129` deliberately removes linearization from its decode path. `opcodes.rs:215–228` has an explicitly installed-Lightroom-15.6-specific suffix route. These are not a universal original matcher or render identity.

The separate proof worker's `proof.rs:7–60,87–138` binds decode context and ordered framed raw payload bytes, with descriptor-state rechecks. `:213` requires a prior successful full decode; it does not independently validate JPEG entropy. `core.rs:189–190` explicitly leaves receipt/journal/binary seal authentication and exact assignment checks to the caller. Its later context/payload gates support **reuse of a prior raw decode result**, not equality of all DNG contents. Linearization values, camera profiles, XMP and opaque data still need preservation/semantic identities. No real photos were run through these workers during this source review.

Expose optional diagnostics as separate structured channels: structural `{valid, invalid, unsupported, not_checked}`, raw decode `{success, failure, unsupported, not_checked}`, embedded digest per algorithm `{valid, mismatch, missing, unsupported, not_checked}`. Record stored/computed values, algorithm/tag, engine revision, supported-stratum ID and source snapshot identity. Only report `mismatch` after a supported successful recomputation; absence of an optional digest is not invalid DNG. Keep native matcher `{candidate, oracle_qualified}` with exact Lightroom version separate. The inspected implementation of a NewRawImageDigest-style algorithm is not automatically a RawImageDigest validator. The Lightroom UI Validate command's exact implementation was **not verified**; promise independently specified DNG checks, not Lightroom UI parity.

**APFS and parser probes.** Disposable APFS clone/write/rename checks confirmed inode separation, an unchanged source after a cloned byte edit, a copied test xattr, and expected old-inode behavior for hardlinks/open readers. Synthetic opaque-trailer fixtures confirmed selected-content equality can conceal same-length byte differences. These were small correctness probes, not throughput or crash-durability benchmarks. Do not extrapolate them to physical write amplification.

**Useful local reuse anchors.** `compare_dng.py:347–397` binds cache results to paths/stamps/version; its decoded equality remains intentionally distinct from bytes. `rust-scanner/src/main.rs:29–127` is a parser seed with known graph/duplicate/overlap gaps, not a validator. `rust-scanner/src/bin/dng-metadata.rs:76–80,195–202` compacts long values and resumes by row count, so cannot serve as lossless payload/write authority. `preserve_apo.py:54–102` and `rust-scanner/src/bin/byte-verify.rs:4–27` demonstrate the reusable reconstruction-plus-SHA-256 contract. Audit licenses and the exact current source before reuse.

**Historical design-only boundary (superseded).** The original design handoff changed only `SOL.md`. The user subsequently authorized Astra to start implementation, and switched to Sol after the tested first implementation was working. The live section at the beginning of this file is authoritative for implemented code, evidence and remaining work; this addendum preserves the original research findings, not the current implementation status.

## Photo interface receiver adoption — v1.0.2

Receiver adopted the exact countersigned normative preview storage/identity/recovery v1.0.2 contract; all four transmitted artifact pins and eight embedded evidence pins verified. Durable receipt: [photo-preview-interface-v1.0.2-adoption.json](doc/photo-preview-interface-v1.0.2-adoption.json). Photo Root/original preview implementation retain generators, Lightroom, Ten/Quasar placement and publisher recovery. Unison consumes the interface for semantic DNG, clone-aware filesystems and independent OxCaml workers. DNG payload equality or clone/delivery receipts do not authorize current-digest preview reuse: metadata/settings/dependency epochs must bind. Finite Ten native-byte recipe recognition is accepted within its stated scope; Quasar lifecycle, standalone rendering, monitor/UI qualification, capacity/performance, production and full runs remain disabled. No native window is granted. Normative changes require immutable successors; runtime evidence uses pinned scoped addenda.

Original-owner BIG selection seal verified: [receiver receipt](doc/photo-big-selection-owner-adoption.json). Saved native5976x3992 fits mathematically at4311.342685x2880 (ceil4312); header/SOF evidence is not native decode. Small2272 mechanism precedes separately admitted BIG storage tests. Ten recipe success does not qualify this key; no native/Quasar/production/full-run grant.

## Seeded worker scheduling qualification

Stock OCaml5.5.1 and OxCaml5.2.0+ox each passed six seeded mixed hash/DNG inspection schedules:3840 jobs,2942 exact sequential-parity completions,898 queued cancellations,8046 checks. Four domains share varying1..4 CPU permits; cancellation settles even while all CPU permits remain reserved, each round settles queues/permits, and lifecycle descriptors match baseline. Seven existing identify controls also pass on each compiler. Retained source/binary/log pins: [qualification](tests/workers/seeded-stress-qualification.json); [scope](tests/workers/README.md). No production changes or Photo/Adobe operations. This narrows M6 scheduling gaps; compiler-safe boundary, active apply/RPC stress, hard resource ceilings and measured full performance remain open.

Seeded DNG apply cancellation-race qualification: stock/OxCaml each passed384 private-stage jobs (192 exact full-byte target completions,192 cancelled/discarded stages),1255 checks under shared CPU budgets1..4. Basis/target inputs remain byte-identical; completed reports record16 metadata bytes/one write; queues/CPU/descriptors settle. [Pinned evidence](tests/workers/seeded-apply-stress-qualification.json). Timers race submission/execution but do not prove cancellation inside a specific write. No production change, publication, Photo/Adobe invocation or full M6 completion is claimed.

## JPEG semantic profile implemented

Opt-in `org.firstpair.jpeg-xmp/0` now registers independently negotiated `jpeg-xmp-v0` and locates one standard APP1 packet before the first scan. Existing generic SDE/workers/receiver clone/publication handle exact same-layout metadata edits; EXIF/ICC/entropy/opaque/trailer changes and growth/relocation fall back. Default and semanticdng selection unchanged. [Profile](doc/jpeg-semantic-profile.md), [pinned qualification](tests/jpeg/qualification.json):139 structural/kernel cases per compiler;30 actual mixed/old-peer/disabled CLI cases; private generated JPEG exact reconstruction and ImageIO raster parity; stock/Ox Make+Dune+selftests and existing DNG remote regressions pass. Root-owned review only. No JPEG validity/rendering equivalence, extended-XMP, Adobe/Lightroom or corpus/performance qualification is claimed; broader goal remains unfinished.

JPEG locator cumulative resource bound corrected:8192 total marker prefix/fill bytes now supplements4096 per-marker/4096-marker/16MiB limits, preventing multiplicative small-read workload. Stock/Ox each pass142 kernel cases, exact8192 and8193 boundaries and genuine prior-kernel negative controls; fresh Make CLI+selftests and six mixed-compiler receiving cases pass. [Evidence](tests/jpeg/fill-bound-qualification.json). This is bounded locator work, not full M6 resource/performance qualification; no Photo/Adobe operations.

## OxCaml compiler-checked boundary investigation

Five pinned installed-toolchain probes passed expected outcomes: unchanged real worker compiles with domain alerts; direct Domain.Safe.spawn substitution rejects its nonportable closure; portable Atomic capture actually executes; unsynchronized and plain-Mutex-protected reference captures both reject. [Evidence](tests/oxcaml_boundary/qualification.json), [implementation requirements](doc/oxcaml-checked-worker-boundary.md). Compiler proves the outstanding M6 boundary cannot be closed by renaming spawn or adding a ordinary lock. Next backend must mode-check synchronized queues/job ownership and selected worker/FFI interfaces while retaining stock support, sole Lwt owner and shared CPU permits. No production mutation or Photo/Adobe invocation; full M6 stays open.

## Checked mailbox component implemented

SemanticMailbox now provides bounded atomic FIFO/close/drain operations with stock and checked OxCaml interface forms. Unchanged source under the checked template actually passes Domain.Safe.spawn immutable packet/ID/cancellation/descriptor-message tests; mutable ref/bytes payload access rejects. Stock/Ox each pass12000 concurrent messages plus FIFO/full/drain/close races, and fresh Make+Dune CLI/selftests pass. Reply envelope allocation precedes winning dequeue CAS. [Component/scope](doc/checked-semantic-mailbox.md), [evidence](tests/checked_mailbox/qualification.json). Production worker pool and production interface selection are not switched yet; selected extension/native interfaces, counters/notification/CPU/FD ownership integration and complete M6 remain open. No Photo/Adobe operations.

## Photo Root scoped Quasar evidence received

Five sealed pins verified and [receiver receipt](doc/photo-quasar-small-timestamp-adoption.json) recorded. One preserved small Quasar highest2272x1704/Ten lower1136x852 control passed four actual native loads/decodes and independent readback, closed; exact Pyramid canonical-link timestamp813657716 binds, not target date813578156. Normative v1.0.2 is unchanged. Production strict placement, restart, BIG, renderer, rewrite/trim/missing/recovery and full run remain unqualified. Latest owner report places ordinary quit in a locked AgDialogs modal with coordinator59489 holding the lease and Classic40020 still alive; this session performed no fresh process audit or native work and infers no release. Photo Root/original preview owner retain execution.

## Checked production worker integration

The actual OxCaml worker closure now compiles with Safe.spawn, checked
portable/contended extension and recognition handles, XMP/delta interfaces and
atomic stopping/running/peak state. Owner registry/Lwt/admission/archive state
stays outside it. The mutex/condition protocol and single shared CPU/helper pool
are retained. Stock/Ox each pass28 full actual-object runtime cases (largest
pools18 workers),48 parallel metadata observations,3840 scheduling jobs/8046
checks,384 apply jobs/1255 checks,39 instrumented waiter-settlement cases,21
FD acquisition cases/117 assertions plus three historical guard negatives,14
helper cases/84 checks and21 receiving paths. Six compiler negatives reject bad
captures and the former mutable-counter worker. Both Make/Dune CLI builds and
selftests pass; checked Dune DNG and mixed JPEG receiving pass. All349 final
Make inputs match the frozen sources. [Current scope](doc/checked-semantic-worker.md),
[pins](tests/checked_worker/qualification.json). No native-contract compiler
proof, complete resource ceilings, performance speedup, GUI/platform or full
M6/M4-V/M5 completion is claimed. No Adobe/Photo invocation; preview ownership
remains with Photo Root.

## SDK pilot aggregate lifecycle checkpoint

Photo Root review accepted as DEFER: fresh generation plus pilot requires13 SDK calls (seed1/writers3/positive3/negative3/pilot3). Original request stays withdrawn. Native phase call ownership and remaining-budget propagation implemented, retained unresolved marker on ambiguous helper closure, actual core emits exclusive settlement proof only after all helpers/resources drain. Stock/Ox build-only and five synthetic helper cases each pass; four Python original process controls pass. No SDK invoked. Whole Python wrapper/fixture/hash lifetime and abrupt-wrapper failure remain unqualified: no successor native-admission request yet. [Checkpoint](tests/qualification/sdk-pilot-aggregate-checkpoint-20261014.json).

## Aggregate SDK pilot successor ready for Root review

The original 12-call request remains withdrawn. [Immutable v2 request](tests/qualification/sdk-pilot-coordination-request-v2-20261014.json) counts 13 (seed 1/writers 3/positive 3/negative 3/pilot 3), one CPU credit, seven generated inputs and one 300-second native phase including Python generation/hashing. Compilation and coordination wait precede that phase. Outer ownership reserves its leader PID through actual group cleanup, observes every other member absent, reaps once and records AGGREGATE-CLOSED.json. Failed observations retain an unresolved marker; timeout alone is never closure. Cancellation starts 8 seconds early, with bounded graceful cleanup and KILL escalation; wall overruns cannot pass.

This pilot links checked production ML objects and separately compiles the helper C stub with UNISON_BENCH_CONTAINED_HELPERS. Production retains separate helper groups; the finite pilot inherits its outer group and signals individual helper PIDs. It therefore qualifies functional/lifecycle behavior, not an exact production-C-backend timing comparison. Trusted native tools must not escape groups; killing the outer supervisor/kernel stalls remain outside the guarantee.

[Sealed source/synthetic evidence](tests/adobe_native_deadline/qualification.json): stock/Ox Make+Dune+selftests, production helper/validation groups, five synthetic benchmark settlement cases per compiler, six aggregate process cases, three actual-core aggregate cases per compiler (including abrupt Python exit), and full fake-tool pipelines with exactly 13 actual processes all in the owned group. Mocks do not decode JPEG/JXL or qualify SDK behavior. No SDK/Adobe/Photo calls ran. Unique start-file remains absent; fresh Root SDK admission and all pins must be checked before dispatch. Photo Root/original preview ownership is unchanged. Full actual SDK receive corpus/single-large-file parallelism and M4-V/M5/M6 remain open; this is an intermediate gate, not completion.

## Actual separately admitted SDK v2 pilot passed and closed

Root admitted the exact sealed v2 request under admission SHA 5d487d084384fd288fbe4fb3a30b695bb06bee752fe776dd88c9a33da3918e58. All source/native/production/compiler pins were checked immediately, unique start/output were absent before dispatch, and the exact command was executed once within the start deadline. Actual wrapper 53126/controller 53120/tool 4905 reached genuine terminal exit 0; aggregate 53366 closed/reaped with every other group member absent before leader reap, within 300 seconds at 37.658310349 seconds. Both unresolved markers are absent and the fresh executable snapshot shows no SDK/writer/validation-bench process. No retry or further slot reuse.

[Actual return packet](tests/qualification/sdk-pilot-v2-actual-return-20261014.json) binds admission/request, START, raw results/logs, wrapper closure and aggregate closure. Exactly 13 SDK calls completed: seed 1/writers 3/positive 3/negative 3/pilot 3; three real codec fixtures and all three current checked ML core receipts reported valid raw digest; three damaged-digest SDK controls reported mismatch/errors. Per-core final CPU/child counters 0, sampled peaks 1. Generated original 24MP CFA only; zero Lightroom/Photo/cache/Main work. Root received exact pins through the parent queue; original preview ownership is unchanged.

This proves actual public SDK v1 functional/lifecycle behavior with the contained pilot C backend and current checked production ML, not exact production C-backend timing, complete receive corpus/publication paths, one-large-file area-task parallelism, rendering/preview reuse or full M4-V/M5/M6 completion. The admitted slot is terminal and fully consumed; subsequent SDK work requires a fresh separately coordinated slot.

Root independently accepted the same completed pilot and its actual owner closure; SDK coordination hold is released. [Pinned receiver adoption](tests/qualification/sdk-pilot-v2-root-closure-adoption-20261014.json) binds Root closure SHA 4ac67c8cae8903aaf7cc074b940c03b73d600f7666d0024831ac50c4ec3fbb67. No replay or new SDK slot is authorized. Photo Root/original preview ownership remains unchanged; broader receive-corpus/parallelism/resource gates remain open.

Root final return acceptance also verifies all six pinned artifacts and embedded actual SDK result; [receiver adoption](tests/qualification/sdk-pilot-v2-root-return-adoption-20261014.json) records SHA c11b656b51ed6082855f17ff03a669ef91b59828a1153b156c9b392058672cdc. Existing functional/aggregate/owner closure scope is unchanged. BIG preview live-source filename/provenance repair belongs to Photo Root; SDK qualification is not preview fidelity and authorizes no new SDK window.

## Compact persistent common metadata bases implemented

Optional endpoint-local `semanticmergebasecache` now retains lossless DNG XMP,
full/protected SHA-256 identities, geometry and canonical parsed scalar spans,
value/shell hashes with explicit profile/policy/parser versions. Stasher captures
stable common-version candidates on shared worker/resource/CPU admission. New
held-descriptor legacy MD5 preserves its cursor and binds the archive fingerprint
to the exact descriptor inspected; no independent pathname hash is substituted.
Only the agreeing non-pseudo previous-common archive plus local root/path selects
a cache object. No current replica or decoded peer claim is inferred as a base.

Private UID/mode/name/held-file/size/link/checksum checks and no-replace publication
protect local storage. Shards bound scans; records retain earlier generations for
partial-commit recovery. Busy capture skips instead of recursively waiting on a
retained publication lease. Cache misses/staleness/unsupported input retain verified
full-backup fallback, otherwise preserve the conflict. Default stays off, no archive
or wire change, Windows cache disabled. General backups/original preservation retain
existing preferences; this packet cache contains no old image payload.

[Usage/format/limits](doc/dng-compact-merge-base.md), [qualification](tests/semantic_base_cache/qualification.json): stock5.2.0/Ox5.2.0+ox Make+Dune+selftests pass; each compiler passes12 cache-only CLI cases (8804-byte record for65536-byte fixture),13 independent SDB controls,8 actual-object held-MD5/cursor/replacement/FD checks,21 receiving-path regressions; prior full-backup13-case merge regression remains passing at its scoped source snapshot. Wrong-generation and checksum-valid wrong-policy records refuse; partial second-receiver rejection recovers deterministically. All data is original synthetic and validators are mocks; zero SDK/Adobe/Photo calls. Broad M4-V/M5/M6/corpus/growth/complete resource and performance qualification remain open. This advances the original metadata-base requirement without claiming overall completion.

Photo Root scoped namespace-import milestone [received and pinned](doc/photo-namespace-import-scoped-adoption-20261014.json): standalone host/import outside Classic succeeded and closed, zero RAW/render calls; independent no-rerun addendum distinguishes actual native success from original parser FAILED_CLOSED on the exact memory-manager stdout trailer. Duplicate ObjC-class warnings remain unresolved rendering risk. No new Unison/SDK/native slot, rendering capability, replay or ownership change is inferred; normative preview contract1.0.2 stays unchanged.

Compact-base private storage qualification now links actual unchanged Make cache
objects on stock5.2.0/Ox5.2.0+ox: each passes16 finite controls,256 valid loads,
repeated malformed/untrusted/missing/directory rejection with unchanged FD counts,
nonreplacement/path binding and4096-entry capacity refusal without temp residue.
Existing records remain usable at capacity. [Evidence](tests/semantic_base_cache/storage-qualification.json).
No Adobe/Photo invocation or implementation behavior change. Concurrent mutation,
allocation failures, crash durability, global quota and full M4-V/M5/M6 remain open.

## SDK-produced JPEG XL container eligibility corrected

Actual receiving of retained SDK-generated originals exposed /1 refusing four
DNG1.7 scalar tags in JPEG XL; preceding stock/Ox logs prove safe generic-clone
fallback. /1 now admits only Image-IFD ColumnInterleaveFactor SHORT/LONG1,
JXLDistance FLOAT1, JXLEffort LONG1 and JXLDecodeSpeed LONG1. Unknown tags and
malformed scalar shapes refuse; /0, exact complement proof and wire stay unchanged.
Scalar values remain protected bytes, not interpreted pixels or image validity.
[Source rationale](tests/sdk_container_receive/MODERN-SCALAR-NOTES.md).

[Sealed qualification](tests/sdk_container_receive/qualification.json): current
stock/Ox Make+Dune+selftests pass; each parser suite passes1253 cases/6288
assertions (including64 malformed scalar shapes and endian/classic/BigTIFF
controls); each actual Make CLI passes12 receiving cases over original
uncompressed/losslessJPEG/JPEGXL containers. All three now actually use SDE
with4543-byte packets. Clone-disabled exact transfer, protected-byte fallback,
mock receiver rejection, preserved old hardlinks, source identity/hash and
no-op inode/helper counts pass. Retained original fixtures were SDK-positive
in the consumed pilot; modified outputs are NOT SDK-qualified. Zero new SDK,
Adobe, Photo or Lightroom calls; no reused native admission. Camera corpus,
actual SDK receive/decode, resource ceilings and full M4-V/M5/M6 stay open.

## Compact-base merges qualified on retained generated codec containers

Current stock/Ox Make CLIs each pass15 actual two-replica cases across retained
uncompressed/losslessJPEG/JPEGXL originals, adding Rating/Label only within
existing fixed XMP padding on disposable copies. Cache-only disjoint merge,
competing scalar/protected-byte/missing-base refusal, partial second-receiver
rejection with fresh retry and successful no-ops all pass. Every recorded base
uses /1; original fixture identities/hashes remain unchanged, and neither
endpoint has a full backup directory. [Evidence](tests/sdk_container_receive/merge-qualification.json).

This extends M5 beyond small hand-built TIFF fixtures to SDK-produced container
layouts and real XMP packet wrappers. Base/merged edits themselves use MOCK
validation and are not SDK-qualified. Zero new SDK/Adobe/Photo/Lightroom calls,
no admission replay. Growth/general structures, actual SDK receive corpus, full
resource/performance qualification and complete M4-V/M5/M6 remain open.

## Compact-cache acquisition ownership hardened

Owner-only cache reads and bounded directory scans now install lexical exception
protection without allocating cleanup callbacks after acquisition. Temporary
records use precomputed exclusive names/flags and raw descriptors, avoiding
post-open channel/tuple setup; bounded partial writes retry EINTR, fsync and
no-replace linking retain exact format. Failed protected bodies close/remove
owned resources; a failed close is not retried on a potentially reused number.

[Qualification](tests/semantic_base_cache/ownership-qualification.json): stock/Ox
Make+Dune+selftests pass; each compiler passes16 actual storage controls,12
cache-only CLI regressions, and three private acquired-resource exception cases
(read/directory/temp) with descriptor conservation, no temp residue and fresh
follow-up capture/load. An intentionally unguarded private negative actually
leaks one descriptor and is detected. No real memory exhaustion, fuzzing or
production fault hooks. Universal allocation/native close/crash behavior and
complete M4-V/M5/M6 remain unqualified. Zero Adobe/SDK/Photo/Lightroom calls.

## General range adapter context parity corrected

The strict range loop now applies raw-decoder error invariants to direct typed
adapters too. Negative native codes, success carrying errno/native error data,
and failure lacking errno stop before accounting/notifying that call's prefix.
Earlier valid prefixes remain exact; contradictory results never authorize
suffix fallback or a successful receipt. This closes a typed-adapter bypass
while retaining valid native and legacy behavior.

[Qualification](tests/native_copy_range/typed-context-qualification.json): stock/Ox
each pass17 typed groups,13 actual macOS C preflight/unavailable groups and14
production receiver-range caller groups. Six bad typed contexts at zero/positive
prior progress refuse; separate private context/mutation negatives are detected.
Both Make/Dune builds+selftests pass. No native ZFS/ReFS/other-platform runtime,
range-sharing/performance, full resource or full-goal claim; zero Adobe/Photo/SDK
calls. M4-V/M5/M6 remain open.

## Finite actual SDK receiving successor prepared

[New request](tests/qualification/sdk-receive-pilot-request-v1-20261014.json) is
NOT ADMITTED. Two compiler-matched production ML CLIs are relinked privately
with only the existing contained test helper C backend. Original generated
SDK v2 inputs are copied/pinned; no SDK linking/loading/invocation ran. Fresh
Root request/READY/source/tool/CLI/input/command/deadline checks and exclusive
owned START are required; old/expired/consumed admissions refuse. Native tool
pins remain expected pins rather than being reselected from a changed file.

[Source/mock qualification](tests/sdk_receive_pilot/qualification.json): six
actual mixed-compiler SDE receives plus bad-digest publication refusal and three
original controls produce exactly10 MOCK entries, seven input states and16
logical states; aggregate genuinely closed/reaped/othersabsent in22.645s and
parent tool45265 exited0. Guard rejects wrong group/tool/input/eleventh call
even under optimized Python; pure admission controls pass one valid +9 denials.
The helper's restricted Python environment is handled explicitly. Entry markers
alone never prove execution/success; supervisor return is not parent exit proof.

Proposed native reservation is8 host credits (one semantic permit per endpoint
plus conservative legacy hashing/orchestration headroom),10 calls/7inputs/16states/
300s. Production-C timing, actual native receiving, broad corpus/area-task scaling
and full M4-V/M5/M6 remain open. Photo Root retains preview/native ownership;
consumed SDK v2 admission is not reused. No fresh native release is inferred.

## Actual SDK receiving pilot passed and parent closed

Fresh Root admission SHA4313662fd51f89b54e8fb322d984f76dbbe3869113022e693f1fb3d6bc491de0
authorized the exact new receive command. Pins/absent start state/no competing
SDK were checked immediately. Wrapper7661/tool84567 reached genuine terminal
exit0; aggregate7662 closed/reaped/othersabsent/within300s at31.661s. Exactly10
real SDK calls completed:3 direct original raw-digest-valid controls,6 mixed
stock/Ox semantic receives over uncompressed/JPEG/JXL with real require-gates,
and1 bad NewRawImageDigest update refused with destination intact. All output
hashes/group/count/multiplicity checks passed; unresolved marker absent.

[Sealed actual return](tests/qualification/sdk-receive-pilot-v1-actual-return-20261014.json),
[parent terminal evidence](tests/qualification/sdk-receive-pilot-v1-parent-terminal-20261014.json)
were queued to Root. Edited helper raw stdout is not separately retained; claims
are real SDK precommit acceptance plus exact output, not independently captured
raw-digest lines for every edited helper. This is contained test-C functional
receiving/lifecycle, not production-C timing, full receive/camera corpus, native
merge validation, rendering or full M4-V/M5/M6 completion. Slot fully consumed;
no retry or additional native scope. Photo Root retains preview ownership.

## Experimental area/memory SDK adapter linked, never executed

The combined separately named v3 area/memory host now builds/links against actual
SDK1.7.1:226 driver/SDK units plus fixture object,227 content-verified objects.
Static Mach-O x86_64 inspection finds actual area/allocator symbols; output is
9056672B SHA370a61af813f49bf88a96846efc55a4b57decb9f517a3563eb635e29ddb95795.
Actual builder tool24141 exited0. Qualified v1 driver retains ca49a32b... pin.
Neither new validator nor fixture writer was invoked; no runtime/thread/speed/
coverage or production capability inferred. [Evidence](tests/sdk_memory/link-only-qualification.json).

A dedicated build-only Make target now preserves the root Makefile's portability
and refuses qualified/unowned/busy output directories. Three independent local
refusal controls and static inspection pass. [Commands](tools/adobe-validator/README.md).
This source-only build closed before the separately admitted receiving pilot.
Actual capped-host/allocator qualification still needs a fresh Root slot; no
reuse of the receiving or older SDK admissions. Full M4-V/M5/M6 stay open.

Root independently verified and accepted the actual receiving pilot, its ten
SDK calls/six mixed receives/bad-digest refusal and actual parent terminal exit0.
[Receiver adoption](tests/qualification/sdk-receive-pilot-v1-root-adoption-20261014.json)
records exact Root/independent-audit/return/terminal pins. Preview coordination
hold is released; slot consumed, no replay/new SDK permission. Qualification
stays generated-container functional/lifecycle with contained test C backend.


### Capped SDK host comparison preparation — 2026-10-14

Prepared a source-only twelve-call matrix: each accepted generated uncompressed,
JPEG and JPEG XL original gets one reference call and experimental host calls
requesting 1/6/18 total threads including the caller. The preparer verifies linked
executables, experimental driver/header content and original input hashes, writes
an exclusive plan, and has no native execution mode. Its strict receipt checker
binds candidate SHA/size/build and valid structure/decode/raw digest/zero errors;
warning counts remain part of reference comparison. Twelve positive receipts,
132 malformed receipt denials and seven invalid matrix denials pass.
[Source/evidence](tests/sdk_host_matrix/qualification.json),
[usage and remaining gates](tests/sdk_host_matrix/README.md).

No SDK/Adobe/Photo/Lightroom process was invoked. This is preparation, not runtime
qualification or a fresh native request. A future executor must revalidate pins,
bind a fresh Root slot, run calls sequentially within 18 reserved credits/300s,
and prove aggregate and parent closure. The existing result protocol cannot prove
pixel equality, actual thread use or allocator peaks, so even validation-result
equivalence will not close those separate gates or establish scaling. Both earlier
SDK admissions remain consumed. Full M4-V/M5/M6 remain open.


### Finite capped-host executor — source/mock gate, 2026-10-14

Added `tests/sdk_host_matrix/run.py`: exact canonical twelve-call reconstruction,
source/tool/input pins, fresh separate host-matrix admission and deadline, exclusive
consumed workspace, sequential calls inside the existing 300-second aggregate,
raw diagnostics retained, positive bound receipts and per-codec reference parity
(including warnings), pre/post input/executable hashes, and separate aggregate
closure versus parent terminal evidence. No production endpoint changes.

Original fake Python validators passed twelve calls; warning divergence and a
zero-exit raw-digest mismatch each stopped after two calls, with genuine closed/
reaped/others-absent aggregate proof. Noncanonical argv refused before workspace
creation; completed workspace replay refused. Pure admission controls accept one
current exact request and reject five stale/wrong-state/pin/command/limit forms.
[Evidence](tests/sdk_host_matrix/executor-qualification.json). Prepared successor
plan v2 binds the new executor and containment sources. It grants no native slot.

Zero SDK/Adobe/Photo/Lightroom calls. Actual SDK execution, task/thread accounting,
pixel equivalence, allocator metrics/cancellation, representative performance and
full M4-V/M5/M6 remain open. Fresh Root coordination is required before any real
comparison; both completed earlier admissions stay consumed.


### Capped-host callback/allocator observations — source qualified, 2026-10-14

Experimental area host now records task attempts, successful Start calls, Finish
attempts, callback invocations/active/peak frames and largest partition, plus
explicit one-thread reference delegations. Borrowed observations live only through
synchronous joined tasks; callback frames retire on exceptions as well as success.
Experimental driver emits bounded stderr activity before host teardown, and
covered allocator limit/used/peak/live/denied after host/buffer teardown while its
allocator is still alive. Observation failure cannot terminate exception unwinding.
Production v1 protocol/default endpoint behavior remains unchanged.

Original scheduler passed789 assertions; simultaneous1/6/18 callback waves and
start/process/launch/finish failure observations passed. Four SDK driver modes
(single/area/memory/combined) compiled to unlinked objects. Added `--plain-only`
to the source runner: no sanitizer build/execution. [Pinned evidence](tests/area_scheduler/activity-qualification-20261014.json).
No SDK/Adobe/Photo/Lightroom runtime, source-photo access or benchmark.

These are callback frames (nested frames may share one thread), not OS-thread or
whole-process CPU accounting; codec threads remain outside the counters. Covered
allocation bytes are not RSS/all heaps. Real telemetry, pixel/thread equivalence,
resource/cancellation/scaling qualification and full M4-V/M5/M6 remain open. Prior
experimental linked artifact and comparison plans are preserved historical proof,
but source binding is now stale; Root notified by queue01a13c31-306e-7e72-8c90-f6d929256476.
A successor link/plan and fresh separate admission are required before runtime.


### Experimental telemetry consumer gate — 2026-10-14

The finite host-matrix executor now requires and retains each experimental
call's bounded versioned stderr area/allocator observations. It refuses missing,
duplicate, malformed or overflowing records, covered quota denials/unexercised or
unsettled allocation accounting, live callbacks, incomplete Start/Finish lifecycle
and partitions larger than the requested allowance. One-thread reference delegation
is explicit. Nested callback frames are not incorrectly treated as OS threads.

Pure controls passed three valid observations and62 malformed/inconsistent denials,
plus the earlier twelve protocol positives/132 denials and seven matrix denials.
Actual fake-tool runs passed twelve calls and independently failed/closed on warning
divergence, bad raw digest, missing telemetry, live allocations and active callbacks;
noncanonical commands and replay still refuse. [Evidence](tests/sdk_host_matrix/telemetry-qualification.json).
Zero SDK/Adobe/Photo/Lightroom/sanitizer execution. Actual SDK telemetry/codec/
allocator behavior, OS-thread/pixel/cancellation/scaling qualifications, source-bound
linked successor and fresh admitted plan remain required. Full goal remains open.


### Compact-base global capture quota — 2026-10-14

Implemented cooperative process-wide monotonic charged-payload/reservation caps
for new captures in `semantic-merge-bases-v1`. Defaults:1024MiB/1048576 reservations;
endpoint-local `semanticmergecachemaxmib` supports1..65536MiB and
`semanticmergecachemaxentries` supports1..16777216. Same-state cooperating owners
must agree on settings and calls stay on the sole archive/Lwt owner. A validated
private79-byte `.quota-v1` ledger uses nonblocking POSIX locking; charge+fsync
precedes record creation. Interrupted/failed capture keeps its charge, never
reclaims allowance or evicts recovery authority. Existing identical bases are
not recharged. Invalid/lost ledgers refuse new captures over retained records;
busy/exhausted capture is best effort and leaves ordinary sync usable.

Existing v0 bases remain trusted read-only fallback, preserving previous-common
recovery and format/policy checks; no legacy data is rewritten/deleted. Quotas
bound new managed payload/reservations, not filesystem block/metadata overhead,
old v0 data or RSS. Snapshot rollback, hostile same-UID changes, fsync-violating
storage and actual crash/power-loss durability remain outside this contract.
[Format/options/limits](doc/dng-compact-merge-base.md).

[Sealed qualification](tests/semantic_base_cache/quota-qualification.json):
stock5.2.0/Ox5.2.0+ox Make+Dune builds/selftests passed with exact current production
cache source bindings. Each compiler passed28 storage/quota controls (including
real separate-process lock refusal/clean reap, counter range/overflow/trust, lost
ledger and legacy recovery); six private acquired-resource exceptions plus an
actual unguarded FD-leak negative; and12 CLI compact-base merge/recovery cases.
Only deterministic original fixtures/mock validators were used. Zero Adobe/SDK/
Photo/Lightroom invocation or source-photo mutation. Full M4-V/M5/M6/native SDK
parallelism/performance/platform/resource qualification remains open.


### Observed experimental successor linked — 2026-10-14

Root allocated exactly four compiler credits, source/link only (releasefdc9e0f9).
Actual wrapper18172/builder18173/tool40529 started with4jobs and genuinely exited0
(terminalchunk33c87d); all builder subprocesses were synchronously awaited.
No SDK validator/fixture-writer output was executed. A new private observed-host
artifact links the current callback/allocator observations; static inspection
passes.227object/input pairs and every unique recorded dependency were rehashed.
Qualified v1 executable AND manifest match their prior receiving-preparation pins.
[Actual parent terminal](tests/qualification/sdk-host-observed-link-parent-terminal-20261014.json),
[artifact/source/static evidence](tests/sdk_host_matrix/observed-link-qualification.json).

Fresh comparison plan v3 binds this successor, current executor/containment sources
and three accepted codec originals. It is UNADMITTED: no new native capability,
SDK runtime, replay, scaling/pixel/cancellation/OS-thread/RSS proof or full goal
completion follows. Root got actualSTART and terminal closure by parent queue,
allowing closure of the four-credit compiler work before its exclusive native slot.
Historical Root review a17aaa3c accepts ONLY90b27d2 source/lifecycle, not newer
telemetry/current tree; [narrow adoption](tests/sdk_host_matrix/historical-root-review-adoption.json)
records that boundary. Current source/plan needs fresh review/admission before
SDK execution. Photo Root/original preview ownership and v1.0.2 remain unchanged.


### Fresh capped-host finite request prepared — 2026-10-14

Current plan v3 passes native-mode pin/canonical-input validation without executing
a child. Prepared [exact immutable request](tests/qualification/sdk-host-matrix-request-v1-20261014.json):
12 sequential SDK calls/3 existing generated inputs/12 logical states,18 declared
CPU credits/300s aggregate,1GiB covered backing allowance, fresh absent workspace.
All source/mock/header/link/parent-terminal pins and exact command are included.
This requests current-source review and future scheduling; it grants NO runtime
release and does not reuse either consumed SDK admission or the four-credit build
allocation. Root retains native scheduling/preview ownership and may prioritize
its forensic work. Actual OS-thread/pixel/cancellation/scaling/RSS and full goal
qualification remain separate. No SDK/Photo/Lightroom invocation in preparation.


### User-run Make entry points and current status — 2026-10-14

Added a separate `tests/Makefile`/`tests/manual.py` for the requested manual test
workflow, leaving upstream Make targets unchanged. `help` lists stock/Ox Make/Dune
build+selftest, compiler-matched cache storage/ownership/CLI and pure/fake-host
checks. Prefixes/paths/jobs are read as environment values and passed as argv;
DRY_RUN=1 executes no target and creates no receipt directory. Build/cache receipts
use fresh private output; existing runner process ownership is retained via exec.
No target automatically starts SDK, Photo/Lightroom, fuzzing or sanitizer work.

Actual Make dry-run smoke checks bind the stock compiler and real cache build
receipt, and `make -f tests/Makefile host-interface` executes the existing pure
protocol checks successfully. [Evidence](tests/qualification/manual-entrypoints-check-20261014.json).
[Current status/user commands](doc/implementation-status.md) now records actual
received-SDK, quota-cache and linked-but-unexecuted host checkpoints, corrects the
stale planned-merge/unlinked-host descriptions, and marks old worker rollout text
historical. Preview runtime ownership remains with Photo Root per the scope
agreement. Pending host-matrix request and all of its source pins are unchanged;
no admission exists and no SDK invocation occurred. Full goal remains open.


### Actual capped-host SDK matrix passed/closed — 2026-10-14

Root current-source reviewa5084a78 was verified, then fresh explicit runtime
admission100faf00 was discovered at the exact requested path and verified against
request7f3260c5, plan811c62cb, all current source/review pins, absent unique workspace,
zero other allocated credits and live start deadline. No old slot/review/build
allocation was reused. Wrapper25464/tool93165 executed the exact command once;
actual group25466 START1792013401.4599848 preceded its deadline1792013601.401626.
Root received actual START and retained its preview/compiler hold for closure.

All12 actual SDK calls passed: each generated24MP uncompressed/JPEG/JXL original
was validated by qualified reference1 and observed experimental1/6/18 hosts. Every
raw SDK receipt bound exact SHA/size/build, valid structure/decode/raw digest,
zero errors and the same4 existing CFA-padding warnings. Experimental1 delegated
to the reference area path;6/18 observed joined tasks and partition caps, with
peak18 callback frames in each18case. Covered allocation used/live/denied ended0;
JXL18 peaked507634690bytes under1GiB allowance. This is not RSS/OS-thread proof.

Actual tool terminalchunk0ea119 exit0/no session, not inferred fromps. Aggregate
closed/reaped/others-absent/exit0 in11.523550753016025s within300s; unresolved marker
absent. Exactly12 ENTRY/CALL pairs and all protocol/telemetry observations were
independently rebound, all input/tool/source postpins match.
[Sealed raw/parsed return](tests/qualification/sdk-host-matrix-v1-actual-return-20261014.json),
[actual parent terminal](tests/qualification/sdk-host-matrix-v1-parent-terminal-20261014.json),
[narrow source-review adoption](tests/sdk_host_matrix/current-root-source-review-adoption.json).
Root got exact return/terminal pins by queue01a13c55-8f4d-7ee1-8ff1-d3ba0eddcadd;
independent Root runtime acceptance/hold release is not inferred here.

The admission is consumed; no retry/new SDK window. Actual callback/covered-
allocator functional parity advances M4-V/M6, but fixed-order single samples are
not benchmarks; pixel/OS-thread/cancellation/quota-exhaustion/representative-camera/
production receiving qualification remain open. Qualifiedv1 is not replaced.
No Photo/Lightroom/Main/cache/source-photo mutation or preview capability claim.
300s covers the supervised aggregate, not pre-supervision wrapper pin validation.


### Root-accepted host result and current compact-container merges — 2026-10-14

[Root adoption](tests/qualification/sdk-host-matrix-v1-root-adoption-20261014.json)
verifies sealed acceptance fa34655d, its actual return/parent/independent-audit
pins, and released shared reservation. Admission100faf00 is consumed. Actual
functional callback/covered-allocation proof does not qualify OS threads, pixels,
cancellation, RSS, scaling, production or preview reuse. No new SDK invocation.

The quota-backed current stock/Ox Make binaries each passed all15 existing
SDK-generated-container compact-base merge cases: uncompressed/JPEG/JXL ×
disjoint/conflicting/protected-change/missing-base/partial-recovery. Both actual
runner tools terminated0; exact expected target hashes agree across compilers,
all current production source/binary pins rechecked before/after. Retained source
containers preserve full hashes/identities. Compact records are5155bytes for
4543byte XMP regions; validators are mocks. This closes the post-quota container
regression gap, not actual merged-output SDK/decode qualification.
[Sealed reports/terminal/source evidence](tests/sdk_container_receive/quota-merge-qualification.json).
No compilers, SDK, Photo/Lightroom/Main/cache or source photos were invoked or
modified. Full M4-V/M5/M6 and representative performance remain open.


### Immutable merged-output SDK preparation — 2026-10-14

Implemented [preparer](tests/sdk_container_receive/prepare_merged.py) binding the
current quota merge evidence, both compiler binaries/all production source pins,
15case rosters and all12 replica outputs. Original generated containers retain
full hashes; every changed result must match expected target size/hash and all
bytes outside its fixed XMP packet. Three identical cross-compiler candidates
were frozen read-only under a fresh private directory, with qualified v1 tool
and exact proposed single-thread argv. No SDK process invoked or old admission
reused. Fifteen deterministic controls reject protected changes/invalid extents/
stale evidence/incomplete compiler proof; actual repeated preparation rejects
its existing directory and leaves all artifacts unchanged.
[Sealed evidence](tests/sdk_container_receive/merged-preparation-qualification.json).
A separately reviewed contained executor and fresh Root slot remain necessary;
this is preparation, not actual merged-output Adobe qualification or a new
runtime request. Source photographs, Photo/Lightroom and production validation
configuration are unchanged. Full goal stays open.


### Finite merged-output executor ready for review — 2026-10-14

Added [contained executor](tests/sdk_container_receive/validate_merged.py) for the
three frozen outputs: qualified single-thread v1 only, exact canonical argv and
source/tool/candidate pins, raw ENTRY/CALL capture, exact candidate/build SDK
receipt, valid structure/decode/rawdigest/zeroerrors and four original warnings.
Fresh distinct Root state binds prepared/command/limits/sourcepins/deadline.
One exclusive workspace, three sequential calls,60s perchild/300s aggregate,
postchecks and actual group closure; wrapper tool terminal remains separate.
No SDK invocation: current native pin validation is pure. Mock positives and four
failed receipt/exit paths genuinely closed/reaped/othermembersabsent, consumed
workspace refuses replay, mock refuses production identity, canonical argv
rejects before acquisition and seven pure admission controls pass.
[Sealed source/mock gate](tests/sdk_container_receive/merged-executor-qualification.json),
[exact finite review request](tests/qualification/sdk-merged-output-request-v1-20261014.json).
Request is UNADMITTED; no past release reused. Original Photo owner retains all
preview scheduling/rendering/publishing. Actual merged-output SDK qualification,
production/camera/resource/performance and full goal remain open.


### User and extension guide implementation alignment — 2026-10-14

Source audit of SemanticFormats registration/selection found stale entry-guide
claims: v0-only DNG shorthand, JPEG unsupported, no scalar merge and no Adobe
throughput comparison. Updated [user guide](doc/semantic-sync.md) and
[extension contract](doc/format-extensions.md) to match actual v1/v0 preference,
separate JPEG opt-in, default exact/conflict behavior, separate narrow scalar
merge/common-base policy, and the scoped historical1/18/36 cached validation
measurements. No new runtime/performance claim or product behavior change.
The pending merged-output executor/request/sourcepins remain unchanged and
UNADMITTED. No SDK/Photo/Lightroom/compiler/benchmark invocation.


### Missing-common-base error and archive downgrade round trip — 2026-10-14

Fresh current→unmodified2.53.5→current archive regression found an actual bug:
a baseline-era update has no new compact base, and falling back to nonexistent
saved `.unison.mergearch` raised uncaught ENOENT. Narrow production fix catches
only missing saved-base ENOENT and raises recoverable Util.Transient with guidance
to capture a common version before merging. Both edits stay intact; no guessed
base, automatic cache reset or synchronization semantics change.

Stock5.2/Ox5.2+ox fresh Make+selftests pass with one compiler job at a time. Each
passes ten actual private loopback stages: current merge, old no-op/update,
current reopen, recoverable missing-base refusal, explicit known common restore
and new current common update/capture, subsequent disjoint merge and finalno-op.
Archive/state/root identities persist; no archives deleted/rebuilt by test.
Old no-op preserves receiver inode/bytes and archive names; ordinary bookkeeping
may rewrite archive hashes. Original previous-binary uncaught-error negative is
retained. [Runner/receipt](tests/archive_downgrade/qualification.json),
[scope/manual command](tests/archive_downgrade/README.md).
Pending merged-output SDK request/executor/frozen artifact pins are unchanged,
with historical producing-source scope; it remains UNADMITTED. No SDK/Photo/
Lightroom/source-photo invocation; both build and regression parents closed0.
Full goal/platform/resource/performance acceptance remains open.


### Recoverable merge filesystem errors with resource settlement — 2026-10-14

A direct actual-object probe reproduced raw Unix errors for missingleft/right/
output, ENOTDIR base parent and EISDIR output, despite settled resources. The
post-cleanup error boundary now uses existing Util.convertUnixErrorsToTransient:
normal filesystem errors become recoverable per-file failures, while unrelated
exceptions retain identity. Dedicated missing-common-base guidance remains.
No write/publication/common-base selection changes.

Current stock/Ox Make+selftests pass (one compiler job, builds serial). Both
actual production-object probes pass six filesystem failures, assert unchanged
sentinel hashes, baseline FD count and zero transaction/payload/descriptor/CPU/
worker/I/O ledgers after each. Previous-source negative reproduces five raw
errors (probeexit2), while already-fixed missing-base is transient. Both final
CLI binaries also rerun allten archive downgrade/recovery stages successfully.
[Sealed source/object/build/terminal evidence](tests/merge_io_errors/qualification.json),
[manual scope](tests/merge_io_errors/README.md). All owned parents closed0;
no SDK/Photo/Lightroom/production archives/source photos involved. Pending native
merged-output request/executor/frozen artifact pins unchanged and UNADMITTED.
Actual SDK merged outputs and broader M4-V/M5/M6 acceptance stay open.


### Source audit correction: restrict merge error conversion — verification pending

Inspection of the full inherited Util.convertUnixErrorsToTransient found that
it also converts Not_found and End_of_file. The preceding implementation's claim
that all programming exceptions retain identity was too broad. Source successor
now matches only Unix.Unix_error, Sys_error and Sys_blocked_io before calling the
utility; unrelated exceptions use unchanged Lwt.fail after cleanup.

Prepared an extended private module probe raising eleven explicit exceptions
after four descriptors are acquired, alongside six actual filesystem errors.
It checks exception constructors and FD/CPU/transaction/worker/I/O settlement;
no production injection hook or physical OOM. Python parses and unique private
injection anchor validates, but NO compiler/runtime verification yet. Requested
one compiler credit through queue01a13c6c-f0cb-7bc1-9268-08a53d816a0b to respect
Root's first standalone-render priority. Source changes remain uncommitted until
verified. Previous 95dbad8 receipts retain their original scope; its broad
programming-exception identity claim is explicitly corrected here.

Root source review of the three merged-output SDK calls is ACCEPTED with runtime
DEFERRED for that preview priority. All request/evidence/current executor pins
verified unchanged; [adoption](tests/sdk_container_receive/merged-root-source-adoption.json).
No native admission/credit/SDK run/replay inferred, no compiler/Photo/Lightroom
operation in this continuation. Goal active, not complete or a verified wait.


### Exception-classification correction verified — 2026-10-14

After the user reported Root's failed standalone-render closure and explicit
18credit release, resumed serial one-job source builds (no SDK/native slot).
Current stock/Ox Make+selftests pass. Both actual production probes pass six
filesystem failures; private actual-interface module copies pass eleven explicit
exception cases after four descriptors acquired: three OS errors convert to
Transient, and Not_found/End_of_file/OOM/Break/Failure/Invalid_argument/Fatal/
preexistingTransient retain constructors/payloads. FD counts, transaction/payload/
descriptor/CPU/worker/I/O ledgers settle and sentinels remain unchanged.
Previous95dbad8 implementation passes OS checks but fails precisely Not_found and
End_of_file in the new private negative (expectedprobeexit2). Original earlier
broad converter-identity claim is corrected, not silently reused as proof.
[Sealed current and negative evidence](tests/merge_io_errors/exception-qualification.json).
All build/probe parents genuinely closed0, no compiler reservation remains;
explicit raises are not physical OOM/EIO or asynchronous signal-delivery proof.
Merged-output SDK review accepted but runtime remains DEFERRED/UNADMITTED;
source/request/frozen candidate pins unchanged. No Adobe/Photo/Lightroom call or
completed-slot replay. Full goal remains active.


### Primary-reader telemetry WIP and compiler closure — 2026-10-14

Uncommitted work adds opt-in SemanticFile logical-read accounting and immutable
worker-completion reports to an owner-only observer, enabled in the CLI with
-debug semantic-reads. Counters cover the primary input reader only; nested
readers (including output verification), legacy/validator reads, partial/failed/
cancelled readers, prefetch, syscalls and physical disk activity are excluded.
Counts saturate with an explicit flag and never authorize publication.
Default jobs allocate/update no read counters. Observer executes after reply
settlement; a captured observer preserves a report when its reply callback
changes future observation. Observer errors retain sibling/pool settlement.

Initial reader/worker tests passed for stock/Ox, including48queued hashes in a
four-domain pool with3CPUpermits, exact counts, owner identity, observer failure
and reentrant disable. Stock final CLI SDE control passed exact bytes, old basis,
no-op and6291684primary-reader logical bytes for its2MiBfixture. Final stock/Ox
Make+selftests both pass. Latest added invalid-read/stability-failure checks and
final Ox CLI telemetry remain UNRUN; no completed telemetry qualification or
production speedup is claimed, and feature code remains uncommitted.

Root requested compiler closure before its next exclusive18render. Actual
stock35884/5f0696, Ox22482/bc233f, label-fix stock47112/3f2d2e and finalOx17796/
6bca0b all terminal0/no sessions. [Sealed owner receipts](tests/qualification/read-stats-build-owner-closure-20261014.json),
queue ACK01a13cd8-8abf-7a62-844f-956c62c9edf8. No compiler/probe/SDK successor
will dispatch until Root releases that window. This is a coordination hold,
not a live process wait on this session.

Fresh merged SDK admissione29f00cd expired UNSTARTED per Root; never executed
here, no SDK outputs, no replay. Separate future admission required. Photo
standalone-render failure remains unqualified; no native/render success inferred.
Goal remains active with the pending qualification work above.


### Primary-reader parser and benchmark bridge — source/pure checks only

During Root's approaching18render hold, no compiler/Unison/SDK dispatch.
Implemented a strict bounded pure parser for primary-reader diagnostic lines:
separate client/server job identities, exact field/byte-chunk relationships,
signed-int64 bounds, duplicate/saturation rejection and absence distinct from
measured zero. Five pure check groups pass, including18bad-receipt controls,
log-size admission and benchmark-counter opt-in/default behavior. Retained actual
stock CLI log independently reparses to3reports/6291684primary input bytes.
[Pure/readback evidence](tests/read_stats/parser-qualification.json).

`bench/sync/run.py` source now accepts --measure-primary-reads, enabling the debug
category only on current endpoints and storing a separate primary_reader_reads
counter. Semantic rows reject missing reports; application_read_bytes remains
None. Reference rows remain uninstrumented. No benchmark execution or timing/
physical/total-read claim. New whole-harness flag and final Ox CLI/latest failure
controls remain UNRUN; telemetry source remains uncommitted pending release and
verification. All six source pins of the deferred merged-output SDK request are
unchanged. Its expired admission stays consumed-unstarted, not reusable.


### Opt-in primary-reader telemetry qualified — 2026-10-14

Following actual Photo diagnostic closure/all18release (no render success
inferred), completed pending tests without Adobe calls. Final stock/Ox Make+
selftests pass; both compiler-matched reader/worker suites pass six groups,
including invalid/bounds reads, mutation at final stability check, callback
cleanup, owner-only reports, reentrant observer disable,48queued16MiBhashes in
four domains under3CPUpermits, and throwing-observer/sibling recovery. Both CLI
controls reconstruct exact SDE bytes, preserve old basis/no-op and report
6291684primary-input bytes for a2MiBfile. No counter state for disabled jobs.

The --measure-primary-reads full-harness functional matrix passes12rows and36CLI
invocations across stock/Ox ordinary/receiver-clone/SDE with1/2worker budgets
(max4configuredendpointcredits). All seed/update/no-op client/server/supervisor
closures verified, exact targets/bases/inodes/staging/private cleanup pass. Each
SDE2file row reports6primary-reader jobs/12583368logical bytes. Ordinary missing
reports remain unknown/not measured zero. Parent85911/d3a7ba exited0, no session.
[Sealed qualification](tests/read_stats/qualification.json),
[scope/manual checks](tests/read_stats/README.md).

This supersedes earlier pending-check notes for these same source features.
Primary readers exclude nested output verification, legacy/validator reads,
partial/cancelled readers, prefetch/syscalls and physical I/O. application_read_
bytes remains None. These are functional/diagnostic observations, not throughput,
whole-process bounds or full M6 qualification. Expired SDK admission remains
unstarted/unusable; no compiler/SDK/Photo/native-render activity remains owned.

### Manual telemetry dispatch and stale-build refusal — 2026-10-14

Added `read-workers`, `read-cli`, and `read-parser` to the user-run tests Make
entry points. Build-dependent cache and reader targets now compare every recorded
`src/` source pin, rather than checking only the cache module; stale worker or
transfer code cannot silently qualify current core behavior through this wrapper.
Existing binary/compiler checks and runner process ownership remain in place.
Pure command-construction checks accepted five current snapshot routes, rejected
four routes with a deliberately stale worker pin, and selected the parser route;
no child test/compiler/SDK was dispatched. `git diff --check` passes. The already
qualified runner suites were not rerun for this dispatcher-only change.
Photo HostV5 closed failed/no output and released its reservation; no renderer
success inferred. Merged SDK admission remains expired unstarted. Full goal is
active; broader SDK/pixel/resource/performance gates remain open.


### Worker completion wake-up allocation — source preparation only

During Photo's exclusive HostV6 runtime reservation, inspected clone/worker
source without compiler/core/SDK dispatch. Found `SemanticWorkers.notify`
allocated a one-byte Bytes buffer after completion mailbox publication; an
allocation exception there can terminate the domain before its wake-up write.
Source now writes an immutable constant string through Unix.write_substring,
retaining EINTR retry and EAGAIN/EWOULDBLOCK coalescing. No mutable scratch buffer
is shared across domains. This removes that specific explicit buffer allocation;
it does not claim all notification/runtime operations allocation-free or solve
all worker-exit/physical-OOM recovery. Source change is UNBUILT/UNTESTED pending
Root release, and earlier qualification receipts do not cover it. Required next
checks: compiler-matched stock/Ox builds plus existing worker/read-observer and
shutdown controls. No new native slot, no SDK admission reuse. Goal active.

### Worker wake-up source verified after HostV6 release

After Root's actual HostV6 closure/all18 release, ran finite serial stock/Ox
Make builds with at most4 compiler jobs and both complete selftests, then six
focused reader/worker groups on each matching snapshot. All passed, including
48 queued concurrent hashes/owner completions, observer exception/reentrancy and
normal shutdown. Stock89617/1756f0, Ox62506/706868, worker39214/2895fe and
23005/e18e05 actual parent terminals all exit0/no session. This supersedes the
UNBUILT/UNTESTED note above for this change only. [Current source/build/worker
pins and actual owner closure](tests/read_stats/wakeup-qualification.json).
Root queued actual closure01a13ce7-0119-7552-bf81-596dd66d7654; all compiler/core
credits released. No SDK/Photo invocation, fuzzing or completed-slot replay.
This removes one explicit buffer allocation, not every potential runtime or
closure allocation and not physical-OOM/failed-domain recovery qualification.

### Fresh merged-output SDK request after prior unstarted expiry

Confirmed Root's sealed v1 EXPIRED_UNSTARTED/zero SDK execution and continued
absence of its workspace. Read-only revalidation passes all three preparation/
executor evidence pins, all six executor source pins, the qualified single-thread
tool/manifest and three frozen merged candidate sizes/hashes/canonical commands.
Prepared [successor request v2](tests/qualification/sdk-merged-output-request-v2-20261014.json)
with a new unique workspace and separate v2 admission path. Same finite3calls/
3inputs/3states/1credit/300saggregate, no generation/writer/Photo work. Frozen
outputs retain historical source scope; no claim of current receiving-path or
pixel/render/resource/performance qualification. Prior admission cannot launch
this successor. Fresh Root review/admission is required; none exists or has been
inferred, no native execution performed. All compiler/core handles remain closed.

### User-run full functional sync matrix entry point

Added `make -f tests/Makefile sync-functional`, taking STOCK_RECEIPT/OX_RECEIPT
and optional fresh OUTPUT_DIR. It verifies both successful build/selftest,
compiler/binary and recorded production source pins, then directly execs the
existing finite sync runner with --qualification --measure-primary-reads and
four configured endpoint credits. This makes the 12-row/36-call exact synthetic
matrix reproducible from build receipts without shell assembly; it does not
start a benchmark, SDK, fuzz campaign or Photo operation. Shared build verification
also retains the existing cache/reader routes. Pure command construction accepts
both current wake-up snapshots, rejects missing/stale Ox receipts and preserves
five existing routes; no child matrix/compiler/test dispatched. Existing actual
matrix evidence remains historical, not relabeled as a new wrapper runtime.
Fresh merged-output v2 admission still absent on current readback; queued request
is not a release. Goal remains active.

### Worker-reachable foreign boundary source inventory

During Photo HostV8 reservation (no compiler/core/SDK dispatch), traced current
worker execution through SemanticFile/Hash/Delta. [Foreign audit inventory](doc/foreign-boundary-audit.md#worker-reachable-primitive-inventory-2026-10-14)
now separates five local C primitives, inherited Unix/channel/synchronization
operations, Windows fallback, trusted callback obligations and owner-only native
work. Explicitly retains shared-open-file-position exclusivity and identifies
unexpected worker/notification failure recovery as unproved, rather than treating
Safe.spawn as an FFI proof. This is source review, not compiler-runtime C audit,
new runtime evidence or all-inherited-FFI completion. HostV8 process-name snapshot
found no matching runtime command; that is not owner terminal/release proof, so
its reported reservation remains respected pending Root closure. Fresh merged
v2 SDK admission is still not inferred from its queued request. Goal active.

### Current core binds the frozen merged SDK candidates

After actual HostV8 closure/all18 release, ran the existing compact-cache merge
controls serially against current stock/Ox wake-up builds:15cases each across
retained generated uncompressed/JPEG/JXL containers (disjoint, competing,
protected change, missing base, partial receiver recovery). All30pass with mock
validators only. Rehashed every recorded current production source; all24
retained disjoint/partial-recovery left/right replicas match the three frozen
SDK candidates in exact bytes/size/SHA. This closes the current-output linkage
without regenerating inputs or changing immutable SDKv2 request pins.
[Actual runs/output binding](tests/sdk_container_receive/current-merge-frozen-binding.json).
Stock85623/c61399 and Ox30602/546f48 actual parent terminals exit0/no session;
post-terminal process snapshot finds no matching fixture-workspace processes.
That snapshot is not a new native process-group/wait4 proof. Root closure queue
01a13cee-777e-75b1-8807-0ea9cd65cbb2 releases all4corecredits. No compiler/SDK/
Photo operations, no production paths, no old admission replay. Fresh SDKv2
admission still required; merged byte validation/pixels/performance remain open.

### Actual merged synthetic output SDK acceptance — v2 consumed

Root issued fresh admission872819f54f550a742e909d572665bbd290b245e2847d82307334dda739e3f48b
for exact request70a380ae. Revalidated hash/deadline/source/command/limits and
unused workspace, dispatched once before deadline. Actual wrapper69150,
aggregate69151, owner3883. Exactly3sequential qualified single-thread SDK calls
(uncompressed/JPEG/JXL) accept all three frozen merged candidates: structure
valid, decode success, raw digest valid, errors0, expected warnings4 each (same
CFA edge-padding findings). Reparsed raw protocols against candidate SHA/size/
build, entry multiplicity, child reaps and post-source/tool/candidate pins.
Aggregate CLOSED/reaped/othermembersabsent/exit0 in5.3315609249984846s, unresolved
marker absent. Parent3883/5aae79 actual terminal0/no session.
[Sealed actual return](tests/qualification/sdk-merged-output-v2-actual-return-20261014.json)
and [parent terminal](tests/qualification/sdk-merged-output-v2-parent-terminal-20261014.json).
Queue actual return01a13cef-6cdb-7462-aab1-22db8f137613 to Root; independent Root
acceptance not yet inferred. v2 admission consumed, no retry/replay/new slot.

This supersedes pending merged-byte SDK acceptance notes for these exact three
candidates only. Current stock/Ox output equality was independently checked in
current-merge-frozen-binding.json; the SDK calls here validated those same bytes
as frozen files, not a live SDK-gated receiving pipeline. Broader corpus, pixel
identity/rendering, production C-backend timing, experimental threads/RSS,
representative full-sync performance and full goal qualification remain open.
No Photo/Lightroom/Main/cache call or production driver replacement occurred.

### SDK v2 independent adoption and live receiving successor scope

Read Root's actual CLOSED receipt and independently matched its parent terminal,
aggregate and released hold against the sealed owner result; rehashed runtime
artifacts and terminal receipt. [Durable receiver adoption](tests/qualification/sdk-merged-output-v2-root-adoption-20261014.json).
No new native execution. Next gate is actual SDK-gated production scalar-merge
receiving, not another validation of the same frozen files.

[Finite source plan](doc/live-sdk-merge-receive-plan.md) specifies3generatedinputs,
12states,6SDKcalls across stock/Ox receiving endpoints, exact/no-op witnesses and
one-thread qualified driver. Source review found the current aggregate runner
requires contained helpers, whereas production HelperSupervisor creates separate
groups. Its group receipt cannot be reused to claim production helper closure.
A separately qualified helper-group ledger/capture owner is a prerequisite;
do not modify production spawn behavior to fit the existing pilot. Proposed
limits are not reservation/admission; executor/ledger implementation and finite
lifecycle controls remain next. Full goal active, production paths untouched.

### Helper terminal identity diagnostic foundation — 2026-10-14

Added HelperSupervisor.result.child_pid, recording the successfully spawned
DIRECT child beside existing actual wait status. A separate historical integer
is installed nonallocating immediately after spawn while the original owned_pid
still exclusively governs signaling/reap. Returned identity is never consulted
by cleanup and never authorizes later signaling. Pre-spawn cancellation, failed
spawn and unsupported backend return None; actual timeout retains child identity.
No process-group creation, cancellation, wire/archive or validator policy change.

Stock/Ox helper suites each pass38groups, including new child-reported identity /
returned identity equality, ECHILD after successful supervisor reap, no fabricated
pre-spawn/failed-spawn identity, and timeout identity. Existing TERM escalation,
descendant cleanup, owner-loop/connection teardown and budget/validation tests
pass. Fresh both compiler Make+selftests pass. [Sources, raw terminal logs and
actual closures](tests/helpers/child-pid-qualification.json): stock suite78595/
1f2b2c, Ox52409/f05781, stockbuild8581/c11912, Ox63551/767b07 all0/no session.
Ox single-process synthetic helper retains two preexisting Sys.set_signal alerts;
no checked-worker/native-safety claim follows from those fixtures.

Root closure queue01a13cf6-f032-79e1-9f0b-0ec57ed7e185 releases all4credits.
No SDK/Photo/renderer invocation. This is a tested diagnostic prerequisite,
not implementation/qualification of the complete helper-group ledger or live
SDK receiving gate. Both remain next; no fresh native release has been inferred.

### Generic receiving helper diagnostic — source prepared during getter hold

While Root's read-only Classic getter reservation remains unreleased here,
prepared owner-side -debug validation-process in CandidateValidation's generic
context.execute wrapper, after supervised/I/O work settles and before validator
policy interpretation. It reports historical helper PID/status/outcome, candidate
SHA/size and bounded4KiB-per-stream hex stdout/stderr with explicit diagnostic
clipping and original capture-truncation flags. Default debug-off path does not
format/copy streams; no wire/archive/validator policy or worker logging change.
This applies to trusted companion backends, not just Adobe.

Prepared five finite fake-validator CLI controls in tests/validation_process:
default off, actual process/candidate/raw receipt binding, no-op silence,
exit-zero finding still rejects publication, arbitrary byte stderr clipping.
These new source and test changes are UNBUILT/UNRUN/uncommitted pending Root
release. Previous build/SDK qualifications do not cover this current source.
No compiler/core/SDK dispatch occurred; no native slot inferred or replayed.
Diagnostic lines are NOT surviving PID ownership, group-absence or validator/
publication authority; complete helper ledger remains required. Full goal active.

### Receiving diagnostic source qualified after getter release

After Root getter68209/aa5991/0 closed and all18released, serial stock/Ox Make+
selftests pass, and both current binaries pass five actual fake-validator CLI
controls. Default diagnostics are off, reported PID matches the fake child's
independent getpid record, captured protocol binds the candidate, no-op emits
nothing, helper exit0/errors1 still rejects and preserves the old target, and
arbitrary5KiBstderr clips exactly to4KiB in hex while valid receipt acceptance
is unchanged. [Current qualification](tests/validation_process/qualification.json).
Initial fixture-only failure correctly rejected an edited fake executable under
its stale private server pin; refreshed that fixture profile before both final
passing runs. No production change was needed for the fixture correction.

Actual stockbuild40120/724471, Ox40857/7cafb3, stockCLI49819/8a5d8e, Ox59407/
f00fcf all exit0/no sessions; initial73327/96de74 exit1 also genuinely terminal.
Root closure queue01a13cfc-b333-76f2-86e8-50ef52ecb50d releases all4credits.
This supersedes the UNBUILT/UNRUN checkpoint above for these sources only.
No SDK/Photo call, fuzzing or old admission reuse. Generic diagnostics remain
observational; the separate helper-group lifetime ledger and actual SDK-gated
production merge receiving test remain unqualified. Full goal active.

### Bounded receiving diagnostic parser and independent readback

Implemented tests/validation_process/records.py for the opt-in helper diagnostic
format: immutable endpoint/PID/status/candidate/capture observations,4MiBlog /
20kline /4096record /4KiBstream bounds, strict framing/numeric/hex checks and
separate capture/diagnostic clipping. Missing observations remain absent;
repeated PID observations are not deduplicated into an invented lifetime proof;
nonzero exits and exit0 findings do not become validator acceptance.

Pure finite controls pass22 malformed cases and independently decode six actual
retained stock/Ox mock records against their pinned original CLI reports, including
arbitrary stderr bytes and exit0/errors1. Both Python3.14/system3.9 pass; this
is not Python3.9 native-supervision qualification. [Pinned sources/reports](tests/validation_process/parser-qualification.json).
No compiler, core executable, helper, SDK or Photo invocation occurred. Live SDK
receiving executor/group-ledger work remains open; previous Root releases/admissions
are not inferred as a new native slot. Goal active.

### Spawn-bound helper group primitive: actual kernel/ABI qualification

Implemented optional/unintegrated opaque group bindings in helperSupervisor_stubs.c.
Create metadata before child acquisition; bound-spawn uses the exact original
native spawn body/attributes and records child/group assignment without a later
ML allocation. Counter accepts only an active same-process binding and retained
terminal direct child, checks waitid(WNOWAIT) before/after bounded64record macOS
process-group enumeration, and never signals/reaps. Retire before releasing PID.
Non-macOS/contained observations remain unsupported; errors are not zero.
Initial getpgid prototype actually failed ESRCH on zombie leader, motivating the
birth binding, not a swallowed failure. Intermediate refactor compile failure
spawned no child and was corrected before final checks.

[Current qualified sources/artifacts/actual terminals](tests/helper_group_observation/qualification.json):
stock20635/7194f8 and Ox1731/564275 pass native+bytecode five groups each plus four
private query-failure cases (ENOMEM/bad length/wrong live group/duplicate leader).
Tests include retained-zero, running/retired/reused/unspawned/lost-child refusal,
GC/serialization, real child status and descendant present→absent before leader
reap. Ordinary helper suites stock87305/70e74d and Ox1963/dee716 each38groups pass;
full Make+selftests stock31089/6821e4 and Ox71700/31e8f5 pass. All terminal0/no
sessions. Root closure01a13d11-df2f-7dc2-8cc5-9bcabef311aa releases all4credits;
all prior prototype/compile handles are also terminal. No SDK/Photo operation.

Production default ABI/spawn body is preserved and new observation calls remain
UNINTEGRATED. No live helper-group diagnostic/SDK receiving qualification follows
until bindings retire on all actual reap paths and current owner cancellation/
exceptional teardown are qualified. Kernel queries are SPI/current-host evidence,
not a future platform guarantee or escaped-child/owner-SIGKILL recovery promise.
[Native contracts/source reference](tests/helper_group_observation/README.md).
Full goal active, no native admission inferred/reused.

### Optional retained-group callback integrated: stock regression passed

HelperSupervisor.run now accepts optional observe_group, creating a private
spawn-bound owner only when requested. Normal terminal monitoring queries before
reaping; every waitpid path retires the binding first, including synchronous
teardown/EINTR retry and lost-child handling. Unsupported/query failures yield
None, never zero; diagnostic callback exceptions do not change helper policy.
Default spawn/result/wire behavior is unchanged. Callback is owner-only and must
not block, signal, reap, or reenter supervision. No diagnostic v1 format or SDK
receiving executor activation yet.

Actual stock helper suite39groups passes, owner31405/chunk884624/exit0/no session,
including callback failure isolation and independent post-return ECHILD. No SDK
or Photo invocation. Ox/native-bytecode full integration and optional teardown
path qualification remain pending; previous primitive-only qualification is not
relabelled as current integration proof. No full build claim. Full goal active.

### HostV15 hold: optional lifecycle regression source prepared

During Root exclusive18 HostV15, added focused opt-in timeout and pre-spawn
cancellation controls, and enabled observation in the existing synchronous
disconnect test. The latter asserts no fabricated terminal callback while
confirming actual child reap before the owner loop resumes. These additions
are NOT RUN; only the preceding39group stock integration run is actual evidence.
No compiler/helper/core/SDK dispatched during this hold. Next after explicit Root
closure/release: run current stock/Ox helper suites, then full serial builds.
Current integration remains unqualified for SDK receiving until these pass.

### HostV15 hold: deferred retained-group diagnostic forwarding

Source now forwards optional observe_group through DngValidation.validate_with_execution.
DngCandidateValidation enables it only with debug validation-group, captures the
observation in memory on the retained-child path and logs after supervised helper
settlement, bound to candidate SHA and historical child PID. Unknown/unobserved
remain distinct; no result policy, archive/wire or existing validation-process v0
parser changes. Added fake-valid/fake-error-zero receipt controls to ensure the
observation cannot replace SDK receipt checks. All these additions UNCOMPILED/UNRUN
during Root exclusive18 HostV15; zero new helper/compiler/core/SDK processes.
Next actual integration qualification must include these current sources.

### HostV15 hold: bounded group parser actual pure controls

Added immutable records.parse_groups for validation-group v0: bounded log/line/
record count, canonical PID/hash/count, native64record-capacity bound, and distinct
observed/unknown/unobserved states. Missing trace remains absent; duplicate PID
records remain separate past observations, never a joined lifetime or verdict.
Actual pure parser run7b187d/exit0 passes14 malformed group fixtures; existing
process parser22 malformed cases and six retained mock CLI records still pass.
Pinned report tests/validation_process/group-parser-qualification.json. No
compiler/core/helper/SDK/Photo invocation during Root hold. Current native/
forwarding source still awaits stock/Ox runs after explicit release.

### HostV15 hold: current CLI receiving regression prepared

Extended tests/validation_process/cli.py to request both trace classes and bind
each group observation to the independently recorded fake-helper PID and exact
candidate SHA. Current macOS normal helpers must report observed zero; other
backends explicitly unknown. Default-off and no-op must emit neither trace.
Exit0/errors1 still must preserve the old target, while raw/binary stderr bounds
remain tested. Parser source SHA now accompanies the CLI report. AST parse and
diff check pass; CLI execution remains NOT RUN pending Root release/current
stock+Ox builds. No new processes beyond source/pure Python work, no SDK calls.

### Manual entry points for current helper integration

Added helper-stock/helper-ox/validation-cli/group-parser Make targets to preserve
user-requested manual test execution. Compiler prefixes are passed as literal
argv; CLI requires current build source/artifact pins via checked_build. Existing
runner retains child ownership through exec, no extra SDK mode. Actual dry-run
stock/Ox command generation and pure14case group-parser pass b824d4/exit0. No
compiler/helper/core/SDK dispatched during HostV15 hold. Runtime integration
qualification still pending, not inferred from dry-run generation.

### Actual current helper integration stock/Ox suites pass after HostV15 release

After Root14750/65151e/0 actual release, serial stock51189/e8b8d1/0 and
Ox38446/8d44f2/0 each pass41groups, no sessions remain. Current optional normal/
timeout callbacks, pre-spawn cancellation, synchronous teardown/no fabricated
observation, callback exception isolation and validator valid/error-zero cases
pass alongside existing supervision controls. Both compile actual current
production helper/validation modules. Two existing Ox alerts confined to original
single-process fake-helper signal setup remain recorded. Pinned actual terminals
and sources: tests/helper_group_observation/integration-qualification.json.
No SDK/Photo invocation; full stock/Ox builds and receiving CLI still pending.
Finite pair allocation CLOSED/released, no successor dispatched.

### Actual full current group integration qualification passed

Following explicit Root14750/65151e/0 release, serial stock full Make+selftest
48021/4e32ed/0 and Ox47235/019297/0 pass. Actual receiving CLI stock11158/35a57b/0
and Ox75415/590990/0 each pass five cases: trace default/noop absent, each normal
helper observed group0 bound to independent actual PID and candidate, exit0/
errors1 preserves old target, arbitrary stderr clipping preserves acceptance.
All handles terminal/no sessions. Independent pure readback reparses all six
actual group records against CLI evidence and rehashes all recorded src pins,
current binaries, raw logs, receipts. Pinned qualification:
tests/validation_process/group-integration-qualification.json. This supersedes
UNCOMPILED/UNRUN checkpoints above for exactly these current sources. Prior
41group stock/Ox helper suite qualification also remains current.

All4credits genuinely RELEASED via queue01a13d1e-7e5f-7160-827e-82ba37980e55. No
SDK/Photo call or successor active. Next real integration target remains finite
SDK-gated production merged receiving with fresh explicit admission after source/
lifecycle review; these past group queries do not prove escaped-process absence,
owner-SIGKILL recovery, full corpus or throughput. Full goal active.

### Live SDK merge receiving: actual pure input preparation

Implemented prepare_live_merge.py: revalidates closed frozen SDK return/artifacts,
current stock/Ox source-matched build/selftest receipts and binaries; checks exact
protected bytes and reconstructs base/left/right/target within fixed XMP extents.
Actual36144/e792b6/0 freezes12 read-only states over3 retained generated codecs,
no native execution. Independently verifies all base/target hashes against both
historical merge reports; pure4state/8negative fixture controls pass140b69/0.
Evidence tests/sdk_container_receive/live-merge-preparation-qualification.json.

No runtime executor/admission exists yet. Next implement bounded production-path
executor and original fake-tool lifecycle controls; do not reuse contained-helper
phase.py as if it owned production helper groups. Native-group integration is now
qualified; unknown/missing/nonzero observations must retain unresolved failure
rather than signal historical PIDs. No compiler/SDK/Photo process active here.

### Live merge receiving case body and proof checking implemented

Added live_merge_cases.py without a native CLI/admission: caller must supply owned
run_sync and aggregate supervision. Body selects actual stock client/Ox server,
ordinary production helper groups, seed-off/disjoint-require/noop-require over
three codecs, target hashes/exact no-op identities/staging cleanup. Proof audit
requires exactly both endpoint receipts, candidate/hash/actualPID binding, full
capture/completed/exit0/SDK success/rawdigestvalid/errors0 and observed group0.
Unknown/unobserved/nonzero is unresolved failure; no historical-PID signaling.
Caller must return actual direct-child reap and bounded capture.

Pure audit tests pass9615e5/0: positive two-endpoint proof,11 negative traces and
unexpected-noop call rejection. No actual receiving CLI/SDK executed. Aggregate
controller/admission entry and original fake-tool lifecycle qualification remain
unimplemented; no native readiness/request inferred. All previous SDK slots
remain consumed. No compiler/core/helper or Photo operation in this step.

### Live receiving direct CLI owner source and refusal controls

Added live_merge_owner.py (no native CLI/admission). Runner retains each CLI
leader through group SIGTERM/KILL, bounded pre-reap membership checks and actual
wait4; captures stdout/stderr bounded4MiB, keeps active_owner reachable if cleanup
fails, writes individual START/CLOSED receipts. This certifies only the CLI group;
ordinary production helper groups remain separate. HELPER-OWNERSHIP-UNRESOLVED
starts before dispatch and can clear only after nine actual matching clean CLI
receipts and six audited endpoint proofs. No historical-PID signaling.

Pure refusal controls b654d9/0 and successor rerun pass incomplete/missing receipts
and pre-dispatch budget/time refusal with zero subprocesses. Finite real fake-child
lifecycle controls, native admission wrapper and independently timed aggregate300s
supervisor are NOT implemented/qualified yet. Existing monotonic deadline in
Runner is not claimed as total-wrapper300s supervision. No SDK/Photo calls, no
current compiler/core/helper allocation. Full goal remains active.

### Actual finite original fake-child CLI-owner lifecycle controls passed

After Root color57228/b45fbf/0 closed/released, actual one-credit serial lifecycle
test13675/96f3ba/0 passes six cases: normal,nonzero,5MiBoutput/4MiBcapture,TERM-
ignoring timeout→KILL,same-group descendant cleanup,capture setup failure. Each
actual direct child independently ECHILD after return, group absence observed
before leader reap, active owner retired. Test markers intentionally remain
because individual fake calls supply no six-helper matrix evidence; no live
child/CPU hold remains. Evidence live-merge-owner-lifecycle-qualification.json.

No SDK/Photo/compiler/real receiving call; aggregate300s controller/admission
entry still required and unqualified. This run is finite deterministic original
fixtures, not fuzzing/sanitizer work. One credit genuinely released.

### Independent aggregate controller implemented and fake-worker qualified

Added live_merge_aggregate.py: child establishes session before parentACK, parent
retains workerPID through independent wall deadline/cleanup/membership query and
wait4. Worker group closure is scoped separately from production helper groups.
EXTERNAL-HELPERS-UNRESOLVED can clear only after normal worker exit,9clean actual
CLI receipts and6required helper proofs; no signaling historical helper PIDs.
No native CLI/admission entry exists, six-helper production branch uninvoked.

Actual one-credit finite fixture owner42542/cf1c11/0 passes normal,failure,missing
helperproof,TERMignoringtimeout. Every worker independently ECHILD after actual
reap and within12s testlimit. Failed fixtures intentionally retain external proof
markers, not live children. Pinned evidence live-merge-aggregate-qualification.json.
No SDK/Photo/UnisonCLI/compiler executed. One credit RELEASED. Native entry/source
review/full mock receiving matrix still pending; full goal active.

### Full live receiving mock passed; fresh native request ready/unadmitted

Implemented run_live_merge.py admission wrapper. Native binds exact command/
workspace/prepared/source/limits/deadline, checks again in independently owned
worker; qualified v1 tool and fixed variants rederived from original+SDKaccepted
target witness pins. Mock tool cannot enter native mode. Aggregate300s covers
worker preflight+matrix, not total wrapper presupervision hashing.

Actual mock53937/a3cf4a/0 passes9CLI/six fake validations on production stock
client/Oxserver over3codecs. Exact final targets/noop identities/staging cleanup,
all nineCLI receipts, six endpointgroup0 observations, aggregate+external proof
closure and no unresolved markers pass. Evidence live-merge-full-mock-qualification.json.
All4credits RELEASED queue01a13d28-5e19-7700-acef-f772517af54f, no successor.
Seven pure admission refusal cases pass; native source-only preflight96729/
f0da0d/0 passes without any SDK invocation.

Fresh pinned request tests/qualification/sdk-live-merge-request-v1-20261015.json
is SOURCE_READY_RUNTIME_UNADMITTED:6SDKcalls/3inputs/12states/4credits/300s,
no Photo/Classic/Main/cache, no retries. Do NOT execute before fresh Root admission
and exact start deadline. Earlier SDK slots remain consumed. Full goal active.

### Read-only live-return auditor implemented during Photo hold

Added audit_live_merge.py: independently reads wrapper/preparation binding, actual
parent terminal,9CLI START/CLOSED identities,aggregate/supervisor binding,sixraw
protocols/group records,retained target bytes/identities,staging and unresolved
markers. Shares bounded protocol parsers, not claimed as independent source
review or native instrumentation. Actual pure922e83/0 passes prior genuine mock
readback and4terminal/provenance refusals; no subprocess. Evidence
live-merge-return-audit-qualification.json. Native request runtime source pins
unchanged; new auditor is offline only and request remains UNADMITTED. Root same
91195/4750 Photo lease+18credits hold remains; no compiler/core/helper/SDK dispatch.

### Offline native-return provenance hardening

Auditor now rejects duplicate/reordered codec rows and checks recorded target
hashes. Native mode separately requires pinned fresh admission, wrapper prepared/
source/workspace and actual dispatchPID/startdeadline bindings plus qualifiedv1
tool provenance; mock cannot become native by relabeling mode. Pure current
e25e5d/0 rereads genuine nine-run mock and rejects six cases, including two owned
metadata overlays (duplicates/native relabel) without modifying original evidence.
Successor evidence live-merge-return-audit-v2-qualification.json; native branch
not exercised because no native admission/result exists. Runtime request pins
remain unchanged/current. Root recovery release acknowledged, no Unison dispatch.

### Actual separately admitted production SDK-gated merge receiving PASSED/CLOSED

Fresh Root8d714359 admitted exact request7c108071. Exact command dispatched once
owner43830; wrapper93031, worker93039 START1792027837.012396 before1792028000.3138611.
Actual parent43830/699a51/0/no session; aggregate93039 reaped/own-group othersabsent
/exit0 in32.48622679398977s within300. All9actualCLIclosures,6qualifiedSDKv1 raw
protocols over3generatedcodecs on stockclient/Oxserver,all6retainedhelpergroup0,
exactmergedoutputs/noopidentities/staging cleanup and unresolvedscan[] PASS.
Native return auditor6980a0/0 independently reparses retained proof and provenance;
all11runtime sourcepins unchanged. SDK warnings remain receipt findings, not
pixel proof. No Photo/Classic/Main/cache operation.

Sealed actual return tests/qualification/sdk-live-merge-v1-actual-return-20261015.json
and actual parentterminal sibling pin all receipts/rawlogs/auditor/input/build
references. Actual RETURN queue01a13d2f-bac4-7f33-b4e1-0841bb69188b. All4credits
released, no successor active; Root independent audit pending. Admission consumed,
NO replay/newslot. This closes the finite production merge-receiving SDK gate,
not broader realcamera corpus/nativeRSSthreads/scaling/benchmark/fullgoal gates.

### Representative-size warm sync measurement preparation, no dispatch

Added bench/sync/prepare_plan.py: rechecks current stock/Ox build/selftest/source/
compiler/binary pins, emits literal commands only. Four separate batches32/128/
512MiB×4files and2048MiB×2files; each compares ordinary/receiverclone/SDE stock/Ox
workers1/6/8,onewarmup+5measuredreps (18configs,90samples,324CLIinvocations).
Loopback2endpoints means8+8=16configuredworkers under proposed18credit scheduling,
not18+18 on18cores. Primary-reader debug counters intentionally off for timing.
No coldcache/network/crossvolume/upstreamoriginal or physicalAPFS/RSS inference.

Actual pure5bcf0a/0 validates command/CPU/sample counts and3badbuild refusals; no
command executed/creditsreserved. Pinned v2plan/evidence
bench/sync/results/warm-plan-qualification-20261015.json. Performance runs still
UNSTARTED; Root scheduling needed before first32MiBbatch. Real native SDK merge
return remains passed/closed, independent Root acceptance pending, no SDK replay.

### Root independent live merge acceptance adopted

Verified Root5b9235bc independently accepted exact9CLI/6SDKreceipt/group/output/
admission/sourcepins and actual43830/699a51/0 closure32.486s. Receiver adoption
tests/qualification/sdk-live-merge-v1-root-adoption-20261015.json records exact
receipt pin. Fourcredits released, admission consumed/no replay. Planned warm
benchmark remains UNSTARTED, needs separate coordination before Root next18credit
color render; no new core/helper/SDK/compiler dispatch from this adoption.

### Performance next action revised after inspecting existing measured evidence

Found existing actual checked-worker-performance-20261014.json:32MiB×8files,
workers1/6,onewarmup/fivemeasuredreps,72rows. Do not relabel that historical source
snapshot as current, and avoid a smaller redundant32MiB×4 preliminary run. Current
plan successor v3 begins128MiB×4files, then512MiB×4 and2048MiB×2; workers1/6/8,
18configs/90measuredsamples/324CLIinvocations percompletebatch. All UNSTARTED.
Purebf22d2/0 checks3largerbatches+3invalidbuildrefusals. Evidence
bench/sync/results/warm-larger-plan-qualification-20261015.json. Proposed scheduling
now first128MiBbatch only; earlier32MiBproposal withdrawn unstarted, no resources
held. SDKactualRoot acceptance adopted; no newSDK/native/Photo capability.

### Warm128 dispatch STOPPED after Root scheduling DEFER; no measured result

Started first128MiB×4 batch owner60597 after observing Rootpublishedreserved0 and
announcing18credits, but BEFORE explicit Root timing allocation. That was a
scheduling mistake; current Root review DEFER/ZERO overrides intent. Actual
normalSIGINT to still-live benchmarkchild95348 ended60597/c34ac2/exit1/no session.
Eight warmups passed, zero measuredsamples, reportcompletefalse, privatefixture
removed, no matching workspace process. Server96294 and supervisor96291 have
actualreaped0 receipts; original nativeclient receipt was lost on exception
rethrow and is NOT fabricated retroactively. Partial owner/limits evidence
bench/sync/results/warm-128-stopped-20261015.json. Owner reservation relinquished,
no successor starts absent explicit coordinated allocation.

Fixed source measure.run to attach actual settled outcome to the original
exception and run.measure_invocation to retain it. Originalexception identity/
payload preserved; unknown evidence stays missing. Purecb0a3d/0 interface fixtures
pass across both wrappers, no child. Real fake-process successor qualification
and whole324CLI ownedaggregate deadline remain required before a refreshed
immutable plan/review. Existing SDKlive return accepted under original pins is
unchanged/historical; new sharedmeasure source is not relabelled oldqualified.
No SDK/Photo/compiler/new benchmark invoked by this source correction.

### Whole-batch owned deadline successor implemented SOURCE ONLY

Added run_bounded.py and batch_audit.py. Fresh exact Root allocation binds full
plan/index/workspace/command/sourcepins/deadline and18credits/7200s/324CLI. Worker
executes existing unchanged matrix then audits every row and client/supervisor/
server actualsettlement before success. Aggregateworker group has independent
wallclock supervision and unresolved retention; SDK default remains300s, only
explicitnonSDK maximum7200 overrides it. Wrapper preflight remains outside owned
worker deadline; no hard OS uninterruptible-wait claim. Allmatrix intact, no retry
or resumption of stopped60597.

Pureeeb471/0 reads216historical CLI receipts, rejects5badmatrix/7badallocation/
2preforkceiling cases, plus originalinterrupt receipt fixture. Purefaa69f/0
checks3largerbatch+3invalidbuild cases and freshly rehashes all v4plan/controller
pins. Evidence bench/sync/results/bounded-source-preparation-20261015.json, plan
/private/tmp/unison-warm-sync-measurement-plan-20261015-v4.json. These are NOT
actual ownership/benchmark qualification; interruptedreceipt realfakechild and
aggregate successor fakeworker regressions still pending fresh coordination.
ZERO new runtime jobs or credits allocated. RootPhoto fidelity priority retained.

### Finite receipt/aggregate successor lifecycle scripts prepared, NOT RUN

interrupted_receipt_lifecycle_test.py covers actual selfSIGINT direct/wrapper and
first/second capturecreation failure with original sleeping children, receiptPID/
reaped flag and independent ECHILD. aggregate_successor_lifecycle_test.py reuses
original4worker fixtures with explicitmaximum7200 but actual12s fixture deadlines;
no2hour wait or matrix. ASTonly9c15cf/0 valid; NO child dispatched. Exact sources/
serial commands/proposed1credit/<60s coordination request
bench/sync/results/lifecycle-successor-request-20261015.json. Timing DEFER
remains; these small regressions also await explicit allocation to avoid another
crossed dispatch. Future refreshed timing plan follows runtime qualification.
