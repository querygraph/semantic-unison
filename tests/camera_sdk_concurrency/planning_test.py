"""Finite accounting boundaries only; no helpers, payloads or canonical IO."""
import unittest
from planning import plan, MIB


class Accounting(unittest.TestCase):
    def test_two_candidates_fit_six_gib_and_standing_eight(self):
        p = plan()
        self.assertEqual(p['minimum_gate_bytes'], 4698406912)
        self.assertEqual(p['minimum_descriptor_credits'], 56)
        self.assertEqual(p['transaction_slots'], 3)
        self.assertEqual(p['configured_endpoint_cpu_total'] + p['owner_credits'], 8)
        self.assertFalse(p['runtime_admitted'])
        self.assertFalse(p['actual_concurrency_qualified'])

    def test_serial_four_gib_gate_cannot_run_two_declared_workspaces(self):
        with self.assertRaisesRegex(ValueError, 'publications'):
            plan(gate_mib=4096)

    def test_exact_gate_boundary(self):
        minimum = (4698406912 + MIB - 1) // MIB
        self.assertEqual(plan(gate_mib=minimum)['gate_mib'], minimum)
        with self.assertRaises(ValueError):
            plan(gate_mib=minimum-1)

    def test_exact_descriptor_boundary(self):
        plan(descriptor_credits=56)
        with self.assertRaises(ValueError):
            plan(descriptor_credits=55)

    def test_endpoint_workers_count_both_sides(self):
        with self.assertRaisesRegex(ValueError, 'both endpoints'):
            plan(endpoint_workers=4)
        with self.assertRaisesRegex(ValueError, 'both single-thread'):
            plan(endpoint_workers=1)

    def test_both_memory_gates_count(self):
        plan(project_memory_gib=12)
        with self.assertRaisesRegex(ValueError, 'both endpoint gates'):
            plan(project_memory_gib=11)

    def test_reject_wrong_counts_and_types(self):
        for args in ({'consumers':1},{'consumers':3},{'cpu_grant':18},
                     {'consumers':True},{'gate_mib':0},{'workspace_mib':-1},
                     {'endpoint_workers':3.0},{'owner_credits':0},
                     {'gate_mib':32769},{'project_memory_gib':33}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan(**args)


if __name__ == '__main__':
    unittest.main()
