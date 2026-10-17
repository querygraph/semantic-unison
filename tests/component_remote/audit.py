"""Independent saved-prefix audit, never a signal/wait/FD-release authority."""
import json
import stat
from component_remote.contract import CASES, FLAGS, command
from component_remote.io import load, identity, sha
from shared_cpu_pool import require
from invocation_journal import audit_no_server_creation

def settlement(run,argv,server):
    require(run['command']==argv and type(run['returncode']) is int and
      run['capture_truncated'] is False and run['supervisor_capture_truncated'] is False,'call binding/capture missing')
    pids=[]
    for key in ('client_cleanup','supervisor_cleanup'):
        value=run[key];pid=value['pid']
        require(type(pid) is int and pid>0 and pid not in pids and type(value['returncode']) is int and
          value['reaped'] is True and value['group_cleanup_before_leader_reap'] is True and
          value['other_group_members_absent_before_reap'] is True,'client/supervisor settlement missing')
        pids.append(pid)
    require(run['returncode']==run['client_cleanup']['returncode'],'client wait mismatch')
    proxy=run['proxy'];require(proxy['schema']=='unison-loopback-protocol-count/1','proxy schema missing')
    native=proxy['server_cleanup']
    if native is None:
        audit_no_server_creation(run)
        return {'client_pid':pids[0],'supervisor_pid':pids[1],'server_pid':None,'server_not_created':True}
    pid=native['pid'];binding=proxy['server_group_binding'];args=proxy['server_command']
    base=[server,'-server','__new-rpc-mode']
    require(type(pid) is int and pid>0 and pid not in pids and native['reaped'] is True and
      type(native['returncode']) is int and proxy['server_pid']==pid and
      proxy['server_returncode']==native['returncode'] and proxy['input_pump_joined'] is True and
      args==base+FLAGS and proxy['launcher_control_header_bytes_excluded']==4+len(json.dumps(base).encode()),
      'native command/wait/pump mismatch')
    require(binding=={'native_pid':pid,'native_process_group':pids[1],'supervisor_pid':pids[1],
      'supervisor_process_group':pids[1],'observed_before_native_reap':True},'server group binding missing')
    return {'client_pid':pids[0],'supervisor_pid':pids[1],'server_pid':pid,'server_not_created':False}

def audit_prefix(plan,workspace):
    rows=[];stopped=False
    for index,(_,server,mode) in enumerate(CASES):
        directory=workspace/str(index)
        if not directory.exists():stopped=True;continue
        require(not stopped and directory.is_dir() and not directory.is_symlink(),'case ledger not a prefix')
        no_dispatch=directory/'NO-DISPATCH.json';intent=directory/'INTENT.json';outcome=directory/'OUTCOME.json'
        if no_dispatch.exists():
            value=load(no_dispatch)
            require(value['schema']=='component-no-dispatch/1' and value['index']==index and
              value['measure_entered'] is False and not outcome.exists(),'unproved no-dispatch state')
            rows.append({'index':index,'no_dispatch':True});stopped=True;continue
        require(intent.exists() and outcome.exists(),'pending intent/outcome; retain owner')
        entry=load(intent);run=load(outcome);argv=command(plan,index)
        require(entry=={'index':index,'command':argv},'intent binding mismatch')
        require(load(directory/'proxy.json')==run['proxy'],'raw proxy differs from saved call')
        rows.append({'index':index,'no_dispatch':False,**settlement(run,argv,plan['artifacts'][server]['path'])})
    require(not any(p.is_dir() and p.name.isdecimal() and p.name not in {str(i) for i in range(8)}
                    for p in workspace.iterdir()),'unexpected case directory')
    return rows

def functional(plan,result,workspace):
    require(result['complete'] is True and len(result['cases'])==8,'complete eight-case result required')
    rows=audit_prefix(plan,workspace);require(len(rows)==8 and all(not r['no_dispatch'] and
      not r['server_not_created'] for r in rows),'functional case settlement missing')
    for index,case in enumerate(result['cases']):
        directory=workspace/str(index);run=load(directory/'OUTCOME.json');mode=CASES[index][2]
        require(case['index']==index and case['mode']==mode and case['outcome']==run and
          case['before']==case['after'],'fixture/result/raw call mismatch')
        for side in ('left','right'):
            parent=directory/side;path=parent/'components.dng'
            require(parent.is_dir() and not parent.is_symlink() and
              sorted(p.name for p in parent.iterdir())==['components.dng'] and
              identity(path)==case['before'][side]['identity'] and
              identity(path)['st_size']==8192 and stat.S_IMODE(identity(path)['st_mode'])==0o600 and
              identity(path)['st_nlink']==1 and sha(path)==case['before'][side]['sha256'],
              'independent generated-file readback differs')
        require(run['returncode']==0 and run['timed_out'] is False and not run.get('fault') and
          all(run[k]['returncode']==0 and run[k]['cancel_reason'] is None
              for k in ('client_cleanup','supervisor_cleanup')),'functional call failed')
        proxy=run['proxy'];require(proxy['server_returncode']==0 and proxy['fault'] is None and
          proxy['pump_errors']==[] and proxy['server_cleanup']['cancel_reason'] is None,'functional server failed')
        log=run['stdout'];require(log.count('PROBE_FUNCTIONAL '+mode+'\n')==1 and
          log.count('PROBE_LOCAL_RESOURCES_CLOSED (external client/server wait proofs still required)')==1,'probe markers missing')
        if mode=='supported':
            for side,key in [('left','LOCAL_SHA256'),('right','REMOTE_SHA256')]:
                require(key+' '+case['before'][side]['sha256']+'\n' in log,'reported file hash differs')
            require('Encoded pixels: equal.' in log and 'Opaque bytes: different.' in log,'component report differs')
        if mode=='unsupported':require('REMOTE_UNSUPPORTED not TIFF\n' in log,'exact parser refusal missing')
    return {'cases':8,'new_supported_pairs':4,'no_capability':2,'unsupported':1,'disabled':1,
            'all_attempted_groups_settled':True,'rendering_or_persistence_authority':False}
