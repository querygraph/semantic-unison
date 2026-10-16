# Prepared transport-separated opaque-DNG fallback case

This package is SOURCE PREPARATION, not a runnable/admitted test. There is no
standalone entry point that can launch Unison. `case.execute_case` requires a
future qualified outer coordinator to own the IO/CPU bundle and all separately
sessioned client/supervisor/server lifetimes, retain unknown outcomes, and audit
the result before releasing anything. Do not wrap it in the simple local-job
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
helper's execution. A pinned aggregate/controller and separately coordinated
finite IO window remain required before the first transfer.

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
The complete aggregate/coordinator remains to be prepared and qualified.
