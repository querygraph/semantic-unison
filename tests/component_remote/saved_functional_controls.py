"""Original producer-shape and receipt-only auditor controls; no RPC/pool IO."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote import io, case, saved_functional as saved
from component_remote.contract import CASES, FLAGS, command

def call(plan,index):
 p=900+index*3;server=plan['artifacts'][CASES[index][1]]['path'];base=[server,'-server','__new-rpc-mode']
 return dict(command=command(plan,index),returncode=0,timed_out=False,capture_truncated=False,
  supervisor_capture_truncated=False,
  client_cleanup=dict(pid=p,returncode=0,reaped=True,hard_kill_required=False,
   other_group_members_absent_before_reap=True,group_cleanup_before_leader_reap=True),
  supervisor_cleanup=dict(pid=p+1,returncode=0,reaped=True,other_group_members_absent_before_reap=True,
   members_before_reap=[dict(pid=p+1,state='Z')],timed_out=False,
   scope='owned group only; separate sessions require independently audited proofs',group_cleanup_before_leader_reap=True),
  proxy=dict(schema='unison-loopback-protocol-count/1',server_pid=p+2,server_returncode=0,
   server_cleanup=dict(pid=p+2,returncode=0,reaped=True,cancel_reason=None,hard_kill_required=False),
   server_command=base+FLAGS,launcher_control_header_bytes_excluded=4+len(json.dumps(base).encode()),
   server_group_binding=dict(native_pid=p+2,native_process_group=p+1,supervisor_pid=p+1,
    supervisor_process_group=p+1,observed_before_native_reap=True),input_pump_joined=True,
   pump_errors=[],fault=None),stdout='')

def files(work):
 plan=dict(workspace=str(work),artifacts={k:dict(path='/fixed/'+k) for k in
  ('stock','ox','old-stock','stock-probe','ox-probe')})
 result=dict(schema='component-remote-result/1',complete=False,cases=[],failure="KeyError('cancel_reason')")
 for index,(_,_,mode) in enumerate(CASES):
  directory=work/str(index);directory.mkdir(mode=0o700)
  for side in ('left','right'):
   parent=directory/side;parent.mkdir(mode=0o700)
   io.write(parent/'components.dng',case.fixture(side=='right',side=='right' and mode=='unsupported'))
  before=case.snapshot(directory);v=call(plan,index)
  v['stdout']='PROBE_FUNCTIONAL '+mode+'\nPROBE_LOCAL_RESOURCES_CLOSED (external client/server wait proofs still required)\n'
  if mode=='supported':v['stdout']+='LOCAL_SHA256 '+before['left']['sha256']+'\nREMOTE_SHA256 '+before['right']['sha256']+'\nEncoded pixels: equal.\nOpaque bytes: different.\n'
  if mode=='unsupported':v['stdout']+='REMOTE_UNSUPPORTED not TIFF\n'
  io.save(directory/'INTENT.json',dict(index=index,command=command(plan,index)))
  io.save(directory/'OUTCOME.json',v);io.save(directory/'proxy.json',v['proxy'])
  result['cases'].append(dict(index=index,mode=mode,before=before,after=deepcopy(before),outcome=v))
 return plan,result

class Controls(unittest.TestCase):
 def test_actual_producer_shapes_need_no_invented_cancel_reason(self):
  p=dict(workspace='/fixed/work',artifacts={k:dict(path='/fixed/'+k) for k in ('stock','ox','old-stock','stock-probe','ox-probe')})
  v=call(p,0);saved.successful_call(v)
  self.assertNotIn('cancel_reason',v['client_cleanup']);self.assertNotIn('cancel_reason',v['supervisor_cleanup'])
  mutations=[lambda v:v['client_cleanup'].update(cancel_reason=None),
   lambda v:v['supervisor_cleanup'].update(cancel_reason=None),
   lambda v:v['client_cleanup'].update(reaped=False),lambda v:v['client_cleanup'].update(hard_kill_required=True),
   lambda v:v['client_cleanup'].update(returncode=1),lambda v:v['supervisor_cleanup'].update(timed_out=True),
   lambda v:v['supervisor_cleanup'].update(other_group_members_absent_before_reap=False),
   lambda v:v['supervisor_cleanup'].update(members_before_reap=[dict(pid=999999,state='S')]),
   lambda v:v['proxy'].update(input_pump_joined=False),
   lambda v:v['proxy']['server_cleanup'].update(cancel_reason='SIGTERM'),
   lambda v:v['proxy']['server_cleanup'].pop('cancel_reason'),
   lambda v:v['proxy']['server_cleanup'].update(hard_kill_required=True),lambda v:v.update(timed_out=True)]
  for mutate in mutations:
   with self.subTest(mutation=mutate):
    bad=deepcopy(v);mutate(bad)
    with self.assertRaises((ValueError,KeyError)):saved.successful_call(bad)
 def test_saved_case_audit_preserves_original_result_and_never_reads_payload(self):
  with tempfile.TemporaryDirectory() as raw:
   work=Path(raw);plan,result=files(work);original=deepcopy(result)
   from unittest.mock import patch
   # Guard the IO helper: the audit may read only the actual saved JSON ledgers.
   original_read=io.read
   def metadata_only(path,*args,**kwargs):
    self.assertNotEqual(Path(path).suffix,'.dng');return original_read(path,*args,**kwargs)
   with patch.object(io,'read',side_effect=metadata_only):
    value=saved.functional_saved(plan,result,work)
   self.assertEqual(value['cases'],8);self.assertFalse(value['current_generated_payload_rehashed'])
   self.assertFalse(value['resource_release_authority']);self.assertEqual(result,original)
   self.assertEqual(saved.functional_saved(plan,result,work),value)
 def test_actual_schema_failure_is_only_accepted_reaudit_scope(self):
  with tempfile.TemporaryDirectory() as raw:
   work=Path(raw);p,r=files(work)
   for mutate in (lambda r:r.update(complete=True),lambda r:r.update(failure='different'),lambda r:r['cases'].pop()):
    bad=deepcopy(r);mutate(bad)
    with self.assertRaises(ValueError):saved.functional_saved(p,bad,work)
 def test_recorded_hash_and_actual_epoch_refusals(self):
  with tempfile.TemporaryDirectory() as raw:
   work=Path(raw);p,r=files(work);bad=deepcopy(r)
   bad['cases'][0]['before']['left']['sha256']='0'*64
   bad['cases'][0]['after']=deepcopy(bad['cases'][0]['before'])
   with self.assertRaises(ValueError):saved.functional_saved(p,bad,work)
   os.utime(work/'0/left/components.dng',ns=(1,1))
   with self.assertRaises(ValueError):saved.functional_saved(p,r,work)
 def test_raw_proxy_and_ledger_bindings_still_required(self):
  with tempfile.TemporaryDirectory() as raw:
   work=Path(raw);p,r=files(work)
   proxy=work/'0/proxy.json';proxy.write_text('{}\n')
   with self.assertRaises(ValueError):saved.functional_saved(p,r,work)
 def test_cannot_hide_failed_command_in_duplicate_case_result(self):
  with tempfile.TemporaryDirectory() as raw:
   work=Path(raw);p,r=files(work);bad=deepcopy(r);bad['cases'][2]['outcome']['returncode']=1
   with self.assertRaises(ValueError):saved.functional_saved(p,bad,work)
if __name__=='__main__':unittest.main()
