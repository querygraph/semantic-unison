#!/usr/bin/env python3
"""Freeze already-merged synthetic outputs for a future finite SDK check.

Preparation only: no validator, compiler, writer, Photo or Lightroom invocation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODECS = ('uncompressed', 'jpeg', 'jxl')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def checked(reference):
    path = Path(reference['path'])
    data = path.read_bytes()
    require(len(data) == reference['bytes'] and sha(data) == reference['sha256'],
            'changed evidence: ' + str(path))
    return json.loads(data)


def exact_packet_change(original, candidate, offset, size, expected):
    require(type(offset) is int and type(size) is int and 0 <= offset
            and 0 < size <= 1048576 and offset + size <= len(original),
            'invalid XMP extent')
    require(len(candidate) == len(original) and sha(candidate) == expected,
            'merged output size/hash mismatch')
    require(candidate[:offset] == original[:offset]
            and candidate[offset + size:] == original[offset + size:],
            'merged output changed protected bytes')
    require(candidate[offset:offset + size] != original[offset:offset + size],
            'XMP change not exercised')


def prepare(qualification, manifest, output):
    qualification = qualification.resolve()
    proof = json.loads(qualification.read_text())
    require(proof['schema'] == 'unison-current-quota-container-merge-qualification/1',
            'requires current quota merge evidence')
    for source in proof['source_pins']:
        checked_source = pin(source['path'])
        require(checked_source == source, 'merge source changed')
    runs = proof['runs']
    require([run['compiler'] for run in runs] == ['stock', 'ox'], 'both compilers required')
    reports = []
    for run in runs:
        require(run['terminal']['exit_code'] == 0
                and run['terminal']['running_session_returned'] is False, 'runner not closed')
        report = checked(run['report'])
        require(report == run['actual'], 'embedded merge evidence differs')
        require([(case['codec'], case['mode'], case['status']) for case in report['cases']]
                == [(codec, mode, 'passed') for codec in CODECS for mode in
                    ('disjoint', 'competing', 'protected-change', 'missing-base', 'partial-recovery')],
                'incomplete merge cases')
        build = checked(run['build_receipt'])
        binary = pin(run['binary']['path'])
        require(binary['bytes'] == run['binary']['bytes']
                and binary['sha256'] == run['binary']['sha256'] == build['binary_sha256'],
                'binary changed')
        for name, digest in build['source_sha256'].items():
            if name.startswith('src/'):
                require(pin(ROOT / name)['sha256'] == digest, 'production source changed')
        reports.append(report)
    require(reports[0]['inputs'] == reports[1]['inputs'], 'compiler input/target divergence')
    spec = importlib.util.spec_from_file_location('host_plan', ROOT / 'tests/sdk_host_matrix/plan.py')
    host = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(host)
    tool = host.tool(manifest.resolve(), False)
    # Validate all twelve live replica outputs and all originals before acquiring
    # a fresh output directory. No source output is modified.
    payloads = []
    origins = []
    for codec, source in zip(CODECS, reports[0]['inputs'], strict=True):
        original_path = Path(source['source'])
        original = original_path.read_bytes()
        require(sha(original) == source['source_sha256'], 'original changed')
        witnesses = []
        candidate = None
        for report in reports:
            for replica in ('left', 'right'):
                path = Path(report['workspace']) / (codec + '-disjoint') / replica / 'image.dng'
                data = path.read_bytes()
                exact_packet_change(original, data, source['xmp_offset'], source['xmp_size'],
                                    source['target_sha256'])
                witnesses.append(pin(path))
                require(candidate is None or candidate == data, 'replica output divergence')
                candidate = data
        payloads.append((codec, candidate))
        origins.append({'codec': codec, 'original': pin(original_path),
                        'xmp_offset': source['xmp_offset'], 'xmp_size': source['xmp_size'],
                        'replica_witnesses': witnesses})
    output = output.resolve()
    output.mkdir(mode=0o700)  # exclusive: failed/partial preparations are never reused
    cases = []
    for codec, data in payloads:
        path = output / (codec + '-merged.dng')
        with path.open('xb') as stream:
            stream.write(data)
        path.chmod(0o400)
        candidate = pin(path)
        require(candidate['sha256'] == sha(data), 'snapshot changed')
        cases.append({'codec': codec, 'candidate': candidate, 'command': [tool['executable'],
                      '--unison-dng-validation-v1', '--expected-sha256', candidate['sha256'],
                      '--expected-size', str(candidate['bytes']), '--threads', '1', '--', str(path)]})
    packet = {'schema': 'unison-merged-output-sdk-preparation/1',
              'runtime_admitted': False, 'qualification': pin(qualification), 'tool': tool,
              'preparer': pin(__file__), 'tool_manifest_reader': pin(host.__file__),
              'origins': origins, 'cases': cases,
              'proposed_limits': {'sdk_calls': 3, 'inputs': 3, 'logical_states': 3,
                                  'cpu_credits': 1, 'aggregate_seconds': 300},
              'scope': 'Frozen identical stock/Ox merged results only. No SDK execution, '
                       'native admission, production helper path or preview reuse qualification.'}
    with (output / 'PREPARED.json').open('x') as stream:
        json.dump(packet, stream, indent=2)
        stream.write('\n')
    return packet


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualification', type=Path, required=True)
    parser.add_argument('--reference-manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.qualification, args.reference_manifest, args.output_dir)
    print(args.output_dir.resolve() / 'PREPARED.json')
