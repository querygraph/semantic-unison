"""Pure complete all-scanned call join; no resource-release authority.

Partial results intentionally require a separate conservative failed-prefix audit.
No helper absence inference, current path access or live process checks occur here.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from invocation_journal import audit_validation_attempted
from all_scanned_sdk_plan import plan as command_plan
from all_scanned_sdk_audit import successful_helpers
from all_scanned_sdk_paths import audit as audit_paths


def require(value, message):
    if not value:
        raise ValueError(message)


def audit_complete(result, contract, *, raw_proxy_receipts):
    require(result.get('schema') == 'unison-all-scanned-sdk-worker/1'
            and result.get('complete') is True and result.get('phase') == 'FINISHED'
            and 'failure' not in result, 'exact complete result only; partial work remains separate')
    entries = result.get('invocations')
    require(type(entries) is list and len(entries) == 4
            and type(raw_proxy_receipts) is list and len(raw_proxy_receipts) == 4,
            'four calls and independently read raw proxy frames required')
    lifecycle = audit_validation_attempted(result)
    helper_proofs = []
    pids = set()
    for index, (entry, raw) in enumerate(zip(entries, raw_proxy_receipts)):
        label = ('stock', 'ox')[index // 2]
        phase = ('baseline', 'validate')[index % 2]
        directory = Path(contract['workspace']) / label
        proposed = command_plan(contract['binaries'][label], contract['tool'], directory)
        expected = proposed[phase]['argv']
        require(entry['identity'] == dict(label=label, mode='validation', workers=3,
                                        directory=str(directory), stage=phase)
                and entry['command'] == expected, 'compiler/phase/namespace/argv binding differs')
        outcome = entry['outcome']
        require(outcome['proxy'] == raw, 'independent raw proxy frame differs')
        require(outcome['returncode'] == outcome['supervisor_cleanup']['returncode'] == 0
                and raw['server_returncode'] == 0 and raw.get('fault') is None
                and outcome.get('fault') is None and raw['pump_errors'] == []
                and outcome.get('timed_out') is False, 'complete result contradicts failed transport')
        server = raw['server_cleanup']
        require(server is not None and server.get('group_cleanup_before_leader_reap') is True
                and server.get('other_group_members_absent_before_reap') is True,
                'server retained group proof required')
        # Do not accept any other server executable or a remote policy different
        # from the client. The proxy's launcher command begins with -server;
        # startup flags before the exact explicit policy are separately retained.
        command = raw['server_command']; flags = proposed[phase]['server_flags']
        require(type(command) is list and command[:2] == [expected[0], '-server']
                and command[-len(flags):] == flags,
                'actual server command lacks the exact endpoint policy')
        log = '\n'.join(outcome[name] for name in ('stdout', 'stderr', 'supervisor_output'))
        helpers = successful_helpers(log, candidate_sha256=contract['source']['sha256'],
                                     candidate_bytes=contract['source']['bytes'], phase=phase)
        inputs = audit_paths(log, directory=directory, helpers=helpers, phase=phase,
                             endpoint_pids=dict(client=outcome['client_cleanup']['pid'],
                                                server=raw['server_pid']))
        if phase == 'validate':
            for helper in helpers['endpoints']:
                require(helper['pid'] not in pids, 'duplicate helper identity in complete matrix')
                pids.add(helper['pid'])
        message = ('Nothing to do: replicas have not changed since last sync.'
                   if phase == 'validate' else None)
        allowed = {message} if message else {
            'Nothing to do: replicas have not changed since last sync.',
            'Nothing to do: replicas have been changed only in identical ways since last sync.'}
        lines = (outcome['stdout'] + '\n' + outcome['stderr']).splitlines()
        require(sum(line in allowed for line in lines) == 1,
                'exact no-transfer UI branch status missing or duplicated')
        helper_proofs.append(dict(label=label, phase=phase, helpers=helpers, inputs=inputs,
                                  no_transfer_status_observed=True))
    return dict(lifecycle, functional_status='PASSED', helper_calls=4, calls=helper_proofs,
                candidate_path_isolation_proved=False, source_bytes_reverified=False,
                private_owner_contexts_observed=True, OS_argv_traced=False,
                aggregate_parent_fd_closure_proved=False, resource_release_authorized=False,
                scope='command-bound complete no-op/helper observations; caller must authenticate source/build, paths, bytes and owner closure')
