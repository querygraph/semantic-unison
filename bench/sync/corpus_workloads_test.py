"""Original metadata-only corpus controls; never create thousands of payloads."""
import unittest
from corpus_workloads import plan


class CorpusTests(unittest.TestCase):
    def test_thousands_small_are_unique_and_have_exact_byte_budget(self):
        value=plan('many-small')
        self.assertEqual(len(value.files),4096)
        self.assertEqual(len({x.relative_path for x in value.files}),4096)
        self.assertEqual([x.seed_index for x in value.files],list(range(4096)))
        self.assertTrue(all(x.before_present and x.semantic_update_expected for x in value.files))
        self.assertEqual(value.generated_target_bytes,134217728)
        self.assertFalse(value.dispatcher_ready)

    def test_mixed_source_distribution_keeps_new_and_fallback_distinct(self):
        value=plan('mostly-eligible-mixed',count=4000)
        self.assertEqual(value.before_files,3800)
        self.assertEqual(value.added_files,200)
        self.assertEqual(value.semantic_updates,3200)
        self.assertEqual(value.fallback_updates,600)
        self.assertEqual(sum(x.edit=='metadata-raw' for x in value.files),200)
        self.assertEqual(sum(x.edit=='metadata-opaque' for x in value.files),200)
        self.assertEqual(sum(x.edit=='unsupported-signature' for x in value.files),200)
        self.assertTrue(all(x.edit is None for x in value.files if not x.before_present))

    def test_new_files_have_no_fabricated_receiver_basis(self):
        value=plan('new-files',count=1024)
        self.assertEqual(value.before_files,0)
        self.assertEqual(value.added_files,1024)
        self.assertEqual(value.semantic_updates,0)
        self.assertEqual(value.fallback_updates,0)
        self.assertTrue(all(not x.before_present and x.edit is None for x in value.files))

    def test_invalid_bounds_do_not_become_smaller_workloads(self):
        for args in [dict(count=True),dict(count=1023),dict(count=16385),
                     dict(file_bytes=True),dict(file_bytes=32767),dict(file_bytes=262145),
                     dict(packet_bytes=1048576)]:
            with self.assertRaises(ValueError):plan('many-small',**args)
        with self.assertRaises(ValueError):plan('unrecognized')


if __name__=='__main__':unittest.main()
