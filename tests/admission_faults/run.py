#!/usr/bin/env python3
"""Qualify finite admission faults with private ML injections and synthetic promises."""
import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCES = [
    'src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
    'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
    'src/borrowedWork.mli', 'src/borrowedWork.ml',
    'src/helperSupervisor_stubs.c', 'src/helperSupervisor.mli', 'src/helperSupervisor.ml',
    'src/semanticAdmission.mli', 'src/semanticAdmission.ml',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def instrument(work):
    path = work / 'lwt.ml'
    source = path.read_text()
    source = replace_once(source,
        'let add_waiter t f = t.waiters <- f :: t.waiters', '''
let waiter_faults = ref 0 and waiter_hits = ref 0
let test_fail_waiters count = waiter_faults := count; waiter_hits := 0
let test_waiter_hits () = !waiter_hits
let add_waiter t f =
  if !waiter_faults > 0 then begin
    decr waiter_faults; incr waiter_hits; raise Out_of_memory
  end;
  t.waiters <- f :: t.waiters
let test_raw_observer t f = add_waiter t f
let test_waiter_count t = List.length t.waiters
''')
    source = replace_once(source,
        'let wakeup t v = restart t (Return v) "wakeup"', '''
let wakeup_target : Obj.t option ref = ref None
let wakeup_faults = ref 0 and wakeup_hits = ref 0
let test_fail_wakeup t count =
  wakeup_target := Some (Obj.repr t); wakeup_faults := count; wakeup_hits := 0
let test_wakeup_hits () = !wakeup_hits
let test_clear_wakeup () = wakeup_target := None; wakeup_faults := 0
let wakeup t v =
  if !wakeup_faults > 0 &&
     (match !wakeup_target with Some target -> Obj.repr t == target | None -> false) then begin
    decr wakeup_faults; incr wakeup_hits; raise Out_of_memory
  end;
  restart t (Return v) "wakeup"
''')
    path.write_text(source)
    with (work / 'lwt.mli').open('a') as stream:
        stream.write('''
val test_fail_waiters : int -> unit
val test_waiter_hits : unit -> int
val test_raw_observer : 'a t -> (unit -> unit) -> unit
val test_waiter_count : 'a t -> int
val test_fail_wakeup : 'a t -> int -> unit
val test_wakeup_hits : unit -> int
val test_clear_wakeup : unit -> unit
''')
    path = work / 'lwt_unix_impl.ml'
    source = replace_once(path.read_text(), 'let yield () = sleep 0.', '''
let yield_faults = ref 0 and yield_hits = ref 0
let test_fail_yields count = yield_faults := count; yield_hits := 0
let test_yield_hits () = !yield_hits
let yield () =
  if !yield_faults > 0 then begin
    decr yield_faults; incr yield_hits; raise Out_of_memory
  end;
  sleep 0.
''')
    path.write_text(source)
    with (work / 'lwt_unix.mli').open('a') as stream:
        stream.write('\nval test_fail_yields : int -> unit\nval test_yield_hits : unit -> int\n')
    path = work / 'helperSupervisor.ml'
    source = replace_once(path.read_text(), 'let on_cancel c notify =', '''
let unregister_faults = ref 0 and unregister_hits = ref 0
let registration_faults = ref 0 and registration_hits = ref 0
let cancel_during_registration = ref false
let test_fail_unregister count = unregister_faults := count; unregister_hits := 0
let test_unregister_hits () = !unregister_hits
let test_fail_registration count = registration_faults := count; registration_hits := 0
let test_registration_hits () = !registration_hits
let test_cancel_during_registration () = cancel_during_registration := true
let on_cancel c notify =
  if !cancel_during_registration then begin
    cancel_during_registration := false; cancel c
  end;
  if !registration_faults > 0 then begin
    decr registration_faults; incr registration_hits; raise Out_of_memory
  end;''')
    source = replace_once(source,
        'listener.listening <- false;\n      c#state.listeners <- List.filter', '''listener.listening <- false;
      if !unregister_faults > 0 then begin
        decr unregister_faults; incr unregister_hits; raise Out_of_memory
      end;
      c#state.listeners <- List.filter''')
    path.write_text(source)
    with (work / 'helperSupervisor.mli').open('a') as stream:
        stream.write('''
val test_fail_unregister : int -> unit
val test_unregister_hits : unit -> int
val test_fail_registration : int -> unit
val test_registration_hits : unit -> int
val test_cancel_during_registration : unit -> unit
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--negative-control', choices=(
        'unregister', 'schedule', 'allocating-grant', 'allocating-retire'))
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(key, None)
    directory = (nullcontext(tempfile.mkdtemp(prefix='unison-admission-faults-', dir='/private/tmp'))
                 if args.keep_work else
                 tempfile.TemporaryDirectory(prefix='unison-admission-faults-', dir='/private/tmp'))
    with directory as tmp:
        work = Path(tmp)
        print('work', work, flush=True)
        pins = {}
        for name in SOURCES + ['tests/admission_faults/test.ml', 'tests/admission_faults/run.py']:
            data = (root / name).read_bytes()
            pins[name] = sha(data)
            (work / Path(name).name).write_bytes(data)
        (work / 'production-source-pins.json').write_text(json.dumps(pins, indent=2) + '\n')
        instrument(work)
        selection = 'all'
        expected_failure = None
        if args.negative_control:
            path = work / 'semanticAdmission.ml'
            source = path.read_text()
            if args.negative_control == 'unregister':
                source = replace_once(source, 'try cleanup () with _ -> ()', 'cleanup ()')
                selection = 'grant-unregister-oom'
                expected_failure = 'grant was lost at unregister failure'
            elif args.negative_control == 'schedule':
                start = source.index('let request_dispatch t =')
                end = source.index('let release t ', start)
                source = source[:start] + '''let request_dispatch t =
  if not t.scheduled then begin
    t.scheduled <- true;
    Lwt.ignore_result (Lwt_unix.yield () >>= fun () ->
      t.scheduled <- false; dispatch t; return ())
  end
''' + source[end:]
                selection = 'schedule-waiter-oom'
                expected_failure = 'one-shot scheduling fault stranded sibling'
            elif args.negative_control == 'allocating-grant':
                source = replace_once(source, 'Lwt.wakeup_from ticket.reply ticket.granted',
                                      'Lwt.wakeup ticket.reply true')
                selection = 'grant-bypasses-result-constructor'
                expected_failure = 'queued grant entered allocating result constructor'
            else:
                source = replace_once(source, 'Lwt.wakeup_from r.reply r.declined',
                                      'Lwt.wakeup r.reply false')
                selection = 'retire-bypasses-result-constructor'
                expected_failure = 'queued retirement entered allocating result constructor or lost false reply'
            path.write_text(source)
        commands = []
        with (work / 'build.log').open('w') as log:
            for name in SOURCES:
                command = [compiler, '-I', '+unix', '-c', Path(name).name]
                commands.append(command)
                subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            objects = [Path(name).stem + ('.o' if name.endswith('.c') else '.cmx')
                       for name in SOURCES if name.endswith(('.c', '.ml'))]
            command = [compiler, '-I', '+unix', 'unix.cmxa', *objects, 'test.ml', '-o', 'fault-test']
            commands.append(command)
            subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        command = [str(work / 'fault-test'), selection]
        with (work / 'test.log').open('w') as log:
            result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=30)
        output = (work / 'test.log').read_text()
        accepted = (result.returncode != 0 and expected_failure in output
                    if args.negative_control else result.returncode == 0)
        verification = {
            'scope': 'Synthetic owner-loop accounting and finite private ML faults only; no native descriptor census, SDK or Photo operations.',
            'compiler': compiler,
            'compiler_version': subprocess.check_output([compiler, '-version'], env=env, text=True).strip(),
            'production_source_pins': pins,
            'mutated_source_pins': {p.name: sha(p.read_bytes()) for p in work.iterdir()
                                    if p.suffix in ('.ml', '.mli', '.c')},
            'build_commands': commands,
            'test_command': command,
            'build_exit': 0,
            'test_exit': result.returncode,
            'negative_control': args.negative_control,
            'expected_failure': expected_failure,
            'accepted': accepted,
            'pass_groups': sum(line.startswith('PASS ') for line in output.splitlines()),
            'artifact_pins': {p.name: sha(p.read_bytes()) for p in work.iterdir() if p.is_file()},
        }
        (work / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
        print(output, end='', flush=True)
        print(json.dumps({key: verification[key] for key in
                         ('compiler_version', 'test_exit', 'negative_control', 'pass_groups', 'accepted')}), flush=True)
        if not accepted:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
