#!/usr/bin/env python3
"""Pure scalar-state and negative framing fixtures; no subprocess or SDK."""
import prepare_live_merge as live

packet = b'<x xmp:Rating="2" xmp:Label="Gold"/>'
original = b'HEADER' + b' ' * len(packet) + b'PAYLOAD'
target = b'HEADER' + packet + b'PAYLOAD'
variants = live.states(original, target, 6, len(packet))
assert list(variants) == ['base', 'left', 'right', 'target']
assert len({value for value in variants.values()}) == 4
assert all(value[:6] == b'HEADER' and value[-7:] == b'PAYLOAD' and len(value) == len(original)
           for value in variants.values())
assert b'Rating="1"' in variants['base'] and b'Label="Blue"' in variants['base']
assert variants['target'] == target
bad = [(original, b'X' + target[1:], 6, len(packet)),
       (original, target + b'!', 6, len(packet)),
       (original, target, -1, len(packet)),
       (original, target, True, len(packet)),
       (original, target, 6, 0),
       (original, target, 6, len(target)),
       (original, target.replace(b'Rating="2"', b'Rating="3"'), 6, len(packet)),
       (original, target.replace(b'Label="Gold"', b'Label="Blue"'), 6, len(packet))]
for args in bad:
    try:
        live.states(*args)
    except ValueError:
        pass
    else:
        raise AssertionError('accepted invalid scalar witness')
print('PASS four immutable scalar-state geometries and', len(bad), 'negative fixtures; no native tool')
