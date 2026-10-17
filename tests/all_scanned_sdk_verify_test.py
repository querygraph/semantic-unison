import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import all_scanned_sdk_verify as verify
import all_scanned_sdk_prepare as prep
import all_scanned_sdk_prepare_test as preparation_controls
from shared_cpu_pool import UnresolvedOwnership


class Verification(unittest.TestCase):
    def fixture(self, root):
        helper = preparation_controls.Preparation()
        source, identity, digest = helper.setup_case(root)
        prepared = prep.prepare(source, identity, digest, root, clone=helper.fake_clone)
        return source, prepared, dict(bytes=identity['st_size'], sha256=digest)

    def test_fresh_pair_hash_epochs_and_roster_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source, prepared, expected = self.fixture(root)
            result = verify.verify_roots(root, prepared, source=expected)
            self.assertEqual(result['payload_read_bytes'], 2 * expected['bytes'])
            self.assertFalse(result['source_payload_opened'])
            self.assertFalse(result['resource_release_authorized'])
            self.assertEqual(prep.stamp(source.lstat()), prepared['source_identity'])

    def test_declared_hash_size_and_borrowed_alias_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, original, expected = self.fixture(root)
            for change in ('hash', 'size', 'alias', 'bool'):
                prepared = copy.deepcopy(original)
                if change == 'hash': prepared['replicas'][0]['sha256'] = 'f' * 64
                elif change == 'size': prepared['replicas'][0]['identity']['st_size'] += 1
                elif change == 'bool': prepared['replicas'][0]['identity']['st_size'] = True
                else:
                    prepared['source_identity']['st_ino'] = prepared['replicas'][0]['identity']['st_ino']
                with self.assertRaises(ValueError): verify.verify_roots(root, prepared, source=expected)

    def test_replaced_or_extra_entries_rejected_without_deleting(self):
        for change in ('replacement', 'extra', 'symlink'):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _, prepared, expected = self.fixture(root)
                path = root / 'left/image.dng'
                if change == 'extra': (root / 'left/unrelated').write_bytes(b'preserve')
                else:
                    path.rename(root / 'saved')
                    if change == 'replacement': path.write_bytes((root / 'saved').read_bytes())
                    else: path.symlink_to(root / 'saved')
                with self.assertRaises((ValueError, OSError)): verify.verify_roots(root, prepared, source=expected)
                self.assertTrue(path.exists())
                if change == 'extra': self.assertEqual((root / 'left/unrelated').read_bytes(), b'preserve')

    def test_cross_pair_mutation_during_last_read_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, prepared, expected = self.fixture(root)
            read = os.pread; calls = []
            def changing(fd, size, offset):
                value = read(fd, size, offset); calls.append(fd)
                if len(calls) == 2: (root / 'left/image.dng').write_bytes(b'changed fixture')
                return value
            with patch.object(verify.os, 'pread', side_effect=changing):
                with self.assertRaises(ValueError): verify.verify_roots(root, prepared, source=expected)

    def test_uncertain_close_is_not_success_or_numeric_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _, prepared, expected = self.fixture(root)
            original = verify.close_descriptors; calls = []
            held = UnresolvedOwnership('original modeled close uncertainty', uncertain_fd=987650)
            def uncertain(fds):
                calls.append(list(fds)); original(fds); raise held
            with patch.object(verify, 'close_descriptors', side_effect=uncertain):
                with self.assertRaises(UnresolvedOwnership) as caught:
                    verify.verify_roots(root, prepared, source=expected)
            self.assertIs(caught.exception, held)
            self.assertEqual(len(calls), 1)


if __name__ == '__main__': unittest.main()
