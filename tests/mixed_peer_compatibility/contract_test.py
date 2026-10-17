"""Original command controls; no binaries, payload or pools opened."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contract import command, CASES, CURRENT_FLAGS, OLD_FLAGS

class Commands(unittest.TestCase):
    artifacts=dict(stock='/inert/stock',ox='/inert/ox',**{'old-stock':'/inert/old'})
    def test_all_twelve(self):
        for i,(current,orientation) in enumerate(CASES):
            for stage in ('seed','update','noop'):
                argv,server=command(self.artifacts,'/private/tmp/inert',i,stage)
                old=orientation=='old-client'
                self.assertEqual(argv[0],self.artifacts['old-stock' if old else current])
                self.assertEqual(argv[argv.index('-servercmd')+1],self.artifacts[current if old else 'old-stock'])
                self.assertEqual(server,list(CURRENT_FLAGS if old else OLD_FLAGS))
                self.assertEqual(argv[-len(OLD_FLAGS if old else CURRENT_FLAGS):],list(OLD_FLAGS if old else CURRENT_FLAGS))
                self.assertIn('/'+stage+'/launcher.py',argv[argv.index('-sshcmd')+1])
    def test_bad_case(self):
        for index in (-1,4,True):
            with self.assertRaises(ValueError):command(self.artifacts,'/private/tmp/inert',index,'seed')
    def test_bad_stage(self):
        with self.assertRaises(ValueError):command(self.artifacts,'/private/tmp/inert',0,'retry')
    def test_missing_old(self):
        with self.assertRaises(ValueError):command({'stock':'/x','ox':'/y'},'/private/tmp/inert',0,'seed')
    def test_relative(self):
        with self.assertRaises(ValueError):command(self.artifacts,'relative',0,'seed')
if __name__=='__main__':unittest.main()
