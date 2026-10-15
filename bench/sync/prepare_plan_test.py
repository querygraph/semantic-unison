#!/usr/bin/env python3
"""Pure build-pin and measurement-plan controls; no compiler/binary invocation."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import prepare_plan as planner

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stock-build',type=Path,required=True)
p.add_argument('--ox-build',type=Path,required=True)
a=p.parse_args()
work=Path(tempfile.mkdtemp(prefix='unison-sync-plan-control-'))
plan=planner.prepare(a.stock_build,a.ox_build,work/'NOT-CREATED')
assert len(plan['commands'])==4 and not plan['runtime_started'] and not plan['cpu_reservation']
assert plan['configured_endpoint_worker_maximum']==16 <= plan['proposed_cpu_credits']==18
for row in plan['commands']:
    assert row['measured_updates']==18*5 and row['expected_cli_invocations']==(18+90)*3
    assert '--measure-primary-reads' not in row['command'] and '--qualification' not in row['command']
assert not (work/'NOT-CREATED').exists()
original=json.loads(a.stock_build.read_text())
for name in ('incomplete','changed-binary','missing-worker-pins'):
    changed=copy.deepcopy(original)
    if name=='incomplete':changed['complete']=False
    elif name=='changed-binary':changed['binary_sha256']='0'*64
    else:changed['source_sha256'].pop('src/semanticWorkers.ml')
    path=work/(name+'.json');path.write_text(json.dumps(changed))
    try:
        planner.prepare(path,a.ox_build,work/'NOT-CREATED')
    except ValueError:
        pass
    else:
        raise AssertionError('invalid build accepted: '+name)
print('PASS four bounded warm batches, worker/sample accounting and three invalid-build refusals; no command executed')
