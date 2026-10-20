#!/usr/bin/env python3
"""One explicitly admitted generated negative SDK receiving matrix; check-plan is metadata only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256
from shared_process_owner import retain_after_record
from sdk_host_matrix.shared_binding import verify as verify_binding,CPU_POLICY
from sdk_negative_receiving import admission as A,metadata,inventory,owner,runtime
from sdk_negative_receiving import parent_runtime as parent
from sdk_merge_receiving import artifacts
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.child_entry import diagnostic

CPU_MANIFEST='/Users/alexy/src/photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'
CPU_SHA='4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd'


def document(ref):
    A.reference(ref);raw=read_bytes(ref['path'],1048576)
    A.require(hashlib.sha256(raw).hexdigest()==ref['sha256'],'reviewed document SHA differs')
    return metadata.document(raw)


def checked(plan_ref):
    return metadata.checked(plan_ref,execution_sources=inventory.execution(),
                            production_sources=inventory.production(),expected_uid=os.getuid())


def request_check(request,packet,plan_ref):
    fields={'schema','state','target','plan','workspace','command','execution_sha256',
            'production_sha256','limits'}
    A.require(type(request) is dict and set(request)==fields
        and request['schema']=='unison-current-sdk-negative-receiving-request/1'
        and request['state']=='PREPARED_UNADMITTED' and request['target']=='current-sdk-negative-receiving'
        and A.exact(request['plan'],plan_ref) and request['workspace']==packet['workspace']
        and A.exact(request['command'],A.worker_command(packet,plan_ref))
        and A.exact(request['execution_sha256'],packet['execution_sha256'])
        and A.exact(request['production_sha256'],packet['production_sha256'])
        and A.exact(request['limits'],packet['limits']),'exact immutable merge request differs')


def worker(packet,plan_ref,workspace):
    A.require(workspace==packet['workspace'] and sys.executable==A.PYTHON,'exact worker context required')
    root=Path(workspace);limit=time.monotonic()+3
    while not (root/'OWNER-START-READY').exists():
        A.require(time.monotonic()<limit,'parent START not fully published');time.sleep(.005)
    native=root.lstat();store=Store(str(root),dict(device=native.st_dev,inode=native.st_ino))
    binding=None;resource_close_attempted=False
    try:
        start=store.read_json('OWNER-START.json',expected_sha256=None)
        bound=store.read_json('ADMISSION-BOUND.json',expected_sha256=None)
        A.require(start['admission_nonce']==bound['admission_nonce']
            and A.exact(bound['plan'],plan_ref),'worker admission ancestry differs')
        binding=verify_binding(start,A.worker_command(packet,plan_ref),parent_pid=os.getppid(),
            worker_pid=os.getpid(),target='current-sdk-negative-receiving',credits=8)
        store.write('WORKER-BINDING.json',dict(schema='unison-current-negative-worker-binding/1',
            parent_pid=os.getppid(),worker_pid=os.getpid(),resource_fds=start['inherited_resource_fds'],binding=binding))
        artifacts.verify(packet)
        deadline=min(time.monotonic()+packet['limits']['worker_seconds'],start['owner_observation_deadline']-30)
        A.require(math.isfinite(deadline) and time.monotonic()<deadline,'worker observation already expired')
        runtime.run(packet,store,start,deadline)
        # Recheck metadata and executable declarations before retiring inherited
        # leases; parent will separately repeat raw records and output hashes.
        checked(plan_ref);artifacts.verify(packet)
        store.close()
        resource_close_attempted=True
        close_descriptors(binding['inherited_fds'])
        return 0
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership(
            'merge worker incomplete; retain directory, children and inherited grant')
        if retained is not error:retained.original_failure=error
        retained.merge_worker_store=store
        excluded=set(getattr(retained,'uncertain_fds',()))
        known=list(retained.retained_fds)
        if binding is not None and not resource_close_attempted:
            known.extend(binding['inherited_fds'])
        if not store.closed:known.append(store.fd)
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in known if fd not in excluded))
        if retained is error:raise
        raise retained from error


def run_owner(packet,plan_ref,admission_ref):
    admission=document(admission_ref);request_ref=admission['request']
    request_check(document(request_ref),packet,plan_ref)
    A.check(admission,packet,request_ref=request_ref,plan_ref=plan_ref,
            command=A.worker_command(packet,plan_ref),now=time.time())
    A.require(authorized_unison_tokens(read_bytes(CPU_POLICY,65536))==tuple(range(8)),
              'current standing grant differs')
    cpu=Pool.read(CPU_MANIFEST,CPU_SHA);io=GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256)
    def audit(packet,store,outcome):
        checked(plan_ref);artifacts.verify(packet)
        return parent.audit(packet,store,outcome)
    env=dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',
        HOME=packet['workspace'],TMPDIR=packet['workspace'],PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
    return owner.run(packet,admission,request_ref=request_ref,plan_ref=plan_ref,
        cpu_pool=cpu,io_pool=io,artifact_check=artifacts.verify,parent_audit=audit,environment=env)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True);parser.add_argument('--plan-sha256',required=True)
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--worker',action='store_true')
    modes.add_argument('--check-plan',action='store_true')
    parser.add_argument('--workspace');parser.add_argument('--admission');parser.add_argument('--admission-sha256')
    args=parser.parse_args(argv)
    A.require(sys.executable==A.PYTHON,'qualified pinned Python required')
    if args.worker or args.check_plan:
        A.require(args.admission is None and args.admission_sha256 is None,'no admission override in child/check mode')
    else:A.require(args.admission is not None and args.admission_sha256 is not None,'fresh explicit admission required')
    plan_ref=dict(path=args.plan,sha256=args.plan_sha256)
    packet,_,proof=checked(plan_ref)
    if args.check_plan:
        A.require(args.workspace is None,'check-plan cannot consume a workspace')
        print(json.dumps(proof));return 0
    if args.worker:return worker(packet,plan_ref,args.workspace)
    A.require(args.workspace is None,'owner workspace comes only from reviewed plan')
    result=run_owner(packet,plan_ref,dict(path=args.admission,sha256=args.admission_sha256))
    print(json.dumps(result));return 0 if result['state']=='OWNED_WORKER_AND_EXTERNAL_CHILDREN_CLOSED' else 75


if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print('MERGE-OWNER-RETAINED '+json.dumps(diagnostic('owner',error)),
                                         file=sys.stderr,flush=True))
