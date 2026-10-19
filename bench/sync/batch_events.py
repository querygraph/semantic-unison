"""One-use ordered sample events; large row sets become bounded shard refs."""
import json
from batch_artifacts import publish

STAGES = (('seed-intent', 'planned_files'), ('seed-inventory', 'files'),
          ('seed-verified', 'files'), ('update-inventory', 'files'),
          ('update-verified', 'observations'), ('noop-verified', 'observations'))


class Events:
    def __init__(self, store):
        self.store = store
        self.next = 0
        self.pins = []
        self.failed = False

    def __call__(self, event):
        if self.failed: raise ValueError('event publication failed; retain without successor')
        if self.next >= len(STAGES): raise ValueError('sample event set already consumed')
        stage, field = STAGES[self.next]
        if type(event) is not dict or set(event) != {'stage', field} or event['stage'] != stage:
            raise ValueError('exact ordered sample event required')
        value = event[field]
        large = stage in ('seed-inventory', 'update-inventory', 'update-verified', 'noop-verified')
        if large:
            if type(value) is not list or len(value) > 16384 or any(type(row) is not dict for row in value):
                raise ValueError('bounded event row objects required')
            for row in value:
                if len(json.dumps(row, allow_nan=False, separators=(',', ':')).encode()) > 2048:
                    raise ValueError('bounded event row required')
        elif type(value) is not int or not 0 <= value <= 16384:
            raise ValueError('typed bounded event count required')
        number = self.next
        self.next += 1  # Any attempted write consumes names, even on uncertainty.
        self.failed = True
        if large:
            refs = []
            for offset in range(0, len(value), 1024):
                raw = (json.dumps(value[offset:offset+1024], allow_nan=False,
                                  sort_keys=True, separators=(',', ':'))+'\n').encode()
                refs.append(publish(self.store, f'event-{number:02d}-{len(refs):02d}', raw))
            payload = dict(count=len(value), shards=refs)
        else: payload = value
        pin = self.store.write(f'event-{number:02d}.json', dict(
            schema='unison-batch-event/1', stage=stage, field=field, value=payload,
            resource_release_authorized=False))
        self.pins.append(pin)
        self.failed = False
        return pin
