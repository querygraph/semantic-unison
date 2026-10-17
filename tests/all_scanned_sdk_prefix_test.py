import copy
import unittest
import all_scanned_sdk_parent_test as parent_controls
from all_scanned_sdk_prefix import audit_failed
from all_scanned_sdk_audit_test import input_frame


class Prefix(unittest.TestCase):
    def fixture(self, count):
        result, contract, proxies = parent_controls.Parent().fixture()
        result.update(complete=False, phase='CALL_MAY_HAVE_STARTED' if count else 'PREPARING_NO_CALL',
                      failure='original known failure')
        result['invocations'] = result['invocations'][:count]
        return result, contract, proxies[:count]

    def test_zero_and_settled_returned_prefix_never_claim_function_or_release(self):
        for count in range(5):
            result, contract, proxies = self.fixture(count)
            proof = audit_failed(result, contract, raw_proxy_receipts=proxies)
            self.assertEqual(proof['functional_status'], 'FAILED')
            self.assertEqual(proof['attempted_cli_invocations'], count)
            self.assertEqual(proof['sdk_helpers_settled'], 2 * (count // 2))
            self.assertFalse(proof['resource_release_authorized'])

    def test_invalid_sdk_verdict_can_be_settled_but_missing_helper_cannot(self):
        result, contract, proxies = self.fixture(2)
        out = result['invocations'][1]['outcome']
        out['stdout'] = out['stdout'].replace(b'errors 0'.hex(), b'errors 1'.hex())
        self.assertEqual(audit_failed(result, contract, raw_proxy_receipts=proxies)['sdk_helpers_settled'], 2)
        out['stdout'] = 'No helper records\n'
        with self.assertRaises(ValueError): audit_failed(result, contract, raw_proxy_receipts=proxies)

    def test_unknown_intent_and_wrong_phase_never_become_failed_release(self):
        for kind in ('intent', 'phase', 'raw', 'group'):
            result, contract, proxies = self.fixture(1)
            if kind == 'intent': result['invocations'][0].update(state='INTENT')
            elif kind == 'phase': result['phase'] = 'PREPARING_NO_CALL'
            elif kind == 'raw': proxies[0]['server_pid'] += 1
            else:
                result['invocations'][0]['outcome']['supervisor_cleanup']['other_group_members_absent_before_reap'] = False
                proxies = [copy.deepcopy(result['invocations'][0]['outcome']['proxy'])]
            with self.assertRaises(ValueError): audit_failed(result, contract, raw_proxy_receipts=proxies)

    def test_baseline_input_evidence_without_result_cannot_prove_zero_helpers(self):
        result, contract, proxies = self.fixture(1)
        result['invocations'][0]['outcome']['stdout'] += input_frame('client', 999, 10, contract['workspace'] + '/stock')
        with self.assertRaises(ValueError): audit_failed(result, contract, raw_proxy_receipts=proxies)


if __name__ == '__main__': unittest.main()
