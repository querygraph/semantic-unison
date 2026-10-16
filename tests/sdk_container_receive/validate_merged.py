#!/usr/bin/env python3
"""Finite merged-output SDK validation; native use requires fresh Root admission."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import prepare_merged as prep
spec = importlib.util.spec_from_file_location('host_plan', prep.ROOT / 'tests/sdk_host_matrix/plan.py')
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
sys.path.insert(0, str(prep.ROOT / 'bench/adobe'))
from phase import supervise, invoke_contained

LIMITS = {'sdk_calls': 3, 'inputs': 3, 'logical_states': 3,
          'cpu_credits': 1, 'aggregate_seconds': 300}
SOURCES = ('tests/sdk_container_receive/validate_merged.py',
           'tests/sdk_container_receive/prepare_merged.py', 'tests/sdk_host_matrix/plan.py',
           'bench/adobe/phase.py', 'bench/sync/ownership.py', 'bench/sync/measure.py')


def source_pins():
    return {name: prep.pin(prep.ROOT / name)['sha256'] for name in SOURCES}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def validate(packet, mode):
    prep.require(packet['schema'] == 'unison-merged-output-sdk-preparation/1'
                 and packet['runtime_admitted'] is False and packet['proposed_limits'] == LIMITS,
                 'preparation schema/limits')
    for name in ('preparer', 'tool_manifest_reader'):
        reference = packet[name]
        prep.require(prep.pin(reference['path']) == reference, 'preparation source changed')
    tool = packet['tool']
    if mode == 'native':
        prep.require(host.tool(Path(tool['manifest']), False) == tool, 'qualified tool changed')
    else:
        prep.require(tool['build_id'].startswith('MOCK-'), 'mock refuses native tool')
    prep.require(prep.pin(tool['executable'])['sha256'] == tool['sha256'], 'tool changed')
    prep.require([case['codec'] for case in packet['cases']] == list(prep.CODECS),
                 'exact three codecs required')
    for case in packet['cases']:
        candidate = case['candidate']
        prep.require(prep.pin(candidate['path']) == candidate, 'candidate changed')
        command = [tool['executable'], '--unison-dng-validation-v1', '--expected-sha256',
                   candidate['sha256'], '--expected-size', str(candidate['bytes']),
                   '--threads', '1', '--', candidate['path']]
        prep.require(case['command'] == command, 'noncanonical command')


def admission_check(admission, prepared, command):
    prep.require(admission['state'] == 'ROOT_ADMITTED_FINITE_UNISON_MERGED_OUTPUT_V1',
                 'fresh merged-output admission required')
    prep.require(admission['prepared'] == prep.pin(prepared)
                 and admission['command'] == command and admission['limits'] == LIMITS
                 and admission['source_pins'] == source_pins(), 'admission binding mismatch')
    prep.require(time.time() < admission['startDeadlineUnix'], 'admission expired')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--mode', choices=('mock', 'native'), required=True)
    parser.add_argument('--admission', type=Path)
    args = parser.parse_args()
    packet = json.loads(args.prepared.read_text())
    prepared_pin, sources = prep.pin(args.prepared), source_pins()
    validate(packet, args.mode)
    admission = None
    command = [sys.executable, *sys.argv]
    if args.mode == 'native':
        prep.require(args.admission is not None, 'fresh admission required')
        admission = json.loads(args.admission.read_text())
        admission_check(admission, args.prepared, command)
    work = args.workspace.resolve()
    work.mkdir(mode=0o700)
    write(work / 'WRAPPER-START.json', {'pid': os.getpid(), 'mode': args.mode,
          'prepared': prepared_pin, 'source_pins': sources,
          'admission': prep.pin(args.admission) if admission else None})

    def phase():
        prep.require(prep.pin(args.prepared) == prepared_pin and source_pins() == sources,
                     'executor/preparation changed')
        validate(packet, args.mode)
        if admission:
            admission_check(admission, args.prepared, command)
        write(work / 'START.json', {'unix': time.time(), 'group': os.getpgrp()})
        print('START ' + str(work / 'START.json'), flush=True)
        results = []
        for index, case in enumerate(packet['cases'], 1):
            validate(packet, args.mode)
            write(work / ('ENTRY-%02d.json' % index),
                  {'index': index, 'group': os.getpgrp(), 'case': case})
            result = invoke_contained(case['command'], dict(os.environ), 60)
            write(work / ('CALL-%02d.json' % index), result)
            prep.require(result['returncode'] == 0 and not result['timed_out']
                         and not result['capture_truncated'], 'child exit/deadline/capture failure')
            candidate = case['candidate']
            receipt = host.receipt(result['stdout'],
                       {'fixture': {'sha256': candidate['sha256'], 'size': candidate['bytes']},
                        'build_id': packet['tool']['build_id']})
            # These retained synthetic originals had four CFA padding warnings.
            # Any changed warning count needs review, even with successful decode.
            prep.require(receipt['warnings'] == '4', 'warning count changed')
            validate(packet, args.mode)
            results.append({'codec': case['codec'], 'receipt': receipt})
        prep.require(source_pins() == sources and prep.pin(args.prepared) == prepared_pin,
                     'source/preparation changed during phase')
        write(work / 'RESULT.json', {'calls': len(results), 'results': results,
              'mode': args.mode, 'scope': 'merged synthetic bytes SDK acceptance only; '
              'not production receiving-path, pixels, performance or preview qualification'})

    closure = supervise(phase, work, 300)
    write(work / 'SUPERVISOR-RETURN.json', {'wrapper_pid': os.getpid(), 'aggregate': closure,
          'scope': 'aggregate closure only; owner must retain actual parent tool terminal'})
    print('CLOSED ' + str(work), flush=True)


if __name__ == '__main__':
    main()
