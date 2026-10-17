"""One-use mixed-peer entry; a fresh exact Root admission is mandatory."""
import argparse
import copy
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import read,load,save
from component_remote.coordinator import inherited_identities
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens,close_descriptors,require
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,read_manifest,try_io_cpu_bundle,close_unstarted
from shared_dispatch import POLICY,MANIFEST,MANIFEST_SHA
from shared_process_owner import require_ownership_support,retain_after_record
from ownership import OwnedGroup
from mixed_peer_compatibility.contract import LIMITS
from mixed_peer_compatibility.worker import execute
from mixed_peer_compatibility.coordinator import observe_and_reap


def digest(path):return hashlib.sha256(read(path)).hexdigest()

def source_paths():
    paths=set((ROOT/'tests/mixed_peer_compatibility').glob('*.py'))
    paths.update((ROOT/'tests/component_remote').glob('*.py'))
    paths.update((ROOT/'bench/sync').glob('*.py'))
    paths.update(ROOT/name for name in ('tests/shared_cpu_pool.py','tests/shared_io_pool.py',
        'tests/shared_dispatch.py','tests/manual.py','tests/shared_process_owner.py',
        'tests/private_camera_receiving/close.py','tests/sdk_host_matrix/shared_child.py'))
    paths.update(p for p in (ROOT/'src').rglob('*') if p.is_file() and
        p!=ROOT/'src/ubase/projectInfo.ml' and (p.suffix in ('.ml','.mli','.c','.h') or
        p.name in ('Makefile','Makefile.OCaml','dune') or p.name.endswith('.ox.mli.in')))
    return paths


def checked_plan(path,expected):
    plan=read_manifest(path,expected)
    require(plan['schema']=='unison-mixed-peer/1' and plan['limits']==LIMITS,'fixed mixed-peer scope required')
    root=Path(plan['workspace'])
    require(root.parent==Path('/private/tmp') and root.name.startswith('u-mp-') and len(str(root))<40,'short fresh mixed-peer namespace required')
    require(set(plan['artifacts'])=={'stock','ox','old-stock'},'exact artifact set required')
    for item in plan['artifacts'].values():
        require(Path(item['path']).is_absolute() and len(item['sha256'])==64,'absolute pinned artifact required')
    require(plan['io_manifest_sha256']==CANONICAL_SHA256 and plan['cpu_manifest_sha256']==MANIFEST_SHA,
            'canonical manifests required')
    require(plan['execution_source_sha256']=={str(p):digest(p) for p in source_paths()},
            'exact current mixed-peer source closure differs')
    require(plan['interpreter']=={'path':sys.executable,'sha256':digest(sys.executable)},
            'qualified interpreter pin differs')
    return plan


def verify_artifacts(plan):
    """Called only after the worker verifies inherited IO/CPU ownership."""
    require(set(plan['current_builds'])=={'stock','ox'},'two current qualified build receipts required')
    for label,pin in plan['current_builds'].items():
        build=read_manifest(pin['path'],pin['sha256'])
        require(build['complete'] is True and type(build['build_exit']) is int
                and build['build_exit']==0 and type(build['selftest_exit']) is int
                and build['selftest_exit']==0 and build['binary']==plan['artifacts'][label]['path']
                and build['binary_sha256']==plan['artifacts'][label]['sha256'],
                'successful current build/selftest/binary binding differs')
        require(digest(build['compiler'])==build['compiler_sha256'],'compiler pin differs')
        production={name:sha for name,sha in build['source_sha256'].items() if name.startswith('src/')}
        require(bool(production),'build production inventory missing')
        for name,sha in production.items():
            relative=Path(name)
            require('..' not in relative.parts and digest(ROOT/relative)==sha,
                    'build no longer matches current production source')
    for item in plan['artifacts'].values():
        require(digest(item['path'])==item['sha256'],'artifact changed after IO acquisition')


def retain(path,error,owner=None):
    retain_after_record(lambda:save(path,dict(error=repr(error),owner_pid=os.getpid(),
        child_pid=owner.pid if owner else None,retained_fds=list(getattr(error,'retained_fds',())),
        uncertain_closes=list(getattr(error,'uncertain_closes',())))))


def worker(packet_path):
    root=Path(packet_path).parent
    saved={'complete':False,'cases':[],'invocations':[]};counter=0
    def persist(result):
        nonlocal saved,counter
        saved=copy.deepcopy(result)
        save(root/('WORKER-SNAPSHOT-%03d.json'%counter),saved);counter+=1
    try:
        packet=load(packet_path)
        plan=checked_plan(packet['plan_path'],packet['plan_sha256'])
        require(root==Path(plan['workspace']) and Path(packet_path)==root/'WORKER-PACKET.json'
                and type(packet['parent_pid']) is int and packet['parent_pid']==os.getppid(),
                'worker packet/parent mismatch')
        rows=packet['inherited_fds']
        require(len(rows)==9 and len({r['fd'] for r in rows})==9
                and [(r['device'],r['inode']) for r in rows]==inherited_identities(),
                'exact inherited IO+CPU grant required')
        for row in rows:
            observed=os.fstat(row['fd'])
            require((observed.st_dev,observed.st_ino)==(row['device'],row['inode']),
                    'inherited FD identity differs')
        verify_artifacts(plan)
        result=execute({k:v['path'] for k,v in plan['artifacts'].items()},root,
                       time.monotonic()+LIMITS['owner_observation_seconds']-10,persist)
    except UnresolvedOwnership as error:retain(root/'WORKER-UNKNOWN.json',error)
    except BaseException as error:
        result=saved;result['failure']=repr(error)
        # No retained_call can precede its persisted Journal INTENT. This is
        # source-bound no-call evidence, not an absent-process inference.
        if not result['invocations']:result['no_calls_started']=True
    save(root/'WORKER-RESULT.json',result)
    return 0 if result['complete'] else 1


def owner(plan_path,plan_sha,admission_path,admission_sha):
    require_ownership_support()
    plan=checked_plan(plan_path,plan_sha);root=Path(plan['workspace'])
    admission=read_manifest(admission_path,admission_sha)
    require(admission['state']=='ROOT_ADMITTED_ONE_MIXED_PEER_JOB'
            and admission['plan_sha256']==plan_sha and admission['workspace']==str(root)
            and admission['start_deadline_unix']>time.time(), 'fresh exact mixed-peer admission required')
    root.mkdir(mode=0o700)
    save(root/'ATTEMPT.json',dict(owner_pid=os.getpid(),admission_sha256=admission_sha))
    io=cpu=child=None;streams=[];closed=False
    try:
        pool=Pool.read(MANIFEST,MANIFEST_SHA)
        global_io=GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256)
        bundle=try_io_cpu_bundle(global_io,pool,authorized_unison_tokens(read(POLICY)))
        if bundle is None:
            save(root/'NOT-STARTED.json',{'state':'CONTENDED_KNOWN_ROLLBACK'});return 2
        io,cpu=bundle
        checked_plan(plan_path,plan_sha)
        if admission['start_deadline_unix']<=time.time():
            close_unstarted(cpu);close_unstarted(io);closed=True
            save(root/'NOT-STARTED.json',{'state':'EXPIRED_AFTER_ACQUISITION_KNOWN_CLOSED'});return 2
        fds=io.fds+cpu.fds
        rows=[dict(fd=fd,device=os.fstat(fd).st_dev,inode=os.fstat(fd).st_ino) for fd in fds]
        packet=root/'WORKER-PACKET.json'
        save(packet,dict(plan_path=str(plan_path),plan_sha256=plan_sha,parent_pid=os.getpid(),inherited_fds=rows))
        for name in ('WORKER-STDOUT.txt','WORKER-STDERR.txt'):
            streams.append(os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_CLOEXEC|os.O_NOFOLLOW,0o600))
        child=OwnedGroup([sys.executable,str(Path(__file__).resolve()),'--worker',str(packet)],
                         stdin=subprocess.DEVNULL,stdout=streams[0],stderr=streams[1],pass_fds=fds)
        # Consume parent copies once. On uncertain close the carrier prevents
        # this coordinator from retrying a numeric FD or dropping its child.
        parent_streams=streams;streams=[];close_descriptors(parent_streams)
        save(root/'START.json',dict(owner_pid=os.getpid(),worker_pid=child.pid,unix=time.time(),inherited_fds=rows))
        result=observe_and_reap(child,lambda:load(root/'WORKER-RESULT.json'),
            {k:v['path'] for k,v in plan['artifacts'].items()},root,
            time.monotonic()+LIMITS['owner_observation_seconds'])
        cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        closed=True
        save(root/'CLOSED.json',dict(result,io_cpu_closed=True,parent_tool_terminal='collect separately'))
        return 0 if result['functional_pass'] else 1
    except BaseException as error:
        if closed:raise
        if child is None and not isinstance(error,UnresolvedOwnership):
            try:
                pending=streams;streams=[];close_descriptors(pending)
                if cpu is not None:close_unstarted(cpu)
                if io is not None:close_unstarted(io)
            except BaseException as cleanup_error:
                cleanup_error.original_setup_failure=error
                retain(root/'OWNER-UNKNOWN.json',cleanup_error,child)
            save(root/'NOT-STARTED.json',{'state':'PRELAUNCH_REFUSAL_KNOWN_CLOSED','failure':repr(error)})
            return 2
        # No automatic signals/retry/lease release after uncertain launch or
        # partial closure. Existing objects and known streams stay in scope.
        retain(root/'OWNER-UNKNOWN.json',error,child)


def main():
    os.umask(0o077)
    def interrupted(number,frame):raise InterruptedError('mixed-peer owner signal '+str(number))
    signal.signal(signal.SIGINT,interrupted);signal.signal(signal.SIGTERM,interrupted)
    if len(sys.argv)==3 and sys.argv[1]=='--worker':return worker(sys.argv[2])
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','plan-sha256','admission','admission-sha256'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args()
    return owner(args.plan,args.plan_sha256,args.admission,args.admission_sha256)
if __name__=='__main__':
    try:raise SystemExit(main())
    except UnresolvedOwnership as error:retain(Path('/private/tmp')/('unison-mixed-peer-unknown-%d.json'%os.getpid()),error)
