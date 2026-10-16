"""Adobe-free metadata-only refusals; no DNG or clone invocation."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import private_dng_copy as control


class Controls(unittest.TestCase):
    def test_source_identity_includes_mode_and_nlink(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'inert'
            p.write_bytes(b'x')
            fd = os.open(p, os.O_RDONLY)
            try:
                plan = {'source': {'path': str(p), 'identity': control.identity(os.fstat(fd))}}
                control.source_check(plan, fd)
                plan['source']['identity']['st_nlink'] = 2
                with self.assertRaises(ValueError):
                    control.source_check(plan, fd)
            finally:
                os.close(fd)

    def test_metadata_symlink_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'metadata'
            p.write_text('{}')
            link = Path(temp) / 'link'
            link.symlink_to(p)
            with self.assertRaises(OSError):
                control.load(link)

    def test_metadata_oversize_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'metadata'
            p.write_bytes(b' ' * 262145)
            with self.assertRaises(ValueError):
                control.load(p)

    def test_admission_binds_command_and_read_budget(self):
        admission = {'state': 'ROOT_ADMITTED_ONE_PRIVATE_DNG_IO_CONTROL',
                     'plan_sha256': 'digest', 'command': [control.sys.executable,
                     str(Path(control.__file__).resolve()), '--plan', '/plan',
                     '--io-admission', '/admission'], 'start_deadline_unix': 200,
                     'accepts_uninstrumented_inspector_logical_read_budget': True}
        with patch.object(control, 'load', return_value=admission), \
             patch.object(control, 'sha', return_value='digest'), \
             patch.object(control.time, 'time', return_value=100):
            control.check_admission('/plan', '/admission')
            for key, wrong in [('plan_sha256', 'wrong'), ('command', []),
                               ('start_deadline_unix', 99),
                               ('accepts_uninstrumented_inspector_logical_read_budget', False)]:
                original = admission[key]
                admission[key] = wrong
                with self.assertRaises(ValueError):
                    control.check_admission('/plan', '/admission')
                admission[key] = original

    def test_wrong_plan_schema_before_pins(self):
        with self.assertRaises(ValueError):
            control.preflight({'schema': 'unknown'})


if __name__ == '__main__':
    unittest.main()
