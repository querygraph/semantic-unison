"""Observed-call composition on one original Python child; zero SDK calls."""
import copy
import os
import sys
import time
import unittest
from shared_observed import invoke_observed,audit_observed,checked_contract

CONTRACT=dict(path='/private/tmp/unison-os-process-observation-20261016a/controls/probe',
 sha256='fc122e591ef1b5e2c943675c4193ac19b43870ba4e08597e7f894f7a91a1b017',
 sample_limit=2,interval_seconds=.05)


class Observed(unittest.TestCase):
    def test_actual_composed_original_child_and_probe_audit(self):
        out=invoke_observed([sys.executable,'-c','import time;time.sleep(.3)'],
                            dict(os.environ),time.monotonic()+10,contract=CONTRACT)
        value=audit_observed(out,CONTRACT)
        self.assertEqual(value['samples'],2);self.assertEqual(value['probe_children_settled'],2)
        self.assertFalse(value['resource_release_authorized'])
        broken=copy.deepcopy(out);broken['process_observations']['probe_children'][0]['client_cleanup']['reaped']=False
        with self.assertRaises(ValueError):audit_observed(broken,CONTRACT)
        broken=copy.deepcopy(out);broken['process_observations']['sample_limit']=3
        with self.assertRaises(ValueError):audit_observed(broken,CONTRACT)
        for child in [out]+out['process_observations']['probe_children']:
            with self.assertRaises(ChildProcessError):os.waitpid(child['client_cleanup']['pid'],os.WNOHANG)

    def test_contract_refuses_extra_field_and_invalid_budgets(self):
        for changes in [dict(extra=True),dict(sample_limit=True),dict(sample_limit=129),dict(interval_seconds=.001),dict(interval_seconds=True),dict(sha256='x'*64)]:
            with self.assertRaises(ValueError):checked_contract(dict(CONTRACT,**changes))


if __name__=='__main__':unittest.main()
