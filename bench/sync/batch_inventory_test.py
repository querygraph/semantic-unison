import unittest
from batch_artifacts_test import MemoryStore
from batch_inventory import save, load, validate


def row(index=0):
    return dict(path=f'group-{index//64:03d}/image-{index:05d}.dng', before_present=True,
                before_sha256='a'*64, target_sha256='b'*64, target_bytes=32768,
                expected_class='semantic-update')


class InventoryTests(unittest.TestCase):
    def test_thousand_file_roundtrip_preserves_all_entries(self):
        rows = [row(i) for i in range(4096)]
        store = MemoryStore(); ref = save(store, 'inventory', rows)
        self.assertEqual(load(store, ref), rows)
        self.assertGreater(len(ref['shards']), 1)

    def test_new_has_no_fabricated_basis(self):
        value = dict(row(), before_present=False, before_sha256=None, expected_class='new-file')
        self.assertEqual(validate([value]), [value])
        with self.assertRaises(ValueError): validate([dict(value, before_sha256='a'*64)])

    def test_unchanged_duplicate_path_and_bool_extent_refuse(self):
        for rows in ([row(), row()], [dict(row(), target_sha256='a'*64)],
                     [dict(row(), target_bytes=True)], [dict(row(), path='../image.dng')]):
            with self.assertRaises(ValueError): validate(rows)


if __name__ == '__main__': unittest.main()
