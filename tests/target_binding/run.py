#!/usr/bin/env python3
"""Test the production TargetBinding registry in an isolated endpoint harness."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from stubs import MODULES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    controls = parser.add_mutually_exclusive_group()
    controls.add_argument('--negative-control', action='store_true')
    controls.add_argument('--negative-handoff-control', action='store_true')
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    with tempfile.TemporaryDirectory(prefix='unison-target-binding-', dir='/private/tmp') as tmp:
        work = Path(tmp)
        for name in ('src/targetBinding.ml', 'src/targetBinding.mli',
                     'src/lwt/lwt.ml', 'src/lwt/lwt.mli',
                     'tests/target_binding/test.ml', 'tests/target_binding/stubs.py'):
            data = (root / name).read_bytes()
            print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
            if name.endswith(('.ml', '.mli')):
                (work / Path(name).name).write_bytes(data)
        for module, source in MODULES.items():
            (work / (module + '.ml')).write_text(source)
        # Keep the real bundled promise implementation. Private one-shot fault
        # hooks exercise its actual continuation-allocation handoff boundary.
        lwt = (work / 'lwt.ml').read_text()
        lwt = lwt.replace('let add_waiter t f = t.waiters <- f :: t.waiters', '''
let waiter_faults = ref 0
let test_fail_waiters count = waiter_faults := count
let add_waiter t f =
  if !waiter_faults > 0 then (decr waiter_faults; raise Out_of_memory);
  t.waiters <- f :: t.waiters''')
        lwt = lwt.replace('let try_bind x f = try_bind_rec (apply x ()) f', '''
let dispatch_count = ref 0
let dispatch_fault = ref 0
let test_fail_dispatch ordinal = dispatch_count := 0; dispatch_fault := ordinal
let try_bind x f g =
  incr dispatch_count;
  if !dispatch_fault = !dispatch_count then begin
    dispatch_fault := 0; raise Out_of_memory
  end;
  try_bind_rec (apply x ()) f g''')
        # The original declaration is curried across both continuations.
        assert 'let test_fail_dispatch' in lwt and 'let test_fail_waiters' in lwt
        (work / 'lwt.ml').write_text(lwt)
        with (work / 'lwt.mli').open('a') as stream:
            stream.write('\nval test_fail_waiters : int -> unit\n'
                         'val test_fail_dispatch : int -> unit\n')
        print('instrumented lwt.ml', hashlib.sha256(lwt.encode()).hexdigest(), flush=True)
        if args.negative_control:
            source = (work / 'targetBinding.ml').read_text()
            source, count = re.subn(
                r'let handoff_failure t =\n.*?\nlet invalidate_session',
                'let handoff_failure t = close_noerr t\n\nlet invalidate_session',
                source, count=1, flags=re.S)
            assert count == 1
            (work / 'targetBinding.ml').write_text(source)
            print('negative-control targetBinding.ml',
                  hashlib.sha256(source.encode()).hexdigest(), flush=True)
        if args.negative_handoff_control:
            source = (work / 'targetBinding.ml').read_text()
            source, count = re.subn(
                r'let legacy_handoff t =\n.*?\nlet quarantine',
                '''let legacy_handoff t =
  if not t.handed_off then begin
    check_open t;
    t.handed_off <- true;
    FinalPublication.release (context t)
  end

let quarantine''', source, count=1, flags=re.S)
            assert count == 1
            (work / 'targetBinding.ml').write_text(source)
            print('negative-handoff targetBinding.ml',
                  hashlib.sha256(source.encode()).hexdigest(), flush=True)
        modules = ['util', 'features', 'prefs', 'osx', 'case', 'name', 'path',
                   'fspath', 'fileinfo', 'remote', 'os', 'finalPublication', 'lwt', 'targetBinding']
        for module in modules:
            interface = work / (module + '.mli')
            if interface.exists():
                subprocess.run([compiler, '-I', '+unix', '-c', interface.name],
                               cwd=work, env=environment, check=True)
            subprocess.run([compiler, '-I', '+unix', '-c', module + '.ml'],
                           cwd=work, env=environment, check=True)
        subprocess.run([compiler, '-I', '+unix', 'unix.cmxa'] +
                       [module + '.cmx' for module in modules] +
                       ['test.ml', '-o', 'ticket-test'],
                       cwd=work, env=environment, check=True)
        print('Compiler', subprocess.check_output([compiler, '-version'], text=True,
                                                  env=environment).strip(), flush=True)
        result = subprocess.run([str(work / 'ticket-test'), str(work)],
                                cwd=work, env=environment, capture_output=True,
                                text=True, timeout=60)
        print(result.stdout, end='', flush=True)
        print(result.stderr, end='', flush=True)
        if args.negative_control:
            assert result.returncode != 0, 'premature-close negative control unexpectedly passed'
            assert 'waiter allocation failure retains sleeping helper fd' in result.stderr
            print('PASS: premature-close negative control rejected', flush=True)
        elif args.negative_handoff_control:
            assert result.returncode != 0, 'unchecked legacy-handoff control unexpectedly passed'
            assert 'rebound resolution cannot select legacy backend' in result.stderr
            print('PASS: unchecked legacy-handoff negative control rejected', flush=True)
        else:
            result.check_returncode()


if __name__ == '__main__':
    main()
