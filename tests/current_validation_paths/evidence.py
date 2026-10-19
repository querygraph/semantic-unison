"""Pure normal-call transport/fake-helper audit, never a publication verdict.

Explicit expected helper observations are bound by the executor to original
control-file/candidate evidence. Missing diagnostics cannot prove an arbitrary
failed no-helper prefix. Interruption/cancellation actors need separate audits.
"""
import hashlib,json,re
from camera_sdk_receiving.sdk_audit import FIELDS,records
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import child,unique
from sdk_merge_receiving.plan import require


def terminal(out,command,code):
    require(type(code) is int and code in (0,2),'normal call expects exact success0 or failed2')
    if code==0:return child(out,command)
    from sdk_negative_receiving.transport_audit import rejected_child
    return rejected_child(out,command)


def trace(command):
    require(type(command) is list and all(type(v) is str for v in command) and '-nodebug' not in command,
            'exact fully traced command required')
    values=[command[i+1] for i,v in enumerate(command[:-1]) if v=='-debug']
    require('validation-process' in values and 'validation-group' in values,'both owner helper traces required')


def fake_receipt(raw,expected):
    require(type(raw) is bytes and 0<len(raw)<=4096,'bounded full fake-validator receipt required')
    try:lines=raw.decode('ascii').split('\n')
    except UnicodeDecodeError as error:raise ValueError('ASCII fake receipt required') from error
    require(len(lines)==11 and lines[0]=='UNISON-DNG-VALIDATION 1' and lines[-2:]==['END',''],
            'exact fake receipt framing required')
    values={}
    for key,line in zip(FIELDS,lines[1:9]):
        prefix=key+' ';require(line.startswith(prefix),'ordered fake receipt fields required');values[key]=line[len(prefix):]
    mode=expected['mode'];actual_hash='0'*64 if mode=='wrong-receipt' else expected['candidate_sha256']
    require(mode!='wrong-receipt' or actual_hash!=expected['candidate_sha256'],'wrong-receipt fixture must actually differ')
    require(values=={'candidate-sha256':actual_hash,'candidate-size':str(expected['candidate_bytes']),
        'driver-build':'validation-path-'+expected['endpoint']+'-v1','structure':'valid','decode':'success',
        'raw-digest':'missing','errors':'1' if mode=='error' else '0','warnings':'0'},'fake fixture receipt differs from declared control mode')
    return dict(values,synthetic_fixture_only=True,raw_digest_verified=False,
                publication_proved=False,resource_release_authorized=False)


def helpers(log,expected,transport_pids):
    require(type(expected) is list and len(expected)<=6,'bounded explicit per-call helper expectations required')
    processes=records.parse(log);groups=records.parse_groups(log)
    require(len(processes)==len(groups)==len(expected),'all helper records and expectations required')
    key=lambda value:(value.endpoint,value.pid,value.candidate_sha256)
    require(len({key(p) for p in processes})==len(processes) and len({key(g) for g in groups})==len(groups),
            'duplicate helper identity observations')
    pending={key(p):p for p in processes};group_map={key(g):g for g in groups};verdicts=[]
    for entry in expected:
        require(type(entry) is dict and set(entry)=={'endpoint','pid','candidate_sha256','candidate_bytes','mode','outcome'}
            and entry['endpoint'] in ('client','server') and type(entry['pid']) is int and 0<entry['pid']<2**31
            and entry['pid'] not in transport_pids and type(entry['candidate_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}',entry['candidate_sha256']) is not None
            and type(entry['candidate_bytes']) is int and 0<entry['candidate_bytes']<=16*1048576
            and entry['mode'] in ('pass','error','wrong-receipt','mutate','delay','hang'),
            'exact original helper/candidate/control binding required')
        identity=(entry['endpoint'],entry['pid'],entry['candidate_sha256'])
        require(identity in pending and identity in group_map,'missing or mismatched helper identity')
        process=pending.pop(identity);group=group_map.pop(identity)
        require(process.candidate_bytes==entry['candidate_bytes'] and group.observation=='observed'
            and group.other_members==0 and process.complete_capture,'helper capture or retained group unresolved')
        require(process.outcome==entry['outcome'],'actual helper disposition differs from source-declared phase')
        if entry['mode']=='hang':
            require(entry['outcome'] in ('timed-out','cancelled') and process.status in (('signal',15),('signal',9))
                and process.stdout==b'','only declared owned timeout/cancellation helper signal allowed')
            report=None
        else:
            require(entry['outcome']=='completed' and process.status==('exit',0),'normal fake helper must return full receipt normally')
            report=fake_receipt(process.stdout,entry)
        verdicts.append(dict(expected=entry,report=report,actual_status=list(process.status),group_others_before_reap=0))
    require(not pending and not group_map,'unaccounted helper observations')
    return verdicts


def audit(pair,*,client_command,proxy_command,server_command,raw_proxy_bytes,expected_client_exit,expected_helpers):
    trace(client_command);trace(server_command)
    require(type(pair) is dict and set(pair)=={'client','proxy','raw_proxy','external_sdk_audit_required','resource_release_authorized'}
        and pair['external_sdk_audit_required'] is True and pair['resource_release_authorized'] is False,
        'exact non-releasing retained pair required')
    client_pid=terminal(pair['client'],client_command,expected_client_exit);proxy_pid=child(pair['proxy'],proxy_command)
    require(client_pid!=proxy_pid and type(raw_proxy_bytes) is bytes and 0<len(raw_proxy_bytes)<=65536,'distinct owners/bounded raw proxy required')
    frame=json.loads(raw_proxy_bytes,object_pairs_hook=unique,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite raw proxy')))
    require(type(frame) is dict and exact(frame,pair['raw_proxy']) and set(frame)=={'schema','server_command',
        'server_pid','server_returncode','server_reaped','server_group','input_eof_forwarded','output_eof_forwarded',
        'forwarded_protocol_bytes','parent_group_audit_required','sdk_helper_audit_required','resource_release_authorized'},
        'exact independently read native proxy frame required')
    require(frame['schema']=='unison-retained-merge-proxy/1' and exact(frame['server_command'],server_command)
        and type(frame['server_pid']) is int and 0<frame['server_pid']<2**31 and frame['server_pid'] not in (client_pid,proxy_pid)
        and type(frame['server_returncode']) is int and frame['server_returncode']==0 and frame['server_reaped'] is True
        and type(frame['server_group']) is int and frame['server_group']==proxy_pid
        and frame['input_eof_forwarded'] is True and frame['output_eof_forwarded'] is True
        and frame['parent_group_audit_required'] is True and frame['sdk_helper_audit_required'] is True
        and frame['resource_release_authorized'] is False,'normal native server and both pumps must settle')
    counts=frame['forwarded_protocol_bytes']
    require(type(counts) is dict and set(counts)=={'client_to_server_bytes','server_to_client_bytes'}
        and all(type(v) is int and 0<v<2**63 for v in counts.values()),'both typed protocol directions required')
    log='\n'.join(pair[p][s] for p in ('client','proxy') for s in ('stdout','stderr'))
    require(expected_client_exit==0 or bool(expected_helpers),'failed no-helper prefix needs separate source/creation audit')
    verdicts=helpers(log,expected_helpers,{client_pid,proxy_pid,frame['server_pid']})
    return dict(command=client_command,client_returncode=expected_client_exit,log=log,
        external_children_settled=True,helper_observations=verdicts,raw_proxy_sha256=hashlib.sha256(raw_proxy_bytes).hexdigest(),
        publication_fence_required=True,worker_settlement_required=True,parent_terminal_proved=False,
        real_SDK_calls=0,resource_release_authorized=False)
