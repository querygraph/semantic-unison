"""Finite clone-only/JXL/twelve-state SDK qualification; never Photo/Main.

Preparation is source/metadata only. Acquire IO then Unison8 just before work;
unknown retains without broad signals. No consumed workspace or file overwrite.
"""
import argparse,hashlib,json,os,re,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from final_profile_owner import sha,closed
from final_clone_interruption_owner import can_close_failed_prefix
from shared_cpu_pool import Pool,authorized_unison_tokens
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.inputs import FIELDS,bind
from sdk_merge_receiving.data import stamp
from sdk_fixture_preservation import preserve_one,BASE
from sdk_fixture_states import states,COMPRESSION,VALUES
from sdk_fixture_generation import write_state
from camera_sdk_receiving.sdk_audit import receipt,BUILD
from shared_child import start

LIMITS=dict(cpu_indexes=list(range(8)),io_mode="EX_GLOBAL",writer_calls=1,validator_calls=12,owner_observation_seconds=600,writer_observation_seconds=120,validator_observation_seconds=90,max_file_bytes=128*1048576,declared_logical_io_bytes=16*1024**3,physical_io_budget_enforced=False,retry_allowed=False)


def sdk_command(tool,reference):
    return [tool,'--unison-dng-validation-v1','--expected-sha256',reference['sha256'],
            '--expected-size',str(reference['bytes']),'--threads','1','--',reference['path']]


def accepted(out,reference):
    closed(out,0)
    report=receipt(out['stdout'].encode('ascii'),candidate_sha256=reference['sha256'],
                   candidate_bytes=reference['bytes'],build_id=BUILD)
    if report['raw_digest_verified'] is not True:raise ValueError('generated fixture raw digest must actually verify')
    return report


def generate(p,root,destination,parent,identity,store,invoke,sources,calls,*,clone_one=preserve_one):
    """Trusted original orchestration seam for disposable controls, no CLI override."""
    clones={}
    for ref in p['sources']:
        clones[ref['codec']]=clone_one(ref,parent,str(destination),identity)
        store.write(ref['codec']+'-CLONE.json',clones[ref['codec']])
    jxl=destination/'jxl.dng'
    if os.path.lexists(jxl):raise ValueError('JXL output already consumed')
    invoke([p['writer']['path'],'jxl',clones['uncompressed']['path'],str(jxl)],120)
    # Generated writer output is private, not a retained source. Freeze only
    # after its actual child/group closure and an exact bounded readback.
    fd=os.open(jxl,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        native=os.fstat(fd)
        if not(stat.S_ISREG(native.st_mode) and native.st_uid==os.getuid() and native.st_nlink==1 and 0<native.st_size<=128*1048576):raise ValueError('bounded fresh JXL output required')
        os.fchmod(fd,0o400)
    finally:close_descriptors([fd])
    cases=[];observations={};reports=[]
    for codec in COMPRESSION:
        source=clones[codec]['path'] if codec in clones else str(jxl)
        data=read_bytes(source,128*1048576);variants=states(data,codec);frozen={}
        if codec in clones and hashlib.sha256(data).hexdigest()!=clones[codec]['sha256']:raise ValueError('disposable clone changed before scalar construction')
        for state in VALUES:
            ref=write_state(parent,str(destination),identity,codec,state,variants['states'][state])
            frozen[state]={key:ref[key] for key in ('path','bytes','sha256')};observations[ref['path']]=ref['identity']
            out=invoke(sdk_command(p['validator']['path'],ref),90);report=accepted(out,ref)
            if stamp(os.lstat(ref['path']))!=ref['identity']:raise ValueError('SDK mutated readonly generated state')
            reports.append(dict(codec=codec,state=state,reference=frozen[state],identity=ref['identity'],report=report,call=calls[-1]));store.write(codec+'-'+state+'-VERIFIED.json',reports[-1])
        cases.append(dict(codec=codec,xmp_offset=variants['xmp_offset'],xmp_size=variants['xmp_size'],states=frozen))
    sources()
    if any(stamp(os.lstat(name))!=epoch for name,epoch in observations.items()):raise ValueError('generated batch epoch changed before final manifest')
    bind(cases,observations,expected_uid=os.getuid())
    if len(calls)!=13 or len(reports)!=12:raise ValueError('one writer and twelve validators required')
    generation=store.write('GENERATION.json',dict(calls=calls,reports=reports,source_pins=p['source_pins'],state_epochs=observations,parent_tool_terminal_proved=False))
    manifest=dict(schema='unison-current-sdk-merge-inputs/1',cases=cases,ancestry=[*p['prerequisites'],dict(path=str(root/'GENERATION.json'),sha256=generation['sha256'])])
    # The exact manifest schema is consumed by the current metadata freezer.
    payload=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();name='INPUT-MANIFEST.json'
    fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=parent)
    try:
        at=0
        while at<len(payload):
            n=os.write(fd,payload[at:]);
            if n<=0:raise ValueError('manifest write stalled')
            at+=n
        os.fsync(fd)
    finally:close_descriptors([fd])
    os.fsync(parent);return dict(complete=True,calls=calls,reports=reports,source_pins=p['source_pins'],input_manifest=dict(path=str(destination/name),bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()),source_hash_bytes=0,SDK_calls=13,parent_tool_terminal_proved=False,scope='Generated SDK fixture structural/decode/raw-digest findings only; no pixel/semantic/corpus/receiving qualification')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--metadata-only',action='store_true');a=parser.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact generated fixture plan required')
    p=json.loads(raw)
    if p['schema']!='unison-sdk-fixture-generation-plan/1' or p['repository']!=str(ROOT) or sys.executable!=p['interpreter']['path']:raise ValueError('qualified fixture context required')
    root=Path(p['workspace']);destination=Path(p['destination'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-sdk-states-') or destination.parent!=BASE or re.fullmatch('[0-9a-f]{32}',destination.name) is None:
        raise ValueError('fresh private runtime and exact persistent state namespace required')
    if [s['codec'] for s in p['sources']]!=['uncompressed','jpeg']:raise ValueError('two retained generated sources required')
    if (p['preservation_manifest']['sha256']!='3f690df1fead5d1a4dc4d47084bf454dbd5aaf2bd8c0aabc9493dc617a3c571d'
            or p['writer']['sha256']!='3a5c9f986c0b8dd10c0ab06cbb675902e89e9ec77c985b9a8a65da2f9de76218'
            or p['validator']['sha256']!='ca49a32bd5980b5cb16e10421d2d7a41542698a49f03a5b50007ff234b432b4a'):
        raise ValueError('exact preserved sources/new writer/old validator required')
    preserved_raw=read_bytes(p['preservation_manifest']['path'],1048576)
    if hashlib.sha256(preserved_raw).hexdigest()!=p['preservation_manifest']['sha256']:raise ValueError('preservation manifest changed')
    preserved=json.loads(preserved_raw)
    expected_sources=[{key:row[key] for key in ('codec','path','identity','sha256')} for row in preserved['fixtures']]
    if p['sources']!=expected_sources or any(row['identity']['st_mode']!=0o100400 for row in p['sources']):raise ValueError('original generated source ancestry differs')
    if not 1<=len(p['prerequisites'])<=15 or any(set(ref)!={'path','sha256'} or Path(ref['path']).suffix!='.json' for ref in p['prerequisites']):raise ValueError('bounded exact generation ancestry required')
    if p['limits']!=LIMITS:raise ValueError('exact finite generation limits required')
    def sources(*,executables=False):
        for name,digest in p['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('generation source changed '+name)
        refs=[*p['prerequisites']]
        if executables:refs += [p['interpreter'],p['writer'],p['validator']]
        for ref in refs:
            if sha(ref['path'],128*1048576)!=ref['sha256']:raise ValueError('generation ancestry/artifact changed '+ref['path'])
        for ref in p['sources']:
            if stamp(os.lstat(ref['path']))!=ref['identity']:raise ValueError('retained generated epoch changed')
    sources()
    if a.metadata_only:
        if os.path.lexists(root) or os.path.lexists(destination):raise ValueError('prepared namespace already consumed')
        print(json.dumps(dict(metadata_ready=True,source_pins=len(p['source_pins']),prerequisites=len(p['prerequisites']),retained_epoch_fences=2,input_payload_opened=False,execution_artifact_opened=False,IO_CPU_acquired=False,workspace_created=False,SDK_invoked=False)),flush=True);return 0
    root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));io=cpu=None;active=False;attempted=False;fds=[];calls=[]
    try:
        policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
        if hashlib.sha256(policy).hexdigest()!='1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352' or authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('exact standing8 required')
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
        if bundle is None:store.write('CONTENTION.json',dict(no_child_or_payload_attempted=True));store.close();return 2
        io,cpu=bundle;sources(executables=True);destination.mkdir(mode=0o700);s=destination.lstat();parent=os.open(destination,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent);identity=(s.st_dev,s.st_ino)
        resource_rows=[]
        for fd in (*cpu.fds,*io.fds):
            v=os.fstat(fd);resource_rows.append(dict(fd=fd,device=v.st_dev,inode=v.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,resource_rows=resource_rows,writer_calls_max=1,validator_calls_max=12,source_hash_bytes=0))
        print('SDK_STATES_START',os.getpid(),str(root),flush=True);deadline=time.monotonic()+600
        def invoke(argv,seconds):
            nonlocal active,attempted
            if time.monotonic()+seconds+5>=deadline:raise TimeoutError('no new SDK child near observation end')
            active=attempted=True;child=start(argv,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),pass_fds=(*cpu.fds,*io.fds))
            out=child.finish(min(deadline,time.monotonic()+seconds));pin=store.write('call-%02d.json'%len(calls),out);calls.append(pin)
            closed(out,out['returncode']);active=False;closed(out,0);return out
        record=generate(p,root,destination,parent,identity,store,invoke,lambda:sources(executables=True),calls)
        store.write('RESULT.json',record)
        close_descriptors(fds);fds=[];store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('SDK_STATES_CLOSED',len(calls),record['input_manifest']['path'],flush=True);return 0
    except BaseException as error:
        if can_close_failed_prefix(active=active,error=error):
            try:
                close_descriptors(fds);fds=[];store.write('KNOWN-FAILED-PREFIX.json',dict(error=repr(error),attempted_children_settled=True,calls=calls));store.close()
                for lease in (cpu,io):
                    if lease is not None and not lease.closed:
                        if attempted:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                        else:close_unstarted(lease)
            except BaseException as failure:retain_after_record(lambda:print('SDK_STATES_CLOSE_RETAIN',repr(failure),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('SDK_STATES_RETAIN',repr(error),str(root),flush=True))

if __name__=='__main__':raise SystemExit(main())
