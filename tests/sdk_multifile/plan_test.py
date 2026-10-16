import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sdk_multifile.plan import plan,BUILD

class Planning(unittest.TestCase):
    def setUp(self):
        self.binary=dict(path='/inert/stock',sha256='a'*64,label='stock')
        self.tool=dict(path='/inert/sdk',sha256='b'*64,build_id=BUILD,threads=1)
    def test_four_slots_preserve_source_and_two_consumers(self):
        p=plan(self.binary,self.tool,'/private/tmp/u-multi-test')
        self.assertEqual(p['transaction_slots'],4)
        self.assertLessEqual(p['minimum_payload_credits'],p['payload_credits'])
        self.assertEqual(sum(p['endpoint_cpu_credits'])+p['owner_cpu_credits'],8)
        self.assertFalse(p['actual_overlap_proved']);self.assertFalse(p['sdk_validation_proved'])
    def test_both_endpoint_flags_match(self):
        p=plan(self.binary,self.tool,'/private/tmp/u-multi-test')
        flags=p['server_flags'];self.assertEqual(p['command'][-len(flags):],flags)
        self.assertEqual(flags[flags.index('-semanticmaxinflight')+1],'4')
        self.assertEqual(flags[flags.index('-adobevalidatorthreads')+1],'1')
    def test_unqualified_native_threads_or_build_refused(self):
        for changes in [dict(threads=2),dict(threads=True),dict(build_id='unqualified'),dict(sha256='bad')]:
            with self.assertRaises(ValueError):plan(self.binary,dict(self.tool,**changes),'/private/tmp/u-multi-test')
    def test_bad_namespace_and_binary_refused(self):
        for path in ['relative','/private/tmp/../bad','/private/tmp/'+'x'*100]:
            with self.assertRaises(ValueError):plan(self.binary,self.tool,path)
        with self.assertRaises(ValueError):plan(dict(self.binary,label='other'),self.tool,'/private/tmp/u-multi-test')

if __name__=='__main__':unittest.main()
