"""Finite isolated stock/Ox EVP adapter controls. No SDK/media or production edit."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tests/sdk_host_matrix'))
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from camera_sdk_concurrency.persistence import save


def pin(path):
    path = Path(path); data = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--production-openssl', action='store_true')
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix='u-evp-controls-', dir='/private/tmp'))
    crypto = Path('/usr/local/opt/openssl@3').resolve()
    result = dict(complete=False, calls=[], compilers=[], library=pin(crypto / 'lib/libcrypto.dylib'),
                  source_pins=[pin(p) for p in sorted((ROOT / 'tools/portable-hash').glob('*')) if p.is_file()]
                  + [pin(Path(__file__)), pin(ROOT / 'src/semanticHash_evp.h'),
                     pin(ROOT / 'src/semanticHash.ml'), pin(ROOT / 'src/semanticHash_stubs.c')], SDK_invoked=False, media_payload_opened=False,
                  production_selected=args.production_openssl,
                  selection_scope='explicit test binary only; shipping default unchanged')
    for label, switch in [('stock', 'default'), ('ox', '5.2.0+ox')]:
        directory = root / label; directory.mkdir(mode=0o700)
        compiler = Path('/Users/alexy/.opam') / switch / 'bin/ocamlopt'
        for name in ('evp.ml', 'evp.mli', 'evp_stubs.c', 'control.ml'):
            shutil.copyfile(ROOT / 'tools/portable-hash' / name, directory / name)
        for name in ('semanticHash.ml', 'semanticHash.mli', 'semanticHash_stubs.c', 'semanticHash_evp.h'):
            shutil.copyfile(ROOT / 'src' / name, directory / name)
        if label == 'ox':
            for name in ('evp.ml', 'semanticHash.ml', 'control.ml'):
                path = directory / name; path.write_text(path.read_text().replace('(* ox-portable-ffi *)', '@@ portable'))
            for name in ('evp.mli', 'semanticHash.mli'):
                path = directory / name; path.write_text('@@ portable\n' + path.read_text())
        else:
            path = directory / 'control.ml'; path.write_text(path.read_text().replace('Domain.Safe.spawn', 'Domain.spawn'))
        for length in (0,1,55,56,63,64,65,119,120,127,128,65535,65536,65537,1048576):
            data = bytes((i * 113 + 29) % 256 for i in range(length))
            (directory / (str(length) + '.bin')).write_bytes(data)
            (directory / (str(length) + '.sha256')).write_text(hashlib.sha256(data).hexdigest())
        env = dict(os.environ, OPENSSL_CONF='/dev/null', PYTHONDONTWRITEBYTECODE='1')
        for name in ('OPENSSL_MODULES', 'OPENSSL_CONF_INCLUDE', 'OPENSSL_ENGINES'): env.pop(name, None)
        def call(argv, expected=0):
            outcome = invoke(argv, env, time.monotonic() + 60)
            result['calls'].append(dict(label=label, outcome=outcome)); save(root, result)
            proof = outcome['client_cleanup']
            if not (proof['reaped'] and proof['other_group_members_absent_before_reap']):
                raise UnresolvedOwnership('EVP control child/group unresolved')
            assert outcome['returncode'] == expected and not outcome['capture_truncated'], outcome['stderr']
            return outcome
        previous = Path.cwd()
        try:
            os.chdir(directory)
            call([str(compiler), '-ccopt', '-std=c11', '-ccopt', '-DEVPHASH_TEST_COUNTERS',
                  '-ccopt', '-I' + str(crypto / 'include'), '-ccopt', '-Wall', '-ccopt', '-Wextra',
                  '-ccopt', '-Werror', '-c', 'evp_stubs.c'])
            selected = (['-ccopt', '-DUNISON_SEMANTIC_HASH_OPENSSL',
                         '-ccopt', '-I' + str(crypto / 'include')]
                        if args.production_openssl else [])
            call([str(compiler), *selected, 'semanticHash_stubs.c', 'semanticHash.mli', 'semanticHash.ml',
                  'evp.mli', 'evp.ml', 'control.ml', 'evp_stubs.o',
                  '-cclib', '-L' + str(crypto / 'lib'), '-cclib', '-lcrypto',
                  '-cclib', '-Wl,-rpath,' + str(crypto / 'lib'), '-o', 'control'])
            call([str(directory / 'control')])
            if label == 'ox':
                for name, setup, operation in [
                    ('context', 'Evp.create ()', 'ignore(Evp.finish shared)'),
                    ('input', 'Bytes.of_string "abc"', 'Evp.feed (Evp.create ()) shared 0 3')]:
                    path = directory / (name + '.ml')
                    path.write_text('let shared = ' + setup + '\nlet _ = Domain.Safe.spawn (fun () -> ' + operation + ')\n')
                    out = call([str(compiler), '-c', path.name], 2)
                    assert 'nonportable' in out['stderr'] or 'contended' in out['stderr']
            result['compilers'].append(dict(label=label, compiler=pin(compiler), executable=pin(directory / 'control')))
        finally: os.chdir(previous)
    result['complete'] = True; save(root, result)
    print(json.dumps(dict(workspace=str(root), calls=len(result['calls']), complete=True)), flush=True)


if __name__ == '__main__':
    try: main()
    except UnresolvedOwnership as error: retain_after_record(lambda: print(repr(error), flush=True))
