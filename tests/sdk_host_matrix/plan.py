#!/usr/bin/env python3
"""Prepare a pinned SDK host comparison plan; never execute an SDK output."""
import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
CODECS = ('uncompressed', 'jpeg', 'jxl')
EXPERIMENTAL = 'unison-sdk171-2724-v3-area-memory-unqualified'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def tool(path, experimental):
    path = path.resolve()
    manifest = json.loads(path.read_text())
    executable = pathlib.Path(manifest['executable']).resolve()
    require(sha(executable) == manifest['executable_sha256'], 'tool pin mismatch')
    if experimental:
        require(manifest['build_id'] == EXPERIMENTAL, 'wrong experimental build')
        require(manifest['protocol'] == '--unison-dng-validation-area-memory-source-v0',
                'wrong experimental protocol')
        require(sha(ROOT / 'tools/adobe-validator/driver.cpp') == manifest['source_sha256'],
                'experimental driver changed')
        for name, digest in manifest['adapter_headers_sha256'].items():
            require(sha(ROOT / 'tools/adobe-validator' / name) == digest,
                    'experimental adapter changed')
    else:
        require(manifest['build_id'] == 'unison-sdk171-2724-v1-single', 'wrong reference build')
    return {'manifest': str(path), 'manifest_sha256': sha(path),
            'executable': str(executable), 'sha256': sha(executable),
            'build_id': manifest['build_id']}


def matrix(reference, experimental, fixtures, memory_bytes):
    require(type(memory_bytes) is int and 0 < memory_bytes <= 2**63 - 1,
            'invalid backing allocation allowance')
    require(len(fixtures) == 3 and {f['codec'] for f in fixtures} == set(CODECS),
            'exactly three distinct codec inputs required')
    cases = []
    for fixture in sorted(fixtures, key=lambda f: CODECS.index(f['codec'])):
        for threads in (0, 1, 6, 18):
            backend = experimental if threads else reference
            protocol = ('--unison-dng-validation-area-memory-source-v0' if threads
                        else '--unison-dng-validation-v1')
            command = [backend['executable'], protocol, '--expected-sha256',
                       fixture['sha256'], '--expected-size', str(fixture['size']),
                       '--threads', str(threads or 1)]
            if threads:
                command += ['--host-memory-bytes', str(memory_bytes)]
            command += ['--', fixture['path']]
            cases.append({'codec': fixture['codec'], 'backend': 'experimental' if threads else 'reference',
                          'threads_including_caller': threads or 1,
                          'build_id': backend['build_id'], 'fixture': fixture,
                          'command': command})
    return cases


def receipt(text, case):
    lines = text.splitlines()
    require(len(lines) == 10 and lines[0] == 'UNISON-DNG-VALIDATION 1'
            and lines[-1] == 'END', 'receipt framing')
    fields = dict(line.split(' ', 1) for line in lines[1:-1])
    require(set(fields) == {'candidate-sha256', 'candidate-size', 'driver-build',
                           'structure', 'decode', 'raw-digest', 'errors', 'warnings'},
            'receipt fields')
    require(fields['candidate-sha256'] == case['fixture']['sha256']
            and fields['candidate-size'] == str(case['fixture']['size'])
            and fields['driver-build'] == case['build_id'], 'receipt binding')
    require(fields['structure'] == 'valid' and fields['decode'] == 'success'
            and fields['raw-digest'] == 'valid' and fields['errors'] == '0',
            'validation finding')
    require(fields['warnings'].isascii() and fields['warnings'].isdecimal(), 'warning count')
    # The driver reports validation outcomes, not decoded pixels or task counts.
    return {key: fields[key] for key in ('structure', 'decode', 'raw-digest', 'errors', 'warnings')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-manifest', type=pathlib.Path, required=True)
    parser.add_argument('--experimental-manifest', type=pathlib.Path, required=True)
    parser.add_argument('--receive-ready', type=pathlib.Path, required=True)
    parser.add_argument('--host-memory-bytes', type=int, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    reference = tool(args.reference_manifest, False)
    experimental = tool(args.experimental_manifest, True)
    ready = json.loads(args.receive_ready.read_text())
    fixtures = []
    for record in ready['fixtures']:
        path = pathlib.Path(record['original']).resolve()
        require(sha(path) == record['original_sha256'], 'fixture changed')
        fixtures.append({'codec': record['codec'], 'path': str(path),
                         'sha256': sha(path), 'size': path.stat().st_size})
    plan = {'schema': 'unison-sdk-host-matrix-plan/1', 'native_release': False,
            'source_sha256': sha(__file__), 'tools': [reference, experimental],
            'limits': {'calls': 12, 'inputs': 3, 'logical_states': 12,
                       'sequential_calls': True, 'CPU_credits': 18, 'aggregate_seconds': 300},
            'cases': matrix(reference, experimental, fixtures, args.host_memory_bytes),
            'limits_of_proof': ['validation-result equivalence only', 'no decoded pixel equality',
                                'no actual task/thread count proof', 'not a throughput benchmark',
                                'host backing allocations only, not process RSS'],
            'execution': 'Not implemented here. Fresh Root admission and owned aggregate runner required.'}
    with args.output.open('x') as output:
        json.dump(plan, output, indent=2)
        output.write('\n')
    print(args.output)


if __name__ == '__main__':
    main()
