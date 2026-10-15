#!/usr/bin/env python3
"""Pure admission binding refusals; never dispatch a validator or CLI."""
import argparse
import copy
from pathlib import Path
import time
import run_live_merge as runner

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared', type=Path, required=True)
a = p.parse_args()
workspace = Path('/private/tmp/UNSTARTED-live-merge-admission-fixture')
command = ['python', 'fixture-only-no-dispatch']
admission = {'state':'ROOT_ADMITTED_FINITE_UNISON_LIVE_MERGE_V1',
             'prepared':runner.prep.pin(a.prepared), 'command':command,
             'workspace':str(workspace),'source_pins':runner.sources(),
             'limits':runner.LIMITS,'startDeadlineUnix':time.time()+300}
runner.check_admission(admission,a.prepared,command,workspace)
changes = [('state','old-consumed-slot'),('command',['different']),('workspace',str(workspace)+'-other'),
           ('source_pins',{}),('limits',dict(runner.LIMITS,sdk_calls=7)),
           ('startDeadlineUnix',0),('prepared',dict(admission['prepared'],sha256='0'*64))]
for key,value in changes:
    candidate=copy.deepcopy(admission);candidate[key]=value
    try:
        runner.check_admission(candidate,a.prepared,command,workspace)
    except ValueError:
        pass
    else:
        raise AssertionError('unbound admission accepted: '+key)
assert not workspace.exists()
print('PASS exact binding and seven admission refusals; no dispatch/workspace created')
