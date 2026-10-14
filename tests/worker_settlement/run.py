#!/usr/bin/env python3
"""Qualify post-dispatch settlement with actual domains and private waiter faults."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PARENT = '9fbfc00ccd03ac6fddd9e04abefc15f1381a72b7'
PARTICIPANTS = ('src/helperSupervisor.ml', 'src/ioAdmission.ml', 'src/semanticWorkers.ml')
SOURCES = [
    'tests/worker_settlement/fault.ml',
    'src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
    'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
    'src/borrowedWork.mli', 'src/borrowedWork.ml',
    'src/helperSupervisor_stubs.c', 'src/helperSupervisor.mli', 'src/helperSupervisor.ml',
    'src/semanticAdmission.mli', 'src/semanticAdmission.ml', 'src/ioAdmission.mli', 'src/ioAdmission.ml',
    'src/semanticHash_stubs.c', 'src/semanticHash.mli', 'src/semanticHash.ml',
    'src/semanticFile_stubs.c', 'src/semanticFile.mli', 'src/semanticFile.ml',
    'src/formatRecognition.mli', 'src/formatRecognition.ml',
    'src/formatExtension.mli', 'src/formatExtension.ml',
    'src/xmpObservation.mli', 'src/xmpObservation.ml',
    'src/dngSemantic.mli', 'src/dngSemantic.ml', 'src/semanticDelta.mli', 'src/semanticDelta.ml',
    'src/semanticWorkers.mli', 'src/semanticWorkers.ml', 'tests/resource_lifetime/census.c',
    'tests/worker_settlement/test.ml', 'tests/worker_settlement/run.py', 'tests/worker_settlement/README.md',
]
PHASES = ('raw-reply', 'cpu-result-map', 'io-callback', 'io-result-map', 'submit-outer', 'identify-map')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('private watch seam no longer unique: ' + old)
    return source.replace(old, new)


def instrument(sources, *, parent):
    modified = dict(sources)
    modified['src/lwt/lwt.ml'] = once(modified['src/lwt/lwt.ml'],
        'let add_waiter t f = t.waiters <- f :: t.waiters',
        'let add_waiter t f = Fault.before_add_waiter (Obj.repr t); t.waiters <- f :: t.waiters')
    source = modified['src/semanticWorkers.ml']
    source = once(source, 'let reply = Lwt.wait () in',
                  'let reply = Lwt.wait () in Fault.capture "raw-reply" (Obj.repr reply);')
    source = once(source, 'Lwt.ignore_result (pump t (Bytes.create 4096));',
                  'Fault.watch_slots (fun () -> t.slots); Lwt.ignore_result (pump t (Bytes.create 4096));')
    if not parent:
        source = once(source, 'else BorrowedWork.try_bind (fun () ->\n          H.with_cpu_permits',
                      'else BorrowedWork.try_bind (Fault.watch "cpu-result-map" (fun () ->\n          H.with_cpu_permits')
        source = once(source, 'end)) (function', 'end))) (function')
        source = once(source, '(fun () -> IoAdmission.with_devices io admission_cancel ~devices execute)',
                      '(Fault.watch "io-result-map" (fun () -> IoAdmission.with_devices io admission_cancel ~devices execute))')
        source = once(source, 'BorrowedWork.try_bind admitted_execution',
                      'BorrowedWork.try_bind (Fault.watch "submit-outer" admitted_execution)')
        source = once(source, '(fun () -> submit t cancellation fd (Identify recognizers))',
                      '(Fault.watch "identify-map" (fun () -> submit t cancellation fd (Identify recognizers)))')
        modified['src/ioAdmission.ml'] = once(modified['src/ioAdmission.ml'],
            'BorrowedWork.try_bind f', 'BorrowedWork.try_bind (Fault.watch "io-callback" f)')
        modified['src/borrowedWork.ml'] = (
            'module Lwt_unix = struct\n  include Lwt_unix\n'
            '  let sleep duration = Fault.before_sleep (); Lwt_unix.sleep duration\nend\n' +
            modified['src/borrowedWork.ml'])
    modified['src/semanticWorkers.ml'] = source
    return modified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--negative-only', action='store_true')
    parser.add_argument('--fixed-only', action='store_true')
    args = parser.parse_args()
    if args.negative_only and args.fixed_only:
        parser.error('choose only one participant mode')
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    compiler = str(Path(compiler).resolve())
    env = os.environ.copy()
    for name in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(name, None)
    work = Path(tempfile.mkdtemp(prefix='unison-worker-settlement-', dir='/private/tmp'))
    original = {name: (ROOT / name).read_text() for name in SOURCES}
    receipt = {'schema': 1, 'work': str(work), 'retained': args.keep_work,
               'source_pins': {name: sha(ROOT / name) for name in SOURCES},
               'parent': PARENT, 'compiler': {'path': compiler, 'sha256': sha(Path(compiler))},
               'commands': [], 'runs': [], 'success': False,
               'scope': 'actual bounded domain and endpoint admission, private returned-promise waiter faults',
               'Photo_or_Adobe_access': False, 'performance_claim': False}

    def command(argv, directory, label, *, expected_failure=False, timeout=30):
        result = subprocess.run(argv, cwd=directory, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        log = directory / (label + '.log')
        log.write_text(result.stdout)
        entry = {'argv': argv, 'cwd': str(directory), 'exit': result.returncode,
                 'log': str(log), 'log_sha256': sha(log)}
        receipt['commands'].append(entry)
        if result.stdout.strip():
            print(result.stdout if result.returncode else result.stdout.strip().splitlines()[-1], flush=True)
        if not expected_failure:
            result.check_returncode()
        return result, entry

    try:
        receipt['compiler']['version'] = command([compiler, '-version'], work, 'compiler-version')[0].stdout.strip()
        frozen = work / 'frozen-inputs'
        for name, text in original.items():
            target = frozen / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        modes = ['parent'] if args.negative_only else ['fixed'] if args.fixed_only else ['parent', 'fixed']
        for mode in modes:
            directory = work / mode
            directory.mkdir()
            sources = dict(original)
            if mode == 'parent':
                parent_sources = {}
                for name in PARTICIPANTS:
                    data = subprocess.check_output(['git', 'show', PARENT + ':' + name], cwd=ROOT)
                    sources[name] = data.decode()
                    parent_sources[name] = hashlib.sha256(data).hexdigest()
                receipt['parent_participant_pins'] = parent_sources
            sources = instrument(sources, parent=mode == 'parent')
            compile_sources = [name for name in SOURCES if name.endswith(('.ml', '.mli', '.c')) and
                               name != 'tests/worker_settlement/test.ml']
            for name in compile_sources + ['tests/worker_settlement/test.ml']:
                (directory / Path(name).name).write_text(sources[name])
            for name in compile_sources:
                command([compiler, '-I', '+unix', '-c', Path(name).name], directory, 'compile-' + Path(name).name)
            objects = [Path(name).stem + ('.o' if name.endswith('.c') else '.cmx')
                       for name in compile_sources if name.endswith(('.ml', '.c'))]
            command([compiler, '-I', '+unix', 'unix.cmxa', *objects, 'test.ml', '-o', 'settlement-test'],
                    directory, 'link')
            if mode == 'parent':
                cases = [('raw-reply', 'success', 'immediate', 0)]
            else:
                cases = [('normal', outcome, 'immediate', 0) for outcome in ('success', 'error', 'cancel')]
                cases += [(phase, outcome, 'immediate', 0) for phase in PHASES for outcome in ('success', 'error', 'cancel')]
                cases += [(phase, 'cancel', wait, 0) for phase in PHASES for wait in ('cpu', 'io')]
                cases += [(phase, 'cancel', 'immediate', 2) for phase in PHASES]
            for index, (phase, outcome, wait, timer_errors) in enumerate(cases):
                files = directory / ('case-' + str(index))
                files.mkdir()
                argv = [str(directory / 'settlement-test'), phase, outcome, wait, str(timer_errors)]
                if mode == 'parent':
                    argv.append('negative')
                result, entry = command(argv, files, 'test', expected_failure=mode == 'parent', timeout=15)
                if mode == 'parent':
                    designated = 'DESIGNATED active worker descriptors escaped retained workspace/CPU/IO/slot admission'
                    if result.returncode != 2 or designated not in result.stdout:
                        raise RuntimeError('parent participants did not fail the independent active-FD/admission oracle')
                receipt['runs'].append({'mode': mode, 'phase': phase, 'operation': outcome,
                                        'initial_wait': wait, 'timer_faults': timer_errors, 'execution': entry,
                                        'designated_negative_detected': mode == 'parent'})
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)): {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}
                                for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work / 'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print('Receipt ' + str(target), flush=True)
        print('Artifacts ' + str(work) + (' (retained)' if args.keep_work else ' (removed after receipt)'), flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
