#!/usr/bin/env python3
"""Pure full-matrix and allocation refusal tests; no child/CLI/SDK."""
import copy
import json
from pathlib import Path
import tempfile
import time

import run_bounded as bounded

root=bounded.ROOT
assert 'bench/sync/phase_stats.py' in bounded.SOURCES
historical=json.loads((root/'bench/sync/results/checked-worker-performance-20261014.json').read_text())
proof=bounded.audit(historical)
assert proof['rows']==72 and proof['cli_invocations']==216
for change in ('incomplete','duplicate','unreaped','server-pid','missing-row'):
    value=copy.deepcopy(historical)
    if change=='incomplete':value['complete']=False
    elif change=='duplicate':value['samples'].append(value['samples'][0])
    elif change=='unreaped':value['samples'][0]['update_sync']['client_cleanup']['reaped']=False
    elif change=='server-pid':value['samples'][0]['update_sync']['proxy']['server_pid']=-1
    else:value['samples'].pop()
    try:bounded.audit(value)
    except ValueError:pass
    else:raise AssertionError('invalid full matrix accepted: '+change)
work=Path(tempfile.mkdtemp(prefix='unison-bounded-source-fixtures-'))
plan=work/'plan.json';plan.write_text('{}')
workspace=work/'NEVER-CREATED'
command=['fixture-not-executable']
allocation={'state':'ROOT_ALLOCATED_FINITE_SYNC_BATCH_V1','plan':bounded.pin(plan),
            'batch_index':0,'workspace':str(workspace),'command':command,'source_pins':bounded.sources(),
            'limits':{'cpu_credits':18,'aggregate_seconds':7200,'cli_invocations':324},
            'startDeadlineUnix':time.time()+300}
bounded.check_allocation(allocation,plan,0,workspace,command)
changes=(('state','old-slot'),('batch_index',1),('workspace',str(workspace)+'-other'),
         ('command',['other']),('source_pins',{}),('startDeadlineUnix',0),
         ('limits',dict(allocation['limits'],cli_invocations=1)))
for key,value in changes:
    changed=copy.deepcopy(allocation);changed[key]=value
    try:bounded.check_allocation(changed,plan,0,workspace,command)
    except ValueError:pass
    else:raise AssertionError('allocation accepted mismatch: '+key)
# Both guard failures occur before fork/readiness/markers, not simulated reaps.
for options in ({'seconds':301},{'maximum_seconds':7201}):
    try:bounded.supervise(lambda _:None,workspace,**options)
    except ValueError:pass
    else:raise AssertionError('aggregate ceiling accepted')
assert not workspace.exists()
print('PASS historical216CLI receipt readback,5matrix+7allocation+2prefork ceiling refusals; no dispatch')
