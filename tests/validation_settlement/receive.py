#!/usr/bin/env python3
"""Actual Files receiving controls against frozen compiler-matched snapshots.

Private source instrumentation pauses original Identify domains or watches an
already-spawned synthetic child. It never reenters/pumps the legacy owner loop.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'bench/sync'))
from dng_profile_v1_remote import fixture, objects
from ownership import OwnedGroup


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('private source seam no longer unique: ' + old)
    return source.replace(old, new, 1)


def instrument(build):
    path = build / 'src/lwt/lwt.ml'
    source = (HERE / 'receive_fault.ml').read_text() + '\n' + path.read_text()
    source = once(source, 'let add_waiter t f = t.waiters <- f :: t.waiters',
                  'let add_waiter t f = validation_test_waiter (Obj.repr t); t.waiters <- f :: t.waiters')
    path.write_text(source)
    with (build / 'src/lwt/lwt.mli').open('a') as output:
        output.write('''
val validation_test_env : string -> string
val validation_test_phase : unit -> string
val validation_test_log : string list -> unit
val validation_test_ready : unit -> (int * string) list
val validation_test_workers : unit -> string list
val validation_test_set_barrier : (int -> unit) -> unit
val validation_test_watch : string -> string -> 'a t -> 'a t
val validation_test_consume : string -> (unit -> 'a t) -> unit -> 'a t
''')
    path = build / 'src/dngValidation.ml'
    anchor = 'let validate_with_execution ~execute supervisor cancellation ~policy ~(tool : tool option) ~inspect ~candidate ~expected =\n'
    path.write_text(once(path.read_text(), anchor, anchor + '''
  let execute work = Lwt.validation_test_watch "execute" candidate (execute work) in
'''))
    path = build / 'src/semanticWorkers.ml'
    source = (HERE / 'receive_worker.ml').read_text() + '\n' + path.read_text()
    source = once(source, '      | Identify recognizers ->\n',
                  '      | Identify recognizers ->\n        ValidationSettlementWorker.pause job.fd;\n')
    path.write_text(source)
    path = build / 'src/candidateValidation.ml'
    source = path.read_text()
    candidate = '(Fspath.toString (Fspath.concat directory candidate))'
    if 'BorrowedWork.all ~on_error:remember' in source:
        source = once(source, '(List.init count (fun _ -> consume))',
                      '(List.init count (fun _ -> Lwt.validation_test_consume ' + candidate + ' consume))')
    else:
        source = once(source, 'Lwt_util.iter (fun _ -> consume ())',
                      'Lwt_util.iter (fun _ -> Lwt.validation_test_consume ' + candidate + ' consume ())')
    path.write_text(source)
    path = build / 'src/files.ml'
    source = (HERE / 'receive_files.ml').read_text() + '\n' + path.read_text()
    anchor = '       ((localPathTo, workingDir, pathFrom, pathTo), (ui, archOpt, notDefault))) =\n'
    source = once(source, anchor, anchor +
                  '  ValidationSettlementFiles.enter fspathTo localPathTo workingDir pathFrom pathTo;\n')
    source = once(source, '      let discard () =\n        let rejected = Os.tempPath',
                  '      ValidationSettlementFiles.record "quarantine";\n'
                  '      let discard () =\n        let rejected = Os.tempPath')
    source = once(source, '  let copyInfo = prepareCopy workingDir pathTo notDefault in',
                  '  ValidationSettlementFiles.record "precommit";\n'
                  '  let copyInfo = prepareCopy workingDir pathTo notDefault in')
    path.write_text(source)


def trace(path):
    rows = [line.split('\t') for line in path.read_text().splitlines()] if path.exists() else []
    files = []
    for row in rows:
        if row[0] == 'files':
            if len(row) != 16:
                raise AssertionError(('invalid typed private Files trace', row))
            files.append(dict(phase=row[1], candidate=row[2], destination=row[3],
                candidate_exists=row[4] == 'true', destination_sha256=row[5], archive_node_sha256=row[6],
                live_unreaped_pids=[int(pid) for pid in row[7].split(',') if pid],
                cpu=int(row[8]), children=int(row[9]), transactions=int(row[10]),
                payload_bytes=int(row[11]), descriptors=int(row[12]), io_jobs=int(row[13]),
                active_worker_markers=int(row[14]), running_workers=int(row[15])))
    return rows, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--parent-build', type=Path)
    parser.add_argument('--ocamlopt', required=True)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--fixed-only', action='store_true')
    args = parser.parse_args()
    if not args.fixed_only and args.parent_build is None:
        parser.error('--parent-build is required unless --fixed-only')
    compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    environment = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get('PATH', ''))
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(key, None)
    work = Path(tempfile.mkdtemp(prefix='unison-validation-receiving-settlement-', dir='/private/tmp'))
    print('work', work, flush=True)
    receipt = {'schema': 1, 'work': str(work), 'compiler': {'path': str(compiler), 'sha256': sha(compiler)},
               'commands': [], 'cases': [], 'builds': [], 'success': False,
               'Photo_or_Adobe_access': False, 'performance_claim': False,
               'limits': ['private finite source seams; no legacy owner-loop reentry',
                          'actual native child controls separate from Files/directory actual paused Identify domains',
                          'positive descriptor/payload ledger totals are accounting, not a whole-process FD/RSS bound']}

    def command(argv, cwd, label):
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        log = work / (label + '.log'); log.write_text(result.stdout)
        entry = {'argv': [str(word) for word in argv], 'cwd': str(cwd), 'exit': result.returncode,
                 'log': str(log), 'log_sha256': sha(log)}
        receipt['commands'].append(entry)
        result.check_returncode()
        return result.stdout

    def archives(state, path, decoder, label):
        saved = work / label; saved.mkdir()
        results = {}
        for archive in sorted(state.glob('ar*')):
            if len(archive.name) == 34 and all(c in '0123456789abcdef' for c in archive.name[2:]):
                retained = saved / archive.name; shutil.copy2(archive, retained)
                node = json.loads(command([str(decoder), str(retained), path], work,
                                          label + '-' + archive.name))
                results[archive.name] = {'raw_sha256': sha(retained), 'retained': str(retained), 'node': node}
        assert len(results) == 2, results
        return results

    def exercise(mode, binary, decoder, index, phase, policy, action):
        case = work / (mode + '-' + str(index) + '-' + phase); case.mkdir()
        left, right, state = (case / name for name in ('left', 'right', 'state'))
        for path in (left, right, state): path.mkdir()
        owned = case / 'controls'; owned.mkdir()
        helper = owned / 'synthetic-validator.py'
        helper.write_bytes((HERE / 'receive_helper.py').read_bytes()); helper.chmod(0o700)
        helper.with_suffix('.control.json').write_text(json.dumps({'owned': str(owned), 'action': 'pass'}))
        gate = owned / 'release.control'; gate.write_text('baseline release\n')
        (owned / 'release.workers').write_text('baseline release\n')
        old, new = fixture(), fixture(b'two')
        source, target = left / 'renamed.bin', right / 'renamed.bin'
        source.write_bytes(old)
        options = [str(left), str(right), '-batch', '-auto', '-fastcheck', 'false', '-clone', 'off',
            '-maxthreads', '1', '-semanticworkers', '3', '-semanticmaxinflight', '8', '-semanticvolumejobs', '3',
            '-adobevalidate', policy, '-adobevalidator', str(helper), '-adobevalidatorhash', sha(helper),
            '-adobevalidatorbuild', 'validation-settlement-synthetic-1', '-adobevalidatorthreads', '1',
            '-adobevalidatetimeout', '10']
        base_env = dict(environment, UNISON=str(state))
        # Baseline command has its own exact environment; retain it explicitly.
        baseline_log = case / 'baseline.log'
        with baseline_log.open('w') as output:
            baseline = OwnedGroup([str(binary), *options], cwd=case, env=base_env,
                                  stdout=output, stderr=subprocess.STDOUT)
            settled, _ = baseline.finish(timeout=30)
        assert settled['returncode'] == 0 and target.read_bytes() == old, baseline_log.read_text()
        receipt['commands'].append({'argv': [str(binary), *options], 'cwd': str(case),
            'exit': settled['returncode'], 'owned_group': settled, 'log': str(baseline_log), 'log_sha256': sha(baseline_log)})
        before = archives(state, 'renamed.bin', decoder, case.name + '-before')
        bundle_before = archives(state, 'bundle', decoder, case.name + '-bundle-before')
        assert all(entry['node']['kind'] == 'absent' for entry in bundle_before.values())
        assert all(entry['node']['kind'] == 'file' and hashlib.md5(old).hexdigest() in
                   entry['node']['fingerprint'] for entry in before.values()), before
        old_inode = target.stat().st_ino
        for path in owned.iterdir():
            if path.suffix in ('.ready', '.json') and path.name != 'synthetic-validator.control.json':
                if path.name.endswith('.call.json') or path.suffix == '.ready': path.unlink()
        gate.unlink(); (owned / 'release.workers').unlink()
        helper.with_suffix('.control.json').write_text(json.dumps({'owned': str(owned), 'action': action}))
        is_directory = phase.startswith('directory-')
        if is_directory:
            directory = left / 'bundle'; directory.mkdir()
            for name in ('one.dng', 'two.dng', 'three.dng'): (directory / name).write_bytes(new)
        else:
            source.write_bytes(new)
        trace_path = case / 'fault-trace.tsv'
        env = dict(base_env, UNISON_VALIDATION_TEST_OWNED=str(owned),
            UNISON_VALIDATION_TEST_PHASE=phase, UNISON_VALIDATION_TEST_TRACE=str(trace_path),
            UNISON_VALIDATION_TEST_ROOT=str(right))
        log = case / 'fault.log'
        observation = {}
        with log.open('w') as output:
            child = OwnedGroup([str(binary), *options], cwd=case, env=env, stdout=output, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 10
                while True:
                    rows, entries = trace(trace_path)
                    if any(row[0] == 'injected' for row in rows): break
                    if child.terminal() or time.monotonic() >= deadline:
                        raise AssertionError('actual receiving fault was not reached: ' + log.read_text())
                    time.sleep(.005)
                time.sleep(.03)
                rows, entries = trace(trace_path)
                active_count = 2 if is_directory else 1
                at_fault = [entry for entry in entries if entry['phase'] == 'fault-before']
                assert at_fault, rows
                if phase == 'execute':
                    assert len(at_fault[0]['live_unreaped_pids']) == 1, at_fault
                else:
                    assert at_fault[0]['active_worker_markers'] >= active_count and at_fault[0]['running_workers'] >= active_count, at_fault
                premature = [entry for entry in entries if entry['phase'] in ('quarantine', 'precommit') and
                    (entry['live_unreaped_pids'] or entry['active_worker_markers'])]
                if mode == 'parent':
                    deadline = time.monotonic() + 2
                    while not premature and time.monotonic() < deadline:
                        time.sleep(.005); rows, entries = trace(trace_path)
                        premature = [entry for entry in entries if entry['phase'] in ('quarantine', 'precommit') and
                            (entry['live_unreaped_pids'] or entry['active_worker_markers'])]
                    assert premature, ('parent did not fail designated Files/aggregate active-work oracle', rows)
                    observation['designated_premature_files_action'] = premature
                else:
                    assert not child.terminal() and not premature, entries
                    assert target.read_bytes() == old and target.stat().st_ino == old_inode
                    assert not is_directory or not (right / 'bundle').exists()
                    assert all(entry['candidate_exists'] for entry in at_fault)
                    assert all(entry['transactions'] > 0 and entry['cpu'] > 0 and entry['io_jobs'] > 0 for entry in at_fault)
                    if phase != 'execute':
                        observed = []
                        for marker in sorted(owned.glob('*.worker')):
                            identity = tuple(map(int, marker.read_text().strip().split(':')))
                            assert len(identity) == 3
                            candidates = set()
                            for entry in at_fault:
                                candidate = Path(entry['candidate'])
                                paths = candidate.rglob('*') if candidate.is_dir() else [candidate]
                                for path in paths:
                                    if path.is_file():
                                        st = path.stat(); candidates.add((st.st_dev, st.st_ino, st.st_size))
                            assert identity in candidates, ('actual worker FD identity did not bind private candidate', identity, candidates)
                            observed.append({'marker': str(marker), 'identity': identity})
                        assert len(observed) >= active_count
                        observation['actual_worker_identity_bindings'] = observed
                    observation['held_before_release'] = at_fault
                    observation['original_live_bytes_and_inode_preserved_while_work_active'] = True
                gate.write_text('release children\n'); (owned / 'release.workers').write_text('release original workers\n')
                settled, _ = child.finish(timeout=30)
            finally:
                gate.write_text('cleanup release\n'); (owned / 'release.workers').write_text('cleanup workers\n')
                if not child.reaped: child.finish(cancel_reason='fixture exception')
        rows, entries = trace(trace_path)
        final_actions = [entry for entry in entries if entry['phase'] in ('quarantine', 'precommit')]
        succeeds = phase == 'execute' and policy == 'warn' and action == 'pass'
        if mode == 'fixed':
            assert (settled['returncode'] == 0) == succeeds, log.read_text()
            assert final_actions and all(not entry['live_unreaped_pids'] and entry['active_worker_markers'] == 0
                                         and entry['running_workers'] == 0 for entry in final_actions), entries
            if succeeds:
                assert target.read_bytes() == new
            else:
                assert target.read_bytes() == old and target.stat().st_ino == old_inode
                assert not is_directory or not (right / 'bundle').exists()
        after = archives(state, 'renamed.bin', decoder, case.name + '-after')
        bundle_after = archives(state, 'bundle', decoder, case.name + '-bundle-after')
        if mode == 'fixed' and not succeeds:
            assert all(after[name]['node']['fingerprint'] == before[name]['node']['fingerprint'] for name in before)
            observation['typed_original_archive_fingerprints_preserved'] = True
            observation['archive_container_bytes_identical'] = all(
                after[name]['raw_sha256'] == before[name]['raw_sha256'] for name in before)
            if is_directory:
                assert all(bundle_after[name]['node']['kind'] == 'absent' and
                           bundle_after[name]['node']['node_sha256'] == bundle_before[name]['node']['node_sha256']
                           for name in bundle_before)
                observation['candidate_directory_archive_node_remained_absent'] = True
            for observed in observation.get('actual_worker_identity_bindings', []):
                marker = Path(observed['marker'])
                assert tuple(map(int, Path(str(marker) + '.done').read_text().strip().split(':'))) == observed['identity']
                observed['fresh_native_fstat_after_gate_identical'] = True
        receipt['commands'].append({'argv': [str(binary), *options], 'cwd': str(case), 'exit': settled['returncode'],
            'owned_group': settled, 'log': str(log), 'log_sha256': sha(log), 'test_environment':
            {key: value for key, value in env.items() if key.startswith('UNISON')}})
        receipt['cases'].append({'mode': mode, 'phase': phase, 'policy': policy, 'action': action,
            'directory': is_directory, 'observation': observation, 'trace': rows, 'typed_files_events': entries,
            'archives_before': before, 'archives_after': after, 'exit': settled['returncode']})
        receipt['cases'][-1]['candidate_directory_archives'] = {'before': bundle_before, 'after': bundle_after}
        if mode == 'fixed' and not succeeds:
            helper.write_bytes((HERE / 'receive_helper.py').read_bytes()); helper.chmod(0o700)
            helper.with_suffix('.control.json').write_text(json.dumps({'owned': str(owned), 'action': 'pass'}))
            retry_log = case / 'retry.log'
            with retry_log.open('w') as output:
                retry = OwnedGroup([str(binary), *options], cwd=case, env=base_env,
                                   stdout=output, stderr=subprocess.STDOUT)
                retry_settled, _ = retry.finish(timeout=30)
            assert retry_settled['returncode'] == 0, retry_log.read_text()
            assert target.read_bytes() == (old if is_directory else new)
            if is_directory:
                assert {path.name: path.read_bytes() for path in (right / 'bundle').iterdir()} == {
                    name: new for name in ('one.dng', 'two.dng', 'three.dng')}
            receipt['commands'].append({'argv': [str(binary), *options], 'cwd': str(case),
                'exit': retry_settled['returncode'], 'owned_group': retry_settled,
                'log': str(retry_log), 'log_sha256': sha(retry_log)})
            receipt['cases'][-1]['exact_retry_after_rejection'] = True

    try:
        receipt['compiler']['version'] = command([str(compiler), '-version'], work, 'compiler-version').strip()
        modes = [('fixed', args.build.resolve())] if args.fixed_only else [('parent', args.parent_build.resolve()), ('fixed', args.build.resolve())]
        for mode, snapshot in modes:
            build = work / (mode + '-build'); shutil.copytree(snapshot, build)
            before = {str(path.relative_to(build)): sha(path) for path in build.rglob('*')
                      if path.is_file() and path.suffix in ('.ml', '.mli', '.c')}
            if mode == 'parent':
                parent = '2059949975ae95e64df74a3056d7211101aa42b6'
                names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', parent, 'src/'],
                                                cwd=ROOT, text=True).splitlines()
                checked = {}
                for name in names:
                    if Path(name).suffix in ('.ml', '.mli', '.c'):
                        data = subprocess.check_output(['git', 'show', parent + ':' + name], cwd=ROOT)
                        digest = hashlib.sha256(data).hexdigest()
                        assert sha(snapshot / name) == digest, ('parent snapshot source drift', name)
                        checked[name] = digest
                receipt['parent_tracked_production_source_verification'] = {
                    'commit': parent, 'inputs': checked, 'checks': len(checked)}
            instrument(build)
            modified = {str(path.relative_to(build)): sha(path) for path in build.rglob('*')
                        if path.is_file() and path.suffix in ('.ml', '.mli', '.c') and
                        before.get(str(path.relative_to(build))) != sha(path)}
            command(['make', '-C', str(build / 'src'), 'tui', '-j2', 'NATIVE=true',
                     'TOOL_PREFIX=' + str(compiler.parent) + '/'], work, mode + '-rebuild')
            compiled = snapshot / 'src'; makefile = (compiled / 'Makefile.OCaml').read_text()
            modules = objects(makefile, 'OCAMLOBJS'); modules = modules[:modules.index('update.cmx') + 1]
            flags = [word for path in (compiled, compiled / 'ubase', compiled / 'system', compiled / 'system/generic',
                                      compiled / 'lwt', compiled / 'lwt/generic') for word in ('-I', str(path))]
            flags += ['-I', '+unix', '-I', '+str']
            decoder_directory = work / (mode + '-decoder'); decoder_directory.mkdir()
            decoder_source = decoder_directory / 'archive_node.ml'
            decoder_source.write_bytes((HERE / 'archive_node.ml').read_bytes())
            decoder = work / (mode + '-archive-node')
            decoder_inputs = [compiled / name for name in modules + objects(makefile, 'COBJS')]
            command([str(compiler), *flags, 'unix.cmxa', 'str.cmxa', *[str(compiled / name) for name in modules],
                str(decoder_source), *[str(compiled / name) for name in objects(makefile, 'COBJS')], '-o', str(decoder)],
                work, mode + '-archive-link')
            receipt['builds'].append({'mode': mode, 'snapshot': str(snapshot), 'original_input_pins': before,
                'private_modified_inputs': modified, 'binary': {'path': str(build / 'src/unison'), 'sha256': sha(build / 'src/unison')},
                'decoder_inputs': {str(path): sha(path) for path in decoder_inputs}})
            cases = [('files-validation', 'warn', 'pass'), ('directory-join', 'require', 'pass')]
            if mode == 'fixed':
                cases += [('directory-launch', 'require', 'pass')]
            for index, case in enumerate(cases): exercise(mode, build / 'src/unison', decoder, index, *case)
        receipt['success'] = True
    finally:
        receipt['fixture_pins'] = {str(path.relative_to(ROOT)): sha(path) for path in HERE.iterdir() if path.is_file()}
        receipt['artifacts'] = {str(path.relative_to(work)): {'bytes': path.stat().st_size, 'sha256': sha(path)}
                               for path in sorted(work.rglob('*')) if path.is_file()}
        target = args.receipt.resolve() if args.receipt else work / 'receipt.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2) + '\n')
        print('receipt', target, 'success', receipt['success'], flush=True)


if __name__ == '__main__':
    main()
