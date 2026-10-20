"""Pure manual inspector command controls; no files/payload/processes opened."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import manual
class Commands(unittest.TestCase):
 def environment(self,**extra):
  return dict(SHARED_CPU_CREDITS='8',INSPECTOR_RECEIPT='/private/tmp/inert-build.json',INSPECT_INPUT='/private/tmp/inert-input.dng',**extra)
 def command(self,**extra):
  with patch.object(Path,'open',side_effect=AssertionError('no file IO')),patch.object(Path,'read_bytes',side_effect=AssertionError('no artifact read')):
   return manual.command('inspect-file',Path('/private/tmp/inert-output'),self.environment(**extra))
 def test_default_unchanged(self):self.assertEqual(self.command()[-3:],['--profile','org.firstpair.dng-xmp/1','/private/tmp/inert-input.dng'])
 def test_components(self):self.assertEqual(self.command(INSPECT_COMPONENTS='1')[-2:],['--components','/private/tmp/inert-input.dng'])
 def test_components_base(self):self.assertEqual(self.command(INSPECT_COMPONENTS='1',INSPECT_BASE='/private/tmp/inert-base.dng')[-4:],['--components','--base','/private/tmp/inert-base.dng','/private/tmp/inert-input.dng'])
 def test_explicit_off(self):self.assertEqual(self.command(INSPECT_COMPONENTS='0'),self.command())
 def test_profile_preserved(self):self.assertEqual(self.command(INSPECT_PROFILE='org.firstpair.dng-xmp/0')[-2],'org.firstpair.dng-xmp/0')
 def test_invalid_bool(self):
  with self.assertRaises(ValueError):self.command(INSPECT_COMPONENTS='true')
 def test_mixed_mode(self):
  with self.assertRaises(ValueError):self.command(INSPECT_COMPONENTS='1',INSPECT_PROFILE='org.firstpair.dng-xmp/1')
 def test_relative_base(self):
  with self.assertRaises(ValueError):self.command(INSPECT_COMPONENTS='1',INSPECT_BASE='relative.dng')
if __name__=='__main__':unittest.main()
