import copy
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import sdk_multifile.entry as e


class Entry(unittest.TestCase):
    def fixture(self):
        inputs=[]
        for i,(name,codec) in enumerate([('uncompressed.dng','uncompressed'),('jpeg.dng','jpeg')]):
            identity=dict(st_dev=1,st_ino=10+i,st_mode=stat.S_IFREG|0o644,st_size=10,st_mtime_ns=1,st_ctime_ns=2,st_nlink=1,st_uid=os.getuid())
            inputs.append(dict(candidate_id=name,path='/private/tmp/inert-'+codec,sha256=str(i+1)*64,identity=identity))
        pins={str(e.ROOT/'bench/sync'/n):'a'*64 for n in e.SCRIPT_NAMES}
        return dict(schema='unison-sdk-multifile-plan/1',workspace='/private/tmp/u-smr-unit-test',parameters=copy.deepcopy(e.PARAMETERS),execution_source_sha256=pins,
                    inputs=inputs,sources=[dict(candidate_id=i['candidate_id'],sha256=i['sha256'],bytes=10) for i in inputs],
                    binaries={n:dict(label=n,path='/private/tmp/inert-'+n,sha256='a'*64) for n in ['stock','ox']},
                    tool=dict(path='/private/tmp/inert-sdk',sha256='b'*64,build_id=e.BUILD,threads=1,manifest='/private/tmp/inert-manifest',manifest_sha256='c'*64),
                    transport_source_sha256={n:'a'*64 for n in e.SCRIPT_NAMES},interpreter=dict(path=e.PYTHON,sha256=e.PYTHON_SHA))
    def check(self,d):
        original=self.fixture()
        def read(path,digest):
            if str(path)=='/private/tmp/inert-plan':return d
            return dict(executable=d['tool']['path'],executable_sha256=d['tool']['sha256'],build_id=e.BUILD)
        def lstat(path):
            index=1 if str(path).endswith('inert-jpeg') else 0
            return SimpleNamespace(**original['inputs'][index]['identity'])
        with patch.object(e,'read_manifest',side_effect=read),patch.object(e,'sources',return_value=original['execution_source_sha256']),patch.object(e.os,'lstat',side_effect=lstat):
            return e.checked_plan('/private/tmp/inert-plan','d'*64)
    def test_exact_metadata_only_plan(self):self.assertEqual(self.check(self.fixture()),self.fixture())
    def test_worker_import_coexists_with_historical_sdk_plan_module(self):
        import plan as historical
        from sdk_multifile import worker,transport
        self.assertTrue(callable(worker.execute));self.assertTrue(callable(transport.Invoker))
        self.assertTrue(hasattr(historical,'matrix'))
        p=self.fixture()
        call=transport.Invoker('/private/tmp/u-smr-unit-test/stock',binary=p['binaries']['stock'],tool=p['tool'],
                               journal=None,script_pins=p['transport_source_sha256'],deadline=200.)
        flags=call.contract['argv'];self.assertEqual(flags[flags.index('-semanticmaxinflight')+1],'4')
    def test_limits_source_and_tool_changes_refuse(self):
        for mutate in [lambda d:d['parameters'].update(cpu_credits=18),lambda d:d['parameters'].update(sdk_calls=True),
                       lambda d:d['tool'].update(threads=2),lambda d:d['execution_source_sha256'].update(extra='x'),
                       lambda d:d.update(extra='unknown')]:
            d=self.fixture();mutate(d)
            with self.assertRaises(ValueError):self.check(d)
    def test_input_ancestry_epoch_and_candidate_binding_refuse(self):
        for mutate in [lambda d:d['inputs'][0]['identity'].update(st_size=11),
                       lambda d:d['inputs'][0].update(path='/Users/inert-original'),
                       lambda d:d['sources'][0].update(bytes=9),lambda d:d['inputs'][1].update(sha256='1'*64),
                       lambda d:d['inputs'][0].update(candidate_id='../escape')]:
            d=self.fixture();mutate(d)
            with self.assertRaises(ValueError):self.check(d)

if __name__=='__main__':unittest.main()
