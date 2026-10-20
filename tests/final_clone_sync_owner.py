"""Current generic receiver-clone exactness and explicit flagged-basis policies.

Original generated fixtures from test_clone_sync; retained transport/FD owners.
"""
import argparse,copy,hashlib,json,os,random,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,UnresolvedOwnership,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.admission import PYTHON
from sdk_merge_receiving.runtime import program,child_environment
from sdk_merge_receiving.transport import run as retained_pair
from batch_pair import invoke
from batch_commands import schedule
from batch_transport import restore
from component_remote.io import identity
from final_clone_stage_owner import write_bytes
from final_profile_owner import sha,closed
from final_clone_interruption_owner import generated_bytes,can_close_failed_prefix,receiver_clone_observed
from shared_child import start
from sdk_fixture_build_owner import tool_sha


def fixtures():
    rng=random.Random(98231);original=rng.randbytes(2*1048576)
    edits=[('same-offset',original[:15000]+b'CHANGED!'+original[15008:]),
        ('insert-prefix',b'inserted prefix'+original),('delete-prefix',original[193:]),
        ('duplicate-shift',original[65536:]+original[:65536]),
        ('all-literals',rng.randbytes(len(original))),('shorten',original[:800000]),
        ('extend',original+b'new end'*10000)]
    return original,edits


def with_policy(row,policy):
    if policy not in ('auto','off','require'):raise ValueError('explicit clone policy required')
    value=copy.deepcopy(row)
    for key in ('command','server_command','server_flags'):
        argv=value[key];argv[argv.index('-clone')+1]=policy
    return value


def audit_refusal(pair,*,client_command,proxy_command,server_command):
    if set(pair)!={'client','proxy','raw_proxy','external_sdk_audit_required','resource_release_authorized'} or pair['external_sdk_audit_required'] is not True or pair['resource_release_authorized'] is not False:raise ValueError('exact retained flagged-basis refusal required')
    client=pair['client'];proxy=pair['proxy']
    for out,argv,code in ((client,client_command,2),(proxy,proxy_command,0)):
        closed(out,code)
        if out['command']!=argv or type(out['client_cleanup']['pid']) is not int or not 0<out['client_cleanup']['pid']<2**31 or out['aggregate_or_parent_terminal_proved'] is not False or out['io_cpu_release_authorized'] is not False:raise ValueError('actual non-authorizing child identities required')
    if 'cannot clone this basis' not in client['stdout']+client['stderr'] or 'Lost connection' in client['stdout']+client['stderr']:raise ValueError('specific normal require-policy refusal required')
    frame=json.loads(pair['raw_proxy']);keys={'schema','server_command','server_pid','server_returncode','server_reaped','server_group','input_eof_forwarded','output_eof_forwarded','forwarded_protocol_bytes','parent_group_audit_required','sdk_helper_audit_required','resource_release_authorized'}
    cp=client['client_cleanup']['pid'];pp=proxy['client_cleanup']['pid'];sp=frame['server_pid']
    if set(frame)!=keys or frame['schema']!='unison-retained-merge-proxy/1' or frame['server_command']!=server_command or type(sp) is not int or not 0<sp<2**31 or len({cp,pp,sp})!=3 or type(frame['server_returncode']) is not int or frame['server_returncode']!=0 or frame['server_reaped'] is not True or frame['server_group']!=pp or frame['input_eof_forwarded'] is not True or frame['output_eof_forwarded'] is not True or frame['parent_group_audit_required'] is not True or frame['sdk_helper_audit_required'] is not True or frame['resource_release_authorized'] is not False:raise ValueError('normal server reap/group/EOF proof required')
    counts=frame['forwarded_protocol_bytes']
    if set(counts)!={'client_to_server_bytes','server_to_client_bytes'} or any(type(n) is not int or not 0<n<2**63 for n in counts.values()):raise ValueError('positive forwarded protocol counts required')
    return dict(client_pid=cp,proxy_pid=pp,server_pid=sp,client_exit=2,server_exit=0,resource_release_authorized=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);args=parser.parse_args();raw=read_bytes(args.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=args.sha256:raise ValueError('exact generated clone plan required')
    p=json.loads(raw)
    if p['schema']!='unison-final-clone-sync-plan/1' or p['repository']!=str(ROOT) or sys.executable!=PYTHON:raise ValueError('qualified two-compiler original fixture context required')
    def sources():
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('clone sync source changed '+name)
        if p['flag_tool']['path']!='/usr/bin/chflags' or tool_sha(p['flag_tool']['path'])!=p['flag_tool']['sha256']:raise ValueError('fixed installed flag tool changed')
        for ref in (*p['artifacts'].values(),p['interpreter'],*p['compiler_artifacts'].values()):
            if sha(ref['path'],64*1048576)!=ref['sha256']:raise ValueError('qualified execution artifact changed')
    sources();root=Path(p['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-clone-sync-'):raise ValueError('new disposable clone workspace required')
    root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));io=cpu=None;attempted=False;active=False;held=[]
    try:
        indexes=authorized_unison_tokens(read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576))
        if indexes!=tuple(range(8)):raise ValueError('standing8 required')
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd');bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,indexes)
        if bundle is None:store.write('CONTENTION.json',dict(no_native_attempted=True));store.close();return 2
        io,cpu=bundle;sources();production={}
        for ref in p['build_receipts']:
            raw=read_bytes(ref['path'],1048576)
            if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:raise ValueError('build receipt changed')
            b=json.loads(raw);artifact=p['artifacts'][ref['compiler']]
            if b['complete'] is not True or b['build_exit']!=0 or b['selftest_exit']!=0 or b['binary']!=artifact['path'] or b['binary_sha256']!=artifact['sha256']:raise ValueError('current complete build required')
            for name,digest in b['source_sha256'].items():
                if name.startswith('src/'):
                    if sha(ROOT/name)!=digest or name in production and production[name]!=digest:raise ValueError('mixed production input')
                    production[name]=digest
        resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=args.sha256,resource_rows=resources,cases_per_compiler=14,SDK_or_Photo_calls=0))
        print('CLONE_SYNC_START',os.getpid(),str(root),flush=True)
        imports='#!'+PYTHON+'\nimport sys\nsys.path[:0]='+repr([str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')])+'\n';scripts={};records=[];modifiers=[];deadline=time.monotonic()+600
        def modifier(argv,name):
            nonlocal active,attempted
            if argv[0]!=p['flag_tool']['path'] or tool_sha(argv[0])!=p['flag_tool']['sha256']:raise ValueError('flag modifier tool changed')
            attempted=active=True;child=start(argv,dict(os.environ),pass_fds=(*cpu.fds,*io.fds));out=child.finish(time.monotonic()+30);store.write(name+'.json',out);closed(out,out['returncode']);active=False
            if out['returncode']!=0:raise ValueError('generated flag modifier failed')
            modifiers.append(dict(name=name,command=argv,child=out['client_cleanup']))
        for index,label in enumerate(('stock','ox')):
            directory=root/str(index);directory.mkdir(mode=0o700)
            for name in ('left','right','home','tmp','state-client','state-server'):(directory/name).mkdir(mode=0o700)
            launcher=directory/'launcher.py';scripts[str(launcher)]=program(launcher,imports+'from sdk_merge_receiving.child_entry import launcher_main\nraise SystemExit(launcher_main())\n')
            binary=p['artifacts'][label]['path'];base=schedule(binary,binary,str(directory),mode='receiver-clone',workers=2)['rows'][0];original,edits=fixtures();source=directory/'left/ordinary.bin';target=directory/'right/ordinary.bin';write_bytes(source,original)
            saved=edits[-1][1];hardlink_data=saved[:9000]+b'new hardlink update'+saved[9019:]
            steps=[('seed',original,'auto'),*[(label,data,'auto') for label,data in edits],('noop',saved,'auto'),('hardlink',hardlink_data,'auto'),('clone-off',original,'off'),('require-flagged',hardlink_data,'require'),('auto-flagged',hardlink_data,'auto'),('final-noop',hardlink_data,'auto')]
            previous=None;old_fd=None
            for phase,(case,data,policy) in enumerate(steps):
                name='c%d-%d'%(index,phase);row=with_policy(base,policy)
                if case=='hardlink':os.link(target,directory/'old-hardlink');old_fd=os.open(target,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);held.append(old_fd)
                if case=='require-flagged':modifier(['/usr/bin/chflags','nodump',str(target)],'c%d-setflag'%index)
                if phase and case not in ('noop','auto-flagged','final-noop'):
                    replacement=directory/'left/replacement';write_bytes(replacement,data);os.replace(replacement,source)
                before=identity(source);sources()
                if time.monotonic()+65>=deadline:raise TimeoutError('no new clone case near observation end')
                phase_deadline=min(deadline,time.monotonic()+60);config=dict(directory=str(root),identity=copy.deepcopy(store.identity),stage=name,binary=binary,flags=row['server_flags'],deadline=phase_deadline,worker_pid=os.getpid(),resource_fds=copy.deepcopy(resources))
                proxy=root/(name+'-proxy.py');scripts[str(proxy)]=program(proxy,imports+'from sdk_merge_receiving.child_entry import proxy_main\nraise SystemExit(proxy_main('+repr(config)+'))\n')
                for path,pin in scripts.items():
                    if sha(path,65536)!=pin['sha256']:raise ValueError('generated shim changed')
                store.write(name+'-INTENT.json',dict(index=index,phase=phase,case=case,row=row,proxy_config=config,source_before=before,scripts=copy.deepcopy(scripts)))
                env=child_environment(directory,'state-client');env.update(UNISON_MERGE_BINARY=binary,UNISON_MERGE_SOCKET=str(root/(name+'.sock')),UNISON_MERGE_DEADLINE=str(phase_deadline));proxy_command=[PYTHON,'-B',str(proxy)];attempted=active=True
                if case=='require-flagged':
                    pair=retained_pair(row['command'],env,proxy_command=proxy_command,proxy_environment=child_environment(directory,'state-server'),socket_path=str(root/(name+'.sock')),deadline=phase_deadline,pass_fds=(*cpu.fds,*io.fds),read_proxy=lambda:store.read(name+'-PROXY.json',maximum=65536))
                    saved_pair=dict(pair);saved_pair['raw_proxy']=pair['raw_proxy'].decode();store.write(name+'-RAW-PAIR.json',saved_pair);joined=audit_refusal(pair,client_command=row['command'],proxy_command=proxy_command,server_command=row['server_command']);active=False;pair_pin=store.write(name+'-REFUSAL.json',dict(audit=joined,raw_record=name+'-RAW-PAIR.json'));client=pair['client'];server=pair['proxy'];expected=original
                else:
                    pair_pin=invoke(row['command'],env,proxy_command=proxy_command,proxy_environment=child_environment(directory,'state-server'),server_command=row['server_command'],socket_path=str(root/(name+'.sock')),deadline=phase_deadline,pass_fds=(*cpu.fds,*io.fds),store=store,name=name,read_proxy_bytes=lambda:store.read(name+'-PROXY.json',maximum=65536));active=False
                    pair=store.read_json(pair_pin['name'],expected_sha256=pair_pin['sha256']);client=restore(store,pair['evidence']['client'],row['command']);server=restore(store,pair['evidence']['proxy'],proxy_command);expected=data
                marker=receiver_clone_observed(client,server);text=''.join(x[k] for x in (client,server) for k in ('stdout','stderr'))
                if case in [x[0] for x in edits]+['hardlink'] and not marker:raise ValueError('named generic receiver-clone case not exercised')
                if case in ('clone-off','require-flagged','auto-flagged','noop','final-noop') and marker:raise ValueError('disabled/refused/noop clone unexpectedly used')
                if case=='same-offset':
                    counts=re.findall(r'Receiver clone preserved (\d+) logical bytes',text)
                    if not counts or int(counts[-1])<=len(expected)//2:raise ValueError('same-offset inherited logical bytes not demonstrated')
                if case=='auto-flagged' and 'Receiver clone declined:' not in text:raise ValueError('explicit known-unsupported fallback not demonstrated')
                if generated_bytes(target,links=1)!=expected or identity(source)!=before:raise ValueError('exact clone output/source fence differs')
                if old_fd is not None:
                    if generated_bytes(directory/'old-hardlink',links=1)!=saved or os.pread(old_fd,len(saved)+1,0)!=saved:raise ValueError('old hardlink/open reader changed')
                after=identity(target)
                if case in ('noop','final-noop') and after!=previous:raise ValueError('clone noop touched or replaced target')
                if {x.name for x in (directory/'right').iterdir()}!={'ordinary.bin'}:raise ValueError('clone case leaked staging files')
                record=dict(compiler=label,phase=phase,case=case,policy=policy,pair=pair_pin,clone_marker=marker,target_identity=after,target_sha256=hashlib.sha256(expected).hexdigest(),source_identity=before,old_reader_preserved=old_fd is not None);store.write(name+'-RESULT.json',record);records.append(record);previous=after
                if case=='auto-flagged':modifier(['/usr/bin/chflags','0',str(target)],'c%d-clearflag'%index);previous=identity(target)
                print('CLONE_SYNC_CASE_CLOSED',label,case,flush=True)
            close_descriptors([held.pop()])
        sources();store.write('RESULT.json',dict(complete=True,cases=records,modifiers=modifiers,source_pins=p['source_pins'],production_pins=production,scripts=scripts,SDK_or_Photo_calls=0,parent_tool_terminal_proved=False,scope='Original generated generic clone exactness/shift/EOF/hardlink/cloneoff/flagrequire-auto/noop; no SDK/photos/physical-write/performance claim'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('CLONE_SYNC_CLOSED',len(records),str(root),flush=True);return 0
    except BaseException as error:
        if can_close_failed_prefix(active=active,error=error):
            try:
                store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),native_attempted=attempted,all_attempted_peer_groups_closed=True))
                while held:close_descriptors([held.pop()])
                store.close()
                for lease in (cpu,io):
                    if lease is not None and not lease.closed:
                        if attempted:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                        else:close_unstarted(lease)
            except BaseException as failure:retain_after_record(lambda:print('CLONE_SYNC_CLOSE_RETAIN',repr(failure),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('CLONE_SYNC_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
