#!/usr/bin/env python3
"""Build the read-only inspector; optionally retain it without executing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MODULES = ['semanticHash', 'semanticFile', 'componentHash', 'formatExtension', 'xmpObservation', 'xmpMerge',
           'dngSemantic', 'dngExtended', 'dngLayout', 'dngComponents', 'semanticDelta']
SOURCES = [Path('src') / (name + suffix) for name in MODULES for suffix in ('.ml', '.mli')]
SOURCES += [Path('src/semanticHash_stubs.c'), Path('src/semanticHash_evp.h'), Path('src/semanticFile_stubs.c'),
            Path('tools/semantic-inspect/inspect.ml')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_read(path, limit, *, digest_only=False):
    """Bounded no-follow regular-file read; no image payload is passed here."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= limit:
            raise ValueError('reuse artifact type/link/size differs')
        result = hashlib.sha256() if digest_only else bytearray()
        total = 0
        while total <= limit:
            block = os.read(fd, min(1048576, limit + 1 - total))
            if not block:
                break
            total += len(block)
            result.update(block) if digest_only else result.extend(block)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if (total != before.st_size or stamp(before) != stamp(os.fstat(fd))
                or stamp(before) != stamp(os.stat(path, follow_symlinks=False))):
            raise ValueError('reuse artifact changed during read')
        return result.hexdigest() if digest_only else bytes(result)
    finally:
        os.close(fd)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate build receipt key')
        value[key] = item
    return value


def checked_inspector(path):
    value = json.loads(stable_read(path, 65536), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError('inspector build receipt must be an object')
    if (value['schema'] != 'unison-semantic-inspector-build/1' or value['complete'] is not True
            or value['build_only'] is not True or type(value['build_exit']) is not int
            or value['build_exit'] != 0):
        raise ValueError('successful build-only inspector receipt required')
    expected = {str(name) for name in SOURCES}
    if not isinstance(value['source_sha256'], dict) or set(value['source_sha256']) != expected:
        raise ValueError('inspector source set differs')
    for name, digest in value['source_sha256'].items():
        if stable_read(ROOT / name, 16 * 1048576, digest_only=True) != digest:
            raise ValueError('inspector source changed: ' + name)
    workspace, binary = Path(value['workspace']), Path(value['binary'])
    if not workspace.is_absolute() or not binary.is_absolute() or binary != workspace / 'semantic-inspect':
        raise ValueError('inspector workspace/binary binding differs')
    info = workspace.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private owned inspector workspace required')
    if stable_read(binary, 128 * 1048576, digest_only=True) != value['binary_sha256']:
        raise ValueError('inspector binary changed')
    return binary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--use-build', type=Path, help='reuse a pinned retained inspector; never rebuild')
    parser.add_argument('--exiftool-build', type=Path, help='optional pinned read-only MakerNote interpretation bridge')
    args, forwarded = parser.parse_known_args()
    if forwarded[:1] == ['--']:
        forwarded = forwarded[1:]
    if args.exiftool_build:
        if not args.use_build or args.build_only or args.report or len(forwarded)!=2 or forwarded[0]!='--components':
            parser.error('--exiftool-build requires --use-build and exactly --components FILE')
        import importlib.util
        spec=importlib.util.spec_from_file_location('unison_exiftool_observation',ROOT/'tools/exiftool-bridge/observe.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from shared_cpu_pool import UnresolvedOwnership
        from shared_process_owner import retain_after_record
        try:
            result=module.observe(Path(forwarded[1]),args.exiftool_build,components_build=args.use_build)
        except UnresolvedOwnership as error:
            retain_after_record(lambda:print(repr(error),file=__import__('sys').stderr,flush=True))
        print(json.dumps(result,indent=2))
        return 0
    if args.use_build:
        if args.build_only or args.report:
            parser.error('--use-build cannot be combined with build/report output')
        try:
            binary = checked_inspector(args.use_build)
        except (ValueError, KeyError, TypeError, OSError) as error:
            parser.error('retained inspector build refused: ' + str(error))
        return subprocess.run([str(binary)] + forwarded).returncode
    if args.build_only and (not args.report or forwarded):
        parser.error('--build-only requires --report and forbids inspector arguments')
    if args.report and not args.build_only:
        parser.error('--report is currently a build-only receipt')
    executable = shutil.which(args.ocamlopt)
    if executable is None:
        parser.error('compiler not found')
    compiler = Path(executable).absolute()
    root, modules, sources = ROOT, MODULES, SOURCES
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
