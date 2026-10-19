"""One-use fault installation into an already-owned disposable generated clone.

Call only under admitted IO/CPU after clone-only source installation. This opens
only endpoint/image.dng, never a retained input, original or arbitrary filename.
"""
import hashlib,os
from pathlib import Path
from private_camera_receiving.close import close_descriptors
from sdk_fixture_digest_fault import corrupt_new_raw_digest
from sdk_merge_receiving.data import directory,hash_fd,inspect,stamp
from sdk_merge_receiving.plan import require


def install_fault(endpoint,identity,expected,codec):
    before=inspect(endpoint,identity,expected)
    fds=[]
    try:
        parent=os.open(endpoint,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(parent)
        directory(parent,endpoint,identity)
        fd=os.open('image.dng',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
        def bound(epoch):
            require(stamp(os.fstat(fd))==epoch==stamp(os.stat('image.dng',dir_fd=parent,follow_symlinks=False)),
                    'disposable image name/epoch changed')
            directory(parent,endpoint,identity)
        bound(before['identity']);parts=[];at=0
        while at<expected['bytes']:
            block=os.pread(fd,min(1048576,expected['bytes']-at),at)
            require(bool(block),'short owned generated clone before fault')
            parts.append(block);at+=len(block)
        require(not os.pread(fd,1,at),'owned generated clone grew')
        data=b''.join(parts);bound(before['identity'])
        require(hashlib.sha256(data).hexdigest()==expected['sha256'],'clone changed before exact digest fault')
        fault=corrupt_new_raw_digest(data,codec);offset=fault['offset']
        require(os.pwrite(fd,fault['data'][offset:offset+1],offset)==1,'one-byte digest fault write incomplete')
        os.fsync(fd);after=stamp(os.fstat(fd))
        require(all(after[k]==before['identity'][k] for k in before['identity'] if k not in ('st_mtime_ns','st_ctime_ns')),
                'fault changed disposable identity/size/mode/link ownership')
        bound(after);digest=hash_fd(fd,expected['bytes']);bound(after)
        require(digest==hashlib.sha256(fault['data']).hexdigest() and digest!=expected['sha256'],
                'one-bit generated fault readback differs')
        os.fsync(parent)
        return dict(before=before,after=dict(sha256=digest,bytes=expected['bytes'],identity=after),
            mutation=dict(tag=fault['tag'],offset=offset,bytes_changed=1,xor_mask=1),
            source_payload_hash_bytes=0,actual_SDK_finding_proved=False,
            receiving_publication_proved=False,resource_release_authorized=False)
    finally:close_descriptors(fds)
