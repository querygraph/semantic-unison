"""Composed worker with original four-byte source and mocked clone/transport."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import worker


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='ucw-',dir='/private/tmp')
        self.root=Path(self.temp.name);self.source=self.root/'borrowed'
        self.source.write_bytes(b'four');self.source.chmod(0o400)
        self.work=self.root/'work';self.work.mkdir(mode=0o700)
        self.plan={'source':{'path':str(self.source),'identity':worker.clone.stamp(self.source.lstat()),
                    'historical_sha256':hashlib.sha256(b'four').hexdigest()},
                   'binaries':{label:{'label':label} for label in ('stock','ox')}}
        self.calls=0;self.failure=None
    def tearDown(self):self.temp.cleanup()
    def prepare(self,source,expected,directory):
        target=directory/'image.dng';target.write_bytes(b'four');target.chmod(0o600)
        # Explicit mock of the runtime clone boundary, not native proof.
        return {'backend':'native-fclonefileat-only','test_double':True}
    def invoker(self,directory,item,server,journal,pins,deadline):
        def call(stage):
            self.calls+=1;argv=['mock-only',item['label'],stage]
            journal.begin({'label':item['label'],'mode':'semantic','workers':2,
                           'directory':str(directory),'stage':stage},argv)
            def group(pid):return {'pid':pid,'reaped':True,'returncode':0,
                'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True}
            outcome={'command':argv,'returncode':0,'timed_out':False,'capture_truncated':False,
                'supervisor_capture_truncated':False,'client_cleanup':group(10),
                'supervisor_cleanup':group(11),'proxy':{'schema':'unison-loopback-protocol-count/1',
                    'server_cleanup':group(12),'server_pid':12,'server_returncode':0,
                    'input_pump_joined':True,'server_command':['mock-only','-server']}}
            if stage==self.failure:
                outcome['returncode']=outcome['client_cleanup']['returncode']=1
            elif stage!='noop':
                target=directory/'right/new';target.write_bytes((directory/'left/image.dng').read_bytes())
                target.replace(directory/'right/image.dng')
            journal.finish(outcome)
            return outcome
        return call
    def execute(self):
        with patch.object(worker.clone,'prepare',side_effect=self.prepare), \
             patch.object(worker.transport,'prepare',return_value={}), \
             patch.object(worker.transport,'Invoker',side_effect=self.invoker):
            return worker.execute(self.plan,self.work,time.monotonic()+300)
    def test_two_cases_six_calls_exact(self):
        result=self.execute();self.assertTrue(result['complete']);self.assertEqual(self.calls,6)
        self.assertEqual(result['call_lifecycle']['attempted_cli_invocations'],6)
        self.assertEqual(worker.clone.stamp(self.source.lstat()),self.plan['source']['identity'])
    def test_first_failure_stops_and_preserves_prefix(self):
        self.failure='seed'
        with self.assertRaises(ValueError):self.execute()
        result=json.loads((self.work/'RESULT.json').read_text())
        self.assertFalse(result['complete']);self.assertEqual(len(result['invocations']),1)
        self.assertEqual(result['invocations'][0]['outcome']['returncode'],1)
        self.assertEqual(len(result['cases']),1);self.assertIn('failure',result['cases'][0]['case'])
    def test_source_identity_refusal_before_clone_or_calls(self):
        self.plan['source']['identity']['st_ino']+=1
        with self.assertRaises(ValueError):self.execute()
        result=json.loads((self.work/'RESULT.json').read_text())
        self.assertEqual(result['phase'],'PREPARING_NO_TRANSPORT_DISPATCH')
        self.assertEqual(result['invocations'],[]);self.assertEqual(self.calls,0)


if __name__=='__main__':unittest.main()
