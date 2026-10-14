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
from deadline import NativeDeadline

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    'src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
    'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
    'src/borrowedWork.mli', 'src/borrowedWork.ml',
    'src/helperSupervisor_stubs.c', 'src/helperSupervisor.mli', 'src/helperSupervisor.ml',
    'src/semanticAdmission.mli', 'src/semanticAdmission.ml',
    'src/ioAdmission.mli', 'src/ioAdmission.ml',
    'src/semanticMailbox.mli', 'src/semanticMailbox.ml',
    'src/semanticHash_stubs.c', 'src/semanticHash.mli', 'src/semanticHash.ml',
    'src/semanticFile_stubs.c', 'src/semanticFile.mli', 'src/semanticFile.ml',
    'src/formatRecognition.mli', 'src/formatRecognition.ml',
    'src/formatExtension.mli', 'src/formatExtension.ml',
    'src/xmpObservation.mli', 'src/xmpObservation.ml', 'src/xmpMerge.mli', 'src/xmpMerge.ml',
    'src/dngSemantic.mli', 'src/dngSemantic.ml', 'src/semanticDelta.mli', 'src/semanticDelta.ml',
    'src/semanticWorkers.mli', 'src/semanticWorkers.ml', 'src/dngValidation.mli', 'src/dngValidation.ml',
    'bench/adobe/clock_stubs.c', 'bench/adobe/validation_bench.ml',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-build', type=Path, required=True)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--fixtures-dir', type=Path)
    parser.add_argument('--workers', default='1,6,18')
    parser.add_argument('--cpu-credit-budget', type=int, default=18,
                        help='maximum configured shared CPU permits; coordinate this allowance before execution')
    parser.add_argument('--jobs', type=int, default=72)
    parser.add_argument('--repetitions', type=int, default=5)
    parser.add_argument('--control-repetitions', type=int, default=1)
    parser.add_argument('--warmups', type=int, default=1)
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--production-build', type=Path,
                        help='full Make snapshot whose compiler-matched core objects will be linked')
    parser.add_argument('--keep-work', action='store_true', help='retain frozen sources, executable and build log')
    parser.add_argument('--pilot', action='store_true', help='one validation per codec at one CPU permit')
    parser.add_argument('--start-file', type=Path, help='wait after compilation for a local measurement coordination file')
    parser.add_argument('--coordination-timeout', type=float, default=600,
                        help='maximum seconds waiting before any SDK fixture or validation invocation')
    parser.add_argument('--batch-deadline', type=float, default=300,
                        help='active validation batch cancellation deadline; cleanup follows before return')
    parser.add_argument('--background-note', default='Ordinary system activity uncontrolled; no cache flush or CPU affinity.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        workers = [int(value) for value in args.workers.split(',')]
    except ValueError:
        parser.error('workers must be comma-separated integers')
    if (not 1 <= args.cpu_credit_budget <= 128 or len(set(workers)) != len(workers)
            or any(value < 1 or value > args.cpu_credit_budget for value in workers)):
        parser.error('unique worker budgets must fit the configured CPU credit allowance')
    if not workers or min(workers + [args.jobs, args.repetitions, args.control_repetitions, args.warmups]) < 1:
        parser.error('all counts must be positive')
    if not 0 < args.coordination_timeout <= 3600:
        parser.error('coordination timeout must be positive and at most 3600 seconds')
    if not 0 < args.batch_deadline <= 3600:
        parser.error('batch deadline must be positive and at most 3600 seconds')
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    compiler = str(Path(compiler).absolute())
    version = subprocess.check_output([compiler, '-version'], text=True).strip()
    production = args.production_build.resolve() if args.production_build else None
    if '+ox' in version and production is None:
        parser.error('OxCaml benchmark requires --production-build from the qualified checked CLI build')
    if production is not None:
        receipt = json.loads((production / 'build-receipt.json').read_text())
        if (receipt['build_system'] != 'make' or receipt['build_exit'] != 0
                or receipt['compiler_sha256'] != sha256(Path(compiler))
                or receipt['binary_sha256'] != sha256(production/'src/unison')):
            parser.error('production snapshot/compiler/binary pins do not match')
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
        'runner_sha256': sha256(Path(__file__).resolve()),
        'fixture_generator_sha256': sha256(Path(__file__).with_name('fixtures.py')),
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

    import contextlib
    retain = True  # Keep unresolved native ownership evidence on every failure.
    temporary_workspace = tempfile.mkdtemp(prefix='unison-adobe-bench-') if retain else None
    with (contextlib.nullcontext(temporary_workspace) if retain else
          tempfile.TemporaryDirectory(prefix='unison-adobe-bench-')) as temporary:
        work = Path(temporary)
        result['build'] = {'workspace': str(work), 'retained': retain,
                           'production_snapshot': str(production) if production else None,
                           'production_receipt_sha256': sha256(production/'build-receipt.json') if production else None,
                           'complete': False, 'native_calls_during_build': False}
        result['parameters']['cpu_credit_budget'] = args.cpu_credit_budget
        save()
        for name, data in source_bytes.items():
            (work / Path(name).name).write_bytes(data)
        with (work / 'build.log').open('w+') as log:
            try:
                linked = {}
                for name in SOURCES[:-1]:
                    if production is not None and name.startswith('src/'):
                        actual = production/name
                        assert actual.read_bytes() == source_bytes[name], 'production source mismatch: '+name
                        extensions = ('.cmi', '.cmx', '.o') if name.endswith('.ml') else (('.cmi',) if name.endswith('.mli') else ('.o',))
                        for suffix in extensions:
                            artifact = actual.with_suffix(suffix)
                            shutil.copyfile(artifact, work/artifact.name)
                            linked[str(artifact)] = sha256(artifact)
                    else:
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
        result['build'] = {'workspace': str(work), 'retained': retain,
                           'production_snapshot': str(production) if production else None,
                           'linked_object_sha256': linked, 'binary_sha256': sha256(work/'validation-bench'),
                           'production_receipt_sha256': sha256(production/'build-receipt.json') if production else None,
                           'build_log_sha256': sha256(work/'build.log'), 'complete': True,
                           'native_calls_during_build': False}
        save()
        if args.build_only:
            print('Built executable:', work/'validation-bench')
            print('Build-only check passed; no validation measurements taken.'); return
        if args.start_file:
            result['coordination'] = {'path': str(args.start_file), 'deadline_seconds': args.coordination_timeout,
                                      'passed': False, 'scope': 'caller-owned CPU coordination; not Lightroom/native-owner admission'}
            save()
            print('Benchmark built; waiting before all SDK fixture/validation calls.', flush=True)
            deadline = time.monotonic() + args.coordination_timeout
            while not args.start_file.is_file():
                if time.monotonic() >= deadline:
                    result['coordination']['timed_out'] = True
                    save()
                    raise TimeoutError('SDK benchmark coordination deadline expired before native work')
                time.sleep(min(0.2, max(0., deadline-time.monotonic())))
            result['coordination']['passed'] = True
            save()
        native_owner = NativeDeadline(work, 300, max_calls=13 if args.pilot else None)
        fixtures_dir = args.fixtures_dir.resolve() if args.fixtures_dir else work / 'fixtures'
        if (fixtures_dir / 'fixtures.json').is_file():
            fixtures = json.loads((fixtures_dir / 'fixtures.json').read_text())
        else:
            fixtures = generate(sdk, fixtures_dir, invoke=native_owner.invoke)
        for fixture in fixtures['fixtures']:
            path = fixtures_dir / fixture['filename']
            assert path.stat().st_size == fixture['size_bytes'] and sha256(path) == fixture['sha256']
            assert fixture['positive']['receipt']['driver-build'] == manifest['build_id']
        result['fixtures'] = fixtures
        configurations = [(fixture, worker) for fixture in fixtures['fixtures'] for worker in workers]
        save()
        result['measurement_started_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        def batch(fixture, worker, jobs, phase, repetition):
            assert sha256(driver) == manifest['executable_sha256'], 'driver changed'
            print(f'Start {phase} {repetition}: {fixture["codec"]} permits={worker} jobs={jobs}', flush=True)
            command = [str(work / 'validation-bench'), str(fixtures_dir / fixture['filename']), fixture['sha256'],
                       str(fixture['size_bytes']), str(driver), manifest['executable_sha256'],
                       manifest['build_id'], str(worker), str(jobs), str(args.batch_deadline)]
            settlement = work / ('settlement-' + str(len(native_owner.calls)) + '.json')
            child = native_owner.invoke(command, env=environment, timeout=args.batch_deadline,
                                        settlement=settlement)
            child.check_returncode()
            sample = json.loads(child.stdout)
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
        result['native_lifecycle'] = native_owner.close()
        result['complete'] = True; save()


if __name__ == '__main__':
    main()
