#!/usr/bin/env python3
"""Frozen-source whole-clone qualification; private fixtures only, no benchmarks."""
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
HERE = Path(__file__).resolve().parent
DEFAULT_PARENT = '330d04829c43f6a19f6d5af1a95cf3ea24d24635'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('private anchor must occur exactly once: ' + old)
    return text.replace(old, new)


def objects(text, name):
    match = re.search(r'^' + name + r' = (.*?)(?=\n\n)', text, re.M | re.S)
    if not match:
        raise RuntimeError('missing Make object list: ' + name)
    body = match.group(1).replace('\\\n', ' ').replace('$(SYSTEM)', 'generic')
    body = body.replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '')
    return body.replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()


HOOK = r'''
module WholeFileClone = WholeFileCloneForTest
module WholeCloneForTest = struct
  module W = WholeFileClone
  let file_calls = ref []
  let path_calls = ref []
  let range_calls = ref 0
  let legacy_file_calls = ref 0
  let legacy_path_calls = ref 0
  let poison_legacy = ref true
  let file_hook = ref (fun ~expected_length _ _ ->
    W.platform_decline ~expected_length)
  let path_hook = ref FsForTest.clone_path_status
  let legacy_file_hook : (Unix.file_descr -> Unix.file_descr -> bool) ref =
    ref (fun _ _ -> false)
  let compatibility_open = ref false
end
module Fs = struct
  include FsForTest
  let openfile path flags permission =
    if !(WholeCloneForTest.compatibility_open) && List.mem Unix.O_EXCL flags then
      raise (Unix.Unix_error(Unix.EOPNOTSUPP,"private O_EXCL decline",Fspath.toString path));
    FsForTest.openfile path flags permission
  let clone_file source destination =
    incr WholeCloneForTest.legacy_file_calls;
    if !(WholeCloneForTest.poison_legacy) then
      failwith "DESIGNATED legacy boolean FD API reached";
    !(WholeCloneForTest.legacy_file_hook) source destination
  let clone_path _ _ =
    incr WholeCloneForTest.legacy_path_calls;
    failwith "DESIGNATED legacy boolean path API reached"
  let clone_file_status ~expected_length source destination =
    WholeCloneForTest.file_calls :=
      (expected_length,Unix.LargeFile.lseek source 0L Unix.SEEK_CUR,
       Unix.LargeFile.lseek destination 0L Unix.SEEK_CUR)::
      !(WholeCloneForTest.file_calls);
    !(WholeCloneForTest.file_hook) ~expected_length source destination
  let clone_path_status ~expected_length source destination =
    WholeCloneForTest.path_calls := (expected_length,source,destination)::
      !(WholeCloneForTest.path_calls);
    !(WholeCloneForTest.path_hook) ~expected_length source destination
  let copy_file_status _ _ _ _ =
    incr WholeCloneForTest.range_calls;
    (1,0,0,0,None,0,1,0L)
end
module StagePublication = struct
  include StagePublication
  let adopt publication ~parent ~stage =
    StagePublication.adopt publication ~parent ~stage;
    Fault.checkpoint "copy-after-adopt"
  let publish publication =
    StagePublication.publish publication;
    Fault.checkpoint "copy-after-publish"
end
'''


def instrument_fs(text):
    text = 'module WholeFileClone = WholeFileCloneForTest\n' + text
    text = once(text, 'source_fd := source; source_owned := true;',
        'source_fd := source; source_owned := true; Fault.source := Some source;')
    text = once(text, 'parent_fd := parent; parent_owned := true;',
        'parent_fd := parent; parent_owned := true; Fault.parent := Some parent;')
    text = once(text,
        '(System.whole_clone_run_named source parent expected_length owner)',
        '(let raw = System.whole_clone_run_named source parent expected_length owner in\n'
        '         Fault.checkpoint_no_raise "after-run-observe";\n'
        '         Fault.checkpoint "after-run"; raw)')
    text = once(text, 'let output = System.whole_clone_peek_named_output owner in',
        'let output = System.whole_clone_peek_named_output owner in\n'
        '          Fault.output := Some output; Fault.checkpoint "after-peek";')
    text = once(text, 'let result = Created_path (receipt, output, parent) in',
        'let result = Created_path (receipt, output, parent) in\n'
        '          Fault.checkpoint "after-result";')
    text = once(text, 'decode_cleanup (System.whole_clone_finish_named owner);',
        'Fault.checkpoint "before-finish";\n'
        '          decode_cleanup (System.whole_clone_finish_named owner);\n'
        '          Fault.checkpoint "after-finish";')
    text = once(text, 'System.whole_clone_transfer_named_output owner output_fd output_owned;',
        'Fault.checkpoint "before-transfer";\n'
        '          System.whole_clone_transfer_named_output owner output_fd output_owned;\n'
        '          Fault.checkpoint "after-transfer";')
    # Instrument the real native slot-close call, never a replacement owner.
    text = once(text, 'System.whole_clone_close_slot descriptor owned',
        'let was_owned = !owned in\n'
        '        if was_owned && descriptor == source_fd then Fault.before_close ();\n'
        '        if was_owned && descriptor == source_fd && !(Fault.phase)="pending-source-close"\n'
        '        then Fault.probe_close_slot descriptor owned\n'
        '        else System.whole_clone_close_slot descriptor owned;\n'
        '        if was_owned && descriptor == source_fd then begin\n'
        '          Fault.checkpoint "after-source-close" end')
    return text


def instrument_native(text):
    text = ('#include <signal.h>\nextern int whole_fixture_mode;\n'
            'extern void whole_fixture_raise_primary(void);\n') + text
    text = once(text,
        'ctx->output = openat(parent, ctx->leaf,\n                       O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);',
        'ctx->output = whole_fixture_mode == 2 ? (errno = EIO, -1) :\n'
        '    openat(parent, ctx->leaf, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);')
    text = once(text, 'ctx->backup = fcntl(ctx->output, F_DUPFD_CLOEXEC, 0);',
        'ctx->backup = whole_fixture_mode == 3 ? (errno = EMFILE, -1) :\n'
        '    fcntl(ctx->output, F_DUPFD_CLOEXEC, 0);')
    text = once(text, '  caml_acquire_runtime_system();\n  CAMLreturn(wf_raw(receipt));',
        '  if (whole_fixture_mode == 1 && receipt.status == WF_SHARED)\n'
        '    kill(getpid(), SIGUSR1);\n'
        '  caml_acquire_runtime_system();\n'
        '  if (whole_fixture_mode == 1) {\n'
        '    caml_process_pending_actions(); whole_fixture_raise_primary();\n'
        '  }\n'
        '  CAMLreturn(wf_raw(receipt));')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--parent', default=DEFAULT_PARENT)
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--fixed-only', action='store_true')
    args = parser.parse_args()
    build = args.build.resolve() / 'src'
    freeze = json.loads(args.freeze.read_text())
    for name, digest in freeze['sources'].items():
        if sha(ROOT / name) != digest or sha(args.build.resolve() / name) != digest:
            raise RuntimeError('production workspace/build differs from freeze: ' + name)
    makefile = (build / 'Makefile.OCaml').read_text()
    modules = objects(makefile, 'OCAMLOBJS')
    modules = modules[:modules.index('copy.cmx')]
    native = [build / name for name in objects(makefile, 'COBJS')]
    flags = [flag for path in [build, build/'lwt', build/'ubase', build/'system',
                               build/'system/generic', build/'lwt/generic']
             for flag in ['-I', str(path)]] + ['-I', '+unix', '-I', '+str']
    env = os.environ.copy()
    for name in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(name, None)
    work = Path(tempfile.mkdtemp(prefix='unison-whole-clone-', dir='/private/tmp'))
    commands = []
    receipt = {'schema':'unison-whole-clone-qualification/1', 'success':False,
        'work':str(work), 'retained':args.keep_work, 'production_build':str(build.parent),
        'freeze':{'path':str(args.freeze.resolve()),'sha256':sha(args.freeze)},
        'source_pins':freeze['sources'], 'fixture_pins':{
            path.name:sha(path) for path in sorted(HERE.iterdir()) if path.is_file()},
        'commands':commands, 'cases':[], 'Photo_or_Adobe_access':False,
        'physical_sharing_measured':False, 'benchmarks':False}

    def run(command, label, allow_failure=False, timeout=120, quiet=False):
        label = str(len(commands)).zfill(3) + '-' + label
        command = [str(item) for item in command]
        # Mutable private module names are reused for exact-parent and single-
        # predicate controls. Save the actual bytes consumed by each command,
        # including paired CMIs, before another trial can overwrite them.
        captured = {}
        for argument in command[1:]:
            item = Path(argument)
            if item.is_absolute() or item.suffix not in ('.ml','.c','.cmx','.cmi','.o'):
                continue
            for candidate in (work/item, (work/item).with_suffix('.cmi')):
                if not candidate.is_file():
                    continue
                target = work/'command-inputs'/label/candidate.name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(candidate,target)
                captured[candidate.name]={'path':str(target),'sha256':sha(target)}
        result = subprocess.run(command, cwd=work, env=env, capture_output=True,
                                text=True, timeout=timeout)
        log = work / (label + '.log')
        log.write_text(result.stdout + result.stderr)
        commands.append({'argv':command, 'cwd':str(work), 'exit':result.returncode,
                         'log':str(log), 'log_sha256':sha(log),'private_inputs':captured})
        if not quiet:
            print(result.stdout, end='', flush=True)
        print(result.stderr, end='', flush=True)
        if not allow_failure:
            if result.returncode:
                raise RuntimeError('command failed: ' + label + '; retained log ' + str(log))
        return result

    def compile_ml(name):
        run([args.ocamlopt,*flags,'-c',name], 'compile-' + name)

    def link(main, output, extra=(), native_faults=False):
        chosen_native = ([path for path in native if path.name!='wholeFileClone_stubs.o']
                         + ['wholeFileCloneForTest_stubs.o']) if native_faults else native
        run([args.ocamlopt,*flags,'unix.cmxa','str.cmxa',
             *[build/name for name in modules],
             'fault.cmx','wholeCommon.cmx','wholeFileCloneForTest.cmx','fsForTest.cmx',
             *extra,main,*chosen_native,
             'native_fixture_stubs.o','census.o','-o',output],
             'link-' + output)

    def case(binary, label, selected=None, expected_failure=None):
        fixture = work / ('fixture-' + label)
        fixture.mkdir()
        result = run([work/binary,fixture,*([selected] if selected else [])],
                     label, allow_failure=bool(expected_failure))
        if expected_failure:
            if result.returncode == 0 or expected_failure not in result.stderr:
                raise RuntimeError('designated independent negative did not fail: ' + label)
        receipt['cases'].append({'name':label,'groups':sum(
            line.startswith('PASS ') for line in result.stdout.splitlines()),
            'expected_failure':expected_failure,'observed_exit':result.returncode})

    try:
        (work/'state').mkdir()
        env['UNISON'] = str(work/'state')
        compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
        receipt['compiler'] = {'path':str(compiler),'sha256':sha(compiler),
            'version':run([args.ocamlopt,'-version'],'compiler-version').stdout.strip()}
        receipt['linked_objects'] = {str(path):sha(path) for path in
                                    [*[build/name for name in modules],*native]}
        for name in ('fault.ml','wholeCommon.ml','unit.ml','native.ml','caller.ml',
                     'native_fixture_stubs.c','settlement.ml','pathCaller.ml'):
            source = HERE/name
            if source.exists():
                shutil.copy2(source,work/name)
        shutil.copy2(ROOT/'tests/resource_lifetime/census.c',work/'census.c')
        (work/'fsForTest.ml').write_text(instrument_fs((build/'fs.ml').read_text()))
        (work/'wholeFileCloneForTest.ml').write_text((build/'wholeFileClone.ml').read_text())
        (work/'wholeFileCloneForTest_stubs.c').write_text(
            instrument_native((build/'wholeFileClone_stubs.c').read_text()))
        for name in ('native_fixture_stubs.c','census.c','wholeFileCloneForTest_stubs.c'):
            run([args.ocamlopt,*flags,'-c',name], 'compile-' + name)
        for name in ('fault.ml','wholeCommon.ml','wholeFileCloneForTest.ml','fsForTest.ml'):
            compile_ml(name)
        run([args.ocamlopt,*flags,'unix.cmxa','wholeCommon.cmx',build/'wholeFileClone.cmx',
             'unit.ml','-o','unit-test'],'link-unit')
        case('unit-test','unit')
        (work/'native.ml').write_text('module Fs = FsForTest\nmodule WholeFileClone = WholeFileCloneForTest\n'
                                    + (work/'native.ml').read_text())
        link('native.ml','native-test')
        case('native-test','native')
        if (work/'settlement.ml').exists():
            link('settlement.ml','settlement-test',native_faults=True)
            case('settlement-test','named-settlement')
        current = HOOK + (build/'copy.ml').read_text()
        (work/'copyForTest.ml').write_text(current)
        compile_ml('copyForTest.ml')
        link('caller.ml','caller-test',('copyForTest.cmx',))
        case('caller-test','caller','current')
        if (work/'pathCaller.ml').exists():
            link('pathCaller.ml','path-caller-test',('copyForTest.cmx',))
            case('path-caller-test','path-caller')
        if not args.fixed_only:
            parent = run(['git','-C',ROOT,'show',args.parent+':src/copy.ml'],
                         'read-exact-parent',quiet=True).stdout
            (work/'parent-copy.ml').write_text(parent)
            receipt['parent_negative'] = {'commit':args.parent,
                'source_sha256':sha(work/'parent-copy.ml'),
                'scope':'exact parent Copy caller with current support/native objects; not a full parent binary'}
            adapter = '\nlet copyFile ?clone_owned:_ = copyFile\n'
            (work/'copyForTest.ml').write_text(HOOK+parent+adapter)
            compile_ml('copyForTest.ml')
            link('caller.ml','parent-caller-test',('copyForTest.cmx',))
            for selected,oracle in (
                ('parent-cursor','DESIGNATED whole clone left cached/native output cursor before EOF'),
                ('parent-length','DESIGNATED whole clone accepted wrong expected EOF'),
                ('parent-error','DESIGNATED failed clone authorized ordinary fallback after unknown effects')):
                case('parent-caller-test',selected,selected,oracle)
            # One changed predicate in the copied decoder; the independent
            # caller oracle counts new work and inspects the unknown extra byte.
            mutated = once((build/'wholeFileClone.ml').read_text(),
                'if r.completed <> 0L || r.mutation <> No_effect ||\n          not (decline_consistent scope r) then',
                'if r.completed <> 0L ||\n          not (decline_consistent scope r) then')
            (work/'wholeFileCloneForTest.ml').write_text(mutated)
            compile_ml('wholeFileCloneForTest.ml')
            compile_ml('fsForTest.ml')
            (work/'copyForTest.ml').write_text(current)
            compile_ml('copyForTest.ml')
            link('caller.ml','mutation-caller-test',('copyForTest.cmx',))
            case('mutation-caller-test','negative-decline-effects','negative-decline-effects',
                 'DESIGNATED indeterminate decline authorized fallback or erased extra effect')
            # Revert only the slot-close operation to its old clear/Unix.close
            # sequence. The real queued signal and fcntl oracle must observe
            # the disarmed-yet-open facade source before the Unix native close.
            (work/'wholeFileCloneForTest.ml').write_text((build/'wholeFileClone.ml').read_text())
            compile_ml('wholeFileCloneForTest.ml')
            private_fs = instrument_fs((build/'fs.ml').read_text())
            private_fs = once(private_fs, 'Fault.probe_close_slot descriptor owned',
                'Fault.legacy_probe_close_slot descriptor owned')
            (work/'fsForTest.ml').write_text(private_fs)
            compile_ml('fsForTest.ml')
            link('settlement.ml','old-close-settlement-test',native_faults=True)
            case('old-close-settlement-test','negative-old-close',None,
                 'DESIGNATED pending exception escaped after disarming a live source FD')
        receipt['success'] = True
    finally:
        receipt['artifacts'] = {str(path.relative_to(work)):{'path':str(path),
            'bytes':path.stat().st_size,'sha256':sha(path)}
            for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work/'receipt.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        print('Receipt',target,'artifacts',work,flush=True)
        if not args.keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    main()
