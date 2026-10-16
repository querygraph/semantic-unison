import copy
from pathlib import Path
import unittest
import synthetic_case_test as fixtures
from unittest.mock import patch
import result_audit as a
from synthetic_case import BUILD
class ParentAudit(unittest.TestCase):
    def plan(self):return dict(workspace='/private/tmp/u-concurrent',tool=dict(build_id=BUILD))
    def result(self):return dict(schema='unison-concurrent-synthetic-worker/1',complete=False,
        phase='PREPARING_NO_CALL',sdk_validation_claimed=False,semantic_eligibility_claimed=False,
        invocations=[],cases=[],failure='original preparation refusal')
    def positive(self):
        plan=self.plan();plan['tool'].update(path='/inert/synthetic-validator',sha256='c'*64,threads=1)
        plan['binaries']={label:dict(label=label,path='/inert/'+label,sha256='a'*64) for label in ['stock','ox']}
        result=dict(self.result(),complete=True,phase='FINISHED');result.pop('failure')
        for index,label in enumerate(['stock','ox']):
            fixture=fixtures.Cases();fixture.setUp()
            try:case=fixture.run_case(fixture.outcome)
            finally:fixture.tearDown()
            command=a.command(Path(plan['workspace'])/label,binary=plan['binaries'][label],tool=plan['tool'])['argv']
            outcome=case['outcome'];outcome['command']=command
            owner=dict(pid=11+index,returncode=0,reaped=True,group_cleanup_before_leader_reap=True,
                       other_group_members_absent_before_reap=True)
            outcome.update(client_cleanup=owner,supervisor_cleanup=dict(owner,pid=15+index))
            outcome['proxy'].update(schema='unison-loopback-protocol-count/1',server_returncode=0,
                server_command=[command[0],'-server'],server_cleanup=dict(owner,pid=31),
                input_pump_joined=True,pump_errors=[])
            result['cases'].append(dict(label=label,case=case))
            result['invocations'].append(dict(index=index,state='OUTCOME',
                identity=dict(label=label,mode='semantic',workers=3,directory=plan['workspace']+'/'+label,stage='seed'),
                command=command,outcome=outcome))
        return result,plan
    def test_two_complete_cases_use_real_pure_auditors(self):
        result,plan=self.positive();proof=a.audit(result,plan,plan['workspace'])
        self.assertEqual(proof['functional_status'],'PASSED')
        self.assertEqual(len(proof['helper_settlements']),4)
        self.assertTrue(proof['all_pairs_overlap']);self.assertFalse(proof['aggregate_parent_fd_closure_proved'])
    def test_case_outcome_and_sources_cannot_be_forged(self):
        result,plan=self.positive()
        for field,value in [('complete',False),('sources',[]),('validation',{})]:
            changed=copy.deepcopy(result);changed['cases'][0]['case'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):a.audit(changed,plan,plan['workspace'])
    def test_unknown_group_or_pump_error_cannot_pass(self):
        for mutate in ['group','pump']:
            result,plan=self.positive();outcome=result['invocations'][0]['outcome']
            if mutate=='group':outcome['stdout']=outcome['stdout'].replace('other-members=0','other-members=unknown',1)
            else:outcome['proxy']['pump_errors']=['injected pump failure']
            with self.assertRaises(ValueError):a.audit(result,plan,plan['workspace'])
    def test_known_failed_prefix_remains_failure_with_helper_settlement(self):
        result,plan=self.positive();result.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='original failed call')
        result['invocations']=result['invocations'][:1];result['cases']=result['cases'][:1]
        outcome=result['invocations'][0]['outcome'];outcome['returncode']=1;outcome['client_cleanup']['returncode']=1
        proof=a.audit(result,plan,plan['workspace'])
        self.assertEqual(proof['functional_status'],'FAILED')
        self.assertEqual(len(proof['helper_settlements']),2)
        self.assertFalse(proof['all_pairs_overlap'])
    def test_order_and_command_are_exact(self):
        result,plan=self.positive()
        for mutate in ['order','command']:
            changed=copy.deepcopy(result)
            if mutate=='order':changed['invocations'].reverse()
            else:changed['invocations'][0]['command'].append('-force')
            with self.assertRaises(ValueError):a.audit(changed,plan,plan['workspace'])
    def test_zero_call_known_preparation(self):
        with patch.object(a,'audit_attempted') as external:
            proof=a.audit(self.result(),self.plan(),'/private/tmp/u-concurrent')
        external.assert_not_called();self.assertEqual(proof['attempted_cli_invocations'],0)
    def test_zero_call_cannot_cover_possible_dispatch(self):
        for change in [dict(phase='CALL_MAY_HAVE_STARTED'),dict(complete=True),dict(failure=''),dict(sdk_validation_claimed=True)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                a.audit(dict(self.result(),**change),self.plan(),'/private/tmp/u-concurrent')
    def test_reject_mistyped_complete_or_wrong_scope(self):
        for change in [dict(complete=0),dict(schema='other'),dict(invocations=[{}]*3)]:
            with self.assertRaises(ValueError):a.audit(dict(self.result(),**change),self.plan(),'/private/tmp/u-concurrent')
    def test_prefix_cannot_skip_independent_call_settlement(self):
        result=dict(self.result(),invocations=[{}])
        with patch.object(a,'audit_attempted',side_effect=ValueError('unknown actual call')) as external:
            with self.assertRaisesRegex(ValueError,'unknown actual call'):
                a.audit(result,self.plan(),'/private/tmp/u-concurrent')
        external.assert_called_once_with(result)
    def test_namespace_and_tool_fences(self):
        for plan in [dict(self.plan(),workspace='/wrong'),dict(self.plan(),tool=dict(build_id='real-sdk'))]:
            with self.assertRaises(ValueError):a.audit(self.result(),plan,'/private/tmp/u-concurrent')
if __name__=='__main__':unittest.main()
