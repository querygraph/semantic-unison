"""Metadata-only comparison entry guards with explicit manifest/stat doubles."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sdk_throughput import entry as e
from sdk_multifile import entry as old
from sdk_multifile.entry_test import Entry as OldEntry


class Entry(unittest.TestCase):
    def fixture(self):
        p=OldEntry().fixture();p.update(schema='unison-sdk-throughput-plan/1',workspace='/private/tmp/u-str-unit-test',parameters=copy.deepcopy(e.PARAMETERS));return p
    def check(self,p):
        original=self.fixture()
        def read(path,digest):
            if str(path)=='/private/tmp/inert-plan':return p
            return dict(executable=p['tool']['path'],executable_sha256=p['tool']['sha256'],build_id=old.BUILD)
        def lstat(path):return SimpleNamespace(**original['inputs'][1 if str(path).endswith('inert-jpeg') else 0]['identity'])
        with patch.object(e,'read_manifest',side_effect=read),patch.object(old,'read_manifest',side_effect=read),patch.object(e,'sources',return_value=original['execution_source_sha256']),patch.object(old.os,'lstat',side_effect=lstat):
            return e.checked_plan('/private/tmp/inert-plan','d'*64)
    def test_exact_fixed_comparison_metadata_passes(self):self.assertEqual(self.check(self.fixture()),self.fixture())
    def test_limits_types_schema_and_namespace_refuse(self):
        for mutate in [lambda p:p['parameters'].update(endpoint_workers=[True,3]),lambda p:p['parameters'].update(sdk_calls=49),
                       lambda p:p['parameters'].update(maximum_result_bytes=0),lambda p:p.update(schema='unison-sdk-multifile-plan/1'),
                       lambda p:p.update(workspace='/private/tmp/u-smr-old-test')]:
            p=self.fixture();mutate(p)
            with self.assertRaises(ValueError):self.check(p)
    def test_changed_ancestry_and_unqualified_tool_refuse(self):
        for mutate in [lambda p:p['inputs'][0]['identity'].update(st_ino=99),lambda p:p['tool'].update(threads=2),
                       lambda p:p['execution_source_sha256'].update(extra='bad')]:
            p=self.fixture();mutate(p)
            with self.assertRaises(ValueError):self.check(p)


if __name__=='__main__':unittest.main()
