# Transport-separated opaque-DNG fallback qualification

The first exact scoped execution has passed and closed; see the actual section
below. Its admission is consumed, not permission to rerun. The
`coordinator.py` entrypoint requires a fresh exact Root admission, plan and
admission SHA before resource acquisition or launching the internal worker.
`case.execute_case` requires that coordinator to own the IO/CPU bundle and all
separately sessioned client/supervisor/server lifetimes, retain unknown outcomes,
and audit the result before release. Do not wrap it in the simple local-job
shared target or run it as an unowned subprocess.

Why separate transport: actual local-root tests showed the preferred whole-source
clone succeeds before semantic inspection. Cloneoff also bypasses semantics.
Neither tests the generic receiver-basis path after an unsupported semantic tag.
The existing qualified same-host loopback transport is therefore reused here,
with exact generation and closure checks rather than a forced production switch.

Planned scope: four stock/Ox client/server pairs, one1MiB generated DNG-shaped
file with tag50740 per pair, seed/update/noop per pair (12CLI). Configure two
semantic workers per endpoint plus two owner credits inside Unison's8-credit
lane. These private synthetic bytes are not photographic or Adobe-valid DNGs.
No SDK/helper/Photo/original/privatecamera data is needed. Current v0/v1 eligibility
and production transfer code remain unchanged.

The case helper uses the existing strict `measure_invocation` ownership and
proxy protocol. It records each actual outcome before inspecting it, checks
both binaries before calls, hashes full generated outputs/basis, independently
hashes the complement outside the fixture's declared XMP bytes, checks no-op
FIVE and stage residue, and stops starting calls near its supplied outer deadline.
Failures preserve partial CASE metadata. An exception is NOT proof of closure:
the future outer owner must retain live handles/leases on unknown. The helper
does not itself acquire or authorize resources, collect parent terminal proof,
provide an aggregate controller, or issue any SDK/native admission.

`audit.py` requires exactly four unique compiler pairs, twelve successful
invocations, strict direct owner cleanup plus native server/pump closure,
semantic decline, one receiver-basis clone start and positive partial inherited
bytes. Local source-clone or successful SDE traces are forbidden: those would
mean the test accidentally exercised another path. The general timed/shared
matrix auditors are unchanged and not weakened to accept this smaller result.
The [pure audit receipt](../qualification/private-remote-fallback-audit-controls-20261016.json)
uses fabricated reports/logs only. It does not prove real receiving or the case
helper's execution. The aggregate/controller is now source-prepared below; a separately admitted
finite IO window remains required before the first transfer.

## Pre-launch ledger and failure settlement

The case helper now writes an exclusive stage INTENT before calling the existing
transport owner and an exclusive OUTCOME after a returned success or qualified
InvocationFailure. A pending intent is not erased on an unexpected exception.
`ledger.audit_directory` checks every recorded call, including failed calls,
for exact argv, direct client/supervisor group settlement, bound server wait
and joined input pump. A nonzero settled call remains a functional failure.
Missing or malformed proof stays unknown; no numeric PID cleanup follows from
this validator. The future outer owner must stop new calls and independently
prove its worker/group closure before consuming these records. Empty ledger
is not independently established no-dispatch proof.

[Seven fixed fabricated controls](../qualification/private-remote-ledger-controls-actual-20261016.json)
passed under Unison00..07 and closed; no transport, payload or Photo IO ran.
The aggregate/coordinator below has mocked coverage only; live qualification
remains separate.

## Prepared aggregate coordinator

[Plan v1](../../doc/private-dng-remote-fallback-plan-v1.json) and
[request v1](../../doc/private-dng-remote-fallback-request-v1.json) freeze the
coordinator and all18 execution sources. No admission exists in this request.
Root's eventual receipt must bind the exact plan hash, workspace, fresh start
deadline and `launch_argv_without_admission_sha256` prefix; append
`--admission-sha256 <published-receipt-hash>` at launch. Omitting that hash from
the receipt's own argv field avoids a self-referential hash.

The coordinator exclusively creates a one-use workspace, acquires EX_GLOBAL IO
then Unison00..07 as one nonblocking bundle, revalidates source/admission and
binaries, and launches one worker inheriting all9 descriptors. The parent keeps
its copies throughout. The worker stops starting calls before440 seconds; the
owner observes up to480 seconds, reserving40 seconds for a bounded in-progress
call to settle. Unknown settlement retains ownership past the observation
deadline; it is not a hard aggregate kill deadline. It never kills an aggregate
whose separately sessioned native children lack proof. Parent preflight and
post-observation census/receipt work are explicit additional scope.

After worker terminal observation, the parent independently reparses every
stage ledger, checks the worker's separate closure record, settles the worker
group, binds functional results to the exact saved call outcomes, and closes
CPU then IO. Nonzero but fully settled failure is released as failure, never
converted to pass. Missing evidence, uncertain close, changed source, or pending
worker retains ownership. A final report error after known closure propagates
as a reporting failure without falsely claiming live resources.

[Fifteen fixed mocked controls](../qualification/private-remote-owner-controls-actual-20261016.json)
passed and closed under Unison00..07. They use fake grants/owners/receipts only;
no actual IO lock, transport, source fixture, native/SDK/Photo input or compiler.
Thus real aggregate/server settlement and receiver-basis fallback remain unrun.
The proposed budget is conservative declared logical IO, not enforced physical
IO, RSS, descriptor-count or OS-thread caps.

## Actual first execution — 2026-10-16

[Sealed actual receipt](../qualification/private-remote-fallback-actual-20261016.json):
Root admission8894bb49 consumed once, owner91702/session11511 actual terminal
a3b0b5/exit0/no session; worker91703 reaped0/other members absent. Four compiler
pairs completed twelve calls. All12 raw proxy receipts and saved stage outcomes
were independently rebound, all16 copied transport sources matched frozen pins,
and the inherited descriptor identity set was exactly Unison00..07 plus the
existing EX_GLOBAL barrier. IO and CPU descriptors closed; unknown markers absent.

Every update showed explicit semantic decline, exactly one immutable receiver
clone basis, positive partial logical inheritance (3072bytes each), exact output,
unchanged prior receiver inode contents, unchanged source complement, stable
no-op FIVE and no receiver staging residue. This is actual transport-separated
ordinary fallback evidence, distinct from the local preferred whole-source clone.
It does not demonstrate eligibility for opaque50740, SDK/pixel validity, physical
extent sharing, physical writes, measured savings, throughput, network-device
independence, a quiet timing window or a general production IO-pool integration.
No original/privatecamera/Photo/Adobe data or code was used.

The request/plan and source/mocked-control sections above remain historical
preparation records. They are superseded only for this exact four-pair test by
the actual evidence here; no new admission or automatic successor is implied.
