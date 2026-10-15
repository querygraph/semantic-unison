#!/usr/bin/env python3
"""Freeze source-matched warm-cache sync measurement commands; executes none."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def build(path):
    value = json.loads(path.read_text())
    if not value['complete'] or value['build_exit'] != 0 or value['selftest_exit'] != 0:
        raise ValueError('completed successful build/selftests required')
    if pin(value['binary'])['sha256'] != value['binary_sha256']:
        raise ValueError('binary changed')
    if pin(value['compiler'])['sha256'] != value['compiler_sha256']:
        raise ValueError('compiler changed')
    if not value['source_sha256'] or 'src/semanticWorkers.ml' not in value['source_sha256']:
        raise ValueError('production source pins required')
    for name, digest in value['source_sha256'].items():
        if name.startswith('src/') and pin(ROOT / name)['sha256'] != digest:
            raise ValueError('source changed: ' + name)
    return value


def prepare(stock_receipt, ox_receipt, output_root):
    builds = [build(path) for path in (stock_receipt, ox_receipt)]
    commands = []
    # Each size is a separate complete measurement batch; never claim later
    # batches ran merely because the smaller batch passed. FourGiB corpus cap.
    for mib, files in ((32, 4), (128, 4), (512, 4), (2048, 2)):
        output = output_root / ('warm-%dMiB-%dfiles.json' % (mib, files))
        if output.exists():
            raise ValueError('measurement output already exists')
        command = [sys.executable, str(ROOT / 'bench/sync/run.py')]
        for label, item in zip(('stock', 'ox'), builds):
            command += ['--binary', label + '=' + item['binary'],
                        '--compiler', label + '=' + item['compiler']]
        command += ['--modes', 'ordinary,receiver-clone,semantic', '--workers', '1,6,8',
                    '--loopback-cpu-credits', '18', '--file-mib', str(mib), '--files', str(files),
                    '--packet-bytes', '8192', '--warmups', '1', '--repetitions', '5',
                    '--timeout', '180', '--background-note',
                    'planned coordinated warm-cache run; actual background activity must be recorded separately',
                    '--output', str(output)]
        commands.append({'file_mib': mib, 'files': files, 'corpus_bytes': mib * files * 1048576,
                         'capacity_model_bytes': 4 * mib * files * 1048576 + 64 * 1048576,
                         'configurations': 18, 'warmup_updates': 18, 'measured_updates': 90,
                         'expected_cli_invocations': 324, 'command': command})
    return {'schema': 'unison-warm-sync-measurement-plan/1', 'runtime_started': False,
            'cpu_reservation': False, 'requires_coordination': True,
            'build_receipts': [pin(path) for path in (stock_receipt, ox_receipt)],
            'binaries': [pin(item['binary']) for item in builds],
            'runner_sources': [pin(path) for path in sorted((ROOT / 'bench/sync').glob('*.py'))],
            'configured_endpoint_worker_maximum': 16, 'proposed_cpu_credits': 18,
            'commands': commands,
            'scope': 'warm/uncontrolled generated fixed-layout XMP loopback only; no cold-cache, real network, camera corpus, cross-volume or SDK evidence',
            'limitations': ['Loopback has two endpoints:8+8 configured workers, not18+18 on18 physical cores.',
                'Reserve18 credits for endpoints plus bridge/controller overhead; not OS hard CPU isolation.',
                'No debug primary-read counters in timing runs; their overhead is qualified separately.',
                'No baseline original/upstream or source-clone rows in this plan; those comparisons remain required.',
                'Per-process wait4 RSS is not aggregate tree RSS; logical counters are not physical APFS writes.',
                'The plan is not execution permission or a resource reservation.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-build', type=Path, required=True)
    p.add_argument('--ox-build', type=Path, required=True)
    p.add_argument('--output-root', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    a = p.parse_args()
    result = prepare(a.stock_build.resolve(), a.ox_build.resolve(), a.output_root.resolve())
    with a.plan.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Prepared four measurement batches; no command executed or CPU reserved')
