import copy
import unittest
from batch_observations import capture,validate
from batch_transport_test import pending


class Observations(unittest.TestCase):
    def test_per_process_wait4_and_clock_scope_preserved(self):
        value=capture(pending().owner)
        self.assertEqual(value['pid'],42);self.assertEqual(value['wall_to_terminal_ns'],1000000000)
        self.assertEqual(value['wait4']['wait4_user_seconds'],.1)
        self.assertFalse(value['resource_release_authorized'])
        self.assertIn('not simultaneous tree peak',value['scope'])

    def test_bad_pid_clock_usage_scope_refuse(self):
        value=capture(pending().owner)
        for mutate in (lambda x:x.update(pid=43),lambda x:x.update(terminal_observed_ns=1),
                       lambda x:x.update(wall_to_terminal_ns=True),lambda x:x['wait4'].update(wait4_user_seconds=float('nan')),
                       lambda x:x.update(scope='hard RSS peak')):
            candidate=copy.deepcopy(value);mutate(candidate)
            with self.assertRaises(ValueError):validate(candidate,42)


if __name__=='__main__':unittest.main()
