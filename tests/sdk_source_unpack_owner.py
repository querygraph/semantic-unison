"""One private official-source extraction; OS unzip child, never SDK execution."""
import argparse,hashlib,json,os,stat,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync'),str(ROOT/'tools/adobe-validator')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,authorized_unison_tokens,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from private_camera_receiving.close import close_descriptors
from sdk_merge_receiving.store import Store
from shared_child import start
from final_profile_owner import sha,closed
from sdk_source_unpack import members,MAX_FILE,MAX_TOTAL
from sdk_source_identity import require_release

FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')
def stamp(s):return {k:getattr(s,k) for k in FIELDS}


def extractor_sha():
    # System binary is root-owned; do not weaken the owned-artifact reader.
    path='/usr/bin/unzip';fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if not(stat.S_ISREG(before.st_mode) and before.st_uid==0 and before.st_nlink>0 and 0<before.st_size<=8*1048576):
            raise ValueError('bounded root-owned system extractor required')
        digest=hashlib.sha256();count=0
        while count<before.st_size:
            block=os.read(fd,min(65536,before.st_size-count))
            if not block:raise ValueError('short system extractor read')
            count+=len(block);digest.update(block)
        if os.read(fd,1) or stamp(before)!=stamp(os.fstat(fd)) or stamp(before)!=stamp(os.lstat(path)):
            raise ValueError('system extractor changed')
        return digest.hexdigest()
    finally:close_descriptors([fd])


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('exact extraction plan required')
    packet=json.loads(raw)
    if packet['schema']!='unison-official-sdk-source-unpack-plan/1' or packet['repository']!=str(ROOT) or sys.executable!=packet['interpreter']['path']:
        raise ValueError('exact source extraction context required')
    def pins():
        for n,d in packet['source_pins'].items():
            if sha(ROOT/n)!=d:raise ValueError('source changed '+n)
        if sha(packet['interpreter']['path'],64*1048576)!=packet['interpreter']['sha256']:raise ValueError('interpreter changed')
        if packet['extractor']['path']!='/usr/bin/unzip' or extractor_sha()!=packet['extractor']['sha256']:raise ValueError('exact system extractor changed')
    pins();reference=packet['source_receipt'];data=read_bytes(reference['path'],65536)
    if len(data)!=reference['bytes'] or hashlib.sha256(data).hexdigest()!=reference['sha256']:raise ValueError('official source ancestry receipt changed')
    receipt=json.loads(data);archive=Path(receipt['archive']);parent=archive.parent;root=Path(packet['workspace'])
    if (root.parent!=parent or not root.name.startswith('source-unpack-') or stat.S_IMODE(parent.lstat().st_mode)!=0o700 or parent.is_symlink() or parent.lstat().st_uid!=os.getuid()):raise ValueError('one private source-parent namespace required')
    def source():
        if stamp(archive.lstat())!=receipt['identity']:raise ValueError('readonly official archive epoch changed')
    source();policy=ROOT.parent/'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
    if authorized_unison_tokens(read_bytes(str(policy),1048576))!=tuple(range(8)):raise ValueError('standing8 differs')
    pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
    bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
    if bundle is None:return 2
    io,cpu=bundle;store=None;fds=[];attempted=False;settled=False
    try:
        root.mkdir(mode=0o700);s=root.lstat();store=Store(str(root),dict(device=s.st_dev,inode=s.st_ino));source();pins()
        fd=os.open(archive,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(fd)
        if stamp(os.fstat(fd))!=receipt['identity']:raise ValueError('archive opened identity differs')
        with os.fdopen(fd,'rb',closefd=False) as stream:
            with zipfile.ZipFile(stream) as z:inventory=members(z.infolist())
        if stamp(os.fstat(fd))!=receipt['identity']:raise ValueError('archive changed during preflight')
        owned=fds;fds=[];close_descriptors(owned)
        if inventory['entries']!=4215 or inventory['declared_bytes']!=133855079:raise ValueError('exact reviewed archive inventory differs')
        store.write('ZIP-PREFLIGHT.json',inventory);destination=root/'extracted';destination.mkdir(mode=0o700)
        resources=[]
        for fd in (*cpu.fds,*io.fds):
            s=os.fstat(fd);resources.append(dict(fd=fd,device=s.st_dev,inode=s.st_ino))
        command=[packet['extractor']['path'],'-q',str(archive),'-d',str(destination)]
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,command=command,resource_rows=resources,SDK_executions=0,scope='OS source extraction only'))
        print('SDK_SOURCE_UNPACK_START',os.getpid(),str(root),inventory['files'],flush=True)
        attempted=True;child=start(command,dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',HOME=str(root)),pass_fds=(*cpu.fds,*io.fds),capture_limit=65536)
        out=child.finish(time.monotonic()+90);store.write('UNZIP-CHILD.json',out);closed(out,out['returncode']);settled=True
        if out['returncode']!=0:raise ValueError('OS source extraction failed; preserve private prefix')
        source();pins();expected={r['path']:r for r in inventory['members']};allowed=set(expected)
        for name in list(expected):
            for ancestor in Path(name).parents:
                if str(ancestor)!='.':allowed.add(str(ancestor))
        observed=set();files=[];hashed=0
        for directory,dirs,names in os.walk(destination,followlinks=False):
            for name in (*dirs,*names):
                path=Path(directory)/name;relative=path.relative_to(destination).as_posix();observed.add(relative);s=path.lstat()
                if relative not in allowed or s.st_uid!=os.getuid() or s.st_dev!=destination.lstat().st_dev or s.st_mode&(stat.S_ISUID|stat.S_ISGID):raise ValueError('unexpected extracted path/ownership')
                if relative not in expected or expected[relative]['directory']:
                    if not stat.S_ISDIR(s.st_mode):raise ValueError('extracted directory type differs')
                else:
                    row=expected[relative]
                    if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_size!=row['bytes']:raise ValueError('extracted regular source type/extent differs')
                    digest=sha(path,MAX_FILE) if s.st_size else hashlib.sha256(b'').hexdigest();hashed+=s.st_size
                    if stamp(path.lstat())!=stamp(s):raise ValueError('extracted source changed while hashing')
                    files.append(dict(path=relative,bytes=s.st_size,mode=stat.S_IMODE(s.st_mode),sha256=digest))
        if observed!=allowed or hashed!=inventory['declared_bytes'] or hashed>MAX_TOTAL:raise ValueError('extracted source census differs')
        sdk=destination/'dng_sdk_1_7_1';release=require_release(read_bytes(str(sdk/'DNG_ReadMe.txt'),65536).decode(),2768)
        for name in ('LICENSE.txt','dng_sdk/source/dng_host.h','dng_sdk/source/dng_validate.cpp','dng_sdk/source/dng_image_writer.cpp'):
            if not (sdk/name).is_file():raise ValueError('required SDK source missing')
        source();pins();store.write('MANIFEST.json',dict(schema='unison-extracted-official-sdk-source/1',complete=True,source_receipt=reference,archive_sha256=receipt['sha256'],sdk_root=str(sdk),release=release,files=files,extracted_payload_hash_bytes=hashed,SDK_executions=0,builds=0,parent_tool_terminal_proved=False,scope='Private official2768 source/CRC-extractor success/fileSHA inventory only; not 2724restoration/newvalidator/fixture/SDKruntime proof'))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True);print('SDK_SOURCE_UNPACK_CLOSED',len(files),hashed,str(root),flush=True);return 0
    except BaseException as error:
        if isinstance(error,UnresolvedOwnership) or attempted and not settled:retain_after_record(lambda:print('UNPACK_RETAIN',repr(error),str(root),flush=True))
        try:
            owned=fds;fds=[];close_descriptors(owned)
            if store is not None and not store.closed:store.write('FAILED.json',dict(error=repr(error),child_attempted=attempted,child_settled=settled,SDK_executions=0));store.close()
            for lease in (cpu,io):
                if not lease.closed:
                    if attempted and settled:lease.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
                    else:close_unstarted(lease)
        except BaseException as cleanup:retain_after_record(lambda:print('UNPACK_CLOSE_RETAIN',repr(cleanup),repr(error),flush=True))
        raise

if __name__=='__main__':raise SystemExit(main())
