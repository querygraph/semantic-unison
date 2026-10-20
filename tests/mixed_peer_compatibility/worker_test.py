"""Disposable worker-flow controls; fake call boundary, no transport/pools."""
import copy
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from mixed_peer_compatibility import worker
from shared_cpu_pool import UnresolvedOwnership

class Worker(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='unison-mixed-worker-control-')
        self.root=Path(self.temp.name);self.saved=[];self.calls=0
    def tearDown(self):self.temp.cleanup()
    def persist(self,result):self.saved.append(copy.deepcopy(result))
    def fake(self,argv,env,directory,deadline):
        self.calls+=1
        self.assertEqual(self.saved[-1]['invocations'][-1]['state'],'INTENT')
        source=Path(argv[1])/'item.dng';target=source.parent.parent/'right/item.dng'
        if directory.name!='noop':target.write_bytes(source.read_bytes())
        return dict(command=argv,returncode=0,supervisor_cleanup={'returncode':0},
                    proxy=dict(server_returncode=0,fault=None,pump_errors=[]))
    def run_worker(self):
        with patch.object(worker,'retained_call',side_effect=self.fake),patch.object(worker,'load',return_value={}),patch.object(worker,'audit',return_value={}):
            return worker.execute({'stock':'/inert/stock','ox':'/inert/ox','old-stock':'/inert/old'},self.root,time.monotonic()+300,self.persist)
    def test_twelve(self):
        result=self.run_worker();self.assertTrue(result['complete']);self.assertEqual(self.calls,12)
        self.assertEqual(len(result['invocations']),12)
        self.assertTrue(all(len(c['stages'])==3 for c in result['cases']))
    def test_unknown_stays_intent(self):
        def unknown(*args):raise UnresolvedOwnership('unknown actual owner',retained_fds=(999,))
        self.fake=unknown
        with self.assertRaises(UnresolvedOwnership) as error:self.run_worker()
        self.assertEqual(error.exception.retained_fds,(999,))
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'INTENT')
    def test_known_failure_outcome_before_abort(self):
        original=self.fake
        def failed(*args):
            out=original(*args);out['returncode']=7;return out
        self.fake=failed
        with self.assertRaises(ValueError):self.run_worker()
        self.assertEqual(self.calls,1)
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'OUTCOME')
        self.assertFalse(self.saved[-1]['complete'])
    def test_wrong_received_bytes_stops_after_outcome(self):
        original=self.fake
        def corrupt(argv,env,directory,deadline):
            out=original(argv,env,directory,deadline)
            (Path(argv[1]).parent/'right/item.dng').write_bytes(b'wrong')
            return out
        self.fake=corrupt
        with self.assertRaises(ValueError):self.run_worker()
        self.assertEqual(self.calls,1)
        self.assertEqual(self.saved[-1]['invocations'][0]['state'],'OUTCOME')
    def test_noop_replacement_refused(self):
        original=self.fake
        def replace(argv,env,directory,deadline):
            out=original(argv,env,directory,deadline)
            if directory.name=='noop':
                target=Path(argv[1]).parent/'right/item.dng'
                replacement=target.with_name('replace')
                replacement.write_bytes(target.read_bytes());replacement.replace(target)
            return out
        self.fake=replace
        with self.assertRaises(ValueError):self.run_worker()
        self.assertEqual(self.calls,3)
if __name__=='__main__':unittest.main()
