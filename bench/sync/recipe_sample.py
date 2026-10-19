"""Versioned two-file protected-change/growth workload, arbitrary generated data.

Trusted source-selected consumer only, not a general TIFF editor or grant.
Old receiver descriptors stay open across update and no-op. Errors preserve them.
"""
from dataclasses import dataclass
import os,stat
from pathlib import Path
from corpus_workloads import File
from workloads import KINDS,layout,recipe
from workload_fixtures import create,edit,digest,epoch
from batch_inventory import validate
from batch_verify import verify,verify_expected
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership

MAXIMUM = 2*1048576+16384


@dataclass(frozen=True)
class RecipeCorpus:
    workload: str
    files: tuple
    file_bytes: int
    packet_bytes: int
    target_file_bytes: int
    generated_target_bytes: int
    before_files: int = 2
    added_files: int = 0
    semantic_updates: int = 0
    fallback_updates: int = 2
    schema: str = 'unison-generated-two-file-recipe/1'


def plan(workload, *, count=2, file_bytes=2*1048576, packet_bytes=8192):
    if workload not in KINDS or workload=='fixed-xmp' or type(count) is not int or count!=2:
        raise ValueError('explicit two-file nonfixed recipe required')
    if type(file_bytes) is not int or file_bytes!=2*1048576 or type(packet_bytes) is not int or packet_bytes!=8192:
        raise ValueError('versioned2MiB/8192byte packet recipe required')
    target=recipe(layout(file_bytes,packet_bytes),workload).target_size
    if target>MAXIMUM:raise ValueError('recipe target exceeds bounded consumer')
    files=tuple(File('group-000/image-%05d.dng'%i,i,True,workload,False) for i in range(2))
    return RecipeCorpus(workload,files,file_bytes,packet_bytes,target,target*2)


def validate_rows(rows):return validate(rows,maximum_file_bytes=MAXIMUM)


def verify_replica(root,rows,*,phase):
    return verify(root,rows,phase=phase,maximum_file_bytes=MAXIMUM)


def sample(corpus,left,right,*,invoke,record):
    if corpus!=plan(corpus.workload):raise ValueError('exact unshrunk recipe required')
    roots=[Path(left),Path(right)];ids=[]
    for root in roots:
        st=root.lstat()
        if not(root.is_absolute() and stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700
               and st.st_uid==os.getuid() and not os.listdir(root)):
            raise ValueError('fresh owned empty recipe roots required')
        ids.append((st.st_dev,st.st_ino))
    if ids[0]==ids[1]:raise ValueError('distinct roots required')
    def fence():
        for root,identity in zip(roots,ids):
            st=root.lstat()
            if not(stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700
                   and st.st_uid==os.getuid() and (st.st_dev,st.st_ino)==identity):
                raise ValueError('recipe root changed')
    metadata={};readers={};before={}
    try:
        record(dict(stage='seed-intent',planned_files=2));(roots[0]/'group-000').mkdir(mode=0o700)
        for file in corpus.files:
            fence();metadata[file.relative_path]=create(roots[0]/file.relative_path,corpus.file_bytes,corpus.packet_bytes,file.seed_index)
        seed=[dict(path=name,sha256=m['before_sha256'],bytes=corpus.file_bytes) for name,m in metadata.items()]
        record(dict(stage='seed-inventory',files=seed))
        verify_expected(roots[0],seed,maximum_file_bytes=MAXIMUM);verify_expected(roots[1],[])
        invoke('seed');fence()
        verify_expected(roots[0],seed,maximum_file_bytes=MAXIMUM);verify_expected(roots[1],seed,maximum_file_bytes=MAXIMUM)
        record(dict(stage='seed-verified',files=2))
        for file in corpus.files:
            fd=os.open(roots[1]/file.relative_path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
            readers[file.relative_path]=fd;before[file.relative_path]=epoch(os.fstat(fd))
        def old_readers():
            for name,fd in readers.items():
                st=os.fstat(fd);saved=before[name]
                if (not 0<=st.st_nlink<=1 or any(getattr(st,k)!=saved[k] for k in
                        ('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_uid'))
                        or digest(fd,corpus.file_bytes)!=metadata[name]['before_sha256']):
                    raise ValueError('old reader bytes/identity changed')
        old_readers();rows=[]
        for file in corpus.files:
            fence();m=metadata[file.relative_path]
            target=edit(roots[0]/file.relative_path,m,corpus.workload)
            rows.append(dict(path=file.relative_path,before_present=True,before_sha256=m['before_sha256'],
                target_sha256=target,target_bytes=corpus.target_file_bytes,expected_class='ordinary-fallback'))
        record(dict(stage='update-inventory',files=rows))
        verify_replica(roots[0],rows,phase='target');verify_expected(roots[1],seed,maximum_file_bytes=MAXIMUM)
        invoke('update');fence();old_readers()
        verify_replica(roots[0],rows,phase='target');updated=verify_replica(roots[1],rows,phase='target')
        record(dict(stage='update-verified',observations=updated))
        invoke('noop');fence();old_readers()
        verify_replica(roots[0],rows,phase='target');final=verify_replica(roots[1],rows,phase='target')
        if final!=updated:raise ValueError('recipe no-op changed receiving identity')
        record(dict(stage='noop-verified',observations=final))
        while readers:
            name,fd=readers.popitem();close_descriptors([fd])
        return dict(files=2,verified_phases=3,retained_old_readers_unchanged=True,
                    process_audit_required=True,resource_release_authorized=False)
    except BaseException as error:
        retained=error if isinstance(error,UnresolvedOwnership) else UnresolvedOwnership('recipe incomplete; retain readers and caller resources')
        if retained is not error:retained.original_failure=error
        retained.recipe_readers=readers;retained.recipe_old_epochs=before
        excluded=set(getattr(retained,'uncertain_fds',()))
        retained.retained_fds=tuple(dict.fromkeys(fd for fd in (*retained.retained_fds,*readers.values()) if fd not in excluded))
        if retained is error:raise
        raise retained from error
