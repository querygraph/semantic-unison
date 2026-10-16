"""Composed SDK worker on four original bytes; all clone/process/SDK calls fake."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import sdk_worker as worker
import sdk_audit_test as frames
import sdk_result_audit


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sdk-worker-fake-',dir='/private/tmp')
        self.root=Path(self.temp.name);self.source=self.root/'source'
        self.source.write_bytes(b'four');self.source.chmod(0o400)
        self.workspace=self.root/'work';self.workspace.mkdir(mode=0o700)
        self.plan={'source':{'path':str(self.source),'identity':worker.clone.stamp(self.source.lstat()),
                    'historical_sha256':hashlib.sha256(b'four').hexdigest()},
                   'binaries':{label:{'label':label,'path':'/inert/'+label} for label in ('stock','ox')},
                   'tool':{'path':'/inert/validator','sha256':'b'*64,
                           'build_id':frames.audit.BUILD,'threads':1}}
        self.calls=0;self.missing=False;self.invalid=False
    def tearDown(self):self.temp.cleanup()
    def prepare(self,source,expected,directory):
        target=directory/'image.dng';target.write_bytes(b'four');target.chmod(0o600)
        return {'backend':'native-fclonefileat-only','test_double':True,'source_identity':expected}
    def invoker(self,directory,item,tool,journal,pins,deadline):
        def call():
            self.calls+=1
            argv=[item['path'],str(directory/'left'),'ssh://localhost/'+str(directory/'right')]
            for k,v in (('-adobevalidate','require'),('-adobevalidator',tool['path']),
                        ('-adobevalidatorhash',tool['sha256']),('-adobevalidatorbuild',tool['build_id']),
                        ('-adobevalidatorthreads','1'),('-adobevalidatorworkspace','2048'),
                        ('-semanticpayloadbudget','4096'),('-validationtreememory','0'),
                        ('-semanticdescriptorbudget','64')):argv += [k,v]
            journal.begin({'label':item['label'],'mode':'semantic','workers':2,
                           'directory':str(directory),'stage':'seed'},argv)
            def group(pid):return {'pid':pid,'reaped':True,'returncode':0,
                'group_cleanup_before_leader_reap':True,'other_group_members_absent_before_reap':True}
            with patch.object(frames,'SHA',self.plan['source']['historical_sha256']),patch.object(frames,'SIZE',4):
                log='' if self.missing else frames.log(frames.report(**{'errors':'1'}) if self.invalid else None)
            outcome={'command':argv,'returncode':1 if self.invalid else 0,'timed_out':False,
                'capture_truncated':False,'supervisor_capture_truncated':False,
                'stdout':log,'stderr':'','supervisor_output':'','client_cleanup':group(10),
                'supervisor_cleanup':group(11),'proxy':{'schema':'unison-loopback-protocol-count/1',
                    'server_cleanup':group(12),'server_pid':12,'server_returncode':0,
                    'input_pump_joined':True,'server_command':[item['path'],'-server'],
                    'fault':None,'pump_errors':[]}}
            outcome['client_cleanup']['returncode']=outcome['returncode']
            if not self.invalid:(directory/'right/image.dng').write_bytes(b'four')
            journal.finish(outcome);return outcome
        return call
    def execute(self):
        with patch.object(worker.clone,'prepare',side_effect=self.prepare), \
             patch.object(worker.preparation_transport,'prepare',return_value={}), \
             patch.object(worker.transport,'Invoker',side_effect=self.invoker):
            return worker.execute(self.plan,self.workspace,time.monotonic()+400)
    def test_two_seeds_two_helpers_full_composed_audit(self):
        result=self.execute()
        self.assertTrue(result['complete']);self.assertEqual(self.calls,2)
        proof=sdk_result_audit.audit(result,self.plan,self.workspace)
        self.assertEqual(proof['attempted_cli_invocations'],2)
        self.assertEqual(proof['helper_invocations'],2)
        # Removing one mandatory group cannot leave an auditable success.
        result['invocations'][0]['outcome']['stdout']=''
        with self.assertRaises(ValueError):sdk_result_audit.audit(result,self.plan,self.workspace)
    def test_complete_result_rejects_proxy_fault_or_changed_sdk_report(self):
        import copy
        result=self.execute()
        changed=copy.deepcopy(result)
        changed['invocations'][0]['outcome']['proxy']['pump_errors']=['original fake pump fault']
        # Keep row/journal outcome binding intact so the pump check is exercised.
        changed['cases'][0]['case']['outcome']=changed['invocations'][0]['outcome']
        with self.assertRaises(ValueError):sdk_result_audit.audit(changed,self.plan,self.workspace)
        result['cases'][0]['case']['sdk']['report']['raw_digest_verified']=False
        with self.assertRaises(ValueError):sdk_result_audit.audit(result,self.plan,self.workspace)
    def test_unknown_helper_never_becomes_failed_prefix_release(self):
        self.missing=True
        with self.assertRaises(worker.UnresolvedOwnership):self.execute()
        result=json.loads((self.workspace/'RESULT.json').read_text())
        self.assertNotIn('failure',result);self.assertEqual(self.calls,1)
        with self.assertRaises(ValueError):sdk_result_audit.audit(result,self.plan,self.workspace)
    def test_settled_invalid_finding_preserves_known_failed_prefix(self):
        self.invalid=True
        with self.assertRaises(ValueError):self.execute()
        result=json.loads((self.workspace/'RESULT.json').read_text())
        self.assertIn('failure',result);self.assertEqual(self.calls,1)
        proof=sdk_result_audit.audit(result,self.plan,self.workspace)
        self.assertEqual(proof['functional_status'],'FAILED');self.assertEqual(proof['helper_invocations'],1)
    def test_borrowed_refusal_has_zero_call_phase(self):
        self.plan['source']['identity']['st_ino']+=1
        with self.assertRaises(ValueError):self.execute()
        result=json.loads((self.workspace/'RESULT.json').read_text())
        proof=sdk_result_audit.audit(result,self.plan,self.workspace)
        self.assertEqual(proof['attempted_cli_invocations'],0)


if __name__=='__main__':unittest.main()
