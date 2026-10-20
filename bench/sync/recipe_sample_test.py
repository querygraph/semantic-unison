"""Original generated2MiB controls with atomic copy doubles; ZERO Unison/SDK."""
import os
from pathlib import Path
import tempfile
import unittest
from recipe_sample import plan,sample,MAXIMUM
from workloads import KINDS
from workload_fixtures import write_at
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership


class Recipes(unittest.TestCase):
    def test_all_nonfixed_recipes_keep_protected_shape_and_exact_growth(self):
        for kind in KINDS:
            if kind=='fixed-xmp':continue
            value=plan(kind)
            self.assertEqual(value.before_files,2);self.assertEqual(value.semantic_updates,0)
            self.assertEqual(value.target_file_bytes,2*1048576+(9216 if kind=='growing-xmp' else 0))
            self.assertLessEqual(value.target_file_bytes,MAXIMUM)
        with self.assertRaises(ValueError):plan('full-change',count=1)

    def exercise(self,kind,*,inplace=False):
        with tempfile.TemporaryDirectory(prefix='unison-recipe-original-control-') as temp:
            left=Path(temp)/'left';right=Path(temp)/'right';left.mkdir(mode=0o700);right.mkdir(mode=0o700)
            phases=[];events=[]
            def invoke(stage):
                phases.append(stage)
                if stage=='noop':return
                for source in sorted(left.glob('*/*.dng')):
                    dest=right/source.relative_to(left);dest.parent.mkdir(mode=0o700,exist_ok=True)
                    name=dest if inplace and stage=='update' else dest.with_suffix('.incoming')
                    flags=os.O_WRONLY|os.O_CLOEXEC|os.O_NOFOLLOW
                    if name!=dest:flags|=os.O_CREAT|os.O_EXCL
                    fd=os.open(name,flags,0o600)
                    try:
                        raw=source.read_bytes();write_at(fd,raw,0);os.ftruncate(fd,len(raw));os.fsync(fd)
                    finally:close_descriptors([fd])
                    if name!=dest:os.replace(name,dest)
            if inplace:
                with self.assertRaises(UnresolvedOwnership) as got:sample(plan(kind),left,right,invoke=invoke,record=events.append)
                error=got.exception
                self.assertFalse(getattr(error,'uncertain_fds',()))
                # Fake completed copy had no child or unknown OSclose: explicitly
                # dispose only these known test-owned readers outside except.
                close_descriptors(list(error.recipe_readers.values()));error.recipe_readers.clear()
                self.assertEqual(phases,['seed','update'])
            else:
                result=sample(plan(kind),left,right,invoke=invoke,record=events.append)
                self.assertTrue(result['retained_old_readers_unchanged'])
                self.assertEqual(phases,['seed','update','noop']);self.assertEqual(len(events),6)
                self.assertFalse(result['resource_release_authorized'])

    def test_growing_packet_keeps_old_receiver_reader_bytes(self):self.exercise('growing-xmp')
    def test_preview_change_keeps_old_receiver_reader_bytes(self):self.exercise('metadata-preview')
    def test_inplace_fake_receiver_is_detected_and_no_noop_starts(self):self.exercise('metadata-preview',inplace=True)


if __name__=='__main__':unittest.main()
