"""Original fake-call accounting controls; no child or binary execution."""
import copy
import unittest
from invocation_journal import Journal


class Controls(unittest.TestCase):
    def setUp(self):
        self.result = {}
        self.saved = []
        self.journal = Journal(self.result, lambda: self.saved.append(copy.deepcopy(self.result)))

    def begin(self):
        self.journal.begin({'stage': 'seed'}, ['fake-only'])

    def test_success_survives_later_verification_failure(self):
        self.begin()
        self.journal.finish({'returncode': 0, 'cleanup': {'reaped': True}})
        try:
            raise ValueError('post-seed verification refused')
        except ValueError:
            pass
        self.assertEqual(self.saved[-1]['invocations'][0]['outcome']['returncode'], 0)

    def test_nonzero_outcome_preserved(self):
        self.begin()
        self.journal.finish({'returncode': 7})
        self.assertEqual(self.saved[-1]['invocations'][0]['outcome']['returncode'], 7)

    def test_unexpected_failure_leaves_unknown_intent(self):
        self.begin()
        self.assertEqual(self.saved[-1]['invocations'][0]['state'], 'INTENT')
        self.assertIsNone(self.saved[-1]['invocations'][0]['outcome'])
        with self.assertRaises(RuntimeError):
            self.begin()

    def test_begin_persist_failure_prevents_dispatch(self):
        self.journal.persist = lambda: (_ for _ in ()).throw(OSError('disk refused'))
        with self.assertRaises(OSError):
            self.begin()
        self.assertIsNotNone(self.journal.pending)

    def test_outcome_persist_failure_retains_pending(self):
        self.begin()
        self.journal.persist = lambda: (_ for _ in ()).throw(OSError('disk refused'))
        with self.assertRaises(OSError):
            self.journal.finish({'returncode': 0})
        self.assertIsNotNone(self.journal.pending)
        self.assertEqual(self.saved[-1]['invocations'][0]['state'], 'INTENT')

    def test_outcome_is_independent_copy(self):
        self.begin()
        outcome = {'cleanup': {'reaped': True}}
        self.journal.finish(outcome)
        outcome['cleanup']['reaped'] = False
        self.assertTrue(self.result['invocations'][0]['outcome']['cleanup']['reaped'])

    def test_order_and_no_outcome_without_intent(self):
        with self.assertRaises(RuntimeError):
            self.journal.finish({})
        for _ in range(3):
            self.begin()
            self.journal.finish({'returncode': 0})
        self.assertEqual([r['index'] for r in self.saved[-1]['invocations']], [0, 1, 2])


if __name__ == '__main__':
    unittest.main()
