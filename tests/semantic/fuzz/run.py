#!/usr/bin/env python3
"""Build a compiler-matched AFL target and retain bounded synthetic campaigns."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

MODULES = 'semanticHash semanticFile formatExtension xmpObservation xmpMerge dngSemantic dngExtended jpegSemantic semanticDelta'.split()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ocamlopt', required=True, type=Path)
    parser.add_argument('--afl-dir', type=Path)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--build-only', action='store_true', help='compile the target without invoking AFL or running inputs')
    parser.add_argument('--modes', nargs='+', choices=['sde', 'sdr', 'dng', 'dng-v1', 'jpeg', 'xmp'], default=['sde', 'sdr', 'dng', 'dng-v1', 'jpeg', 'xmp'])
    args = parser.parse_args()
    if not args.build_only and args.afl_dir is None:
        parser.error('--afl-dir is required for a campaign')
    if not 1 <= args.seconds <= 3600:
        parser.error('seconds must be 1..3600 per sequential campaign')
    root = Path(__file__).resolve().parents[3]
    work = Path(tempfile.mkdtemp(prefix='unison-semantic-afl-', dir='/private/tmp'))
    print('Workspace:', work, flush=True)
    compiler = args.ocamlopt.resolve()
    env = dict(os.environ)
    for key in ('OCAMLLIB', 'OCAMLPATH', 'CAML_LD_LIBRARY_PATH', 'OCAMLRUNPARAM'):
        env.pop(key, None)
    env.update(PATH=str(compiler.parent)+os.pathsep+env.get('PATH', ''),
               AFL_NO_FORKSRV='1', AFL_CRASH_EXITCODE='86', AFL_MAP_SIZE='65536',
               AFL_NO_UI='1', AFL_SKIP_CPUFREQ='1',
               AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES='1')
    version = subprocess.check_output([str(compiler), '-version'], env=env, text=True).strip()
    sources = {}
    shutil.copy2(root/'src/semantic_mode_filter.ml', work/'semantic_mode_filter.ml')
    subprocess.run([str(compiler), 'semantic_mode_filter.ml', '-o', 'filter'], cwd=work, env=env, check=True)
    for name in MODULES:
        for suffix in ('.mli', '.ml'):
            source = root/'src'/f'{name}{suffix}'
            sources[str(source.relative_to(root))] = sha(source)
            (work/source.name).write_bytes(subprocess.check_output([str(work/'filter'), version, str(source)]))
    for source in (root/'src/semanticHash_stubs.c', root/'src/semanticFile_stubs.c', Path(__file__).with_name('target.ml')):
        sources[str(source.relative_to(root))] = sha(source)
        shutil.copy2(source, work/source.name)
    command = [str(compiler), '-afl-instrument', '-I', '+unix', 'unix.cmxa', 'semanticHash_stubs.c', 'semanticFile_stubs.c']
    for name in MODULES:
        command += [name+'.mli', name+'.ml']
    with (work/'build.log').open('w') as log:
        subprocess.run(command+['target.ml', '-o', 'target'], cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    if args.build_only:
        receipt = {'compiler': str(compiler), 'version': version, 'compiler_sha256': sha(compiler),
                   'source_sha256': sources, 'target_sha256': sha(work/'target'),
                   'workspace': str(work), 'build_only': True, 'native_or_input_execution': False}
        (work/'build-only.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print('Built target:', work/'target', flush=True)
        return
    golden = root/'tests/semantic/conformance/golden'
    results = {}
    for mode in args.modes:
        corpus = work/f'{mode}-inputs'
        corpus.mkdir()
        suffix = {'sde': '.sde', 'sdr': '.sdr', 'dng': '.base', 'dng-v1': '.base'}.get(mode)
        if suffix:
            for source in golden.glob('*'+suffix):
                if mode.startswith('dng') and not source.name.startswith('dng-'):
                    continue
                shutil.copy2(source, corpus/source.name)
        elif mode == 'xmp':
            (corpus/'rdf').write_bytes(b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description/></rdf:RDF>')
        else:
            packet = b'http://ns.adobe.com/xap/1.0/\0<x/>'
            (corpus/'markers').write_bytes(b'\xff\xd8\xff\xe1'+(len(packet)+2).to_bytes(2, 'big')+packet+b'\xff\xd9')
        (corpus/'short').write_bytes(b'X')
        output = work/f'{mode}-output'
        command = [str(args.afl_dir/'afl-fuzz'), '-i', str(corpus), '-o', str(output), '-m', 'none', '-t', '1000', '-V', str(args.seconds), '-s', '173', '--', str(work/'target'), mode, '@@']
        with (work/f'{mode}.log').open('w') as log:
            result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=args.seconds+60)
        stats = output/'default/fuzzer_stats'
        saved = {kind: [str(path.relative_to(output)) for path in sorted((output/'default'/kind).glob('id:*'))]
                 for kind in ('crashes', 'hangs')}
        results[mode] = {'exit': result.returncode, 'stats': stats.read_text() if stats.exists() else None,
                         'saved_failures': saved}
        (work/'progress.json').write_text(json.dumps(results, indent=2))
        print(mode, 'exit', result.returncode, flush=True)
        if result.returncode:
            raise RuntimeError(f'{mode} AFL failed; inspect {work}/{mode}.log')
        if not stats.exists() or any(saved.values()):
            raise RuntimeError(f'{mode} missing statistics or saved failures; inspect {output}')
    receipt = {'compiler': str(compiler), 'version': version, 'compiler_sha256': sha(compiler), 'source_sha256': sources,
               'target_sha256': sha(work/'target'), 'afl_sha256': sha(args.afl_dir/'afl-fuzz'), 'input_limit': 262144,
               'seconds_per_mode': args.seconds, 'results': results, 'workspace': str(work),
               'scope': 'read-only synthetic parser/roundtrip campaigns; no SDK, photo, apply or publication operations',
               'limitations': ['macOS crash reporter remains enabled; signal-crash discovery timing is unqualified',
                               'exit-86 exception/invariant oracle; input size capped at 256 KiB',
                               'OCaml instrumentation does not instrument native C helpers']}
    (work/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')

if __name__ == '__main__':
    main()
