"""Prepared original case transport; caller owns admission/IO/CPU/lifecycle.

No CLI or default binaries. No call occurs on construction/import. Owner must
audit the journal and aggregate independently before releasing resources.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
from run import measure_invocation, InvocationFailure
from artifact_pins import stable_sha as file_hash


def require(value,reason):
    if not value:raise ValueError(reason)


def prepare(directory):
    """Copy four pinned source scripts into an unused private case directory."""
    directory=Path(directory)
    require(directory.is_absolute() and directory.is_dir() and not directory.is_symlink(),
            'owned case directory required')
    for name in ('proxy.py','measure.py','launcher.py','ownership.py'):
        target=directory/name
        require(not target.exists() and not target.is_symlink(),'transport script already exists')
        with (ROOT/'bench/sync'/name).open('rb') as source,target.open('xb') as output:
            shutil.copyfileobj(source,output,65536)
        target.chmod(0o700 if name=='launcher.py' else 0o600)
    return {name:file_hash(directory/name) for name in ('proxy.py','measure.py','launcher.py','ownership.py')}


class Invoker:
    def __init__(self,directory,client,server,journal,script_pins,deadline_monotonic):
        self.directory=Path(directory);self.client=client;self.server=server
        self.journal=journal;self.script_pins=script_pins
        self.deadline=deadline_monotonic;self.next_stage=0
        require(set(script_pins)=={'proxy.py','measure.py','launcher.py','ownership.py'},
                'exact transport source pins required')
        for item in (client,server):
            require(item['label'] in ('stock','ox') and Path(item['path']).is_absolute()
                    and len(item['sha256'])==64
                    and all(c in '0123456789abcdef' for c in item['sha256']),
                    'exact compiler binary identity required')

    def __call__(self,stage):
        require(self.next_stage<3 and stage==('seed','update','noop')[self.next_stage],
                'one ordered invocation per stage only')
        require(time.monotonic()+70<self.deadline,'no new call near observation deadline')
        for item in (self.client,self.server):
            require(file_hash(item['path'])==item['sha256'],'pinned binary changed')
        for name,digest in self.script_pins.items():
            require(file_hash(self.directory/name)==digest,'copied transport source changed')
        flags=['-clone','auto','-semanticdng','-semanticworkers','2','-maxthreads','2',
               '-adobevalidate','off','-debug','copy','-debug','semantic']
        socket=self.directory/(stage+'.sock')
        require(len(os.fsencode(socket))<100,'Darwin Unix socket path budget exceeded')
        env=dict(os.environ,UNISON=str(self.directory/'state'),
                 UNISON_SYNC_BENCH_BINARY=self.server['path'],
                 UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
                 UNISON_SYNC_BENCH_PROXY_RECEIPT=str(self.directory/(stage+'-proxy.json')),
                 UNISON_SYNC_BENCH_SOCKET=str(socket),UNISON_SYNC_BENCH_DEADLINE_SECONDS='65')
        command=[self.client['path'],str(self.directory/'left'),
                 'ssh://localhost/'+str(self.directory/'right'),'-sshcmd',str(self.directory/'launcher.py'),
                 '-servercmd',self.server['path'],'-batch','-auto','-fastcheck','false','-times',*flags]
        self.journal.begin({'label':self.client['label'],'mode':'semantic','workers':2,
                            'directory':str(self.directory),'stage':stage},command)
        self.next_stage+=1 # Failure consumes the stage; never retry the call.
        try:
            outcome=measure_invocation(command,env,60,self.directory/'proxy.py',strict_group_settlement=True)
        except InvocationFailure as error:
            self.journal.finish(error.outcome)
            raise
        self.journal.finish(outcome)
        if stage=='update':
            log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
            require('Remote semantic fallback: no negotiated profile proves eligibility' in log,
                    'actual camera layout did not take declared semantic fallback')
            require(log.count('Using immutable receiver clone basis')==1
                    and 'Remote semantic clone wrote' not in log
                    and 'Local source clone completed' not in log,
                    'receiver-basis fallback evidence differs')
        return outcome
