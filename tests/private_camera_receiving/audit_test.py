"""Source fixture composition only; no processes, camera or native cloning."""
import copy
import unittest
import audit
import worker_test


class Controls(unittest.TestCase):
    def setUp(self):
        self.fixture=worker_test.Controls();self.fixture.setUp()
        self.result=self.fixture.execute()
    def tearDown(self):self.fixture.tearDown()
    def check(self,result=None):
        return audit.audit(self.result if result is None else result,
                           self.fixture.plan,self.fixture.work)
    def test_complete_bound_six_calls(self):
        proof=self.check();self.assertEqual(proof['functional_status'],'PASSED')
        self.assertEqual(proof['attempted_cli_invocations'],6)
    def test_malformed_or_unsettled_complete_refused(self):
        mutations=[lambda r:r.update(complete=1),
                   lambda r:r.update(failure='conflicting saved failure'),
                   lambda r:r.update(camera_validity_claimed=True),
                   lambda r:r['invocations'].pop(),
                   lambda r:r['invocations'][0]['command'].__setitem__(0,'/wrong'),
                   lambda r:r['invocations'][0]['identity'].update(directory='/wrong'),
                   lambda r:r['invocations'][0]['outcome']['client_cleanup'].update(reaped=False),
                   lambda r:r['invocations'][0]['outcome']['supervisor_cleanup'].update(returncode=70),
                   lambda r:r['cases'][0]['case'].update(exact_receiving=False),
                   lambda r:r['cases'][0]['clone'].update(backend='full-copy-fallback'),
                   lambda r:r['cases'].reverse(),
                   lambda r:r['cases'][0]['case']['calls'].pop('noop')]
        for mutate in mutations:
            result=copy.deepcopy(self.result);mutate(result)
            with self.assertRaises((ValueError,KeyError)):self.check(result)
    def test_known_failed_prefix_not_functional_success(self):
        result=copy.deepcopy(self.result)
        result.update(complete=False,phase='TRANSPORT_MAY_HAVE_STARTED',failure='verification refused')
        result['invocations']=result['invocations'][:1]
        self.assertEqual(self.check(result)['functional_status'],'FAILED')
    def test_empty_preparation_requires_unstarted_phase_and_failure(self):
        result=copy.deepcopy(self.result)
        result.update(complete=False,phase='PREPARING_NO_TRANSPORT_DISPATCH',failure='clone refused',invocations=[])
        self.assertEqual(self.check(result)['attempted_cli_invocations'],0)
        result['phase']='TRANSPORT_MAY_HAVE_STARTED'
        with self.assertRaises(ValueError):self.check(result)
    def test_pending_intent_cannot_release(self):
        result=copy.deepcopy(self.result)
        result.update(complete=False,phase='TRANSPORT_MAY_HAVE_STARTED',failure='interrupted')
        result['invocations'][0].update(state='INTENT',outcome=None)
        with self.assertRaises(ValueError):self.check(result)


if __name__=='__main__':unittest.main()
