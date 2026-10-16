"""Finite stock/Ox production-linked private-safety controls; no fuzz/SDK/media."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from shared_process_owner import retain_after_record
from shared_cpu_pool import UnresolvedOwnership
from private_maker_execute import save


def main():
    modules=['semanticHash','semanticFile','formatExtension','xmpObservation','xmpMerge',
             'dngSemantic','dngExtended','semanticDelta']
    names=[ROOT/'src'/(name+suffix) for name in modules for suffix in ('.mli','.ml')]
    names += [ROOT/'src/semanticHash_stubs.c',ROOT/'src/semanticFile_stubs.c',
              ROOT/'tests/semantic/private_safety.ml',Path(__file__).resolve()]
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    root=Path(tempfile.mkdtemp(prefix='unison-private-safety-',dir='/private/tmp'));calls=[]
    for label,prefix in [('stock','default'),('ox','5.2.0+ox')]:
        compiler=Path('/Users/alexy/.opam')/prefix/'bin/ocamlopt'
        compiler_sha=hashlib.sha256(compiler.read_bytes()).hexdigest()
        work=root/label;work.mkdir(mode=0o700)
        for path in names:
            if path.suffix!='.py':shutil.copyfile(path,work/path.name)
        argv=[str(compiler),'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c']
        for name in modules:argv.extend([name+'.mli',name+'.ml'])
        argv.extend(['private_safety.ml','-o','private-safety'])
        previous=Path.cwd()
        try:
            os.chdir(work)
            for command in (argv,[str(work/'private-safety')]):
                outcome=invoke(command,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+60)
                calls.append(dict(label=label,compiler_sha256=compiler_sha,outcome=outcome))
                save(root/('CALL-'+str(len(calls))+'.json'),calls[-1])
                proof=outcome['client_cleanup']
                assert proof['reaped'] and proof['other_group_members_absent_before_reap']
                assert outcome['returncode']==0 and not outcome['capture_truncated']
        finally:os.chdir(previous)
    assert pins=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in names}
    report=dict(source_pins=pins,calls=calls,workspace=str(root),
                photo_payload_opened=False,SDK_invoked=False,scope='Original generated TIFF inputs; four scalar baselines and eight refusals per compiler, no fuzz campaign.')
    save(root/'RESULT.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
