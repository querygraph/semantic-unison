"""Mock command construction/journal only; no executable or SDK dispatch."""
import time
import unittest
from unittest.mock import Mock, patch
import sdk_transport as transport


class Controls(unittest.TestCase):
    def invoker(self):
        return transport.Invoker('/private/tmp/sdk-seed-inert',
            {'label':'stock','path':'/inert/unison','sha256':'a'*64},
            {'path':'/inert/validator','sha256':'b'*64,'build_id':transport.BUILD,'threads':1},
            Mock(),{n:'c'*64 for n in transport.SCRIPT_NAMES},time.monotonic()+300)
    def hash(self,path):
        return 'a'*64 if str(path)=='/inert/unison' else 'b'*64 if str(path)=='/inert/validator' else 'c'*64
    def test_one_require_seed_two_endpoint_workers_one_sdk_thread(self):
        call=self.invoker();outcome={'returncode':0}
        def measure(argv,env,seconds,script,**kwargs):
            call.journal.begin.assert_called_once()
            self.assertEqual(argv[argv.index('-adobevalidate')+1],'require')
            self.assertEqual(argv[argv.index('-adobevalidatorthreads')+1],'1')
            self.assertEqual(argv[argv.index('-semanticworkers')+1],'2')
            self.assertEqual(argv[argv.index('-semanticpayloadbudget')+1],'4096')
            self.assertEqual(argv[argv.index('-adobevalidatorworkspace')+1],'2048')
            self.assertEqual(seconds,120);self.assertTrue(kwargs['strict_group_settlement'])
            return outcome
        with patch.object(transport,'stable_sha',side_effect=self.hash), \
             patch.object(transport,'measure_invocation',side_effect=measure) as measure_call:
            self.assertIs(call(),outcome)
            with self.assertRaises(ValueError):call()
        measure_call.assert_called_once();call.journal.finish.assert_called_once_with(outcome)
    def test_changed_tool_refuses_before_journal_and_call(self):
        call=self.invoker()
        with patch.object(transport,'stable_sha',return_value='d'*64), \
             patch.object(transport,'measure_invocation') as measure:
            with self.assertRaises(ValueError):call()
        call.journal.begin.assert_not_called();measure.assert_not_called()
    def test_nonreference_or_multithread_tool_refused(self):
        call=self.invoker()
        for change in ({'build_id':'experimental'},{'threads':6}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                transport.Invoker(call.directory,call.binary,dict(call.tool,**change),
                    call.journal,call.pins,call.deadline)
    def test_failed_invocation_outcome_is_journaled_without_retry(self):
        call=self.invoker();outcome={'returncode':1}
        error=transport.InvocationFailure(outcome)
        with patch.object(transport,'stable_sha',side_effect=self.hash), \
             patch.object(transport,'measure_invocation',side_effect=error):
            with self.assertRaises(transport.InvocationFailure):call()
        call.journal.finish.assert_called_once_with(outcome)
        with self.assertRaises(ValueError):call()


if __name__=='__main__':unittest.main()
