"""Native-clone-only preservation of two already-qualified generated SDK inputs.

No SDK, child process, source payload hash, source mutation, copy fallback or
cleanup. Published clones are readonly in one new persistent private namespace.
"""
import argparse,hashlib,json,os,re,stat,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_multifile.clone import native_clone,FIELDS,stamp
from sdk_merge_receiving.data import hash_fd
from sdk_merge_receiving.store import Store

BASE=Path('/Users/alexy/Library/Application Support/FirstPair Unison/retained-sdk-fixtures-v1')
SOURCES=('/private/tmp/u-asv-fixture-ea3c7dda/uncompressed.dng','/private/tmp/u-smr-current-9e2e489b/stock/left/jpeg.dng')


def preserve_one(reference,parent,path,identity,*,clone=native_clone):
    """The clone seam is for original disposable controls, never a packet option."""
    fds=[]
    try:
        if reference['codec'] not in ('uncompressed','jpeg') or set(reference['identity'])!=set(FIELDS):raise ValueError('fixed generated source/epoch required')
        if re.fullmatch('[0-9a-f]{64}',reference['sha256']) is None:raise ValueError('historical exact SHA required')
        def directory():
            for value in (os.fstat(parent),os.lstat(path)):
                if not(stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode)==0o700 and value.st_uid==os.getuid()
                       and (value.st_dev,value.st_ino)==identity):raise ValueError('persistent private directory changed')
        directory();source=os.open(reference['path'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC);fds.append(source)
        def fence():
            if stamp(os.fstat(source))!=reference['identity'] or stamp(os.lstat(reference['path']))!=reference['identity']:raise ValueError('retained generated source epoch changed')
        fence();before=os.fstat(source)
        if not(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode) in (0o400,0o600) and before.st_uid==os.getuid()
                and before.st_nlink==1 and 0<before.st_size<=128*1048576 and getattr(before,'st_flags',0)==0):raise ValueError('fixed owned generated source refused')
        name=reference['codec']+'.dng'
        try:os.stat(name,dir_fd=parent,follow_symlinks=False)
        except FileNotFoundError:pass
        else:raise ValueError('preservation target exists; no overwrite/retry')
        clone(source,parent,name);fence();directory()
        target=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(target);copied=os.fstat(target)
        if not(stat.S_ISREG(copied.st_mode) and copied.st_uid==os.getuid() and copied.st_nlink==1 and copied.st_size==before.st_size
                and (copied.st_dev,copied.st_ino)!=(before.st_dev,before.st_ino) and getattr(copied,'st_flags',0)==0):raise ValueError('distinct native clone identity refused')
        os.fchmod(target,0o400);epoch=stamp(os.fstat(target));actual=hash_fd(target,before.st_size)
        if actual!=reference['sha256'] or epoch!=stamp(os.fstat(target)) or epoch!=stamp(os.stat(name,dir_fd=parent,follow_symlinks=False)):
            raise ValueError('preserved clone SHA or epoch differs; no fallback')
        os.fsync(target);os.fsync(parent);fence();directory()
        return dict(codec=reference['codec'],source=reference['path'],source_identity=dict(reference['identity']),
            path=str(Path(path)/name),identity=epoch,bytes=before.st_size,sha256=actual,clone_hash_bytes=before.st_size,
            source_payload_hash_bytes=0 if clone is native_clone else None,
            backend='native-fclonefileat-only' if clone is native_clone else 'original-disposable-test-double',readonly=True)
    finally:close_descriptors(fds)


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('preservation plan differs')
    packet=json.loads(raw)
    if (packet['schema']!='unison-generated-fixture-preservation-plan/2' or packet['repository']!=str(ROOT)
            or tuple(s['path'] for s in packet['sources'])!=SOURCES
            or [s['codec'] for s in packet['sources']]!=['uncompressed','jpeg']):raise ValueError('exact existing generated inputs required')
    destination=Path(packet['destination'])
    if destination.parent!=BASE or re.fullmatch('[0-9a-f]{32}',destination.name) is None or destination.exists():raise ValueError('new exact persistent preservation nonce required')
    for name,digest in packet['source_pins'].items():
        if hashlib.sha256(read_bytes(str(ROOT/name),16*1048576)).hexdigest()!=digest:raise ValueError('preservation source changed '+name)
    for source in packet['sources']:
        if stamp(os.lstat(source['path']))!=source['identity']:raise ValueError('generated fixture metadata changed before entry')
    policy=read_bytes(str(ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'),1048576)
    if authorized_unison_tokens(policy)!=tuple(range(8)):raise ValueError('standing Unison8 differs')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
    if bundle is None:print('PRESERVATION_CONTENDED_NO_READ',flush=True);return 2
    io,cpu=bundle;fds=[];store=None
    try:
        # Open existing user Application Support, create only the two named
        # private data parents and a new nonce. Never chmod an existing parent.
        parent_path=Path('/Users/alexy/Library/Application Support');parent=os.open(parent_path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent)
        parents=[]
        for name in ('FirstPair Unison','retained-sdk-fixtures-v1',destination.name):
            try:os.mkdir(name,0o700,dir_fd=parent)
            except FileExistsError:
                if name==destination.name:raise ValueError('preservation nonce already consumed')
            parent=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent);fds.append(parent);parent_path/=name
            observed=os.fstat(parent)
            if not(stat.S_ISDIR(observed.st_mode) and stat.S_IMODE(observed.st_mode)==0o700 and observed.st_uid==os.getuid()
                    and (observed.st_dev,observed.st_ino)==(os.lstat(parent_path).st_dev,os.lstat(parent_path).st_ino)):
                raise ValueError('private parent identity/permissions refused; no chmod')
            parents.append(dict(path=str(parent_path),device=observed.st_dev,inode=observed.st_ino))
        identity=(os.fstat(parent).st_dev,os.fstat(parent).st_ino);store=Store(str(destination),dict(device=identity[0],inode=identity[1]))
        resource_rows=[]
        for fd in (*cpu.fds,*io.fds):
            value=os.fstat(fd);resource_rows.append(dict(fd=fd,device=value.st_dev,inode=value.st_ino))
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,cpu_indexes=list(range(8)),io_mode='EX_GLOBAL',resource_rows=resource_rows,
            source_hash_bytes=0,SDK_calls=0,no_child_processes=True,parents=parents))
        print('PRESERVATION_START',os.getpid(),str(destination),flush=True);deadline=time.monotonic()+60;preserved=[]
        for reference in packet['sources']:
            if time.monotonic()>=deadline:raise TimeoutError('preservation observation expired before next clone')
            result=preserve_one(reference,parent,str(destination),identity);preserved.append(result);store.write(reference['codec']+'-PRESERVED.json',result)
            print('FIXTURE_PRESERVED',reference['codec'],result['bytes'],flush=True)
        for reference in packet['sources']:
            if stamp(os.lstat(reference['path']))!=reference['identity']:raise ValueError('original generated input changed')
        if sum(r['clone_hash_bytes'] for r in preserved)!=87022256:raise ValueError('exact two-input hash budget changed')
        store.write('MANIFEST.json',dict(schema='unison-retained-generated-sdk-fixtures/1',complete=True,source_plan_sha256=a.sha256,fixtures=preserved,
            clone_hash_bytes=87022256,source_payload_hash_bytes=0,SDK_calls=0,no_child_processes=True,
            scope='two byte-integrity-preserved generated inputs only; no new SDK/semantic/pixel/12state/JXL/receiving qualification',
            future_input_root_integration_required=True,parent_tool_terminal_proved=False))
        store.close();close_descriptors(fds);fds=[];close_unstarted(cpu);close_unstarted(io)
        print('PRESERVATION_CLOSED',str(destination),flush=True);return 0
    except BaseException as error:
        # Never open another diagnostic FD on uncertain close, or auto-delete a
        # failed clone. Preserve source/clone descriptors and canonical owners.
        retain_after_record(lambda:print('PRESERVATION_RETAIN',repr(error),str(destination),flush=True))


if __name__=='__main__':raise SystemExit(main())
