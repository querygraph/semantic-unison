"""Original injected metadata/source bytes; only tiny frozen JSON files real."""
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from shared_io_pool import UnresolvedIOOwnership
import uuid
from sdk_negative_receiving import freeze
from sdk_negative_receiving import metadata_test as fixtures
from sdk_negative_receiving.admission_test import EXECUTION,PRODUCTION
from sdk_negative_receiving.entry import request_check
from sdk_merge_receiving.store import Store

class Freeze(unittest.TestCase):
    def setUp(self):self.outputs=[]
    def tearDown(self):
        for path in self.outputs:shutil.rmtree(path,ignore_errors=True)
    def prepare(self,mutation=None):
        source=fixtures.Metadata();_,read,observe,packet=source.prepare(mutation)
        output=Path(freeze.A.REPOSITORY)/'doc'/('current-sdk-negative-control-'+uuid.uuid4().hex[:16])
        self.outputs.append(output)
        with patch.object(freeze.inventory,'execution',return_value=EXECUTION), \
             patch.object(freeze.inventory,'production',return_value=PRODUCTION):
            result=freeze.prepare(packet['input_manifest']['path'],packet['sdk_manifest']['path'],
                {label:packet['builds'][label]['receipt']['path'] for label in ('stock','ox')},output,
                read=read,observe=observe)
        return result,output,source

    def test_immutable_metadata_request_never_opens_native_or_media(self):
        result,root,source=self.prepare();native=root.stat()
        store=Store(str(root),dict(device=native.st_dev,inode=native.st_ino))
        try:
            packet=store.read_json('PLAN.json',expected_sha256=result['plan']['sha256'])
            request=store.read_json('REQUEST.json',expected_sha256=result['request']['sha256'])
            request_check(request,packet,result['plan'])
            self.assertFalse(result['runtime_admitted']);self.assertFalse(result['sdk_invoked'])
            self.assertFalse(Path(result['workspace']).exists())
            self.assertFalse(set(source.observations).intersection(source.reads))
        finally:store.close()

    def test_unknown_record_close_never_closes_retained_directory_again(self):
        carrier=UnresolvedIOOwnership('inert before OS close',retained_fds=(777,),uncertain_closes=[
            dict(fd=701,role='inert',observed_before_close=None)])
        calls=[]
        store=SimpleNamespace(write=lambda *a:(_ for _ in ()).throw(carrier),
                              close=lambda:calls.append('close'),fd=777,closed=False)
        with patch.object(freeze,'Store',return_value=store):
            with self.assertRaises(UnresolvedIOOwnership) as caught:self.prepare()
        self.assertIs(caught.exception,carrier);self.assertIs(carrier.merge_freeze_store,store)
        self.assertEqual(calls,[])
        self.assertEqual(carrier.retained_fds,(777,));self.assertEqual(carrier.uncertain_fds,(701,))

    def test_stale_compiled_source_refuses_without_creating_request(self):
        with self.assertRaises(ValueError):self.prepare('compiled')
        root=self.outputs[-1]
        self.assertFalse((root/'REQUEST.json').exists())

if __name__=='__main__':unittest.main()
