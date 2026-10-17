"""Original fabricated metadata controls; no RPC, pool lock or media."""
from copy import deepcopy
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote import readback
from component_remote.readback import compare
from component_remote.contract import PARAMETERS
from component_remote import io

def fixture(passed=True):
    plan={'schema':'unison-component-remote/1','parameters':deepcopy(PARAMETERS),'workspace':'/fixed/private'}
    admission={'state':'ROOT_ADMITTED_ONE_COMPONENT_RPC_JOB','plan_sha256':'P','workspace':plan['workspace']}
    ids=[(1,i) for i in range(9)]
    inherited=[{'fd':10+i,'device':d,'inode':n} for i,(d,n) in enumerate(ids)]
    calls=[{'index':i,'no_dispatch':False,'server_not_created':False,
      'client_pid':100+3*i,'supervisor_pid':101+3*i,'server_pid':102+3*i} for i in range(8 if passed else 1)]
    records={'ATTEMPT':{'owner_pid':50,'admission_sha256':'A'},
      'START':{'owner_pid':50,'worker_pid':51,'admission_sha256':'A','cpu_indexes':list(range(8)),
        'io_mode':'EX_GLOBAL','inherited_fds':inherited},
      'WORKER-PACKET':{'parent_pid':50,'plan':plan,'inherited_fds':deepcopy(inherited)},
      'WORKER-RESULT':{'complete':passed,'cases':[{} for _ in range(8 if passed else 0)]},
      'REMOTE-SETTLED':{'worker_finished_starting_calls':True,'calls':calls,'functional_pass':passed},
      'AGGREGATE-CLOSED':{'worker':{'pid':51,'returncode':0 if passed else 1,'reaped':True,
         'other_group_members_absent_before_reap':True,'timed_out':False},'calls':calls,
         'cpu_closed':True,'io_closed':True,'functional_pass':passed}}
    return plan,admission,records,calls,ids

class Controls(unittest.TestCase):
    def check(self,data):
        plan,admission,records,calls,ids=data
        return compare(plan,'P',admission,'A',records,calls,ids)
    def test_metadata_pass_never_authenticates_parent_or_inputs(self):
        value=self.check(fixture())
        self.assertTrue(value['functional_pass_reported'])
        for key in ('parent_terminal_authenticated','resource_release_authorized','functional_inputs_independently_rehashed'):
            self.assertIs(value[key],False)
    def test_failed_prefix_remains_failure(self):
        value=self.check(fixture(False))
        self.assertFalse(value['functional_pass_reported']);self.assertEqual(value['attempted_case_records'],1)
    def test_owner_worker_admission_and_packet_substitution_refused(self):
        for mutate in (lambda r:r['ATTEMPT'].update(owner_pid=70),
          lambda r:r['WORKER-PACKET'].update(parent_pid=70),
          lambda r:r['START'].update(admission_sha256='OTHER'),
          lambda r:r['AGGREGATE-CLOSED']['worker'].update(pid=60)):
            data=fixture();mutate(data[2])
            with self.assertRaises(ValueError):self.check(data)
    def test_wrong_range_duplicate_FD_or_canonical_identity_refused(self):
        for mutate in (lambda r:r['START'].update(cpu_indexes=list(range(8,16))),
          lambda r:r['START']['inherited_fds'][1].update(fd=10),
          lambda r:r['START']['inherited_fds'][0].update(inode=999)):
            data=fixture();mutate(data[2])
            with self.assertRaises(ValueError):self.check(data)
    def test_missing_closure_or_unproved_worker_is_not_release(self):
        for mutate in (lambda r:r['AGGREGATE-CLOSED'].update(io_closed=False),
          lambda r:r['AGGREGATE-CLOSED']['worker'].update(reaped=False),
          lambda r:r['AGGREGATE-CLOSED']['worker'].update(timed_out=True),
          lambda r:r['REMOTE-SETTLED'].update(calls=[])):
            data=fixture();mutate(data[2])
            with self.assertRaises(ValueError):self.check(data)
    def test_incomplete_eight_case_pass_and_ancestor_alias_refused(self):
        data=fixture();data[2]['WORKER-RESULT']['cases'].pop()
        with self.assertRaises(ValueError):self.check(data)
        data=fixture();data[3][0]['client_pid']=50
        with self.assertRaises(ValueError):self.check(data)

    def test_metadata_reader_reparses_saved_proxy_and_reports_no_parent_authority(self):
        from component_remote.controls import outcome,record,plan as artifact_plan
        with tempfile.TemporaryDirectory(prefix='u-cr-',dir='/private/tmp') as raw:
            # Production uses a hex nonce. Mock only namespace matching and the
            # canonical metadata IDs, never the saved intent/proxy auditing.
            work=Path(raw);plan,admission,records,_,ids=fixture()
            plan.update(artifact_plan(work));admission['workspace']=str(work)
            records['WORKER-PACKET']['plan']=plan
            for index in range(8):record(plan,index,outcome(plan,index))
            rows=readback.audit_prefix(plan,work)
            records['AGGREGATE-CLOSED']['calls']=records['REMOTE-SETTLED']['calls']=rows
            plan_path=work/'plan.json';io.save(plan_path,plan);plan_sha=io.sha(plan_path)
            admission['plan_sha256']=plan_sha;admission_path=work/'admission.json';io.save(admission_path,admission)
            admission_sha=io.sha(admission_path)
            records['ATTEMPT']['admission_sha256']=records['START']['admission_sha256']=admission_sha
            for key,value in records.items():io.save(work/(key+'.json'),value)
            with patch.object(readback.re,'fullmatch',return_value=True),\
                 patch.object(readback,'inherited_identities',return_value=ids):
                value=readback.inspect(plan_path,plan_sha,admission_path,admission_sha)
                self.assertEqual(value['attempted_case_records'],8)
                self.assertFalse(value['parent_terminal_authenticated'])
                # An authentic-looking aggregate never replaces missing raw evidence.
                (work/'0/proxy.json').unlink()
                with self.assertRaises((ValueError,FileNotFoundError)):
                    readback.inspect(plan_path,plan_sha,admission_path,admission_sha)

    def test_wrong_plan_pin_refuses_before_any_case_or_canonical_read(self):
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'plan.json';io.save(path,{'workspace':'/not-used'})
            with patch.object(readback,'audit_prefix') as prefix,\
                 patch.object(readback,'inherited_identities') as canonical:
                with self.assertRaises(ValueError):readback.inspect(path,'wrong','/unused','unused')
                prefix.assert_not_called();canonical.assert_not_called()

if __name__=='__main__':unittest.main()
