"""Receipt-only audit successor for the consumed eight-case RPC schema failure.

Never changes frozen runtime code or original results, opens generated payloads,
starts a process, signals, waits or authorizes resource release. Recompute known
fixture bytes in memory and bind their in-run before/after hashes and current
metadata fences. This is not a fresh independent payload SHA readback.
"""
import hashlib
import stat
from component_remote.audit import audit_prefix
from component_remote.case import fixture
from component_remote.contract import CASES
from component_remote.io import identity, load
from shared_cpu_pool import require

CLIENT_KEYS={'pid','returncode','reaped','hard_kill_required',
 'other_group_members_absent_before_reap','group_cleanup_before_leader_reap'}
SUPERVISOR_KEYS={'pid','returncode','reaped','other_group_members_absent_before_reap',
 'members_before_reap','timed_out','scope','group_cleanup_before_leader_reap'}

def successful_call(run):
    """Validate the actual pinned producer schemas; do not invent cancel_reason."""
    require(run['returncode']==0 and type(run['returncode']) is int and
      run['timed_out'] is False and run['capture_truncated'] is False and
      run['supervisor_capture_truncated'] is False,'non-successful RPC call')
    client=run['client_cleanup'];supervisor=run['supervisor_cleanup']
    require(set(client)==CLIENT_KEYS and set(supervisor)==SUPERVISOR_KEYS,
            'actual client/supervisor producer schema required')
    for value in (client,supervisor):
        require(type(value['pid']) is int and value['pid']>0 and
          type(value['returncode']) is int and value['returncode']==0 and
          value['reaped'] is True and value['group_cleanup_before_leader_reap'] is True and
          value['other_group_members_absent_before_reap'] is True,'normal direct wait/group proof required')
    require(client['hard_kill_required'] is False and supervisor['timed_out'] is False and
      supervisor['scope']=='owned group only; separate sessions require independently audited proofs',
      'normal producer settlement required')
    members=supervisor['members_before_reap']
    require(type(members) is list and all(set(row)=={'pid','state'} and
      row['pid']==supervisor['pid'] and type(row['state']) is str and row['state'].startswith('Z')
      for row in members),'pre-reap supervisor census differs')
    proxy=run['proxy'];native=proxy['server_cleanup']
    require(native is not None and proxy['server_returncode']==0 and proxy['fault'] is None and
      proxy['pump_errors']==[] and proxy['input_pump_joined'] is True and
      native['returncode']==0 and native['reaped'] is True and
      native['cancel_reason'] is None and native['hard_kill_required'] is False,
      'native server wait/cancellation/pump proof missing')

def functional_saved(plan,result,workspace):
    require(result['schema']=='component-remote-result/1' and result['complete'] is False and
      result['failure']=="KeyError('cancel_reason')" and len(result['cases'])==8,
      'only the exact consumed schema-failed result may be re-audited')
    rows=audit_prefix(plan,workspace)
    require(len(rows)==8 and all(not row['no_dispatch'] and not row['server_not_created']
      for row in rows),'all eight actual raw call settlements required')
    for index,case in enumerate(result['cases']):
        directory=workspace/str(index);run=load(directory/'OUTCOME.json');mode=CASES[index][2]
        require(case['index']==index and case['mode']==mode and case['outcome']==run and
          case['before']==case['after'],'actual case/result/raw binding differs')
        successful_call(run)
        for side in ('left','right'):
            parent=directory/side;path=parent/'components.dng';observed=identity(path)
            expected=fixture(side=='right',side=='right' and mode=='unsupported')
            digest=hashlib.sha256(expected).hexdigest()
            require(parent.is_dir() and not parent.is_symlink() and
              sorted(p.name for p in parent.iterdir())==['components.dng'] and
              observed==case['before'][side]['identity'] and observed['st_size']==8192 and
              stat.S_IMODE(observed['st_mode'])==0o600 and observed['st_nlink']==1 and
              case['before'][side]['sha256']==digest,'recorded fixture hash/current metadata differs')
        text=run['stdout']
        require(text.count('PROBE_FUNCTIONAL '+mode+'\n')==1 and
          text.count('PROBE_LOCAL_RESOURCES_CLOSED (external client/server wait proofs still required)')==1,
          'actual functional markers missing')
        if mode=='supported':
            for side,key in [('left','LOCAL_SHA256'),('right','REMOTE_SHA256')]:
                require(key+' '+case['before'][side]['sha256']+'\n' in text,'reported actual file hash differs')
            require('Encoded pixels: equal.' in text and 'Opaque bytes: different.' in text,
                    'actual role projection report differs')
        if mode=='unsupported':require('REMOTE_UNSUPPORTED not TIFF\n' in text,'exact parser refusal missing')
    return dict(state='SAVED_EIGHT_CASE_FUNCTIONAL_RECEIPTS_VERIFIED_ORIGINAL_EXIT1_RETAINED',
      cases=8,new_supported_pairs=4,no_capability=2,unsupported=1,disabled=1,
      strict_raw_prefix=rows,source_bound_in_run_before_after_hashes_verified=True,
      expected_fixture_bytes_recomputed_in_memory=True,current_metadata_fences_verified=True,
      current_generated_payload_rehashed=False,original_complete=False,
      original_failure=result['failure'],actual_runtime_replayed=False,
      resource_release_authority=False,rendering_or_persistence_authority=False)
