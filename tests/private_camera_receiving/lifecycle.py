"""Real Python binding/reap controls, disposable inner grants, tiny source only.

The real outer owner holds canonical Unison8. Inner admission and the child
script's command identity are explicit test doubles; no canonical IO is held.
"""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import execute
import clone
import shared_dispatch as dispatch
from shared_cpu_pool import close_descriptors

HERE=Path(__file__).resolve()


class Lease:
    def __init__(self,directory,count):
        self.fds=tuple(os.open(directory/str(i),os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
                       for i in range(count))
        self.closed=False
    def close_after_verified_settlement(self,**proof):
        assert all(v is True for v in proof.values()) and not self.closed
        self.closed=True
        close_descriptors(self.fds)


def argv(plan,digest,workspace):
    return [sys.executable,str(HERE),'--worker','--plan',str(plan),
            '--plan-sha256',digest,'--workspace',str(workspace)]


def child():
    plan_path,digest,workspace=sys.argv[3],sys.argv[5],Path(sys.argv[7])
    assert hashlib.sha256(Path(plan_path).read_bytes()).hexdigest()==digest
    plan=json.loads(Path(plan_path).read_text())
    args=SimpleNamespace(plan=plan_path,plan_sha256=digest,workspace=str(workspace))
    # Test only the live-parent/FD boundary. The real payload kernel MUST NOT
    # be called, even in the nine-descriptor positive case.
    with patch.object(execute,'child_argv',side_effect=argv), \
         patch.object(execute.worker,'execute',side_effect=ValueError('original pre-payload fixture refusal')):
        try:
            execute.worker_entry(args,plan)
        except ValueError as error:
            from run import save
            save(workspace/'RESULT.json',{'schema':'unison-camera-receiving-worker/1',
                'complete':False,'phase':'PREPARING_NO_TRANSPORT_DISPATCH',
                'invocations':[],'cases':[],'camera_validity_claimed':False,
                'semantic_eligibility_claimed':False,'failure':str(error)})
            return 7
    raise AssertionError('payload boundary did not refuse')


def controls():
    root=Path(tempfile.mkdtemp(prefix='ucr-life-',dir='/private/tmp'))
    records=[]
    for count in (8,7):
        workspace=root/str(count);workspace.mkdir(mode=0o700)
        source=workspace/'original-tiny';source.write_bytes(b'four');source.chmod(0o400)
        plan={'workspace':str(workspace),'source':{'path':str(source),
                    'identity':clone.stamp(source.lstat())}}
        plan_path=workspace/'plan.json';plan_path.write_text(json.dumps(plan))
        digest=hashlib.sha256(plan_path.read_bytes()).hexdigest()
        planned=argv(plan_path,digest,workspace)
        assert planned[1:][3]==str(plan_path) and planned[1:][5]==digest
        assert planned[1:][7]==str(workspace) # Python argv excludes interpreter.
        for name in ('cpu','io'):(workspace/name).mkdir(mode=0o700)
        cpu,io=Lease(workspace/'cpu',count),Lease(workspace/'io',1)
        class CPU:
            def try_acquire(self,indexes):return cpu
        class IO:
            def try_acquire(self):return io
        io_pool=IO()
        with patch.object(dispatch.Pool,'read',return_value=CPU()), \
             patch.object(dispatch,'checked_io_request',return_value=(io_pool,execute.time.time()+60)):
            code=dispatch.run('camera-receive',planned,workspace,8,
                              io_admission={'path':'/disposable-only','sha256':'0'*64})
        assert code==7 and cpu.closed and io.closed
        closed=json.loads((workspace/'SHARED-CLOSED.json').read_text())
        assert closed['child']['returncode']==7 and closed['child']['reaped']
        assert closed['child']['other_group_members_absent_before_reap']
        started=(workspace/'EXECUTOR-START.json').exists()
        assert started==(count==8)
        result=json.loads((workspace/'RESULT.json').read_text())
        if count==8:assert result['failure']=='original pre-payload fixture refusal'
        else:assert 'nine inherited' in result['failure']
        proof=json.loads((workspace/'SHARED-SERVER-AUDIT.json').read_text())
        assert proof['attempted_cli_invocations']==0 and proof['functional_status']=='FAILED'
        records.append({'workspace':str(workspace),'cpu_descriptors':count,
                        'entry_binding_passed':started,'actual_child':closed['child'],
                        'disposable_grants_closed':True,'result_audit':proof})
    print(json.dumps({'workspace':str(root),'cases':records,
                      'scope':'actual Python children/inherited FD checks/reap; disposable inner grants/tiny data only'}))


if __name__=='__main__':
    if sys.argv[1:2]==['--worker']:
        raise SystemExit(child())
    if sys.argv[1:]==['--controls']:
        controls();raise SystemExit(0)
    if len(sys.argv)!=1:raise ValueError('fixed controls only')
    os.umask(0o077)
    output=Path(tempfile.mkdtemp(prefix='unison-camera-binding-lifecycle-'))
    print('Outer owner workspace: '+str(output),flush=True)
    raise SystemExit(dispatch.run('shared-io-controls',[sys.executable,str(HERE),'--controls'],output,8))
