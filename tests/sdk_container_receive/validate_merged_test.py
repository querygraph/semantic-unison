#!/usr/bin/env python3
"""Original fake-tool executor and admission controls; never execute Adobe."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import prepare_merged as prep
import validate_merged as runner

work = Path(tempfile.mkdtemp(prefix='unison-merged-executor-')).resolve()
tool = work / 'fake-validator'
tool.write_text('''#!/usr/bin/env python3
import os,sys
args=sys.argv
sha=args[args.index('--expected-sha256')+1]
size=args[args.index('--expected-size')+1]
fault=os.environ.get('MERGED_TEST_FAULT','')
if fault=='exit':sys.exit(7)
if fault=='digest':sha='0'*64
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+sha)
print('candidate-size '+size)
print('driver-build MOCK-merged')
print('structure valid\\ndecode success\\nraw-digest valid\\nerrors 0')
print('warnings '+('5' if fault=='warnings' else '4'))
if fault!='truncated':print('END')
''')
tool.chmod(0o700)
packet={'schema':'unison-merged-output-sdk-preparation/1','runtime_admitted':False,
        'proposed_limits':runner.LIMITS,'preparer':prep.pin(prep.__file__),
        'tool_manifest_reader':prep.pin(runner.host.__file__),
        'tool':{'executable':str(tool),'sha256':prep.pin(tool)['sha256'],
                'build_id':'MOCK-merged'},'cases':[]}
for codec in prep.CODECS:
    candidate=work/(codec+'.dng');candidate.write_bytes(('synthetic '+codec).encode())
    pin=prep.pin(candidate)
    packet['cases'].append({'codec':codec,'candidate':pin,'command':[str(tool),
        '--unison-dng-validation-v1','--expected-sha256',pin['sha256'],
        '--expected-size',str(pin['bytes']),'--threads','1','--',str(candidate)]})
prepared=work/'PREPARED.json';prepared.write_text(json.dumps(packet))
records=[]
for fault in ('','digest','warnings','truncated','exit'):
    output=work/('run-'+(fault or 'positive'))
    command=[sys.executable,str(Path(runner.__file__).resolve()),'--prepared',str(prepared),
             '--workspace',str(output),'--mode','mock']
    result=subprocess.run(command,env={**os.environ,'MERGED_TEST_FAULT':fault},
                          capture_output=True,text=True,timeout=45)
    assert (result.returncode==0)==(not fault),(fault,result.stderr)
    closure=json.loads((output/'AGGREGATE-CLOSED.json').read_text())
    assert closure['closed'] and closure['reaped'] and closure['other_members_absent']
    assert not (output/'AGGREGATE-OWNERSHIP-UNRESOLVED.json').exists()
    assert len(list(output.glob('ENTRY-*.json')))==(1 if fault else 3)
    assert (output/'RESULT.json').exists()==(not fault)
    records.append({'fault':fault or 'none','command':command,'exit':result.returncode,
                    'stdout':result.stdout,'stderr':result.stderr,'closure':closure})
# A consumed workspace cannot dispatch another call, even after success.
positive=work/'run-positive'
entries={p.name:prep.pin(p) for p in positive.glob('ENTRY-*.json')}
replay=subprocess.run(records[0]['command'],capture_output=True,text=True,timeout=10)
assert replay.returncode!=0 and 'FileExistsError' in replay.stderr
assert entries=={p.name:prep.pin(p) for p in positive.glob('ENTRY-*.json')}
# Mock mode cannot smuggle a production executable identity.
forged=copy.deepcopy(packet);forged['tool']['build_id']='unison-sdk171-2724-v1-single'
try:runner.validate(forged,'mock')
except ValueError:pass
else:raise AssertionError('native identity accepted in mock mode')
# Canonical argv must fail before acquiring a workspace.
bad=copy.deepcopy(packet);bad['cases'][0]['command'].append('--unexpected')
wrong=work/'wrong.json';wrong.write_text(json.dumps(bad));output=work/'wrong-output'
result=subprocess.run([sys.executable,str(Path(runner.__file__).resolve()),'--prepared',str(wrong),
                      '--workspace',str(output),'--mode','mock'],capture_output=True,text=True,timeout=10)
assert result.returncode!=0 and not output.exists()
# Native admission tests are pure calls and cannot execute the fake tool.
command=['python','example'];admission={'state':'ROOT_ADMITTED_FINITE_UNISON_MERGED_OUTPUT_V1',
 'prepared':prep.pin(prepared),'command':command,'limits':runner.LIMITS,
 'source_pins':runner.source_pins(),'startDeadlineUnix':time.time()+60}
runner.admission_check(admission,prepared,command)
for key,value in [('state','ROOT_ADMITTED_FINITE_UNISON_HOST_MATRIX_V1'),
                  ('command',command+['wrong']),('limits',{}),('source_pins',{}),
                  ('prepared',{}),('startDeadlineUnix',0)]:
    bad=copy.deepcopy(admission);bad[key]=value
    try:runner.admission_check(bad,prepared,command)
    except ValueError:pass
    else:raise AssertionError(key)
result={'schema':'unison-merged-executor-fake-qualification/1','workspace':str(work),
 'records':records,'canonical_argv_refused_before_acquisition':True,'consumed_workspace_refused':True,
 'mock_refuses_native_identity':True,
 'pure_admission_controls':7,'sdk_executions':0,
 'sources':[prep.pin(p) for p in (prep.__file__,runner.__file__,__file__)],
 'scope':'Fake validator success/zero-exit bad receipt/nonzero exit and genuine aggregate closure only; no SDK runtime admission.'}
(work/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS fake executor/admission controls:',work/'RESULT.json')
