"""Original in-memory evidence controls: no payload/child/IO execution."""
import hashlib
import json
import unittest
from unittest.mock import patch
import batch_artifacts as artifacts


class MemoryStore:
    def __init__(self): self.files = {}
    def write(self, name, value):
        if name in self.files: raise FileExistsError(name)
        raw = json.dumps(value).encode()
        self.files[name] = raw
        return dict(name=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    def read(self, name, *, expected_sha256):
        raw = self.files[name]
        if hashlib.sha256(raw).hexdigest() != expected_sha256: raise ValueError('SHA')
        return raw
    def read_json(self, name, *, expected_sha256):
        return json.loads(self.read(name, expected_sha256=expected_sha256))


class ArtifactTests(unittest.TestCase):
    def test_binary_empty_and_chunk_boundary_roundtrip(self):
        for raw in (b'', b'\xff\x00\xfe', b'x' * artifacts.CHUNK_BYTES + b'y'):
            store = MemoryStore()
            reference = artifacts.publish(store, 'stdout', raw)
            self.assertEqual(artifacts.read(store, reference), raw)
            self.assertNotIn('base64', reference)

    def test_overflow_and_wrong_types_publish_nothing(self):
        for raw in ('replacement text', b'x' * (artifacts.MAX_BYTES + 1)):
            store = MemoryStore()
            with self.assertRaises(ValueError): artifacts.publish(store, 'stdout', raw)
            self.assertEqual(store.files, {})

    def test_tamper_and_false_length_refused(self):
        store = MemoryStore(); ref = artifacts.publish(store, 'stderr', b'abc')
        with self.assertRaises(ValueError): artifacts.read(store, dict(ref, bytes=True))
        with self.assertRaises(ValueError): artifacts.read(store, dict(ref, sha256='0' * 64))
        store.files[ref['chunks'][0]['name']] += b' '
        with self.assertRaises(ValueError): artifacts.read(store, ref)

    def test_uncertainty_propagates_without_retry_or_cleanup(self):
        store = MemoryStore(); marker = RuntimeError('owned uncertainty')
        with patch.object(store, 'write', side_effect=marker) as write:
            with self.assertRaises(RuntimeError) as raised:
                artifacts.publish(store, 'stdout', b'x')
            self.assertIs(raised.exception, marker)
            self.assertEqual(write.call_count, 1)


if __name__ == '__main__': unittest.main()
