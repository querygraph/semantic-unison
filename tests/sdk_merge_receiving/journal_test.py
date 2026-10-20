"""Worker-to-durable-evidence integration using original fabricated invocations."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sdk_merge_receiving.store import Store
from sdk_merge_receiving.journal import Journal
from sdk_merge_receiving.plan import CODECS,STAGES,schedule
from sdk_merge_receiving.plan_test import inputs
from sdk_merge_receiving.evidence_test import fixture,PROXY
from sdk_merge_receiving.bound_call import call
from sdk_merge_receiving.worker import execute
from sdk_merge_receiving.helpers_test import SHA

class Durable(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='unison-merge-journal-')
        self.root=Path(self.temporary.name).resolve();os.chmod(self.root,0o700)
        st=self.root.stat();self.store=Store(str(self.root),dict(device=st.st_dev,inode=st.st_ino))
        self.journal=Journal(self.store,{(c,s):PROXY for c in CODECS for s in STAGES})
    def tearDown(self):
        self.store.close();self.temporary.cleanup()

    def test_all_nine_calls_reaudit_saved_pair_bytes_before_worker_finishes(self):
        # The inert transport double must still invoke the independent frame reader.
        def invocation(row):
            _,pair=fixture(row['stage']);pair['client']['command']=row['command']
            pair['raw_proxy']['server_command']=row['server_command'];raw=json.dumps(pair['raw_proxy']).encode()
            def run(*args,**kwargs):
                self.assertEqual(kwargs['read_proxy'](),pair['raw_proxy']);return pair
            with patch('sdk_merge_receiving.bound_call.transport.run',side_effect=run):
                return call(row,{},proxy_command=PROXY,proxy_environment={},socket_path='/private/tmp/inert.sock',
                    deadline=1,pass_fds=(),read_proxy_bytes=lambda:raw,persist=self.journal.persist_pair)
        result=execute(*inputs(),prepare=lambda _:dict(sha256=SHA,bytes=256),invoke=invocation,
            audit_transport=self.journal.audit_transport,verify_outputs=lambda *_:None,
            persist=self.journal.persist)
        self.assertTrue(result['ledger']['complete']);self.assertFalse(result['resource_release_authorized'])
        self.assertEqual(len(self.journal.events),19);self.assertEqual(len(self.journal.pair_pins),9)
        final=self.journal.events[-1]
        reread=self.store.read_json(final['name'],expected_sha256=final['sha256'])
        self.assertEqual(len(reread['pair_pins']),9)
        self.assertTrue(reread['snapshot']['ledger']['complete'])

    def test_substituted_worker_outcome_is_not_accepted_by_saved_audit(self):
        row=schedule(*inputs())['rows'][0];_,pair=fixture('seed')
        from sdk_merge_receiving.evidence import bind
        raw=json.dumps(pair['raw_proxy']).encode()
        self.journal.persist_pair(row,pair,raw)
        outcome=bind(row,pair,expected_proxy_command=PROXY,raw_proxy_bytes=raw)
        self.journal.audit_transport(row,outcome)
        altered=copy.deepcopy(outcome);altered['transport_record_sha256']='0'*64
        with self.assertRaises(ValueError):self.journal.audit_transport(row,altered)
        with self.assertRaises(ValueError):self.journal.persist_pair(row,pair,raw)

if __name__=='__main__':unittest.main()
