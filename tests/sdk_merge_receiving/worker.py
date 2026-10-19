"""Caller-owned serial merge kernel, without a native CLI or admission route.

All adapters are trusted pinned executor code, not fields accepted from a packet.
The caller owns IO/CPU and preparation descriptors. invoke must retain actual
children/captures on uncertainty; audit_transport independently reparses raw
proxy/journal evidence. This kernel never releases those resources.
"""
from copy import deepcopy
import hashlib
import json
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.plan import schedule, require
from sdk_merge_receiving.ledger import Ledger
from sdk_merge_receiving.helpers import audit as audit_helpers


def execute(binaries, tool, workspace, *, prepare, invoke, audit_transport,
            verify_outputs, persist):
    contract = schedule(binaries, tool, workspace)
    ledger = Ledger()
    results = []
    def save():
        persist(dict(ledger=ledger.report(), results=deepcopy(results),
                     resource_release_authorized=False))
    save()
    for row in contract['rows']:
        # Source/clone preparation must itself preserve uncertain descriptor
        # ownership. It occurs before any command intent or process dispatch.
        candidate = prepare(deepcopy(row))
        require(type(candidate) is dict and set(candidate) == {'sha256','bytes'},
                'exact expected phase candidate required')
        command_hash = hashlib.sha256(json.dumps(row['command'],
            ensure_ascii=True, separators=(',', ':')).encode('ascii')).hexdigest()
        index = ledger.begin(row['codec'], row['stage'], command_hash)
        save()  # Durable intent must complete before invoking any child adapter.
        outcome = None
        try:
            outcome = invoke(deepcopy(row))
            # The adapter must consume independently read raw evidence, not a
            # caller's booleans or a zero returncode. It raises on any gap.
            audit_transport(deepcopy(row), outcome)
            require(type(outcome) is dict and set(outcome) == {
                'returncode','log','transport_record_sha256','helper_record_sha256s'},
                'exact audited invocation result required')
            helpers = audit_helpers(outcome['log'], stage=row['stage'],
                returncode=outcome['returncode'], candidate_sha256=candidate['sha256'],
                candidate_bytes=candidate['bytes'])
            verify_outputs(deepcopy(row), deepcopy(candidate))
            ledger.finish(index, returncode=outcome['returncode'],
                transport_record_sha256=outcome['transport_record_sha256'],
                helper_record_sha256s=outcome['helper_record_sha256s'])
            results.append(dict(index=index, codec=row['codec'], stage=row['stage'],
                                candidate=deepcopy(candidate), helpers=helpers))
            save()
        except UnresolvedOwnership:
            # Preserve the original carrier, all owner/capture references and
            # every uncertain descriptor identity. No replacement or retry.
            raise
        except BaseException as error:
            retained = UnresolvedOwnership(
                'merge invocation or its independent audit unresolved; retain owner')
            retained.original_failure = error
            retained.invocation_outcome = outcome
            retained.call_ledger = ledger.report()
            # No failure-record callback here: it could replace the primary
            # uncertainty. The outer retained owner persists this carrier.
            raise retained from error
    return dict(ledger=ledger.report(), results=results,
                resource_release_authorized=False)
