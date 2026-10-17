"""Build-only production-linked probes. No remote connection or payload dispatch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def objects(text,name):
    match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',text,re.M|re.S)
    if match is None:raise ValueError('missing build object list')
    return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace(
        '$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stock-build',type=Path,required=True)
    parser.add_argument('--ox-build',type=Path,required=True)
    args=parser.parse_args()
    work=Path(tempfile.mkdtemp(prefix='unison-component-remote-probes-',dir='/private/tmp'))
    result={'complete':False,'work':str(work),'calls':[],'probes':{},'linked_artifacts':{},
            'sources':{str(p):sha(p) for p in [Path(__file__),ROOT/'tests/report/remote_probe.ml']},
            'remote_or_IO_dispatch':False,'SDK_invoked':False}
    def call(argv,cwd,expected=0,expected_stderr=None,expected_stdout=None):
        previous=Path.cwd()
        try:
            os.chdir(cwd)
            out=invoke(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),time.monotonic()+60)
        finally:os.chdir(previous)
        result['calls'].append(out);save(work,result)
        cleanup=out['client_cleanup']
        if not(cleanup['reaped'] and cleanup['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('probe compile/preentry child unresolved')
        if out['returncode']!=expected or out['capture_truncated']:
            raise ValueError(out['stderr'])
        if expected_stderr is not None and expected_stderr not in out['stderr']:
            raise ValueError('probe did not reach its exact preentry refusal')
        if expected_stdout is not None and expected_stdout not in out['stdout']:
            raise ValueError('probe did not reach its offline preference preflight')
    for label,path in [('stock',args.stock_build),('ox',args.ox_build)]:
        value=json.loads(path.read_text())
        assert value['complete'] and value['build_exit']==0 and value['build_system']=='make'
        for relative,digest in value['source_sha256'].items():
            if relative.startswith('src/'):
                assert sha(ROOT/relative)==digest,relative
                result['sources'][str(ROOT/relative)]=digest
        assert sha(value['compiler'])==value['compiler_sha256']
        build=Path(value['workspace'])/'src';text=(build/'Makefile.OCaml').read_text()
        modules=objects(text,'OCAMLOBJS');modules=modules[:modules.index('uicommon.cmx')]
        cobjects=objects(text,'COBJS');files=[build/n for n in modules+cobjects]
        files += [p.with_suffix('.o') for p in files if p.suffix=='.cmx']
        pins={str(p):sha(p) for p in files};result['linked_artifacts'].update(pins)
        target=work/label;target.mkdir(mode=0o700)
        source=target/'probe.ml';source.write_bytes((ROOT/'tests/report/remote_probe.ml').read_bytes())
        flags=[v for p in [build,build/'ubase',build/'system',build/'system/generic',
                          build/'lwt',build/'lwt/generic'] for v in ('-I',str(p))]
        binary=target/'component-probe'
        argv=[value['compiler'],*flags,'-I','+unix','-I','+str','unix.cmxa','str.cmxa']
        argv += [str(build/n) for n in modules]+[str(source)]+[str(build/n) for n in cobjects]+['-o',str(binary)]
        call(argv,target)
        # Exact original guards, before preferences/root installation. These
        # do not qualify an actual remote connection or exercise supplied paths.
        call([str(binary)],target,expected=2,expected_stderr='usage: component-probe')
        call([str(binary),'relative','/probe-unused-right','/probe-unused-server',
              '/probe-unused-launcher','supported'],target,expected=2,
              expected_stderr='absolute probe paths required')
        call([str(binary),'/probe-unused-left','/probe-unused-right','/probe-unused-server',
              '/probe-unused-launcher','unknown'],target,expected=2,
              expected_stderr='unknown probe mode')
        call([str(binary),'/probe-unused-left','/probe-unused-right','/probe-unused-server',
              '/probe-unused-launcher','preflight'],target,
              expected_stdout='PROBE_PREFLIGHT_ONLY')
        assert all(sha(p)==digest for p,digest in pins.items())
        result['probes'][label]={'path':str(binary),'sha256':sha(binary),'build_receipt':str(path),
                                 'compiler_sha256':value['compiler_sha256']}
    assert all(sha(p)==digest for p,digest in result['sources'].items())
    result['complete']=True;save(work,result);print(work,flush=True)

if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
