"""Current stock/Ox versus unmodified8772 default-RPC loopback qualification.

Retained batch transport, not the older cancellation proxy. Four fresh cases,
seed/update/noop, generated8192B only; no SDK/Photo/real SSH or old admission.
"""
import argparse,copy,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.runtime import program,child_environment
from sdk_merge_receiving.admission import PYTHON
from batch_pair import invoke
from batch_commands import schedule
from component_remote.io import identity
from mixed_peer_compatibility.worker import fixture
from mixed_peer_compatibility.entry import verify_upstream_baseline
from final_clone_stage_owner import write_bytes
from final_profile_owner import sha

CASES=(('stock','current-client'),('stock','upstream-client'),('ox','current-client'),('ox','upstream-client'))
PHASES=('seed','update','noop')


def command(artifacts,root,index):
    if type(index) is not int or not 0<=index<4 or set(artifacts)!={'stock','ox','old-stock'}:
        raise ValueError('exact current/upstream role matrix required')
    label,orientation=CASES[index];old_client=orientation=='upstream-client'
    client=artifacts['old-stock' if old_client else label]['path'];server=artifacts[label if old_client else 'old-stock']['path']
    current=schedule(artifacts[label]['path'],artifacts[label]['path'],str(root),mode='semantic',workers=2)['rows'][0]['server_flags']
    old=['-maxthreads','2'];cf=old if old_client else current;sf=current if old_client else old
    directory=root/str(index)
    argv=[client,str(directory/'left'),'ssh://localhost/'+str(directory/'right'),'-sshcmd',str(root/'launcher.py'),'-servercmd',server,
        '-batch','-auto','-fastcheck','false','-times',*cf]
    return dict(label=label,orientation=orientation,client=client,server=server,command=argv,server_flags=sf,
        server_command=[server,'-server','__new-rpc-mode',*sf],configured_endpoint_plus_owner_bound=6,reserved_credits=8)


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('upstream pair plan SHA differs')
    packet=json.loads(raw)
    if packet['schema']!='unison-final-default-upstream-plan/1' or packet['repository']!=str(ROOT) or sys.executable!=PYTHON:
        raise ValueError('exact current default-RPC context required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('peer source changed '+name)
    sources()
    indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
    if indexes!=tuple(range(8)):raise ValueError('standing8 grant differs')
    root=Path(packet['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-peer-'):raise ValueError('new private peer namespace required')
    root.mkdir(mode=0o700);st=root.lstat();store=Store(str(root),dict(device=st.st_dev,inode=st.st_ino))
    io=cpu=None;attempted=False;current=None
    try:
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,indexes)
        if bundle is None:store.write('CONTENTION.json',dict(native_attempted=False));store.close();return 2
        io,cpu=bundle;production={}
        for ref in packet['build_receipts']:
            data=read_bytes(ref['path'],1048576)
            if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('current build receipt differs')
            build=json.loads(data);artifact=packet['artifacts'][ref['compiler']]
            if not(build['complete'] is True and build['build_exit']==0 and build['selftest_exit']==0
                    and build['binary']==artifact['path'] and build['binary_sha256']==artifact['sha256']):raise ValueError('current binary/build binding differs')
            for name,digest in build['source_sha256'].items():
                if name.startswith('src/'):
                    if name in production and production[name]!=digest:raise ValueError('mixed production builds')
                    production[name]=digest
        def artifacts():
            sources();verify_upstream_baseline(packet)
            for name,digest in production.items():
                if sha(ROOT/name)!=digest:raise ValueError('production source changed')
            for ref in (*packet['artifacts'].values(),packet['interpreter'],*packet['compiler_artifacts'].values()):
                if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('peer artifact changed')
        artifacts();resource_rows=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resource_rows.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resource_rows,cpu_indexes=list(indexes),io_mode='EX_GLOBAL',
            cases=4,calls=12,scope='defaultRPCnewmode loopback/nativebyte integrity; not realSSH/RPCv0/archive-roundtrip/semantic/SDK proof'))
        print('PEER_START',os.getpid(),str(root),flush=True)
        paths=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
        imports='#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr(paths)+'\n'
        scripts={str(root/'launcher.py'):program(root/'launcher.py',imports+'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')}
        deadline=time.monotonic()+300;cases=[]
        for index in range(4):
            row=command(packet['artifacts'],root,index);directory=root/str(index);directory.mkdir(mode=0o700)
            for name in ('left','right','home','tmp','state-client','state-server'):(directory/name).mkdir(mode=0o700)
            source=directory/'left/item.dng';target=directory/'right/item.dng';write_bytes(source,fixture())
            previous=None;records=[]
            for phase in PHASES:
                if phase=='update':
                    replacement=directory/'left/replacement';write_bytes(replacement,fixture(True));os.replace(replacement,source)
                before=identity(source);expected=fixture(phase!='seed');stage='c%d-%s'%(index,phase)
                if time.monotonic()+35>=deadline:raise TimeoutError('no new peer call near observation end')
                artifacts();call_deadline=min(deadline,time.monotonic()+60)
                config=dict(directory=str(root),identity=copy.deepcopy(store.identity),stage=stage,binary=row['server'],flags=row['server_flags'],
                    deadline=call_deadline,worker_pid=os.getpid(),resource_fds=copy.deepcopy(resource_rows))
                proxy=root/(stage+'-proxy.py');scripts[str(proxy)]=program(proxy,imports+'from sdk_merge_receiving.child_entry import proxy_main\nraise SystemExit(proxy_main('+repr(config)+'))\n')
                for path,pin in scripts.items():
                    if sha(path,65536)!=pin['sha256']:raise ValueError('generated peer shim changed')
                intent=store.write(stage+'-INTENT.json',dict(index=index,phase=phase,row=row,proxy_config=config,scripts=copy.deepcopy(scripts),source_before=before))
                env=child_environment(directory,'state-client');env.update(UNISON_MERGE_BINARY=row['server'],UNISON_MERGE_SOCKET=str(root/(stage+'.sock')),UNISON_MERGE_DEADLINE=str(call_deadline))
                attempted=True
                current=invoke(row['command'],env,proxy_command=[PYTHON,'-B',str(proxy)],proxy_environment=child_environment(directory,'state-server'),
                    server_command=row['server_command'],socket_path=str(root/(stage+'.sock')),deadline=call_deadline,pass_fds=(*cpu.fds,*io.fds),store=store,name=stage,
                    read_proxy_bytes=lambda:store.read(stage+'-PROXY.json',maximum=65536))
                if identity(source)!=before or read_bytes(str(source),16384)!=expected or read_bytes(str(target),16384)!=expected:raise ValueError('peer bytes/source fence differ')
                after=identity(target)
                if phase=='noop' and after!=previous:raise ValueError('peer noop replaced or touched target')
                previous=after
                record=dict(phase=phase,pair=current,intent=intent,sha256=hashlib.sha256(expected).hexdigest(),source_identity=before,target_identity=after)
                records.append(record);store.write(stage+'-RESULT.json',record);print('PEER_PHASE_CLOSED',index,phase,flush=True)
            cases.append(dict(index=index,label=row['label'],orientation=row['orientation'],stages=records))
        artifacts();store.write('RESULT.json',dict(complete=True,cases=cases,source_pins=packet['source_pins'],production_pins=production,scripts=scripts,
            no_sdk_or_photos=True,parent_tool_terminal_proved=False,scope='fourdefaultRPCcurrent/genuineupstream cases; not archiveformat/RPCv0/physicalnetwork/pixel/semantic eligibility proof'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('PEER_CLOSED',12,str(root),flush=True);return 0
    except BaseException as error:
        if not attempted and not isinstance(error,UnresolvedOwnership):
            try:
                store.write('PREENTRY-REFUSED.json',dict(native_attempted=False,error=repr(error)));store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('PEER_PREENTRY_RETAIN',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('PEER_RETAIN',repr(error),str(root),flush=True))


if __name__=='__main__':raise SystemExit(main())
