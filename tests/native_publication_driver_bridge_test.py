import subprocess,tempfile,unittest
from pathlib import Path
from native_publication_driver_bridge import Commands,Temporary,driver_source
class Controls(unittest.TestCase):
 def test_command_binding_and_normal_failed_child(self):
  seen=[]
  def invoke(argv,env,cwd,seconds):seen.append((argv,env,cwd,seconds));return dict(returncode=2,stdout='original',stderr='designated')
  bridge=Commands('/compiler','/private/tmp/work',invoke)
  result=bridge.run(['/private/tmp/work/publication-test'],cwd='/private/tmp/work',text=True,capture_output=True,timeout=60)
  self.assertEqual((result.returncode,result.stdout,result.stderr),(2,'original','designated'))
  with self.assertRaises(subprocess.CalledProcessError):bridge.run(['/compiler','-bad'],check=True)
  for argv,cwd in [(['/other'],None),(['/compiler'],'/other')]:
   with self.assertRaises(ValueError):bridge.run(argv,cwd=cwd)
  self.assertEqual(len(seen),2)
 def test_output_and_original_environment_forwarding(self):
  seen=[]
  def invoke(argv,env,cwd,seconds):seen.append(env);return dict(returncode=0,stdout='library\n',stderr='')
  bridge=Commands('/compiler','/private/tmp/work',invoke)
  self.assertEqual(bridge.check_output(['/compiler','-where'],text=True,env={'original':'environment'}),'library\n');self.assertEqual(seen,[{'original':'environment'}])
 def test_retained_directory_never_automatically_removes_fixture(self):
  with tempfile.TemporaryDirectory() as parent:
   path=Path(parent)/'retained';proxy=Temporary(path,'original-')
   with self.assertRaisesRegex(ValueError,'known original failure'):
    with proxy.TemporaryDirectory(prefix='original-',dir='/private/tmp') as directory:
     (Path(directory)/'evidence').write_bytes(b'original');raise ValueError('known original failure')
   self.assertEqual((path/'evidence').read_bytes(),b'original')
   with self.assertRaises(ValueError):proxy.mkdtemp(prefix='original-',dir='/private/tmp')
 def test_driver_body_only_loses_two_exact_imports(self):
  source='import subprocess\nimport tempfile\noriginal_body()\n';self.assertEqual(driver_source(source),'original_body()\n')
  with self.assertRaises(ValueError):driver_source(source+'import subprocess\n')
if __name__=='__main__':unittest.main()
