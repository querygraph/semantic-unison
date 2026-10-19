"""Pure scheduling/failure-accounting controls, no worker/CLI execution."""
import unittest
from types import SimpleNamespace
from shared_cpu_pool import UnresolvedOwnership
from current_validation_paths.runtime import prefix_settled,case_summary

class Prefix(unittest.TestCase):
    def setUp(self):
        self.actor=SimpleNamespace(retained=None,active=None,calls={1:dict(original='settled raw candidate')},attempts=1)
        self.files=SimpleNamespace(retained=None)
    def test_ordinary_case_assertion_can_be_parent_audited_but_not_unknown(self):
        self.assertTrue(prefix_settled(self.actor,self.files,AssertionError('original generated case failure')))
        self.assertFalse(prefix_settled(self.actor,self.files,UnresolvedOwnership('original uncertainty')))
    def test_one_active_or_unaccepted_attempt_cannot_close_as_failed_prefix(self):
        self.actor.active=dict(original='live call');self.assertFalse(prefix_settled(self.actor,self.files,ValueError()))
        self.actor.active=None;self.actor.attempts=2;self.assertFalse(prefix_settled(self.actor,self.files,ValueError()))
    def test_fd_or_actor_uncertainty_cannot_be_relabelled_ordinary(self):
        self.files.retained=UnresolvedOwnership('uncertain close')
        self.assertFalse(prefix_settled(self.actor,self.files,ValueError()))
        self.files.retained=None;self.actor.retained=UnresolvedOwnership('uncertain actor')
        self.assertFalse(prefix_settled(self.actor,self.files,ValueError()))

class Inventory(unittest.TestCase):
    def setUp(self):
        self.row=dict(index=0,family='resumed',arguments=['complete','pass'],name='resume-complete-pass',max_CLI_calls=3,max_fake_validator_calls=1)
        self.calls=[dict(verdict=dict(helper_observations=[dict(original='helper')],external_observations=[])),
            dict(verdict=dict(helper_observations=[],external_observations=[dict(original='producer')])),dict(verdict=dict(helper_observations=[],external_observations=[]))]
    def test_exact_original_case_inventory_is_not_release_authority(self):
        result=case_summary(self.row,self.calls,dict(original_assertions='passed'))
        self.assertEqual((result['calls'],result['fake_validators'],result['external_children']),(3,1,1))
        self.assertFalse(result['resource_release_authorized'])
    def test_missing_or_extra_call_refuses_complete_case_label(self):
        for calls in (self.calls[:-1],self.calls+[self.calls[2]]):
            with self.subTest(count=len(calls)),self.assertRaises(ValueError):case_summary(self.row,calls,None)
    def test_missing_helper_cannot_make_full_case_inventory(self):
        self.calls[0]['verdict']['helper_observations']=[]
        with self.assertRaises(ValueError):case_summary(self.row,self.calls,None)

if __name__=='__main__':unittest.main()
