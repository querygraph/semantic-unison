#!/usr/bin/env python3
"""Deterministic preparation controls; no SDK processes or compiler jobs."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

spec = importlib.util.spec_from_file_location('prepare', Path(__file__).with_name('prepare_merged.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

original = b'protected-XMP-tail'
candidate = b'protected-NEW-tail'
m.exact_packet_change(original, candidate, 10, 3, m.sha(candidate))
checks = 1
for label, data, offset, size, digest in [
    ('protected prefix', b'Protected-NEW-tail', 10, 3, None),
    ('protected suffix', b'protected-NEW-Tail', 10, 3, None),
    ('length growth', candidate + b' ', 10, 3, None),
    ('wrong target', candidate, 10, 3, '0' * 64),
    ('unchanged packet', original, 10, 3, None),
    ('negative extent', candidate, -1, 3, None),
    ('empty extent', candidate, 10, 0, None),
    ('past EOF', candidate, 10, 100, None),
    ('noninteger extent', candidate, True, 3, None),
]:
    try:
        m.exact_packet_change(original, data, offset, size, digest or m.sha(data))
    except ValueError:
        checks += 1
    else:
        raise AssertionError(label)

# Stale evidence must reject before creating the proposed output directory.
with tempfile.TemporaryDirectory(prefix='unison-merged-preparation-controls-') as temp:
    work = Path(temp)
    source = work / 'source.json'
    source.write_text('{}')
    reference = m.pin(source)
    assert m.checked(reference) == {}
    checks += 1
    source.write_text('{"changed":true}')
    try:
        m.checked(reference)
    except ValueError:
        checks += 1
    else:
        raise AssertionError('changed receipt accepted')
    template = {'schema': 'unison-current-quota-container-merge-qualification/1',
                'source_pins': [], 'runs': []}
    for label, change in [('missing compilers', {}),
                          ('stale sources', {'source_pins': [reference]}),
                          ('wrong schema', {'schema': 'other'})]:
        proof = copy.deepcopy(template)
        proof.update(change)
        qualification = work / (label + '.json')
        qualification.write_text(json.dumps(proof))
        output = work / (label + '-output')
        try:
            m.prepare(qualification, work / 'absent-manifest', output)
        except ValueError:
            checks += 1
        else:
            raise AssertionError(label)
        assert not output.exists()
print('PASS', checks, 'merged-output preparation controls; no SDK invocation')
