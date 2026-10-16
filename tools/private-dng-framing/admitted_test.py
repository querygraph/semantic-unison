"""Fixed disposable metadata/mocked-child controls; no admitted camera read."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import admitted as a


def diagnostic():
    return {'schema': 'unison-private-framing-diagnostic/1', 'diagnostic_only': True,
            'semantic_eligibility': False, 'full_file_sha256_computed': False, 'sdk_validation': False,
            'native_nanosecond_epoch_fence_performed_by_child': False,
            'logical_read_bytes': 1, 'requested_read_bytes': 1, 'read_limit_bytes': a.LIMIT,
            'read_requests': 1, 'read_ranges': [{'offset': 0, 'length': 1}],
            'locator_completed': False, 'framing_recognized': False}


def plan(source, expected):
    return {'schema': 'unison-private-framing-input/1', 'source': {'path': str(source), 'identity': expected},
            'max_reads_each': a.LIMIT, 'diagnostic_seconds_each': 10,
            'programs': [{'label': label} for label in ('stock', 'ox')]}


class Controls(unittest.TestCase):
    def test_typed_source_and_fixed_scope(self):
        expected = dict.fromkeys(a.SOURCE_KEYS, 1)
        value = plan(a.SOURCE, expected)
        self.assertEqual(a.checked_plan(value), expected)
        for field, replacement in (('max_reads_each', float(a.LIMIT)), ('diagnostic_seconds_each', 11)):
            v = deepcopy(value); v[field] = replacement
            with self.assertRaises(ValueError): a.checked_plan(v)
        for change in ('source', 'typed', 'programs'):
            v = deepcopy(value)
            if change == 'source': v['source']['path'] = '/never-open-original'
            elif change == 'typed': v['source']['identity']['st_ino'] = True
            else: v['programs'].reverse()
            with self.assertRaises(ValueError): a.checked_plan(v)

    def test_held_path_native_epoch_and_mode(self):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name)/'fixture'; source.write_bytes(b'original'); source.chmod(0o400)
            expected = a.identity(os.lstat(source)); fd = os.open(source, os.O_RDONLY)
            try:
                a.check_input(fd, source, expected)
                os.utime(source, ns=(os.stat(source).st_atime_ns, expected['st_mtime_ns']+1))
                with self.assertRaises(ValueError): a.check_input(fd, source, expected)
            finally: os.close(fd)
            source.chmod(0o600); expected = a.identity(os.lstat(source)); fd = os.open(source, os.O_RDONLY)
            try:
                with self.assertRaises(ValueError): a.check_input(fd, source, expected)
            finally: os.close(fd)

    def test_diagnostic_claims_and_ranges(self):
        self.assertIs(a.validate_diagnostic(diagnostic(), 1)['semantic_eligibility'], False)
        for field in ('semantic_eligibility', 'full_file_sha256_computed', 'sdk_validation',
                      'native_nanosecond_epoch_fence_performed_by_child'):
            v = diagnostic(); v[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError): a.validate_diagnostic(v, 1)
        for change in ('negative', 'outside', 'count', 'sum', 'bool', 'cap'):
            v = diagnostic()
            if change == 'negative': v['read_ranges'][0]['offset'] = -1
            elif change == 'outside': v['read_ranges'][0]['offset'] = 1
            elif change == 'count': v['read_requests'] = 2
            elif change == 'sum': v['requested_read_bytes'] = v['logical_read_bytes'] = 2
            elif change == 'bool': v['read_requests'] = True
            else: v['requested_read_bytes'] = v['logical_read_bytes'] = a.LIMIT+1
            with self.subTest(change=change), self.assertRaises(ValueError): a.validate_diagnostic(v, 1)

    def test_no_admission_refuses_before_file_open(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(a.os, 'open') as opened:
            with self.assertRaises(KeyError): a.parent_gate()
            opened.assert_not_called()

    def test_program_byte_binding_without_execution(self):
        with tempfile.TemporaryDirectory() as name:
            base = Path(name); work = base/'stock'; work.mkdir(mode=0o700)
            binary = work/'private-framing-diagnostic'; binary.write_bytes(b'original inert test bytes')
            digest = a.hashlib.sha256(binary.read_bytes()).hexdigest()
            item = {'label': 'stock', 'path': str(binary), 'sha256': digest,
                    'build_report': {'path': '/fake-report', 'sha256': '0'*64}}
            report = {'schema': 'unison-private-framing-cli-controls/1', 'complete': True,
                'workspace': str(base), 'source_sha256': {str(a.ROOT/p):
                    a.hashlib.sha256((a.ROOT/p).read_bytes()).hexdigest() for p in a.PROGRAM_SOURCES},
                'builds': [{'compiler_label': 'stock', 'returncode': 0, 'binary': str(binary),
                            'binary_sha256': digest}]}
            with patch.object(a, 'read_manifest', return_value=report), \
                    patch.object(a.subprocess, 'run', side_effect=AssertionError('unexpected execution')):
                self.assertEqual(a.checked_program(item), binary)
                binary.write_bytes(b'different inert test bytes')
                with self.assertRaises(ValueError): a.checked_program(item)

    def test_parent_binding_and_one_use_marker(self):
        with tempfile.TemporaryDirectory() as name:
            workspace = Path(name); command = [sys.executable, str(Path(a.__file__)), '--plan', '/fixed']
            adm = {'state': 'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB', 'target': 'private-dng-framing-input',
                   'command': command, 'workspace': str(workspace)}
            environment = {'SHARED_IO_ADMISSION': '/fake', 'SHARED_IO_ADMISSION_SHA256': '0'*64}
            attempt = {'owner_pid': os.getppid(), 'target': adm['target'], 'command': command,
                       'admission': {'path': '/fake', 'sha256': '0'*64}}
            marker = workspace/'SHARED-IO-ATTEMPT.json'; marker.write_text(json.dumps(attempt))
            with patch.dict(os.environ, environment), patch.object(a, 'read_manifest', return_value=adm), \
                    patch.object(sys, 'argv', [str(Path(a.__file__)), '--plan', '/fixed']):
                a.parent_gate()
                with self.assertRaises(FileExistsError): a.parent_gate()
                marker.write_text(json.dumps(dict(attempt, owner_pid=-1)))
                with self.assertRaises(ValueError): a.parent_gate()

    def exercise_main(self, mutation=False, timeout=False):
        with tempfile.TemporaryDirectory() as name:
            source = Path(name)/'fixture'; source.write_bytes(b'original'); source.chmod(0o400)
            expected = a.identity(os.lstat(source)); value = plan(source, expected)
            output = io.StringIO(); fds = []
            def child(command, *, stdin, **kwargs):
                fds.append(stdin)
                if timeout: raise subprocess.TimeoutExpired(command, 10)
                if mutation:
                    os.utime(source, ns=(os.stat(source).st_atime_ns, expected['st_mtime_ns']+1))
                return types.SimpleNamespace(returncode=0, stdout=json.dumps(diagnostic()).encode(), stderr=b'')
            with patch.object(a, 'SOURCE', source), patch.object(a, 'parent_gate'), \
                    patch.object(a, 'read_manifest', return_value=value), \
                    patch.object(a, 'checked_program', return_value=Path('/never-executed')), \
                    patch.object(a.subprocess, 'run', side_effect=child), \
                    patch.object(sys, 'argv', ['worker', '--plan', '/fake', '--plan-sha256', '0'*64]), \
                    redirect_stdout(output):
                if mutation or timeout:
                    with self.assertRaises((ValueError, subprocess.TimeoutExpired)): a.main()
                else: a.main()
            result = json.loads(output.getvalue())
            self.assertEqual(result['complete'], not (mutation or timeout))
            self.assertEqual(len(fds), 1 if mutation or timeout else 2)
            for fd in set(fds):
                with self.assertRaises(OSError): os.fstat(fd)
            if not (mutation or timeout):
                self.assertTrue(result['source_native_epoch_verified'])
                self.assertFalse(result['source_sha256_computed'])
                self.assertEqual(result['total_logical_read_bytes'], 2)

    def test_two_mock_children_and_descriptor_close(self):
        self.exercise_main()

    def test_mutation_stops_before_second_child(self):
        self.exercise_main(mutation=True)

    def test_timeout_stops_before_second_child(self):
        self.exercise_main(timeout=True)


if __name__ == '__main__': unittest.main()
