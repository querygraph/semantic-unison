"""Persist call intent and returned evidence before caller-side verification.

An intent without an outcome is unknown, never evidence of no execution or
process settlement. Outcomes contain evidence; this journal does not audit it.
"""
import copy


def audit_no_server_creation(run):
    """Consume a pinned proxy's complete pre-creation frame.

    Caller must separately audit client/supervisor identity, reap and groups;
    this helper alone proves neither those lifetimes nor aggregate closure.
    """
    proxy = run.get('proxy')
    if not (type(proxy) is dict
            and proxy.get('schema') == 'unison-loopback-protocol-count/1'
            and all(proxy.get(k, 'MISSING') is None for k in (
                'server_command', 'server_pid', 'server_returncode',
                'server_cleanup', 'server_resources', 'launcher_control_header_bytes_excluded'))
            and proxy.get('forwarded_protocol_bytes') == {
                'client_to_server_bytes': 0, 'server_to_client_bytes': 0}
            and proxy.get('input_pump_joined') is True
            and proxy.get('pump_errors') == []
            and type(proxy.get('fault')) is str and bool(proxy['fault'])
            and run.get('capture_truncated') is False
            and run.get('supervisor_capture_truncated') is False
            and run['supervisor_cleanup']['returncode'] == 70
            and type(run.get('returncode')) is int and run['returncode'] != 0):
        raise ValueError('server no-creation proof incomplete')


def audit_attempted(result):
    """Audit a journal prefix's lifecycle, independently of functional success.

    This does not prove the aggregate owner exited, authenticate a receipt, or
    release any FD. Only the exact shared loopback configuration is supported.
    Missing evidence remains unknown. A pinned proxy's explicit pre-creation
    state is the sole supported server-not-started proof, not null PID alone.
    """
    def require(value, message):
        if not value:
            raise ValueError(message)
    entries = result.get('invocations')
    require(type(entries) is list and 0 < len(entries) <= 54, 'bounded nonempty journal required')
    seen = {}
    never_created = 0
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
        require(len(previous) < 3, 'duplicate invocation after noop')
        require(identity['stage'] == ('seed', 'update', 'noop')[len(previous)],
                'duplicate or unordered stage')
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
        require(type(proxy) is dict and proxy.get('schema') == 'unison-loopback-protocol-count/1',
                'pinned proxy receipt schema required')
        server = proxy['server_cleanup']
        if server is None:
            # proxy.py assigns command BEFORE constructing NativeChild, so
            # null command + complete normal-finally receipt proves that the
            # creation line was never reached. The supervisor group proof
            # above is independently required even in this branch.
            audit_no_server_creation(run)
            never_created += 1
            continue
        require(type(server['pid']) is int and server['pid'] > 0
                and server['reaped'] is True and type(server['returncode']) is int
                and proxy['server_pid'] == server['pid']
                and proxy['server_returncode'] == server['returncode']
                and proxy['input_pump_joined'] is True
                and proxy['server_command'][0] == entry['command'][0],
                'server or pump settlement missing')
    return {'attempted_cli_invocations': len(entries),
            'server_not_created_invocations': never_created,
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
