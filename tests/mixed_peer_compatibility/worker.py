"""Inactive finite worker kernel; admitted outer owner must hold IO then CPU.

No standalone launch path. Persist callback owns durable aggregate snapshots.
Every actual call's intent/outcome is persisted before functional inspection.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time
from component_remote.call import execute as retained_call
from component_remote.io import load, read, write, identity
from invocation_journal import Journal
from mixed_peer_compatibility.audit import audit, require
from mixed_peer_compatibility.contract import RETAINED_FORK, CASES, STAGES, command

ROOT = Path(__file__).resolve().parents[2]


def fixture(updated=False):
    data=bytearray(8192)
    struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
    for i,entry in enumerate(((273,4,1,4096),(279,4,1,1024),
                              (700,1,16,1024),(50706,1,4,1025))):
        struct.pack_into('<HHII',data,10+12*i,*entry)
    data[1024:1040]=b'<x>two</x>      ' if updated else b'<x>one</x>      '
    data[4096:5120]=b'P'*1024
    return bytes(data)


def execute(artifacts, workspace, deadline, persist, peer_contract=RETAINED_FORK):
    """Artifacts already authenticated by future outer owner after IO acquisition.

    Unknown call state propagates the actual retained carrier. Ordinary errors
    preserve the journal; the parent must independently audit before any release.
    """
    workspace=Path(workspace)
    result={'complete':False,'cases':[]}
    journal=Journal(result,lambda:persist(result))
    raw=[]
    for index,(label,orientation) in enumerate(CASES):
        directory=workspace/str(index)
        directory.mkdir(mode=0o700)
        for name in ('left','right','state'):(directory/name).mkdir(mode=0o700)
        source=directory/'left/item.dng';target=directory/'right/item.dng'
        write(source,fixture())
        case={'index':index,'stages':[]};result['cases'].append(case)
        previous_target=None
        for stage in STAGES:
            require(deadline-time.monotonic()>35,'no new mixed-peer call near deadline')
            call_dir=directory/stage;call_dir.mkdir(mode=0o700)
            if stage=='update':
                replacement=directory/'left/replacement'
                write(replacement,fixture(True));os.replace(replacement,source)
            before=identity(source);expected=fixture(stage!='seed')
            for name in ('proxy.py','measure.py','ownership.py','launcher.py'):
                write(call_dir/name,read(ROOT/'bench/sync'/name))
            os.chmod(call_dir/'launcher.py',0o700)
            argv,flags=command(artifacts,str(workspace),index,stage,peer_contract)
            server=artifacts[label if orientation=='old-client' else 'old-stock']
            environment=dict(os.environ,UNISON=str(directory/'state'),
                PATH=str(Path(sys.executable).parent)+':/usr/bin:/bin',
                UNISON_SYNC_BENCH_BINARY=server,
                UNISON_SYNC_BENCH_SERVER_FLAGS=json.dumps(flags),
                UNISON_SYNC_BENCH_PROXY_RECEIPT=str(call_dir/'proxy.json'),
                UNISON_SYNC_BENCH_SOCKET=str(call_dir/'call.sock'),
                UNISON_SYNC_BENCH_DEADLINE_SECONDS='35')
            journal.begin(dict(case=index,label=label,orientation=orientation,stage=stage),argv)
            outcome=retained_call(argv,environment,call_dir,min(deadline,time.monotonic()+30))
            journal.finish(outcome)
            raw.append(load(call_dir/'proxy.json'))
            audit(result,artifacts,str(workspace),raw,peer_contract)
            require(outcome['returncode']==0 and outcome['supervisor_cleanup']['returncode']==0
                    and outcome['proxy']['server_returncode']==0
                    and outcome['proxy']['fault'] is None
                    and outcome['proxy']['pump_errors']==[], 'mixed-peer call failed; stop')
            require(identity(source)==before and read(source,8192)==expected
                    and read(target,8192)==expected, 'mixed-peer exact bytes/source fence differs')
            target_identity=identity(target)
            if stage=='noop':
                require(target_identity==previous_target,'noop replaced or modified target')
            previous_target=target_identity
            case['stages'].append(dict(stage=stage,sha256=hashlib.sha256(expected).hexdigest(),
                                       source_identity=before,target_identity=target_identity))
            persist(result)
    result['complete']=True;persist(result)
    return result
