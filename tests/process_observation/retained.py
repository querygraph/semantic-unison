"""Bounded synchronous observations while the calling thread retains a child.

The query adapter must separately own/settle any probe process it creates.
This component neither reaps children nor authorizes resource release.
"""
import threading
import time


class RetainedSamples:
    def __init__(self, owner, query, *, limit=128, clock=time.monotonic_ns):
        if type(limit) is not int or not 1 <= limit <= 1024:
            raise ValueError('bounded sample count required')
        if owner.reaped or type(owner.pid) is not int or owner.pid <= 0:
            raise ValueError('unreaped owned child required')
        self.owner, self.pid, self.query = owner, owner.pid, query
        self.limit, self.clock = limit, clock
        self.thread = threading.get_ident()
        self.samples = []

    def sample(self):
        # The owner loop must stay synchronous: no reaper thread can invalidate
        # the reservation between the guard and query. Do not accept raw PIDs.
        if threading.get_ident() != self.thread:
            raise RuntimeError('observation belongs to the retained owner thread')
        if self.owner.reaped or self.owner.pid != self.pid:
            raise RuntimeError('child reservation no longer held')
        if len(self.samples) >= self.limit or self.owner.terminal():
            return False
        before = self.clock()
        # Query/ownership exceptions deliberately propagate. In particular, an
        # unresolved probe must not be converted into an ordinary missing sample.
        value = self.query(self.pid)
        after = self.clock()
        if self.owner.reaped or self.owner.pid != self.pid:
            raise RuntimeError('query violated retained-child ownership')
        if type(before) is not int or type(after) is not int or after < before:
            raise ValueError('monotonic query bracket required')
        if type(value) is not dict or value.get('pid') != self.pid or type(value.get('available')) is not bool:
            raise ValueError('typed PID-bound observation required')
        if value['available']:
            fields = ('resident_bytes', 'virtual_bytes', 'threads', 'running_threads',
                      'total_user_native_units', 'total_system_native_units')
            if any(type(value.get(k)) is not int or value[k] < 0 for k in fields):
                raise ValueError('nonnegative typed OS counters required')
            if value['threads'] < 1 or value['running_threads'] > value['threads']:
                raise ValueError('OS thread counters inconsistent')
            observation = {k: value[k] for k in fields}
            observation.update(pid=self.pid, available=True)
        else:
            # Missing stays missing; no synthetic zero counters or peak claim.
            observation = dict(pid=self.pid, available=False)
        self.samples.append(dict(before_monotonic_ns=before, after_monotonic_ns=after,
                                 observation=observation))
        return True

    def report(self):
        return dict(pid=self.pid, samples=list(self.samples), sample_limit=self.limit,
                    process_settlement_proved=False, resource_release_authorized=False,
                    scope='sampled per-process OS counters; not peaks, tree totals or hard caps')
