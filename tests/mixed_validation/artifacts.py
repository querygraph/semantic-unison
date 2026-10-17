import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
"""Pinned artifact/clone preparation under caller-owned IO; no admission grant."""
import hashlib
import os
from pathlib import Path
import stat
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from mixed_validation.plan import commands,artifact
from sdk_multifile.clone import prepare as prepare_clone,stamp,native_clone
from private_camera_receiving.close import close_descriptors


def verified_hash(item, *, expected_epoch=None):
    """Hash one exact regular file; every close uncertainty retains its identity."""
    artifact(item)
    before=os.lstat(item['path'])
    fd=os.open(item['path'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        held=os.fstat(fd)
        if (not stat.S_ISREG(held.st_mode) or held.st_uid!=os.getuid()
                or held.st_nlink!=1 or held.st_size!=item['bytes']
                or stamp(before)!=stamp(held)
                or (expected_epoch is not None and stamp(held)!=expected_epoch)):
            raise ValueError('artifact identity/type/size differs')
        digest=hashlib.sha256();remaining=item['bytes']
        while remaining:
            chunk=os.read(fd,min(1048576,remaining))
            if not chunk:raise ValueError('short artifact read')
            digest.update(chunk);remaining-=len(chunk)
        if os.read(fd,1):raise ValueError('artifact grew')
        if (digest.hexdigest()!=item['sha256'] or stamp(os.fstat(fd))!=stamp(held)
                or stamp(os.lstat(item['path']))!=stamp(held)):
            raise ValueError('artifact SHA/epoch changed')
        return stamp(held)
    finally:
        close_descriptors([fd])


def verify_sources(plan):
    """Rehash execution/tool inventory; source media is metadata-fenced only."""
    commands(plan)
    items=list(plan['source_pins'])+list(plan['ancestry'])
    items += [row[k] for row in plan['probes'] for k in ('executable','build_receipt')]
    items += [plan['sdk'][k] for k in ('executable','manifest')]
    items += [plan['metadata'][k] for k in ('executable','inventory')]
    # Never accidentally rehash a source supplied again as an artifact pin.
    if any(item['path']==plan['input']['path'] for item in items):
        raise ValueError('source media cannot be an execution artifact')
    for item in items:verified_hash(item)
    if stamp(os.lstat(plan['input']['path']))!=plan['input_epoch']:
        raise ValueError('source metadata changed')


def prepare_input(plan,index,*,clone=native_clone):
    argv=commands(plan)
    if type(index) is not int or index not in (0,1):raise ValueError('exact probe index required')
    workspace=Path(plan['workspace']);root=os.lstat(workspace)
    if (not stat.S_ISDIR(root.st_mode) or root.st_uid!=os.getuid()
            or stat.S_IMODE(root.st_mode)!=0o700):
        raise ValueError('owned private worker workspace required')
    directory=workspace/plan['probes'][index]['label']
    directory.mkdir(mode=0o700) # Existing path is consumed, never replaced.
    record=prepare_clone(plan['input']['path'],plan['input_epoch'],directory,
                         'uncompressed.dng',clone=clone)
    candidate=dict(path=argv[index][3],sha256=plan['input']['sha256'],bytes=plan['input']['bytes'])
    verified_hash(candidate,expected_epoch=record['clone_identity'])
    current=os.lstat(workspace)
    if (root.st_dev,root.st_ino)!=(current.st_dev,current.st_ino):
        raise ValueError('worker workspace replaced')
    return record


def verify_input(plan,index,record):
    argv=commands(plan)
    if stamp(os.lstat(plan['input']['path']))!=plan['input_epoch']:
        raise ValueError('source metadata changed')
    return verified_hash(dict(path=argv[index][3],sha256=plan['input']['sha256'],
                              bytes=plan['input']['bytes']),expected_epoch=record['clone_identity'])
