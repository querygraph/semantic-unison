"""Independent saved mixed-task audit; owns no descriptors or live processes."""
import json
from decimal import Decimal
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests/supervised_external'),str(ROOT/'tests')]
from external_records import parse as external_records
from shared_io_pool import unique_object

SDK=re.compile(r'SDK_RESULT pid=(none|[1-9][0-9]{0,9}) status=(none|(?:exit|signal|stopped):-?(?:0|[1-9][0-9]{0,9})) outcome=(completed|cancelled|timed-out|output-limit|failed) other-members=(unobserved|unknown|0|[1-9][0-9]{0,9}) truncated=(true|false) stdout-hex=([0-9a-f]{0,32768}) stderr-hex=([0-9a-f]{0,32768})')
CLOSED=re.compile(r'MIXED_CLOSED owner=([1-9][0-9]{0,9}) sdk-ok=(true|false) metadata-ok=(true|false) hashes-ok=true hashes=16 cpu=0 children=0 pending=0 running=0 fd-baseline=true')
FIELDS=('candidate-sha256','candidate-size','driver-build','structure','decode','raw-digest','errors','warnings')


def require(value,message):
    if not value:raise ValueError(message)


def report(raw,command):
    require(len(raw)<=4096,'SDK receipt byte limit')
    lines=raw.decode('ascii').split('\n')
    require(len(lines)==11 and lines[0]=='UNISON-DNG-VALIDATION 1' and lines[-2:]==['END',''],'SDK framing')
    values={}
    for name,line in zip(FIELDS,lines[1:9]):
        require(line.startswith(name+' '),'SDK field order')
        values[name]=line[len(name)+1:]
    require(values['candidate-sha256']==command[6] and values['candidate-size']==command[7]
            and values['driver-build']==command[5],'SDK candidate/build binding')
    require(values['structure'] in ('valid','invalid','unsupported')
            and values['decode'] in ('success','failure','unsupported','not_checked')
            and values['raw-digest'] in ('valid','missing','mismatch','unsupported','not_checked'),'SDK enum')
    for name in ('errors','warnings'):
        require(re.fullmatch(r'(?:0|[1-9][0-9]{0,18})',values[name]) is not None
                and int(values[name])<2**62,'SDK canonical count')
    return values


def audit(outcome,*,command,metadata_version,expected_helpers=None):
    require(type(metadata_version) is str and 0<len(metadata_version)<=128 and '\0' not in metadata_version,'exact metadata version required')
    require(type(command) is list and len(command)==8 and all(type(x) is str and '\0' not in x and len(x)<=4096 for x in command),'exact bounded command required')
    require(all(Path(x).is_absolute() for x in command[:4])
            and re.fullmatch('[0-9a-f]{64}',command[4]) and re.fullmatch('[0-9a-f]{64}',command[6])
            and re.fullmatch(r'(?:0|[1-9][0-9]{0,18})',command[7]) and int(command[7])<2**63,'pinned command metadata differs')
    require(outcome.get('command')==command,'actual invocation differs')
    require(type(outcome.get('returncode')) is int and outcome['returncode']==0
            and outcome.get('timed_out') is False and outcome.get('capture_truncated') is False,'probe not normally closed')
    child=outcome.get('client_cleanup',{})
    require(type(child.get('pid')) is int and 0<child['pid']<2**31
            and type(child.get('returncode')) is int and child['returncode']==0
            and child.get('reaped') is True and child.get('hard_kill_required') is False
            and child.get('other_group_members_absent_before_reap') is True,'probe group/wait unresolved')
    stdout,stderr=outcome.get('stdout'),outcome.get('stderr')
    require(type(stdout) is str and type(stderr) is str and len(stdout)+len(stderr)<=4*1048576,'bounded output required')
    log=stdout+'\n'+stderr
    require(len(log.encode('utf-8'))<=4*1048576,'output byte limit')
    lines=log.splitlines()
    sdk=[line for line in lines if line.startswith('SDK_RESULT ')]
    closed=[line for line in lines if line.startswith('MIXED_CLOSED ')]
    require(len(sdk)==len(closed)==1,'exact SDK and closed records required')
    sm=SDK.fullmatch(sdk[0]);cm=CLOSED.fullmatch(closed[0])
    require(sm is not None and cm is not None,'unknown or malformed task state')
    pid,status,kind,members,truncated,raw,diagnostic=sm.groups()
    synthetic=f'[external-process] External result v0 pid={pid} status={status} outcome={kind} cpu-weight=1 other-members={members} capture-truncated={truncated}'
    sdk_process=external_records(synthetic)[0]
    helpers=external_records(log)
    require(len(helpers)==1,'exact metadata helper record required')
    metadata=helpers[0]
    require(sdk_process.pid is not None and metadata.pid is not None
            and len({child['pid'],sdk_process.pid,metadata.pid})==3,'ambiguous helper/owner PID binding')
    for process in (sdk_process,metadata):
        require(process.endpoint=='client' and process.status is not None and process.status[0] in ('exit','signal')
                and process.group_observation=='observed' and process.other_members==0
                and process.cpu_weight==1,'helper group/terminal/accounting unresolved')
    if expected_helpers is not None:
        require(type(expected_helpers) is dict and set(expected_helpers)=={'sdk','metadata'}
                and all(type(x) is int for x in expected_helpers.values())
                and expected_helpers==dict(sdk=sdk_process.pid,metadata=metadata.pid),'independent helper ledger binding differs')
    raw=bytes.fromhex(raw);diagnostic=bytes.fromhex(diagnostic)
    sdk_report=None;finding=None
    try:sdk_report=report(raw,command)
    except (ValueError,UnicodeError) as error:finding=str(error)
    sdk_ok=(sdk_process.outcome=='completed' and sdk_process.status==('exit',0)
            and not sdk_process.capture_truncated and sdk_report is not None
            and sdk_report['structure']=='valid' and sdk_report['decode']=='success'
            and sdk_report['raw-digest'] in ('valid','missing') and sdk_report['errors']=='0')
    metadata_exit_ok=metadata.outcome=='completed' and metadata.status==('exit',0) and not metadata.capture_truncated
    payloads=[line[len('METADATA_RESULT stdout-hex='):] for line in lines if line.startswith('METADATA_RESULT stdout-hex=')]
    require(len(payloads)==(1 if metadata_exit_ok else 0),'metadata result count contradicts process outcome')
    metadata_fields=False;metadata_finding=None
    if payloads:
        try:
            require(len(payloads[0])<=131072 and re.fullmatch('[0-9a-f]*',payloads[0]) is not None,'metadata byte encoding/limit')
            rows=json.loads(bytes.fromhex(payloads[0]),object_pairs_hook=unique_object,parse_float=Decimal)
            require(type(rows) is list and len(rows)==1 and type(rows[0]) is dict,'one metadata row required')
            require(rows[0].get('SourceFile')==command[3] and type(rows[0].get('ExifToolVersion')) in (str,Decimal,int) and str(rows[0]['ExifToolVersion'])==metadata_version,'metadata source/version differs')
            require(set(rows[0])<= {'SourceFile','Rating','Label','ExifToolVersion'},'unexpected requested metadata fields')
            metadata_fields=True
        except (ValueError,UnicodeError,RecursionError) as error:metadata_finding=str(error)
    owner,claimed_sdk,claimed_meta=cm.groups()
    require(int(owner)==child['pid'] and (claimed_sdk=='true')==sdk_ok
            and (claimed_meta=='true')==metadata_exit_ok,'closed counters contradict task outcomes')
    return dict(functional_status='PASSED' if sdk_ok and metadata_fields else 'FAILED',
                sdk_accepted=sdk_ok,metadata_accepted=metadata_exit_ok,metadata_fields_verified=metadata_fields,
                sdk_helper_pid=sdk_process.pid,metadata_helper_pid=metadata.pid,sdk_report=sdk_report,
                sdk_protocol_finding=finding,metadata_protocol_finding=metadata_finding,
                sdk_stdout_hex=raw.hex(),sdk_stderr_hex=diagnostic.hex(),worker_hashes_reported=16,
                known_helper_settlements=2,independent_helper_ledger_bound=expected_helpers is not None,
                owning_tool_terminal_proved=False,worker_bytes_rehashed=False,
                resource_release_authorized=False,producer_authenticated=False,
                scope='Saved task/counter audit only; actual parent terminal, input/tool pins, FD ownership and byte fences remain caller obligations.')


def audit_prefix(result,*,commands,metadata_version):
    require(type(commands) is list and len(commands)==2,'exact stock/Ox two-probe plan required')
    require(result.get('schema')=='unison-mixed-validation-worker/1' and type(result.get('complete')) is bool,'typed mixed worker result required')
    entries=result.get('invocations');complete=result['complete']
    require(set(result)==({'schema','complete','phase','invocations'} | (set() if complete else {'failure'})),'unexpected result fields')
    require(type(entries) is list and len(entries)<=2,'bounded mixed journal required')
    if complete:require('failure' not in result,'complete result carries failure')
    else:require(type(result.get('failure')) is str and result['failure'],'original failure required')
    require(result.get('phase')==('FINISHED' if complete else 'CALL_MAY_HAVE_STARTED' if entries else 'PREPARING_NO_CALL'),'ambiguous execution phase')
    proofs=[]
    for index,entry in enumerate(entries):
        require(type(entry) is dict and set(entry)=={'index','state','outcome'}
                and type(entry['index']) is int and entry['index']==index and entry['state']=='OUTCOME','unknown/reordered/extra invocation state')
        require(not proofs or proofs[-1]['functional_status']=='PASSED','continued execution after failed mixed task')
        proofs.append(audit(entry['outcome'],command=commands[index],metadata_version=metadata_version))
    if complete:require(len(proofs)==2 and all(p['functional_status']=='PASSED' for p in proofs),'two complete functional probes required')
    return dict(functional_status='PASSED' if complete else 'FAILED',attempted_probes=len(proofs),
                sdk_helpers_settled=len(proofs),metadata_helpers_settled=len(proofs),case_audits=proofs,
                resource_release_authorized=False,aggregate_parent_fd_closure_proved=False)
