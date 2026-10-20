"""Injected source/receipt bytes; only tiny frozen JSON files are real."""
import hashlib,json,shutil,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from current_validation_paths import freeze,metadata,admission as A
from current_validation_paths.admission_test import EXECUTION,PRODUCTION,ENTRY
from current_validation_paths.parent_test import SOURCE
from current_validation_paths.entry import request_check
from sdk_merge_receiving.store import Store


class Sources:
    def __init__(self,compiler='stock',mutation=None):
        self.reads=[];self.receipt='/private/tmp/named-build-'+compiler+'/RESULT.json'
        root=A.REPOSITORY+'/'
        self.files={root+A.LEGACY:SOURCE.encode(),root+ENTRY:b'entry',root+'src/semanticRuntime.ml':b'production'}
        build=dict(complete=True,selftest_requested=True,build_exit=0,selftest_exit=0,binary='/private/tmp/named-build-'+compiler+'/src/unison',
            binary_sha256='c'*64,compiler=A.COMPILERS[compiler],compiler_sha256='d'*64,
            source_sha256={'src/semanticRuntime.ml':hashlib.sha256(b'other' if mutation=='compiled' else b'production').hexdigest(),'tests/x.py':'1'*64})
        if mutation=='selftest':build['selftest_exit']=1
        self.files[self.receipt]=json.dumps(build).encode()
    def read(self,path,limit):
        self.reads.append(path);data=self.files[path];assert len(data)<=limit;return data


class Freeze(unittest.TestCase):
    def setUp(self):self.outputs=[]
    def tearDown(self):
        for path in self.outputs:shutil.rmtree(path,ignore_errors=True)
    def prepare(self,compiler='stock',mutation=None):
        source=Sources(compiler,mutation)
        output=Path(A.REPOSITORY)/'doc'/('current-named-receiving-'+compiler+'-control-'+uuid.uuid4().hex[:16]);self.outputs.append(output)
        with patch.object(freeze.inventory,'execution',return_value=EXECUTION),patch.object(freeze.inventory,'production',return_value=PRODUCTION):
            return freeze.prepare(compiler,source.receipt,output,read=source.read),output,source
    def test_immutable_plan_and_request_never_open_executables_or_workspace(self):
        for compiler in ('stock','ox'):
            index,root,source=self.prepare(compiler);native=root.stat()
            store=Store(str(root),dict(device=native.st_dev,inode=native.st_ino))
            try:
                packet=store.read_json('PLAN.json',expected_sha256=index['plan']['sha256'])
                request=store.read_json('REQUEST.json',expected_sha256=index['request']['sha256'])
                request_check(request,packet,index['plan'])
            finally:store.close()
            self.assertEqual(packet['compiler'],compiler);self.assertEqual(len(packet['rows']),21)
            self.assertFalse(Path(index['workspace']).exists());self.assertFalse(index['runtime_admitted'])
            self.assertNotIn(packet['binary']['path'],source.reads);self.assertNotIn(A.PYTHON,source.reads)
            self.assertNotIn(packet['build']['compiler']['path'],source.reads)
    def test_dng_merge_suite_freezes_its_own_contract_and_namespace(self):
        source=Sources();output=Path(A.REPOSITORY)/'doc'/('current-dng-merge-receiving-stock-control-'+uuid.uuid4().hex[:16]);self.outputs.append(output)
        with patch.object(freeze.inventory,'execution',return_value=EXECUTION),patch.object(freeze.inventory,'production',return_value=PRODUCTION):
            index=freeze.prepare('stock',source.receipt,output,read=source.read,suite='dng_merge')
        packet=json.loads((output/'PLAN.json').read_text())
        self.assertEqual(packet['schema'],'unison-current-dng-merge-receiving-execution/1');self.assertEqual(len(packet['rows']),13)
        self.assertTrue(index['workspace'].startswith('/private/tmp/u-dmerge-'));self.assertEqual(packet['limits']['CLI_calls'],29)
        with self.assertRaises(ValueError):freeze.prepare('stock',source.receipt,Path(A.REPOSITORY)/'doc'/'current-named-receiving-stock-x',read=source.read,suite='dng_merge')
    def test_fs_properties_suite_freezes_its_own_contract_and_namespace(self):
        source=Sources();output=Path(A.REPOSITORY)/'doc'/('current-fs-properties-receiving-stock-control-'+uuid.uuid4().hex[:16]);self.outputs.append(output)
        with patch.object(freeze.inventory,'execution',return_value=EXECUTION),patch.object(freeze.inventory,'production',return_value=PRODUCTION):
            index=freeze.prepare('stock',source.receipt,output,read=source.read,suite='fs_properties')
        packet=json.loads((output/'PLAN.json').read_text())
        self.assertEqual(packet['schema'],'unison-current-fs-properties-receiving-execution/1');self.assertEqual(len(packet['rows']),6)
        self.assertTrue(index['workspace'].startswith('/private/tmp/u-fsprop-'));self.assertEqual(packet['limits']['CLI_calls'],17)
        with self.assertRaises(ValueError):freeze.prepare('stock',source.receipt,Path(A.REPOSITORY)/'doc'/'current-dng-merge-receiving-stock-x',read=source.read,suite='fs_properties')
    def test_stale_compiled_source_or_failed_selftest_refuses_without_request(self):
        for mutation in ('compiled','selftest'):
            with self.subTest(mutation=mutation),self.assertRaisesRegex(ValueError,'compiled source|selftest'):self.prepare(mutation=mutation)
            self.assertFalse((self.outputs[-1]/'REQUEST.json').exists())
    def test_metadata_refuses_changed_source_after_freeze(self):
        index,root,source=self.prepare()
        source.files[A.REPOSITORY+'/'+ENTRY]=b'changed entry'
        def read(path,limit):return (root/'PLAN.json').read_bytes() if path==index['plan']['path'] else source.read(path,limit)
        with self.assertRaisesRegex(ValueError,'current source changed'):
            metadata.checked(index['plan'],execution_sources=EXECUTION,production_sources=PRODUCTION,read=read)
    def test_output_outside_doc_or_other_compiler_name_refuses_before_any_read(self):
        source=Sources()
        for output in (Path('/private/tmp/current-named-receiving-stock-x'),Path(A.REPOSITORY)/'doc'/'current-named-receiving-ox-x'):
            with self.subTest(output=str(output)),self.assertRaises(ValueError):freeze.prepare('stock',source.receipt,output,read=source.read)
        self.assertEqual(source.reads,[])

if __name__=='__main__':unittest.main()
