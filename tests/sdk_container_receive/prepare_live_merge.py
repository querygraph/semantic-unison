#!/usr/bin/env python3
"""Freeze four scalar states per retained generated DNG; invokes no native tool."""
import argparse
import json
from pathlib import Path

import prepare_merged as prep


def checked_build(path):
    data = json.loads(path.read_text())
    prep.require(data['complete'] and data['build_exit'] == data['selftest_exit'] == 0,
                 'successful current build/selftests required')
    prep.require(prep.pin(data['binary'])['sha256'] == data['binary_sha256'], 'binary changed')
    for name, digest in data['source_sha256'].items():
        if name.startswith('src/'):
            prep.require(prep.pin(prep.ROOT / name)['sha256'] == digest, 'source changed: ' + name)
    return data


def states(original, target, offset, size):
    """Reverse only the two accepted fixed-width scalar attributes."""
    prep.require(type(offset) is int and type(size) is int and 0 <= offset
                 and 0 < size <= 1048576 and offset + size <= len(original), 'XMP extent')
    prep.require(len(original) == len(target) and original[:offset] == target[:offset]
                 and original[offset + size:] == target[offset + size:], 'protected bytes differ')
    packet = target[offset:offset + size]
    prep.require(packet.count(b'xmp:Rating="2"') == 1
                 and packet.count(b'xmp:Label="Gold"') == 1, 'accepted target scalar ambiguity')
    output = {}
    for state, rating, label in (('base', b'1', b'Blue'), ('left', b'2', b'Blue'),
                                 ('right', b'1', b'Gold'), ('target', b'2', b'Gold')):
        changed = packet.replace(b'xmp:Rating="2"', b'xmp:Rating="' + rating + b'"', 1)
        changed = changed.replace(b'xmp:Label="Gold"', b'xmp:Label="' + label + b'"', 1)
        prep.require(len(changed) == size, 'scalar geometry changed')
        output[state] = original[:offset] + changed + original[offset + size:]
    prep.require(output['target'] == target, 'target reconstruction differs')
    return output


def prepare(return_path, stock_path, ox_path, output):
    evidence = json.loads(return_path.read_text())
    prep.require(evidence['complete'] and evidence['schema'] == 'unison-merged-output-sdk-v2-actual-return/1'
                 and evidence['actual_terminal']['exit_code'] == 0
                 and evidence['actual_terminal']['running_session_returned'] is False
                 and evidence['unresolved_markers'] == [], 'closed frozen SDK return required')
    actual = evidence['actual_result']
    closure = evidence['actual_closure']
    prep.require(actual['mode'] == 'native' and actual['calls'] == 3
                 and [item['codec'] for item in actual['results']] == list(prep.CODECS)
                 and all(item['receipt']['structure'] == 'valid'
                         and item['receipt']['decode'] == 'success'
                         and item['receipt']['raw-digest'] == 'valid'
                         and item['receipt']['errors'] == '0' for item in actual['results']),
                 'three successful frozen SDK receipts required')
    prep.require(closure['closed'] and closure['reaped'] and closure['other_members_absent']
                 and closure['returncode'] == 0 and not closure['timed_out'], 'SDK aggregate not closed')
    for reference in evidence['artifacts']:
        prep.require(prep.pin(reference['path']) == reference, 'frozen runtime evidence changed')
    packet = prep.checked(evidence['prepared'])
    builds = [checked_build(path) for path in (stock_path, ox_path)]
    prep.require([case['codec'] for case in packet['cases']] == list(prep.CODECS), 'three codecs required')
    origins = {item['codec']: item for item in packet['origins']}
    # Read and validate all witnesses before claiming a new workspace.
    cases = []
    for case in packet['cases']:
        origin = origins[case['codec']]
        prep.require(prep.pin(origin['original']['path']) == origin['original'], 'original changed')
        prep.require(prep.pin(case['candidate']['path']) == case['candidate'], 'accepted target changed')
        original = Path(origin['original']['path']).read_bytes()
        target = Path(case['candidate']['path']).read_bytes()
        cases.append((case['codec'], origin, states(original, target, origin['xmp_offset'], origin['xmp_size'])))
    output.mkdir(mode=0o700)
    result = []
    for codec, origin, variants in cases:
        frozen = {}
        for state, data in variants.items():
            path = output / (codec + '-' + state + '.dng')
            with path.open('xb') as stream:
                stream.write(data)
            path.chmod(0o400)
            frozen[state] = prep.pin(path)
        result.append({'codec': codec, 'original': origin['original'], 'xmp_offset': origin['xmp_offset'],
                       'xmp_size': origin['xmp_size'], 'states': frozen})
    prepared = {'schema': 'unison-live-sdk-merge-preparation/1', 'runtime_admitted': False,
                'proposed_limits': {'sdk_calls': 6, 'inputs': 3, 'logical_states': 12,
                                    'cpu_credits': 4, 'aggregate_seconds': 300},
                'frozen_sdk_return': prep.pin(return_path), 'frozen_preparation': evidence['prepared'],
                'preparer': prep.pin(__file__), 'tool': packet['tool'],
                'builds': [{'kind': kind, 'receipt': prep.pin(path), 'binary': prep.pin(build['binary'])}
                           for kind, path, build in zip(('stock', 'ox'), (stock_path, ox_path), builds)],
                'cases': result, 'scope': 'Preparation only: retained generated bytes, no SDK/Photo/native execution. No runtime command or admission supplied.'}
    with (output / 'PREPARED.json').open('x') as stream:
        json.dump(prepared, stream, indent=2)
        stream.write('\n')
    return prepared


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen-return', type=Path, required=True)
    parser.add_argument('--stock-build', type=Path, required=True)
    parser.add_argument('--ox-build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.frozen_return.resolve(), args.stock_build.resolve(), args.ox_build.resolve(), args.output.resolve())
    print('Prepared twelve scalar states; runtime unadmitted; no native invocation')
