"""Original cancellation assertions over owned tiny files/inert sync adapters.

The fake receiver below is deliberately NOT Unison or a lifecycle verifier.
These controls prove the source adapter invokes the original assertions and
fails before recovery when preservation/cleanup is violated.
"""
import hashlib,json,tempfile,unittest
from pathlib import Path
from current_validation_paths.files import Files
from current_validation_paths.original import load
from current_validation_paths.session import factory as session_factory
from current_validation_paths.cancel_case import factory
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()

class OriginalCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='vpcase-',dir='/private/tmp');root=Path(self.temp.name);st=root.lstat()
        self.files=Files(root,(st.st_dev,st.st_ino));self.events=[];self.fault=None
        def invoke(session,intent):
            self.events.append(intent);name='cancelled.dng';left=session.left/name;right=session.right/name
            if not right.exists():source,destination,endpoint=left,right,'server'
            elif left.read_bytes()!=right.read_bytes():source,destination,endpoint=right,left,'client'
            else:return dict(command=intent['command'],client_returncode=0,log='original fabricated noop',external_children_settled=True,resource_release_authorized=False)
            incoming=source.read_bytes();previous=destination.read_bytes() if destination.exists() else None
            candidate=destination.parent/'generated-private-stage';candidate.write_bytes(incoming);st=candidate.lstat()
            sha=hashlib.sha256(incoming).hexdigest();control=intent['helper_controls'][endpoint]
            record=dict(endpoint=endpoint,mode=control['mode'],pid=100+len(self.events),candidate=str(candidate),destination=str(destination),
                sha256=sha,size=len(incoming),destination_sha256=None if previous is None else hashlib.sha256(previous).hexdigest(),
                device=st.st_dev,inode=st.st_ino,argv=['--unison-dng-validation-v1','--expected-sha256',sha,'--expected-size',str(len(incoming)),'--threads','1','--',str(candidate)])
            counter=session.drivers[endpoint].with_suffix('.calls.jsonl')
            old=counter.read_text() if counter.exists() else '';counter.write_text(old+json.dumps(record)+'\n')
            prefix='[semantic]' if endpoint=='client' else '[server: semantic]';log=prefix+' 1 jobs per filesystem\n'
            if intent['expected_client_exit']==3:
                log+='Update propagation interrupted\nAborted by user request\n'
                if self.fault=='replace-old':destination.write_bytes(incoming)
                if self.fault=='mutate-source':source.write_bytes(b'corrupt generated source')
                if self.fault!='leave-stage':candidate.unlink()
            else:destination.write_bytes(incoming);candidate.unlink()
            return dict(command=intent['command'],client_returncode=intent['expected_client_exit'],log=log,
                external_children_settled=True,resource_release_authorized=False)
        result=load(SOURCE,session_factory=lambda legacy:session_factory(legacy,files=self.files,binary='/inert/current-unison',
            repository=str(Path(__file__).resolve().parents[2]),invoke=invoke,audit=lambda session,intent,result:result,
            interrupt=lambda *args:None,persist=lambda *args:None),cancel_actor=lambda *args:None,
            path_factory=lambda _:self.files.Path,filename='/original-source/run.py')
        cls=result['functions']['resumed'].__globals__['Session'];self.case=factory(cls)
    def tearDown(self):self.files.close();self.temp.cleanup()
    def run_case(self,policy='require'):self.case(self.files.Path(self.temp.name)/'case','/inert/current-unison',policy)
    def test_require_original_seed_cancel_recover_noop_all_assertions(self):
        self.run_case();self.assertEqual([e['expected_client_exit'] for e in self.events],[0,3,0,0])
        self.assertIn('cancellation',self.events[1]);self.assertNotIn('cancellation',self.events[2])
    def test_warn_does_not_turn_cancel_into_publication(self):
        self.run_case('warn');command=self.events[1]['command'];self.assertEqual(command[command.index('-adobevalidate')+1],'warn')
        self.assertEqual(len(self.events),4)
    def test_replaced_live_destination_fails_before_recovery_call(self):
        self.fault='replace-old'
        with self.assertRaisesRegex(AssertionError,'cancellation replaced old live receiver'):self.run_case()
        self.assertEqual(len(self.events),2)
    def test_mutated_source_fails_before_recovery_call(self):
        self.fault='mutate-source'
        with self.assertRaisesRegex(AssertionError,'cancellation mutated sending source'):self.run_case()
        self.assertEqual(len(self.events),2)
    def test_leftover_cancelled_candidate_fails_before_recovery_call(self):
        self.fault='leave-stage'
        with self.assertRaisesRegex(AssertionError,'cancelled validation stage remained resumable'):self.run_case()
        self.assertEqual(len(self.events),2)

if __name__=='__main__':unittest.main()
