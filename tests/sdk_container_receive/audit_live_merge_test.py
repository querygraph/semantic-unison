#!/usr/bin/env python3
"""Read-only audit controls over a genuinely closed original mock run."""
import argparse
import copy
import json
import tempfile
from pathlib import Path
import audit_live_merge as audit

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--mock-workspace',type=Path,required=True)
a=p.parse_args()
packet=json.loads((a.mock_workspace/'MOCK-PREPARED.json').read_text())
terminal={'owner_tool':53937,'terminal_chunk':'a3cf4a','exit_code':0,'running_session_returned':False}
proof=audit.audit(packet,a.mock_workspace/'runtime',terminal)
assert proof['complete'] and proof['mode']=='mock' and len(proof['independent_receipts'])==3
for changed_packet, changed_terminal in (
        (packet,dict(terminal,exit_code=1)),
        (packet,dict(terminal,running_session_returned=True)),
        (dict(packet,tool=dict(packet['tool'],build_id='MOCK-wrong')),terminal)):
    try:
        audit.audit(changed_packet,a.mock_workspace/'runtime',changed_terminal)
    except ValueError:
        pass
    else:
        raise AssertionError('mismatched terminal/provenance accepted')
changed=copy.deepcopy(packet)
changed['cases'][0]['states']['target']['sha256']='0'*64
try:
    audit.audit(changed,a.mock_workspace/'runtime',terminal)
except ValueError:
    pass
else:
    raise AssertionError('mismatched target accepted')
print('PASS closed nine-run mock readback and four terminal/provenance refusals; no process/SDK')

# Mutate only owned metadata copies. Retained original logs/output bytes are
# referenced read-only; no original receipt is overwritten.
original=a.mock_workspace/'runtime'
for name in ('duplicate-codec', 'mock-relabeled-native'):
    overlay=Path(tempfile.mkdtemp(prefix='unison-return-audit-overlay-'))
    for item in original.iterdir():
        (overlay/item.name).symlink_to(item, target_is_directory=item.is_dir())
    result=json.loads((original/'RESULT.json').read_text())
    start=json.loads((original/'WRAPPER-START.json').read_text())
    if name=='duplicate-codec':
        result['results'].append(result['results'][0])
    else:
        result['mode']=start['mode']='native'
    for filename,value in (('RESULT.json',result),('WRAPPER-START.json',start)):
        (overlay/filename).unlink()
        (overlay/filename).write_text(json.dumps(value))
    try:
        audit.audit(packet,overlay,terminal)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid retained metadata accepted: '+name)
print('PASS duplicate-codec and native-relabel refusal on disposable metadata overlays')
