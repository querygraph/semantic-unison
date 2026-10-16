#!/usr/bin/env python3
"""Finite SDK comparison executor; native mode requires fresh pinned admission."""
import argparse
import json
import os
import pathlib
import sys
import time

import plan
sys.path.insert(0, str(plan.ROOT / 'bench/adobe'))
from phase import supervise, invoke_contained


def write(path, value):
    with path.open('x') as output:
        json.dump(value, output, indent=2)
        output.write('\n')


def validate(packet, mode):
    plan.require(packet['schema'] == 'unison-sdk-host-matrix-plan/1'
                 and packet['limits'] == plan.LIMITS, 'matrix schema/limits')
    plan.require(packet['source_pins'] == {name: plan.sha(plan.ROOT / name)
                                          for name in plan.SOURCES}, 'executor sources changed')
    reference, experimental = packet['tools']
    for index, record in enumerate(packet['tools']):
        if mode == 'native':
            plan.require(plan.tool(pathlib.Path(record['manifest']), bool(index)) == record,
                         'tool manifest changed')
        else:
            plan.require(record['build_id'].startswith('MOCK-'), 'mock mode refuses native tools')
        plan.require(plan.sha(record['executable']) == record['sha256'], 'executable changed')
    fixtures = [case['fixture'] for case in packet['cases'] if case['backend'] == 'reference']
    plan.require(packet['cases'] == plan.matrix(reference, experimental, fixtures,
                                              packet['host_memory_bytes']), 'noncanonical commands')
    for fixture in fixtures:
        path = pathlib.Path(fixture['path'])
        plan.require(path.is_file() and path.stat().st_size == fixture['size']
                     and plan.sha(path) == fixture['sha256'], 'input changed')


def admission_check(admission, path, command):
    plan.require(admission['state'] == 'ROOT_ADMITTED_FINITE_UNISON_HOST_MATRIX_V1',
                 'fresh host-matrix admission required')
    plan.require(admission['plan'] == {'path': str(path.resolve()), 'sha256': plan.sha(path)},
                 'admitted plan mismatch')
    plan.require(admission['command'] == command and admission['limits'] == plan.LIMITS,
                 'admitted command/limits mismatch')
    plan.require(time.time() < admission['startDeadlineUnix'], 'admission expired')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=pathlib.Path, required=True)
    parser.add_argument('--workspace', type=pathlib.Path, required=True)
    parser.add_argument('--mode', choices=['mock', 'native'], required=True)
    parser.add_argument('--admission', type=pathlib.Path)
    args = parser.parse_args()
    packet = json.loads(args.plan.read_text())
    validate(packet, args.mode)
    admission = None
    if args.mode == 'native':
        plan.require(args.admission is not None, 'fresh admission required')
        admission = json.loads(args.admission.read_text())
        admission_check(admission, args.plan, [sys.executable, *sys.argv])
    work = args.workspace.resolve()
    # No reuse, even after a positively closed failure. An abandoned wrapper
    # start without aggregate closure requires owner investigation, not retry.
    work.mkdir(mode=0o700)
    write(work / 'WRAPPER-START.json', {'pid': os.getpid(), 'mode': args.mode,
          'plan_sha256': plan.sha(args.plan),
          'admission_sha256': plan.sha(args.admission) if admission else None})

    def phase():
        validate(packet, args.mode)
        if admission:
            admission_check(admission, args.plan, [sys.executable, *sys.argv])
        write(work / 'START.json', {'group': os.getpgrp(), 'unix': time.time(), 'mode': args.mode})
        print('START ' + str(work / 'START.json'), flush=True)
        references = {}
        results = []
        for index, case in enumerate(packet['cases'], 1):
            tool = packet['tools'][case['backend'] == 'experimental']
            fixture = case['fixture']
            plan.require(plan.sha(tool['executable']) == tool['sha256']
                         and plan.sha(fixture['path']) == fixture['sha256'], 'pre-call pin changed')
            write(work / ('ENTRY-%02d.json' % index), {'index': index, 'case': case,
                                                      'group': os.getpgrp()})
            started = time.monotonic()
            result = invoke_contained(case['command'], dict(os.environ), 60)
            result['seconds'] = time.monotonic() - started
            write(work / ('CALL-%02d.json' % index), result)
            plan.require(not result['timed_out'] and not result['capture_truncated']
                         and result['returncode'] == 0, 'child exit/deadline/capture failure')
            value = plan.receipt(result['stdout'], case)
            if case['backend'] == 'reference':
                references[case['codec']] = value
            plan.require(value == references[case['codec']], 'reference result differs')
            observations = (plan.telemetry(result['stderr'], case, packet['host_memory_bytes'])
                            if case['backend'] == 'experimental' else None)
            plan.require(plan.sha(tool['executable']) == tool['sha256']
                         and plan.sha(fixture['path']) == fixture['sha256'], 'post-call pin changed')
            results.append({'index': index, 'codec': case['codec'], 'backend': case['backend'],
                            'requested_threads': case['threads_including_caller'], 'receipt': value,
                            'observations': observations})
        write(work / 'RESULT.json', {'mode': args.mode, 'results': results,
                                     'calls': len(results), 'runtime_scaling_qualified': False})

    closure = supervise(phase, work, 300)
    write(work / 'SUPERVISOR-RETURN.json', {'wrapper_pid': os.getpid(), 'aggregate': closure,
          'scope': 'aggregate closed; parent terminal exit still requires owner tool receipt'})
    print('CLOSED ' + str(work), flush=True)


if __name__ == '__main__':
    main()
