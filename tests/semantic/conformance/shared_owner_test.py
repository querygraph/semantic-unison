"""Inert-child controls for compiler wait uncertainty; no compiler execution."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock,patch
spec=importlib.util.spec_from_file_location('sde_shared_owner',Path(__file__).with_name('shared.py'))
owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)


class Retained(BaseException):pass


class Controls(unittest.TestCase):
    def test_actual_wait_status_is_preserved_without_retention(self):
        for code in (0,7,-15):
            child=Mock(pid=999001);child.wait.return_value=code
            with patch.object(owner,'retain_after_record') as retain:
                self.assertEqual(owner.wait_owned_child(child,timeout=50,record=self.fail),code)
            child.wait.assert_called_once_with(timeout=50);retain.assert_not_called()
    def test_timeout_and_interruption_retain_before_return_or_second_wait(self):
        for error in (subprocess.TimeoutExpired(['original-fake'],50),KeyboardInterrupt(),OSError('original wait refused')):
            child=Mock(pid=999002);child.wait.side_effect=error;records=[]
            def retained(record):
                record();raise Retained()
            with patch.object(owner,'retain_after_record',side_effect=retained):
                with self.assertRaises(Retained):owner.wait_owned_child(child,timeout=50,record=records.append)
            child.wait.assert_called_once_with(timeout=50)
            child.kill.assert_not_called();child.terminate.assert_not_called();child.poll.assert_not_called()
            self.assertEqual(records[0]['child_pid'],999002)
            self.assertFalse(records[0]['direct_child_wait_proved'])
            self.assertFalse(records[0]['resource_release_authorized'])
            self.assertIn(repr(error),records[0]['error'])


if __name__=='__main__':unittest.main()
