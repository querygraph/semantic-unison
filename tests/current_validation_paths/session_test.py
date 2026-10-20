"""Tiny owned script fixtures and inert dispatch/audit adapters; zero processes."""
import tempfile,unittest,os
from pathlib import Path
from current_validation_paths.files import Files
from current_validation_paths.original import load
from current_validation_paths.session import factory
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving.admission import PYTHON
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()


class RetainedSession(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);st=self.root.lstat()
        self.files=Files(self.root,(st.st_dev,st.st_ino));self.events=[];self.fault=None;self.status=0
        def invoke(session,intent):
            self.events.append('invoke')
            if self.fault=='invoke':raise self.error
            return dict(original='fake pair')
        def audit(session,intent,outcome):
            self.events.append('audit')
            return dict(command=intent['command'],client_returncode=self.status,log='original fabricated settled output',
                external_children_settled=self.fault!='audit',resource_release_authorized=False)
        def persist(event,session,value):
            self.events.append(event)
            if self.fault=='persist':raise ValueError('original intent persistence failure')
        def interrupt(*args):raise self.error
        result=load(SOURCE,session_factory=lambda legacy:factory(legacy,files=self.files,binary='/original/current-unison',
            repository='/source-only/repository',invoke=invoke,audit=audit,interrupt=interrupt,persist=persist),
            path_factory=lambda _:self.files.Path,cancel_actor=lambda *args:None,filename='/source-only/run.py')
        cls=result['functions']['resumed'].__globals__['Session']
        self.session=cls(self.files.Path(self.root/'case'),'/original/current-unison')
    def tearDown(self):
        if self.files.retained is None:self.files.close()
        else:
            # Only inert dispatch/persistence failures are injected here;
            # the real root descriptor is known held, no uncertain OS close.
            os.close(self.files.fd);self.files.closed=True
        self.temp.cleanup()
    def test_private_scripts_and_endpoint_command_use_qualified_python_and_budget(self):
        for path in (*self.session.drivers.values(),self.session.copy,self.session.merger,self.session.launcher):
            self.assertTrue(path.read_text().startswith('#!'+PYTHON+'\n'));self.assertEqual(path.stat().st_mode&0o777,0o700)
        command=self.session.command();self.assertEqual(command[command.index('-semanticcpubudget')+1],'2')
        self.assertEqual(command[command.index('-semanticvolumejobs')+1],'1')
        self.assertEqual(command[command.index('-adobevalidatescope')+1],'received')
    def test_intent_precedes_dispatch_and_audit_precedes_acceptance(self):
        self.assertEqual(self.session.sync(),'original fabricated settled output')
        self.assertEqual(self.events,['INTENT','invoke','audit','ACCEPTED'])
        self.assertEqual((self.session.root/'run-01.log').read_text(),'original fabricated settled output')
    def test_failed_intent_never_dispatches(self):
        self.fault='persist'
        with self.assertRaises(UnresolvedOwnership) as raised:self.session.sync()
        self.assertEqual(self.events,['INTENT']);self.assertIsInstance(raised.exception.original_failure,ValueError)
    def test_uncertain_invocation_preserves_same_carrier_and_prevents_new_calls(self):
        self.fault='invoke';self.error=UnresolvedOwnership('original inert unknown');self.error.retained_fds=(999,)
        with self.assertRaises(UnresolvedOwnership) as raised:self.session.sync()
        self.assertIs(raised.exception,self.error);self.assertIsNone(self.error.__cause__)
        with self.assertRaises(UnresolvedOwnership) as again:self.session.sync()
        self.assertIs(again.exception,self.error);self.assertEqual(self.events,['INTENT','invoke'])
    def test_exact_failure2_and_missing_settlement_refuse_other_outcomes(self):
        self.status=2;self.session.sync(success=False)
        self.status=1
        with self.assertRaises(UnresolvedOwnership):self.session.sync(success=False)
        self.assertNotEqual(self.events[-1],'ACCEPTED')
    def test_unsettled_audit_keeps_outcome_and_root_owner(self):
        self.fault='audit'
        with self.assertRaises(UnresolvedOwnership) as raised:self.session.sync()
        self.assertEqual(raised.exception.named_invocation_outcome,dict(original='fake pair'))
        self.assertIn(self.files.fd,raised.exception.retained_fds)
        self.assertIs(self.files.retained,raised.exception)
        self.assertEqual(self.events,['INTENT','invoke','audit'])
    def test_interruption_delegates_only_to_retained_actor(self):
        self.error=UnresolvedOwnership('original inert interruption')
        with self.assertRaises(UnresolvedOwnership) as raised:self.session.interruption('fixture',b'private','complete')
        self.assertIs(raised.exception,self.error);self.assertIn(self.files.fd,self.error.retained_fds)
        self.assertEqual(self.events,[])
    def test_budget_or_scope_override_cannot_enter_original_options(self):
        for options in (('-semanticcpubudget','18'),('-adobevalidate','off'),('-copyprog','/outside/program')):
            with self.assertRaises(ValueError):self.session.command(options=options)
        self.assertEqual(self.events,[])

if __name__=='__main__':unittest.main()
