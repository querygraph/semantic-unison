"""Original source-binding fixtures; no production media, process or lock access."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from acceptance_pin_audit import bindings, compare, source_relative


class Bindings(unittest.TestCase):
    def test_keyed_relative_and_worktree_paths(self):
        digest='a'*64
        self.assertEqual(bindings({'src/unit.ml':digest,'sources':{'/private/tmp/build/src/other.mli':digest}}),
                         {('src/unit.ml',digest),('src/other.mli',digest)})
    def test_explicit_artifact_record_and_version_retention(self):
        self.assertEqual(bindings([{'path':'/Users/u/src/fork/src/unit.ml','sha256':'a'*64},
                                   {'src/unit.ml':'b'*64}]),{('src/unit.ml','a'*64),('src/unit.ml','b'*64)})
    def test_no_inference_from_narrative_or_digest_only(self):
        self.assertEqual(bindings({'scope':'source src/unit.ml '+ 'a'*64,'sha256':'b'*64}),set())
    def test_checkout_under_host_src_does_not_promote_test_artifacts(self):
        for name in ('/Users/u/src/unison/tests/probe.ml','/Users/u/src/fork/tools/native.c'):
            self.assertIsNone(source_relative(name))
    def test_payload_and_traversal_paths_excluded(self):
        for name in ('/private/tmp/source.DNG','src/../original.c','src/unison','src/image.jpg','src/stage.cmx'):
            with self.subTest(name=name):self.assertIsNone(source_relative(name))
    def test_match_change_and_missing_are_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'src').mkdir();(root/'src/unit.ml').write_bytes(b'original')
            rows=compare(root,{'src/unit.ml':hashlib.sha256(b'original').hexdigest(),
                               'other':{'src/unit.ml':'a'*64},'src/missing.c':'b'*64})
            self.assertEqual({(r['path'],r['status']) for r in rows},
                             {('src/unit.ml','MATCH'),('src/unit.ml','CHANGED'),('src/missing.c','MISSING')})
    def test_generated_version_module_not_reported_as_missing_source(self):
        self.assertIsNone(source_relative('src/ubase/projectInfo.ml'))
    def test_zero_bindings_remains_empty(self):self.assertEqual(compare(Path('/inert'),{'complete':True}),[])


if __name__=='__main__':unittest.main()
