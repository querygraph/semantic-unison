"""Original tiny generated replica controls; no Unison/Photo/native execution."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from batch_verify import verify
from workload_fixtures import create, create_corpus, edit


class ReplicaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='unison-corpus-verifier-')
        self.root = Path(self.temp.name)
        self.group = self.root / 'group-004'; self.group.mkdir(mode=0o700)
        self.file = self.group / 'image-00256.dng'
        self.metadata = create_corpus(self.file, 32768, 512, 256)
        before = self.metadata['before_sha256']
        after = edit(self.file, self.metadata, 'fixed-xmp')
        self.rows = [dict(path='group-004/image-00256.dng', before_present=True,
                          before_sha256=before, target_sha256=after, target_bytes=32768,
                          expected_class='semantic-update')]

    def tearDown(self): self.temp.cleanup()

    def test_exact_target_and_legacy_seed_limit(self):
        observed = verify(self.root, self.rows, phase='target')
        self.assertEqual(observed[0]['sha256'], self.rows[0]['target_sha256'])
        with self.assertRaises(ValueError): create(self.group/'legacy.dng', 32768, 512, 256)
        self.assertFalse((self.group/'legacy.dng').exists())

    def test_wrong_phase_hash_and_extra_file_refuse(self):
        with self.assertRaises(ValueError): verify(self.root, self.rows, phase='before')
        (self.group/'extra').write_bytes(b'x')
        with self.assertRaises(ValueError): verify(self.root, self.rows, phase='target')

    def test_alias_and_symlink_refuse(self):
        alias = self.root/'alias'; os.link(self.file, alias)
        with self.assertRaises(ValueError): verify(self.root, self.rows, phase='target')
        alias.unlink()
        self.file.unlink(); self.file.symlink_to('/dev/null')
        with self.assertRaises((OSError, ValueError)): verify(self.root, self.rows, phase='target')

    def test_empty_before_addition_is_verified_without_fabricated_basis(self):
        self.file.unlink(); self.group.rmdir()
        row = dict(self.rows[0], before_present=False, before_sha256=None, expected_class='new-file')
        self.assertEqual(verify(self.root, [row], phase='before'), [])
        with self.assertRaises(ValueError): verify(self.root, [row], phase='target')


if __name__ == '__main__': unittest.main()
