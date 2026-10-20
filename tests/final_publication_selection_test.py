"""Argument-only controls: no compile, transfer, pool or fixture IO."""
import contextlib
import io
import unittest
from unittest.mock import patch
import test_final_publication as runner

class Selection(unittest.TestCase):
    def args(self,*extra):
        return runner.arguments(['/inert/build','--ocamlopt','/inert/ocamlopt',*extra])
    def refused(self,*extra):
        with patch.object(runner.tempfile,'mkdtemp',side_effect=AssertionError('no workspace')),contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:self.args(*extra)
        self.assertEqual(error.exception.code,2)
    def test_missing_peer(self):self.refused('--only','old-peer')
    def test_unknown_selection(self):self.refused('--only','typo')
    def test_conflicting_selection(self):self.refused('--only','observe','--negative-control','resolution')
    def test_peer_selected(self):self.assertEqual(self.args('--only','old-peer','--old-peer','/inert/old').only,'old-peer')
    def test_default(self):self.assertIsNone(self.args().only)
    def test_normal_selection(self):self.assertEqual(self.args('--only','resume-prefix').only,'resume-prefix')
    def test_negative(self):self.assertEqual(self.args('--negative-control','resolution').negative_control,'resolution')
if __name__=='__main__':unittest.main()
