"""Original inert declaration tests; no actual metadata read or execution grant."""
import copy,unittest
from sdk_merge_receiving.admission_test import fixture as merge_fixture
from sdk_negative_receiving import admission as A
from sdk_negative_receiving.plan import LIMITS

EXECUTION=['tests/sdk_negative_receiving/entry.py']
PRODUCTION=['src/semanticRuntime.ml','src/semanticWorkers.ml']

def fixture():
    packet,grant,request,plan,_=merge_fixture()
    packet['schema']='unison-current-sdk-negative-receiving-execution/1'
    packet['workspace']='/private/tmp/u-snr-'+'a'*16;packet['limits']=copy.deepcopy(LIMITS)
    packet['execution_sha256']={'tests/sdk_negative_receiving/entry.py':'5'*64}
    grant.update(schema='unison-current-sdk-negative-receiving-admission/1',
        state='ROOT_ADMITTED_ONE_CURRENT_SDK_NEGATIVE_RECEIVING',workspace=packet['workspace'],
        limits=copy.deepcopy(LIMITS),execution_sha256=copy.deepcopy(packet['execution_sha256']))
    command=A.worker_command(packet,plan);grant['command']=command
    return packet,grant,request,plan,command


class Admission(unittest.TestCase):
    def test_exact_source_bound_negative_contract_and_fresh_inert_admission(self):
        packet,grant,request,plan,command=fixture()
        result=A.validate(packet,execution_sources=packet['execution_sha256'],
            production_sources=packet['production_sha256'],expected_uid=501)
        self.assertEqual(len(result['rows']),12)
        self.assertEqual(A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=199),tuple(range(8)))
        self.assertIn('/tests/sdk_negative_receiving/entry.py',command[1])
    def test_old_merge_grant_deadline_and_changed_limits_sources_refuse(self):
        for kind in ('old','expired','command','limits','source','credits'):
            packet,grant,request,plan,command=fixture()
            if kind=='old':grant['state']='ROOT_ADMITTED_ONE_CURRENT_SDK_MERGE'
            if kind=='expired':grant['start_deadline_unix']=199
            if kind=='command':grant['command']=['/different']
            if kind=='limits':grant['limits']['sdk_calls']=7
            if kind=='source':grant['execution_sha256']={}
            if kind=='credits':grant['cpu_token_indexes']=list(range(18))
            with self.subTest(kind=kind),self.assertRaises(ValueError):A.check(grant,packet,request_ref=request,plan_ref=plan,command=command,now=199)

if __name__=='__main__':unittest.main()
