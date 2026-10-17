"""Independently join a known failed all-scanned journal prefix.

No current paths/processes are inspected and no resource release is authorized.
Missing evidence, especially a partial helper pair, remains unauditable unknown.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from invocation_journal import audit_validation_attempted
from all_scanned_sdk_plan import plan as command_plan
from all_scanned_sdk_audit import settled_helpers
from all_scanned_sdk_paths import parse as parse_inputs


def require(value, message):
    if not value: raise ValueError(message)


def audit_failed(result, contract, *, raw_proxy_receipts):
    require(result.get('schema') == 'unison-all-scanned-sdk-worker/1'
            and result.get('complete') is False and type(result.get('failure')) is str
            and bool(result['failure']), 'original known failed worker result required')
    entries = result.get('invocations')
    require(type(entries) is list and len(entries) <= 4 and type(raw_proxy_receipts) is list
            and len(raw_proxy_receipts) == len(entries), 'exact bounded attempted prefix required')
    if not entries:
        require(result.get('phase') == 'PREPARING_NO_CALL', 'possible call cannot become zero-call preparation')
        return dict(functional_status='FAILED', attempted_cli_invocations=0, sdk_helpers_settled=0,
                    resource_release_authorized=False, aggregate_parent_fd_closure_proved=False)
    require(result.get('phase') == 'CALL_MAY_HAVE_STARTED', 'failed call phase differs')
    lifecycle = audit_validation_attempted(result)
    count = 0
    for index, (entry, raw) in enumerate(zip(entries, raw_proxy_receipts)):
        label, phase = ('stock', 'ox')[index // 2], ('baseline', 'validate')[index % 2]
        directory = Path(contract['workspace']) / label
        proposed = command_plan(contract['binaries'][label], contract['tool'], directory)[phase]
        require(entry['command'] == proposed['argv'] and entry['identity'] == dict(
            label=label, mode='validation', workers=3, directory=str(directory), stage=phase),
            'exact prefix command/order differs')
        outcome = entry['outcome']
        require(outcome['proxy'] == raw, 'raw proxy receipt binding differs')
        if raw['server_cleanup'] is not None:
            require(raw['server_cleanup'].get('group_cleanup_before_leader_reap') is True
                    and raw['server_cleanup'].get('other_group_members_absent_before_reap') is True,
                    'server retained group proof missing')
            flags = proposed['server_flags']; command = raw['server_command']
            require(type(command) is list and command[:2] == [proposed['argv'][0], '-server']
                    and command[-len(flags):] == flags, 'actual endpoint policy differs')
        log = '\n'.join(outcome[k] for k in ('stdout', 'stderr', 'supervisor_output'))
        if phase == 'baseline':
            require(not parse_inputs(log), 'baseline has contradictory possible helper input evidence')
        proof = settled_helpers(log, candidate_sha256=contract['source']['sha256'],
                                candidate_bytes=contract['source']['bytes'], phase=phase)
        count += proof['sdk_helpers']
    return dict(lifecycle, functional_status='FAILED', sdk_helpers_settled=count,
                resource_release_authorized=False, aggregate_parent_fd_closure_proved=False,
                scope='known attempted transport/helper prefix only; source/build authentication and actual worker/FD closure remain external')
