"""Whole worker composition with arbitrary byte states and inert SDK transport."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_merge_receiving import runtime
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.evidence import bind
from sdk_merge_receiving.evidence_test import fixture as pair_fixture
from sdk_merge_receiving.helpers_test import frame
from sdk_merge_receiving import data_test as fixtures
from sdk_merge_receiving.plan_test import inputs

class Runtime(unittest.TestCase):
    setUp=fixtures.Data.setUp
    tearDown=fixtures.Data.tearDown
    outputs=fixtures.Data.outputs
    def run_runtime(self,fail=None):
        binaries,tool,_=inputs();packet=dict(self.packet,binaries=binaries,tool=tool,
            repository=str(Path(__file__).resolve().parents[2]),
            limits=dict(per_cli_seconds=120))
        # schedule requires its canonical short one-use namespace, so use the
        # fixture root as a test-only schedule adapter; commands remain exact.
        original_schedule=runtime.schedule
        def schedule(b,t,w):
            result=original_schedule(b,t,'/private/tmp/u-smg-'+'a'*16)
            for row in result['rows']:
                row['directory']=str(self.workspace/row['codec'])
                row['command']=[argument.replace('/private/tmp/u-smg-'+'a'*16,str(self.workspace))
                                for argument in row['command']]
                row['identity']['directory']=row['directory']
            return result
        st=self.workspace.stat();store=Store(str(self.workspace),dict(device=st.st_dev,inode=st.st_ino))
        self.runtime_store=store
        start=dict(inherited_resource_fds=[dict(fd=700+i,device=1,inode=700+i) for i in range(9)])
        real_read=runtime.read_bytes
        def read(path,limit):
            if path in (binaries['stock']['path'],binaries['ox']['path'],tool['path']):
                # Original artifact bytes and matching hashes, no executable opened.
                value=('original '+path).encode();return value
            return real_read(path,limit)
        for item in (*binaries.values(),tool):item['sha256']=hashlib.sha256(('original '+item['path']).encode()).hexdigest()
        self.calls=[]
        def pair_call(row,env,**kwargs):
            self.calls.append((row['codec'],row['stage']))
            if fail=='pair':raise UnresolvedOwnership('inert pair retained',retained_fds=(999,))
            self.outputs(row)
            _,pair=pair_fixture(row['stage']);pair['client']['command']=row['command']
            pair['proxy']['command']=kwargs['proxy_command'];pair['raw_proxy']['server_command']=row['server_command']
            case=next(c for c in packet['cases'] if c['codec']==row['codec'])
            sha=case['states']['target']['sha256']
            # The fake SDK frames must bind the expected generated candidate.
            if row['stage']=='update':
                pair['client']['stdout']=frame('client',size=64,digest=sha)
                pair['proxy']['stdout']=frame('server',pid=124,size=64,digest=sha)
            raw=json.dumps(pair['raw_proxy']).encode();kwargs['persist'](row,pair,raw)
            return bind(row,pair,expected_proxy_command=kwargs['proxy_command'],raw_proxy_bytes=raw)
        try:
            # Worker uses the same trusted schedule function, preserving row identity.
            with patch.object(runtime,'schedule',side_effect=schedule), \
                 patch('sdk_merge_receiving.worker.schedule',side_effect=schedule), \
                 patch.object(runtime,'read_bytes',side_effect=read):
                return runtime.run(packet,store,start,__import__('time').monotonic()+30,
                                   clone=self.clone,pair_call=pair_call)
        except UnresolvedOwnership as error:
            self.runtime_error=error;raise
        finally:
            # Test-only known metadata owners; all process/FD numbers are inert.
            error=getattr(self,'runtime_error',None)
            if error:
                for codec in error.merge_runtime['codec_stores'].values():
                    if not codec.closed:codec.close()
            if not store.closed:store.close()

    def test_whole_runtime_persists_and_reaudits_all_nine_fake_calls(self):
        # Noop must not rewrite bytes/epochs: unlike seed/update, the simulated
        # native no-op leaves receiving files exactly unchanged.
        original=self.outputs
        self.outputs=lambda row:None if row['stage']=='noop' else original(row)
        result=self.run_runtime()
        self.assertTrue(result['ledger']['complete']);self.assertEqual(len(self.calls),9)
        self.assertTrue((self.workspace/'WORKER-RESULT.json').exists())
        saved=json.loads((self.workspace/'WORKER-RESULT.json').read_text())
        self.assertEqual(len(saved['preparation_pins']),9)
        for pin in saved['preparation_pins'].values():
            self.assertEqual(hashlib.sha256((self.workspace/pin['name']).read_bytes()).hexdigest(),pin['sha256'])
        self.assertTrue((self.workspace/'WORKER-DIRECTORIES-CLOSED.json').exists())

    def test_pair_failure_retains_runtime_and_grant_without_success_record(self):
        with self.assertRaises(UnresolvedOwnership) as caught:self.run_runtime('pair')
        self.assertEqual(len(self.calls),1)
        self.assertIn(999,caught.exception.retained_fds)
        self.assertTrue(set(range(700,709))<=set(caught.exception.retained_fds))
        self.assertFalse((self.workspace/'WORKER-RESULT.json').exists())

if __name__=='__main__':unittest.main()
