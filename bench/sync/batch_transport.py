"""Bounded batch transport adapter over the qualified retained child owner.

Caller owns fresh admission, pinned command, EXIO/CPU and all peer/server audits.
CapturedStream retains its original chunks even after producing diagnostic text;
we publish those bytes, never reconstruct them from decoded/replacement text.
"""
import sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / 'tests'),
                str(Path(__file__).resolve().parents[2] / 'tests/sdk_host_matrix')]
from batch_child import start, audit_child as child
from batch_artifacts import publish, read
from batch_observations import capture as observe, read as read_observation


class Call:
    """Retainable live call handle; at most one finish attempt."""
    def __init__(self, pending, command, store, name):
        self.pending = pending
        self.command = command
        self.store = store
        self.name = name
        self.finished = False
        self.outcome = None
        self.record = None
        self.observation = None

    def finish(self, deadline):
        if self.finished: raise ValueError('batch call finish already attempted; no retry')
        self.finished = True
        # On uncertainty pending keeps the actual owner/captures/identities.
        # Do not convert that carrier to an ordinary failed prefix.
        self.outcome = self.pending.finish(deadline)
        refs = {}
        for stream, capture in zip(('stdout', 'stderr'), self.pending.capture_owners):
            if (capture.thread.is_alive() or capture.error is not None
                    or type(capture.total) is not int or capture.total > capture.limit):
                raise ValueError('incomplete batch capture refuses qualification')
            raw = b''.join(capture.chunks)
            if len(raw) != capture.total:
                raise ValueError('batch capture byte extent differs')
            refs[stream] = publish(self.store, self.name + '-' + stream, raw)
        metadata = {key: value for key, value in self.outcome.items() if key not in ('stdout', 'stderr')}
        self.observation = self.store.write(self.name+'-resources.json', observe(self.pending.owner))
        self.record = self.store.write(self.name + '-call.json', dict(
            schema='unison-batch-child/2', outcome=metadata, streams=refs, observation=self.observation,
            external_server_audit_required=True, resource_release_authorized=False))
        # Preserve failed child evidence first, then refuse functionality.
        child(self.outcome, self.command)
        return self.record


def launch(command, environment, *, pass_fds, store, name):
    import re
    if (type(command) is not list or not command or any(type(x) is not str for x in command)
            or type(name) is not str or re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,31}', name) is None):
        raise ValueError('exact command and bounded one-use call name required')
    return Call(start(command, environment, pass_fds=pass_fds, capture_limit=4*1048576),
                list(command), store, name)


def restore(store, pin, command):
    """Reconstruct diagnostic form for independent child/peer audits."""
    if (type(pin) is not dict or set(pin) != {'name', 'sha256', 'bytes'}
            or type(pin['bytes']) is not int or not 0 < pin['bytes'] <= 2 * 1048576):
        raise ValueError('exact bounded child metadata pin required')
    raw = store.read(pin['name'], expected_sha256=pin['sha256'])
    if len(raw) != pin['bytes']: raise ValueError('child metadata byte pin differs')
    value = store.read_json(pin['name'], expected_sha256=pin['sha256'])
    fields={'schema','outcome','streams','external_server_audit_required','resource_release_authorized'}
    if type(value) is dict and value.get('schema')=='unison-batch-child/2': fields.add('observation')
    if (type(value) is not dict or set(value) != fields
            or value['schema'] not in ('unison-batch-child/1','unison-batch-child/2')
            or value['external_server_audit_required'] is not True
            or value['resource_release_authorized'] is not False
            or type(value['outcome']) is not dict
            or type(value['streams']) is not dict or set(value['streams']) != {'stdout', 'stderr'}
            or {'stdout', 'stderr'}.intersection(value['outcome'])):
        raise ValueError('exact non-releasing batch child record required')
    outcome = dict(value['outcome'])
    for stream in ('stdout', 'stderr'):
        outcome[stream] = read(store, value['streams'][stream]).decode('utf8', 'replace')
    child(outcome, command)
    if value['schema']=='unison-batch-child/2':
        read_observation(store,value['observation'],outcome['client_cleanup']['pid'])
    return outcome
