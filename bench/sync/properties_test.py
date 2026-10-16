"""Fixed native metadata controls on original four-byte disposable files only."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import properties as p
from run import selected_property_flags


class ArgumentControls(unittest.TestCase):
    def test_property_values_cannot_be_anonymous_roots(self):
        flags=selected_property_flags()
        self.assertEqual(flags,['-rsrc=true','-xattrs=true','-perms=0o777'])
        self.assertTrue(all(flag.startswith('-') and '=' in flag for flag in flags))


@unittest.skipUnless(sys.platform == 'darwin', 'native ResourceFork fixture requires Darwin')
class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='unison-property-controls-')
        self.path=Path(self.tmp.name)/'original-generated'
        self.path.write_bytes(b'abcd')
    def tearDown(self):self.tmp.cleanup()
    def test_initial_native_fork_xattr_and_mode(self):
        p.initialise(self.path);p.verify_initial(self.path)
        self.assertEqual(self.path.read_bytes(),b'abcd')
    def test_removal_does_not_modify_data(self):
        p.initialise(self.path);p.remove_source(self.path);p.verify_removed(self.path)
        self.assertEqual(self.path.read_bytes(),b'abcd')
    def test_old_reader_survives_name_replacement(self):
        p.initialise(self.path)
        with self.path.open('rb') as reader:
            before=p.old_reader_snapshot(reader.fileno())
            replacement=Path(self.tmp.name)/'replacement';replacement.write_bytes(b'efgh')
            p.initialise(replacement);p.remove_source(replacement)
            replacement.replace(self.path)
            self.assertEqual(p.old_reader_snapshot(reader.fileno()),before)
            self.assertEqual(self.path.read_bytes(),b'efgh');p.verify_removed(self.path)
    def test_in_place_mutation_detected(self):
        p.initialise(self.path)
        with self.path.open('rb') as reader:
            before=p.old_reader_snapshot(reader.fileno())
            self.path.write_bytes(b'efgh')
            self.assertNotEqual(p.old_reader_snapshot(reader.fileno()),before)
    def test_nonempty_inherited_fork_rejected(self):
        p.initialise(self.path);p.remove_source(self.path)
        os.chmod(self.path,0o600);p.set_attribute(self.path,p.FORK,p.OLD_FORK);os.chmod(self.path,0o400)
        with self.assertRaises(ValueError):p.verify_removed(self.path)
    def test_inherited_xattr_rejected(self):
        p.initialise(self.path);p.remove_source(self.path)
        os.chmod(self.path,0o600);p.set_attribute(self.path,p.NAME,p.OLD_VALUE);os.chmod(self.path,0o400)
        with self.assertRaises(ValueError):p.verify_removed(self.path)
    def test_fd_path_native_attribute_binding_and_read_bound(self):
        value=b'a\0b'
        p.set_attribute(self.path,p.NAME,value)
        with self.path.open('rb') as reader:
            self.assertEqual(p.attribute(reader.fileno(),p.NAME),value)
            self.assertEqual(p.attribute(self.path,p.NAME),value)
        p.set_attribute(self.path,p.NAME,b'x'*(p.MAX_ATTRIBUTE+1))
        with self.assertRaises(ValueError):p.attribute(self.path,p.NAME)

    def test_noop_mode_or_attribute_change_rejected(self):
        p.initialise(self.path);p.remove_source(self.path);before=p.noop_snapshot(self.path)
        os.chmod(self.path,0o600)
        with self.assertRaises(ValueError):p.noop_snapshot(self.path)
        p.set_attribute(self.path,p.NAME,b'changed');os.chmod(self.path,0o400)
        with self.assertRaises(ValueError):p.noop_snapshot(self.path)
        self.assertEqual(before['st_mode'] & 0o777,0o400)

if __name__=='__main__':unittest.main()
