import json
import time
import unittest
from unittest.mock import patch
from transport import Invoker
import invocation as original
from sdk_multifile.plan import BUILD


class Journal:
    def __init__(self):self.events=[]
    def begin(self,identity,command):self.events.append(('begin',identity,command))
    def finish(self,outcome):self.events.append(('finish',outcome))


class Transport(unittest.TestCase):
    def create(self,deadline=None):
        self.journal=Journal()
        return Invoker('/private/tmp/u-sdk-multi-test',binary=dict(label='stock',path='/inert/stock',sha256='a'*64),
                       tool=dict(path='/inert/sdk',sha256='a'*64,threads=1,build_id=BUILD),journal=self.journal,
                       script_pins={n:'a'*64 for n in original.SCRIPT_NAMES},deadline=deadline or time.monotonic()+200)
    def test_four_slot_command_and_server_flags_exact(self):
        call=self.create();argv=call.contract['argv'];flags=json.loads(call.contract['environment_overrides']['UNISON_SYNC_BENCH_SERVER_FLAGS'])
        self.assertEqual(argv[-len(flags):],flags)
        self.assertEqual(flags[flags.index('-semanticmaxinflight')+1],'4')
        self.assertNotIn('UNISON_CONCURRENT_SYNTHETIC_ROOT',call.contract['environment_overrides'])
    def test_one_use_and_intent_before_returned_outcome(self):
        call=self.create();outcome=dict(original='inert outcome')
        def measured(*args,**kw):
            self.assertEqual(self.journal.events[0][0],'begin')
            self.assertTrue(kw['strict_group_settlement']);return outcome
        with patch.object(original,'artifact_sha',return_value='a'*64),patch.object(original,'measure_invocation',side_effect=measured) as run:
            self.assertIs(call(),outcome)
            self.assertEqual(self.journal.events[-1],('finish',outcome))
            with self.assertRaises(ValueError):call()
            self.assertEqual(run.call_count,1)
    def test_expired_phase_and_changed_pin_never_dispatch(self):
        for short in [True,False]:
            call=self.create(deadline=time.monotonic()+1 if short else None)
            with patch.object(original,'artifact_sha',return_value='b'*64),patch.object(original,'measure_invocation') as run:
                with self.assertRaises(ValueError):call()
                run.assert_not_called();self.assertEqual(self.journal.events,[])

if __name__=='__main__':unittest.main()
