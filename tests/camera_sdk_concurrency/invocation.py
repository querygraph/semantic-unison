"""One-shot transport kernel; exact future admission/owned dispatcher required."""
import hashlib
import os
from pathlib import Path
import stat
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'bench/sync'))
from private_camera_receiving.close import close_descriptors
from run import measure_invocation, InvocationFailure
from command import command
SCRIPT_NAMES=('proxy.py','measure.py','launcher.py','ownership.py')
FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')


def artifact_sha(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0<before.st_size<=128*1024*1024:
            raise ValueError('bounded regular execution artifact required')
        digest=hashlib.sha256();total=0
        while total<before.st_size:
            block=os.read(fd,min(1048576,before.st_size-total))
            if not block:raise ValueError('short artifact read')
            total+=len(block);digest.update(block)
        if os.read(fd,1) or any(getattr(before,k)!=getattr(now,k)
                for now in (os.fstat(fd),os.lstat(path)) for k in FIELDS):
            raise ValueError('artifact epoch changed')
        return digest.hexdigest()
    finally:
        close_descriptors([fd])


class Invoker:
    def __init__(self,directory,*,binary,tool,journal,script_pins,deadline):
        self.directory=Path(directory);self.binary=dict(binary);self.tool=dict(tool)
        self.contract=command(directory,binary=self.binary,tool=self.tool)
        self.journal=journal;self.pins=dict(script_pins);self.deadline=deadline;self.used=False
        if set(self.pins)!=set(SCRIPT_NAMES) or any(type(v) is not str or len(v)!=64
                or any(c not in '0123456789abcdef' for c in v) for v in self.pins.values()):
            raise ValueError('exact transport script pins required')
        if type(deadline) not in (int,float) or not 0<deadline<float('inf'):
            raise ValueError('finite observation deadline required')

    def __call__(self):
        if self.used:raise ValueError('one seed only; no retry')
        self.used=True
        if time.monotonic()+135>=self.deadline:raise ValueError('insufficient call observation window')
        for item in (self.binary,self.tool):
            if artifact_sha(item['path'])!=item['sha256']:raise ValueError('execution artifact changed')
        for name,digest in self.pins.items():
            if artifact_sha(self.directory/name)!=digest:raise ValueError('transport source changed')
        argv=self.contract['argv'];env=dict(os.environ,**self.contract['environment_overrides'])
        self.journal.begin({'label':self.binary['label'],'mode':'semantic','workers':3,
                            'directory':str(self.directory),'stage':'seed'},argv)
        try:
            outcome=measure_invocation(argv,env,120,self.directory/'proxy.py',strict_group_settlement=True)
        except InvocationFailure as error:
            self.journal.finish(error.outcome)
            raise
        self.journal.finish(outcome)
        return outcome
