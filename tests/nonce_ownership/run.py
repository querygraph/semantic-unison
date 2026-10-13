#!/usr/bin/env python3
"""Test the exact SemanticRemote nonce function with private Unix/Bytes shims."""
import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ORIGINAL_COMMIT = 'e9be473'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract(source):
    match = re.search(rb'^let nonce \(\) =\n.*?(?=^let [A-Za-z_])', source,
                      re.MULTILINE | re.DOTALL)
    assert match is not None
    return match.group(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--negative-control', choices=('original-constructor', 'unchecked-close'))
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(key, None)
    current = (root / 'src/semanticRemote.ml').read_bytes()
    original_commit = subprocess.check_output(['git', 'rev-parse', ORIGINAL_COMMIT], cwd=root, text=True).strip()
    original = subprocess.check_output(['git', 'show', original_commit + ':src/semanticRemote.ml'], cwd=root)
    current_nonce = extract(current)
    original_nonce = extract(original)
    directory = (nullcontext(tempfile.mkdtemp(prefix='unison-nonce-ownership-', dir='/private/tmp'))
                 if args.keep_work else
                 tempfile.TemporaryDirectory(prefix='unison-nonce-ownership-', dir='/private/tmp'))
    with directory as tmp:
        work = Path(tmp)
        print('work', work, flush=True)
        pins = {'src/semanticRemote.ml': sha(current)}
        for name in ('tests/nonce_ownership/harness.ml', 'tests/nonce_ownership/test.ml',
                     'tests/nonce_ownership/run.py'):
            data = (root / name).read_bytes()
            pins[name] = sha(data)
            (work / Path(name).name).write_bytes(data)
        (work / 'semanticRemote-current.ml').write_bytes(current)
        (work / 'semanticRemote-original.ml').write_bytes(original)
        (work / 'nonce-current.ml').write_bytes(current_nonce)
        (work / 'nonce-original.ml').write_bytes(original_nonce)
        selected = 'all'
        expected_failure = None
        body = current_nonce
        if args.negative_control == 'original-constructor':
            body = original_nonce
            selected = 'constructor-oom-pre-open'
            expected_failure = 'constructor OOM opened random fd'
        elif args.negative_control == 'unchecked-close':
            anchor = b'let close fd = if !owned then begin owned := false; Unix.close fd end in'
            assert body.count(anchor) == 1
            body = body.replace(anchor, b'let close fd = Unix.close fd in', 1)
            selected = 'close-eio-reused-number'
            expected_failure = 'nonce performed repeated native close on the reused number'
        prefix = b'module Unix = Harness.Unix\nmodule Bytes = Harness.Bytes\nmodule Util = Harness.Util\n\n'
        (work / 'nonceFunction.ml').write_bytes(prefix + body)
        commands = []
        with (work / 'build.log').open('w') as log:
            for module in ('harness.ml', 'nonceFunction.ml'):
                command = [compiler, '-I', '+unix', '-c', module]
                commands.append(command)
                subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            command = [compiler, '-I', '+unix', 'unix.cmxa', 'harness.cmx', 'nonceFunction.cmx',
                       'test.ml', '-o', 'nonce-test']
            commands.append(command)
            subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        command = [str(work / 'nonce-test'), str(work), selected]
        with (work / 'test.log').open('w') as log:
            result = subprocess.run(command, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=15)
        output = (work / 'test.log').read_text()
        accepted = (result.returncode != 0 and expected_failure in output
                    if args.negative_control else result.returncode == 0)
        if args.negative_control == 'original-constructor':
            accepted = accepted and 'opens=1' in output and 'random_alive=true' in output
        elif args.negative_control == 'unchecked-close':
            accepted = accepted and 'actual_closes=2' in output and 'reused=true sentinel_alive=false' in output
        if args.negative_control:
            accepted = accepted and ('CLEAN ' + selected + ' owned_flags_clear=true '
                                      'random_number_closed=true sentinel_number_closed=true') in output
        verification = {
            'scope': 'Exact extracted production nonce with private module aliases and Unix/Bytes fault shims; actual OS random descriptors and synthetic sentinel files only.',
            'compiler': compiler,
            'compiler_resolved': str(Path(compiler).resolve()),
            'compiler_sha256': sha(Path(compiler).read_bytes()),
            'compiler_version': subprocess.check_output([compiler, '-version'], env=env, text=True).strip(),
            'source_pins': pins,
            'original_commit': original_commit,
            'original_source_sha256': sha(original),
            'current_nonce_sha256': sha(current_nonce),
            'original_nonce_sha256': sha(original_nonce),
            'compiled_nonce_body_sha256': sha(body),
            'exact_current_function': body == current_nonce,
            'exact_original_function': body == original_nonce,
            'module_alias_prefix_sha256': sha(prefix),
            'build_commands': commands,
            'test_command': command,
            'build_exit': 0,
            'test_exit': result.returncode,
            'negative_control': args.negative_control,
            'expected_failure': expected_failure,
            'accepted': accepted,
            'pass_groups': sum(line.startswith('PASS ') for line in output.splitlines()),
            'observations': [line for line in output.splitlines() if line.startswith('OBS ')],
            'fixture_cleanup': [line for line in output.splitlines() if line.startswith('CLEAN ')],
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
