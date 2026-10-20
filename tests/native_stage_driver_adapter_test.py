import subprocess,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from native_stage_driver_adapter import Bridge,RetainedDirectory


class Adapter(unittest.TestCase):
    def test_preserves_negative_exit_and_raw_text_without_shell(self):
        invoked=[]
        def call(argv,timeout):
            invoked.append((argv,timeout));return dict(returncode=77,stdout='native output\n',stderr='original diagnostic')
        bridge=Bridge('/private/tmp/probe',call)
        self.assertEqual(bridge.run(['/private/tmp/probe'],timeout=5).returncode,77)
        with self.assertRaises(subprocess.CalledProcessError):bridge.run(['/private/tmp/probe'],check=True)
        self.assertEqual(len(bridge.calls),2);self.assertEqual(invoked[0][1],5)

    def test_rejects_unexpected_program_kwargs_and_invalid_timeout_before_child(self):
        def no_child(*args):self.fail('no subprocess authorized')
        bridge=Bridge('/private/tmp/probe',no_child)
        for argv,kw in ((['/bin/rm'],{}),(['/private/tmp/probe'],dict(timeout=True)),(['/private/tmp/probe'],dict(timeout=61))):
            with self.assertRaises(ValueError):bridge.run(argv,**kw)
        with self.assertRaises(TypeError):bridge.run(['/private/tmp/probe'],shell=True)

    def test_check_output_compatible_with_original_driver(self):
        bridge=Bridge('/private/tmp/probe',lambda *args:dict(returncode=0,stdout='acl result',stderr=''))
        self.assertEqual(bridge.check_output(['/bin/ls'],text=True),'acl result')
        self.assertEqual(bridge.check_output(['/bin/ls']),b'acl result')

    def test_directory_is_preserved_on_original_assertion_failure(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'original-fixture'
            with self.assertRaisesRegex(AssertionError,'original assertion'):
                with RetainedDirectory(path,prefix='unison-clone-stage-',dir='/private/tmp'):
                    (path/'sentinel').write_text('own original fixture')
                    raise AssertionError('original assertion')
            self.assertEqual((path/'sentinel').read_text(),'own original fixture')


if __name__=='__main__':unittest.main()
