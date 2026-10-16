"""Reparse retained native host-matrix receipts only; never read SDK/input binaries."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests/sdk_host_matrix'))
import plan

def pin(path):
    raw=Path(path).read_bytes();return dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def checked(record):
    assert pin(record['path'])==record,record['path']
    return json.loads(Path(record['path']).read_text())
def run(output):
    source=ROOT/'tests/qualification/sdk-host-matrix-v1-actual-return-20261014.json';d=json.loads(source.read_text())
    prior=checked(d['plan']);native=checked(d['result']['pin']);terminal=checked(d['parent_terminal']);aggregate=checked(d['aggregate']['pin'])
    assert terminal['actual_tool_exit_code']==0 and terminal['running_session_returned'] is False
    assert aggregate['reaped'] and aggregate['returncode']==0 and aggregate['other_members_absent']
    refs={};verified=[]
    for row,case,saved in zip(d['raw_calls'],prior['cases'],native['results']):
        entry=checked(row['entry']);call=checked(row['call']);assert entry['case']==case
        assert call['stdout']==row['actual_stdout'] and call['stderr']==row['actual_stderr']
        assert call['returncode']==0 and call['timed_out'] is False and call['capture_truncated'] is False
        assert call['client_cleanup']['reaped'] and call['client_cleanup']['returncode']==0
        value=plan.receipt(call['stdout'],case)
        if case['backend']=='reference':refs[case['codec']]=value
        assert value==refs[case['codec']]==saved['receipt']
        observations=plan.telemetry(call['stderr'],case,prior['host_memory_bytes']) if case['backend']=='experimental' else None
        assert observations==saved['observations']
        verified.extend([row['entry'],row['call']])
    assert len(d['raw_calls'])==len(prior['cases'])==len(native['results'])==12
    new=json.loads((ROOT/'doc/shared-sdk-host-plan-v1.json').read_text())
    old_tools={(v['path'],v['sha256']) for v in d['post_tools']}
    assert {(v['executable'],v['sha256']) for v in new['tools'].values()}==old_tools
    assert {(f['path'],f['sha256'],f['size']) for f in new['fixtures']}=={(f['path'],f['sha256'],f['bytes']) for f in d['post_inputs']}
    adoption=ROOT/'tests/qualification/sdk-host-matrix-v1-root-adoption-20261014.json';ad=json.loads(adoption.read_text());checked(ad['root_receipt'])
    result=dict(schema='unison-sdk-prior-host-scope-review/1',state='PRIOR_ACTUAL_RECEIPTS_REPARSED_NOT_REEXECUTED',prior_actual_return=pin(source),prior_root_adoption=pin(adoption),prior_parent_terminal=d['parent_terminal'],prior_aggregate=d['aggregate']['pin'],verified_raw_call_pins=verified,
        proposed_plan=pin(ROOT/'doc/shared-sdk-host-plan-v1.json'),planned_tool_and_input_pins_match_prior_verified_artifacts=True,
        prior_native_calls=12,new_sdk_calls=0,new_tool_or_input_payload_hash_reads=0,
        prior_scope='Same pinned reference and experimental tool: three generated codecs, reference1/experimental1,6,18 validation outcomes equal, task/coveredallocator settled; prior actual93165/0ea119/0 and aggregate25466/reaped0.',
        new_request_scope='Fresh proposed shared8 executor/grant/inherited9FD binding and new experimental2-thread case. Existing1/6functional result is not a missing first-use gate. Exact new owner still requires separate admission.',
        limits='No fresh SDK/tool/input execution or fullhash, no currentwholecode snapshot/nativeOSthreads/RSS/pixels/scaling/throughput/production qualification; old18slot consumed, no replay.',full_goal_complete=False)
    with Path(output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print('PASS12 retained native calls reparsed; same planned tool/input SHA pins; zero new SDK/payload reads')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
