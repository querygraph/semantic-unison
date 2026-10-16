"""Single-seed transport kernel; requires separate pinned SDK/IO admission.

Import/construction never runs binaries. A caller must journal, retain child
ownership and audit SDK groups before settling its aggregate or closing grants.
"""
import json
import os
from pathlib import Path
import sys
import time
import sdk_budget

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from artifact_pins import stable_sha
from run import measure_invocation, InvocationFailure


SCRIPT_NAMES = ('proxy.py', 'measure.py', 'launcher.py', 'ownership.py')
BUILD = 'unison-sdk171-2724-v1-single'


def require(value, message):
    if not value:
        raise ValueError(message)


class Invoker:
    def __init__(self, directory, binary, tool, journal, script_pins, deadline_monotonic):
        self.directory=Path(directory); self.binary=dict(binary); self.tool=dict(tool)
        self.journal=journal; self.pins=dict(script_pins); self.deadline=deadline_monotonic
        self.used=False
        sdk_budget.validate()
        require(self.directory.is_absolute() and binary['label'] in ('stock','ox')
                and set(self.pins)==set(SCRIPT_NAMES), 'exact owned same-compiler case required')
        require(tool['build_id']==BUILD and tool['threads']==1,
                'only qualified single-thread v1 SDK driver is planned')
        for item in (binary, tool):
            require(Path(item['path']).is_absolute() and len(item['sha256'])==64
                    and all(c in '0123456789abcdef' for c in item['sha256']),
                    'exact binary and SDK executable pins required')

    def __call__(self):
        require(not self.used, 'one receiving seed only; never retry')
        self.used=True
        require(time.monotonic()+135<self.deadline, 'no SDK call near observation deadline')
        for item in (self.binary,self.tool):
            require(stable_sha(item['path'])==item['sha256'], 'receiving binary/tool changed')
        for name,digest in self.pins.items():
            require(stable_sha(self.directory/name)==digest, 'copied transport source changed')
        flags=['-clone','auto','-semanticdng','-semanticworkers','2','-maxthreads','2',
               '-adobevalidate','require','-adobevalidator',self.tool['path'],
               '-adobevalidatorhash',self.tool['sha256'],
               '-adobevalidatorbuild',self.tool['build_id'],'-adobevalidatorthreads','1',
               '-adobevalidatetimeout','90','-adobevalidatorworkspace',str(sdk_budget.WORKSPACE_MIB),
               '-semanticpayloadbudget',str(sdk_budget.GATE_MIB),'-validationtreememory','0',
               '-semanticdescriptorbudget','64',
               '-debug','validation-process',
               '-debug','validation-group','-debug','copy','-debug','semantic']
        socket=self.directory/'seed.sock'
        require(len(os.fsencode(socket))<100, 'Darwin socket path exceeds budget')
        env=dict(os.environ,UNISON=str(self.directory/'state'),
                 UNISON_SYNC_BENCH_BINARY=self.binary['path'],
                 UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
                 UNISON_SYNC_BENCH_PROXY_RECEIPT=str(self.directory/'seed-proxy.json'),
                 UNISON_SYNC_BENCH_SOCKET=str(socket),UNISON_SYNC_BENCH_DEADLINE_SECONDS='125')
        command=[self.binary['path'],str(self.directory/'left'),
                 'ssh://localhost/'+str(self.directory/'right'),
                 '-sshcmd',str(self.directory/'launcher.py'),'-servercmd',self.binary['path'],
                 '-batch','-auto','-fastcheck','false','-times',*flags]
        self.journal.begin({'label':self.binary['label'],'mode':'semantic','workers':2,
                            'directory':str(self.directory),'stage':'seed'},command)
        try:
            outcome=measure_invocation(command,env,120,self.directory/'proxy.py',
                                       strict_group_settlement=True)
        except InvocationFailure as error:
            self.journal.finish(error.outcome)
            raise
        self.journal.finish(outcome)
        return outcome
