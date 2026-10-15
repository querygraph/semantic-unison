#!/usr/bin/env python3
"""Run one full measurement batch only under a fresh exact Root allocation."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import time

import prepare_plan
from batch_audit import audit
from partitions import COUNT, audit_part, specification

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/sdk_container_receive'))
from live_merge_aggregate import supervise
from live_merge_owner import write

SOURCES = ('bench/sync/run_bounded.py', 'bench/sync/batch_audit.py',
           'bench/sync/prepare_plan.py', 'bench/sync/run.py', 'bench/sync/fixtures.py',
           'bench/sync/partitions.py',
           'bench/sync/measure.py', 'bench/sync/ownership.py', 'bench/sync/proxy.py',
           'bench/sync/launcher.py', 'bench/sync/read_stats.py',
           'tests/sdk_container_receive/live_merge_aggregate.py',
           'tests/sdk_container_receive/live_merge_owner.py',
           'tests/sdk_container_receive/prepare_merged.py')


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def sources():
    return {name: pin(ROOT / name)['sha256'] for name in SOURCES}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def validate_plan(plan):
    require(plan['schema'] == 'unison-warm-sync-measurement-plan/1'
            and plan['runtime_started'] is False and plan['cpu_reservation'] is False, 'plan schema')
    for reference in plan['runner_sources'] + plan['build_receipts'] + plan['binaries']:
        require(pin(reference['path'])['sha256'] == reference['sha256'], 'stale plan pin: ' + reference['path'])
    for reference in plan['build_receipts']:
        prepare_plan.build(Path(reference['path']))


def check_allocation(allocation, plan_path, index, workspace, command, *, partition=None):
    state = ('ROOT_ALLOCATED_FINITE_SYNC_BATCH_V1' if partition is None
             else 'ROOT_ALLOCATED_FINITE_SYNC_PARTITION_V1')
    calls = 324 if partition is None else 54
    require(allocation['state'] == state, 'fresh explicit timing allocation required')
    if partition is not None:
        require(type(partition) is int and 0 <= partition < COUNT
                and type(allocation['partition_index']) is int
                and allocation['partition_index'] == partition, 'allocation partition differs')
    require(allocation['plan'] == pin(plan_path) and allocation['batch_index'] == index
            and allocation['workspace'] == str(workspace) and allocation['command'] == command
            and allocation['source_pins'] == sources(), 'allocation exact binding')
    require(allocation['limits'] == {'cpu_credits': 18, 'aggregate_seconds': 7200, 'cli_invocations': calls},
            'whole-batch limits differ')
    require(time.time() < allocation['startDeadlineUnix'], 'allocation expired')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--batch-index', type=int, default=0)
    p.add_argument('--partition', type=int)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--allocation', type=Path, required=True)
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    validate_plan(plan)
    require(0 <= args.batch_index < len(plan['commands']), 'batch index')
    row = plan['commands'][args.batch_index]
    require(row['expected_cli_invocations'] == 324, 'full matrix must remain intact')
    if args.partition is not None:
        require(0 <= args.partition < COUNT, 'partition index')
        row = row['partitions'][args.partition]
        require(row['partition'] == specification(args.partition)
                and row['expected_cli_invocations'] == 54, 'exact partition required')
    else:
        require(not row.get('duration_planning', {}).get('partition_review_needed', False),
                'large batch requires separately allocated bounded partitions')
    expected_calls = row['expected_cli_invocations']
    output = Path(row['command'][-1])
    require(not output.exists(), 'existing measurement output; no replay')
    allocation = json.loads(args.allocation.read_text())
    command = [sys.executable, *sys.argv]
    workspace = args.workspace.resolve()
    plan_pin, source_pins, allocation_pin = pin(args.plan), sources(), pin(args.allocation)
    check_allocation(allocation, args.plan, args.batch_index, workspace, command, partition=args.partition)
    workspace.mkdir(mode=0o700)
    write(workspace / 'WRAPPER-START.json', {'pid': __import__('os').getpid(), 'plan': plan_pin,
          'allocation': allocation_pin, 'source_pins': source_pins, 'batch_index': args.batch_index,
          'partition_index': args.partition})

    def worker(deadline):
        require(pin(args.plan) == plan_pin and pin(args.allocation) == allocation_pin
                and sources() == source_pins, 'controller inputs changed')
        validate_plan(plan)
        check_allocation(allocation, args.plan, args.batch_index, workspace, command, partition=args.partition)
        write(workspace / 'START.json', {'pid': __import__('os').getpid(), 'unix': time.time(),
              'aggregate_deadline_monotonic': deadline, 'batch_command': row['command']})
        # Shared aggregate owns this worker. Its signal handler propagates
        # ordinary cancellation through run.py's existing finally settlement;
        # interrupted direct-client receipts are now retained on the exception.
        sys.argv = row['command'][1:]
        runpy.run_path(str(ROOT / 'bench/sync/run.py'), run_name='__main__')
        result = json.loads(output.read_text())
        auditor = audit if args.partition is None else audit_part
        proof = auditor(result, {'file_mib': row['file_mib'], 'files': row['files'],
                                 'workers': [1, 6, 8], 'warmups': 1, 'repetitions': 5})
        require(proof['cli_invocations'] == expected_calls and sources() == source_pins,
                'batch proof/source changed')
        write(workspace / 'BATCH-PROOFS-COMPLETE.json', {'measurement': pin(output), 'proof': proof})

    closure = supervise(worker, workspace, seconds=7200, maximum_seconds=7200, expected_helper_calls=0)
    # No SDK/helper groups are allowed by these private measurement commands.
    # The aggregate receipt scopes its worker; this separate proof covers every
    # externally grouped client/supervisor and inherited native server.
    proof = json.loads((workspace / 'BATCH-PROOFS-COMPLETE.json').read_text())
    require(pin(output) == proof['measurement'], 'measurement changed after worker exit')
    write(workspace / 'BATCH-RETURN.json', {'aggregate': closure, 'proof': proof,
          'partition_index': args.partition,
          'scope': 'one allocated batch/partition only; no SDK/Photo/cold-cache or physical I/O proof'})
    print('Bounded measurement complete; aggregate reaped, all%d CLI/server settlements audited' % expected_calls)


if __name__ == '__main__':
    main()
