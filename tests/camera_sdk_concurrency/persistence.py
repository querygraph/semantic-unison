"""Bounded private result publication with qualified close uncertainty."""
import json
import os
from pathlib import Path
import stat
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from private_camera_receiving.close import close_descriptors
MAX_BYTES=16*1048576


def save(directory,value):
    raw=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')
    if len(raw)>MAX_BYTES:raise ValueError('bounded result JSON required')
    directory=Path(directory);before=os.lstat(directory)
    if (not directory.is_absolute() or not stat.S_ISDIR(before.st_mode)
            or before.st_mode & 0o777 != 0o700 or before.st_uid!=os.getuid()):
        raise ValueError('private owned result namespace required')
    dfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        held=os.fstat(dfd)
        if (before.st_dev,before.st_ino)!=(held.st_dev,held.st_ino):
            raise ValueError('result namespace identity changed')
        fd=os.open('RESULT.next',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                   0o600,dir_fd=dfd)
        try:
            at=0
            while at<len(raw):
                count=os.write(fd,raw[at:])
                if count<=0:raise OSError('result write made no progress')
                at+=count
            os.fsync(fd)
        finally:
            close_descriptors([fd])
        os.replace('RESULT.next','RESULT.json',src_dir_fd=dfd,dst_dir_fd=dfd)
        os.fsync(dfd)
    finally:
        close_descriptors([dfd])
