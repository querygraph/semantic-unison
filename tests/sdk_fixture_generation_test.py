import hashlib,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import sdk_fixture_generation as G
from sdk_fixture_generation_owner import sdk_command,accepted
from sdk_fixture_states import states
from sdk_fixture_states_test import fixture
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership
from final_clone_interruption_owner import can_close_failed_prefix


class Generation(unittest.TestCase):
    def setup(self,name):
        path=Path(name)/'states';path.mkdir(mode=0o700);s=path.stat();fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
        return path,fd,(s.st_dev,s.st_ino)
    def test_twelve_readonly_distinct_files_exact_hashes_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            path,fd,identity=self.setup(name);inodes=[]
            try:
                for codec in ('uncompressed','jpeg','jxl'):
                    for state,data in states(fixture(codec),codec)['states'].items():
                        out=G.write_state(fd,str(path),identity,codec,state,data);inodes.append(out['identity']['st_ino'])
                        self.assertEqual(Path(out['path']).read_bytes(),data);self.assertEqual(out['sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(out['identity']['st_mode'],0o100400)
                with self.assertRaises(FileExistsError):G.write_state(fd,str(path),identity,'jxl','target',b'preserve original file')
                self.assertEqual(len(set(inodes)),12);self.assertEqual(len(list(path.iterdir())),12)
            finally:close_descriptors([fd])
    def test_short_writes_complete_and_zero_write_refuses_preserving_partial(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            path,fd,identity=self.setup(name);real=os.write
            try:
                with patch.object(G.os,'write',side_effect=lambda f,b:real(f,b[:3])):out=G.write_state(fd,str(path),identity,'jpeg','left',b'original bounded output')
                self.assertEqual(Path(out['path']).read_bytes(),b'original bounded output')
                with patch.object(G.os,'write',return_value=0):
                    with self.assertRaises(ValueError):G.write_state(fd,str(path),identity,'jpeg','right',b'other bytes')
                self.assertTrue((path/'jpeg-right.dng').exists())
            finally:close_descriptors([fd])
    def test_directory_identity_failure_precedes_file_creation(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            path,fd,identity=self.setup(name)
            try:
                with self.assertRaises(ValueError):G.write_state(fd,str(path),(identity[0],identity[1]+1),'jpeg','base',b'bytes')
                self.assertEqual(list(path.iterdir()),[])
            finally:close_descriptors([fd])
    def test_fsync_failure_keeps_failed_file_and_closes_owned_fd(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            path,fd,identity=self.setup(name);baseline=len(os.listdir('/dev/fd'))
            try:
                with patch.object(G.os,'fsync',side_effect=OSError('original injected fsync failure')):
                    with self.assertRaises(OSError):G.write_state(fd,str(path),identity,'jpeg','base',b'bytes')
                self.assertTrue((path/'jpeg-base.dng').exists());self.assertEqual(len(os.listdir('/dev/fd')),baseline)
            finally:close_descriptors([fd])
    def test_close_uncertainty_carrier_preserved_once_and_cannot_release_prefix(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            path,fd,identity=self.setup(name);injected=UnresolvedOwnership('original close uncertainty',uncertain_fd=987);calls=[]
            def fail_after_fixture_close(fds):calls.append(tuple(fds));close_descriptors(fds);raise injected
            try:
                with patch.object(G,'close_descriptors',side_effect=fail_after_fixture_close):
                    with self.assertRaises(UnresolvedOwnership) as caught:G.write_state(fd,str(path),identity,'jpeg','base',b'bytes')
                self.assertIs(caught.exception,injected);self.assertEqual(len(calls),1);self.assertFalse(can_close_failed_prefix(active=False,error=caught.exception))
            finally:close_descriptors([fd])
    def test_exact_validator_protocol_command_and_full_digest_requirement(self):
        ref=dict(path='/private/tmp/owned/jpeg-base.dng',sha256='a'*64,bytes=4096)
        self.assertEqual(sdk_command('/private/tmp/tool',ref),['/private/tmp/tool','--unison-dng-validation-v1','--expected-sha256','a'*64,'--expected-size','4096','--threads','1','--',ref['path']])
        lines=['UNISON-DNG-VALIDATION 1','candidate-sha256 '+'a'*64,'candidate-size 4096','driver-build unison-sdk171-2724-v1-single','structure valid','decode success','raw-digest valid','errors 0','warnings 0','END','']
        out=dict(returncode=0,timed_out=False,capture_truncated=False,stdout='\n'.join(lines),client_cleanup=dict(returncode=0,reaped=True,other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True,hard_kill_required=False))
        self.assertTrue(accepted(out,ref)['raw_digest_verified'])
        for before,after in (('raw-digest valid','raw-digest missing'),('candidate-size 4096','candidate-size 4097'),('errors 0','errors 1')):
            changed=dict(out,stdout=out['stdout'].replace(before,after))
            with self.assertRaises(ValueError):accepted(changed,ref)
        with self.assertRaises(ValueError):accepted(dict(out,capture_truncated=True),ref)


# Full original orchestration uses only trusted Python doubles and tiny bytes.
# No fake SDK path is executable; no production packet can select these seams.
class Composition(unittest.TestCase):
    def run_original(self,root,*,fail_at=None,uncertain=False,mutate_first=False):
        import sdk_fixture_generation_owner as O
        from sdk_merge_receiving.store import Store
        from sdk_fixture_preservation_test import copied
        from sdk_fixture_preservation import preserve_one
        root=Path(root);destination=root/'outputs';destination.mkdir(mode=0o700);records=root/'records';records.mkdir(mode=0o700)
        s=records.stat();store=Store(str(records),dict(device=s.st_dev,inode=s.st_ino));parent=os.open(destination,os.O_RDONLY|os.O_DIRECTORY);s=destination.stat();identity=(s.st_dev,s.st_ino)
        references=[]
        for codec in ('uncompressed','jpeg'):
            path=root/(codec+'-retained.dng');data=fixture(codec);path.write_bytes(data);path.chmod(0o400)
            references.append(dict(codec=codec,path=str(path),identity=O.stamp(path.stat()),sha256=hashlib.sha256(data).hexdigest()))
        packet=dict(sources=references,writer=dict(path='/original-nonexistent/fake-writer'),validator=dict(path='/original-nonexistent/fake-validator'),source_pins={'original-control':'a'*64},prerequisites=[dict(path='/original-nonexistent/ancestry.json',sha256='b'*64)])
        calls=[];seen=[];checks=[]
        def invoke(argv,seconds):
            seen.append(list(argv));index=len(seen)
            if argv[0]==packet['writer']['path']:
                self.assertEqual((index,seconds),(1,120));self.assertEqual(argv[1],'jxl');Path(argv[3]).write_bytes(fixture('jxl'));out={}
            else:
                self.assertEqual((argv[0],seconds),(packet['validator']['path'],90));path=Path(argv[-1]);raw=path.read_bytes()
                sha=hashlib.sha256(raw).hexdigest();self.assertEqual(argv,sdk_command(packet['validator']['path'],dict(path=str(path),sha256=sha,bytes=len(raw))))
                if fail_at==index-1:
                    if uncertain:raise UnresolvedOwnership('original injected fake SDK uncertainty',uncertain_fd=987)
                    raise ValueError('original injected fake SDK finding')
                lines=['UNISON-DNG-VALIDATION 1','candidate-sha256 '+sha,'candidate-size '+str(len(raw)),'driver-build unison-sdk171-2724-v1-single','structure valid','decode success','raw-digest valid','errors 0','warnings 0','END','']
                out=dict(returncode=0,timed_out=False,capture_truncated=False,stdout='\n'.join(lines),client_cleanup=dict(returncode=0,reaped=True,other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True,hard_kill_required=False),original_fake_only=True)
                if mutate_first and index==13:os.utime(destination/'uncompressed-base.dng',ns=(1,1))
            calls.append(store.write('fake-call-%02d.json'%index,out));return out
        def fence():
            for ref in references:self.assertEqual(O.stamp(os.lstat(ref['path'])),ref['identity'])
            checks.append(True)
        try:
            result=O.generate(packet,records,destination,parent,identity,store,invoke,fence,calls,clone_one=lambda *args:preserve_one(*args,clone=copied))
            return result,seen,checks
        finally:
            self.last_seen=seen;self.last_destination=destination;store.close();close_descriptors([parent])
    def test_complete_one_writer_twelve_validators_and_manifest_ancestry(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            result,seen,checks=self.run_original(name)
            self.assertEqual((len(seen),len(result['reports']),len(checks)),(13,12,1))
            import json
            manifest=json.loads(Path(result['input_manifest']['path']).read_text())
            self.assertEqual([c['codec'] for c in manifest['cases']],['uncompressed','jpeg','jxl'])
            self.assertTrue(all(set(c['states'])=={'base','left','right','target'} for c in manifest['cases']))
            self.assertEqual(len(manifest['ancestry']),2);self.assertTrue(Path(manifest['ancestry'][-1]['path']).exists())
            self.assertFalse(result['parent_tool_terminal_proved'])
    def test_first_sdk_finding_stops_without_success_manifest_or_retry(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            with self.assertRaisesRegex(ValueError,'fake SDK finding'):self.run_original(name,fail_at=1)
            self.assertEqual(len(self.last_seen),2);self.assertFalse((self.last_destination/'INPUT-MANIFEST.json').exists())
            self.assertTrue((self.last_destination/'uncompressed-base.dng').exists())
    def test_sdk_uncertainty_propagates_without_successor_or_prefix_release(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            with self.assertRaises(UnresolvedOwnership) as caught:self.run_original(name,fail_at=2,uncertain=True)
            self.assertEqual(len(self.last_seen),3);self.assertFalse(can_close_failed_prefix(active=False,error=caught.exception))
            self.assertFalse((self.last_destination/'INPUT-MANIFEST.json').exists())
    def test_late_prior_state_mutation_prevents_batch_manifest(self):
        with tempfile.TemporaryDirectory(prefix='unison-original-sdk-states-',dir='/private/tmp') as name:
            with self.assertRaisesRegex(ValueError,'batch epoch changed'):self.run_original(name,mutate_first=True)
            self.assertEqual(len(self.last_seen),13);self.assertFalse((self.last_destination/'INPUT-MANIFEST.json').exists())

if __name__=='__main__':unittest.main()
