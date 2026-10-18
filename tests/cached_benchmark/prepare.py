"""Freeze source/artifact metadata only. Never creates admission, locks or fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cached_benchmark.contract import (ROOT, TARGET, PYTHON, LIMITS, document,
    read_bytes, sources, artifact_paths, checked_plan, worker_argv)
from cached_benchmark.entry import write
from shared_cpu_pool import require, UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('stock','ox','workspace','admission','plan','request','qualification'):
        p.add_argument('--'+name,required=True)
    args=p.parse_args()
    require(not os.path.lexists(args.workspace) and not os.path.lexists(args.admission),
            'fresh workspace/admission required')
    builds=[]
    for label in ('stock','ox'):
        path=Path(getattr(args,label)).resolve();receipt=document(path)
        builds.append(dict(label=label,compiler=str(Path(receipt['compiler']).resolve()),
            src=str((Path(receipt['workspace'])/'src').resolve()),receipt=str(path)))
    plan=dict(schema='unison-cached-benchmark-plan/1',workspace=args.workspace,
              limits=LIMITS,builds=builds,source_sha256={name:hashlib.sha256(
                  read_bytes(ROOT/name,16*1048576)).hexdigest() for name in sources()},
              artifact_sha256={})
    plan['artifact_sha256']={name:hashlib.sha256(read_bytes(name,256*1048576)).hexdigest()
                            for name in artifact_paths(plan)}
    qualification=document(Path(args.qualification).resolve())
    require(qualification['state']=='SOURCE_CONTROLS_PASS_NO_BENCHMARK_MATRIX'
            and qualification['source_sha256']==plan['source_sha256'],
            'current exact source qualification required')
    plan_path=Path(args.plan).resolve();write(plan_path,plan)
    digest=hashlib.sha256(read_bytes(plan_path,1048576)).hexdigest()
    checked_plan(str(plan_path),digest)
    command=worker_argv(plan,str(plan_path),digest)
    launch=[PYTHON,str(ROOT/'tests/cached_benchmark/entry.py'),'--plan',str(plan_path),
            '--plan-sha256',digest,'--admission',args.admission,'--admission-sha256',
            'ROOT_PUBLISHED_SHA_REQUIRED']
    request=dict(schema='unison-cached-benchmark-request/1',state='PREPARED_NOT_ADMITTED',
        target=TARGET,command=command,launch_argv=launch,workspace=args.workspace,
        proposed_admission=args.admission,plan=dict(path=str(plan_path),sha256=digest),
        cpu_credits=8,limits=LIMITS,
        prerequisites=[dict(path=str(Path(args.qualification).resolve()),
            sha256=hashlib.sha256(read_bytes(Path(args.qualification).resolve(),1048576)).hexdigest())],
        execution_source_sha256={str(ROOT/name):value for name,value in plan['source_sha256'].items()},
        io_manifest_sha256='f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636',
        requested_logical_digest_read_bytes=9*1024**3,generated_fixture_bytes=32*1048576,
        scope='One generated cached digest cohort,48serial native batches/288jobs, stock/Ox1/2/4/6workers+2owner within8. No SDK/Adobe/camera/Photo/nativeUI/original/18borrow.300s observation retains unknown; budgets are declared, not physical caps. No quiet-window or end-to-end throughput claim.')
    write(Path(args.request).resolve(),request)
    print(json.dumps(dict(plan=str(plan_path),plan_sha256=digest,
                          request=str(Path(args.request).resolve()),admission_created=False)))


if __name__=='__main__':
    try:main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(repr(error),flush=True))
