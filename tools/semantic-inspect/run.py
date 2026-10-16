#!/usr/bin/env python3
"""Build the read-only inspector; optionally retain it without executing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--report', type=Path)
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ['--']:
        forwarded = forwarded[1:]
    if args.build_only and (not args.report or forwarded):
        parser.error('--build-only requires --report and forbids inspector arguments')
    if args.report and not args.build_only:
        parser.error('--report is currently a build-only receipt')
    executable = shutil.which(args.ocamlopt)
    if executable is None:
        parser.error('compiler not found')
    compiler = Path(executable).absolute()
    root = Path(__file__).resolve().parents[2]
    modules = ['semanticHash', 'semanticFile', 'formatExtension', 'xmpObservation', 'xmpMerge',
               'dngSemantic', 'dngExtended', 'semanticDelta']
    sources = [Path('src') / (name + suffix) for name in modules for suffix in ('.ml', '.mli')]
    sources += [Path('src/semanticHash_stubs.c'), Path('src/semanticFile_stubs.c'),
                Path('tools/semantic-inspect/inspect.ml')]
    report = None
    temporary = None
    try:
        if args.report:
            report = os.fdopen(os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                       | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600), 'w')
            build = Path(tempfile.mkdtemp(prefix='unison-semantic-inspect-retained-'))
        else:
            temporary = tempfile.TemporaryDirectory(prefix='unison-semantic-inspect-')
            build = Path(temporary.name)
        pins = {}
        for relative in sources:
            source = root / relative
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            (build / relative.name).write_bytes(data)
            if sha(source) != digest:
                raise RuntimeError('source changed while snapshotting: ' + str(relative))
            pins[str(relative)] = digest
        receipt = {'schema': 'unison-semantic-inspector-build/1', 'complete': False,
                   'build_only': args.build_only, 'inspector_executions': 0,
                   'workspace': str(build), 'compiler': str(compiler),
                   'compiler_sha256': sha(compiler), 'source_sha256': pins,
                   'runner_sha256': sha(Path(__file__).resolve()), 'build_exit': None}
        def save():
            raw = json.dumps(receipt, indent=2) + '\n'
            (build / 'build-receipt.json').write_text(raw)
            if report:
                report.seek(0)
                report.write(raw)
                report.truncate()
                report.flush()
                os.fsync(report.fileno())
        save()
        command = [str(compiler), '-I', '+unix', 'unix.cmxa',
                   'semanticHash_stubs.c', 'semanticFile_stubs.c']
        for name in modules:
            command += [name + '.mli', name + '.ml']
        command += ['inspect.ml', '-o', 'semantic-inspect']
        receipt['command'] = command
        with (build / 'build.log').open('x') as log:
            result = subprocess.run(command, cwd=build, stdout=log, stderr=subprocess.STDOUT)
        receipt['build_exit'] = result.returncode
        receipt['build_log_sha256'] = sha(build / 'build.log')
        if sha(compiler) != receipt['compiler_sha256']:
            receipt['failure'] = 'compiler changed during build'
            save()
            raise RuntimeError(receipt['failure'])
        if any(sha(root / name) != digest for name, digest in pins.items()):
            receipt['failure'] = 'source changed during build'
            save()
            raise RuntimeError(receipt['failure'])
        if result.returncode:
            save()
            print((build / 'build.log').read_text(), end='')
            return result.returncode
        binary = build / 'semantic-inspect'
        receipt.update(binary=str(binary), binary_sha256=sha(binary), complete=True)
        save()
        if args.build_only:
            print('Retained inspector build: ' + str(build), flush=True)
            print('Receipt: ' + str(args.report), flush=True)
            return 0
        receipt['inspector_executions'] = 1
        save()
        result = subprocess.run([str(binary)] + forwarded)
        receipt['inspector_exit'] = result.returncode
        save()
        return result.returncode
    finally:
        if report:
            report.close()
        if temporary:
            temporary.cleanup()


if __name__ == '__main__':
    raise SystemExit(main())
