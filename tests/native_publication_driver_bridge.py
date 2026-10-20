"""Trusted original-driver bindings; never patch the actual subprocess module."""
import os,subprocess
from pathlib import Path


class Commands:
    def __init__(self,compiler,work,invoke):
        self.compiler=compiler;self.work=Path(work);self.invoke=invoke
    def run(self,argv,*,cwd=None,env=None,check=False,timeout=None,capture_output=False,text=False):
        argv=[os.fspath(x) for x in argv]
        native={str(self.work/name) for name in ('publication-test','lease-test')}
        if (not argv or argv[0] not in native|{self.compiler} or any('\0' in x for x in argv)
                or cwd is not None and Path(cwd)!=self.work
                or timeout is not None and (type(timeout) not in (int,float) or not 0<timeout<=60)
                or any(type(x) is not bool for x in (check,capture_output,text))):
            raise ValueError('exact original driver command/working-directory bound required')
        out=self.invoke(argv,env,cwd,30 if timeout is None else timeout)
        result=subprocess.CompletedProcess(argv,out['returncode'],
            (out['stdout'] if text else out['stdout'].encode()) if capture_output else None,
            (out['stderr'] if text else out['stderr'].encode()) if capture_output else None)
        if check:result.check_returncode()
        return result
    def check_output(self,argv,*,text=False,env=None):
        return self.run(argv,check=True,capture_output=True,text=text,env=env).stdout


class Temporary:
    def __init__(self,work,prefix):self.work=Path(work);self.prefix=prefix;self.created=False
    def mkdtemp(self,*,prefix,dir):
        if self.created or prefix!=self.prefix or dir!='/private/tmp':raise ValueError('one exact original temporary namespace required')
        self.work.mkdir(mode=0o700);self.created=True;return str(self.work)
    def TemporaryDirectory(self,*,prefix,dir):
        self.mkdtemp(prefix=prefix,dir=dir);return self
    def __enter__(self):return str(self.work)
    def __exit__(self,*error):return False


def driver_source(raw):
    """Replace only module imports with caller-owned compatible bindings."""
    for statement in ('import subprocess\n','import tempfile\n'):
        if raw.count(statement)!=1:raise ValueError('original import seam changed')
        raw=raw.replace(statement,'')
    return raw
