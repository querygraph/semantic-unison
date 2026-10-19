"""Actual tiny private records read by the parent adapters; no child/SDK/payload."""
import json,os,shutil,tempfile,unittest
from pathlib import Path
from current_validation_paths import parent,recipes
from current_validation_paths.parent_io import Reader
from current_validation_paths import parent_test as base


class Records(unittest.TestCase):
    def setUp(self):
        self.workspace=Path(tempfile.mkdtemp(prefix='u-vpath-io-'));self.addCleanup(shutil.rmtree,self.workspace)
        self.fixture=base.Replay('test_failed_original_prefix_can_be_replayed_without_benchmark_pass_or_release')
        self.case=self.workspace/'resumed-complete';self.case.mkdir(0o700)
        native=self.case.lstat();self.fixture.case_identity=(native.st_dev,native.st_ino);self.fixture.setUp()
        f=self.fixture;row=f.packet['rows'][0];self.case=self.case.rename(self.workspace/Path(row['directory']).name)
        self.roots={row['directory']:self.case.name}
        def write(path,data,mode=0o600):
            path.write_bytes(data);path.chmod(mode)
        for (root,record),raw in f.records.items():write(self.case/record,raw)
        for script,text in f.scripts.items():write(self.case/script,text.encode(),0o700)
        write(self.case/'call-001-proxy.py',recipes.proxy_source(f.packet['repository'],f.config).encode(),0o700)
        (self.case/'server-state').mkdir(0o700);write(self.case/'server-state/endpoint.prf',f.phase['server_profile_text'].encode())
        write(self.case/'external-copy.calls.jsonl',b''.join(json.dumps(v).encode()+b'\n' for v in f.state['counters']['copy']),0o644)
        for record,value in f.root_records.items():write(self.workspace/record,json.dumps(value).encode())
        st=self.workspace.lstat();self.identity=dict(device=st.st_dev,inode=st.st_ino)
    def reader(self):
        reader=Reader(str(self.workspace),self.identity,self.roots);self.addCleanup(lambda:reader.closed or reader.close());return reader
    def replay(self):
        f=self.fixture;reader=self.reader()
        return parent.replay(f.packet,f.result,source=base.SOURCE,
            worker_pid=500,resources=f.resources,owner_deadline=1000.,read_case=reader.read_case,read_root=reader.read_root,case_state=reader.case_state)
    def test_actual_private_records_replay_failed_prefix_without_release(self):
        value=self.replay();self.assertFalse(value['complete']);self.assertEqual(value['producer_interruptions'],1)
        self.assertFalse(value['resource_release_authorized']);self.assertFalse(value['parent_terminal_proved'])
    def test_symlinked_record_refuses(self):
        target=self.workspace/'outside.json';shutil.copyfile(self.case/'call-001-AUDIT.json',target)
        (self.case/'call-001-AUDIT.json').unlink();(self.case/'call-001-AUDIT.json').symlink_to(target)
        with self.assertRaises(OSError):self.replay()
    def test_hardlinked_record_refuses(self):
        os.link(self.case/'call-001-PAIR.json',self.workspace/'alias.json')
        with self.assertRaisesRegex(ValueError,'single-link'):self.replay()
    def test_unreported_call_in_case_directory_refuses(self):
        (self.case/'call-002-INTENT.json').write_text('{}');(self.case/'call-002-INTENT.json').chmod(0o600)
        with self.assertRaisesRegex(ValueError,'absent from worker inventory'):self.replay()
    def test_changed_generated_script_refuses(self):
        path=self.case/'merge.py';path.write_text(path.read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'must verify actual bytes'):self.replay()
    def test_changed_profile_refuses(self):
        path=self.case/'server-state/endpoint.prf';path.write_text(path.read_text()+'x = y\n')
        with self.assertRaisesRegex(ValueError,'must verify actual bytes'):self.replay()
    def test_duplicate_counter_key_refuses(self):
        (self.case/'merge.calls.jsonl').write_text('{"pid":1,"pid":2}\n')
        with self.assertRaisesRegex(ValueError,'duplicate'):self.replay()
    def test_truncated_counter_line_refuses(self):
        path=self.case/'external-copy.calls.jsonl';path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaisesRegex(ValueError,'complete counter lines'):self.replay()
    def test_symlinked_case_directory_refuses(self):
        moved=self.workspace/'moved';self.case.rename(moved);self.case.symlink_to(moved)
        with self.assertRaises(OSError):self.replay()
    def test_undeclared_root_and_identity_and_closed_reader_refuse(self):
        reader=self.reader()
        with self.assertRaisesRegex(ValueError,'undeclared case root'):reader.read_case(str(self.workspace/'other'),'call-001-PAIR.json')
        with self.assertRaisesRegex(ValueError,'private named directory changed'):Reader(str(self.workspace),dict(device=1,inode=2),self.roots)
        reader.close()
        with self.assertRaisesRegex(ValueError,'reader closed'):reader.read_root('case-00-START.json')

if __name__=='__main__':unittest.main()
