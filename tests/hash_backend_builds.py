"""Finite Make/Dune opt-in OpenSSL builds; no SDK/media or installation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    work = Path(tempfile.mkdtemp(prefix='unison-hash-builds-', dir='/private/tmp'))
    crypto = Path('/usr/local/opt/openssl@3').resolve()
    result = dict(complete=False, calls=[], builds=[], work=str(work),
                  openssl_library=pin(crypto / 'lib/libcrypto.dylib'), SDK_invoked=False,
                  media_payload_opened=False, non_Apple_qualified=False)
    def call(argv, env, expected=0, seconds=240):
        outcome = invoke(argv, env, time.monotonic() + seconds)
        result['calls'].append(outcome); save(work, result)
        closed = outcome['client_cleanup']
        if not (closed['reaped'] and closed['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('hash build child/group unresolved')
        assert outcome['returncode'] == expected and not outcome['capture_truncated'], outcome['stderr']
        return outcome
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OPENSSL_CONF='/dev/null')
    for key in ('CFLAGS', 'CPPFLAGS', 'LDFLAGS', 'LDLIBS', 'OPENSSL_MODULES', 'OPENSSL_CONF_INCLUDE'):
        env.pop(key, None)
    compiler = Path('/Users/alexy/.opam/default/bin/ocamlopt')
    config = work / 'hash-config'
    config_source = work / 'semantic_hash_config.ml'
    shutil.copyfile(ROOT / 'src/semantic_hash_config.ml', config_source)
    call([str(compiler), str(config_source), '-o', str(config)], env)
    for index, (args, expected) in enumerate([
            (['platform', '', ''], 0), (['openssl', str(crypto / 'include'), str(crypto / 'lib')], 0),
            (['unknown', '', ''], 2), (['openssl', 'relative', ''], 2),
            (['openssl', '', '/bad$path'], 2)]):
        cflags, libs = work / (str(index)+'.cflags'), work / (str(index)+'.libs')
        call([str(config), *args, str(cflags), str(libs)], env, expected, 10)
        if expected == 0:
            if args[0] == 'platform': assert cflags.read_text() == libs.read_text() == '()\n'
            else:
                assert '-DUNISON_SEMANTIC_HASH_OPENSSL' in cflags.read_text()
                assert '-lcrypto' in libs.read_text()
        else: assert not cflags.exists() and not libs.exists()
    cases = [('stock', 'default', 'make', 'openssl'), ('ox', '5.2.0+ox', 'make', 'openssl'),
             ('stock', 'default', 'dune', 'openssl'), ('ox', '5.2.0+ox', 'dune', 'openssl'),
             ('stock', 'default', 'dune', 'platform')]
    for label, switch, system, backend in cases:
        report = work / (label+'-'+system+'-'+backend+'.json')
        configured = dict(env, SEMANTIC_HASH_BACKEND=backend,
                          SEMANTIC_OPENSSL_INCLUDE=str(crypto / 'include'),
                          SEMANTIC_OPENSSL_LIB=str(crypto / 'lib'))
        call([sys.executable, str(ROOT / 'tests/build_snapshot.py'), '--compiler-prefix',
              '/Users/alexy/.opam/'+switch+'/bin', '--jobs', '2', '--build-system', system,
              '--report', str(report)], configured)
        built = json.loads(report.read_text())
        assert built['complete'] and built['build_exit'] == 0
        assert pin(built['binary'])['sha256'] == built['binary_sha256']
        result['builds'].append(dict(label=label, system=system, backend=backend,
                                    report=pin(report), binary=pin(built['binary']),
                                    configured_hash_environment={k:configured[k] for k in
                                      ('SEMANTIC_HASH_BACKEND', 'SEMANTIC_OPENSSL_INCLUDE', 'SEMANTIC_OPENSSL_LIB')}))
        save(work, result)
    result['complete'] = True; save(work, result); print(work, flush=True)


if __name__ == '__main__':
    try: main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda: print(repr(error), file=sys.stderr, flush=True))
