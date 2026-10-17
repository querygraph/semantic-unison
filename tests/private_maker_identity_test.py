"""Disposable authored bytes only; never execute on the retained camera file."""
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import private_maker_identity as model
from private_maker_slice import stamp
from shared_cpu_pool import UnresolvedOwnership


def shape():
    # Original synthetic table with the exact candidate shape, not saved bytes.
    rows = [dict(tag=i, type=4, count=1, value_bytes=4, out_of_line=False,
                 payload_relative_offset=None, declared_extent_within_payload=None,
                 private_pointer_semantics_verified=False) for i in range(33)]
    rows[21].update(type=2, count=9, value_bytes=9, out_of_line=True,
                    payload_relative_offset=450, declared_extent_within_payload=True)
    return dict(schema='unison-private-maker-candidate-shape/1', entries=rows,
                semantic_eligibility=False, private_reference_closure_proved=False)


class Model(unittest.TestCase):
    def fixture(self, root):
        p = Path(root) / 'authored-only'
        p.write_bytes(b'\0' * 11440 + b'MODEL123\0')
        p.chmod(0o400)
        return dict(path=str(p), identity=stamp(os.lstat(p)))

    def test_exact_selection_and_no_vendor_authority(self):
        self.assertEqual(model.selected_field(shape()), dict(tag=21, offset=11440, bytes=9))
        result = model.interpret(b'MODEL123\0')
        self.assertEqual(result['candidate_text'], 'MODEL123')
        for key in ('maker_format_recognized', 'private_reference_closure_proved', 'semantic_eligibility'):
            self.assertIs(result[key], False)

    def test_invalid_text_preserved_without_decoding_or_reclassification(self):
        for raw in (b'123456789', b'\0'*9, b'A\0BCDEFG\0', b'\xffBCDEFGH\0', b'        \0'):
            result = model.interpret(raw)
            self.assertIsNone(result['candidate_text'])
            self.assertEqual(result['raw_hex'], raw.hex())
        for raw in (b'', b'a'*10, bytearray(b'MODEL123\0')):
            with self.assertRaises(ValueError): model.interpret(raw)

    def test_changed_type_count_offset_and_ambiguous_geometry_refused(self):
        for key, value in (('type', 7), ('count', 8), ('payload_relative_offset', 451)):
            bad = shape(); bad['entries'][21][key] = value
            with self.assertRaises(ValueError): model.selected_field(bad)
        bad = shape(); bad['entries'][20] = copy.deepcopy(bad['entries'][21])
        with self.assertRaises(ValueError): model.selected_field(bad)

    def test_one_nine_byte_read_and_actual_close(self):
        with tempfile.TemporaryDirectory() as root:
            source = self.fixture(root); actual = os.pread; calls = []
            def read(fd, count, offset):
                calls.append((count, offset)); return actual(fd, count, offset)
            with patch.object(model.os, 'pread', side_effect=read):
                result = model.read_candidate(source, shape(), deadline=time.monotonic()+2)
            self.assertEqual(calls, [(9, 11440)])
            self.assertTrue(result['fd_closure_proved_by_return'])
            self.assertEqual(stamp(os.lstat(source['path'])), source['identity'])

    def test_stale_epoch_and_expired_deadline_do_not_read(self):
        with tempfile.TemporaryDirectory() as root:
            source = self.fixture(root)
            with patch.object(model.os, 'pread', side_effect=AssertionError('unexpected read')):
                with self.assertRaises(ValueError):
                    model.read_candidate(source, shape(), deadline=time.monotonic()-1)
                source['identity']['st_ino'] += 1
                with self.assertRaises(ValueError):
                    model.read_candidate(source, shape(), deadline=time.monotonic()+2)

    def test_short_read_and_read_error_close_owned_descriptor(self):
        with tempfile.TemporaryDirectory() as root:
            source = self.fixture(root); actual_close = model.close_descriptors
            for error in (b'x', OSError('injected pread failure')):
                with patch.object(model.os, 'pread', side_effect=error if isinstance(error, Exception) else None,
                                  return_value=error if isinstance(error, bytes) else None), \
                     patch.object(model, 'close_descriptors', wraps=actual_close) as close:
                    with self.assertRaises((ValueError, OSError)):
                        model.read_candidate(source, shape(), deadline=time.monotonic()+2)
                    self.assertEqual(close.call_count, 1)

    def test_uncertain_close_preserves_read_failure_and_never_retries(self):
        from private_camera_receiving import close as cleanup
        with tempfile.TemporaryDirectory() as root:
            source = self.fixture(root); observed = []; info = os.lstat(source['path'])
            def fail(fd):
                observed.append(fd)
                raise OSError('injected before any OS close attempt')
            # Entirely fictitious descriptor: no real close/retry or process
            # ownership is inferred from this uncertainty-injection fixture.
            with patch.object(model.os, 'open', return_value=900), \
                 patch.object(model.os, 'fstat', return_value=info), \
                 patch.object(model.os, 'pread', side_effect=OSError('original read failure')), \
                 patch.object(cleanup.os, 'close', side_effect=fail):
                with self.assertRaises(UnresolvedOwnership) as caught:
                    model.read_candidate(source, shape(), deadline=time.monotonic()+2)
            self.assertEqual(observed, [900])
            self.assertEqual(caught.exception.uncertain_closes[0]['fd'], 900)
            self.assertIn('original read failure', repr(caught.exception.original_failure))


if __name__ == '__main__': unittest.main()
