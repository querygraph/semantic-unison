#!/usr/bin/env python3
"""Finite actual original children and self-SIGINT; no benchmark/SDK/Photo."""
import json
import os
from pathlib import Path
import signal
import sys
import tempfile

import measure
import run as sync

work=Path(tempfile.mkdtemp(prefix='unison-interrupted-receipts-'))
print('Workspace:',work,flush=True)
original_group,original_capture=measure.OwnedGroup,measure.CapturedStream
results=[]
for mode in ('sigint-direct','sigint-wrapper','capture-first','capture-second'):
    owners=[]
    class RecordingGroup(original_group):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.interrupt_once=mode.startswith('sigint')
            owners.append(self)
        def await_terminal(self,timeout):
            if self.interrupt_once:
                self.interrupt_once=False
                os.kill(os.getpid(),signal.SIGINT)
            return super().await_terminal(timeout)
    count=[0]
    def capture(*args,**kwargs):
        index=count[0];count[0]+=1
        if (mode=='capture-first' and index==0) or (mode=='capture-second' and index==1):
            raise RuntimeError('original capture setup '+mode)
        return original_capture(*args,**kwargs)
    measure.OwnedGroup,measure.CapturedStream=RecordingGroup,capture
    evidence=None
    try:
        command=[sys.executable,'-c','import time;time.sleep(30)']
        if mode=='sigint-wrapper':
            try:
                sync.measure_invocation(command,{'UNISON_SYNC_BENCH_PROXY_RECEIPT':str(work/'NEVER-RECEIPT')},
                                        3,None,use_proxy=False)
            except sync.InvocationFailure as error:
                evidence=error.outcome
                assert 'KeyboardInterrupt' in evidence['fault']
            else:raise AssertionError('interrupted wrapper accepted')
        else:
            try:
                measure.run(command,os.environ.copy(),3)
            except (KeyboardInterrupt,RuntimeError) as error:
                evidence=error.owned_process_outcome
                assert isinstance(error,KeyboardInterrupt) if mode.startswith('sigint') else 'capture setup' in str(error)
            else:raise AssertionError('expected actual failure absent')
    finally:
        measure.OwnedGroup,measure.CapturedStream=original_group,original_capture
    assert len(owners)==1 and owners[0].reaped
    assert evidence['client_cleanup']['pid']==owners[0].pid and evidence['client_cleanup']['reaped']
    try:os.waitpid(owners[0].pid,os.WNOHANG)
    except ChildProcessError:pass
    else:raise AssertionError('actual child not reaped')
    results.append({'case':mode,'actual_receipt':evidence})
    print('PASS',mode,flush=True)
(work/'RESULT.json').write_text(json.dumps({'complete':True,'cases':results,
    'scope':'four actual original fake-child interruption/capture regressions; no SDK/Photo or timing matrix'},indent=2)+'\n')
print('PASS four actual receipt-retention lifecycle cases; report',work/'RESULT.json')
