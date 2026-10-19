"""Original tiny generated-file and runner counter controls; no sync/benchmark."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest
from workload_fixtures import create, edit
from workloads import KINDS
from run import internal_counters


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='unison-workload-file-control-')
        self.path = Path(self.tmp.name)/'owned.bin'

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_new_workloads_match_independent_byte_oracle(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                name = self.path.with_name(kind)
                info = create(name, 32768, 512, 0)
                # Recorded data must survive the runner's JSON persistence.
                info = json.loads(json.dumps(info))
                before = name.read_bytes()
                got = edit(name, info, kind)
                after = name.read_bytes()
                self.assertEqual(got, hashlib.sha256(after).hexdigest())
                self.assertNotEqual(got, info['before_sha256'])
                outside = [i for i, (a,b) in enumerate(zip(before,after))
                           if a != b and not 1024 <= i < 1536]
                if kind == 'full-change':
                    self.assertEqual(after, bytes(value ^ 255 for value in before))
                elif kind in ('malformed-ifd','unsupported-signature'):
                    expected=set(range(4,8)) if kind=='malformed-ifd' else {0,1}
                    self.assertTrue(outside and set(outside)<=expected)
                    self.assertEqual(len(after),len(before))
                elif kind == 'growing-xmp':
                    self.assertEqual(len(after), 32768+1536)
                    self.assertEqual(after[70:32768], before[70:])
                    self.assertTrue(all(62 <= i < 70 for i in outside))
                else:
                    self.assertEqual(len(after), 32768)
                    self.assertEqual(outside, {'fixed-xmp': [], 'metadata-preview': [28672],
                                              'metadata-raw': [4096], 'metadata-opaque': [256]}[kind])
                self.assertEqual(info['after_size_bytes'], len(after))

    def test_existing_destination_cannot_be_recreated(self):
        self.path.write_bytes(b'untouched')
        with self.assertRaises(FileExistsError): create(self.path,32768,512,0)
        self.assertEqual(self.path.read_bytes(),b'untouched')

    def test_replaced_generated_source_refuses_before_writing(self):
        info=create(self.path,32768,512,0)
        saved=self.path.with_name('old');self.path.rename(saved)
        self.path.write_bytes(b'new file')
        with self.assertRaises(ValueError):edit(self.path,info,'metadata-raw')
        self.assertEqual(self.path.read_bytes(),b'new file')

    def test_alias_refuses_before_mutation(self):
        import os
        info=create(self.path,32768,512,0)
        before=self.path.read_bytes();os.link(self.path,self.path.with_name('alias'))
        with self.assertRaises(ValueError):edit(self.path,info,'metadata-preview')
        self.assertEqual(self.path.read_bytes(),before)

    def test_stale_digest_and_unknown_schema_refuse(self):
        info=create(self.path,32768,512,0);before=self.path.read_bytes()
        for field,value in [('schema','not-generated'),('before_sha256','f'*64)]:
            bad=copy.deepcopy(info);bad[field]=value
            with self.assertRaises(ValueError):edit(self.path,bad,'metadata-opaque')
            self.assertEqual(self.path.read_bytes(),before)

    def test_create_close_uncertainty_is_not_success_or_retried(self):
        import os
        from shared_io_pool import UnresolvedIOOwnership, descriptor_observation
        errors=[]
        def closer(fds):
            observation=descriptor_observation(fds[0], 'injected-fixture-close')
            os.close(fds[0])
            error=UnresolvedIOOwnership('injected close uncertainty', uncertain_closes=(observation,))
            errors.append(error)
            raise error
        with patch('workload_fixtures.close_descriptors', side_effect=closer) as close:
            with self.assertRaises(UnresolvedIOOwnership) as caught:
                create(self.path,32768,512,0)
        self.assertIs(caught.exception, errors[0])
        self.assertEqual(close.call_count,1)
        self.assertTrue(self.path.exists())  # Preserve the created effect.

    def test_edit_close_uncertainty_preserves_effect_without_retry(self):
        import os
        from shared_io_pool import UnresolvedIOOwnership, descriptor_observation
        info=create(self.path,32768,512,0);before=self.path.read_bytes();errors=[]
        def closer(fds):
            observation=descriptor_observation(fds[0], 'injected-fixture-edit-close')
            os.close(fds[0])
            error=UnresolvedIOOwnership('injected close uncertainty', uncertain_closes=(observation,))
            errors.append(error)
            raise error
        with patch('workload_fixtures.close_descriptors', side_effect=closer) as close:
            with self.assertRaises(UnresolvedIOOwnership) as caught:
                edit(self.path,info,'metadata-preview')
        self.assertIs(caught.exception,errors[0])
        self.assertEqual(close.call_count,1)
        self.assertNotEqual(self.path.read_bytes(),before)

    def test_fallback_counter_not_counted_as_SDE_success(self):
        log='Using immutable receiver clone basis\nReceiver clone preserved 30000 logical bytes\n'
        c=internal_counters(log,'semantic',1,34304,expect_semantic=False)
        self.assertEqual(c['semantic_updates'],0)
        self.assertFalse(c['expected_semantic_update'])
        self.assertEqual(c['materialization_non_inherited_logical_bytes_model'],4304)
        with self.assertRaises(AssertionError):internal_counters(log,'semantic',1,34304)
        fake='Remote semantic clone wrote 1 logical metadata bytes in 1 write calls (512 payload bytes; 4096-byte comparison windows; org.firstpair.dng-xmp/0)\n'
        with self.assertRaises(AssertionError):internal_counters(fake,'semantic',1,34304,expect_semantic=False)
        with self.assertRaises(ValueError):internal_counters('', 'semantic',1,34304,expect_semantic=0)


if __name__ == '__main__':
    unittest.main()
