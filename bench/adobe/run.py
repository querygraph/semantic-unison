#!/usr/bin/env python3
"""Benchmark the actual Adobe receive-validation core over cached synthetic DNGs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import tempfile
import time

from fixtures import generate, sha256

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    'src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
    'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
    'src/helperSupervisor_stubs.c', 'src/helperSupervisor.mli', 'src/helperSupervisor.ml',
    'src/semanticAdmission.mli', 'src/semanticAdmission.ml',
    'src/ioAdmission.mli', 'src/ioAdmission.ml',
    'src/semanticHash_stubs.c', 'src/semanticHash.mli', 'src/semanticHash.ml',
    'src/semanticFile_stubs.c', 'src/semanticFile.mli', 'src/semanticFile.ml',
    'src/formatExtension.mli', 'src/formatExtension.ml',
    'src/xmpObservation.mli', 'src/xmpObservation.ml',
    'src/dngSemantic.mli', 'src/dngSemantic.ml', 'src/semanticDelta.mli', 'src/semanticDelta.ml',
    'src/semanticWorkers.mli', 'src/semanticWorkers.ml', 'src/dngValidation.mli', 'src/dngValidation.ml',
    'bench/adobe/clock_stubs.c', 'bench/adobe/validation_bench.ml',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-build', type=Path, required=True)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--fixtures-dir', type=Path)
    parser.add_argument('--workers', default='1,18,36')
    parser.add_argument('--jobs', type=int, default=72)
    parser.add_argument('--repetitions', type=int, default=5)
    parser.add_argument('--control-repetitions', type=int, default=1)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--pilot', action='store_true', help='one validation per codec at one CPU permit')
    parser.add_argument('--start-file', type=Path, help='wait after compilation for a local measurement coordination file')
    parser.add_argument('--background-note', default='Ordinary system activity uncontrolled; no cache flush or CPU affinity.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    workers = [int(value) for value in args.workers.split(',')]
    if not workers or min(workers + [args.jobs, args.repetitions, args.control_repetitions, args.warmups]) < 1:
        parser.error('all counts must be positive')
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    compiler = str(Path(compiler).absolute())
    sdk = args.sdk_build.resolve()
    manifest = json.loads((sdk / 'build-manifest.json').read_text())
    driver = sdk / 'unison-adobe-validator'
    assert sha256(driver) == manifest['executable_sha256'] and manifest['threads'] == 1
    assert manifest['qualification'].startswith('passed '), 'use a qualified driver'
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    source_bytes = {name: (ROOT / name).read_bytes() for name in SOURCES}
    result = {
        'schema': 'unison-adobe-validation-core-v1', 'complete': False,
        'mode': 'pilot' if args.pilot else 'throughput',
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'host': dict(system=platform.system(), release=platform.release(), machine=platform.machine(), logical_cpus=os.cpu_count()),
        'scope': 'Cached synthetic CFA files; production shared validation/hash/helper/resource core, not full synchronization or Lightroom.',
        'background_activity': args.background_note,
        'compiler': dict(version=subprocess.check_output([compiler, '-version'], env=environment, text=True).strip(),
                         executable_sha256=sha256(Path(compiler)), flags=['-I', '+unix']),
        'driver': {key: manifest[key] for key in ('sdk', 'executable_sha256', 'build_id', 'source_sha256', 'threads', 'qualification')},
        'source_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in source_bytes.items()},
        'clock': dict(wall='CLOCK_MONOTONIC', parent_cpu='CLOCK_PROCESS_CPUTIME_ID', child_cpu='getrusage RUSAGE_CHILDREN after reap'),
        'parameters': dict(workers=workers, jobs=args.jobs, repetitions=args.repetitions,
                           control_repetitions=args.control_repetitions, warmups=args.warmups,
                           one_worker_warmup_jobs=1, peak_sampling_seconds=0.001),
        'samples': [], 'summary': [],
    }
    if platform.system() == 'Darwin':
        for key in ('hw.physicalcpu', 'hw.memsize'):
            query = subprocess.run(['sysctl', '-n', key], text=True, capture_output=True)
            result['host'][key] = int(query.stdout) if query.returncode == 0 else None

    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')

    with tempfile.TemporaryDirectory(prefix='unison-adobe-bench-') as temporary:
        work = Path(temporary)
        for name, data in source_bytes.items():
            (work / Path(name).name).write_bytes(data)
        with (work / 'build.log').open('w+') as log:
            try:
                for name in SOURCES[:-1]:
                    subprocess.run([compiler, '-I', '+unix', '-c', Path(name).name],
                                   cwd=work, env=environment, stdout=log, stderr=log, check=True)
                objects = [Path(name).stem + ('.o' if name.endswith('.c') else '.cmx')
                           for name in SOURCES[:-1] if name.endswith(('.ml', '.c'))]
                subprocess.run([compiler, '-I', '+unix', 'unix.cmxa', *objects,
                                'validation_bench.ml', '-o', 'validation-bench'],
                               cwd=work, env=environment, stdout=log, stderr=log, check=True)
            except subprocess.CalledProcessError:
                log.seek(0); print(log.read()); raise
        print('Built validation core with OCaml ' + result['compiler']['version'], flush=True)
        if args.build_only:
            print('Build-only check passed; no validation measurements taken.'); return
        fixtures_dir = args.fixtures_dir.resolve() if args.fixtures_dir else work / 'fixtures'
        if (fixtures_dir / 'fixtures.json').is_file():
            fixtures = json.loads((fixtures_dir / 'fixtures.json').read_text())
        else:
            fixtures = generate(sdk, fixtures_dir)
        for fixture in fixtures['fixtures']:
            path = fixtures_dir / fixture['filename']
            assert path.stat().st_size == fixture['size_bytes'] and sha256(path) == fixture['sha256']
            assert fixture['positive']['receipt']['driver-build'] == manifest['build_id']
        result['fixtures'] = fixtures
        configurations = [(fixture, worker) for fixture in fixtures['fixtures'] for worker in workers]
        save()
        if args.start_file:
            print('Benchmark prepared; waiting for local measurement coordination.', flush=True)
            while not args.start_file.is_file():
                time.sleep(0.2)
        result['measurement_started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        def batch(fixture, worker, jobs, phase, repetition):
            assert sha256(driver) == manifest['executable_sha256'], 'driver changed'
            print(f'Start {phase} {repetition}: {fixture["codec"]} permits={worker} jobs={jobs}', flush=True)
            command = [str(work / 'validation-bench'), str(fixtures_dir / fixture['filename']), fixture['sha256'],
                       str(fixture['size_bytes']), str(driver), manifest['executable_sha256'],
                       manifest['build_id'], str(worker), str(jobs)]
            output = subprocess.check_output(command, cwd=work, env=environment, text=True, timeout=1200)
            sample = json.loads(output)
            assert sample['correct_receipts'] == jobs and sample['final_cpu_permits'] == sample['final_children'] == 0
            sample.update(codec=fixture['codec'], cpu_permits=worker, jobs=jobs, phase=phase, repetition=repetition)
            sample['total_cpu_seconds'] = sample['parent_cpu_seconds'] + sample['child_cpu_seconds']
            sample['logical_cpu_equivalents'] = sample['total_cpu_seconds'] / sample['wall_seconds']
            sample['validations_per_second'] = jobs / sample['wall_seconds']
            sample['raw_megapixels_per_second'] = fixtures['specification']['width'] * fixtures['specification']['height'] / 1e6 * jobs / sample['wall_seconds']
            result['samples'].append(sample); save()
            print(f'{phase} {repetition}: {fixture["codec"]} permits={worker} '
                  f'{sample["wall_seconds"]:.2f}s {sample["validations_per_second"]:.2f} files/s '
                  f'CPU/wall={sample["logical_cpu_equivalents"]:.2f} children<={sample["peak_admitted_children"]}', flush=True)

        if args.pilot:
            for fixture in fixtures['fixtures']:
                batch(fixture, 1, 1, 'pilot', 1)
        else:
            for repetition in range(1, args.warmups + 1):
                for fixture, worker in configurations:
                    batch(fixture, worker, 1 if worker == 1 else args.jobs, 'warmup', repetition)
            for repetition in range(1, max(args.repetitions, args.control_repetitions) + 1):
                order = configurations if repetition % 2 else list(reversed(configurations))
                for fixture, worker in order:
                    maximum = args.control_repetitions if worker == 1 else args.repetitions
                    if repetition <= maximum:
                        batch(fixture, worker, args.jobs, 'measured', repetition)
            for fixture, worker in configurations:
                samples = [sample for sample in result['samples'] if sample['codec'] == fixture['codec'] and
                           sample['cpu_permits'] == worker and sample['phase'] == 'measured']
                summary = dict(codec=fixture['codec'], cpu_permits=worker, measured_samples=len(samples))
                for key in ('wall_seconds', 'parent_cpu_seconds', 'child_cpu_seconds', 'total_cpu_seconds',
                            'logical_cpu_equivalents', 'validations_per_second', 'raw_megapixels_per_second',
                            'peak_admitted_children'):
                    values = [sample[key] for sample in samples]
                    summary[key] = dict(median=statistics.median(values), min=min(values), max=max(values))
                summary['all_receipts_correct'] = all(sample['correct_receipts'] == args.jobs for sample in samples)
                result['summary'].append(summary)
        assert sha256(driver) == manifest['executable_sha256']
        result['complete'] = True; save()


if __name__ == '__main__':
    main()
