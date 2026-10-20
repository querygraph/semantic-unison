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


class Cases:
    """Source-bound twelve-phase data lifecycle, only under admitted retained IO."""
    def __init__(self,packet,*,clone=None):
        from copy import deepcopy
        from sdk_merge_receiving.data import native_clone
        self.packet=deepcopy(packet);self.clone=native_clone if clone is None else clone
        self.index=0;self.active=None;self.history=[];self.endpoints={};self.accepted={}
        self.candidate=None;self.right_before=None;self.left_fault=None

    def fence_sources(self):
        for name,epoch in self.packet['source_observations'].items():
            require(stamp(os.lstat(name))==epoch,'retained generated source epoch changed')

    def prepare(self,row):
        from copy import deepcopy
        from sdk_merge_receiving.data import install
        codecs=('uncompressed','jpeg','jxl');policies=('require','warn');stages=('seed','negative')
        require(self.active is None and self.index<12,'exact one-use negative phase required')
        key=(row['codec'],row['policy'],row['stage'])
        require(key==(codecs[self.index//4],policies[self.index%4//2],stages[self.index%2]),
                'negative receiving phase order differs')
        root=Path(self.packet['workspace'])/(key[0]+'-'+key[1])
        require(row['directory']==str(root),'exact codec/policy namespace required')
        self.fence_sources();self.active=key
        reference=next(c for c in self.packet['cases'] if c['codec']==key[0])['states']['base']
        expected={k:reference[k] for k in ('sha256','bytes')};record=dict(codec=key[0],policy=key[1],stage=key[2],event='PREPARED')
        if key[2]=='seed':
            root.mkdir(mode=0o700)
            for side in ('left','right'):
                path=root/side;path.mkdir(mode=0o700);native=path.lstat()
                self.endpoints[key[:2],side]=(path,(native.st_dev,native.st_ino))
            path,identity=self.endpoints[key[:2],'left']
            record['clone']=install(reference,self.packet['source_observations'][reference['path']],
                path,identity,'seed',None,clone=self.clone)
        else:
            left,identity=self.endpoints[key[:2],'left']
            require(inspect(left,identity,expected)==self.accepted[key[:2],'left'],
                    'source-side disposable changed since seed')
            right,right_identity=self.endpoints[key[:2],'right']
            self.right_before=inspect(right,right_identity,expected)
            require(self.right_before==self.accepted[key[:2],'right'],'destination changed since seed')
            fault=install_fault(left,identity,expected,key[0]);self.left_fault=fault['after']
            record['fault']=fault;expected={k:fault['after'][k] for k in ('sha256','bytes')}
        record['candidate']=deepcopy(expected);self.candidate=deepcopy(expected)
        self.fence_sources();self.history.append(record)
        return expected

    def verify(self,row,candidate):
        from copy import deepcopy
        from sdk_negative_receiving.publication import verify
        key=(row['codec'],row['policy'],row['stage'])
        require(self.active==key and candidate==self.candidate,'only current exact candidate may verify')
        outputs={};self.fence_sources()
        for side in ('left','right'):
            path,identity=self.endpoints[key[:2],side]
            expected=candidate if key[2]=='seed' or side=='left' or key[1]=='warn' else {k:self.right_before[k] for k in ('sha256','bytes')}
            outputs[side]=inspect(path,identity,expected)
        if key[2]=='negative':
            require(outputs['left']==self.left_fault,'SDK/CLI changed source-side disposable fault')
            publication=verify(policy=key[1],before=self.right_before,after=outputs['right'],candidate=candidate)
        else:publication=dict(seed_exact=True,resource_release_authorized=False)
        self.fence_sources()
        for side in outputs:self.accepted[key[:2],side]=deepcopy(outputs[side])
        self.history.append(dict(codec=key[0],policy=key[1],stage=key[2],event='VERIFIED',
                                 outputs=deepcopy(outputs),publication=deepcopy(publication)))
        self.index+=1;self.active=None;self.candidate=None;self.left_fault=None;self.right_before=None
        return publication
