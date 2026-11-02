#!/usr/bin/env python3
"""Recompute every accepted vector's SDE/0-preserved digest from the bytes and
regions in out/vectors.json, independently of the OCaml code."""
import hashlib, json, pathlib, struct
out = pathlib.Path(__file__).resolve().parent / 'out'
doc = json.loads((out / 'vectors.json').read_text())
n = 0
for v in doc['vectors']:
    data = (out / v['file']).read_bytes()
    assert len(data) == v['size'] and hashlib.sha256(data).hexdigest() == v['sha256'], v['file']
    for profile, r in v['profiles'].items():
        if 'refused' in r:
            continue
        regions = r['regions']
        h = hashlib.sha256(b'SDE/0-preserved\0' + struct.pack('>QQ', len(data), len(regions)))
        for off, ln in regions:
            h.update(struct.pack('>QQ', off, ln))
        pos = 0
        for off, ln in regions + [[len(data), 0]]:
            h.update(struct.pack('>QQ', pos, off - pos) + data[pos:off]); pos = off + ln
        assert h.hexdigest() == r['preserved_digest'], (v['file'], profile); n += 1
print('ok %d digests over %d vectors' % (n, len(doc['vectors'])))
