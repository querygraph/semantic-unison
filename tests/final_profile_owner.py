"""Direct generated parser-pair owner after explicit Photo IO handover.

Exact immutable plan + standing Unison8/EXglobal; no SDK/media/Main/cache. On
unknown, retain owner and descriptors; no signals, retries or broad cleanup.
"""
import argparse,hashlib,json,os,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from shared_child import start


def sha(path,limit=16*1048576):return hashlib.sha256(read_bytes(str(path),limit)).hexdigest()

def closed(out,code):
    c=out['client_cleanup']
    if not (type(out['returncode']) is int and out['returncode']==code and out['timed_out'] is False
            and out['capture_truncated'] is False and type(c['returncode']) is int
            and c['returncode']==code and c['reaped'] is True
            and c['other_group_members_absent_before_reap'] is True
            and c['group_cleanup_before_leader_reap'] is True and c['hard_kill_required'] is False):
        raise ValueError('actual child/group proof incomplete')


def log_sha(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if not (stat.S_ISREG(before.st_mode) and before.st_uid==os.getuid() and before.st_nlink==1
                and 0<=before.st_size<=262144):raise ValueError('bounded owned log required')
        raw=bytearray()
        while len(raw)<before.st_size:
            block=os.read(fd,before.st_size-len(raw))
            if not block:raise ValueError('short child log')
            raw.extend(block)
        fields=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
        if os.read(fd,1) or fields(before)!=fields(os.fstat(fd)) or fields(before)!=fields(os.lstat(path)):
            raise ValueError('child log changed')
        return hashlib.sha256(raw).hexdigest()
    finally:close_descriptors([fd])


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('plan SHA differs')
    packet=json.loads(raw)
    if packet['repository']!=str(ROOT) or packet['state']!='PREPARED_V3_AFTER_ACTUAL_PHOTO_HANDOVER':raise ValueError('exact handover plan required')
    def sources():
        for name,digest in packet['source_sha256'].items():
            if sha(ROOT/name)!=digest:raise ValueError('source changed: '+name)
    sources()
    policy=ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
    if sha(policy)!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352':raise ValueError('policy changed')
    indexes=authorized_unison_tokens(read_bytes(str(policy),1048576))
    if tuple(indexes)!=tuple(range(8)):raise ValueError('standing Unison8 required')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    io_pool=GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256)
    workspace=Path(packet['workspace']);workspace.mkdir(mode=0o700)
    store=None;io=cpu=current=None
    try:
        st=workspace.stat();store=Store(str(workspace),dict(device=st.st_dev,inode=st.st_ino))
        bundle=try_io_cpu_bundle(io_pool,pool,tuple(range(8)))
        if bundle is None:
            store.write('CONTENTION.json',dict(no_child_attempted=True));store.close();return 2
        io,cpu=bundle;sources()
        if sha(packet['interpreter']['path'],64*1048576)!=packet['interpreter']['sha256']:raise ValueError('interpreter changed')
        for job in packet['jobs']:
            if sha(job['compiler_path'],64*1048576)!=job['compiler_sha256']:raise ValueError('compiler changed')
        deadline=time.monotonic()+packet['resources']['pair_observation_seconds']
        fds=(*cpu.fds,*io.fds)
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,commands=[j['argv'] for j in packet['jobs']],
            cpu_indexes=list(range(8)),io_mode='EX_GLOBAL',deadline=deadline))
        print('START',os.getpid(),str(workspace),flush=True)
        audits=[]
        for job in packet['jobs']:
            current=start(job['argv'],dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),pass_fds=fds)
            out=current.finish(deadline);store.write(job['compiler']+'-RUNNER.json',out);closed(out,0)
            if out['command']!=job['argv']:raise ValueError('runner command differs')
            target=Path(job['argv'][job['argv'].index('--receipt')+1]);record=json.loads(read_bytes(str(target),32*1048576))
            if record['compiler']!=job['compiler_path'] or record['compiler_sha256']!=job['compiler_sha256']:raise ValueError('compiler receipt differs')
            if any(packet['source_sha256'].get(name)!=value for name,value in record['source_sha256'].items()):raise ValueError('parser snapshot source differs')
            if record['terminal']!='passed' or record['current_sources_match_snapshot'] is not True:raise ValueError('parser matrix failed')
            if [r['mode'] for r in record['runs']]!=job['modes'] or len(record['sparse_inspector_only'])!=4:raise ValueError('parser scope narrowed')
            fixed=record['runs'][0]['test']
            if fixed['cases']!=job['fixed_case_count_from_fixture_source']:raise ValueError('fixed cases missing')
            calls=[*record['compiler_probes']]
            for row in record['runs']:calls.extend([row['compile'],row['test']])
            for call in calls:
                expected=2 if call.get('detected_assertion') else 0
                closed(call['outcome'],expected)
                if call['outcome']['command']!=call['argv']:raise ValueError('nested command binding differs')
                if call['exit_code']!=expected or log_sha(call['log'])!=call['log_sha256']:raise ValueError('nested raw call/log differs')
            if sha(record['artifact_manifest'],32*1048576)!=record['artifact_manifest_sha256']:raise ValueError('artifact manifest changed')
            sources()
            audit=dict(compiler=job['compiler'],cases=fixed['cases'],assertions=fixed['assertions'],
                modes=job['modes'],sparse_cases=4,nested_children=len(calls),runner=out['client_cleanup'],
                receipt=dict(path=str(target),sha256=sha(target,32*1048576)))
            audits.append(audit);store.write(job['compiler']+'-AUDIT.json',audit)
            print('PASS',job['compiler'],fixed['cases'],fixed['assertions'],flush=True)
        sources();store.write('RESULT.json',dict(complete=True,audits=audits,all_nested_children_closed=True,
            no_sdk_or_photos=True,parent_tool_terminal_proved=False))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('CLOSED',str(workspace),flush=True);return 0
    except BaseException as error:
        retain_after_record(lambda:print('RETAIN',repr(error),str(workspace),flush=True))


if __name__=='__main__':raise SystemExit(main())
