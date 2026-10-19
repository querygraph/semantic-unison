import copy,unittest
from final_dng_component_owner import audit_calls

def out(command,code=0,stderr=''):
 return dict(command=command,returncode=code,timed_out=False,capture_truncated=False,stdout='original checks',stderr=stderr,aggregate_or_parent_terminal_proved=False,io_cpu_release_authorized=False,client_cleanup=dict(pid=1234,returncode=code,reaped=True,other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True,hard_kill_required=False))
def fixture():
 calls=[]
 for c in ('stock','ox'):
  calls += [out(['/private/tmp/'+c+'/dng-component-controls']),out(['/private/tmp/'+c+'/archive-reference-fault']),out(['/private/tmp/'+c+'/dng-component-ablation'],2,'changed named record escaped lookup before reader retirement')]
 for name in ('cache_capture','owner_index_publication'):calls.append(out(['compiler','-c','owner_only_'+name+'.ml'],2,'nonportable'))
 return dict(calls=calls)
class Audit(unittest.TestCase):
 def test_exact_normal_and_four_designated_negative_calls(self):
  r=audit_calls(fixture());self.assertEqual((r['calls'],r['zero'],r['expected_two']),(8,4,4))
 def test_wrong_negative_reason_or_arbitrary_failure_refuses(self):
  for field,value in [('stderr','different failure'),('returncode',1)]:
   r=fixture();r['calls'][2][field]=value
   with self.assertRaises(ValueError):audit_calls(r)
  r=fixture();r['calls'].append(out(['unexpected'],2))
  with self.assertRaises(ValueError):audit_calls(r)
 def test_missing_group_or_capture_proof_never_qualifies(self):
  for key in ('reaped','other_group_members_absent_before_reap','group_cleanup_before_leader_reap'):
   r=fixture();r['calls'][0]['client_cleanup'][key]=False
   with self.assertRaises(ValueError):audit_calls(r)
  r=fixture();r['calls'][0]['capture_truncated']=True
  with self.assertRaises(ValueError):audit_calls(r)
 def test_invalid_identity_or_producer_authority_refuses(self):
  for pid in (True,0,-1,2**31,'1234'):
   r=fixture();r['calls'][0]['client_cleanup']['pid']=pid
   with self.assertRaises(ValueError):audit_calls(r)
  for key in ('aggregate_or_parent_terminal_proved','io_cpu_release_authorized'):
   r=fixture();r['calls'][0][key]=True
   with self.assertRaises(ValueError):audit_calls(r)
 def test_missing_compiler_case_or_missing_negative_refuses(self):
  r=fixture();r['calls'].pop(1)
  with self.assertRaises(ValueError):audit_calls(r)
  r=fixture();r['calls'].pop()
  with self.assertRaises(ValueError):audit_calls(r)
if __name__=='__main__':unittest.main()
