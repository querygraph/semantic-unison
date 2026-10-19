"""Source-only adapter controls; no Session instances or subprocesses created."""
import unittest
from pathlib import Path
from current_validation_paths.original import load
SOURCE=(Path(__file__).resolve().parents[1]/'validation_paths/run.py').read_text()


def factory(legacy):
    class Retained(legacy):
        def __init__(self,*args):raise AssertionError('no construction during source load')
        def sync(self,*args):raise AssertionError('no call during source load')
        def command(self,*args):raise AssertionError('no command during source load')
        def interruption(self,*args):raise AssertionError('no interruption during source load')
    return Retained

def path_factory(legacy):
    class Owned(type(legacy('.'))):
        def read_bytes(self,*args):raise AssertionError('no file IO during source load')
        def read_text(self,*args):raise AssertionError('no file IO during source load')
        def write_bytes(self,*args):raise AssertionError('no file IO during source load')
        def write_text(self,*args):raise AssertionError('no file IO during source load')
        def open(self,*args):raise AssertionError('no file IO during source load')
    return Owned

def cancel(*args):return 'original inert actor'


class OriginalAdapter(unittest.TestCase):
    def test_all_seven_families_loaded_without_main_or_legacy_cancellation(self):
        result=load(SOURCE,session_factory=factory,cancel_actor=cancel,path_factory=path_factory,filename='/source-only/run.py')
        self.assertEqual(set(result['functions']),{'resumed','external','moved','merged','timed_out','cancelled','directory_admission'})
        self.assertIs(result['functions']['cancelled'],cancel)
        self.assertEqual(result['functions']['resumed'].__globals__['Session'].__name__,'Retained')
        self.assertNotIn('main',result['functions']['resumed'].__globals__)
        self.assertFalse(result['runtime_admitted']);self.assertFalse(result['legacy_bare_cancellation_exposed'])
        self.assertFalse(result['legacy_bare_Path_IO_exposed'])
    def test_old_session_or_incomplete_successor_cannot_be_selected(self):
        for candidate in (lambda legacy:legacy,lambda legacy:object,lambda legacy:lambda *args:None):
            with self.assertRaises(ValueError):load(SOURCE,session_factory=candidate,cancel_actor=cancel,path_factory=path_factory,filename='/source-only/run.py')
    def test_bare_path_cannot_reintroduce_unqualified_file_close(self):
        with self.assertRaises(ValueError):load(SOURCE,session_factory=factory,cancel_actor=cancel,
            path_factory=lambda legacy:legacy,filename='/source-only/run.py')
    def test_unexpected_top_level_execution_import_or_initializer_refuses(self):
        for changed in (SOURCE+'\nraise AssertionError("never execute")\n',
                        SOURCE+'\nside_effect()\n',SOURCE+'\nvalue=side_effect()\n',
                        SOURCE+'\nimport external_module\n',SOURCE+'\ndef unsafe(x=side_effect()):pass\n',
                        SOURCE+'\nclass Unsafe:\n    side_effect()\n'):
            with self.assertRaises(ValueError):load(changed,session_factory=factory,cancel_actor=cancel,path_factory=path_factory,filename='/source-only/run.py')

if __name__=='__main__':unittest.main()
