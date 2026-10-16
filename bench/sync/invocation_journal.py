"""Persist call intent and returned evidence before caller-side verification.

An intent without an outcome is unknown, never evidence of no execution or
process settlement. Outcomes contain evidence; this journal does not audit it.
"""
import copy


def audit_attempted(result):
    """Audit a journal prefix's lifecycle, independently of functional success.

    This does not prove the aggregate owner exited, authenticate a receipt, or
    release any FD. Only the exact shared loopback configuration is supported.
    Missing client/server evidence (including failures before server creation)
    remains unknown rather than being interpreted as a no-start proof.
    """
    def require(value, message):
        if not value:
            raise ValueError(message)
    entries = result.get('invocations')
    require(type(entries) is list and 0 < len(entries) <= 54, 'bounded nonempty journal required')
    seen = {}
    for index, entry in enumerate(entries):
        require(type(entry['index']) is int and entry['index'] == index
                and entry['state'] == 'OUTCOME', 'unknown or reordered invocation')
        identity = entry['identity']
        require(identity['label'] in ('stock', 'ox')
                and identity['mode'] in ('ordinary', 'receiver-clone', 'semantic')
                and type(identity['workers']) is int and identity['workers'] in (1, 2, 3),
                'unexpected invocation configuration')
        key = identity['directory']
        require(type(key) is str and key, 'invocation directory missing')
        previous = seen.setdefault(key, [])
        require(identity['stage'] == ('seed', 'update', 'noop')[len(previous)]
                if len(previous) < 3 else False, 'duplicate or unordered stage')
        configuration = (identity['label'], identity['mode'], identity['workers'])
        require(not previous or previous[0] == configuration, 'directory configuration changed')
        previous.append(configuration)
        run = entry['outcome']
        require(type(entry['command']) is list and entry['command']
                and all(type(arg) is str for arg in entry['command'])
                and run['command'] == entry['command'], 'call command binding differs')
        require(type(run['returncode']) is int
                and run['capture_truncated'] is False
                and run['supervisor_capture_truncated'] is False, 'incomplete call capture')
        for name in ('client_cleanup', 'supervisor_cleanup'):
            owner = run[name]
            require(type(owner['pid']) is int and owner['pid'] > 0
                    and type(owner['returncode']) is int and owner['reaped'] is True
                    and owner['group_cleanup_before_leader_reap'] is True
                    and owner['other_group_members_absent_before_reap'] is True,
                    'call owner group unsettled')
        require(run['client_cleanup']['returncode'] == run['returncode'], 'client exit differs')
        proxy = run['proxy']
        server = proxy['server_cleanup']
        require(type(server['pid']) is int and server['pid'] > 0
                and server['reaped'] is True and type(server['returncode']) is int
                and proxy['server_pid'] == server['pid']
                and proxy['server_returncode'] == server['returncode']
                and proxy['input_pump_joined'] is True
                and proxy['server_command'][0] == entry['command'][0],
                'server or pump settlement missing')
    return {'attempted_cli_invocations': len(entries),
            'all_attempted_client_server_supervisor_settled': True,
            'functional_success_inferred': False,
            'scope': 'journal-prefix lifecycle only; not aggregate or parent terminal'}


class Journal:
    def __init__(self, result, persist):
        self.result = result
        self.persist = persist
        self.pending = None
        result['invocations'] = []

    def begin(self, identity, command):
        if self.pending is not None:
            raise RuntimeError('previous invocation outcome unknown')
        entry = {'index': len(self.result['invocations']),
                 'identity': dict(identity), 'command': list(command),
                 'state': 'INTENT', 'outcome': None}
        self.result['invocations'].append(entry)
        self.pending = entry
        # A failed persistence MUST prevent dispatch. Keep pending on failure.
        self.persist()

    def finish(self, outcome):
        if self.pending is None:
            raise RuntimeError('outcome has no invocation intent')
        self.pending['outcome'] = copy.deepcopy(outcome)
        self.pending['state'] = 'OUTCOME'
        self.persist()
        self.pending = None
