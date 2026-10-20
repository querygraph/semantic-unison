"""Execute an original fake compiler only; build-only must not create a fixture."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cached_benchmark.contract import ROOT
from private_camera_receiving.close import close_descriptors

FAKE = '''import json,os,sys
from pathlib import Path
fds=json.loads(os.environ['ORIGINAL_FAKE_FDS'])
observed=[dict(fd=fd,device=os.fstat(fd).st_dev,inode=os.fstat(fd).st_ino) for fd in fds]
assert len(observed)==9
with open(os.environ['ORIGINAL_FAKE_LOG'],'a') as out:
 out.write(json.dumps(dict(argv=sys.argv[1:],observed=observed))+'\\n')
if '-version' in sys.argv:print('original-fake-compiler-no-native-code')
if '-o' in sys.argv:Path(sys.argv[sys.argv.index('-o')+1]).write_bytes(b'original fake, never executed')
'''


class Inheritance(unittest.TestCase):
    def test_all_compiler_calls_inherit_exact_disposable_nine(self):
        with tempfile.TemporaryDirectory(prefix='cached-inheritance-',dir='/private/tmp') as tmp:
            root=Path(tmp);fake=root/'original-compiler';log=root/'compiler.jsonl'
            fake.write_text('#!'+sys.executable+'\n'+FAKE);fake.chmod(0o700)
            fds=tuple(os.open('/dev/null',os.O_RDONLY|os.O_CLOEXEC) for _ in range(9))
            try:
                expected=[dict(fd=fd,device=os.fstat(fd).st_dev,inode=os.fstat(fd).st_ino) for fd in fds]
                argv=[sys.executable,str(ROOT/'bench/semantic/run.py'),'--build-only','--keep-work',
                      '--work-parent',str(root),'--compiler','fake='+str(fake),
                      '--output',str(root/'RESULT.json'),'--inherited-resource-fds',','.join(map(str,fds))]
                child=subprocess.run(argv,pass_fds=fds,capture_output=True,text=True,timeout=30,
                    env=dict(os.environ,ORIGINAL_FAKE_FDS=json.dumps(fds),ORIGINAL_FAKE_LOG=str(log)))
                self.assertEqual(child.returncode,0,child.stdout+child.stderr)
                result=json.loads((root/'RESULT.json').read_text())
                self.assertTrue(result['build_complete']);self.assertFalse(result['measurement_complete'])
                self.assertEqual(result['inherited_resource_fds'],expected)
                calls=[json.loads(line) for line in log.read_text().splitlines()]
                self.assertGreater(len(calls),30)
                self.assertTrue(all(call['observed']==expected for call in calls))
                self.assertTrue(any('-version' in call['argv'] for call in calls))
                self.assertTrue(any('-o' in call['argv'] for call in calls))
                self.assertFalse((Path(result['retained_workspace'])/'synthetic.bin').exists())
                self.assertEqual(result['samples'],[])
            finally:
                close_descriptors(fds)


if __name__=='__main__':unittest.main()
