"""Parent audit over saved outcomes; no helper invocation or payload reads."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from parent import audit,bind_exit
from plan_test import fixture


class Parent(unittest.TestCase):
    def fixture(self):
        path=Path(__file__).resolve().parents[1]/'qualification/mixed-validation-memory-admission-actual-20261016.json'
        rows=[r for r in json.loads(path.read_text())['rows'] if r['label'] in ('stock','ox')]
        outcomes=[copy.deepcopy(next(c for c in r['report']['cases'] if c['mode']=='pass')['outcome']) for r in rows]
        p=fixture();p['metadata']['version']='synthetic-only'
        # Saved argv are exact historical paths, so derive the expected pair
        # explicitly; plan validation itself is covered by plan_test.
        result=dict(schema='unison-mixed-validation-worker/1',complete=True,phase='FINISHED',
                    invocations=[dict(index=i,state='OUTCOME',outcome=o) for i,o in enumerate(outcomes)])
        return p,result,[o['command'] for o in outcomes]
    def test_complete_saved_pair_requires_actual_exit_separately(self):
        p,r,argv=self.fixture()
        with patch('parent.commands',return_value=argv):proof=audit(r,p,check_files=False)
        self.assertEqual(proof['attempted_probes'],2)
        self.assertFalse(proof['parent_input_bytes_reverified'])
        self.assertFalse(proof['worker_exit_bound'])
        self.assertFalse(bind_exit(proof,0)['resource_release_authorized'])
        for code in (1,True,None):
            with self.assertRaises(ValueError):bind_exit(proof,code)
    def test_missing_outcome_cannot_be_known_failed_prefix(self):
        p,r,argv=self.fixture();r.update(complete=False,phase='CALL_MAY_HAVE_STARTED',failure='missing outcome')
        r['invocations'][-1].update(state='INTENT',outcome=None)
        with patch('parent.commands',return_value=argv),self.assertRaises(ValueError):audit(r,p,check_files=False)
    def test_empty_known_preentry_failure_is_not_a_pass(self):
        p=fixture();r=dict(schema='unison-mixed-validation-worker/1',complete=False,
                          phase='PREPARING_NO_CALL',invocations=[],failure='guard refused')
        proof=audit(r,p,check_files=False)
        self.assertEqual(proof['attempted_probes'],0)
        self.assertEqual(proof['functional_status'],'FAILED')
        self.assertTrue(bind_exit(proof,1)['worker_exit_bound'])
        with self.assertRaises(ValueError):bind_exit(proof,0)


if __name__=='__main__':unittest.main()
