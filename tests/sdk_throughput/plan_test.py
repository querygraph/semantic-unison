import collections
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sdk_throughput.plan import comparison
from sdk_multifile.plan import BUILD


class Planning(unittest.TestCase):
    def fixture(self):
        return {n:dict(label=n,path='/inert/'+n,sha256='a'*64) for n in ('stock','ox')},dict(path='/inert/sdk',sha256='b'*64,build_id=BUILD,threads=1)
    def test_exact_finite_repetitions_and_unused_namespaces(self):
        b,t=self.fixture();p=comparison(b,t,'/private/tmp/u-st-unit')
        counts=collections.Counter((r['label'],r['endpoint_workers'],r['phase']) for r in p['rows'])
        self.assertEqual(len(p['rows']),24);self.assertEqual(len({r['directory'] for r in p['rows']}),24)
        for label in ('stock','ox'):
            for workers in (1,3):
                self.assertEqual(counts[label,workers,'warmup'],1);self.assertEqual(counts[label,workers,'measured'],5)
        self.assertEqual(p['maximum_sdk_calls'],48);self.assertFalse(p['runtime_admitted']);self.assertFalse(p['runtime_dispatcher_qualified'])
    def test_exact_both_endpoint_cpu_and_qualified_sdk_contract(self):
        b,t=self.fixture();p=comparison(b,t,'/private/tmp/u-st-unit')
        for r in p['rows']:
            flags=r['server_flags'];self.assertEqual(r['command'][-len(flags):],flags)
            for key in ('-semanticworkers','-maxthreads'):self.assertEqual(flags[flags.index(key)+1],str(r['endpoint_workers']))
            self.assertEqual(flags[flags.index('-adobevalidatorthreads')+1],'1')
            self.assertEqual(flags[flags.index('-semanticmaxinflight')+1],'4')
            self.assertLessEqual(r['configured_endpoint_and_owner_credits'],r['reserved_cpu_credits'])
        self.assertNotEqual([r['label'] for r in p['rows'][:4]],[r['label'] for r in p['rows'][4:8]])
    def test_unknown_compiler_or_unqualified_tool_refuses(self):
        b,t=self.fixture()
        for invalid in [dict(t,threads=6),dict(t,threads=True),dict(t,build_id='unknown')]:
            with self.assertRaises(ValueError):comparison(b,invalid,'/private/tmp/u-st-unit')
        with self.assertRaises(ValueError):comparison(dict(b,other=b['stock']),t,'/private/tmp/u-st-unit')


if __name__=='__main__':unittest.main()
