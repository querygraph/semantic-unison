#!/usr/bin/env python3
"""Live merge pilot: mock-only unless an exact fresh Root admission is supplied."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

import prepare_merged as prep
import prepare_live_merge as preparation
import live_merge_cases as cases
from live_merge_owner import Runner, write
from live_merge_aggregate import supervise

LIMITS = {'sdk_calls': 6, 'inputs': 3, 'logical_states': 12,
          'cpu_credits': 4, 'aggregate_seconds': 300}
SOURCES = ('tests/sdk_container_receive/run_live_merge.py',
           'tests/sdk_container_receive/live_merge_cases.py',
           'tests/sdk_container_receive/live_merge_owner.py',
           'tests/sdk_container_receive/live_merge_aggregate.py',
           'tests/sdk_container_receive/prepare_live_merge.py',
           'tests/sdk_container_receive/prepare_merged.py',
           'tests/validation_process/records.py', 'tests/validation_paths/run.py',
           'tests/sdk_host_matrix/plan.py', 'bench/sync/ownership.py', 'bench/sync/measure.py')


def sources():
    return {name: prep.pin(prep.ROOT / name)['sha256'] for name in SOURCES}


def validate(packet, mode):
    prep.require(packet['schema'] == 'unison-live-sdk-merge-preparation/1'
                 and packet['runtime_admitted'] is False and packet['proposed_limits'] == LIMITS,
                 'exact live preparation/limits required')
    prep.require(prep.pin(packet['preparer']['path']) == packet['preparer'], 'preparer changed')
    prep.require([item['kind'] for item in packet['builds']] == ['stock', 'ox'], 'stock/Ox pair required')
    for item in packet['builds']:
        prep.require(prep.pin(item['receipt']['path']) == item['receipt'], 'build receipt changed')
        build = preparation.checked_build(Path(item['receipt']['path']))
        prep.require(prep.pin(build['binary']) == item['binary'], 'build artifact changed')
    tool = packet['tool']
    prep.require(prep.pin(tool['executable'])['sha256'] == tool['sha256'], 'tool changed')
    if mode == 'native':
        prep.require(cases.host.tool(Path(tool['manifest']), False) == tool, 'qualified v1 tool required')
        # Native mode may not change tool or target provenance from the closed
        # frozen-byte SDK return. Mock overrides are deliberately ineligible.
        frozen = prep.checked(packet['frozen_preparation'])
        prep.require(frozen['tool'] == tool, 'native tool differs from frozen qualification')
        prep.require(prep.pin(packet['frozen_sdk_return']['path']) == packet['frozen_sdk_return'],
                     'frozen return changed')
        for case, accepted, origin in zip(packet['cases'], frozen['cases'], frozen['origins']):
            prep.require(case['codec'] == accepted['codec'] == origin['codec']
                         and case['original'] == origin['original']
                         and case['xmp_offset'] == origin['xmp_offset']
                         and case['xmp_size'] == origin['xmp_size'], 'native origin binding')
            prep.require(prep.pin(origin['original']['path']) == origin['original']
                         and prep.pin(accepted['candidate']['path']) == accepted['candidate'], 'native witness changed')
            variants = preparation.states(Path(origin['original']['path']).read_bytes(),
                Path(accepted['candidate']['path']).read_bytes(), origin['xmp_offset'], origin['xmp_size'])
            for state, data in variants.items():
                prep.require(case['states'][state]['sha256'] == prep.sha(data)
                             and case['states'][state]['bytes'] == len(data), 'native scalar state mismatch')

    else:
        prep.require(tool['build_id'].startswith('MOCK-'), 'mock refuses native tool')
    prep.require([item['codec'] for item in packet['cases']] == list(prep.CODECS), 'exact codec order')
    for case in packet['cases']:
        prep.require(list(case['states']) == ['base', 'left', 'right', 'target'], 'exact four states')
        for reference in case['states'].values():
            prep.require(prep.pin(reference['path']) == reference, 'frozen state changed')


def check_admission(admission, prepared, command, workspace):
    prep.require(admission['state'] == 'ROOT_ADMITTED_FINITE_UNISON_LIVE_MERGE_V1', 'fresh admission required')
    prep.require(admission['prepared'] == prep.pin(prepared) and admission['command'] == command
                 and admission['workspace'] == str(workspace) and admission['source_pins'] == sources()
                 and admission['limits'] == LIMITS, 'admission exact binding mismatch')
    prep.require(time.time() < admission['startDeadlineUnix'], 'admission expired')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--mode', choices=('mock', 'native'), required=True)
    parser.add_argument('--admission', type=Path)
    args = parser.parse_args()
    packet = json.loads(args.prepared.read_text())
    original_pin, source_pins = prep.pin(args.prepared), sources()
    validate(packet, args.mode)
    workspace = args.workspace.resolve()
    command = [sys.executable, *sys.argv]
    admission = None
    if args.mode == 'native':
        prep.require(args.admission is not None, 'fresh Root admission required')
        admission = json.loads(args.admission.read_text())
        check_admission(admission, args.prepared, command, workspace)
    workspace.mkdir(mode=0o700)
    write(workspace / 'WRAPPER-START.json', {'pid': os.getpid(), 'mode': args.mode,
          'prepared': original_pin, 'sources': source_pins,
          'admission': prep.pin(args.admission) if admission else None})

    def worker(deadline):
        prep.require(prep.pin(args.prepared) == original_pin and sources() == source_pins,
                     'executor/preparation changed')
        validate(packet, args.mode)
        if admission:
            check_admission(admission, args.prepared, command, workspace)
        runner = Runner(workspace, deadline)
        write(workspace / 'START.json', {'pid': os.getpid(), 'unix': time.time(), 'mode': args.mode})
        results = cases.run_cases(packet, workspace, runner.run_sync)
        # Recheck source/tool/input pins after the last real receive and no-op.
        validate(packet, args.mode)
        prep.require(sources() == source_pins, 'source changed during run')
        runner.accept_complete_proofs(results)
        write(workspace / 'RESULT.json', {'complete': True, 'mode': args.mode,
              'cli_runs': runner.calls, 'validation_calls': 6, 'results': results,
              'scope': 'exact generated scalar merge receiving only; no pixels/performance/Photo inference'})

    closure = supervise(worker, workspace, seconds=300, expected_helper_calls=6)
    print('Live merge matrix complete; aggregate', closure['pid'], 'reaped; mode', args.mode)


if __name__ == '__main__':
    main()
