"""Postclosure metadata/raw-protocol audit; never open DNG or executable bytes.

This replays the pure transport/helper checks and independently binds exact
source pins, output records, no-op fences and retained input epochs. Fresh output
payload hashes belong to the actual owning parent, not this postclosure audit.
"""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.plan import schedule
from sdk_merge_receiving.evidence import bind,child
from sdk_merge_receiving.helpers import audit as helper_audit
from sdk_merge_receiving.runtime import proxy_command
from sdk_merge_receiving.data import stamp
from final_profile_owner import sha
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted


def document(path,maximum=2*1048576):
    return json.loads(read_bytes(str(path),maximum))


def main():
    cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),
        '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire((0,))
    if cpu is None:raise ValueError('standing CPU00 busy')
    try:
        sealed=document(ROOT/'tests/qualification/current-sdk-merge-native-actual-20261019.json')
        assert sealed['state']=='PASS_ACTUAL_CLOSED' and sealed['cpu_closed'] and sealed['io_closed']
        work=Path(sealed['workspace'])
        for ref in sealed['references']:
            raw=read_bytes(ref['path'],2*1048576)
            assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
        plan=ROOT/'doc/current-sdk-merge-native-20261019-01/PLAN.json'
        assert sha(plan,2*1048576)=='7047511856ed22ea39bd4b7a8b29fb8f10a17900ddd854810f515ec649cf2eb7'
        packet=document(plan);counts={}
        for key in ('execution_sha256','production_sha256'):
            for name,digest in packet[key].items():assert sha(ROOT/name)==digest
            counts[key]=len(packet[key])
        for name,digest in packet['prerequisite_sha256'].items():
            assert sha(name,2*1048576)==digest
        for name,epoch in packet['source_observations'].items():assert stamp(os.lstat(name))==epoch
        start=document(work/'OWNER-START.json');saved=document(work/'WORKER-RESULT.json')
        owner=document(work/'OWNER-AUDIT.json');terminal=document(work/'OWNER-TOOL-TERMINAL.json')
        assert terminal==sealed['terminal'] and terminal['exit_code']==0 and terminal['running_session_returned'] is False
        assert child(owner['outcome'],start['command'])==start['child_pid']==terminal['worker_pid']
        assert start['owner_pid']==terminal['owner_pid'] and start['token_indexes']==list(range(8))
        assert start['io_mode']=='EX_GLOBAL' and len(start['inherited_resource_fds'])==9
        calls=[];reports=[];previous={}
        for index,row in enumerate(schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']):
            key=row['codec']+'-'+row['stage'];pin=saved['pair_pins'][key+'-PAIR.json']
            raw=read_bytes(str(work/pin['name']),2*1048576)
            assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
            record=json.loads(raw)
            assert record['command']==row['command'] and record['identity']==row['identity']
            call=bind(row,record['pair'],expected_proxy_command=proxy_command(packet,row),raw_proxy_bytes=bytes.fromhex(record['raw_proxy_hex']))
            case=next(c for c in packet['cases'] if c['codec']==row['codec'])
            target=case['states']['base' if row['stage']=='seed' else 'target']
            helpers=helper_audit(call['log'],stage=row['stage'],returncode=call['returncode'],candidate_sha256=target['sha256'],candidate_bytes=target['bytes'])
            assert helpers==saved['result']['results'][index]['helpers']
            reports.extend(h['report'] for h in helpers['helpers'])
            verified=saved['data_history'][index*2+1]
            assert verified==document(work/(key+'-OUTPUTS.json'))
            for output in verified['outputs'].values():
                assert output['sha256']==target['sha256'] and output['bytes']==target['bytes']
            if row['stage']=='noop':assert previous[row['codec']]==verified['outputs']
            previous[row['codec']]=verified['outputs']
            calls.append(dict(codec=row['codec'],stage=row['stage'],helpers=helpers['helper_count'],transport_sha256=call['transport_record_sha256']))
        assert len(calls)==9 and len(reports)==6 and reports==owner['audit']['reports']
        assert all(r['raw_digest_verified'] and r['errors']=='0' and r['warnings']=='4' for r in reports)
        result=dict(schema='unison-current-sdk-merge-saved-audit/1',actual_terminal=terminal,
            source_pins_verified=counts,prerequisites_verified=len(packet['prerequisite_sha256']),
            retained_input_epochs_unchanged=len(packet['source_observations']),calls=calls,reports=reports,
            input_or_output_payload_opened=False,execution_artifact_opened=False,EX_acquired=False,
            actual_parent_output_hashes_adopted=True,scope='Generated three-codec scalar merge/off-seed/require-update/noop; no pixels/corpus/performance/production claim')
    finally:
        if not cpu.closed:close_unstarted(cpu)
    result['audit_CPU00_closed']=True
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
