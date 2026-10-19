"""Bounded exact sample inventory, serialized via byte-artifact references.

Observations come from the owning runner, not this serializer. No filesystem
observation, process settlement or release authority is inferred from a record.
"""
import json
import re
from batch_artifacts import publish, read

MAX_FILES = 16384
FIELDS = {'path', 'before_present', 'before_sha256', 'target_sha256', 'target_bytes', 'expected_class'}
CLASSES = {'semantic-update', 'ordinary-fallback', 'new-file'}


def validate(rows, *, maximum_file_bytes=262144):
    if type(maximum_file_bytes) is not int or not 262144 <= maximum_file_bytes <= 2*1024**3+2*1048576:
        raise ValueError('trusted bounded file ceiling required')
    if type(rows) is not list or not 1 <= len(rows) <= MAX_FILES:
        raise ValueError('bounded nonempty sample inventory required')
    names = set()
    total = 0
    for row in rows:
        if type(row) is not dict or set(row) != FIELDS:
            raise ValueError('exact inventory fields required')
        name = row['path']
        if (type(name) is not str
                or re.fullmatch(r'group-[0-9]{3}/image-[0-9]{5}\.dng', name) is None
                or name in names):
            raise ValueError('unique generated relative path required')
        names.add(name)
        if type(row['before_present']) is not bool or row['expected_class'] not in CLASSES:
            raise ValueError('explicit presence and expected dispatch class required')
        new = row['expected_class'] == 'new-file'
        if new == row['before_present']:
            raise ValueError('new files must have absent receiver basis')
        before = row['before_sha256']
        target = row['target_sha256']
        if (type(target) is not str or re.fullmatch('[0-9a-f]{64}', target) is None
                or (new and before is not None)
                or (not new and (type(before) is not str
                    or re.fullmatch('[0-9a-f]{64}', before) is None or before == target))):
            raise ValueError('exact changed target and optional existing basis SHA required')
        size = row['target_bytes']
        if type(size) is not int or not 32768 <= size <= maximum_file_bytes:
            raise ValueError('bounded generated target extent required')
        total += size
    if total > 8 * 1024**3:
        raise ValueError('declared corpus extent exceeded')
    return rows


def save(store, name, rows):
    validate(rows)
    shards = []
    for offset in range(0, len(rows), 1024):
        raw = (json.dumps({'schema': 'unison-batch-inventory-shard/1',
                           'files': rows[offset:offset + 1024]},
                          sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
        shards.append(publish(store, f'{name}-{len(shards):02d}', raw))
    return dict(schema='unison-batch-inventory/1', count=len(rows), shards=shards)


def load(store, reference):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('duplicate inventory field')
            result[key] = value
        return result
    if (type(reference) is not dict or set(reference) != {'schema', 'count', 'shards'}
            or reference['schema'] != 'unison-batch-inventory/1'
            or type(reference['count']) is not int or not 1 <= reference['count'] <= MAX_FILES
            or type(reference['shards']) is not list
            or len(reference['shards']) != (reference['count'] + 1023) // 1024):
        raise ValueError('exact bounded inventory reference required')
    rows = []
    for shard in reference['shards']:
        value = json.loads(read(store, shard), object_pairs_hook=unique)
        if (type(value) is not dict or set(value) != {'schema', 'files'}
                or value['schema'] != 'unison-batch-inventory-shard/1'
                or type(value['files']) is not list
                or len(value['files']) != min(1024, reference['count'] - len(rows))):
            raise ValueError('exact inventory shard required')
        rows.extend(value['files'])
    return validate(rows)
