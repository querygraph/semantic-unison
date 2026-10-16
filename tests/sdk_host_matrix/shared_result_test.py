"""Inert12call frames; source-only join, no process execution."""
import copy,unittest
from shared_plan_test import Shared
from shared_plan import shared_matrix
from shared_result import audit
class Results(unittest.TestCase):
    def frames(self):
        args=Shared().values();rows=[]
        for i,c in enumerate(shared_matrix(*args)['cases'],1):
            fields=[('candidate-sha256',c['fixture']['sha256']),('candidate-size',str(c['fixture']['size'])),
                    ('driver-build',c['build_id']),('structure','valid'),('decode','success'),('raw-digest','valid'),('errors','0'),('warnings','0')]
            stdout='UNISON-DNG-VALIDATION 1\n'+'\n'.join(k+' '+v for k,v in fields)+'\nEND\n'
            n=c['threads_including_caller'];area=('tasks=0 started=0 finish=0 calls=0 active=0 peak=0 max-partition=0 reference=1' if n==1 else f'tasks=1 started=1 finish=1 calls={n} active=0 peak={n} max-partition={n} reference=0')
            stderr='UNISON-HOST-AREA 1 '+area+'\nUNISON-HOST-MEMORY 1 limit=1073741824 used=0 peak=4096 live=0 denied=0\n'
            rows.append(dict(index=i,command=c['command'],outcome=dict(returncode=0,timed_out=False,capture_truncated=False,stdout=stdout,stderr=stderr,
                client_cleanup=dict(pid=100+i,reaped=True,returncode=0,hard_kill_required=False))))
        return args,rows
    def test_full_join_does_not_release_resources(self):
        args,rows=self.frames();d=audit(*args,rows)
        self.assertEqual(d['calls'],12);self.assertEqual(d['experimental_calls'],9)
        for k in ['aggregate_group_settlement_proved','parent_terminal_proved','io_cpu_fd_closure_proved','resource_release_authorized','os_thread_scaling_proved','hard_rss_cap_proved','pixel_equivalence_proved']:self.assertFalse(d[k])
    def test_missing_duplicate_or_reordered_calls_refused(self):
        args,rows=self.frames()
        for altered in [rows[:-1],rows+[rows[-1]],list(reversed(rows)),[rows[0]]*12]:
            with self.assertRaises(ValueError):audit(*args,altered)
    def test_call_and_cleanup_uncertainty_refused(self):
        args,original=self.frames()
        for key,value in [('returncode',True),('returncode',1),('timed_out',True),('capture_truncated',True)]:
            rows=copy.deepcopy(original);rows[1]['outcome'][key]=value
            with self.assertRaises(ValueError):audit(*args,rows)
        for key,value in [('reaped',False),('pid',True),('pid',101),('returncode',1),('hard_kill_required',True)]:
            rows=copy.deepcopy(original);rows[1]['outcome']['client_cleanup'][key]=value
            with self.assertRaises(ValueError):audit(*args,rows)
    def test_decode_success_cannot_mask_unsettled_native_telemetry(self):
        args,original=self.frames()
        for old,new in [('live=0','live=1'),('used=0','used=1'),('active=0','active=1'),('denied=0','denied=1'),('finish=1','finish=0')]:
            rows=copy.deepcopy(original);rows[2]['outcome']['stderr']=rows[2]['outcome']['stderr'].replace(old,new)
            with self.assertRaises(ValueError):audit(*args,rows)
    def test_reference_difference_and_argv_tampering_refused(self):
        args,rows=self.frames();rows[1]['outcome']['stdout']=rows[1]['outcome']['stdout'].replace('warnings 0','warnings 1')
        with self.assertRaises(ValueError):audit(*args,rows)
        args,rows=self.frames();rows[2]['command']=['/different']
        with self.assertRaises(ValueError):audit(*args,rows)
if __name__=='__main__':unittest.main()
