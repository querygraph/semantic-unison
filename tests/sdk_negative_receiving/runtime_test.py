"""Tiny generated files + fabricated captures, grants and clone-provenance labels.

No real clone, CLI, SDK, canonical IO or eight-credit grant. Explicit source
seams emulate their records to exercise runtime+parent serialization and joins.
"""
import copy,hashlib,json,os,shutil,time,unittest,uuid
from pathlib import Path
from unittest.mock import patch
from shared_cpu_pool import UnresolvedOwnership
from sdk_negative_receiving import runtime,parent_runtime
from sdk_negative_receiving import cases_test as fixtures
from sdk_merge_receiving.plan_test import inputs
from sdk_merge_receiving.evidence_test import fixture
from sdk_negative_receiving.finding_test import raw as negative_raw,SHA
from sdk_merge_receiving.store import Store


class Runtime(unittest.TestCase):
    def setUp(self):
        fixtures.CaseLifecycle.setUp(self);self.clone=self.data.clone;self.workspace.rmdir()
        self.workspace=Path('/private/tmp')/('u-snr-'+uuid.uuid4().hex[:16]);self.workspace.mkdir(mode=0o700)
        self.data.packet['workspace']=str(self.workspace);self.open_store=None;self.error=None
    def tearDown(self):
        if self.error is not None:
            for directory in self.error.negative_runtime['directories'].values():
                if not directory.closed:directory.close()
        if self.open_store is not None and not self.open_store.closed:self.open_store.close()
        shutil.rmtree(self.workspace);fixtures.CaseLifecycle.tearDown(self)
    def run_case(self,fail=None):
        binaries,tool,_=inputs();packet=dict(self.data.packet,binaries=binaries,tool=tool,
            repository=str(Path(__file__).resolve().parents[2]),limits=dict(per_cli_seconds=120))
        for ref in (*binaries.values(),tool):ref['sha256']=hashlib.sha256(('fake '+ref['path']).encode()).hexdigest()
        native=self.workspace.lstat();store=Store(str(self.workspace),dict(device=native.st_dev,inode=native.st_ino));self.open_store=store
        fds=[dict(fd=700+i,device=1,inode=700+i) for i in range(9)]
        start=dict(owner_pid=os.getpid()+1000000,child_pid=os.getpid(),target='current-sdk-negative-receiving',command=['/original/fakeworker'],
            cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',inherited_resource_fds=fds,
            admission_nonce='a'*32,owner_observation_deadline=time.monotonic()+90)
        store.write('OWNER-START.json',start);store.write('ADMISSION-BOUND.json',dict(command=start['command'],admission_nonce=start['admission_nonce']))
        store.write('WORKER-BINDING.json',dict(schema='unison-current-negative-worker-binding/1',parent_pid=start['owner_pid'],worker_pid=start['child_pid'],
            resource_fds=fds,binding=dict(inherited_fds=[r['fd'] for r in fds],canonical_metadata_bound=True,
                lock_ownership_independently_proved=False,resource_release_authorized=False)))
        actual_read=runtime.read_bytes
        def read(path,limit):
            if path in [r['path'] for r in (*binaries.values(),tool)]:return ('fake '+path).encode()
            return actual_read(path,limit)
        self.calls=[]
        def pair_call(row,env,**kwargs):
            self.calls.append(runtime.key(row))
            if fail=='pair':raise UnresolvedOwnership('original fake owner retained',retained_fds=(999,))
            self.transfer_double(row);_,pair=fixture('seed');pair['client']['command']=row['command']
            pair['proxy']['command']=kwargs['proxy_command'];pair['raw_proxy']['server_command']=row['server_command']
            if row['stage']=='negative':
                image=Path(row['directory'])/'left/image.dng';digest=hashlib.sha256(image.read_bytes()).hexdigest()
                receipt=negative_raw().replace(SHA.encode(),digest.encode())
                code=2 if row['policy']=='require' else 0
                pair['client']['returncode']=pair['client']['client_cleanup']['returncode']=code
                marker='rejected' if row['policy']=='require' else 'warning'
                pair['client']['stderr']='Adobe DNG validation '+marker+': SDK driver reported validation errors'
                pair['proxy']['stderr']=('[server: validation-process] Helper result v0 pid=321 status=exit:0 outcome=completed candidate-sha256='+digest+
                    ' candidate-bytes=4096 capture-truncated=false stdout-truncated=false stderr-truncated=false stdout-hex='+receipt.hex()+
                    ' stderr-hex=\n[server: validation-group] Retained group v0 pid=321 candidate-sha256='+digest+' other-members=0\n')
                if fail=='finding':pair['proxy']['stderr']=''
            raw=json.dumps(pair['raw_proxy']).encode();root=Path(row['directory']);st=root.lstat();directory=Store(str(root),dict(device=st.st_dev,inode=st.st_ino))
            try:directory.write(row['stage']+'-INHERITED.json',dict(proxy_pid=pair['proxy']['client_cleanup']['pid'],worker_pid=start['child_pid'],
                resource_fds=fds,binding=dict(inherited_fds=[r['fd'] for r in fds],canonical_metadata_bound=True,
                    lock_ownership_independently_proved=False,resource_release_authorized=False)))
            finally:directory.close()
            kwargs['persist'](row,pair,raw);return pair,raw
        try:
            # Emulate native_clone identity labels only in original fixture
            # records. No native syscall or source-byte counter is qualified.
            with patch.object(runtime,'read_bytes',side_effect=read),patch('sdk_merge_receiving.data.native_clone',self.clone):
                result=runtime.run(packet,store,start,time.monotonic()+60,clone=self.clone,pair_call=pair_call)
            outcome=copy.deepcopy(fixture('seed')[1]['client']);outcome['command']=start['command'];outcome['client_cleanup']['pid']=start['child_pid']
            with patch.object(parent_runtime.os,'getpid',return_value=start['owner_pid']):
                verdict=parent_runtime.audit(packet,store,outcome)
            return result,verdict
        except UnresolvedOwnership as error:self.error=error;raise
    transfer_double=fixtures.CaseLifecycle.transfer_double
    def test_whole_runtime_and_retained_parent_replay_fake_twelve_calls(self):
        result,verdict=self.run_case();self.assertTrue(result['complete']);self.assertEqual(len(self.calls),12)
        self.assertEqual(verdict['cli_calls'],12);self.assertEqual(verdict['SDK_helpers'],6)
        self.assertTrue(verdict['external_children_settled']);self.assertTrue(verdict['final_private_outputs_rehashed'])
    def test_pair_uncertainty_retains_all_inherited_copies(self):
        with self.assertRaises(UnresolvedOwnership) as raised:self.run_case('pair')
        self.assertTrue({999,*range(700,709)}<=set(raised.exception.retained_fds))
        self.assertEqual(len(self.calls),1);self.assertFalse((self.workspace/'WORKER-RESULT.json').exists())
    def test_failed_negative_audit_stops_after_second_call(self):
        with self.assertRaises(UnresolvedOwnership):self.run_case('finding')
        self.assertEqual(len(self.calls),2);self.assertFalse((self.workspace/'WORKER-RESULT.json').exists())

if __name__=='__main__':unittest.main()
