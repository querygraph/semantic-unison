"""Tiny disposable APFS syscall control; no retained payload, SDK or compiler."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from sdk_multifile.clone import prepare_inputs,prepare,stamp


def controls():
    root=Path(tempfile.mkdtemp(prefix='u-smr-nativeclone-',dir='/private/tmp'));root.chmod(0o700);cases=[]
    for mode in (0o400,0o644):
        w=root/oct(mode);w.mkdir(mode=0o700);left=w/'left';left.mkdir(mode=0o700)
        inputs=[];sources=[];originals={}
        for i,name in enumerate(('uncompressed.dng','jpeg.dng')):
            # Original bytes are not DNGs: names exercise only fixed adapter slots.
            value=(b'original disposable native clone control\0'+bytes([i]))*16
            p=w/name
            with p.open('xb') as f:f.write(value)
            p.chmod(mode);identity=stamp(p.lstat());digest=hashlib.sha256(value).hexdigest();originals[name]=value
            inputs.append(dict(candidate_id=name,path=str(p),sha256=digest,identity=identity))
            sources.append(dict(candidate_id=name,sha256=digest,bytes=len(value)))
        records=prepare_inputs(inputs,sources,left)
        assert len(records)==2
        for item,record in zip(inputs,records):
            source=Path(item['path']);clone=left/item['candidate_id']
            assert stamp(source.lstat())==item['identity'] and source.read_bytes()==originals[item['candidate_id']]
            assert clone.read_bytes()==originals[item['candidate_id']]
            assert record['backend']=='native-fclonefileat-only' and record['source_payload_read_bytes']==0
            assert stat.S_IMODE(clone.lstat().st_mode)==0o600 and clone.lstat().st_nlink==1
            assert (clone.lstat().st_dev,clone.lstat().st_ino)!=(source.lstat().st_dev,source.lstat().st_ino)
            baseline=stamp(clone.lstat())
            try:prepare(source,item['identity'],left,item['candidate_id'])
            except ValueError as error:assert 'already consumed' in str(error)
            else:raise AssertionError('existing clone must refuse without replacement')
            assert stamp(clone.lstat())==baseline and stamp(source.lstat())==item['identity']
        cases.append(dict(source_mode=oct(mode),native_clones=records,exact_tiny_bytes=True,source_metadata_unchanged=True,existing_name_refused=True))
    receipt=dict(cases=cases,scope='Four native fclonefileat operations on original tiny disposable files. Exact bytes/distinct inode/source metadata/no overwrite checked. Verification reads only these tiny original fixtures; no retained generated/camera input/SDK/compiler/canonical IO. Native syscall success is not physical sharing or write-savings proof.')
    (root/'RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(workspace=str(root),native_clone_calls=4,source_payload_bytes=sum(s['bytes'] for s in sources)*2,sdk_calls=0)),flush=True)


if __name__=='__main__':
    from shared_cpu_pool import UnresolvedOwnership
    from shared_process_owner import retain_after_record
    try:controls()
    except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),flush=True))
