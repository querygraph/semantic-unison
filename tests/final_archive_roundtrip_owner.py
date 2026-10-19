"""Retained ten-stage current/installed2.53.5 archive round trip, both compilers."""
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
from archive_roundtrip_contract import fixture,stage,verify
from archive_refusal_pair import invoke as refuse_invoke,child as refusal_child
from batch_transport import restore
from batch_artifacts import read as artifact_read
from final_clone_stage_owner import write_bytes
from final_profile_owner import sha

def command(artifacts,root,index,phase):
    if type(index) is not int or index not in (0,1) or set(artifacts)!={'stock','ox','old-stock'}:
        raise ValueError('exact stock/Ox archive case required')
    spec=stage(phase);label=('stock','ox')[index];old=spec['generation']=='baseline'
    binary=artifacts['old-stock' if old else label]['path'];directory=root/str(index)
    flags=['-maxthreads','2'] if old else schedule(binary,binary,str(directory),mode='semantic',workers=2)['rows'][0]['server_flags']+[
        '-semanticmergebasecache','-merge','Name *.dng -> unison:dng-xmp-scalars/0']
    argv=[binary,str(directory/'left'),'ssh://localhost/'+str(directory/'right'),'-sshcmd',str(root/'launcher.py'),'-servercmd',binary,
        '-batch','-auto','-fastcheck','false','-times','-debug','archive',*flags]
    return dict(label=label,generation=spec['generation'],client=binary,server=binary,command=argv,server_flags=flags,
        server_command=[binary,'-server','__new-rpc-mode',*flags],configured_endpoint_plus_owner_bound=6,reserved_credits=8)


def inventory(directory):
    return {role:{p.name:sha(p) for p in sorted((directory/('state-'+role)).iterdir()) if p.name.startswith('ar')}
            for role in ('client','server')}


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('upstream pair plan SHA differs')
    packet=json.loads(raw)
    if packet['schema']!='unison-final-archive-roundtrip-plan/1' or packet['repository']!=str(ROOT) or sys.executable!=PYTHON:
        raise ValueError('exact current archive roundtrip context required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('peer source changed '+name)
    sources()
    indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
    if indexes!=tuple(range(8)):raise ValueError('standing8 grant differs')
    root=Path(packet['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-archive-'):raise ValueError('new private peer namespace required')
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
            sources()
            baseline=json.loads(read_bytes(str(ROOT/'tests/archive_downgrade/qualification.json'),1048576))
            old=packet['artifacts']['old-stock']
            if baseline['baseline_version']!='unison version 2.53.5 (ocaml 5.2.0)' or not all(
                run['actual']['baseline']==old['path'] and run['actual']['baseline_sha256']==old['sha256'] for run in baseline['runs']):
                raise ValueError('installed old peer historical byte/version binding differs')
            for name,digest in production.items():
                if sha(ROOT/name)!=digest:raise ValueError('production source changed')
            for ref in (*packet['artifacts'].values(),packet['interpreter'],*packet['compiler_artifacts'].values()):
                if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('peer artifact changed')
        artifacts();resource_rows=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resource_rows.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resource_rows,cpu_indexes=list(indexes),io_mode='EX_GLOBAL',
            cases=2,calls=20,scope='tenarchivephases/current-installed2.53.5/defaultRPCloopback; noSDK/Photo/realSSH/RPCv0'))
        print('ARCHIVE_START',os.getpid(),str(root),flush=True)
        paths=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
        imports='#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr(paths)+'\n'
        scripts={str(root/'launcher.py'):program(root/'launcher.py',imports+'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')}
        deadline=time.monotonic()+600;cases=[]
        for index in range(2):
            directory=root/str(index);directory.mkdir(mode=0o700)
            for name in ('left','right','home','tmp','state-client','state-server'):(directory/name).mkdir(mode=0o700)
            source=directory/'left/image.dng';target=directory/'right/image.dng';records=[]
            for phase in range(10):
                spec=stage(phase);row=command(packet['artifacts'],root,index,phase)
                for role,data in spec['writes'].items():
                    path=directory/role/'image.dng';replacement=directory/role/'replacement'
                    write_bytes(replacement,data);os.replace(replacement,path)
                source_before=identity(source);target_before=identity(target) if target.exists() else None
                archives_before=inventory(directory);name='c%d-%d'%(index,phase)
                if time.monotonic()+65>=deadline:raise TimeoutError('no new archive call near observation end')
                artifacts();call_deadline=min(deadline,time.monotonic()+60)
                config=dict(directory=str(root),identity=copy.deepcopy(store.identity),stage=name,binary=row['server'],flags=row['server_flags'],
                    deadline=call_deadline,worker_pid=os.getpid(),resource_fds=copy.deepcopy(resource_rows))
                proxy=root/(name+'-proxy.py');scripts[str(proxy)]=program(proxy,imports+'from sdk_merge_receiving.child_entry import proxy_main\nraise SystemExit(proxy_main('+repr(config)+'))\n')
                for path,pin in scripts.items():
                    if sha(path,65536)!=pin['sha256']:raise ValueError('generated archive shim changed')
                intent=store.write(name+'-INTENT.json',dict(index=index,phase=phase,row=row,proxy_config=config,scripts=copy.deepcopy(scripts),
                    source_before=source_before,target_before=target_before,archives_before=archives_before))
                env=child_environment(directory,'state-client');env.update(UNISON_MERGE_BINARY=row['server'],UNISON_MERGE_SOCKET=str(root/(name+'.sock')),UNISON_MERGE_DEADLINE=str(call_deadline))
                attempted=True
                call=refuse_invoke if phase==5 else invoke
                current=call(row['command'],env,proxy_command=[PYTHON,'-B',str(proxy)],proxy_environment=child_environment(directory,'state-server'),
                    server_command=row['server_command'],socket_path=str(root/(name+'.sock')),deadline=call_deadline,pass_fds=(*cpu.fds,*io.fds),store=store,name=name,
                    read_proxy_bytes=lambda:store.read(name+'-PROXY.json',maximum=65536))
                pair=store.read_json(current['name'],expected_sha256=current['sha256'])
                client=refusal_child(store,pair['evidence']['client'],row['command'],(1,2)) if phase==5 else restore(store,pair['evidence']['client'],row['command'])
                target_after=identity(target);archives_after=inventory(directory)
                proof=verify(phase,returncode=client['returncode'],log=client['stdout']+client['stderr'],
                    left=read_bytes(str(source),131072),right=read_bytes(str(target),131072),archives_before=archives_before,archives_after=archives_after,
                    target_before=target_before,target_after=target_after)
                if not spec['expected_merge'] and identity(source)!=source_before:raise ValueError('archive phase unexpectedly mutated source identity')
                record=dict(phase=phase,pair=current,intent=intent,proof=proof,source_identity=source_before,target_identity=target_after,archives_after=archives_after)
                records.append(record);store.write(name+'-RESULT.json',record);print('ARCHIVE_PHASE_CLOSED',index,phase,flush=True)
            cases.append(dict(index=index,label=row['label'],stages=records))
        artifacts();store.write('RESULT.json',dict(complete=True,cases=cases,source_pins=packet['source_pins'],production_pins=production,scripts=scripts,
            no_sdk_or_photos=True,parent_tool_terminal_proved=False,scope='two current/installed2.53.5 tenstage archive roundtrips with exactscalarmerge+missingbasepreservation; notRPCv0/physicalnetwork/SDK proof'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('ARCHIVE_CLOSED',20,str(root),flush=True);return 0
    except BaseException as error:
        if not attempted and not isinstance(error,UnresolvedOwnership):
            try:
                store.write('PREENTRY-REFUSED.json',dict(native_attempted=False,error=repr(error)));store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('ARCHIVE_PREENTRY_RETAIN',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('ARCHIVE_RETAIN',repr(error),str(root),flush=True))


if __name__=='__main__':raise SystemExit(main())
