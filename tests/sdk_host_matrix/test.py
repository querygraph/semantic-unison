#!/usr/bin/env python3
"""Deterministic plan/protocol controls; no SDK or native child invoked."""
import json
import pathlib
import tempfile
import plan


def denied(function):
    try:
        function()
    except ValueError:
        return
    raise RuntimeError('invalid input accepted')


reference = {'executable': '/unused/reference', 'build_id': 'REFERENCE'}
experimental = {'executable': '/unused/experimental', 'build_id': 'EXPERIMENTAL'}
fixtures = [{'codec': codec, 'path': '/unused/' + codec, 'sha256': str(index) * 64,
             'size': 123 + index} for index, codec in enumerate(plan.CODECS)]
cases = plan.matrix(reference, experimental, fixtures, 1073741824)
plan.require(len(cases) == 12, 'matrix cardinality')
for index, case in enumerate(cases):
    command = case['command']
    plan.require(case['threads_including_caller'] == (1, 1, 6, 18)[index % 4], 'thread matrix')
    plan.require(command[-2:] == ['--', case['fixture']['path']], 'candidate argv')
    plan.require(('--host-memory-bytes' in command) == (case['backend'] == 'experimental'),
                 'reference protocol separation')
    fields = [('candidate-sha256', case['fixture']['sha256']),
              ('candidate-size', str(case['fixture']['size'])), ('driver-build', case['build_id']),
              ('structure', 'valid'), ('decode', 'success'), ('raw-digest', 'valid'),
              ('errors', '0'), ('warnings', '4')]
    def text(values):
        return 'UNISON-DNG-VALIDATION 1\n' + '\n'.join(k + ' ' + v for k, v in values) + '\nEND\n'
    result = plan.receipt(text(fields), case)
    plan.require(result['warnings'] == '4', 'positive receipt')
    for key, value in [('candidate-sha256', 'f' * 64), ('candidate-size', '0'),
                       ('driver-build', 'OTHER'), ('structure', 'invalid'),
                       ('decode', 'not_checked'), ('raw-digest', 'mismatch'),
                       ('errors', '1'), ('warnings', '-1'), ('warnings', '４')]:
        changed = [(k, value if k == key else v) for k, v in fields]
        denied(lambda: plan.receipt(text(changed), case))
    denied(lambda: plan.receipt(text(fields) + 'unframed trailer\n', case))
    denied(lambda: plan.receipt(text(fields[:-1] + [fields[-2]]), case))
for allowance in [0, -1, 2**63, True]:
    denied(lambda: plan.matrix(reference, experimental, fixtures, allowance))
for invalid in [fixtures[:2], fixtures + fixtures[:1], [fixtures[0]] * 3]:
    denied(lambda: plan.matrix(reference, experimental, invalid, 1024))
workspace = pathlib.Path(tempfile.mkdtemp(prefix='unison-sdk-host-plan-', dir='/private/tmp'))
receipt = {'scope': 'pure plan and receipt controls; zero SDK/native invocations',
           'cases': len(cases), 'receipt_denials': 132, 'matrix_denials': 7,
           'source_sha256': plan.sha(pathlib.Path(plan.__file__)),
           'test_sha256': plan.sha(__file__)}
(workspace / 'RESULT.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(workspace / 'RESULT.json')
