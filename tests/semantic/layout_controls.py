"""Production-linked stock/Ox exact-layout fixtures and strict-profile regressions."""
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
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    modules=['semanticHash','semanticFile','formatExtension','xmpObservation','xmpMerge',
             'dngSemantic','dngExtended','dngLayout','semanticDelta']
    root=Path(tempfile.mkdtemp(prefix='unison-layout-controls-',dir='/private/tmp'))
    sources=[ROOT/'src'/(m+ext) for m in modules for ext in ('.ml','.mli','.ox.mli.in')]
    sources += [ROOT/'src'/name for name in ('semantic_mode_filter.ml','semanticHash_stubs.c',
                                           'semanticHash_evp.h','semanticFile_stubs.c')]
    sources += [ROOT/'tests/semantic'/name for name in ('layout_only.ml','private_safety.ml')]
    result=dict(complete=False,calls=[],source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources},work=str(root),SDK_invoked=False,media_payload_opened=False)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    def call(argv,expected=0):
        out=invoke(argv,env,time.monotonic()+60)
        result['calls'].append(out);save(root,result)
        closed=out['client_cleanup']
        if not (closed['reaped'] and closed['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('layout control child/group unresolved')
        assert out['returncode']==expected and not out['capture_truncated'],out['stderr']
        return out
    mode=root/'semantic-mode-filter'
    shutil.copyfile(ROOT/'src/semantic_mode_filter.ml',root/'semantic_mode_filter.ml')
    call(['/Users/alexy/.opam/default/bin/ocamlopt',str(root/'semantic_mode_filter.ml'),'-o',str(mode)])
    for label,switch in [('stock','default'),('ox','5.2.0+ox')]:
        compiler='/Users/alexy/.opam/'+switch+'/bin/ocamlopt'
        version=call([compiler,'-version'])['stdout'].strip()
        work=root/label;work.mkdir(mode=0o700)
        for module in modules:
            for ext in ('.mli','.ml'):
                out=call([str(mode),version,str(ROOT/'src'/(module+ext))])
                (work/(module+ext)).write_text(out['stdout'])
        for name in ('semanticHash_stubs.c','semanticHash_evp.h','semanticFile_stubs.c'):
            shutil.copyfile(ROOT/'src'/name,work/name)
        for name in ('layout_only.ml','private_safety.ml'):
            shutil.copyfile(ROOT/'tests/semantic'/name,work/name)
        command=[compiler,'-I','+unix','unix.cmxa','semanticHash_stubs.c','semanticFile_stubs.c']
        for module in modules:command += [module+'.mli',module+'.ml']
        command += ['private_safety.ml','layout_only.ml','-o','layout-controls']
        previous=Path.cwd()
        try:
            os.chdir(work);call(command);call([str(work/'layout-controls')])
        finally:os.chdir(previous)
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in result['source_pins'].items())
    result['complete']=True;save(root,result);print(root,flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
