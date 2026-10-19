"""Pure current merge helper audit; consumes complete captured diagnostics only.

No-helper log absence alone never proves pre-creation on a failed command. The
caller still audits raw transport, publication bytes, worker and all owning FDs.
"""
from camera_sdk_receiving import sdk_audit
from sdk_merge_receiving.plan import BUILD, digest, require

records = sdk_audit.records


def audit(log, *, stage, returncode, candidate_sha256, candidate_bytes):
    require(stage in ('seed', 'update', 'noop') and type(returncode) is int,
            'exact phase and typed terminal status required')
    digest(candidate_sha256)
    require(type(candidate_bytes) is int and 0 < candidate_bytes <= 128*1048576,
            'bounded expected merge candidate required')
    processes, groups = records.parse(log), records.parse_groups(log)
    require(len(processes) == len(groups) <= 2,
            'complete bounded endpoint helper records required')
    endpoints = [p.endpoint for p in processes]
    require(len(set(endpoints)) == len(endpoints)
            and set(endpoints) == {g.endpoint for g in groups}
            and len({g.endpoint for g in groups}) == len(groups),
            'duplicate or unmatched endpoint helper records')
    # Even successful commands with no expected validation need the independent
    # transport/policy audit. Failed commands require production call-order or
    # helper-live census evidence that this pure log parser cannot manufacture.
    require(returncode == 0, 'failed command requires separate retained-prefix audit')
    expected = {'client', 'server'} if stage == 'update' else set()
    require(set(endpoints) == expected, 'phase helper count or endpoint differs')
    verdicts = []
    for endpoint in ('client', 'server'):
        if endpoint not in expected:
            continue
        process = next(p for p in processes if p.endpoint == endpoint)
        group = next(g for g in groups if g.endpoint == endpoint)
        require(process.pid is not None and process.pid == group.pid
                and process.candidate_sha256 == group.candidate_sha256 == candidate_sha256
                and process.candidate_bytes == candidate_bytes,
                'helper candidate/PID binding differs')
        require(process.outcome == 'completed' and process.status == ('exit', 0)
                and process.complete_capture and group.observation == 'observed'
                and group.other_members == 0,
                'helper terminal, capture or retained-group observation unresolved')
        report = sdk_audit.receipt(process.stdout,
            candidate_sha256=candidate_sha256, candidate_bytes=candidate_bytes,
            build_id=BUILD)
        verdicts.append(dict(endpoint=endpoint, pid=process.pid, report=report,
                             stderr_hex=process.stderr.hex()))
    return dict(stage=stage, helpers=verdicts, helper_count=len(verdicts),
                raw_transport_audit_required=True, output_bytes_verified=False,
                worker_settlement_proved=False, resource_release_authorized=False)
