"""Retained invocation bridge for the unchanged original clone-stage driver.

Only this driver's module globals are replaced. The actual subprocess module
used by the retained kernel is untouched. No cleanup of generated fixtures.
"""
import os
import subprocess


class Bridge:
    def __init__(self,harness,invoke):
        self.allowed={harness,'/usr/bin/xattr','/bin/chmod','/bin/ls','/usr/bin/chflags'}
        self.invoke=invoke;self.calls=[]

    def run(self,argv,*,check=False,timeout=None,text=False,capture_output=False):
        argv=[os.fspath(p) for p in argv]
        if (not argv or argv[0] not in self.allowed or any('\0' in p for p in argv)
                or type(check) is not bool or type(text) is not bool or type(capture_output) is not bool
                or timeout is not None and (type(timeout) not in (int,float) or not 0<timeout<=60)):
            raise ValueError('exact original-driver subprocess contract required')
        out=self.invoke(argv,30 if timeout is None else timeout)
        self.calls.append(out)
        result=subprocess.CompletedProcess(argv,out['returncode'],
            (out['stdout'] if text else out['stdout'].encode()) if capture_output else None,
            (out['stderr'] if text else out['stderr'].encode()) if capture_output else None)
        if check:result.check_returncode()
        return result

    def check_output(self,argv,*,text=False):
        return self.run(argv,check=True,text=text,capture_output=True).stdout


class RetainedDirectory:
    def __init__(self,path,*,prefix,dir):
        if prefix!='unison-clone-stage-' or dir!='/private/tmp':
            raise ValueError('exact original temporary-directory request required')
        self.path=path
    def __enter__(self):
        self.path.mkdir(mode=0o700);return str(self.path)
    def __exit__(self,*error):
        # No implicit rm/rmtree, including after an assertion or known failure.
        return False
