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
telemetry_denials = 0
for case in cases[1:4]:
    n = case['threads_including_caller']
    area = ('tasks=0 started=0 finish=0 calls=0 active=0 peak=0 max-partition=0 reference=1'
            if n == 1 else 'tasks=2 started=2 finish=2 calls=%d active=0 peak=%d max-partition=%d reference=0'
            % (n * 2, n, n))
    text = ('unrelated SDK warning\nUNISON-HOST-AREA 1 ' + area
            + '\nUNISON-HOST-MEMORY 1 limit=1073741824 used=0 peak=4096 live=0 denied=0\n')
    observed = plan.telemetry(text, case, 1073741824)
    plan.require(observed['covered_allocator_bytes']['peak'] == 4096, 'telemetry positive')
    variants = [text.replace('UNISON-HOST-AREA', 'missing-area'),
                text.replace('UNISON-HOST-MEMORY', 'missing-memory'),
                text + text, text.replace('MEMORY 1', 'MEMORY 2'),
                text.replace('used=0', 'used=1'), text.replace('live=0', 'live=1'),
                text.replace('denied=0', 'denied=1'), text.replace('active=0', 'active=1'),
                text.replace('limit=1073741824', 'limit=1073741823'),
                text.replace('peak=4096', 'peak=0'),
                text.replace('peak=4096', 'peak=1073741825'),
                text.replace('used=0', 'used=-1'), text.replace('used=0', 'used=０'),
                text.replace('used=0', 'used=18446744073709551616'),
                text.replace('used=0', 'used=' + '0' * 513),
                text.replace('used=0', 'limit=0'),
                text.replace('UNISON-HOST-MEMORY 1', 'UNISON-HOST-MEMORY\t1'),
                text + 'UNISON-HOST-MEMORY unavailable\n']
    if n == 1:
        variants += [text.replace('reference=1', 'reference=0'), text.replace('tasks=0', 'tasks=1')]
    else:
        variants += [text.replace('finish=2', 'finish=1'), text.replace('reference=0', 'reference=1'),
                     text.replace('max-partition=%d' % n, 'max-partition=128')]
    for invalid in variants:
        denied(lambda: plan.telemetry(invalid, case, 1073741824))
        telemetry_denials += 1
workspace = pathlib.Path(tempfile.mkdtemp(prefix='unison-sdk-host-plan-', dir='/private/tmp'))
receipt = {'scope': 'pure plan and receipt controls; zero SDK/native invocations',
           'cases': len(cases), 'receipt_denials': 132, 'matrix_denials': 7,
           'telemetry_positives': 3, 'telemetry_denials': telemetry_denials,
           'source_sha256': plan.sha(pathlib.Path(plan.__file__)),
           'test_sha256': plan.sha(__file__)}
(workspace / 'RESULT.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(workspace / 'RESULT.json')
