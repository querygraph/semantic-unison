"""Finite source/fixture controls only; actual sync matrix needs fresh IO admission."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import re

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stock-build',type=Path,required=True)
    parser.add_argument('--ox-build',type=Path,required=True)
    args=parser.parse_args()
    work=Path(tempfile.mkdtemp(prefix='unison-layout-receiving-controls-',dir='/private/tmp'))
    sources=[ROOT/p for p in ['bench/sync/fixtures.py','bench/sync/run.py','bench/sync/phase_stats.py','bench/sync/shared_audit.py',
        'bench/sync/layout_fixture_test.py','tests/manual.py','tests/shared_dispatch.py',
        'tests/shared_sync_controls.py','tests/manual_shared_test.py','tests/shared_io_dispatch_test.py',
        'tests/layout_receiving_controls.py','tests/dng_layout_preferences.ml']]
    result=dict(complete=False,calls=[],source_pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources},workspace=str(work),actual_sync_invoked=False,SDK_invoked=False,
                real_media_opened=False)
    def call(argv,cwd=None):
        previous=Path.cwd()
        try:
            if cwd is not None:os.chdir(cwd)
            out=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+45)
        finally:os.chdir(previous)
        result['calls'].append(out);save(work,result)
        c=out['client_cleanup']
        if not(c['reaped'] and c['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('layout source controls child/group unresolved')
        assert out['returncode']==0 and not out['capture_truncated'],out['stderr']
        return out
    for relative in ['bench/sync/layout_fixture_test.py','tests/shared_sync_controls.py',
                     'tests/manual_shared_test.py','tests/shared_io_dispatch_test.py']:
        call([sys.executable,str(ROOT/relative)])
    def objects(text,name):
        match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S)
        assert match,name
        return (match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic')
                .replace('$(WINOBJS)','').replace('$(WINCOBJS)','')
                .replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split())
    result['linked_artifacts']={}
    for label,path in [('stock',args.stock_build),('ox',args.ox_build)]:
        receipt=json.loads(path.read_text())
        assert receipt['complete'] and receipt['build_exit']==0 and receipt['build_system']=='make'
        for relative,digest in receipt['source_sha256'].items():
            if relative.startswith('src/'):
                assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
        build=Path(receipt['workspace'])/'src'
        text=(build/'Makefile.OCaml').read_text();modules=objects(text,'OCAMLOBJS')
        modules=modules[:modules.index('semanticFormats.cmx')+1]
        cobjects=objects(text,'COBJS')
        linked=[build/name for name in modules+cobjects]
        linked += [p.with_suffix('.o') for p in linked if p.suffix=='.cmx']
        pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in linked}
        result['linked_artifacts'].update(pins)
        target=work/label;target.mkdir(mode=0o700)
        source=target/'preferences.ml';source.write_bytes((ROOT/'tests/dng_layout_preferences.ml').read_bytes())
        includes=[build,build/'ubase',build/'system',build/'system/generic',build/'lwt',build/'lwt/generic']
        argv=[receipt['compiler']]+[v for p in includes for v in ('-I',str(p))]+['-I','+unix','-I','+str','unix.cmxa','str.cmxa']
        argv += [str(build/name) for name in modules]+[str(source)]+[str(build/name) for name in cobjects]+['-o',str(target/'preferences')]
        call(argv,cwd=target);call([str(target/'preferences')])
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
    for name,digest in result['source_pins'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
    result['complete']=True;save(work,result);print(work,flush=True)

if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
