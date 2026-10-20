"""Pure exact raw pair composition for positive seed and designated negative.

Never interpret an expected CLI rejection as an ordinary safe failed prefix.
Neither branch supplies destination/worker/parent closure or FD-release proof.
"""
from sdk_merge_receiving.evidence import bind
from sdk_merge_receiving.helpers import audit as seed_helpers
from sdk_merge_receiving.plan import require
from sdk_negative_receiving.transport_audit import audit as negative


def audit(row,pair,raw,candidate,*,proxy_command):
    require(row['stage'] in ('seed','negative'),'fixed negative receiving stages required')
    if row['stage']=='seed':
        call=bind(row,pair,expected_proxy_command=proxy_command,raw_proxy_bytes=raw)
        helpers=seed_helpers(call['log'],stage='seed',returncode=call['returncode'],
            candidate_sha256=candidate['sha256'],candidate_bytes=candidate['bytes'])
        return dict(stage='seed',call=call,helpers=helpers,resource_release_authorized=False,
                    destination_fence_required=True,worker_settlement_required=True)
    return dict(stage='negative',call=negative(pair,client_command=row['command'],
        proxy_command=proxy_command,server_command=row['server_command'],policy=row['policy'],
        raw_proxy_bytes=raw,candidate_sha256=candidate['sha256'],candidate_bytes=candidate['bytes']),
        resource_release_authorized=False,destination_fence_required=True,worker_settlement_required=True)
