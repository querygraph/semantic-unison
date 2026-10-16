"""Fixed local artifact/refusal controls; no inspector/compiler/image execution."""
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('inspector_driver', Path(__file__).with_name('run.py'))
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class ReuseControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unison-inspector-reuse-controls-')
        self.work = Path(self.temp.name)
        self.work.chmod(0o700)
        self.binary = self.work / 'semantic-inspect'
        self.binary.write_bytes(b'original inert test artifact; never executed')
        self.receipt = self.work / 'build.json'
        self.value = {'schema': 'unison-semantic-inspector-build/1', 'complete': True,
                      'build_only': True, 'build_exit': 0, 'workspace': str(self.work),
                      'binary': str(self.binary), 'binary_sha256': driver.sha(self.binary),
                      'source_sha256': {str(p): driver.sha(driver.ROOT / p) for p in driver.SOURCES}}
        self.save(self.value)

    def save(self, value):
        self.receipt.write_text(json.dumps(value))

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_build_and_verbatim_argv_without_compiler_or_workspace(self):
        self.assertEqual(driver.checked_inspector(self.receipt), self.binary)
        argv = ['inspector', '--use-build', str(self.receipt), '--', '--profile',
                'org.firstpair.dng-xmp/1', '/NEVER-READ input.dng']
        with patch.object(sys, 'argv', argv), patch.object(driver.shutil, 'which', side_effect=AssertionError('compiler lookup')), \
                patch.object(driver.tempfile, 'mkdtemp', side_effect=AssertionError('new build')), \
                patch.object(driver.subprocess, 'run', return_value=SimpleNamespace(returncode=7)) as run:
            self.assertEqual(driver.main(), 7)
            run.assert_called_once_with([str(self.binary)] + argv[4:])

    def test_stale_binary_refused(self):
        self.binary.write_bytes(b'changed artifact')
        with self.assertRaises(ValueError):
            driver.checked_inspector(self.receipt)

    def test_changed_source_pin_refused(self):
        value = copy.deepcopy(self.value)
        value['source_sha256']['src/xmpMerge.ml'] = '0' * 64
        self.save(value)
        with self.assertRaises(ValueError):
            driver.checked_inspector(self.receipt)

    def test_incomplete_or_wrong_schema_and_source_set_refused(self):
        for change in ({'complete': False}, {'build_only': False}, {'build_exit': False},
                       {'schema': 'unknown'}, {'source_sha256': {}}, {'binary': 'relative'}):
            with self.subTest(change=change):
                self.save(dict(self.value, **change))
                with self.assertRaises(ValueError):
                    driver.checked_inspector(self.receipt)

    def test_duplicate_and_oversized_receipts_refused(self):
        for raw in ('{"schema":1,"schema":2}', '[]', ' ' * 65537):
            self.receipt.write_text(raw)
            with self.assertRaises(ValueError):
                driver.checked_inspector(self.receipt)

    def test_symlink_receipt_refused(self):
        alias = self.work / 'alias.json'
        alias.symlink_to(self.receipt)
        with self.assertRaises(OSError):
            driver.checked_inspector(alias)

    def test_shared_workspace_refused(self):
        self.work.chmod(0o755)
        with self.assertRaises(ValueError):
            driver.checked_inspector(self.receipt)

    def test_reuse_cannot_request_build_side_effects(self):
        for extra in (['--build-only'], ['--report', '/NEVER-CREATED']):
            with patch.object(sys, 'argv', ['inspector', '--use-build', str(self.receipt)] + extra), \
                    patch.object(sys, 'stderr', io.StringIO()), \
                    patch.object(driver, 'checked_inspector', side_effect=AssertionError('artifact read')):
                with self.assertRaises(SystemExit) as error:
                    driver.main()
                self.assertEqual(error.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
