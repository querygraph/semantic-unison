import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import all_scanned_sdk_prepare as prep
from shared_cpu_pool import UnresolvedOwnership


class Preparation(unittest.TestCase):
    def setup_case(self, root):
        source = root / 'retained.dng'; source.write_bytes(b'original disposable toy')
        source.chmod(0o400)
        for side in ('left', 'right'): (root / side).mkdir(mode=0o700)
        return source, prep.stamp(source.lstat()), hashlib.sha256(source.read_bytes()).hexdigest()

    @staticmethod
    def fake_clone(source, directory, name):
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        try:
            data = os.pread(source, os.fstat(source).st_size, 0)
            assert os.write(fd, data) == len(data)
        finally: os.close(fd)

    def test_pair_independent_inodes_exact_hash_and_source_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, identity, digest = self.setup_case(root)
            result = prep.prepare(source, identity, digest, root, clone=self.fake_clone)
            self.assertEqual(prep.stamp(source.lstat()), identity)
            rows = result['replicas']
            self.assertEqual(len({r['identity']['st_ino'] for r in rows}), 2)
            self.assertEqual(result['clone_read_bytes'], 2 * identity['st_size'])
            self.assertEqual(result['backend'], 'original-disposable-test-double')
            self.assertTrue(all(r['sha256'] == digest for r in rows))

    def test_clone_refusal_has_no_fallback_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, identity, digest = self.setup_case(root)
            calls = []
            def refuse(*args): calls.append(args); raise OSError('native refusal')
            with self.assertRaises(OSError): prep.prepare(source, identity, digest, root, clone=refuse)
            self.assertEqual(len(calls), 1)
            self.assertFalse((root / 'left/image.dng').exists())
            (root / 'left/image.dng').write_bytes(b'preserve')
            with self.assertRaises(ValueError): prep.prepare(source, identity, digest, root, clone=refuse)
            self.assertEqual(len(calls), 1)
            self.assertEqual((root / 'left/image.dng').read_bytes(), b'preserve')

    def test_wrong_digest_preserves_partial_and_never_starts_right(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, identity, _ = self.setup_case(root)
            with self.assertRaises(ValueError): prep.prepare(source, identity, 'f' * 64, root, clone=self.fake_clone)
            self.assertTrue((root / 'left/image.dng').exists())
            self.assertFalse((root / 'right/image.dng').exists())
            self.assertEqual(prep.stamp(source.lstat()), identity)

    def test_close_uncertainty_preserves_original_carrier_without_numeric_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, identity, digest = self.setup_case(root)
            original_close = prep.close_descriptors; calls = []
            held = UnresolvedOwnership('original modeled close uncertainty', uncertain_fd=987654)
            def uncertain(fds):
                calls.append(list(fds)); original_close(fds); raise held
            with patch.object(prep, 'close_descriptors', side_effect=uncertain):
                with self.assertRaises(UnresolvedOwnership) as caught:
                    prep.prepare(source, identity, digest, root, clone=self.fake_clone)
            self.assertIs(caught.exception, held)
            self.assertEqual(len(calls), 1)


if __name__ == '__main__': unittest.main()
