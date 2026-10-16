#!/usr/bin/env python3
"""Exercise production FinalPublication with small isolated native fixtures."""
import argparse
from contextlib import nullcontext
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', default='ocamlopt')
    parser.add_argument('--keep-work', action='store_true')
    parser.add_argument('--negative-control', action='store_true',
                        help='remove candidate baseline check in the private copy')
    parser.add_argument('--producer-negative-control', action='store_true',
                        help='reopen the normal name instead of duplicating the producer fd')
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error('native compiler unavailable')
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    for variable in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        environment.pop(variable, None)
    sources = ['src/finalPublication.mli', 'src/finalPublication.ml',
               'src/finalPublication_stubs.c', 'tests/final_publication/fixture.c']
    library = Path(subprocess.check_output([compiler, '-where'], text=True,
                                           env=environment).strip())
    temporary = (nullcontext(tempfile.mkdtemp(prefix='unison-final-publication-', dir='/private/tmp'))
                 if args.keep_work else
                 tempfile.TemporaryDirectory(prefix='unison-final-publication-', dir='/private/tmp'))
    with temporary as tmp:
        work = Path(tmp)
        print('Build:', work, flush=True)
        for name in sources + ['tests/final_publication/test.ml',
                               'tests/final_publication/producerTest.ml']:
            data = (root / name).read_bytes()
            (work / Path(name).name).write_bytes(data)
            print('source', name, hashlib.sha256(data).hexdigest(), flush=True)
        harness = (work / 'test.ml').read_text()
        if 'val with_async_exns' in (library / 'sys.mli').read_text():
            harness = harness.replace('let with_async_exns f = f ()',
                                      'let with_async_exns = Sys.with_async_exns')
        (work / 'test.ml').write_text(harness)
        producer_harness = (work / 'producerTest.ml').read_text()
        if 'val with_async_exns' in (library / 'sys.mli').read_text():
            producer_harness = producer_harness.replace('let with_async_exns f = f ()',
                                                       'let with_async_exns = Sys.with_async_exns')
        (work / 'producerTest.ml').write_text(producer_harness)
        if args.negative_control:
            native = work / 'finalPublication_stubs.c'
            text = native.read_text()
            guard = 'if (require_baseline && !same_file(&context->candidate_stat, &before)) return EBUSY;'
            if text.count(guard) != 1:
                raise RuntimeError('candidate baseline control seam changed')
            native.write_text(text.replace(guard, '(void)require_baseline; /* private negative control */'))
            print('Negative-control C', hashlib.sha256(native.read_bytes()).hexdigest(), flush=True)
        if args.producer_negative_control:
            native = work / 'finalPublication_stubs.c'
            text = native.read_text()
            seam = 'context->witness_fd = fcntl(borrowed, F_DUPFD_CLOEXEC, 0);'
            if text.count(seam) != 1:
                raise RuntimeError('producer descriptor control seam changed')
            native.write_text(text.replace(seam,
                'context->witness_fd = openat(context->candidate_parent_fd, context->candidate_name, '
                'O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC); /* private reopen control */'))
            print('Producer-negative-control C', hashlib.sha256(native.read_bytes()).hexdigest(), flush=True)
        print('compiled test.ml', hashlib.sha256(harness.encode()).hexdigest(), flush=True)
        print('compiled producerTest.ml', hashlib.sha256(producer_harness.encode()).hexdigest(), flush=True)
        # fixture.c includes the byte-identical production C translation unit
        # under private syscall wrappers; never link duplicate native symbols.
        for name in ['src/finalPublication.mli', 'src/finalPublication.ml',
                     'tests/final_publication/fixture.c']:
            subprocess.run([compiler, '-I', '+unix', '-c', Path(name).name],
                           cwd=work, env=environment, check=True)
        subprocess.run([compiler, '-I', '+unix', 'unix.cmxa',
                        'fixture.o',
                        'finalPublication.cmx', 'test.ml', 'producerTest.ml', '-o', 'publication-test'],
                       cwd=work, env=environment, check=True)
        print('Compiler', subprocess.check_output([compiler, '-version'], text=True,
                                                  env=environment).strip(), flush=True)
        result = subprocess.run([str(work / 'publication-test'), str(work)],
                                cwd=work, env=environment, timeout=60,
                                capture_output=True, text=True)
        print(result.stdout, end='', flush=True)
        print(result.stderr, end='', flush=True)
        if args.producer_negative_control:
            last_case = next((line for line in reversed(result.stdout.splitlines())
                              if line.startswith('RUN ')), None)
            if (result.returncode == 0 or
                    last_case != 'RUN same-byte replacement before producer adoption' or
                    'Failure("wrong producer descriptor admitted")' not in result.stderr):
                raise RuntimeError('producer negative control did not detect name reopening')
            print('PASS producer negative control: original output descriptor is required', flush=True)
            return
        if args.negative_control:
            last_case = next((line for line in reversed(result.stdout.splitlines())
                              if line.startswith('RUN ')), None)
            if (result.returncode == 0 or
                    last_case != 'RUN candidate mutation after attach' or
                    'Failure("candidate mutation was published")' not in result.stderr):
                raise RuntimeError('negative control did not detect lost candidate binding')
            print('PASS negative control: late candidate mutation detected by harness', flush=True)
            return
        if result.returncode == 77:
            print('SKIP: native exclusive publication requires macOS 10.12+')
        else:
            result.check_returncode()


if __name__ == '__main__':
    main()
