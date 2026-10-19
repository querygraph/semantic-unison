"""Prepare ten immutable metadata plans; never admit or dispatch a cohort."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'bench/sync'))
import auto_cohort as A
import cohort_plan as C
from cohort_entry import worker_argv, TARGET, COMPILERS
from cached_benchmark.contract import read_bytes, PYTHON, PYTHON_SHA
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import require, unique_object


def pin(path,limit=16*1048576):
    return hashlib.sha256(read_bytes(path,limit)).hexdigest()


def write(path,value):
    raw=(json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        at=0
        while at<len(raw):
            n=os.write(fd,raw[at:]);require(n>0,'metadata write stalled');at+=n
        os.fsync(fd)
    finally:
        close_descriptors([fd])
    return hashlib.sha256(raw).hexdigest()


def artifact(build,label):
    require(build.get('complete') is True and build.get('selftest_requested') is True
            and type(build.get('build_exit')) is int and build['build_exit']==0
            and type(build.get('selftest_exit')) is int and build['selftest_exit']==0,
            'successful build/selftest receipt required')
    compiler=str(Path(build['compiler']).resolve())
    require(compiler==COMPILERS[label],'exact stock/Ox compiler required')
    return dict(binary=str(Path(build['binary']).resolve()),compiler=compiler,
                binary_sha256=C.digest(build['binary_sha256']),
                compiler_sha256=C.digest(build['compiler_sha256']))


def prepare(output,build_paths,prerequisites,*,file_mib=32,files=8):
    require(not os.path.lexists(output),'freeze output already exists')
    A.contract('stock',1,file_mib=file_mib,files=files)
    names=C.execution_sources(ROOT)
    source_sha={name:pin(ROOT/name) for name in names}
    prerequisites={str(Path(p).resolve()):pin(Path(p).resolve()) for p in prerequisites}
    builds={}
    for label in ('stock','ox'):
        path=Path(build_paths[label]).resolve()
        raw=read_bytes(path,1048576)
        builds[label]=(str(path),artifact(json.loads(raw,object_pairs_hook=unique_object),label))
        prerequisites[str(path)]=hashlib.sha256(raw).hexdigest()
    output.mkdir(mode=0o700)
    rows=[]
    for selection in A.SELECTORS:
        for label in ('stock','ox'):
            cohort=A.contract(label,selection,file_mib=file_mib,files=files)
            workspace=Path('/private/tmp')/('unison-auto-cohort-'+uuid.uuid4().hex)
            require(not os.path.lexists(workspace),'generated workspace already exists')
            build_path,tool=builds[label]
            plan=dict(schema=C.SCHEMA,workspace=str(workspace),interpreter=PYTHON,
                interpreter_sha256=PYTHON_SHA,script=str(ROOT/'bench/sync/run.py'),
                cohort=cohort,artifact=tool,build_receipt=build_path,
                execution_sha256=source_sha,prerequisite_sha256=prerequisites,
                limits=C.limits(cohort),cpu_token_indexes=list(range(cohort['reserved_credits'])),
                requires_temporary_borrow=cohort['reserved_credits']==18)
            plan['launch_argv']=A.launch_argv(cohort,interpreter=PYTHON,script=plan['script'],
                                            output=str(workspace/'RESULT.json'),artifact=tool)
            C.validate(plan,execution_sources=names)
            stem=label+'-'+str(selection)
            plan_path=output/(stem+'-plan.json');plan_sha=write(plan_path,plan)
            C.checked_metadata(str(plan_path),plan_sha,repository=ROOT,execution_sources=names)
            request=dict(schema='unison-auto-cohort-request/1',state='PREPARED_UNADMITTED',
                target=TARGET,plan=dict(path=str(plan_path),sha256=plan_sha),workspace=str(workspace),
                cpu_credits=cohort['reserved_credits'],requires_temporary_borrow=plan['requires_temporary_borrow'],
                limits=plan['limits'],command=worker_argv(plan,str(plan_path),plan_sha),
                execution_source_sha256={str(ROOT/name):sha for name,sha in source_sha.items()},
                launch_argv=[PYTHON,str(ROOT/'tests/cohort_entry.py'),'--plan',str(plan_path),
                    '--plan-sha256',plan_sha,'--admission','ROOT_PUBLISHED_ADMISSION_REQUIRED',
                    '--admission-sha256','ROOT_PUBLISHED_SHA_REQUIRED'])
            request_path=output/(stem+'-request.json');request_sha=write(request_path,request)
            rows.append(dict(label=label,selection=selection,cpu_credits=cohort['reserved_credits'],
                request=dict(path=str(request_path),sha256=request_sha),plan=request['plan'],
                workspace=str(workspace),runtime_admitted=False))
    index=dict(schema='unison-auto-cohort-index/1',state='PREPARED_UNADMITTED',cohorts=rows,
        workload=dict(file_mib=file_mib,files=files),
        total_rows=180,total_cli_invocations=540,warmup_rows=30,measured_rows=150,
        source_sha256=source_sha,preparer_sha256=pin(Path(__file__)),
        scope='metadata only; binary/compiler hashes copied from qualified receipts, not freshly read; no admission or execution')
    write(output/'INDEX.json',index)
    return index


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stock-build','ox-build','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--prerequisite',type=Path,action='append',default=[])
    parser.add_argument('--file-mib',type=int,default=32)
    parser.add_argument('--files',type=int,default=8)
    args=parser.parse_args()
    output=args.output.resolve()
    require(output.parent==ROOT/'doc' and output.name.startswith('auto-cohort-qualification-'),
            'repository doc freeze directory required')
    index=prepare(output,dict(stock=args.stock_build,ox=args.ox_build),args.prerequisite,
                  file_mib=args.file_mib,files=args.files)
    print(json.dumps(dict(index=str(output/'INDEX.json'),cohorts=len(index['cohorts']),
                         runtime_admitted=False),indent=2))


if __name__=='__main__':main()
