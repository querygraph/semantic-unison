"""Finite serial stock/Ox independent wire controls under the shared owner.

Only existing hand-written synthetic conformance cases, one compiler at a time;
no SDK, Adobe, photographic data, server sessions or external input arguments.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests'))
from shared_process_owner import retain_after_record


def wait_owned_child(child, *, timeout, record):
    """An observation failure never discards the unreaped direct-child handle.

    Compiler descendants stay in the existing containing shared process group.
    This does not create a separate session or claim settlement on timeout.
    """
    try:
        return child.wait(timeout=timeout)
    except BaseException as error:
        # Called inside the log context: retain both child and open log owner
        # before unwinding. retain_after_record retains even if recording fails.
        retain_after_record(lambda: record(dict(
            state='CONFORMANCE_CHILD_OWNERSHIP_RETAINED',child_pid=child.pid,
            error=repr(error),direct_child_wait_proved=False,
            group_closure_proved=False,resource_release_authorized=False)))
        raise RuntimeError('ownership retention unexpectedly returned')

def main():
    if len(sys.argv) != 1:
        raise ValueError('fixed original conformance controls accept no arguments')
    os.umask(0o077)
    work = Path(tempfile.mkdtemp(prefix='unison-sde-shared-controls-'))
    sources = ['src/formatExtension.ml', 'src/formatExtension.mli', 'src/formatExtension.ox.mli.in', 'src/semanticDelta.ml', 'src/semanticDelta.mli',
               'tests/semantic/conformance/test.ml',
               'tests/semantic/conformance/reference.py',
               'tests/semantic/conformance/run.py',
               'tests/semantic/conformance/shared.py']
    def pins():
        return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
    before = pins()
    rows = []
    for label, compiler, variant in [(label, compiler, variant)
            for label, compiler in [('stock', '/Users/alexy/.opam/default/bin/ocamlopt'),
                            ('ox', '/Users/alexy/.opam/5.2.0+ox/bin/ocamlopt')]
            for variant in ('current', 'previous-profile-domain', 'previous-target-proof', 'previous-profile-inspection')]:
        report = work/(label+'-'+variant+'.json')
        command = [sys.executable, str(ROOT/'tests/semantic/conformance/run.py'),
                   '--ocamlopt', compiler, '--report', str(report)]
        if variant == 'previous-profile-domain':
            command += ['--negative-control', 'profile-id']
        elif variant == 'previous-target-proof':
            command += ['--negative-control', 'target-proof']
        elif variant == 'previous-profile-inspection':
            command += ['--negative-control', 'profile-inspection']
        log = work/(label+'-'+variant+'.log')
        with log.open('xb') as stream:
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
            code = wait_owned_child(child, timeout=50, record=lambda value:
                (work/'OWNERSHIP-RETAINED.json').write_text(json.dumps(dict(value,
                    command=command,log=str(log)),indent=2)+'\n'))
        rows.append({'compiler': label, 'variant':variant, 'pid': child.pid, 'actual_wait_exit': code,
                     'command': command, 'log': str(log),
                     'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest(),
                     'report': str(report)})
        print(json.dumps(rows[-1]), flush=True)
        if code:
            raise RuntimeError(log.read_text(errors='replace'))
    if pins() != before:
        raise RuntimeError('current conformance source changed')
    print(json.dumps({'schema':'unison-shared-sde-conformance/1', 'complete':True,
                      'workspace':str(work), 'sources':before, 'calls':rows}), flush=True)

if __name__ == '__main__':
    main()
