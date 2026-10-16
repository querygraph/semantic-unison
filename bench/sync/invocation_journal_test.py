"""Original fake-call accounting controls; no child or binary execution."""
import copy
import unittest
from invocation_journal import Journal, audit_attempted


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

    def prefix(self):
        owner = {'pid': 11, 'returncode': 7, 'reaped': True,
                 'group_cleanup_before_leader_reap': True,
                 'other_group_members_absent_before_reap': True}
        outcome = {'command': ['fake'], 'returncode': 7, 'capture_truncated': False,
                   'supervisor_capture_truncated': False, 'client_cleanup': owner,
                   'supervisor_cleanup': dict(owner, pid=12),
                   'proxy': {'server_cleanup': dict(owner, pid=13), 'server_pid': 13,
                             'server_returncode': 7, 'server_command': ['fake', '-server'],
                             'input_pump_joined': True}}
        return {'invocations': [{'index': 0, 'state': 'OUTCOME',
                'identity': {'label': 'stock', 'mode': 'semantic', 'workers': 3,
                             'directory': '/fake', 'stage': 'seed'},
                'command': ['fake'], 'outcome': outcome}]}

    def test_nonzero_prefix_lifecycle_not_functional_pass(self):
        proof = audit_attempted(self.prefix())
        self.assertEqual(proof['attempted_cli_invocations'], 1)
        self.assertIs(proof['functional_success_inferred'], False)

    def test_unsettled_prefix_refusals(self):
        mutations = [
            lambda e: e.update(state='INTENT'),
            lambda e: e.update(index=True),
            lambda e: e['identity'].update(stage='update'),
            lambda e: e['identity'].update(workers=18),
            lambda e: e['outcome'].update(command=['other']),
            lambda e: e['outcome'].update(capture_truncated=True),
            lambda e: e['outcome']['client_cleanup'].update(reaped=False),
            lambda e: e['outcome']['supervisor_cleanup'].update(other_group_members_absent_before_reap=False),
            lambda e: e['outcome']['proxy'].update(input_pump_joined=False),
            lambda e: e['outcome']['proxy'].update(server_pid=99),
            lambda e: e['outcome']['proxy'].update(server_command=['other']),
        ]
        for mutate in mutations:
            result = self.prefix()
            mutate(result['invocations'][0])
            with self.assertRaises((ValueError, KeyError, TypeError)):
                audit_attempted(result)

    def test_duplicate_seed_refused(self):
        result = self.prefix()
        second = copy.deepcopy(result['invocations'][0])
        second['index'] = 1
        result['invocations'].append(second)
        with self.assertRaises(ValueError):
            audit_attempted(result)


if __name__ == '__main__':
    unittest.main()
