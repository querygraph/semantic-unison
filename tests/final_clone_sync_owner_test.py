import copy,json,unittest
from pathlib import Path
from final_clone_sync_owner import fixtures,with_policy,audit_refusal
from clone_interruption_transport_test import child
from batch_commands import schedule


def pair():
 frame=dict(schema='unison-retained-merge-proxy/1',server_command=['server'],server_pid=33,server_returncode=0,server_reaped=True,server_group=22,input_eof_forwarded=True,output_eof_forwarded=True,forwarded_protocol_bytes=dict(client_to_server_bytes=123,server_to_client_bytes=456),parent_group_audit_required=True,sdk_helper_audit_required=True,resource_release_authorized=False)
 client=child(['client'],2,11);client['stdout']='Receiver filesystem cannot clone this basis: restricted flags'
 return dict(client=client,proxy=child(['proxy'],0,22),raw_proxy=json.dumps(frame),external_sdk_audit_required=True,resource_release_authorized=False)
def audit(value):return audit_refusal(value,client_command=['client'],proxy_command=['proxy'],server_command=['server'])
class Controls(unittest.TestCase):
 def test_original_seven_cases_keep_expected_extent_relationships(self):
  original,rows=fixtures();cases=dict(rows)
  self.assertEqual(list(cases),['same-offset','insert-prefix','delete-prefix','duplicate-shift','all-literals','shorten','extend'])
  self.assertEqual(cases['same-offset'][:15000],original[:15000]);self.assertEqual(cases['same-offset'][15008:],original[15008:]);self.assertEqual(cases['same-offset'][15000:15008],b'CHANGED!')
  self.assertEqual(cases['insert-prefix'],b'inserted prefix'+original);self.assertEqual(cases['delete-prefix'],original[193:]);self.assertEqual(cases['duplicate-shift'],original[65536:]+original[:65536]);self.assertEqual(len(cases['all-literals']),len(original));self.assertNotEqual(cases['all-literals'],original);self.assertEqual(cases['shorten'],original[:800000]);self.assertEqual(cases['extend'],original+b'new end'*10000)
 def test_policy_sets_both_endpoints_without_mutating_template(self):
  base=schedule('/private/tmp/bin','/private/tmp/bin','/private/tmp/test',mode='receiver-clone',workers=2)['rows'][0];saved=copy.deepcopy(base)
  for policy in ('auto','off','require'):
   row=with_policy(base,policy)
   for name in ('command','server_command','server_flags'):self.assertEqual(row[name][row[name].index('-clone')+1],policy)
   self.assertEqual(base,saved)
  with self.assertRaises(ValueError):with_policy(base,'unknown')
 def test_only_specific_normal_require_refusal_is_accepted(self):
  self.assertEqual(audit(pair())['client_exit'],2)
  for code in (0,1,3,-9):
   value=pair();value['client']['returncode']=value['client']['client_cleanup']['returncode']=code
   with self.assertRaises(ValueError):audit(value)
  for text in ('another error','Lost connection: cannot clone this basis'):
   value=pair();value['client']['stdout']=text
   with self.assertRaises(ValueError):audit(value)
 def test_refusal_needs_each_actual_peer_and_native_reap(self):
  for role in ('client','proxy'):
   for key in ('reaped','other_group_members_absent_before_reap','group_cleanup_before_leader_reap'):
    value=pair();value[role]['client_cleanup'][key]=False
    with self.assertRaises(ValueError):audit(value)
  for key,v in [('server_reaped',False),('server_returncode',2),('server_command',['other']),('server_group',99),('resource_release_authorized',True)]:
   value=pair();frame=json.loads(value['raw_proxy']);frame[key]=v;value['raw_proxy']=json.dumps(frame)
   with self.assertRaises(ValueError):audit(value)
 def test_refusal_does_not_turn_producer_claim_into_release(self):
  for key in ('io_cpu_release_authorized','aggregate_or_parent_terminal_proved'):
   value=pair();value['client'][key]=True
   with self.assertRaises(ValueError):audit(value)
if __name__=='__main__':unittest.main()
