"""Persist call intent and returned evidence before caller-side verification.

An intent without an outcome is unknown, never evidence of no execution or
process settlement. Outcomes contain evidence; this journal does not audit it.
"""
import copy


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
