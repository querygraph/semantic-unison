"""Original in-memory capture controls, no subprocess or payload filesystem."""
import io
import unittest
from batch_artifacts import read
from batch_artifacts_test import MemoryStore
from batch_capture import BatchCapture as CapturedStream


class CaptureTests(unittest.TestCase):
    def test_invalid_utf8_is_preserved_as_original_bytes(self):
        store = MemoryStore(); raw = b'\xff\x00\xc0\x80stderr\n'
        capture = CapturedStream(io.BytesIO(raw))
        ref = capture.finish_artifact(store, 'stdout')
        self.assertEqual(read(store, ref), raw)
        with self.assertRaises(RuntimeError): capture.finish_raw()

    def test_overflow_drains_but_publishes_no_partial_artifact(self):
        store = MemoryStore(); stream = io.BytesIO(b'abcdef')
        capture = CapturedStream(stream, limit=3)
        with self.assertRaises(ValueError): capture.finish_artifact(store, 'stderr')
        self.assertTrue(stream.closed)
        self.assertEqual(store.files, {})
        self.assertEqual(capture.total, 6)

    def test_legacy_text_contract_keeps_truncation_visible(self):
        capture = CapturedStream(io.BytesIO(b'\xffab'), limit=2)
        self.assertEqual(capture.finish(), dict(bytes=3, truncated=True, text='\ufffda'))

    def test_close_error_is_not_retried(self):
        class CloseError(io.BytesIO):
            def close(self):
                self.attempts = getattr(self, 'attempts', 0) + 1
                super().close()
                raise OSError('injected uncertain close')
        stream = CloseError(b'x'); capture = CapturedStream(stream)
        with self.assertRaises(OSError): capture.finish_raw()
        with self.assertRaises(RuntimeError): capture.finish_raw()
        self.assertEqual(stream.attempts, 1)


if __name__ == '__main__': unittest.main()
