"""Exact inherited canonical FD metadata guard; not lock/settlement authority."""
import os,stat,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from shared_cpu_pool import Pool
from shared_io_pool import GlobalPool
from shared_dispatch import MANIFEST,MANIFEST_SHA
CPU_POLICY=Path('/Users/alexy/src/photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json')
CPU_POLICY_SHA='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352'
IO_MANIFEST=Path('/Users/alexy/src/photo/preview-generator/SHARED-PHYSICAL-IO-POOL-v1.json')
IO_SHA='f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636'
TARGET='shared-sdk-host-matrix'

def inventory(credits=8):
    # Manifest readers touch metadata only, never acquire or create pool locks.
    from shared_io_pool import read_manifest
    policy=read_manifest(CPU_POLICY,CPU_POLICY_SHA)
    indexes=policy['locking']['defaultUnisonTokenIndexes']
    if policy['version']!=3 or policy['defaultShared']['unison']['cpuCredits']!=8 or indexes!=list(range(8)):
        raise ValueError('exact pinned standing Unison00..07 required')
    if type(credits) is not int or credits not in (8,18):raise ValueError('known descriptor inventory required')
    cpu=Pool.read(MANIFEST,MANIFEST_SHA);io=GlobalPool.read(IO_MANIFEST,IO_SHA)
    return tuple(cpu.token_identities[i] for i in range(credits))+((io.barrier_identity['device'],io.barrier_identity['inode']),)

def verify(start,command,*,parent_pid,worker_pid,observe=os.fstat,target=TARGET,credits=8):
    def require(v,s):
        if not v:raise ValueError(s)
    require(type(credits) is int and (credits==8 or credits==18 and target=='sync-auto-cohort'),'explicit known grant size required')
    require(type(parent_pid) is int and parent_pid>0 and type(worker_pid) is int and worker_pid>0,'actual parent/worker IDs required')
    require(target in ('current-sdk-merge','sync-auto-cohort',TARGET,'cached-sha-benchmark','sdk-multifile-receive','sdk-receiving-comparison','mixed-sdk-metadata-hash','private-maker-slice','private-maker-model','all-scanned-sdk-validate'),'known exact shared IO target required')
    require(type(start) is dict and type(start.get('owner_pid')) is int and type(start.get('child_pid')) is int
        and start['owner_pid']==parent_pid and start['child_pid']==worker_pid
        and start.get('target')==target and start.get('command')==command
        and type(start.get('cpu_credits')) is int and start['cpu_credits']==credits
        and type(start.get('token_indexes')) is list
        and all(type(i) is int for i in start['token_indexes'])
        and start['token_indexes']==list(range(credits)) and start.get('io_mode')=='EX_GLOBAL','actual parent/command/grant/EXglobal binding differs')
    return descriptors(start.get('inherited_resource_fds'),credits=credits,observe=observe)


def descriptors(rows,*,credits=8,observe=os.fstat):
    """Inspect canonical inherited metadata only, never infer a grant or locks."""
    def require(v,s):
        if not v:raise ValueError(s)
    require(type(credits) is int and credits in (8,18),'known descriptor inventory required')
    expected=inventory() if credits==8 else inventory(credits=18)
    require(type(rows) is list and len(rows)==credits+1,'exact inherited descriptor count required')
    fds=[]
    for row,identity in zip(rows,expected):
        require(type(row) is dict and set(row)=={'fd','device','inode'}
            and all(type(row[k]) is int and row[k]>=0 for k in row)
            and row['fd']>=3 and row['fd'] not in fds and (row['device'],row['inode'])==identity,'typed unique ordered canonical identity required')
        observed=observe(row['fd'])
        require((observed.st_dev,observed.st_ino)==identity and stat.S_ISREG(observed.st_mode)
            and stat.S_IMODE(observed.st_mode)==0o600 and observed.st_uid==os.getuid()
            and observed.st_nlink==1 and observed.st_size==0,'actual inherited description differs')
        fds.append(row['fd'])
    return dict(inherited_fds=tuple(fds),canonical_metadata_bound=True,
        lock_ownership_independently_proved=False,resource_release_authorized=False)
