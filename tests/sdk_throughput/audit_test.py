import copy
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'sdk_multifile')]
from sdk_throughput.audit import audit
from sdk_throughput.plan import comparison
from sdk_multifile.parent_test import Parent


def fixture(count=24,complete=True):
    old,plan,_=Parent().fixture();plan['workspace']='/private/tmp/u-st-audit';schedule=comparison(plan['binaries'],plan['tool'],plan['workspace'])['rows']
    r=dict(schema='unison-sdk-receiving-comparison-worker/1',complete=complete,phase='FINISHED' if complete else 'CALL_MAY_HAVE_STARTED',
           invocations=[],cases=[],semantic_eligibility_claimed=False,pixel_equivalence_claimed=False,throughput_qualified=False)
    if not complete:r['failure']='original final post-call failure'
    proxies=[]
    for i,row in enumerate(schedule[:count]):
        out=copy.deepcopy(old['invocations'][0]['outcome']);out.update(command=row['command'],wall_seconds=1.+i)
        out['proxy']['server_command']=[row['command'][0],'-server']
        case=copy.deepcopy(old['cases'][0]['case']);case['outcome']=out
        r['cases'].append(dict(schedule=row,case=case));r['invocations'].append(dict(index=i,state='OUTCOME',
            identity=dict(label=row['label'],mode='semantic',workers=row['endpoint_workers'],directory=row['directory'],stage='seed'),command=row['command'],outcome=out))
        proxies.append(copy.deepcopy(out['proxy']))
    return r,plan,proxies


class Audit(unittest.TestCase):
    def test_complete_exact24rows48helper_proof_is_not_resource_or_throughput_authority(self):
        r,p,raw=fixture();a=audit(r,p,raw_proxy_receipts=raw)
        self.assertEqual(a['sdk_helpers_settled'],48);self.assertEqual(a['measured_rows'],20)
        self.assertFalse(a['resource_release_authorized']);self.assertFalse(a['throughput_qualified'])
    def test_known_failed_prefix_does_not_become_success(self):
        r,p,raw=fixture(2,False);a=audit(r,p,raw_proxy_receipts=raw)
        self.assertEqual(a['functional_status'],'FAILED');self.assertEqual(a['attempted_cli_invocations'],2)
        c=r['cases'][-1]['case'];c.update(complete=False,phase='HELPER_SETTLEMENT_RECORDED',failure='original byte mismatch')
        self.assertEqual(audit(r,p,raw_proxy_receipts=raw)['sdk_helpers_settled'],4)
    def test_missing_raw_intent_group_case_or_reordered_rows_refuse(self):
        for mutate in [lambda r:r['cases'][0]['schedule'].update(round=False),lambda r:r['invocations'][-1].update(state='INTENT'),lambda r:r['cases'].pop(),
                       lambda r:r['cases'][0].update(schedule=r['cases'][1]['schedule']),
                       lambda r:r['invocations'][0]['outcome']['supervisor_cleanup'].update(other_group_members_absent_before_reap=False),
                       lambda r:r['cases'][0]['case'].update(complete=False),
                       lambda r:r['invocations'][0]['outcome'].update(wall_seconds=float('nan'))]:
            r,p,raw=fixture();mutate(r)
            with self.assertRaises((ValueError,KeyError)):audit(r,p,raw_proxy_receipts=raw)
        r,p,raw=fixture()
        with self.assertRaises(ValueError):audit(r,p,raw_proxy_receipts=raw[:-1])
    def test_empty_preparation_is_distinct_from_unknown_call(self):
        r,p,raw=fixture(0,False);r['phase']='PREPARING_NO_CALL'
        self.assertEqual(audit(r,p,raw_proxy_receipts=raw)['attempted_cli_invocations'],0)
        r['phase']='CALL_MAY_HAVE_STARTED'
        with self.assertRaises(ValueError):audit(r,p,raw_proxy_receipts=raw)


if __name__=='__main__':unittest.main()
