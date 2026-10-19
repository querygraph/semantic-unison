"""Pure crash-at-durable-copy-stage evidence; no ordinary success substitution."""
import hashlib,json
from pathlib import PurePosixPath
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.evidence import child,unique
from sdk_negative_receiving.transport_audit import rejected_child
from current_validation_paths.cancel_evidence import cancelled_client
from current_validation_paths.evidence import trace,helpers
from current_validation_paths.external_evidence import audit as external_audit


def audit(pair,*,client_command,proxy_command,server_command,raw_proxy_bytes,observer):
    trace(client_command);trace(server_command)
    if (type(pair) is not dict or set(pair)!={'client','proxy','raw_proxy','external_sdk_audit_required','resource_release_authorized'}
        or pair['external_sdk_audit_required'] is not True or pair['resource_release_authorized'] is not False):raise ValueError('exact non-releasing pair required')
    code=pair['client']['returncode']
    if type(code) is not int or code not in (2,3):raise ValueError('exact source-bound connection failure2/3 required')
    cp=rejected_child(pair['client'],client_command) if code==2 else cancelled_client(pair['client'],client_command,3)
    pp=child(pair['proxy'],proxy_command)
    if cp==pp or type(raw_proxy_bytes) is not bytes or not 0<len(raw_proxy_bytes)<=65536:raise ValueError('distinct owners/bounded raw native frame required')
    frame=json.loads(raw_proxy_bytes,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite raw frame')))
    if (not exact(frame,pair['raw_proxy']) or set(frame)!={'schema','server_command','server_pid','server_returncode','server_reaped','server_group','transport','resource_release_authorized'}
        or frame['schema']!='unison-generated-producer-interruption/1' or not exact(frame['server_command'],server_command)
        or type(frame['server_pid']) is not int or not 0<frame['server_pid']<2**31 or frame['server_pid'] in (cp,pp)
        or type(frame['server_returncode']) is not int or frame['server_returncode']!=-9 or frame['server_reaped'] is not True
        or type(frame['server_group']) is not int or frame['server_group']!=pp or frame['resource_release_authorized'] is not False):
        raise ValueError('actual owned receiver crash/reap differs')
    transport=frame['transport']
    if (type(transport) is not dict or set(transport)!={'event','counts','client_eof_observed','server_eof_observed','input_eof_forwarded','discard_permitted_only_after_owned_signal'}
        or transport['client_eof_observed'] is not True or transport['server_eof_observed'] is not True
        or transport['input_eof_forwarded'] is not False or transport['discard_permitted_only_after_owned_signal'] is not True):
        raise ValueError('exact interrupted protocol disposition required')
    counts=transport['counts']
    if (type(counts) is not dict or set(counts)!={'client_to_server_bytes','server_to_client_bytes','discarded_client_bytes'}
        or any(type(n) is not int or not 0<=n<2**63 for n in counts.values())
        or min(counts['client_to_server_bytes'],counts['server_to_client_bytes'])<=0):raise ValueError('actual nonempty protocol counters required')
    event=transport['event']
    if type(event) is not dict or set(event)!={'stage','signal','release'}:raise ValueError('one exact observed stage/signal/release required')
    if not exact(event['signal'],dict(pid=frame['server_pid'],signal=9,owned_unreaped_before_signal=True,group=pp,
        reason='observed generated external-copy stage; owned receiver interruption')):raise ValueError('signal not bound to actual unreaped receiver')
    root=PurePosixPath(observer['root']);stage=event['stage'];record=stage['record'];candidate=PurePosixPath(record['destination'])
    if (type(stage) is not dict or set(stage)!={'record','stage_identity','source_sha256','staged_sha256','staged_bytes',
        'old_destination_absent','validator_calls_before_copy_return','resource_release_authorized'}
        or stage['old_destination_absent'] is not True or type(stage['validator_calls_before_copy_return']) is not int or stage['validator_calls_before_copy_return']!=0
        or stage['resource_release_authorized'] is not False or stage['source_sha256']!=observer['source_sha256']
        or stage['staged_sha256']!=observer['staged_sha256'] or type(stage['staged_bytes']) is not int or stage['staged_bytes']!=observer['staged_bytes']
        or candidate.parent!=root/'right' or not candidate.name.endswith('.unison.tmp') or candidate==root/'right'/observer['name']
        or record['source']!=str(root/'left'/observer['name']) or record['interrupt']!=observer['kind']
        or record['sha256']!=observer['staged_sha256'] or record['size']!=observer['staged_bytes']):raise ValueError('exact original generated staging binding required')
    identity=stage['stage_identity']
    if (type(identity) is not list or len(identity)!=8 or any(type(v) is not int or v<0 for v in identity)
        or identity[:2]!=[record['device'],record['inode']] or identity[3]!=observer['staged_bytes'] or identity[6]!=1):raise ValueError('exact durable staging native identity required')
    release=dict(marker=str(root/'external-copy.release'),copy_fixture_released=True,producer_signalled=False,resource_release_authorized=False)
    if not exact(event['release'],release):raise ValueError('producer must return via exact one-use source marker, not counter-PID signal')
    log='\n'.join(pair[p][stream] for p in ('client','proxy') for stream in ('stdout','stderr'))
    if 'Lost connection with the server' not in log:raise ValueError('actual source-bound interrupted connection diagnostic required')
    identities={cp,pp,frame['server_pid']};helpers(log,[],identities)
    expected=dict(endpoint='client',pid=record['group'],fixture_pid=record['pid'],kind='copy')
    externals=external_audit(log,[expected],identities)
    return dict(command=client_command,client_returncode=code,log=log,external_children_settled=True,
        helper_observations=[],external_observations=externals,produced=record,stage_identity=identity,
        raw_proxy_sha256=hashlib.sha256(raw_proxy_bytes).hexdigest(),
        publication_proved=False,parent_terminal_proved=False,SDK_calls=0,resource_release_authorized=False)
