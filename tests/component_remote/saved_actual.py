"""One output-only metadata audit; never dispatch or rehash generated payloads."""
import argparse
import hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import read,load,save,sha
from component_remote.contract import checked_plan
from component_remote.saved_functional import functional_saved
from shared_cpu_pool import require,UnresolvedOwnership
from shared_process_owner import retain_after_record

def pin(path):
 data=read(path);return dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True)
 p.add_argument('--owner-return-sha256',required=True);a=p.parse_args()
 plan=load(a.plan);work=checked_plan(plan);output=work/'SAVED-AUDIT-V2.json'
 require(not output.exists(),'saved audit output already present; never overwrite')
 require(sha(work/'OWNER-RETURN.json')==a.owner_return_sha256,'trusted closed owner return changed')
 owner=load(work/'OWNER-RETURN.json')
 require(owner['state']=='ACTUAL_RPC_EIGHT_COMMANDS_ZERO_FINAL_AUDITOR_SCHEMA_FAILED_RESOURCES_CLOSED' and
  owner['actual_parent_terminal']['exit_code']==1 and owner['actual_parent_terminal']['no_session'] is True and
  owner['worker_reaped_exit']==1 and owner['cpu_and_io_closed'] is True and owner['unresolved']==[] and
  owner['original_functional_result'] is False,'exact failed/closed original scope required')
 expected={work/name for name in ('OWNER-TERMINAL.json','START.json','ATTEMPT.json','WORKER-PACKET.json',
  'WORKER-RESULT.json','REMOTE-SETTLED.json','AGGREGATE-CLOSED.json','STDOUT.txt','STDERR.txt')}
 expected.update(work/str(i)/name for i in range(8) for name in ('INTENT.json','OUTCOME.json','proxy.json'))
 refs=owner['references'];require(len(refs)==len(expected) and {Path(v['path']) for v in refs}==expected,
   'only exact closed-run metadata references permitted')
 for ref in refs:require(pin(Path(ref['path']))==ref,'original metadata reference changed')
 start=load(work/'START.json');closed=load(work/'AGGREGATE-CLOSED.json');terminal=load(work/'OWNER-TERMINAL.json')
 require(start['owner_pid']==owner['owner_pid']==terminal['owner_pid'] and
   start['worker_pid']==owner['worker_pid']==closed['worker']['pid']==terminal['worker_pid'] and
   terminal['owning_tool_session']==owner['actual_parent_terminal']['session'] and
   terminal['terminal_chunk']==owner['actual_parent_terminal']['terminal_chunk'] and
   terminal['exit_code']==1 and terminal['no_session'] is True and
   closed['worker']['reaped'] is True and closed['worker']['returncode']==1 and
   closed['worker']['other_group_members_absent_before_reap'] is True and
   closed['cpu_closed'] is True and closed['io_closed'] is True,'actual parent/worker closure binding differs')
 result=functional_saved(plan,load(work/'WORKER-RESULT.json'),work)
 require(result['strict_raw_prefix']==closed['calls']==owner['strict_prefix_audit'],
   'corrected saved audit raw settlement differs')
 result.update(owner_return=pin(work/'OWNER-RETURN.json'),original_worker_result=pin(work/'WORKER-RESULT.json'),
   source_plan=pin(a.plan),source_references=[pin(ROOT/'tests/component_remote'/n)
    for n in ('saved_actual.py','saved_functional.py','saved_functional_controls.py')],
   frozen_execution_source_pins_verified=len(plan['execution_source_sha256']),
   payload_read_claim='No generated payload opened: actual pinned in-run before/after hashes, in-memory expected fixtures and current lstat only')
 require(sha(work/'OWNER-RETURN.json')==a.owner_return_sha256,'original owner return changed during audit')
 save(output,result);print(output,flush=True)
if __name__=='__main__':
 try:main()
 except UnresolvedOwnership as error:retain_after_record(lambda:print(repr(error),file=sys.stderr,flush=True))
