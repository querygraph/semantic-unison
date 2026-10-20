"""Postclosure raw/source/metadata replay, never reopen DNG or executable bytes."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix'),str(ROOT/'bench/sync')]
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.data import stamp
from sdk_merge_receiving.evidence import child
from sdk_negative_receiving.plan import schedule
from sdk_negative_receiving.parent import audit as replay
from sdk_negative_receiving.runtime import key,proxy_command
from sdk_negative_receiving.publication import verify
from shared_cpu_pool import Pool
from shared_io_pool import close_unstarted


def document(path):
    from sdk_merge_receiving.metadata import document as parse
    return parse(read_bytes(str(path),2*1048576))
def sha(path):return hashlib.sha256(read_bytes(str(path),16*1048576)).hexdigest()


def main():
    cpu=Pool.read(str(ROOT.parent/'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'),
        '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd').try_acquire((0,))
    if cpu is None:raise ValueError('CPU00 busy')
    try:
        seal=document(ROOT/'tests/qualification/sdk-negative03-native-actual-20261019.json')
        assert seal['state']=='PASS_ACTUAL_CLOSED' and seal['CPU00_07_closed'] and seal['EX_global_closed']
        for ref in seal['references']:
            raw=read_bytes(ref['path'],2*1048576)
            assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
        plan=ROOT/'doc/current-sdk-negative-native-20261019-03/PLAN.json'
        assert sha(plan)=='796e788f3efb46935e015f7effc5670731fc04eed37e4de8b966973f94cbde62'
        p=document(plan);work=Path(p['workspace'])
        for name,digest in {**p['execution_sha256'],**p['production_sha256']}.items():assert sha(ROOT/name)==digest,name
        for name,digest in p['prerequisite_sha256'].items():assert sha(name)==digest,name
        for name,epoch in p['source_observations'].items():assert stamp(os.lstat(name))==epoch
        start=document(work/'OWNER-START.json');owner=document(work/'OWNER-AUDIT.json');saved=document(work/'WORKER-RESULT.json')
        assert child(owner['outcome'],start['command'])==16122==seal['terminal']['worker_pid']
        assert exact(document(work/'OWNER-TOOL-TERMINAL.json'),seal['terminal']) and seal['terminal']['exit_code']==0 and seal['terminal']['running_session_returned'] is False
        rows=schedule(p['binaries'],p['tool'],p['workspace'])['rows'];previous={};decisions=[]
        def output(row,candidate):
            index=rows.index(row);name=key(row);group=(row['codec'],row['policy'])
            before,after=saved['data_history'][index*2:index*2+2]
            ref=saved['output_pins'][name];raw=read_bytes(str(work/ref['name']),2*1048576)
            assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'] and exact(json.loads(raw),after)
            assert all(v[k]==row[k] for v in (before,after) for k in ('codec','policy','stage'))
            assert before['event']=='PREPARED' and after['event']=='VERIFIED' and exact(before['candidate'],candidate)
            outputs=after['outputs'];assert set(outputs)=={'left','right'}
            if row['stage']=='seed':
                case=next(c for c in p['cases'] if c['codec']==row['codec']);base=case['states']['base']
                assert candidate=={k:base[k] for k in ('sha256','bytes')}
                assert all(value['sha256']==base['sha256'] and value['bytes']==base['bytes'] for value in outputs.values())
                publication=dict(seed_exact=True,resource_release_authorized=False)
            else:
                assert exact(before['fault']['before'],previous[group]['left']) and exact(before['fault']['after'],outputs['left'])
                assert outputs['left']['sha256']==candidate['sha256']
                publication=verify(policy=row['policy'],before=previous[group]['right'],after=outputs['right'],candidate=candidate)
                for side,value in outputs.items():assert stamp(os.lstat(Path(row['directory'])/side/'image.dng'))==value['identity']
                decisions.append(dict(codec=row['codec'],policy=row['policy'],publication=publication))
            assert exact(publication,after['publication']);previous[group]=outputs
            return publication
        verdict=replay(p,dict(result=saved['result'],pair_pins=saved['pair_pins']),
            read_pinned=lambda pin:read_bytes(str(work/pin['name']),2*1048576),
            proxy_command=lambda row:proxy_command(p,row),verify_outputs=output)
        assert verdict['cli_calls']==12 and verdict['SDK_helpers']==6 and len(decisions)==6
        reports=[entry['transport']['call']['finding']['report'] for entry in saved['result']['results'] if entry['stage']=='negative']
        assert all(r['raw-digest']=='mismatch' and r['errors']=='1' and r['warnings']=='4' for r in reports)
        result=dict(schema='unison-negative03-saved-actual-audit/1',actual_owner=seal['terminal'],
            production_pins_verified=329,execution_pins_verified=176,JSON_prerequisites_verified=13,
            retained_input_epochs_unchanged=12,current_private_output_metadata_fences=12,
            raw_replay=verdict,decisions=decisions,SDK_findings=reports,
            actual_parent_fresh_output_hashes_adopted=True,fresh_payload_or_executable_opened=False,
            new_CLI_or_SDK_calls=0,EX_acquired=False,scope='Generated3codecs require preservation/warn exact publication with genuine negative SDK findings; not camera/pixels/corpus/performance/production')
    finally:
        if not cpu.closed:close_unstarted(cpu)
    result['CPU00_closed']=True;print(json.dumps(result,indent=2))
if __name__=='__main__':main()
