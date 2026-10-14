#!/usr/bin/env python3
"""Retained actual synthetic-helper settlement controls, stock or OxCaml.

This runner builds private copies only. Parent mode restores the listed complete
production module inputs at the pinned commit; faults are applied after freezing
those bytes. No SDK, photograph, preview/cache, or benchmark is invoked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PARENT = '2059949975ae95e64df74a3056d7211101aa42b6'
SOURCES = [
    'tests/validation_settlement/fault.ml',
    'src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
    'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
    'src/borrowedWork.mli', 'src/borrowedWork.ml',
    'src/helperSupervisor.mli', 'src/helperSupervisor.ml',
    'src/semanticAdmission.mli', 'src/semanticAdmission.ml',
    'src/ioAdmission.mli', 'src/ioAdmission.ml',
    'src/semanticHash_stubs.c', 'src/semanticHash.mli', 'src/semanticHash.ml',
    'src/dngValidation.mli', 'src/dngValidation.ml',
    'src/helperSupervisor_stubs.c',
    'tests/validation_settlement/fixture.c',
    'tests/validation_settlement/test.ml',
    'tests/validation_settlement/group.ml',
    'tests/validation_settlement/helper.py',
    'tests/validation_settlement/run.py',
    'tests/validation_settlement/README.md',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('private waiter seam no longer unique: ' + old)
    return source.replace(old, new, 1)


def instrument(sources):
    modified = dict(sources)
    name = 'src/lwt/lwt.ml'
    modified[name] = once(modified[name],
        'let add_waiter t f = t.waiters <- f :: t.waiters',
        'let add_waiter t f = Fault.before_add_waiter (Obj.repr t); t.waiters <- f :: t.waiters')
    modified['src/borrowedWork.ml'] = (
        'module Lwt_unix = struct\n include Lwt_unix\n'
        ' let sleep duration = Fault.before_sleep (); Lwt_unix.sleep duration\nend\n' +
        modified['src/borrowedWork.ml'])
    return modified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--keep-work', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--negative-only', action='store_true')
    mode.add_argument('--fixed-only', action='store_true')
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    compiler = str(Path(compiler).resolve())
    environment = os.environ.copy()
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(key, None)
    work = Path(tempfile.mkdtemp(prefix='unison-validation-settlement-', dir='/private/tmp'))
    print('work', work, flush=True)
    original = {name: (ROOT / name).read_text() for name in SOURCES}
    receipt = {
        'schema': 1, 'work': str(work), 'retained': args.keep_work, 'parent': PARENT,
        'source_pins': {name: sha(ROOT / name) for name in SOURCES},
        'compiler': {'path': compiler, 'sha256': sha(Path(compiler))},
        'commands': [], 'runs': [], 'success': False,
        'scope': 'actual synthetic gated child, DNG returned-promise observers and retained CPU/IO/workspace',
        'Adobe_or_Photo_access': False, 'performance_claim': False,
    }

    def command(argv, directory, label, *, designated=None, timeout=30):
        result = subprocess.run(argv, cwd=directory, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        log = directory / (label + '.log')
        log.write_text(result.stdout)
        entry = {'argv': list(argv), 'cwd': str(directory), 'exit': result.returncode,
                 'log': str(log), 'log_sha256': sha(log)}
        receipt['commands'].append(entry)
        if result.stdout.strip():
            print(result.stdout.rstrip(), flush=True)
        if designated is None:
            result.check_returncode()
        elif result.returncode != 2 or designated not in result.stdout:
            raise RuntimeError('parent did not fail the independent live-child settlement oracle')
        return result, entry

    try:
        receipt['compiler']['version'] = command([compiler, '-version'], work, 'compiler-version')[0].stdout.strip()
        frozen = work / 'frozen-inputs'
        for name, contents in original.items():
            target = frozen / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents)
        modes = ['parent'] if args.negative_only else ['fixed'] if args.fixed_only else ['parent', 'fixed']
        for mode in modes:
            directory = work / mode
            directory.mkdir()
            sources = dict(original)
            production = {}
            if mode == 'parent':
                for name in SOURCES:
                    if name.startswith('src/'):
                        data = subprocess.check_output(['git', 'show', PARENT + ':' + name], cwd=ROOT)
                        sources[name] = data.decode()
                        production[name] = hashlib.sha256(data).hexdigest()
                receipt['parent_production_pins'] = production
            sources = instrument(sources)
            compile_sources = [name for name in SOURCES if name.endswith(('.ml', '.mli', '.c')) and
                               name not in ('src/helperSupervisor_stubs.c', 'tests/validation_settlement/test.ml',
                                            'tests/validation_settlement/group.ml')]
            for name in SOURCES:
                (directory / Path(name).name).write_text(sources[name])
            for name in compile_sources:
                command([compiler, '-I', '+unix', '-c', Path(name).name], directory,
                        'compile-' + Path(name).name)
            objects = [Path(name).stem + ('.o' if name.endswith('.c') else '.cmx')
                       for name in compile_sources if name.endswith(('.ml', '.c'))]
            command([compiler, '-I', '+unix', 'unix.cmxa', *objects, 'test.ml', '-o', 'validation-settlement-test'],
                    directory, 'link')
            cases = [('execute', 'pass', 'warn', 'ordinary')] if mode == 'parent' else [
                (phase, action, policy, cancellation)
                for phase in ('normal', 'execute')
                for action in ('pass', 'malformed', 'candidate-mutation', 'tool-mutation')
                for policy in ('warn', 'require')
                for cancellation in ('ordinary',)
            ] + [(phase, 'pass', policy, 'cancel')
                 for phase in ('normal', 'execute') for policy in ('warn', 'require')]
            if mode == 'fixed':
                cases.append(('execute', 'pass', 'off', 'ordinary'))
                cases += [('execute', 'pass', policy, 'timer-2') for policy in ('warn', 'require')]
            for index, (phase, action, policy, cancellation) in enumerate(cases):
                case = directory / ('case-' + str(index))
                case.mkdir()
                helper = case / 'synthetic-validator.py'
                helper.write_text(sources['tests/validation_settlement/helper.py'])
                helper.chmod(0o700)
                argv = [str(directory / 'validation-settlement-test'), phase, action, policy,
                        'ordinary' if cancellation == 'timer-2' else cancellation, str(helper)]
                if cancellation == 'timer-2':
                    argv.append('2')
                if mode == 'parent':
                    argv.append('negative')
                _, entry = command(argv, case, 'test', designated=(
                    'DESIGNATED validation result/workspace retired with an actual live helper'
                    if mode == 'parent' else None), timeout=20)
                receipt['runs'].append({'mode': mode, 'phase': phase, 'action': action,
                    'policy': policy, 'cancellation': cancellation, 'execution': entry,
                    'designated_negative_detected': mode == 'parent'})
            prefix = ('module Group = struct\n'
                      ' let all ~on_error tasks =\n'
                      '  BorrowedWork.try_bind (fun () -> BorrowedWork.all ~on_error tasks)\n'
                      '   (fun _ -> Lwt.return ()) Lwt.fail\nend\n')
            if mode == 'parent':
                legacy = subprocess.check_output(['git', 'show', PARENT + ':src/lwt/lwt_util.ml'], cwd=ROOT).decode()
                start = legacy.index('let rec iter ')
                end = legacy.index('\nlet ', start + 1)
                legacy_iter = legacy[start:end].replace('let rec iter f l =',
                    'let all ~on_error:_ tasks =\n let f work = work () and l = tasks in', 1)
                prefix = ('module Group = struct\n open Lwt\n' + legacy_iter + '\nend\n')
                receipt['parent_legacy_iter_source_sha256'] = hashlib.sha256(legacy.encode()).hexdigest()
                (directory / 'legacy_lwt_util.original.ml').write_text(legacy)
            group_source = directory / 'group.ml'
            group_source.write_text(prefix + sources['tests/validation_settlement/group.ml'])
            command([compiler, '-I', '+unix', 'unix.cmxa', *objects, 'group.ml', '-o', 'group-settlement-test'],
                    directory, 'link-group')
            group_cases = [('join', 0), ('launch', 0), ('launch-one', 0)] if mode == 'parent' else [
                ('normal', 0), ('join', 0), ('launch', 0), ('launch-one', 0), ('join', 2)]
            for phase, timer_errors in group_cases:
                case = directory / ('group-' + phase + '-timers-' + str(timer_errors))
                case.mkdir()
                helper = case / 'synthetic-validator.py'
                helper.write_text(sources['tests/validation_settlement/helper.py'])
                helper.chmod(0o700)
                argv = [str(directory / 'group-settlement-test'), phase, str(helper)]
                if timer_errors:
                    argv.append(str(timer_errors))
                if mode == 'parent':
                    argv.append('negative')
                _, entry = command(argv, case, 'test', designated=(
                    'DESIGNATED aggregate reported failure with an actual live sibling consumer'
                    if mode == 'parent' else None), timeout=20)
                receipt['runs'].append({'mode': mode, 'component': 'group', 'phase': phase, 'timer_errors': timer_errors,
                    'execution': entry, 'designated_negative_detected': mode == 'parent'})
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)): {'path': str(path),
            'bytes': path.stat().st_size, 'sha256': sha(path)}
            for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work / 'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print('receipt', target, 'success', receipt['success'], flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
