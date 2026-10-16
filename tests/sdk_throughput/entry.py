"""Exact-admission finite receiving comparison; no CPU-only native route."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_io_pool import read_manifest
from sdk_multifile.entry import sources as shared_sources
from invocation import artifact_sha,SCRIPT_NAMES
from sdk_multifile.plan import plan as command_plan,BUILD
from sdk_multifile.clone import FIELDS
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

TARGET='sdk-receiving-comparison'
PYTHON='/Users/alexy/.local/share/uv/python/cpython-3.14.6-macos-x86_64-none/bin/python3.14'
PYTHON_SHA='56f92de75b49e94ceb314dba0a2ed6175156f6c61739e4827c28beca32948d29'
PARAMETERS=dict(cpu_credits=8,cases=24,cli_calls=24,sdk_calls=48,endpoint_workers=[1,3],
                observation_seconds=600,worker_seconds=570,per_cli_seconds=120,per_sdk_seconds=90,
                declared_logical_io_bytes=32*1073741824,io_budget_enforced=False,
                maximum_result_bytes=16*1048576)


def require(value,message):
    if not value:raise ValueError(message)


def sources():
    result=shared_sources()
    result.update({str(p):artifact_sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))})
    return result


def checked_plan(path,digest):
    from sdk_multifile.entry import _checked_packet
    from sdk_throughput.plan import comparison
    path=Path(path);require(path.is_absolute() and path.resolve()==path,'canonical plan path required')
    d=read_manifest(path,digest)
    packet=_checked_packet(d,schema='unison-sdk-throughput-plan/1',parameters=PARAMETERS,
                           source_pins=sources(),workspace_prefix='u-str-')
    comparison(packet['binaries'],packet['tool'],packet['workspace'])
    return packet


def child_argv(path,digest,workspace):
    return [sys.executable,str(Path(__file__).resolve()),'--worker','--plan',str(path),'--plan-sha256',digest,'--workspace',str(workspace)]


def worker_entry(args,plan):
    from shared_binding import verify
    from sdk_multifile import clone
    from sdk_throughput import worker
    from persistence import save
    w=Path(args.workspace);require(str(w)==plan['workspace'],'worker namespace differs')
    end=time.monotonic()+3
    while True:
        try:start=read_manifest(w/'SHARED-START.json',artifact_sha(w/'SHARED-START.json'));break
        except (ValueError,OSError):
            require(time.monotonic()<end,'actual parent START absent');time.sleep(.005)
    verify(start,child_argv(args.plan,args.plan_sha256,w),parent_pid=os.getppid(),worker_pid=os.getpid(),target=TARGET)
    require(artifact_sha(PYTHON)==plan['interpreter']['sha256'],'interpreter changed under IO')
    for item in [*plan['binaries'].values(),plan['tool']]:
        require(artifact_sha(item['path'])==item['sha256'],'execution artifact changed under IO')
    def check():
        for item in plan['inputs']:
            require(clone.stamp(os.lstat(item['path']))==item['identity'],'borrowed input epoch changed')
    return worker.execute(plan,w,time.monotonic()+570,
        prepare_sources=lambda directory,label:clone.prepare_inputs(plan['inputs'],plan['sources'],directory/'left'),
        check_sources=check,read_proxy=lambda path:read_manifest(path,artifact_sha(path)),persist=lambda value:save(w,value))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['plan','plan-sha256']:parser.add_argument('--'+name,required=True)
    for name in ['workspace','admission','admission-sha256']:parser.add_argument('--'+name)
    parser.add_argument('--worker',action='store_true');a=parser.parse_args()
    plan=checked_plan(a.plan,a.plan_sha256);w=Path(plan['workspace'])
    if a.worker:
        try:worker_entry(a,plan);return 0
        except UnresolvedOwnership:raise
        except BaseException as error:
            if not (w/'RESULT.json').exists():
                from persistence import save
                save(w,dict(schema='unison-sdk-receiving-comparison-worker/1',complete=False,phase='PREPARING_NO_CALL',
                            cases=[],invocations=[],semantic_eligibility_claimed=False,pixel_equivalence_claimed=False,throughput_qualified=False,failure=repr(error)))
            raise
    require(a.admission and a.admission_sha256 and not a.workspace,'fresh exact IO admission required')
    require(not w.exists() and not w.is_symlink(),'workspace consumed; no replay')
    from shared_dispatch import checked_io_request,run
    argv=child_argv(a.plan,a.plan_sha256,w);ad=dict(path=a.admission,sha256=a.admission_sha256)
    checked_io_request(ad,TARGET,argv,w,8);os.umask(0o077);w.mkdir(mode=0o700)
    return run(TARGET,argv,w,8,io_admission=ad)


if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps(dict(state='SDK_COMPARISON_OWNERSHIP_RETAINED',error=repr(error),
            retained_fds=list(getattr(error,'retained_fds',())),uncertain_closes=list(getattr(error,'uncertain_closes',())))),file=sys.stderr,flush=True))
