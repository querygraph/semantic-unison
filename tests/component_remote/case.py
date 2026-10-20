"""Inactive case kernel. An admitted outer owner must hold IO and CPU first."""
import os
import json
from pathlib import Path
import struct
import sys
import time
from component_remote.contract import CASES, FLAGS, ROOT, command
from component_remote.io import identity, sha, read, write, save
from shared_cpu_pool import require, UnresolvedOwnership
from component_remote.call import execute as invoke

def fixture(right=False,unsupported=False):
    data=bytearray(8192)
    if unsupported:
        data[:8]=b'NO-TIFF!';return bytes(data)
    struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
    for i,entry in enumerate([(273,4,1,4096),(279,4,1,1024),(700,1,16,1024),(50706,1,4,1025)]):
        struct.pack_into('<HHII',data,10+12*i,*entry)
    data[1024:1040]=b'<x>two</x>      ' if right else b'<x>one</x>      '
    data[4096:5120]=b'P'*1024;data[-1]=int(right)
    return bytes(data)

def snapshot(directory):
    result={}
    for side in ('left','right'):
        path=directory/side/'components.dng'
        require(sorted(p.name for p in path.parent.iterdir())==['components.dng'],'generated root contents changed')
        result[side]={'identity':identity(path),'sha256':sha(path)}
    return result

def execute(plan,index,deadline):
    directory=Path(plan['workspace'])/str(index);entered=False
    directory.mkdir(mode=0o700)
    try:
        _,server,mode=CASES[index]
        for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
        for name in ('proxy.py','measure.py','ownership.py','launcher.py'):
            write(directory/name,read(ROOT/'bench/sync'/name))
        os.chmod(directory/'launcher.py',0o700)
        write(directory/'left/components.dng',fixture())
        write(directory/'right/components.dng',fixture(True,mode=='unsupported'))
        before=snapshot(directory)
        require(deadline-time.monotonic()>35,'no new call near worker deadline')
        argv=command(plan,index)
        environment=dict(os.environ,UNISON=str(directory/'state'),
          PATH=str(Path(sys.executable).parent)+':/usr/bin:/bin',
          UNISON_SYNC_BENCH_BINARY=plan['artifacts'][server]['path'],
          UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(FLAGS),
          UNISON_SYNC_BENCH_PROXY_RECEIPT=str(directory/'proxy.json'),
          UNISON_SYNC_BENCH_SOCKET=str(directory/'call.sock'),
          UNISON_SYNC_BENCH_DEADLINE_SECONDS='35')
        save(directory/'INTENT.json',{'index':index,'command':argv})
        entered=True # before the only call site; uncertainty never becomes no-dispatch
        outcome=invoke(argv,environment,directory,min(deadline,time.monotonic()+30))
        save(directory/'OUTCOME.json',outcome)
        require(outcome['returncode']==0 and outcome['timed_out'] is False and
          outcome['capture_truncated'] is False and outcome['supervisor_capture_truncated'] is False and
          outcome['supervisor_cleanup']['returncode']==0 and outcome['proxy']['server_returncode']==0 and
          outcome['proxy']['fault'] is None and outcome['proxy']['pump_errors']==[] and
          'PROBE_FUNCTIONAL '+mode+'\n' in outcome['stdout'],'probe failed; stop before any successor case')
        if mode=='supported':
            require('LOCAL_SHA256 '+before['left']['sha256']+'\n' in outcome['stdout'] and
              'REMOTE_SHA256 '+before['right']['sha256']+'\n' in outcome['stdout'],'reported hashes differ from generated files')
        after=snapshot(directory)
        require(before==after,'generated input changed during component inspection')
        return {'index':index,'mode':mode,'before':before,'after':after,'outcome':outcome}
    except UnresolvedOwnership:raise
    except BaseException as error:
        if not entered:
            save(directory/'NO-DISPATCH.json',{'schema':'component-no-dispatch/1',
              'index':index,'measure_entered':False,'failure':repr(error)})
        raise
