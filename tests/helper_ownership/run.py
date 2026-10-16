#!/usr/bin/env python3
"""Finite macOS helper ownership controls in retained private compiler builds."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--ocamlopt', required=True)
parser.add_argument('--negative', choices=('missing-guard', 'early-release', 'missing-outer-guard', 'early-cpu-release'))
args = parser.parse_args()
if sys.platform != 'darwin':
    raise SystemExit('The retained native descriptor/PID fixture is qualified on macOS only')
root = Path(__file__).resolve().parents[2]
compiler = Path(args.ocamlopt).resolve()
work = Path(tempfile.mkdtemp(prefix='unison-helper-ownership-', dir='/private/tmp'))
print('work', work, flush=True)
inputs = ['src/lwt/lwt.mli', 'src/lwt/lwt.ml', 'src/lwt/pqueue.mli', 'src/lwt/pqueue.ml',
          'src/lwt/generic/lwt_unix_impl.ml', 'src/lwt/lwt_unix.mli', 'src/lwt/lwt_unix.ml',
          'src/borrowedWork.mli', 'src/borrowedWork.ml',
          'src/helperSupervisor.mli', 'src/helperSupervisor.ml', 'src/helperSupervisor_stubs.c',
          'tests/helper_ownership/fixture.c', 'tests/helper_ownership/fixture.ml',
          'tests/helper_ownership/test.ml', 'tests/helper_ownership/run.py',
          'tests/helper_ownership/README.md']
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
pins = {name: sha(root / name) for name in inputs}
for name in inputs:
    shutil.copy2(root / name, work / Path(name).name)
original = (work / 'helperSupervisor.ml').read_text()
prefix = '''module RealUnix = Unix
module Unix = struct
  include RealUnix
  let waitpid flags target =
    Fixture.before_wait target;
    let result = RealUnix.waitpid flags target in
    Fixture.after_wait target result;
    result
  let close descriptor = RealUnix.close descriptor; Fixture.after_close descriptor
end
'''
mutated = prefix + original
def insert(old, new, count=1):
    global mutated
    assert mutated.count(old) == count, (old, mutated.count(old), count)
    mutated = mutated.replace(old, new)
insert('let descriptors = Array.make 4 Unix.stdin in',
       'let descriptors = (Fixture.hit 1; Array.make 4 Unix.stdin) in')
insert('pipe 0 1;', 'pipe 0 1; Fixture.hit 2;')
insert('pipe 2 3;', 'pipe 2 3; Fixture.hit 3;')
insert('Unix.set_nonblock out.fd; Unix.set_nonblock err.fd;',
       'Unix.set_nonblock out.fd; Unix.set_nonblock err.fd; Fixture.hit 4;')
insert('owned_pid := spawn_group executable argv environment descriptors.(1) descriptors.(3);',
       'owned_pid := spawn_group executable argv environment descriptors.(1) descriptors.(3); Fixture.hit 5;')
insert('close 1; close 3;', 'close 1; close 3; Fixture.hit 6;')
insert('unregister := register_cleanup c teardown;',
       'Fixture.hit 7; unregister := register_cleanup c teardown; Fixture.hit 8;')
insert('end else Lwt_unix.sleep tick >>= monitor',
       'end else Lwt_unix.sleep tick >>= (fun () -> Fixture.hit 9; monitor ())')
insert('let result = { outcome = !outcome; status = !reaped;',
       'Fixture.hit 10;\n        let result = { outcome = !outcome; status = !reaped;')
mutated, count = re.subn(r'(owned_pid := -1;)(\n +reaped := Some status)',
                        r'\1 Fixture.hit 11;\2', mutated)
assert count == 2
insert('let process_cleanups = cleanup :: !active_cleanups in',
       'Fixture.hit 12;\n  let process_cleanups = cleanup :: !active_cleanups in')
insert('return { outcome = Failed (Printexc.to_string exn); status = !reaped;',
       'Fixture.hit 13;\n         return { outcome = Failed (Printexc.to_string exn); status = !reaped;')
insert('try catch start failed with exn ->',
       'try (if !Fixture.selected = 15 then (let pending = start () in Fixture.hit 15; catch (fun () -> pending) failed) else catch start failed) with exn ->')
insert('try try_bind execute_owned succeeded failed',
       'try Fixture.hit 25; (if !Fixture.selected = 18 then (let pending = execute_owned () in Fixture.hit 18; try_bind (fun () -> pending) succeeded failed) else try_bind execute_owned succeeded failed)')
insert('let granted = return true and rejected = return false in',
       'let granted = (Fixture.hit 19; return true) and rejected = return false in')
insert('unregister := register_cleanup c retire_pending;',
       'Fixture.hit 20; unregister := register_cleanup c retire_pending; Fixture.hit 22;')
insert('let process_cleanups = cleanup :: !active_cleanups in',
       'Fixture.hit 21; Fixture.registration_callback (); let process_cleanups = cleanup :: !active_cleanups in')
insert('let next = previous @ [ticket] in',
       'Fixture.hit 23; Fixture.publish_callback (); let next = previous @ [ticket] in')
insert('on_admitted ();', 'Fixture.hit 24; on_admitted ();')
insert('let remaining = List.filter (fun x -> x.number <> ticket.number) t.queue in',
       'Fixture.hit 31; let remaining = List.filter (fun x -> x.number <> ticket.number) t.queue in')
insert('remove ();\n      !unregister ();', 'remove ();\n      Fixture.hit 32; !unregister ();')
insert('try try_bind acquire_owned activate acquisition_failed',
       'try (if !Fixture.selected = 33 || !Fixture.selected = 34 then (let pending = acquire_owned () in Fixture.hit !Fixture.selected; try_bind (fun () -> pending) activate acquisition_failed) else try_bind acquire_owned activate acquisition_failed)', count=2)
insert('let borrowed = ref false and awaited = ref (wait ()) in',
       'let borrowed = (Fixture.hit 27; ref false) and awaited = ref (wait ()) in')
insert('else BorrowedWork.try_bind start success failure',
       'else (Fixture.hit 28; BorrowedWork.try_bind start success failure)')
# Raise at the returned-promise observer installation boundary. BorrowedWork's
# real invoke has already recorded awaited/returned when this private wrapper
# receives the promise. Raising inside invoke itself would be converted into a
# work failure by vendored Lwt.apply and would test a different boundary.
borrowed_prefix = '''module RealLwt = Lwt
module Lwt = struct
  include RealLwt
  let try_bind invoke success failure =
    let pending = invoke () in
    Fixture.hit 26;
    RealLwt.try_bind (fun () -> pending) success failure
end
'''
borrowed = borrowed_prefix + (work / 'borrowedWork.ml').read_text()
if args.negative == 'missing-guard':
    insert('''(try teardown () with _ ->
         (* A later status/cleanup allocation must not hide the first error.
            Unexpected OS refusal to reap remains outside a hard deadline. *)
         if !owned_pid >= 0 then raise exn);''', '();')
elif args.negative == 'early-release':
    insert('let teardown () =', 'let teardown () =\n      release ();')
    insert('if !owns_reservation && !owner_settled () then begin',
           'if !owns_reservation then begin')
elif args.negative == 'missing-outer-guard':
    insert('''let failed exn =
    (try !owner_cleanup () with _ -> ());
    release_once (); fail exn in''',
           'let failed exn = release_once (); fail exn in')
    insert('''with exn ->
      (try !owner_cleanup () with _ -> ());
      release_once (); raise exn in''',
           'with exn -> release_once (); raise exn in')
    insert('''with exn ->
    (try !abort_pending () with _ -> ());
    (try !owner_cleanup () with _ -> ());
    release_once (); raise exn''',
           'with exn -> (try !abort_pending () with _ -> ()); release_once (); raise exn')
elif args.negative == 'early-cpu-release':
    # Retire the actual CPU reservation at the observer error, then retain the
    # ordinary drain. The sleeping borrower observes premature retirement and
    # the existing designated assertion distinguishes this ownership fault.
    with (work / 'fixture.ml').open('a') as stream:
        stream.write('\nlet before_borrowed_failure = ref (fun () -> ())\n')
    insert('else (Fixture.hit 28; BorrowedWork.try_bind start success failure)',
           'else (Fixture.hit 28; Fixture.before_borrowed_failure := release_once; BorrowedWork.try_bind start success failure)')
    assert borrowed.count('first_error := error;') == 1
    borrowed = borrowed.replace('first_error := error;',
                                'first_error := error; !Fixture.before_borrowed_failure ();')
(work / 'helperSupervisor.ml').write_text(mutated)
(work / 'borrowedWork.ml').write_text(borrowed)
(work / 'child.ml').write_text('let () = ignore (Unix.select [] [] [] (float_of_string Sys.argv.(1)))\n')
commands = []
environment = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get('PATH',''))
for name in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):
    environment.pop(name, None)
configuration = subprocess.check_output([str(compiler), '-config'], env=environment, text=True)
(work/'compiler-config.txt').write_text(configuration)
config = dict(line.split(': ',1) for line in configuration.splitlines() if ': ' in line)
native_compiler = shutil.which(config['c_compiler'].split()[0], path=environment['PATH'])
def run(command, log):
    commands.append(command)
    result = subprocess.run(command, cwd=work, env=environment, stdout=log, stderr=subprocess.STDOUT,
                            timeout=30)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)
with (work / 'build.log').open('w') as log:
    for name in ('lwt.mli','lwt.ml','pqueue.mli','pqueue.ml','lwt_unix_impl.ml','lwt_unix.mli',
                 'lwt_unix.ml','fixture.c','fixture.ml','borrowedWork.mli','borrowedWork.ml',
                 'helperSupervisor.mli','helperSupervisor.ml'):
        run([str(compiler), '-I', '+unix', '-c', name] +
            (['-o', 'owner_stubs.o'] if name == 'fixture.c' else []), log)
    run([str(compiler), '-I','+unix','unix.cmxa','child.ml','-o','child'], log)
    run([str(compiler), '-I','+unix','unix.cmxa','lwt.cmx','pqueue.cmx','lwt_unix_impl.cmx',
         'lwt_unix.cmx','owner_stubs.o','fixture.cmx','borrowedWork.cmx',
         'helperSupervisor.cmx','test.ml','-o','test'], log)
command = [str(work / 'test'), str(work / 'child')]
if args.negative:
    command.append('18' if args.negative == 'missing-outer-guard' else '26' if args.negative == 'early-cpu-release' else '5')
with (work / 'test.log').open('w') as log:
    commands.append(command)
    result = subprocess.run(command, cwd=work, env=environment, stdout=log, stderr=subprocess.STDOUT,
                            timeout=30)
text = (work / 'test.log').read_text()
expected = 'DESIGNATED child was not actually reaped before return' if args.negative in ('missing-guard','missing-outer-guard') else \
           'DESIGNATED CPU borrower released before settlement' if args.negative == 'early-cpu-release' else \
           'DESIGNATED permits released before owned child wait'
accepted = result.returncode == 0 if not args.negative else result.returncode == 2 and expected in text
receipt = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), work=str(work),
               compiler=str(compiler), compiler_sha256=sha(compiler),
               compiler_version=subprocess.check_output([str(compiler),'-version'],text=True).strip(),
               compiler_config_sha256=sha(work/'compiler-config.txt'),
               native_compiler=native_compiler, native_compiler_sha256=sha(native_compiler),
               sources=pins, private_source_sha256=sha(work/'helperSupervisor.ml'),
               private_borrowed_work_sha256=sha(work/'borrowedWork.ml'),
               private_fixture_sha256=sha(work/'fixture.ml'),
               cpu_observer_fault_seam='Private BorrowedWork Lwt.try_bind wrapper invokes the real recording closure, then hits phase26 before installing the observer; phase28 is before BorrowedWork/start.',
               early_cpu_release_negative=('Actual HelperSupervisor release_once called from private BorrowedWork observer-error handling before the normal settlement drain.'
                                           if args.negative == 'early-cpu-release' else None),
               commands=commands, negative=args.negative, test_exit=result.returncode, accepted=accepted,
               artifacts={str(p):sha(p) for p in sorted(work.iterdir()) if p.is_file()},
               limits=['Synthetic finite child only; no Adobe/Photo.',
                       'Private ML fault injections/native PID observation; no production hooks.',
                       'Actual direct-child wait and ECHILD checked, not PID absence.',
                       'CPU/child credits observed before actual wait; no process RSS/FD cap.',
                       'Unexpected OS refusal/uninterruptible wait and universal allocation failure are not bounded.'])
(work/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(text, end='')
print('receipt', work/'verification.json', flush=True)
raise SystemExit(0 if accepted else 1)
