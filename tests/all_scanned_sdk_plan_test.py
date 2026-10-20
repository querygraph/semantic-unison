import unittest
from all_scanned_sdk_plan import BUILD, MIB, plan


class Planning(unittest.TestCase):
    def setUp(self):
        self.binary = dict(path='/inert/unison', sha256='a' * 64, label='stock')
        self.tool = dict(path='/inert/sdk', sha256='b' * 64, build_id=BUILD, threads=1)

    def test_identical_both_endpoint_policy_and_explicit_baseline(self):
        p = plan(self.binary, self.tool, '/private/tmp/u-scan-inert')
        for name, policy, scope in [('baseline', 'off', 'received'),
                                    ('validate', 'require', 'all-scanned')]:
            call = p[name]; flags = call['server_flags']
            self.assertEqual(call['argv'][-len(flags):], flags)
            self.assertEqual(flags[flags.index('-adobevalidate') + 1], policy)
            self.assertEqual(flags[flags.index('-adobevalidatescope') + 1], scope)
        self.assertEqual(p['maximum_sdk_calls_per_compiler'], 2)
        self.assertTrue(p['requires_empty_transfer_on_validation'])

    def test_unchanged_accounting_is_not_receiving_publication_accounting(self):
        p = plan(self.binary, self.tool, '/private/tmp/u-scan-inert')
        self.assertEqual(p['minimum_payload_credits_per_endpoint'], 2050 * MIB)
        self.assertLessEqual(p['minimum_payload_credits_per_endpoint'], p['payload_credits_per_endpoint'])
        self.assertEqual(sum(p['cpu_endpoint_credits']) + p['cpu_owner_credits'], 8)
        self.assertFalse(p['runtime_admitted']); self.assertFalse(p['sdk_validation_proved'])

    def test_no_unqualified_driver_or_namespace(self):
        for changes in [dict(threads=True), dict(threads=2), dict(build_id='new'), dict(sha256='bad')]:
            with self.assertRaises(ValueError):
                plan(self.binary, dict(self.tool, **changes), '/private/tmp/u-scan-inert')
        for path in ['relative', '/private/tmp/../bad', '/private/tmp/' + 'x' * 100]:
            with self.assertRaises(ValueError): plan(self.binary, self.tool, path)


if __name__ == '__main__':
    unittest.main()
