"""Owner-side join over actual tiny private records; fabricated captures, no child."""
import hashlib,json,os,shutil,unittest,uuid
from pathlib import Path
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.store import Store
from current_validation_paths import admission as A,parent_runtime,recipes
from current_validation_paths import parent_test as base
from current_validation_paths.parent_io import Reader


class Join(unittest.TestCase):
    def setUp(self):
        self.root=Path('/private/tmp')/('u-vpath-'+uuid.uuid4().hex[:16]);self.root.mkdir(0o700);self.addCleanup(shutil.rmtree,self.root)
        f=self.fixture=base.Replay('test_failed_original_prefix_can_be_replayed_without_benchmark_pass_or_release')
        f.workspace=str(self.root);case=self.root/'resume-complete-pass';case.mkdir(0o700)
        native=case.lstat();f.case_identity=(native.st_dev,native.st_ino);f.setUp()
        legacy=read_bytes(A.REPOSITORY+'/'+A.LEGACY,256*1024)
        f.packet.update(workspace=str(self.root),legacy_source=dict(path=A.REPOSITORY+'/'+A.LEGACY,bytes=len(legacy),sha256=hashlib.sha256(legacy).hexdigest()))
        def write(path,data,mode=0o600):path.write_bytes(data);path.chmod(mode)
        for (_,name),raw in f.records.items():write(case/name,raw)
        for name,text in f.scripts.items():write(case/name,text.encode(),0o700)
        write(case/'call-001-proxy.py',recipes.proxy_source(f.packet['repository'],f.config).encode(),0o700)
        (case/'server-state').mkdir(0o700);write(case/'server-state/endpoint.prf',f.phase['server_profile_text'].encode())
        write(case/'external-copy.calls.jsonl',b''.join(json.dumps(v).encode()+b'\n' for v in f.state['counters']['copy']))
        st=self.root.lstat();self.store=Store(str(self.root),dict(device=st.st_dev,inode=st.st_ino));self.addCleanup(lambda:self.store.closed or self.store.close())
        for name,value in f.root_records.items():self.store.write(name,value)
        self.command=['/inert/worker','--worker'];binding=dict(inherited_fds=[r['fd'] for r in f.resources],canonical_metadata_bound=True,
            lock_ownership_independently_proved=False,resource_release_authorized=False)
        self.records=dict(OWNER=dict(owner_pid=os.getpid(),child_pid=500,target=A.TARGET,command=self.command,cpu_credits=8,token_indexes=list(range(8)),
                io_mode='EX_GLOBAL',inherited_resource_fds=f.resources,admission_nonce='a'*32,owner_observation_deadline=1000.),
            BOUND=dict(command=self.command,admission_nonce='a'*32),
            BINDING=dict(schema='unison-current-named-worker-binding/1',parent_pid=os.getpid(),worker_pid=500,resource_fds=f.resources,binding=binding),
            CLOSED=dict(result_complete=False,worker_metadata_closed=True,inherited_resource_fds_closed=False,resource_release_authorized=False))
        self.readers=[]
    def outcome(self,pid=500):
        return dict(command=self.command,returncode=0,timed_out=False,capture_truncated=False,stdout='',stderr='',
            client_cleanup=dict(pid=pid,returncode=0,reaped=True,hard_kill_required=False,other_group_members_absent_before_reap=True,
                group_cleanup_before_leader_reap=True),aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False)
    def audit(self,skip=(),pid=500):
        names=dict(OWNER='OWNER-START.json',BOUND='ADMISSION-BOUND.json',BINDING='WORKER-BINDING.json',CLOSED='WORKER-CLOSED.json')
        for key,name in names.items():
            if key not in skip:self.store.write(name,self.records[key])
        self.store.write('RESULT.json',self.fixture.result)
        def reader(*args):
            value=Reader(*args);self.readers.append(value);return value
        return parent_runtime.audit(self.fixture.packet,self.store,self.outcome(pid),reader=reader)
    def test_settled_failed_prefix_is_audited_incomplete_and_reader_closed(self):
        value=self.audit();self.assertFalse(value['complete']);self.assertTrue(value['external_children_settled'])
        self.assertEqual(value['replay']['raw_pairs_reparsed'],1);self.assertFalse(value['resource_release_authorized'])
        self.assertTrue(all(r.closed for r in self.readers))
    def test_other_worker_pid_or_binding_refuses_and_closes_reader(self):
        with self.assertRaises(ValueError):self.audit(pid=501)
        self.setUp();self.records['BINDING']['worker_pid']=501
        with self.assertRaisesRegex(ValueError,'inherited binding'):self.audit()
    def test_missing_worker_closure_is_not_settlement(self):
        with self.assertRaises(FileNotFoundError):self.audit(skip=('CLOSED',))
    def test_raw_replay_failure_closes_reader_and_propagates(self):
        (self.root/'resume-complete-pass'/'merge.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'must verify actual bytes'):self.audit()
        self.assertTrue(self.readers and all(r.closed for r in self.readers))

if __name__=='__main__':unittest.main()
