"""Pure complete-run replay for the retained parent, with external IO adapters.

Reparse every pinned raw pair and reconstruct the exact intent/acceptance order.
Source-bound phase output records, fresh final payload/epoch and inherited-FD/worker proofs are mandatory caller duties;
this parser deliberately cannot release resources or claim those observations.
"""
from copy import deepcopy
import hashlib,json
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.plan import require,digest
from sdk_negative_receiving.plan import schedule
from sdk_negative_receiving.pair import audit as audit_pair


def audit(packet,saved,*,read_pinned,proxy_command,verify_outputs):
    require(type(saved) is dict and set(saved)=={'result','pair_pins'},'complete exact saved worker bundle required')
    result=saved['result']
    require(type(result) is dict and set(result)=={'complete','results','events','parent_audit_required','resource_release_authorized'}
        and result['complete'] is True and result['parent_audit_required'] is True
        and result['resource_release_authorized'] is False,'complete non-releasing worker result required')
    rows=schedule(packet['binaries'],packet['tool'],packet['workspace'])['rows']
    require(type(result['results']) is list and len(result['results'])==12
        and type(result['events']) is list and len(result['events'])==24
        and type(saved['pair_pins']) is dict and len(saved['pair_pins'])==12,'complete twelve-pair matrix required')
    events=[];keys=[];helpers=0
    for index,row in enumerate(rows):
        key=row['codec']+'-'+row['policy']+'-'+row['stage'];keys.append(key)
        entry=result['results'][index];active=dict(index=index,codec=row['codec'],policy=row['policy'],stage=row['stage'])
        require(type(entry) is dict and set(entry)=={*active,'candidate','transport','publication'}
            and exact({k:entry[k] for k in active},active),'exact ordered accepted row required')
        candidate=entry['candidate'];require(type(candidate) is dict and set(candidate)=={'sha256','bytes'}
            and type(candidate['bytes']) is int and 0<candidate['bytes']<=128*1048576,'bounded exact candidate required')
        digest(candidate['sha256'])
        pin=saved['pair_pins'][key]
        require(type(pin) is dict and set(pin)=={'name','sha256','bytes'} and pin['name']==key+'-PAIR.json'
            and type(pin['bytes']) is int and 0<pin['bytes']<=2*1048576,'exact bounded pair pin required')
        digest(pin['sha256']);raw=read_pinned(pin)
        require(type(raw) is bytes and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],
                'independently read pair pin differs')
        from sdk_merge_receiving.metadata import document
        record=document(raw)
        require(type(record) is dict and set(record)=={'identity','pair','raw_proxy_hex'}
            and exact(record['identity'],row['identity']) and type(record['raw_proxy_hex']) is str
            and 0<len(record['raw_proxy_hex'])<=131072,'exact bounded pair identity/frame required')
        frame=bytes.fromhex(record['raw_proxy_hex'])
        require(frame.hex()==record['raw_proxy_hex'],'canonical raw proxy hex required')
        transport=audit_pair(row,record['pair'],frame,candidate,proxy_command=proxy_command(row))
        require(exact(transport,entry['transport']),'worker transport verdict differs from raw independent replay')
        publication=verify_outputs(deepcopy(row),deepcopy(candidate))
        require(type(publication) is dict and publication.get('resource_release_authorized') is False
            and exact(publication,entry['publication']),'independent destination verdict differs')
        command_sha=hashlib.sha256(json.dumps(row['command'],ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
        events.extend([dict(event='INTENT',**active,command_sha256=command_sha,candidate=deepcopy(candidate)),
                       dict(event='ACCEPTED',**active,expected_client_exit=row['expected_client_exit'])])
        helpers+=row['expected_sdk_helpers']
    require(set(keys)==set(saved['pair_pins']) and exact(events,result['events']) and helpers==6,
            'durable call order/count or pair inventory differs')
    return dict(cli_calls=12,SDK_helpers=6,raw_pairs_reparsed=12,events_reconstructed=24,
        output_evidence_adapter_consumed=True,worker_settlement_required=True,
        inherited_resource_binding_required=True,parent_terminal_proved=False,resource_release_authorized=False)
