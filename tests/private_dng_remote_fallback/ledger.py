"""Prepared remote-call ledger; receipt validation is not live process cleanup.

Every launch intent precedes dispatch. Missing/malformed settlement evidence
must retain the future owning coordinator and its grants, even after failure.
This module never signals, waits, acquires resources or launches anything.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'bench/sync'))
from invocation_journal import audit_no_server_creation

STAGES = ('seed', 'update', 'noop')


def require(value, reason):
    if not value:
        raise ValueError(reason)


def exclusive_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def begin(directory, stage, command):
    require(stage in STAGES, 'unknown remote stage')
    require(isinstance(command, list) and command and
            all(type(arg) is str for arg in command), 'exact command argv required')
    exclusive_json(Path(directory)/(stage+'-INTENT.json'),
                   {'stage': stage, 'command': command})


def record(directory, stage, outcome):
    require(stage in STAGES, 'unknown remote stage')
    intent = json.loads((Path(directory)/(stage+'-INTENT.json')).read_text())
    require(outcome.get('command') == intent['command'], 'outcome command differs from intent')
    exclusive_json(Path(directory)/(stage+'-OUTCOME.json'), outcome)


def settled(outcome):
    """Accept nonzero *settled* calls without converting them to test success."""
    for key in ('client_cleanup', 'supervisor_cleanup'):
        owner = outcome[key]
        require(type(owner['pid']) is int and owner['pid'] > 0 and
                owner['reaped'] is True and type(owner['returncode']) is int and
                owner['group_cleanup_before_leader_reap'] is True and
                owner['other_group_members_absent_before_reap'] is True,
                'direct group settlement missing')
    require(outcome['client_cleanup']['pid'] != outcome['supervisor_cleanup']['pid'],
            'client and supervisor identity collide')
    require(type(outcome['returncode']) is int and
            outcome['returncode'] == outcome['client_cleanup']['returncode'],
            'client wait binding differs')
    proxy = outcome['proxy']
    server = proxy['server_cleanup']
    if server is None:
        audit_no_server_creation(outcome)
        return {'client_pid': outcome['client_cleanup']['pid'],
                'supervisor_pid': outcome['supervisor_cleanup']['pid'],
                'server_pid': None, 'server_not_created': True, 'settled': True,
                'test_success_not_inferred': True}
    require(type(server['pid']) is int and server['pid'] > 0 and
            server['pid'] not in (outcome['client_cleanup']['pid'],
                                  outcome['supervisor_cleanup']['pid']) and
            server['reaped'] is True and type(server['returncode']) is int and
            proxy['server_pid'] == server['pid'] and
            type(proxy['server_returncode']) is int and
            proxy['server_returncode'] == server['returncode'] and
            proxy['input_pump_joined'] is True,
            'server wait or pump settlement missing')
    # Faults, cancellation and pump errors invalidate functional success, but
    # joined pumps plus actual waits can still establish resource settlement.
    return {'client_pid': outcome['client_cleanup']['pid'],
            'supervisor_pid': outcome['supervisor_cleanup']['pid'],
            'server_pid': server['pid'], 'settled': True,
            'test_success_not_inferred': True}


def audit_directory(directory):
    """Call only after the worker is stopped from starting any further calls.

    An outer owner must independently prove worker/group settlement. File
    receipts cannot establish that fact or authorize releasing its lock FDs.
    Empty means no recorded calls, NOT independently proved no native entry.
    """
    directory = Path(directory)
    intents = {p.name.removesuffix('-INTENT.json'): p
               for p in directory.glob('*-INTENT.json')}
    outcomes = {p.name.removesuffix('-OUTCOME.json'): p
                for p in directory.glob('*-OUTCOME.json')}
    require(set(intents) <= set(STAGES), 'unexpected intent stage')
    require(set(outcomes) == set(intents), 'pending intent or orphan outcome; retain owner')
    require(list(stage for stage in STAGES if stage in intents) ==
            list(STAGES[:len(intents)]), 'non-prefix remote stage ledger')
    rows = []
    for stage in STAGES:
        if stage not in intents:
            continue
        intent = json.loads(intents[stage].read_text())
        outcome = json.loads(outcomes[stage].read_text())
        require(intent['stage'] == stage and outcome['command'] == intent['command'],
                'ledger stage/command binding differs')
        rows.append(dict(stage=stage, **settled(outcome)))
    return rows
