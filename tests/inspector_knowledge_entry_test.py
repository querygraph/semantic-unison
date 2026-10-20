"""Original entry controls; fake dispatcher, no IO pool or image reads."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import inspector_knowledge_entry as entry

class Entry(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.output=Path(self.temp.name)/'new'
        self.env=dict(SHARED_CPU_CREDITS='8',INSPECTOR_RECEIPT='/inert/components.json',
            INSPECT_INPUT='/inert/input.dng',EXIFTOOL_BUILD='/inert/bridge.json',
            OUTPUT_DIR=str(self.output),SHARED_IO_ADMISSION='/inert/admission.json',
            SHARED_IO_ADMISSION_SHA256='a'*64)
    def tearDown(self):self.temp.cleanup()
    def invoke(self):
        def run(target,argv,output,credits,**kwargs):
            self.assertEqual((target,credits),('inspect-file',8))
            self.assertEqual(output,self.output)
            self.assertTrue(output.is_dir());self.assertEqual(output.stat().st_mode & 0o777,0o700)
            self.assertEqual(argv[4:6],['--exiftool-build','/inert/bridge.json'])
            self.assertEqual(argv[-3:],['--','--components','/inert/input.dng'])
            return 0
        with patch.dict(os.environ,self.env,clear=True),patch.object(entry,'run',side_effect=run) as called:
            result=entry.main();self.assertEqual(called.call_count,1);return result
    def test_creates_private_receipt_directory(self):self.assertEqual(self.invoke(),0)
    def test_existing_directory_refused(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):self.invoke()
    def test_missing_environment_refused_before_directory(self):
        del self.env['EXIFTOOL_BUILD']
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.output.exists())
    def test_relative_path_refused_before_directory(self):
        self.env['INSPECT_INPUT']='relative.dng'
        with self.assertRaises(ValueError):self.invoke()
        self.assertFalse(self.output.exists())
if __name__=='__main__':unittest.main()
