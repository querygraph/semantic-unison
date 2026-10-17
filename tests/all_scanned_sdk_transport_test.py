import time
import unittest
from unittest.mock import patch
import all_scanned_sdk_transport as transport
from all_scanned_sdk_plan import BUILD


class Journal:
    def __init__(self): self.events = []
    def begin(self, identity, argv): self.events.append(('begin', identity, argv))
    def finish(self, outcome): self.events.append(('finish', outcome))


class Transport(unittest.TestCase):
    def create(self, phase='validate', deadline=None):
        self.journal = Journal()
        return transport.Invoker('/private/tmp/u-scan-inert',
            binary=dict(path='/inert/unison', label='stock', sha256='a' * 64),
            tool=dict(path='/inert/sdk', sha256='a' * 64, build_id=BUILD, threads=1),
            phase=phase, journal=self.journal,
            script_pins={k: 'a' * 64 for k in transport.SCRIPT_NAMES},
            deadline=deadline if deadline is not None else time.monotonic() + 400)

    def test_each_phase_exact_server_policy_and_intent_before_dispatch(self):
        import json
        for phase in ('baseline', 'validate'):
            call = self.create(phase)
            out = dict(inert=True)
            def measured(argv, env, seconds, proxy, **kwargs):
                self.assertEqual(self.journal.events[0][0], 'begin')
                self.assertEqual(self.journal.events[0][1]['stage'], phase)
                self.assertEqual(seconds, 240)
                self.assertEqual(argv, call.contract[phase]['argv'])
                flags = json.loads(env['UNISON_SYNC_BENCH_SERVER_FLAGS'])
                self.assertEqual(argv[-len(flags):], flags)
                self.assertTrue(env['UNISON_SYNC_BENCH_PROXY_RECEIPT'].endswith(phase + '-proxy.json'))
                self.assertTrue(env['UNISON_SYNC_BENCH_SOCKET'].endswith(phase + '-scan.sock'))
                self.assertNotIn('UNISON_CONCURRENT_SYNTHETIC_ROOT', env)
                self.assertTrue(kwargs['strict_group_settlement'])
                return out
            with patch.object(transport, 'artifact_sha', return_value='a' * 64), \
                 patch.object(transport, 'measure_invocation', side_effect=measured) as run:
                self.assertIs(call(), out)
                self.assertEqual(self.journal.events[-1], ('finish', out))
                with self.assertRaises(ValueError): call()
                self.assertEqual(run.call_count, 1)

    def test_refusal_is_one_use_and_never_journals_possible_call(self):
        for short in (True, False):
            call = self.create(deadline=time.monotonic() + 1 if short else None)
            with patch.object(transport, 'artifact_sha', return_value='b' * 64), \
                 patch.object(transport, 'measure_invocation') as run:
                with self.assertRaises(ValueError): call()
                with self.assertRaises(ValueError): call()
                run.assert_not_called()
                self.assertEqual(self.journal.events, [])

    def test_possible_unknown_call_does_not_forge_finish_or_retry(self):
        call = self.create()
        with patch.object(transport, 'artifact_sha', return_value='a' * 64), \
             patch.object(transport, 'measure_invocation', side_effect=RuntimeError('unknown')) as run:
            with self.assertRaises(RuntimeError): call()
            self.assertEqual([e[0] for e in self.journal.events], ['begin'])
            with self.assertRaises(ValueError): call()
            self.assertEqual(run.call_count, 1)

    def test_returned_failed_outcome_is_journaled_before_propagation(self):
        call = self.create()
        outcome = dict(inert_failure=True)
        error = transport.InvocationFailure(outcome)
        with patch.object(transport, 'artifact_sha', return_value='a' * 64), \
             patch.object(transport, 'measure_invocation', side_effect=error) as run:
            with self.assertRaises(transport.InvocationFailure) as raised: call()
            self.assertIs(raised.exception, error)
            self.assertEqual(self.journal.events[-1], ('finish', outcome))
            with self.assertRaises(ValueError): call()
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__': unittest.main()
