"""Verify mixed probe build provenance; no executable or helper is launched."""
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]


def require(value,message):
    if not value:raise ValueError(message)


def check(receipt,row,production):
    require(receipt.get('schema')=='unison-mixed-probe-build/1'
            and receipt.get('complete') is True and receipt.get('phase')=='FINISHED'
            and type(receipt.get('probe_executions')) is int and receipt['probe_executions']==0
            and type(receipt.get('sdk_calls')) is int and receipt['sdk_calls']==0,'completed build-only receipt required')
    require(receipt.get('executable')==row['executable'],'compiled executable differs from plan')
    require(receipt['source']['path']==str(ROOT/'tests/mixed_validation/probe.ml'),'mixed probe source binding differs')
    require(production.get('complete') is True and type(production.get('build_exit')) is int
            and production['build_exit']==0 and type(production.get('selftest_exit')) is int
            and production['selftest_exit']==0,'production build/selftest not qualified')
    require(receipt['compiler']['sha256']==production['compiler_sha256']
            and Path(production['compiler']).resolve()==Path(receipt['compiler']['path']),
            'compiler differs from production build')
    out=receipt['outcome'];child=out.get('client_cleanup',{})
    require(out.get('command')==receipt['command'] and type(out.get('returncode')) is int and out['returncode']==0
            and out.get('timed_out') is False and out.get('capture_truncated') is False
            and type(child.get('pid')) is int and child['pid']>0
            and type(child.get('returncode')) is int and child['returncode']==0
            and child.get('reaped') is True and child.get('other_group_members_absent_before_reap') is True
            and child.get('hard_kill_required') is False,'compiler outcome/group unresolved')
    src=Path(production['workspace'])/'src';command=receipt['command']
    includes=[src,src/'ubase',src/'lwt',src/'lwt/generic',src/'system',src/'system/generic']
    prefix=[receipt['compiler']['path'],*[str(v) for p in includes for v in ('-I',p)],
            '-I','+unix','-I','+str','unix.cmxa','str.cmxa']
    output=Path(row['executable']['path'])
    require(type(command) is list and command[:len(prefix)]==prefix
            and command[-3:]==[str(output.parent/'probe.ml'),'-o',str(output)],'exact probe compiler argv differs')
    objects=command[len(prefix):-3]
    require(objects and len(objects)==len(set(objects))
            and all(type(p) is str and Path(p).is_relative_to(src) and '..' not in Path(p).parts
                    and Path(p).suffix in ('.cmx','.o') for p in objects)
            and str(src/'supervisedExternal.cmx') in objects,'bounded production link objects required')
    expected=set(objects)|{str(src/'Makefile.OCaml')}
    expected.update(str(Path(p).with_suffix(s)) for p in objects if p.endswith('.cmx') for s in ('.o','.cmi'))
    require(type(receipt['linked_inputs']) is dict and set(receipt['linked_inputs'])==expected
            and all(type(h) is str and re.fullmatch('[0-9a-f]{64}',h) for h in receipt['linked_inputs'].values()),
            'exact linked object/interface companions required')
    return dict(build_provenance_bound=True,standard_library_inventory_complete=False,
                artifact_execution_authorized=False)


def verify(row):
    from mixed_validation.artifacts import verified_hash
    from mixed_validation.execute import document
    for item in (row['build_receipt'],row['executable']):verified_hash(item)
    receipt=document(row['build_receipt']['path'],row['build_receipt']['sha256'])
    verified_hash(receipt['build_result'])
    production=document(receipt['build_result']['path'],receipt['build_result']['sha256'])
    proof=check(receipt,row,production)
    for name in ('source','compiler'):verified_hash(receipt[name])
    for name,digest in receipt['linked_inputs'].items():
        verified_hash(dict(path=name,sha256=digest,bytes=os.lstat(name).st_size))
    for name,digest in production['source_sha256'].items():
        if name.startswith('src/'):
            require('..' not in Path(name).parts,'canonical production source path required')
            p=ROOT/name
            verified_hash(dict(path=str(p),sha256=digest,bytes=os.lstat(p).st_size))
    return proof
