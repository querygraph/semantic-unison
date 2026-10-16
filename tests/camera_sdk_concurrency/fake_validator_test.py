"""Actual original helper processes with the production sanitized environment."""
import hashlib,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from synthetic_case import FILES,create_file
HELPER=Path(__file__).with_name('fake_validator.py')
class Sanitized(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='u-crs-env-',dir='/private/tmp')
        self.root=Path(self.tmp.name);self.root.chmod(0o700)
        self.case=self.root/'stock';self.case.mkdir(mode=0o700)
        self.right=self.case/'right';self.right.mkdir(mode=0o700)
    def tearDown(self):self.tmp.cleanup()
    def call(self,path,data):
        args=[str(HELPER),'--unison-dng-validation-v1','--expected-sha256',hashlib.sha256(data).hexdigest(),
              '--expected-size',str(len(data)),'--threads','1','--',str(path)]
        child=subprocess.Popen(args,env={'LANG':'C','LC_ALL':'C','PATH':'/usr/bin:/bin'},stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err=child.communicate()
        self.assertIsNotNone(child.returncode)
        return child.returncode,out,err
    def test_both_original_candidates_without_custom_environment(self):
        for name,data in FILES.items():
            path=self.right/name;create_file(path,data)
            code,out,err=self.call(path,data)
            self.assertEqual(code,0,err);self.assertIn(b'decode success',out)
            self.assertIn(hashlib.sha256(data).hexdigest().encode(),out)
    def test_outside_receiving_root_rejected(self):
        data=next(iter(FILES.values()));path=self.case/'outside.dng';create_file(path,data)
        self.assertNotEqual(self.call(path,data)[0],0)
    def test_symlink_candidate_rejected(self):
        data=next(iter(FILES.values()));path=self.right/'actual.dng';create_file(path,data)
        link=self.right/'link.dng';link.symlink_to(path)
        self.assertNotEqual(self.call(link,data)[0],0)
    def test_wrong_bytes_rejected(self):
        data=next(iter(FILES.values()));path=self.right/'wrong.dng';create_file(path,b'x'*len(data))
        self.assertNotEqual(self.call(path,data)[0],0)
    def test_nonprivate_directory_rejected(self):
        data=next(iter(FILES.values()));path=self.right/'one.dng';create_file(path,data);self.case.chmod(0o755)
        self.assertNotEqual(self.call(path,data)[0],0)
if __name__=='__main__':unittest.main()
