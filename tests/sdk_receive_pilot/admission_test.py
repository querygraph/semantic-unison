#!/usr/bin/env python3
"""Pure admission checks, no process/tool execution or SDK access."""
import copy,importlib.util,json,pathlib,tempfile,time
root=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('pilot',root/'tests/sdk_receive_pilot/run.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
w=pathlib.Path(tempfile.mkdtemp(prefix='unison-receive-admission-',dir='/private/tmp'))
blob=w/'original';blob.write_text('original finite admission bytes')
packet={'mode':'prepare','source_pins':{'tests/sdk_receive_pilot/run.py':m.sha(root/'tests/sdk_receive_pilot/run.py')},'builds':{'stock':{'binary':str(blob),'sha256':m.sha(blob)}},'fixtures':[{'original':str(blob),'original_sha256':m.sha(blob),'edited':str(blob),'edited_sha256':m.sha(blob)}],'bad_digest':{'path':str(blob),'sha256':m.sha(blob)},'driver_manifest':{'executable':str(blob),'executable_sha256':m.sha(blob)}}
m.write(w/'READY.json',packet);request=w/'request.json';m.write(request,{'prepared':{'path':str(w/'READY.json'),'sha256':m.sha(w/'READY.json')}})
a={'state':'ROOT_ADMITTED_FINITE_UNISON_RECEIVE_PILOT_V1','startDeadlineUnix':time.time()+60,'command':['synthetic-only'],'limits':{'SDK_calls_maximum':10,'generated_inputs_maximum':7,'logical_states_maximum':16,'active_CPU_credits':8,'aggregate_native_wall_seconds':300},'request':{'path':str(request),'sha256':m.sha(request)}}
def verify(p,a):m.check_admission(p,w,a,request,['synthetic-only'])
verify(packet,a)
mutations=[('old release',lambda p,a:a.update(state='ROOT_ADMITTED_SEPARATE_FINITE_PUBLIC_SDK_PILOT_V2')),('expired',lambda p,a:a.update(startDeadlineUnix=0)),('wrong command',lambda p,a:a.update(command=['different'])),('wrong limits',lambda p,a:a['limits'].update(SDK_calls_maximum=11)),('request pin',lambda p,a:a['request'].update(sha256='0'*64)),('source changed',lambda p,a:p['source_pins'].update({'tests/sdk_receive_pilot/run.py':'0'*64})),('CLI changed',lambda p,a:p['builds']['stock'].update(sha256='0'*64)),('input changed',lambda p,a:p['bad_digest'].update(sha256='0'*64))]
for name,mutate in mutations:
 p,b=copy.deepcopy(packet),copy.deepcopy(a);mutate(p,b)
 try:verify(p,b)
 except RuntimeError:pass
 else:raise RuntimeError('admission bypassed: '+name)
(w/'START.json').write_text('consumed')
try:verify(packet,a)
except RuntimeError:pass
else:raise RuntimeError('consumed slot accepted')
r={'scope':'pure admission checks; zero SDK/process invocations','workspace':str(w),'positive':1,'denials':9,'runner_sha256':m.sha(root/'tests/sdk_receive_pilot/run.py')}
m.write(w/'RESULT.json',r);print(json.dumps(r))
