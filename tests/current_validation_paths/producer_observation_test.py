"""Original generated source bytes/tiny counters only; no child or signal."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from current_validation_paths.files import Files
from current_validation_paths.producer_observation import Observer

class Producer(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='vpp-',dir='/private/tmp');root=Path(self.temp.name);st=root.lstat()
        self.setup_files=Files(root,(st.st_dev,st.st_ino));self.root=self.setup_files.Path(root)
        for name in ('left','right'):(self.root/name).mkdir()
        self.source=bytes(range(256))*8192+b'synthetic resume tail\n';(self.root/'left/resumed.DNG').write_bytes(self.source)
        self.observers=[]
    def tearDown(self):
        for observer in self.observers:observer.close()
        self.setup_files.close();self.temp.cleanup()
    def prepare(self,kind='complete'):
        data=self.source if kind=='complete' else self.source[:len(self.source)//2]
        candidate=self.root/'right/.resumed.DNG.stage.unison.tmp';candidate.write_bytes(data);st=candidate.lstat()
        config=dict(root=str(self.root),identity=[self.root.lstat().st_dev,self.root.lstat().st_ino],name='resumed.DNG',kind=kind,
            source_bytes=len(self.source),source_sha256=hashlib.sha256(self.source).hexdigest(),staged_bytes=len(data),staged_sha256=hashlib.sha256(data).hexdigest())
        self.record=dict(source=str(self.root/'left/resumed.DNG'),destination=str(candidate),pid=301,group=301,
            size=len(data),sha256=hashlib.sha256(data).hexdigest(),device=st.st_dev,inode=st.st_ino,interrupt=kind,nofile_hard=256)
        self.counter=self.root/'external-copy.calls.jsonl';self.counter.write_text(json.dumps(self.record)+'\n')
        observer=Observer(config);self.observers.append(observer);return observer
    def signal(self):return dict(pid=200,signal=9,owned_unreaped_before_signal=True,group=199)
    def test_complete_stage_observation_then_release_never_signals_recorded_producer(self):
        observer=self.prepare();result=observer.observe();self.assertEqual(result['record'],self.record)
        release=observer.release(self.signal());self.assertFalse(release['producer_signalled']);self.assertTrue(observer.marker.exists())
        with self.assertRaises(ValueError):observer.release(self.signal())
    def test_partial_stage_is_exact_prefix_and_original_inode(self):
        observer=self.prepare('partial');result=observer.observe();self.assertEqual(result['staged_bytes'],len(self.source)//2)
        self.assertEqual(result['record']['inode'],Path(self.record['destination']).lstat().st_ino)
    def test_partial_counter_waits_without_stage_event(self):
        observer=self.prepare();self.counter.write_text(json.dumps(self.record))
        self.assertIsNone(observer.observe());self.assertIsNone(observer.observed)
    def test_replaced_stage_or_mutated_source_refuses(self):
        observer=self.prepare();p=self.root.__class__(self.record['destination']);p.write_bytes(b'corrupt')
        with self.assertRaises(ValueError):observer.observe()
    def test_early_validator_or_destination_publication_refuses(self):
        observer=self.prepare();(self.root/'server-validator.calls.jsonl').write_text('{}\n')
        with self.assertRaises(ValueError):observer.observe()
    def test_release_refuses_signal_of_counter_pid(self):
        observer=self.prepare();observer.observe();signal=self.signal();signal['pid']=301
        with self.assertRaises(ValueError):observer.release(signal)
        self.assertFalse(observer.marker.exists())
        with self.assertRaises(ValueError):observer.release(self.signal())
    def test_modified_stage_after_observation_refuses_release(self):
        observer=self.prepare();observer.observe();self.root.__class__(self.record['destination']).write_bytes(b'changed')
        with self.assertRaises(ValueError):observer.release(self.signal())
        self.assertFalse(observer.marker.exists())
    def test_old_release_marker_cannot_be_reused(self):
        observer=self.prepare();observer.marker.write_bytes(b'old')
        with self.assertRaises(ValueError):observer.observe()

if __name__=='__main__':unittest.main()
