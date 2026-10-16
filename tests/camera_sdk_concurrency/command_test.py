import copy,json,unittest
from command import command
B=dict(path='/private/tmp/current-unison',sha256='a'*64,label='stock')
T=dict(path='/private/tmp/current-validator',sha256='b'*64,threads=1,build_id='synthetic-or-separately-qualified')
class Commands(unittest.TestCase):
    def build(self,**kw):
        args=dict(binary=B,tool=T);args.update(kw);return command('/private/tmp/u-concurrent-abc',**args)
    def test_no_execution_and_exact_endpoint_flags(self):
        c=self.build();flags=json.loads(c['environment_overrides']['UNISON_SYNC_BENCH_SERVER_FLAGS'])
        self.assertEqual(c['argv'][-len(flags):],flags)
        self.assertFalse(c['runtime_admitted']);self.assertEqual(c['maximum_validator_calls'],2)
        for flag,value in [('-semanticworkers','3'),('-maxthreads','3'),('-semanticvolumejobs','2'),
                           ('-semanticmaxinflight','3'),('-adobevalidate','require'),
                           ('-adobevalidatorworkspace','2048'),('-semanticpayloadbudget','6144')]:
            self.assertEqual(flags.count(flag),1);self.assertEqual(flags[flags.index(flag)+1],value)
    def test_no_merge_update_or_base_reuse(self):
        argv=self.build()['argv']
        for flag in ['-merge','--base','-semanticdng']:
            self.assertNotIn(flag,argv)
        self.assertIn('validation-live',argv)
    def test_paths_and_socket_bounds(self):
        for path in ['relative','/private/tmp/../escape','/private/tmp/'+'a'*101]:
            with self.assertRaises(ValueError):command(path,binary=B,tool=T)
    def test_bad_executable_pins(self):
        for field,value in [('path','relative'),('sha256','bad'),('label','other')]:
            b=copy.deepcopy(B);b[field]=value
            with self.assertRaises(ValueError):self.build(binary=b)
    def test_tool_contract(self):
        for field,value in [('threads',True),('threads',2),('build_id','bad\nID'),('path','relative')]:
            t=copy.deepcopy(T);t[field]=value
            with self.assertRaises(ValueError):self.build(tool=t)
    def test_nul_refused(self):
        b=dict(B,path='/private/tmp/bad\0binary')
        with self.assertRaises(ValueError):self.build(binary=b)
if __name__=='__main__':unittest.main()
