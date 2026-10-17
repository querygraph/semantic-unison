"""Pure successful helper-prefix audit. Never authorizes FD/parent release.

Failed or incomplete prefixes need the future coordinator's separate lifecycle
audit; rejecting a verdict here must never be treated as known resource closure.
"""
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from validation_process import records
from camera_sdk_receiving.sdk_audit import receipt, BUILD


def successful_helpers(log, *, candidate_sha256, candidate_bytes, phase):
    if phase not in ('baseline', 'validate'):
        raise ValueError('exact phase required')
    if (type(candidate_bytes) is not int or not 0 < candidate_bytes <= 256 * 1048576
            or type(candidate_sha256) is not str
            or re.fullmatch('[0-9a-f]{64}', candidate_sha256) is None):
        raise ValueError('exact bounded candidate identity required')
    processes, groups = records.parse(log), records.parse_groups(log)
    if phase == 'baseline':
        if processes or groups:
            raise ValueError('off baseline contradicts helper observations')
        return dict(sdk_helpers=0, resource_release_authorized=False,
                    scope='absence of diagnostics only; pinned off command and owner proof required')
    if len(processes) != 2 or len(groups) != 2:
        raise ValueError('exact client plus server helper pair required')
    if {p.endpoint for p in processes} != {'client', 'server'}:
        raise ValueError('one helper per scanned endpoint required')
    if len({p.pid for p in processes}) != 2:
        raise ValueError('distinct loopback direct helper PIDs required')
    reports = []
    for process in processes:
        matching = [g for g in groups if (g.endpoint, g.pid, g.candidate_sha256)
                    == (process.endpoint, process.pid, candidate_sha256)]
        if (process.pid is None or process.candidate_sha256 != candidate_sha256
                or process.candidate_bytes != candidate_bytes or len(matching) != 1
                or matching[0].observation != 'observed' or matching[0].other_members != 0):
            raise ValueError('helper/group/candidate binding or settlement differs')
        if (process.status != ('exit', 0) or process.outcome != 'completed'
                or not process.complete_capture):
            raise ValueError('SDK helper did not complete with full capture')
        report = receipt(process.stdout, candidate_sha256=candidate_sha256,
                         candidate_bytes=candidate_bytes, build_id=BUILD)
        reports.append(dict(endpoint=process.endpoint, pid=process.pid, report=report,
                            stdout_hex=process.stdout.hex(), stderr_hex=process.stderr.hex()))
    return dict(sdk_helpers=2, endpoints=reports, resource_release_authorized=False,
                unchanged_transfer_proved=False, candidate_path_isolation_proved=False,
                scope='bound helper receipts only; caller must join no-transfer, private path and owner proofs')
