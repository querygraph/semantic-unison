"""One-use component RPC owner. Source only until a fresh exact Root admission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import read, load, save
from component_remote.contract import checked_plan, check_artifacts, sources, PARAMETERS, CASES
from component_remote.audit import audit_prefix, functional
from shared_cpu_pool import Pool, UnresolvedOwnership, authorized_unison_tokens, close_descriptors, require, unique_object
from shared_io_pool import (GlobalPool, CANONICAL_MANIFEST, CANONICAL_SHA256,
                            read_manifest, try_io_cpu_bundle, close_unstarted)
from shared_dispatch import POLICY, MANIFEST, MANIFEST_SHA
from shared_process_owner import require_ownership_support, retain_after_record, settle
from ownership import OwnedGroup

def unknown(path,error,**facts):
    retain_after_record(lambda:save(path,dict(error=repr(error),
      retained_fds=list(getattr(error,'retained_fds',())),
      uncertain_closes=list(getattr(error,'uncertain_closes',())),**facts)))

def inherited_identities():
    indexes=authorized_unison_tokens(read(POLICY))
    cpu_raw=read(MANIFEST);io_raw=read(CANONICAL_MANIFEST)
    require(hashlib.sha256(cpu_raw).hexdigest()==MANIFEST_SHA and
      hashlib.sha256(io_raw).hexdigest()==CANONICAL_SHA256,'inherited manifest pin differs')
    cpu=json.loads(cpu_raw,object_pairs_hook=unique_object)
    io=json.loads(io_raw,object_pairs_hook=unique_object)['barrier']['identity']
    return [(io['device'],io['inode'])]+[(cpu['credits'][i]['device'],cpu['credits'][i]['inode']) for i in indexes]

def worker(packet_path):
    packet=load(packet_path);plan=packet['plan'];workspace=checked_plan(plan)
    require(Path(packet_path)==workspace/'WORKER-PACKET.json' and
      type(packet['parent_pid']) is int and packet['parent_pid']==os.getppid(),'worker parent/packet mismatch')
    rows=packet['inherited_fds']
    require(len(rows)==9 and len({r['fd'] for r in rows})==9,'nine inherited grant descriptions required')
    require([(r['device'],r['inode']) for r in rows]==inherited_identities(),
            'worker descriptions are not the authorized canonical IO+Unison00..07 set')
    for row in rows:
        value=os.fstat(row['fd']);require((value.st_dev,value.st_ino)==(row['device'],row['inode']),
                                         'inherited resource identity changed')
    result={'schema':'component-remote-result/1','complete':False,'cases':[]}
    original=None
    try:
        from component_remote.case import execute
        for index in range(len(CASES)):
            check_artifacts(plan)
            result['cases'].append(execute(plan,index,packet['deadline_monotonic']))
        result['complete']=True;result['audit']=functional(plan,result,workspace)
    except UnresolvedOwnership as error:
        unknown(workspace/'WORKER-UNKNOWN.json',error,pid=os.getpid())
    except BaseException as error:
        original=error;result['complete']=False;result['failure']=repr(error)
    try:
        rows=audit_prefix(plan,workspace)
        save(workspace/'WORKER-RESULT.json',result)
        save(workspace/'REMOTE-SETTLED.json',{'calls':rows,'worker_finished_starting_calls':True,
             'functional_pass':original is None})
    except BaseException as error:
        unknown(workspace/'WORKER-UNKNOWN.json',error,pid=os.getpid(),
                original_failure=repr(original),original_exception_retained=original is not None)
    return 0 if original is None else 1

def owner(plan_path,admission_path,admission_sha):
    require_ownership_support()
    plan_raw=read(plan_path);plan=json.loads(plan_raw,object_pairs_hook=unique_object);workspace=checked_plan(plan)
    admission=read_manifest(admission_path,admission_sha)
    require(admission['state']=='ROOT_ADMITTED_ONE_COMPONENT_RPC_JOB' and
      admission['plan_sha256']==hashlib.sha256(plan_raw).hexdigest() and admission['workspace']==str(workspace) and
      admission['launch_argv_without_admission_sha256']==[sys.executable,str(Path(__file__)),
       '--plan',str(plan_path),'--admission',str(admission_path)] and
      admission['start_deadline_unix']>time.time(),'fresh exact component admission required')
    workspace.mkdir(mode=0o700) # one-use, never retry/replace
    save(workspace/'ATTEMPT.json',{'owner_pid':os.getpid(),'admission_sha256':admission_sha})
    io=cpu=child=None;closed=False
    try:
        indexes=authorized_unison_tokens(read(POLICY))
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),
                                 Pool.read(MANIFEST,MANIFEST_SHA),indexes)
        if bundle is None:
            save(workspace/'NOT-STARTED.json',{'state':'CONTENDED_PARTIALS_CLOSED'});return 2
        io,cpu=bundle
        checked_plan(plan);check_artifacts(plan)
        require(read(plan_path)==plan_raw and read_manifest(admission_path,admission_sha)==admission and
          admission['start_deadline_unix']>time.time(),'plan/admission changed or expired before dispatch')
        fds=list(io.fds)+list(cpu.fds);observation=time.monotonic()+PARAMETERS['owner_seconds']
        packet={'plan':plan,'parent_pid':os.getpid(),'deadline_monotonic':observation-40,
          'inherited_fds':[{'fd':fd,'device':os.fstat(fd).st_dev,'inode':os.fstat(fd).st_ino} for fd in fds]}
        save(workspace/'WORKER-PACKET.json',packet)
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC
        streams=[]
        try:
            streams.append(os.open(workspace/'STDOUT.txt',flags,0o600))
            streams.append(os.open(workspace/'STDERR.txt',flags,0o600))
            child=OwnedGroup([sys.executable,str(Path(__file__)),'--worker',str(workspace/'WORKER-PACKET.json')],
              strict_group_settlement=True,pass_fds=tuple(fds),stdin=subprocess.DEVNULL,
              stdout=streams[0],stderr=streams[1])
        finally:close_descriptors(streams)
        save(workspace/'START.json',{'owner_pid':os.getpid(),'worker_pid':child.pid,
          'admission_sha256':admission_sha,'cpu_indexes':list(indexes),'io_mode':'EX_GLOBAL',
          'owner_observation_deadline_monotonic':observation,'inherited_fds':packet['inherited_fds']})
        require(child.await_terminal(max(0,observation-time.monotonic())),
                'worker observation elapsed; retain all remote owners, no aggregate kill')
        calls=audit_prefix(plan,workspace);recorded=load(workspace/'REMOTE-SETTLED.json')
        require(recorded['worker_finished_starting_calls'] is True and recorded['calls']==calls,
                'independent prefix differs from worker settlement')
        stopped=settle(child,time.monotonic()+5)
        result=load(workspace/'WORKER-RESULT.json');passed=stopped['returncode']==0
        if passed:functional(plan,result,workspace)
        require(recorded['functional_pass'] is passed and sources()==plan['execution_source_sha256'],
                'result/settlement/source mismatch')
        for lease in (cpu,io):
            lease.close_after_verified_settlement(owner_reaped=stopped['reaped'],
              groups_settled=stopped['other_group_members_absent_before_reap'],external_children_settled=True)
        closed=True
        save(workspace/'AGGREGATE-CLOSED.json',{'worker':stopped,'calls':calls,'cpu_closed':True,
          'io_closed':True,'functional_pass':passed,'parent_terminal':'collect owning tool separately'})
        return 0 if passed else 1
    except BaseException as error:
        if closed:raise
        if child is None and not isinstance(error,UnresolvedOwnership):
            try:
                for lease in (cpu,io):
                    if lease is not None:close_unstarted(lease)
            except BaseException as close_error:error=close_error
            else:
                save(workspace/'NOT-STARTED.json',{'known_rollback':True,'failure':repr(error)});return 2
        unknown(workspace/'OWNER-UNKNOWN.json',error,owner_pid=os.getpid(),
          worker_pid=child.pid if child else None,
          known_cpu_fds=list(cpu.fds) if cpu and not cpu.closed else [],
          known_io_fds=list(io.fds) if io and not io.closed else [])

def main():
    os.umask(0o077)
    def interrupted(number,frame):raise InterruptedError('component coordinator signal '+str(number))
    signal.signal(signal.SIGINT,interrupted);signal.signal(signal.SIGTERM,interrupted)
    if len(sys.argv)==3 and sys.argv[1]=='--worker':return worker(sys.argv[2])
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True)
    parser.add_argument('--admission',required=True);parser.add_argument('--admission-sha256',required=True)
    args=parser.parse_args();return owner(args.plan,args.admission,args.admission_sha256)
if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda:print(json.dumps({'error':repr(error),'pid':os.getpid(),
          'retained_fds':list(getattr(error,'retained_fds',())),
          'uncertain_closes':list(getattr(error,'uncertain_closes',()))}),file=sys.stderr,flush=True))
