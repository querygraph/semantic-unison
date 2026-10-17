"""Build-only private mixed probe against an actual qualified production build."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_child import invoke
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record
from camera_sdk_concurrency.persistence import save


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def artifact(p):
    p=Path(p).resolve()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-result',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not args.output.is_absolute() or args.output.exists() or args.output.is_symlink():
        raise ValueError('fresh absolute build-only namespace required')
    build=json.loads(args.build_result.read_text());src=Path(build['workspace'])/'src'
    if not build['complete'] or build['build_exit']!=0 or build['selftest_exit']!=0:
        raise ValueError('actual qualified production build required')
    compiler=Path(build['compiler']).resolve()
    if sha(compiler)!=build['compiler_sha256']:raise ValueError('compiler changed')
    def check_sources():
        for name,digest in build['source_sha256'].items():
            if name.startswith('src/') and sha(ROOT/name)!=digest:
                raise ValueError('production source changed: '+name)
    check_sources()
    spec=importlib.util.spec_from_file_location('mixed_bridge_builder',ROOT/'tests/supervised_external/run.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    text=(src/'Makefile.OCaml').read_text()
    modules=builder.objects(text,'OCAMLOBJS');modules=modules[:modules.index('supervisedExternal.cmx')+1]
    objects=[src/p for p in modules+builder.objects(text,'COBJS')]
    # ocamlopt also consumes companion native objects and compiled interfaces.
    companions={p.with_suffix(suffix) for p in objects if p.suffix=='.cmx'
                for suffix in ('.o','.cmi')}
    if any(not p.is_file() for p in companions):raise ValueError('compiled companion absent')
    inputs={str(p):sha(p) for p in [*objects,*sorted(companions),src/'Makefile.OCaml']}
    args.output.mkdir(mode=0o700)
    source=ROOT/'tests/mixed_validation/probe.ml';source_pin=artifact(source)
    shutil.copyfile(source,args.output/'probe.ml')
    includes=[src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic']
    flags=[str(v) for p in includes for v in ('-I',p)]+['-I','+unix','-I','+str']
    command=[str(compiler),*flags,'unix.cmxa','str.cmxa',*[str(p) for p in objects],
             str(args.output/'probe.ml'),'-o',str(args.output/'probe')]
    result=dict(schema='unison-mixed-probe-build/1',complete=False,phase='COMPILER_INTENT',
                command=command,compiler=artifact(compiler),source=source_pin,
                build_result=artifact(args.build_result),linked_inputs=inputs,
                probe_executions=0,sdk_calls=0)
    save(args.output,result)
    environment=dict(os.environ)
    for name in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):environment.pop(name,None)
    outcome=invoke(command,environment,time.monotonic()+60)
    result.update(phase='COMPILER_OUTCOME',outcome=outcome);save(args.output,result)
    if outcome['returncode']!=0:raise ValueError('private probe build failed: '+outcome['stderr'])
    check_sources()
    if (sha(compiler)!=build['compiler_sha256'] or artifact(source)!=source_pin
            or any(sha(p)!=digest for p,digest in inputs.items())):
        raise ValueError('compiler/source/object changed during build')
    result.update(complete=True,phase='FINISHED',executable=artifact(args.output/'probe'),
                  standard_library_inventory_complete=False,
                  scope='Build-only; links qualified production objects and companions, uses existing qualified compiler installation; no probe/SDK/media execution or performance proof.')
    save(args.output,result)
    print(json.dumps(dict(complete=True,output=str(args.output),executable=result['executable'])),flush=True)


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print('MIXED_BUILD_RETAINED '+repr(error),flush=True))
