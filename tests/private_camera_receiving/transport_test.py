"""Inert executable bytes and fake outcomes only; no actual process launch."""
import copy
import hashlib
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import transport
from invocation_journal import Journal


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='uc-',dir='/private/tmp')
        self.root=Path(self.temp.name)
        self.binary=self.root/'inert';self.binary.write_bytes(b'not an executable')
        self.item={'label':'stock','path':str(self.binary),
                   'sha256':hashlib.sha256(self.binary.read_bytes()).hexdigest()}
        self.pins=transport.prepare(self.root);self.result={};self.saved=[]
        self.journal=Journal(self.result,lambda:self.saved.append(copy.deepcopy(self.result)))
        self.call=transport.Invoker(self.root,self.item,self.item,self.journal,self.pins,time.monotonic()+300)
    def tearDown(self):self.temp.cleanup()
    def outcome(self):
        return {'returncode':0,'stdout':'','stderr':'','supervisor_output':''}
    def test_success_records_before_return_and_uses_fixed_budget(self):
        with patch.object(transport,'measure_invocation',return_value=self.outcome()) as run:
            self.call('seed')
        argv,env,seconds,_=run.call_args.args
        self.assertEqual(seconds,60);self.assertTrue(run.call_args.kwargs['strict_group_settlement'])
        self.assertEqual(env['UNISON_SYNC_BENCH_DEADLINE_SECONDS'],'65')
        self.assertIn('-adobevalidate',argv);self.assertNotIn('true',argv)
        self.assertEqual(self.saved[0]['invocations'][0]['state'],'INTENT')
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'OUTCOME')
    def test_binary_change_refuses_before_intent_or_launch(self):
        self.binary.write_bytes(b'changed')
        with patch.object(transport,'measure_invocation') as run,self.assertRaises(ValueError):self.call('seed')
        run.assert_not_called();self.assertEqual(self.result['invocations'],[])
    def test_script_change_refuses(self):
        (self.root/'proxy.py').write_text('changed')
        with patch.object(transport,'measure_invocation') as run,self.assertRaises(ValueError):self.call('seed')
        run.assert_not_called()
    def test_failed_call_preserved_and_stage_not_retried(self):
        value=dict(self.outcome(),returncode=1)
        with patch.object(transport,'measure_invocation',side_effect=transport.InvocationFailure(value)):
            with self.assertRaises(transport.InvocationFailure):self.call('seed')
        self.assertEqual(self.saved[-1]['invocations'][0]['outcome']['returncode'],1)
        with self.assertRaises(ValueError):self.call('seed')
    def test_missing_fallback_log_preserves_outcome_but_refuses_success(self):
        with patch.object(transport,'measure_invocation',return_value=self.outcome()):
            self.call('seed')
            with self.assertRaises(ValueError):self.call('update')
        self.assertEqual(len(self.saved[-1]['invocations']),2)
        self.assertEqual(self.saved[-1]['invocations'][-1]['state'],'OUTCOME')
    def test_expected_fallback_log(self):
        value=self.outcome();value['stderr']='Remote semantic fallback: no negotiated profile proves eligibility\nUsing immutable receiver clone basis\n'
        with patch.object(transport,'measure_invocation',return_value=value):
            self.call('seed');self.call('update');self.call('noop')
        with self.assertRaises(ValueError):self.call('noop')
    def test_expired_deadline_refuses_before_binary_read(self):
        self.call.deadline=time.monotonic()+69
        with patch.object(transport,'file_hash') as hashed,self.assertRaises(ValueError):self.call('seed')
        hashed.assert_not_called()


if __name__=='__main__':unittest.main()
