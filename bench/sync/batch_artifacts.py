"""Bounded byte-exact evidence chunks over an existing qualified Store.

The caller owns Store and process settlement. This module neither closes it nor
supplies resource-release authority. Partial publication is preserved on error.
"""
import base64
import hashlib
import re

CHUNK_BYTES = 256 * 1024
MAX_BYTES = 4 * 1024 * 1024
MAX_CHUNKS = MAX_BYTES // CHUNK_BYTES


def publish(store, name, raw):
    if type(name) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,47}', name) is None:
        raise ValueError('bounded artifact name required')
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('complete bounded raw bytes required; overflow refuses')
    chunks = []
    for offset in range(0, len(raw), CHUNK_BYTES):
        block = raw[offset:offset + CHUNK_BYTES]
        chunks.append(store.write(f'{name}.{len(chunks):02d}.json', {
            'schema': 'unison-batch-byte-chunk/1',
            'base64': base64.b64encode(block).decode('ascii'),
        }))
    return dict(schema='unison-batch-byte-artifact/1', bytes=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(), chunks=chunks)


def read(store, reference):
    if (type(reference) is not dict or set(reference) != {'schema', 'bytes', 'sha256', 'chunks'}
            or reference['schema'] != 'unison-batch-byte-artifact/1'
            or type(reference['bytes']) is not int or not 0 <= reference['bytes'] <= MAX_BYTES
            or type(reference['sha256']) is not str
            or re.fullmatch('[0-9a-f]{64}', reference['sha256']) is None
            or type(reference['chunks']) is not list
            or len(reference['chunks']) != (reference['bytes'] + CHUNK_BYTES - 1) // CHUNK_BYTES):
        raise ValueError('exact bounded artifact reference required')
    raw = bytearray()
    names = set()
    for pin in reference['chunks']:
        if (type(pin) is not dict or set(pin) != {'name', 'sha256', 'bytes'}
                or type(pin['name']) is not str or pin['name'] in names
                or type(pin['bytes']) is not int or not 0 < pin['bytes'] <= 2 * CHUNK_BYTES):
            raise ValueError('distinct bounded chunk pin required')
        names.add(pin['name'])
        encoded = store.read(pin['name'], expected_sha256=pin['sha256'])
        if len(encoded) != pin['bytes']:
            raise ValueError('chunk byte pin differs')
        value = store.read_json(pin['name'], expected_sha256=pin['sha256'])
        if (type(value) is not dict or set(value) != {'schema', 'base64'}
                or value['schema'] != 'unison-batch-byte-chunk/1'
                or type(value['base64']) is not str):
            raise ValueError('exact byte chunk required')
        block = base64.b64decode(value['base64'], validate=True)
        expected = min(CHUNK_BYTES, reference['bytes'] - len(raw))
        if len(block) != expected:
            raise ValueError('chunk extent differs')
        raw.extend(block)
    if len(raw) != reference['bytes'] or hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('whole artifact pin differs')
    return bytes(raw)
