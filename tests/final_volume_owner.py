"""One retained private-image cross-volume qualification after Photo handover.

Only a newly created HFS+ image/private APFS roots. Never format a device or
force-detach. Once any child is attempted, failure retains the owner, mount and
IO/CPU descriptors for independent recovery; no cleanup from a finally block.
"""
import argparse,hashlib,json,os,plistlib,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from shared_cpu_pool import Pool,UnresolvedOwnership
from shared_io_pool import GlobalPool,CANONICAL_MANIFEST,CANONICAL_SHA256,try_io_cpu_bundle,close_unstarted
from shared_process_owner import retain_after_record
from sdk_merge_receiving.store import Store
from shared_child import start
from final_profile_owner import closed,sha
from batch_commands import schedule as peer_schedule
import fixtures


def cases():
    return [dict(label=label,direction=direction,mode=mode) for label in ('stock','ox')
        for direction in ('hfs-to-apfs','apfs-to-hfs') for mode in ('generic-auto','generic-off','dng-auto')]


def owned_attachment(info,image,mount):
    """Do not turn an unverified disk identifier into a detach command."""
    rows=[r for r in info['images'] if r.get('image-path')==str(image)]
    if len(rows)!=1:raise ValueError('exact owned image attachment missing or ambiguous')
    points=[r for r in rows[0]['system-entities'] if r.get('mount-point')==str(mount)]
    if len(points)!=1 or rows[0].get('owner-uid')!=os.getuid():raise ValueError('owned HFS+ mount differs')
    point=points[0]
    if point.get('volume-kind') is not None:
        if point['volume-kind']!='hfs':raise ValueError('owned filesystem kind differs')
    elif point.get('content-hint')!='48465300-0000-11AA-AA11-00306543ECAC':
        raise ValueError('owned HFS+ content hint missing')
    device=points[0].get('dev-entry')
    if not isinstance(device,str) or re.fullmatch('/dev/disk[0-9]+s[0-9]+',device) is None:
        raise ValueError('exact owned logical device identifier required')
    return points[0]


def sync_argv(binary,source,target,mode):
    selected={'generic-auto':'receiver-clone','generic-off':'ordinary','dng-auto':'semantic'}[mode]
    # Reuse the actually qualified preference builder instead of inventing flags.
    contract=peer_schedule(binary,binary,str(Path(source).parent/'contract'),mode=selected,workers=2)
    return [binary,str(source),str(target),'-batch','-auto','-fastcheck','false','-times',
        *contract['rows'][0]['server_flags']]


def persist_completed_command(store,name,out,*,combined=False):
    # A nonzero outcome must remain available before functional refusal.
    pin=store.write(name+'.json',out)
    closed(out,0)
    return pin,out['stdout']+(out['stderr'] if combined else '')


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--sha256',required=True);a=p.parse_args()
    raw=read_bytes(a.plan,2*1048576)
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('volume plan SHA differs')
    packet=json.loads(raw)
    if (sys.platform!='darwin' or packet['schema']!='unison-final-private-volume-plan/1'
            or packet['repository']!=str(ROOT) or packet['cases']!=cases()):raise ValueError('exact twelve-case Darwin matrix required')
    def sources():
        for name,digest in packet['source_pins'].items():
            if sha(ROOT/name)!=digest:raise ValueError('volume source changed: '+name)
    sources()
    root=Path(packet['workspace'])
    if root.parent!=Path('/private/tmp') or not root.name.startswith('u-volume-'):raise ValueError('private new volume workspace required')
    root.mkdir(mode=0o700);st=root.lstat();store=Store(str(root),dict(device=st.st_dev,inode=st.st_ino))
    io=cpu=None;attempted=False;child=None
    try:
        pool=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),'4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd')
        bundle=try_io_cpu_bundle(GlobalPool.read(CANONICAL_MANIFEST,CANONICAL_SHA256),pool,tuple(range(8)))
        if bundle is None:store.write('CONTENTION.json',dict(child_attempted=False));store.close();return 2
        io,cpu=bundle
        production={}
        for ref in packet['build_receipts']:
            data=read_bytes(ref['path'],1048576)
            if len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:raise ValueError('current build receipt differs')
            build=json.loads(data);artifact=packet['artifacts'][ref['compiler']]
            if not(build['complete'] is True and build['build_exit']==0 and build['selftest_exit']==0
                   and build['binary']==artifact['path'] and build['binary_sha256']==artifact['sha256']):raise ValueError('current qualified binary binding differs')
            for name,digest in build['source_sha256'].items():
                if name.startswith('src/'):
                    if name in production and production[name]!=digest:raise ValueError('mixed production sources')
                    production[name]=digest
        def artifacts():
            sources()
            for name,digest in production.items():
                if sha(ROOT/name)!=digest:raise ValueError('production source changed')
            for item in (*packet['artifacts'].values(),packet['interpreter']):
                if sha(item['path'],64*1048576)!=item['sha256']:raise ValueError('volume artifact changed')
        artifacts();deadline=time.monotonic()+900;calls=[]
        def command(argv,name,environment=None,*,combined=False):
            nonlocal attempted,child
            artifacts()
            if time.monotonic()>=deadline:raise TimeoutError('volume observation expired; retain, no forced detach')
            attempted=True
            child=start(list(map(str,argv)),dict(os.environ,PYTHONDONTWRITEBYTECODE='1') if environment is None else environment,
                pass_fds=(*cpu.fds,*io.fds))
            out=child.finish(min(deadline,time.monotonic()+60))
            pin,text=persist_completed_command(store,name,out,combined=combined)
            if out['command']!=list(map(str,argv)):raise ValueError('actual volume child command differs')
            calls.append(pin);return text
        mount=root/'mount';mount.mkdir(mode=0o700);image=root/'fixture.dmg'
        store.write('START.json',dict(owner_pid=os.getpid(),plan_sha256=a.sha256,cpu_indexes=list(range(8)),
            io_mode='EX_GLOBAL',originals_sdk_photo=False,cases=12,cli_calls=36,
            scope='private HFS+ image on internal APFS; same physical storage, no independent-device/physical-write/timing claim'))
        print('VOLUME_START',os.getpid(),str(root),flush=True)
        command(['/usr/bin/hdiutil','create','-size','128m','-fs','HFS+','-volname','UnisonPrivateFixture','-type','UDIF','-nospotlight',str(image)],'image-create')
        before_image=image.lstat()
        attached=plistlib.loads(command(['/usr/bin/hdiutil','attach','-nobrowse','-noautoopen','-mountpoint',str(mount),'-plist',str(image)],'image-attach').encode())
        points=[r for r in attached['system-entities'] if r.get('mount-point')==str(mount)]
        if len(points)!=1 or points[0].get('volume-kind')!='hfs' or mount.stat().st_dev==root.stat().st_dev:raise ValueError('distinct private HFS volume required')
        apfs=plistlib.loads(command(['/usr/sbin/diskutil','info','-plist','/System/Volumes/Data'],'apfs-metadata').encode())
        if apfs.get('FilesystemType','').lower()!='apfs' or os.stat('/System/Volumes/Data').st_dev!=root.stat().st_dev:raise ValueError('private APFS source volume differs')
        rows=[]
        for spec in cases():
            label,direction,mode=(spec[k] for k in ('label','direction','mode'));name='-'.join((label,direction,mode))
            state=root/(name+'-state');state.mkdir(mode=0o700)
            apfs_root=root/(name+'-apfs');hfs_root=mount/(name+'-hfs')
            apfs_root.mkdir(mode=0o700);hfs_root.mkdir(mode=0o700)
            source,target=(hfs_root,apfs_root) if direction=='hfs-to-apfs' else (apfs_root,hfs_root)
            is_dng=mode=='dng-auto';filename='fixture-é.'+('dng' if is_dng else 'bin');path=source/filename
            metadata=fixtures.create(path,2097152,8192,7)
            # Generic cases use the same bytes but semantic extensions are off.
            before=fixtures.sha256(path)
            binary=packet['artifacts'][label]['path']
            argv=sync_argv(binary,source,target,mode)
            def sync(stage):return command(argv,name+'-'+stage,dict(os.environ,UNISON=str(state),PYTHONDONTWRITEBYTECODE='1'),combined=True)
            sync('seed')
            if fixtures.sha256(target/filename)!=before:raise ValueError('cross-volume seed differs')
            basis=(root if direction=='hfs-to-apfs' else mount)/(name+'-basis');os.link(target/filename,basis)
            stamp=path.stat()
            if is_dng:after=fixtures.edit(path,metadata)
            else:
                with path.open('r+b') as stream:stream.seek(123456);stream.write(b'private exact binary edit')
                after=fixtures.sha256(path)
            os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns+2000000000))
            log=sync('update')
            semantic='Local semantic workers wrote' in log;generic='Local receiver clone preserved' in log
            expected=direction=='hfs-to-apfs' and mode!='generic-off'
            if semantic!=(expected and is_dng) or generic!=(expected and not is_dng):raise ValueError('cross-volume clone/fallback selection differs')
            if not fixtures.equal_files(path,target/filename) or fixtures.sha256(basis)!=before:raise ValueError('cross-volume target or old hardlink differs')
            preserved=re.findall(r'Local receiver clone preserved ([0-9]+) logical bytes',log)
            if generic and preserved!=[str(2097152-131072)]:raise ValueError('generic inherited-byte counter differs')
            inode=(target/filename).stat().st_ino;sync('noop')
            if ((target/filename).stat().st_ino!=inode or fixtures.sha256(path)!=after
                    or fixtures.sha256(target/filename)!=after or fixtures.sha256(basis)!=before
                    or len(list(source.iterdir()))!=1 or len(list(target.iterdir()))!=1):raise ValueError('cross-volume no-op or old receiver preservation differs')
            rows.append(dict(**spec,before_sha256=before,after_sha256=after,exact=True,old_hardlink_preserved=True,noop_inode_preserved=True,
                semantic_clone=semantic,generic_clone=generic,inherited_logical_bytes=int(preserved[0]) if preserved else None))
            store.write(name+'-RESULT.json',rows[-1]);print('VOLUME_CASE_CLOSED',name,flush=True)
        info=plistlib.loads(command(['/usr/bin/hdiutil','info','-plist'],'before-detach').encode());owned_attachment(info,image,mount)
        if (image.lstat().st_dev,image.lstat().st_ino)!=(before_image.st_dev,before_image.st_ino):raise ValueError('owned image inode changed')
        command(['/usr/bin/hdiutil','detach',str(mount)],'image-detach')
        final=plistlib.loads(command(['/usr/bin/hdiutil','info','-plist'],'after-detach').encode())
        if any(row.get('image-path')==str(image) for row in final['images']):raise ValueError('owned attachment remains')
        artifacts();store.write('RESULT.json',dict(complete=True,cases=rows,calls=calls,owned_image_detached=True,all_direct_children_reaped=True,
            groups_absent=True,production_pins=production,scope='12case/36CLI directed cross-logical-volume functional matrix; same physical backing, no SDK/pixel/performance proof',parent_tool_terminal_proved=False))
        store.close();cpu.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        io.close_after_verified_settlement(owner_reaped=True,groups_settled=True,external_children_settled=True)
        print('VOLUME_CLOSED',len(rows),str(root),flush=True);return 0
    except BaseException as error:
        if not attempted and not isinstance(error,UnresolvedOwnership):
            try:
                store.write('PREENTRY-REFUSED.json',dict(child_attempted=False,error=repr(error)));store.close()
                if cpu is not None and not cpu.closed:close_unstarted(cpu)
                if io is not None and not io.closed:close_unstarted(io)
            except BaseException as cleanup:retain_after_record(lambda:print('VOLUME_PREENTRY_RETAIN',repr(cleanup),repr(error),flush=True))
            raise
        retain_after_record(lambda:print('VOLUME_RETAIN',repr(error),str(root),__import__('traceback').format_exc(),flush=True))


if __name__=='__main__':raise SystemExit(main())
