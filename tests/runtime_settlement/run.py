#!/usr/bin/env python3
"""Qualify real runtime/report owners with private returned-promise faults."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PARENT = '2059949975ae95e64df74a3056d7211101aa42b6'
PARENT_PARTICIPANTS = ('semanticRuntime.ml', 'semanticAdmission.ml', 'semanticRemote.ml', 'remote.ml')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('private fixture anchor must occur once: ' + old)
    return source.replace(old, new)


def section(source, begin, end, edit):
    first, last = source.index(begin), source.index(end, source.index(begin))
    return source[:first] + edit(source[first:last]) + source[last:]


RPC_EXPORTS = r'''
(* Private actual processRequest/output control. No handshake/client parser. *)
let test_rpc_name = "runtimeSettlementFixture"
let test_rpc_start fd with_scope handler =
  let channel = Lwt_unix.of_unix_file_descr fd in
  let conn = makeConnection true channel channel in
  let () = setConnectionVersion conn 1 in
  let _ = registerBoundedServerCmd test_rpc_name ~maxArgs:64 ~maxResult:1048576
    ~withScope:(fun _ () dispatch -> with_scope dispatch)
    Umarshal.unit (Umarshal.bounded_string 1048576) (fun _ () -> handler ()) in
  let fragments = safeMarshal (marshalV1 Umarshal.unit)
    (Bytearray.of_string (test_rpc_name ^ "-args")) () [] in
  let data = String.concat "" (List.map (fun (s,p,n) -> Bytearray.sub s p n) fragments) in
  let args = Bytearray.of_string (String.sub data intSize (String.length data - intSize)) in
  let id,_,_ = encodeInt 711 in
  conn, processRequest conn id test_rpc_name args
let test_rpc_decode conn data =
  let wire = Bytearray.of_string data in
  let total = Bytearray.length wire in
  let slice position length =
    if position < 0 || length < 0 || position > total - length then
      failwith "incomplete actual RPC frame";
    Bytearray.of_string (Bytearray.sub wire position length) in
  if decodeInt wire 0 <> 711 then failwith "actual RPC id mismatch";
  let header_size = decodeInt wire intSize in
  let header = unmarshalHeader conn (slice (2*intSize) header_size) in
  if header <> NormalResult then failwith "unexpected actual RPC exception/header";
  let body_position = 2*intSize + header_size in
  let body_size = decodeInt wire body_position in
  let body_position = body_position + intSize in
  let tag = Bytearray.of_string (test_rpc_name ^ "-res") in
  let answer = safeUnmarshal (unmarshalV1 (Umarshal.bounded_string 1048576)) tag
    (slice body_position body_size) in
  if body_position + body_size <> total then failwith "extra/trailing actual RPC packet";
  answer
let test_rpc_expected conn answer =
  let body = safeMarshal (marshalV1 (Umarshal.bounded_string 1048576))
    (Bytearray.of_string (test_rpc_name ^ "-res")) answer [] in
  let fragments = encodeInt 711 :: marshalHeader conn NormalResult body in
  String.concat "" (List.map (fun (s,p,n) -> Bytearray.sub s p n) fragments)
let test_client_cleanup = clientCloseCleanup
let test_rpc_close = closeConnection
'''


def instrument(directory, *, parent):
    def modify(name, edit):
        path = directory / name
        path.write_text(edit(path.read_text()))

    modify('lwt/lwt.ml', lambda text: once(text,
        'let add_waiter t f = t.waiters <- f :: t.waiters',
        'let add_waiter t f = Fault.before_add_waiter (Obj.repr t); t.waiters <- f :: t.waiters'))
    modify('borrowedWork.ml', lambda text:
        'module Lwt_unix = struct\n include Lwt_unix\n'
        ' let sleep duration = Fault.before_sleep (); Lwt_unix.sleep duration\nend\n' + text)
    modify('semanticWorkers.ml', lambda text: text + '\nlet test_slots t = t.slots\n')
    modify('semanticWorkers.mli', lambda text: text + '\nval test_slots : t -> int\n')

    def runtime(text):
        guard = 'Lwt.try_bind' if parent else 'BorrowedWork.try_bind'
        if parent:
            text = once(text, guard + ' (fun () -> f cancellation)',
                guard + ' (Fault.watch "runtime-cancellation" (fun () -> f cancellation))')
        else:
            text = section(text, 'let with_cancellation f =', 'let with_admission ',
                lambda block: once(block, 'BorrowedWork.try_bind invoke success failure',
                    'BorrowedWork.try_bind (Fault.watch "runtime-cancellation" invoke) success failure'))
        def io(block):
            block = once(block, guard + ' (fun () ->',
                guard + ' (Fault.watch "runtime-io-outer" (fun () ->')
            if parent:
                block = once(block, 'IoAdmission.with_devices (get ()).io cancellation ~devices f >>= function',
                    'Fault.watch "runtime-io-map" (fun () -> IoAdmission.with_devices (get ()).io cancellation ~devices f) () >>= function')
                block = once(block, 'fail (Util.Transient "Filesystem I/O admission cancelled"))',
                    'fail (Util.Transient "Filesystem I/O admission cancelled")))')
            else:
                block = once(block, '(fun () -> IoAdmission.with_devices (get ()).io cancellation ~devices f)',
                    '(Fault.watch "runtime-io-map" (fun () -> IoAdmission.with_devices (get ()).io cancellation ~devices f))')
                block = once(block, 'fail (Util.Transient "Filesystem I/O admission cancelled")))',
                    'fail (Util.Transient "Filesystem I/O admission cancelled"))))')
            return block
        text = section(text, 'let with_io_file ', 'let publication_cost ', io)
        def admission(block):
            catcher = 'Lwt.catch' if parent else 'BorrowedWork.catch'
            block = once(block, catcher + ' (fun () ->',
                catcher + ' (Fault.watch "runtime-admission-catch" (fun () ->')
            closing = 'fail (Util.Transient "Semantic resource admission cancelled"))' if parent else \
                'fail (Util.Transient "Semantic resource admission cancelled")))'
            block = once(block, closing, closing + ')')
            if not parent:
                block = once(block, '(fun () -> SemanticAdmission.with_lease (resource_gate ()) cancellation ~role ~cost f)',
                    '(Fault.watch "runtime-admission-map" (fun () -> SemanticAdmission.with_lease (resource_gate ()) cancellation ~role ~cost f))')
            return block
        return section(text, 'let with_admission ', 'let with_io_file ', admission)
    modify('semanticRuntime.ml', runtime)

    def admission(text):
        if parent:
            return text  # Parent negatives target concrete FD-owning wrappers.
        text = once(text, 'BorrowedWork.try_bind invoke success failure',
            'BorrowedWork.try_bind (Fault.watch "resource-borrow" invoke) success failure')
        text = once(text, 'BorrowedWork.try_bind (fun () -> acquire r cancellation)',
            'BorrowedWork.try_bind (Fault.watch "resource-acquire" (fun () -> acquire r cancellation))')
        return once(text, 'BorrowedWork.try_bind (fun () -> with_borrow r ~cost f)',
            'BorrowedWork.try_bind (Fault.watch "resource-lease-result" (fun () -> with_borrow r ~cost f))')
    modify('semanticAdmission.ml', admission)

    def report(text):
        text = once(text, 'let register_held_fd fd =',
            'let test_held_files = ref []\nlet register_held_fd fd =')
        text = once(text, 'try held_files.register files with error ->',
            'try let registered = held_files.register files in test_held_files := registered :: !test_held_files; registered with error ->')
        if parent:
            text = section(text, 'let borrowed files f =', 'let inspected =',
                lambda block: once(block, 'Lwt.try_bind f', 'Lwt.try_bind (Fault.watch "report-borrowed" f)'))
        else:
            text = section(text, 'let borrowed files f =', 'let inspected =',
                lambda block: once(block, 'BorrowedWork.try_bind (fun () -> files.busy <- true; f ())',
                    'BorrowedWork.try_bind (Fault.watch "report-borrowed" (fun () -> files.busy <- true; f ()))'))
        catcher = 'Lwt.catch' if parent else 'BorrowedWork.catch'
        text = once(text, 'let capture_report profile f = ' + catcher + ' f (function',
            'let capture_report profile f = ' + catcher + ' (Fault.watch "report-capture" f) (function')
        guard = 'Lwt.try_bind' if parent else 'BorrowedWork.try_bind'
        def inspect(block):
            block = once(block, guard + ' (fun () -> borrowed files (fun () ->',
                guard + ' (Fault.watch "report-outer" (fun () -> borrowed files (fun () ->')
            if parent:
                block = once(block, 'SemanticWorkers.inspect pool cancellation ~extension fd >>= fun result ->',
                    'Fault.watch "report-v0-map" (fun () -> SemanticWorkers.inspect pool cancellation ~extension fd) () >>= fun result ->')
                block = once(block, 'result) end))', 'result) end)))')
            else:
                block = once(block, '(fun () -> SemanticWorkers.inspect pool cancellation ~extension fd)',
                    '(Fault.watch "report-v0-map" (fun () -> SemanticWorkers.inspect pool cancellation ~extension fd))')
                block = once(block, 'result)) end))', 'result)) end)))')
            return block
        text = section(text, 'let inspect_file ', 'let inspection_args =', inspect)
        return text + '''\nlet test_inspect_file = inspect_file
let test_report_state () = match !test_held_files with
  | [] -> [] | files::_ -> [files.busy;files.closing;files.closed]
let test_release_reports () = List.iter held_files.release_noerr !test_held_files
'''
    modify('semanticRemote.ml', report)
    modify('semanticRemote.mli', lambda text: text + '''
val test_inspect_file : ?meaning:bool -> HelperSupervisor.cancellation -> FormatExtension.handle -> Fspath.t -> inspection Lwt.t
val test_report_state : unit -> bool list
val test_release_reports : unit -> unit
''')
    def remote(text):
        if parent:
            text = once(text, '| None -> action ()) >>= fun () ->',
                '| None -> Fault.watch_output (fun promise () -> Lwt.poll promise = None) action ()) >>= fun () ->')
            text = once(text, 'serverSide conn args >>= (fun answer ->',
                'Fault.watch "rpc-server-map" (fun () -> serverSide conn args) () >>= (fun answer ->')
            text = once(text, 'Lwt.try_bind (fun () -> cmd conn buf)',
                'Lwt.try_bind (Fault.watch "rpc-dispatch" (fun () -> cmd conn buf))')
            text = once(text, 'Lwt.catch (fun () -> scope conn buf dispatch)',
                'Lwt.catch (Fault.watch "rpc-scope" (fun () -> scope conn buf dispatch))')
        else:
            text = once(text, '(fun () -> match q.failure with Some e -> Lwt.fail e | None -> action ())',
                '(fun () -> match q.failure with Some e -> Lwt.fail e | None -> Fault.watch_output (fun promise () -> Lwt.poll promise = None) action ())')
            text = once(text, '(fun () -> serverSide conn args)',
                '(Fault.watch "rpc-server-map" (fun () -> serverSide conn args))')
            text = once(text, '(fun () -> cmd conn buf)',
                '(Fault.watch "rpc-dispatch" (fun () -> cmd conn buf))')
            text = once(text, 'BorrowedWork.catch (fun () -> scope conn buf dispatch)',
                'BorrowedWork.catch (Fault.watch "rpc-scope" (fun () -> scope conn buf dispatch))')
        return text + RPC_EXPORTS
    modify('remote.ml', remote)
    modify('remote.mli', lambda text: text + '''
val test_client_cleanup : unit -> unit
val test_rpc_start : Unix.file_descr -> ((unit -> unit Lwt.t) -> unit Lwt.t) -> (unit -> string Lwt.t) -> connection * unit Lwt.t
val test_rpc_decode : connection -> string -> string
val test_rpc_expected : connection -> string -> string
val test_rpc_close : connection -> unit
''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--negative-only', action='store_true')
    parser.add_argument('--fixed-only', action='store_true')
    args = parser.parse_args()
    if args.negative_only and args.fixed_only:
        parser.error('select one participant mode')
    compiler = str(Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve())
    build = args.build.resolve() / 'src'
    makefile = (build / 'Makefile.OCaml').read_text()
    def objects(name):
        match = re.search(r'^' + name + r' = (.*?)(?=\n\n)', makefile, re.M | re.S)
        if match is None:
            raise RuntimeError('Make object list unavailable: ' + name)
        return match.group(1).replace('\\\n', ' ').replace('$(SYSTEM)', 'generic') \
            .replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '') \
            .replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()
    modules = objects('OCAMLOBJS')
    modules = modules[:modules.index('semanticRemote.cmx') + 1]
    native = objects('COBJS')
    for path in modules + native:
        if not (build / path).is_file():
            raise RuntimeError('complete native compiler-matched snapshot required: ' + path)
    production = [path.with_suffix(suffix) for name in modules for path in [Path(name)]
                  for suffix in ('.ml', '.mli') if (build / path.with_suffix(suffix)).exists()]
    frozen_inputs = json.loads(args.freeze.read_text())['sources']
    frozen_production = [path for path in production if 'src/' + str(path) in frozen_inputs]
    generated = [path for path in production if path not in frozen_production]
    for path in frozen_production:
        if sha(ROOT / 'src' / path) != frozen_inputs['src/' + str(path)] or \
           sha(build / path) != frozen_inputs['src/' + str(path)]:
            raise RuntimeError('snapshot and workspace source differ: ' + str(path))
    test_names = ('run.py', 'test.ml', 'fault.ml', 'README.md')
    work = Path(tempfile.mkdtemp(prefix='unison-runtime-settlement-', dir='/private/tmp'))
    env = os.environ.copy()
    for name in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(name, None)
    receipt = {'schema': 'unison-runtime-report-returned-promise-settlement/0',
        'work': str(work), 'retained': args.keep_work, 'parent': PARENT,
        'compiler': {'path': compiler, 'sha256': sha(Path(compiler))},
        'freeze': {'path': str(args.freeze.resolve()), 'sha256': sha(args.freeze)},
        'build_snapshot': str(build.parent),
        'source_pins': {str(path): sha(build / path) for path in frozen_production},
        'generated_snapshot_source_pins': {str(path): sha(build / path) for path in generated},
        'test_pins': {name: sha(ROOT / 'tests/runtime_settlement' / name) for name in test_names},
        'input_object_pins': {name: sha(build / name) for name in modules + native},
        'commands': [], 'runs': [], 'success': False,
        'scope': 'Actual linked runtime, report held-FD and resource owners; private finite post-return waiter faults; synthetic files only.',
        'Photo_or_Adobe_access': False, 'performance_claim': False}
    def command(argv, directory, label, *, expected_failure=False, timeout=30, extra_env=None):
        command_env = dict(env, **(extra_env or {}))
        log = directory / (label + '.log')
        try:
            result = subprocess.run(argv, cwd=directory, env=command_env, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            log.write_text(result.stdout)
            entry = {'argv': argv, 'cwd': str(directory), 'exit': result.returncode,
                'log': str(log), 'log_sha256': sha(log), 'task_env': extra_env or {}}
            receipt['commands'].append(entry)
            if result.stdout.strip():
                print(result.stdout if result.returncode else result.stdout.strip().splitlines()[-1], flush=True)
            if not expected_failure:
                result.check_returncode()
            return result, entry
        except subprocess.TimeoutExpired as error:
            output = error.stdout or ''
            if isinstance(output, bytes):
                output = output.decode(errors='replace')
            log.write_text(output)
            receipt['commands'].append({'argv': argv, 'cwd': str(directory), 'timeout': timeout,
                'log': str(log), 'log_sha256': sha(log)})
            raise
    try:
        receipt['compiler']['version'] = command([compiler, '-version'], work, 'compiler-version')[0].stdout.strip()
        frozen = work / 'frozen-inputs'
        frozen.mkdir()
        for path in production:
            target = frozen / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(build / path, target)
        for name in test_names:
            shutil.copyfile(ROOT / 'tests/runtime_settlement' / name, frozen / name)
        shutil.copyfile(args.freeze, frozen / 'SOURCE-FREEZE.json')
        modes = ['parent', 'group-negative'] if args.negative_only else ['fixed'] if args.fixed_only else ['parent', 'fixed', 'group-negative']
        for mode in modes:
            directory = work / mode
            shutil.copytree(build, directory)
            shutil.copyfile(frozen/'fault.ml', directory/'fault.ml')
            shutil.copyfile(frozen/'test.ml', directory/'runtimeSettlementTest.ml')
            shutil.copyfile(ROOT / 'tests/resource_lifetime/census.c', directory / 'census.c')
            if mode == 'parent':
                receipt['parent_participant_pins'] = {}
                for name in PARENT_PARTICIPANTS:
                    data = subprocess.check_output(['git', 'show', PARENT + ':src/' + name], cwd=ROOT)
                    (directory / name).write_bytes(data)
                    receipt['parent_participant_pins'][name] = hashlib.sha256(data).hexdigest()
            instrument(directory, parent=mode == 'parent')
            if mode == 'group-negative':
                group_source = directory / 'borrowedWork.ml'
                source = group_source.read_text()
                start = source.index('let all ')
                source = source[:start] + '''let all ?on_error:_ tasks =
  let promises = List.map (fun task -> task ()) tasks in
  let rec join = function
    | [] -> Lwt.return []
    | promise :: rest -> Lwt.bind promise (fun value ->
      Lwt.bind (join rest) (fun values -> Lwt.return (value :: values))) in
  join promises
'''
                group_source.write_text(source)
                receipt['private_group_negative_sha256'] = sha(group_source)
            includes = [directory, directory/'ubase', directory/'system', directory/'system/generic',
                        directory/'lwt', directory/'lwt/generic']
            flags = [arg for path in includes for arg in ('-I', str(path))] + ['-I', '+unix', '-I', '+str']
            command([compiler, *flags, '-c', 'census.c'], directory, 'compile-census')
            command([compiler, *flags, '-c', 'fault.ml'], directory, 'compile-fault')
            first = modules.index('lwt/lwt.cmx')
            for obj in modules[first:]:
                stem = Path(obj).with_suffix('')
                interface = stem.with_suffix('.mli')
                if (directory / interface).exists():
                    command([compiler, *flags, '-c', str(interface)], directory, 'compile-' + str(interface).replace('/', '-'))
                source = stem.with_suffix('.ml')
                command([compiler, *flags, '-c', str(source)], directory, 'compile-' + str(source).replace('/', '-'))
            binary = directory / 'runtime-settlement-test'
            command([compiler, *flags, 'unix.cmxa', 'str.cmxa', 'fault.cmx', *modules,
                     'runtimeSettlementTest.ml', *native, 'census.o', '-o', str(binary)], directory, 'link')
            if mode == 'group-negative':
                cases = [('pair', 'normal', 'launch-error', 0, False, 0),
                         ('pair', 'pair-first', 'normal', 1, True, 0)]
            elif mode == 'parent':
                cases = [('runtime', 'runtime-io-map', 'normal', 1, False, 0),
                         ('runtime', 'runtime-io-outer', 'connection', 1, False, 0),
                         ('report', 'report-v0-map', 'close', 1, False, 0),
                         ('report', 'report-borrowed', 'connection', 1, True, 0),
                         ('report', 'report-outer', 'close', 1, True, 0),
                         ('rpc', 'rpc-output-action', 'normal', 1, True, 0)]
            else:
                cases = [('runtime', 'normal', 'normal', 0, False, 0),
                         ('report', 'normal', 'normal', 0, False, 0),
                         ('report', 'normal', 'normal', 0, True, 0),
                         ('loan', 'normal', 'retire', 0, False, 0),
                         ('pair', 'normal', 'normal', 0, True, 0),
                         ('pair', 'normal', 'launch-error', 0, False, 0),
                         ('rpc', 'normal', 'normal', 0, True, 0)]
                for phase in ('runtime-io-map', 'runtime-io-outer', 'runtime-cancellation'):
                    cases += [('runtime', phase, disposition, 2, False, 0)
                              for disposition in ('normal', 'cancel', 'connection')]
                for phase in ('report-v0-map', 'report-borrowed', 'report-outer', 'report-capture'):
                    for meaning in (False, True) if phase != 'report-v0-map' else (False,):
                        cases += [('report', phase, disposition, 2, meaning, 0)
                                  for disposition in ('normal', 'cancel', 'connection', 'close')]
                for phase in ('resource-borrow', 'resource-lease-result', 'runtime-admission-map', 'runtime-admission-catch'):
                    cases += [('loan', phase, 'cancel', 2, False, 0)]
                cases += [('loan', 'resource-borrow', 'retire', 2, False, 0)]
                for phase in ('pair-first', 'pair-second'):
                    cases += [('pair', phase, 'normal', 2, meaning, 0) for meaning in (False, True)]
                cases += [('runtime', 'runtime-io-map', 'cancel', 2, False, 2),
                          ('report', 'report-borrowed', 'close', 2, True, 2),
                          ('pair', 'pair-first', 'normal', 2, True, 2)]
                cases += [('rpc', phase, 'normal', 2, True, 0)
                          for phase in ('rpc-server-map', 'rpc-dispatch', 'rpc-scope', 'rpc-output-action')]
                cases += [('rpc', 'rpc-output-action', 'normal', 2, True, 2)]
                cases += [('runtime', 'runtime-io-map', 'cancel', 1, False, 0),
                          ('report', 'report-v0-map', 'close', 1, False, 0),
                          ('report', 'report-borrowed', 'connection', 1, True, 0),
                          ('loan', 'resource-borrow', 'retire', 1, False, 0),
                          ('pair', 'pair-first', 'normal', 1, True, 0),
                          ('rpc', 'rpc-output-action', 'normal', 1, True, 0)]
            for index, case in enumerate(cases):
                family, phase, disposition, faults, meaning, timers = case
                files = directory / ('case-' + str(index))
                files.mkdir()
                argv = [str(binary), family, phase, disposition, str(faults), 'meaning' if meaning else 'proof']
                if mode != 'fixed':
                    argv.append('negative')
                result, entry = command(argv, files, 'test', expected_failure=mode != 'fixed', timeout=15,
                    extra_env={'UNISON': str(files/'state'), 'UNISON_SETTLEMENT_TIMER_FAULTS': str(timers)})
                if mode != 'fixed':
                    designated = {'runtime': 'DESIGNATED runtime grouped descriptor or active worker loan retired before settlement',
                        'report': 'DESIGNATED report held descriptor or active source loan retired before settlement',
                        'rpc': 'DESIGNATED scoped RPC released Source admission while actual output action remained sleeping',
                        'pair': 'DESIGNATED report pair lost an actual started participant before settlement'}[family]
                    if result.returncode != 2 or designated not in result.stdout:
                        raise RuntimeError('parent hazard missed independent live-FD/admission oracle')
                receipt['runs'].append({'mode': mode, 'family': family, 'phase': phase,
                    'disposition': disposition, 'faults': faults, 'meaning': meaning, 'timer_faults': timers,
                    'execution': entry, 'designated_negative_detected': mode != 'fixed'})
        receipt['workspace_sources_still_match'] = all(
            sha(ROOT/'src'/name) == pin for name, pin in receipt['source_pins'].items())
        receipt['fixture_sources_still_match'] = all(
            sha(ROOT/'tests/runtime_settlement'/name) == pin for name, pin in receipt['test_pins'].items())
        if not receipt['workspace_sources_still_match'] or not receipt['fixture_sources_still_match']:
            raise RuntimeError('production or fixture source changed during qualification')
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)): {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}
            for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work/'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        print('Receipt ' + str(target), flush=True)
        print('Artifacts ' + str(work), flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
