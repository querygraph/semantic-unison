#!/usr/bin/env python3
"""Actual native publication admission, FD census and token handoff faults."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--ocamlopt', required=True)
    ap.add_argument('--keep', action='store_true')
    ap.add_argument('--receipt', type=Path)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    build = args.build.resolve() / 'src'
    text = (build / 'Makefile.OCaml').read_text()
    def objects(name):
        value = re.search(r'^' + name + r' = (.*?)(?=\n\n)', text, re.M | re.S).group(1)
        return value.replace('\\\n', ' ').replace('$(SYSTEM)', 'generic').replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '').replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()
    modules = objects('OCAMLOBJS')
    modules = modules[:modules.index('targetBinding.cmx') + 1]
    native = objects('COBJS')
    production = ['semanticAdmission.ml', 'semanticAdmission.mli', 'semanticRuntime.ml', 'semanticRuntime.mli',
                  'targetBinding.ml', 'targetBinding.mli', 'finalPublication.ml', 'finalPublication.mli',
                  'finalPublication_stubs.c', 'helperSupervisor.ml', 'semanticWorkers.ml', 'semanticFile.ml',
                  'semanticRemote.ml', 'semanticRemote.mli']
    for name in production:
        if sha(root / 'src' / name) != sha(build / name):
            raise RuntimeError('snapshot differs: ' + name)
    work = Path(tempfile.mkdtemp(prefix='unison-resource-lifetime-', dir='/private/tmp'))
    print('artifact_directory', work, flush=True)
    env = os.environ.copy()
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(key, None)
    compiler = str(Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve())
    flags = [arg for directory in [work, build, build/'ubase', build/'system', build/'system/generic', build/'lwt', build/'lwt/generic'] for arg in ['-I', str(directory)]] + ['-I', '+unix', '-I', '+str']
    for name in ('test.ml', 'census.c'):
        shutil.copyfile(root/'tests/resource_lifetime'/name, work/name)
    record = {'schema': 'unison-resource-lifetime-phase-census/0',
              'scope': 'Actual linked TargetBinding/FinalPublication/lazy resource runtime; synthetic native files; phase-boundary FD counts exclude census descriptor. Private one-shot Runtime result faults cover synchronous and queued token handoff. No global exhausted-heap, transient-peak or whole-process hard-FD/RSS claim; no Adobe/Photo invocation.',
              'compiler': compiler, 'compiler_version': subprocess.check_output([compiler, '-version'], text=True).strip(),
              'build_snapshot': str(build.parent), 'artifact_directory': str(work),
              'production_sha256': {name: sha(build/name) for name in production},
              'test_sha256': {name: sha(root/'tests/resource_lifetime'/name) for name in ('run.py','test.ml','census.c')},
              'linked_object_sha256': {name: sha(build/name) for name in modules+native}, 'runs': []}
    try:
        subprocess.run([compiler, *flags, '-c', 'census.c'], cwd=work, env=env, check=True)
        # Private module; no hook or public interface change in production.
        (work/'handoffFault.ml').write_text('''let armed = ref false
let hits = ref 0
let before = ref (fun () -> ())
let arm observer = armed := true; hits := 0; before := observer
let after_result () = if !armed then begin
  armed := false; incr hits; !before (); raise Out_of_memory
end
''')
        subprocess.run([compiler, *flags, '-c', 'handoffFault.ml'], cwd=work, env=env, check=True)
        def link(label, overrides=None):
            overrides = overrides or {}
            binary=work/label
            private_flags = [arg for directory in reversed(list(dict.fromkeys(path.parent for path in overrides.values())))
                             for arg in ['-I', str(directory)]]
            subprocess.run([compiler, *private_flags, *flags, 'unix.cmxa', 'str.cmxa',
                str(work/'handoffFault.cmx'),
                *(str(overrides.get(module, build/module)) for module in modules),
                str(work/'test.ml'), *(str(build/obj) for obj in native), 'census.o', '-o', str(binary)],
                cwd=work, env=env, check=True)
            return binary
        def execute(binary, expected=None, selected='baseline'):
            directory=work/(binary.name+'-'+selected+'-case');directory.mkdir()
            command=[str(binary),selected]
            try:
                result=subprocess.run(command, cwd=directory,
                    env=dict(env, UNISON=str(directory/'state')), capture_output=True, text=True, timeout=20)
            except subprocess.TimeoutExpired as error:
                def decode(value):
                    return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
                (directory/'result.log').write_text(decode(error.stdout)+decode(error.stderr))
                record['timeout']={'binary':str(binary),'log':str(directory/'result.log')}
                raise
            log=directory/'result.log';log.write_text(result.stdout+result.stderr)
            print(result.stdout+result.stderr, end='', flush=True)
            entry={'argv':command, 'selected':selected, 'binary':str(binary), 'binary_sha256':sha(binary), 'exit_code':result.returncode,
                   'log':str(log), 'log_sha256':sha(log), 'expected_rejection':expected,
                   'phase_census': [line for line in result.stdout.splitlines() if line.startswith('CENSUS ')]}
            record['runs'].append(entry)
            if expected:
                if result.returncode!=2 or expected not in result.stderr:
                    raise RuntimeError('private regression missed designated rejection')
            else:
                result.check_returncode()
        execute(link('resource-current'))
        # Restore only premature retirement at the actual producer return.
        name='targetBinding';source=(build/(name+'.ml')).read_text()
        before='    t.phase <- Finalized;\n'
        assert source.count(before)==1
        source=source.replace(before, before+'    (match t.reservation with None -> () | Some r -> SemanticAdmission.retire r);\n')
        early=work/'early';early.mkdir()
        def compile_private(name, source, private):
            (private/(name+'.ml')).write_text(source)
            for suffix in ('.mli','.cmi'):
                original=build/(name+suffix)
                if original.exists():shutil.copyfile(original,private/original.name)
            subprocess.run([compiler,'-I',str(private),*flags,'-c',name+'.ml'],
                           cwd=private,env=env,check=True)
        compile_private(name, source, early)
        record['early_release_mutation_sha256']=sha(early/(name+'.ml'))
        execute(link('resource-early-release', {name+'.cmx':early/(name+'.cmx')}),
                'owned proof FD outlives lease after producer return')
        # Remove inherited borrowing so validation tries another Consumer slot.
        # The minimum-budget test observes non-entry immediately, without sleep.
        name='semanticRuntime';source=(build/(name+'.ml')).read_text()
        before='else SemanticAdmission.with_borrow reservation ~cost guarded'
        assert source.count(before)==1
        source=source.replace(before, 'else (SemanticAdmission.with_lease (resource_gate ()) cancellation ~role ~cost guarded >>= function\n          | Some result -> return result | None -> fail (Util.Transient "cancelled"))')
        # Recompile all later modules against matching native optimization
        # metadata; changing a runtime implementation changes its cmx digest.
        def compile_runtime(label, source):
            private=work/label;private.mkdir()
            compile_private('semanticRuntime',source,private)
            overrides={'semanticRuntime.cmx':private/'semanticRuntime.cmx'}
            for module in modules[modules.index('semanticRuntime.cmx')+1:]:
                stem=Path(module).stem
                compile_private(stem,(build/(stem+'.ml')).read_text(),private)
                overrides[module]=private/module
            return private,overrides
        private,overrides=compile_runtime('nested',source)
        record['nested_gate_mutation_sha256']=sha(private/(name+'.ml'))
        execute(link('resource-nested-gate', overrides),
                'inherited validation deadlocked under source headroom')

        # Fail after real preparation and cancellation cleanup, at the exact
        # success-result allocation boundary that used to lose the native owner.
        source=(build/'semanticRuntime.ml').read_text()
        before='finished := true; cancellations.release cancellation; return result'
        assert source.count(before)==1
        source=source.replace(before,
            'finished := true; cancellations.release cancellation; HandoffFault.after_result (); return result')
        private,overrides=compile_runtime('handoff',source)
        record['handoff_instrumentation_sha256']=sha(private/'semanticRuntime.ml')
        fixed=link('resource-handoff-current',overrides)
        for selected in ('handoff-sync','handoff-async'):
            execute(fixed,selected=selected)

        # Restore only the pre-fix retire-only error continuation; native
        # ownership recording and all other admission/publication guards stay.
        source=(build/'targetBinding.ml').read_text()
        start=source.index('  let retire_error error =\n',source.index('let prepare_admitted '))
        end=source.index('  let prepare_now () =\n',start)
        source=source[:start]+'''  let retire_error error =
    (try SemanticAdmission.retire reservation with _ -> ()); Lwt.fail error in
'''+source[end:]
        lost=work/'handoff-pre-fix';lost.mkdir()
        # TargetBinding must see the instrumented Runtime optimization record.
        for path in private.glob('*.cmx'):
            shutil.copyfile(path,lost/path.name)
        compile_private('targetBinding',source,lost)
        overrides=dict(overrides,**{'targetBinding.cmx':lost/'targetBinding.cmx'})
        record['pre_fix_cleanup_mutation_sha256']=sha(lost/'targetBinding.ml')
        broken=link('resource-handoff-pre-fix',overrides)
        for selected in ('handoff-sync','handoff-async'):
            execute(broken,'DESIGNATED prepared native owner escaped failed token handoff',selected)
        record['status']='PASS_CURRENT_TWO_HANDOFF_FAULTS_THREE_MUTATIONS_FOUR_REJECTIONS'
    finally:
        record.setdefault('status','FAIL_OR_OPEN_GAP')
        artifact={str(path.relative_to(work)):sha(path) for path in sorted(work.rglob('*')) if path.is_file()}
        record['artifact_sha256']=artifact
        (work/'verification.json').write_text(json.dumps(record,indent=2)+'\n')
        if args.receipt:
            args.receipt.parent.mkdir(parents=True,exist_ok=True)
            args.receipt.write_text(json.dumps(record,indent=2)+'\n')
        if not args.keep:
            shutil.rmtree(work)

if __name__=='__main__':
    main()
