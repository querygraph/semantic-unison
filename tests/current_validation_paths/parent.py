"""Independent pure replay of every attempted named receiving call.

IO adapters are pinned parent source: they must freshly read bounded records,
verify actual case identity/script/profile bytes and supply final counter lists.
The caller must separately prove worker/group/FD settlement. No release authority
or actual parent-tool terminal is inferred by this module.
"""
import hashlib,json,math
from pathlib import PurePosixPath as Path
from sdk_merge_receiving.admission import exact,PYTHON
from sdk_merge_receiving.metadata import document
from current_validation_paths import recipes,parent_counters,successors
NAMED_TOTALS=dict(cli_calls=69,fake_validators=54,copy=9,merge=7,producer_interruptions=4,client_cancellations=2)
from current_validation_paths.evidence import audit as audit_normal
from current_validation_paths.cancel_evidence import audit as audit_cancel
from current_validation_paths.producer_evidence import audit as audit_producer
from current_validation_paths.runtime import case_summary


def pinned(root,pin,name,read):
    if (type(pin) is not dict or set(pin)!={'name','sha256','bytes'} or pin['name']!=name
        or type(pin['bytes']) is not int or not 0<pin['bytes']<=2*1048576):raise ValueError('exact bounded named record pin required')
    raw=read(root,name)
    if type(raw) is not bytes or len(raw)!=pin['bytes'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
        raise ValueError('independently read named record pin differs')
    return document(raw)


def replay(packet,result,*,source,worker_pid,resources,owner_deadline,read_case,read_root,case_state):
    if (type(result) is not dict or set(result)!={'complete','cases','failed_case','calls','attempted_CLI_calls','actual_SDK_calls',
        'actual_Photo_calls','parent_terminal_proved','resource_release_authorized','independent_parent_raw_audit_required'}
        or type(result['complete']) is not bool or result['parent_terminal_proved'] is not False
        or result['resource_release_authorized'] is not False or result['independent_parent_raw_audit_required'] is not True
        or type(result['actual_SDK_calls']) is not int or result['actual_SDK_calls']!=0
        or type(result['actual_Photo_calls']) is not int or result['actual_Photo_calls']!=0):raise ValueError('exact non-releasing original worker result required')
    n=result['attempted_CLI_calls'];calls=result['calls'];rows=packet['rows']
    if (type(n) is not int or not 0<=n<=69 or type(calls) is not dict or set(calls)!={str(i) for i in range(1,n+1)}
        or type(result['cases']) is not list or len(result['cases'])>len(rows)
        or type(worker_pid) is not int or not 0<worker_pid<2**31 or type(resources) is not list or len(resources)!=9
        or any(type(r) is not dict or set(r)!={'fd','device','inode'} or any(type(v) is not int or v<=0 for v in r.values()) for r in resources)
        or len({r['fd'] for r in resources})!=9
        or type(owner_deadline) not in (int,float) or not math.isfinite(owner_deadline) or owner_deadline<=0):raise ValueError('exact contiguous call/worker/resource inventory required')
    successor=successors.contract(packet.get('schema'))
    server=successors.server_binary(packet)
    phase_of=(lambda *a:recipes.successor_phase(successor,*a,server_binary=server)) if successor else recipes.phase
    totals=successor.TOTALS if successor else NAMED_TOTALS
    if not 0<=n<=totals['cli_calls']:raise ValueError('attempted calls exceed declared suite inventory')
    scripts=recipes.scripts(recipes.literal_templates(source),packet['repository']);rowmap={row['directory']:row for row in rows}
    loaded=[];by_root={};last_index=-1
    for number in range(1,n+1):
        item=calls[str(number)];root=item['root']
        base={'root','intent_pin','config_pin','pair_pin','audit_pin'}
        if root not in rowmap or not base<=set(item)<=base|{'cancellation_pin'}:raise ValueError('exact declared case call refs required')
        row=rowmap[root]
        if row['index']<last_index or row['index']>last_index+1:raise ValueError('original case call order skipped or replayed')
        last_index=row['index'];sequence=len(by_root.get(root,[]))+1;stem='call-%03d'%number
        intent_record=pinned(root,item['intent_pin'],stem+'-INTENT.json',read_case);intent=intent_record['intent']
        if not exact(intent_record,dict(intent=intent,global_call=number,resource_release_authorized=False)):
            raise ValueError('exact independently read intent number required')
        phase=phase_of(row,sequence,scripts,packet['binary']['path'])
        kind=None if successor else 'producer_interruption' if row['family']=='resumed' and sequence==1 else 'cancellation' if row['family']=='cancelled' and sequence==2 else None
        keys={'case_root','sequence','resource_release_authorized','before_fake_helper_counts','before_external_counts',*phase}
        if kind:keys.add(kind)
        if (type(intent) is not dict or set(intent)!=keys or intent['case_root']!=root or type(intent['sequence']) is not int
            or intent['sequence']!=sequence or intent['resource_release_authorized'] is not False
            or not exact({k:intent[k] for k in phase},phase)
            or type(intent['before_fake_helper_counts']) is not dict or set(intent['before_fake_helper_counts'])!={'client','server'}
            or type(intent['before_external_counts']) is not dict or set(intent['before_external_counts'])!={'copy','merge'}):
            raise ValueError('actual intent differs from exact original case phase recipe')
        if not exact(read_root('case-%02d-seq-%03d-INTENT.json'%(row['index'],sequence)),intent):raise ValueError('root and case intent history differ')
        config_record=pinned(root,item['config_pin'],stem+'-CONFIG.json',read_case);config=config_record['proxy']
        expected_keys={'directory','identity','stage','binary','flags','deadline','worker_pid','resource_fds'}|({'producer_observer'} if kind=='producer_interruption' else set())
        if (type(config_record) is not dict or set(config_record)!={'proxy','script_sha256','resource_release_authorized'}
            or config_record['resource_release_authorized'] is not False or type(config) is not dict or set(config)!=expected_keys
            or config['directory']!=root or config['stage']!=stem or config['binary']!=server
            or not exact(config['flags'],phase['server_command'][3:]) or type(config['worker_pid']) is not int or config['worker_pid']!=worker_pid
            or not exact(config['resource_fds'],resources) or type(config['deadline']) not in (int,float)
            or not math.isfinite(config['deadline']) or not 0<config['deadline']<=owner_deadline
            or type(config['identity']) is not dict or set(config['identity'])!={'device','inode'}
            or any(type(v) is not int or v<=0 for v in config['identity'].values())):raise ValueError('proxy configuration not bound to actual worker/inherited resources')
        if kind=='producer_interruption':
            observer=recipes.producer_observer(row,(config['identity']['device'],config['identity']['inode']))
            if not exact(intent[kind],observer) or not exact(config['producer_observer'],observer):raise ValueError('original generated stage declaration differs')
        if kind=='cancellation' and not exact(intent[kind],recipes.cancellation_fixture()):raise ValueError('original cancellation bytes differ')
        source_text=recipes.proxy_source(packet['repository'],config)
        if config_record['script_sha256']!=hashlib.sha256(source_text.encode()).hexdigest():raise ValueError('proxy script not reproducible from exact source configuration')
        raw_pair=pinned(root,item['pair_pin'],stem+'-PAIR.json',read_case)
        if type(raw_pair) is not dict or set(raw_pair)!={'pair','raw_proxy_hex','resource_release_authorized'} or raw_pair['resource_release_authorized'] is not False:raise ValueError('exact saved native pair required')
        raw=bytes.fromhex(raw_pair['raw_proxy_hex'])
        if raw.hex()!=raw_pair['raw_proxy_hex']:raise ValueError('canonical raw native frame required')
        loaded_item=dict(number=number,row=row,item=item,root=root,sequence=sequence,stem=stem,intent=intent,kind=kind,
            phase=phase,config=config,source=source_text,pair=raw_pair['pair'],raw=raw)
        loaded.append(loaded_item);by_root.setdefault(root,[]).append(loaded_item)
    states={};verdicts={};counts=dict(cli_calls=0,fake_validators=0,copy=0,merge=0,producer_interruptions=0,client_cancellations=0)
    for root,group in by_root.items():
        state=case_state(root,scripts,group[-1]['phase']['server_profile_text'],{item['stem']+'-proxy.py':item['source'] for item in group})
        if type(state) is not dict or set(state)!={'identity','counters','scripts_current','profile_current'} or state['scripts_current'] is not True or state['profile_current'] is not True:raise ValueError('fresh source-script/profile/counter adapter must verify actual bytes')
        states[root]=state
        for offset,entry in enumerate(group):
            number=entry['number'];intent=entry['intent'];kind=entry['kind'];item=entry['item'];pair=entry['pair'];config=entry['config'];stem=entry['stem']
            if not exact(state['identity'],config['identity']):raise ValueError('fresh case directory differs from original proxy identity')
            if offset==0 and any([*intent['before_fake_helper_counts'].values(),*intent['before_external_counts'].values()]):raise ValueError('initial case counter prefix must be empty')
            values=parent_counters.slices(intent,group[offset+1]['intent'] if offset+1<len(group) else None,state['counters'])
            helpers=parent_counters.helpers(root,intent,values);external=parent_counters.externals(values)
            proxy=[PYTHON,'-B',root+'/'+stem+'-proxy.py'];arguments=dict(client_command=intent['command'],proxy_command=proxy,server_command=intent['server_command'],raw_proxy_bytes=entry['raw'])
            if kind=='producer_interruption':
                if helpers:raise ValueError('no validator before interrupted external-copy return')
                verdict=audit_producer(pair,**arguments,observer=intent[kind]);produced=verdict['produced']
                if not exact(values['copy'],[produced]) or values['merge']:raise ValueError('saved observed producer differs from final external counters')
                counts['producer_interruptions']+=1
            elif kind=='cancellation':
                if external or 'cancellation_pin' not in item:raise ValueError('exact original cancellation may not run external producer')
                cancel=pinned(root,item['cancellation_pin'],stem+'-CANCELLATION.json',read_case)
                if (len(values['client'])!=1 or values['server'] or not exact(cancel['fixture_observation']['helper'],values['client'][0])
                    or len(helpers)!=1 or helpers[0]['candidate_sha256']!=intent[kind]['incoming_sha256']
                    or helpers[0]['candidate_bytes']!=intent[kind]['incoming_bytes']
                    or values['client'][0]['destination_sha256']!=intent[kind]['previous_sha256']):
                    raise ValueError('pre-signal cancellation bytes/counter differ from original fixture')
                verdict=audit_cancel(pair,**arguments,cancellation=cancel,expected_helpers=helpers);counts['client_cancellations']+=1
            else:
                if 'cancellation_pin' in item:raise ValueError('ordinary call cannot import cancellation proof')
                if 'designated' in intent:arguments['designated']=intent['designated']
                verdict=audit_normal(pair,**arguments,expected_client_exit=intent['expected_client_exit'],expected_helpers=helpers,expected_external=external)
            inherited=read_case(root,stem+'-INHERITED.json');inherited=document(inherited)
            observed=dict(proxy_pid=pair['proxy']['client_cleanup']['pid'],worker_pid=worker_pid,resource_fds=resources,
                binding=dict(inherited_fds=[r['fd'] for r in resources],canonical_metadata_bound=True,lock_ownership_independently_proved=False,resource_release_authorized=False))
            if not exact(inherited,observed):raise ValueError('actual proxy inherited-FD observation differs')
            saved_verdict=pinned(root,item['audit_pin'],stem+'-AUDIT.json',read_case)
            if not exact(verdict,saved_verdict):raise ValueError('worker verdict differs from independent raw/counter replay')
            accepted=read_root('case-%02d-seq-%03d-ACCEPTED.json'%(entry['row']['index'],entry['sequence']))
            if not exact(accepted,dict(intent=intent,verdict=verdict,resource_release_authorized=False)):raise ValueError('root acceptance history differs from independently replayed raw call')
            verdicts[number]=dict(root=root,verdict=verdict);counts['cli_calls']+=1;counts['fake_validators']+=len(helpers)
            for value in external:counts[value['kind']]+=1
    completed=result['cases']
    for index,summary in enumerate(completed):
        row=rows[index];calls_for_case=[v for v in verdicts.values() if v['root']==row['directory']]
        expected=case_summary(row,calls_for_case,summary['original_result'])
        if not exact(expected,summary) or not exact(read_root('case-%02d-RESULT.json'%index),summary):raise ValueError('original case summary differs from raw independent inventory')
    failure=result['failed_case']
    if result['complete']:
        if failure is not None or len(completed)!=len(rows) or not exact(counts,totals):raise ValueError('full original case inventory not proven')
    else:
        if (type(failure) is not dict or set(failure)!={'index','family','name','error','ordinary_case_failure_only','worker_local_settled_candidate','independent_parent_raw_audit_required','resource_release_authorized'}
            or failure['ordinary_case_failure_only'] is not True or failure['worker_local_settled_candidate'] is not True
            or failure['independent_parent_raw_audit_required'] is not True or failure['resource_release_authorized'] is not False):raise ValueError('exact ordinary settled failed-prefix classification required')
        index=failure['index']
        if index is None:
            if len(completed)!=len(rows) or failure['family']!='whole-inventory' or failure['name']!='whole-inventory':raise ValueError('whole-inventory failure must follow complete original cases')
            name='INVENTORY-FAILED.json';last_allowed=len(rows)-1
        else:
            if type(index) is not int or index!=len(completed) or not 0<=index<len(rows) or failure['family']!=rows[index]['family'] or failure['name']!=rows[index]['name']:raise ValueError('failed prefix cannot skip original cases')
            name='case-%02d-FAILED.json'%index;last_allowed=index
        if any(entry['row']['index']>last_allowed for entry in loaded) or not exact(read_root(name),failure):raise ValueError('calls after failed prefix or mismatched failure record')
    attempted_cases=len(completed)+(1 if not result['complete'] and failure['index'] is not None else 0)
    for row in rows[:attempted_cases]:
        if not exact(read_root('case-%02d-START.json'%row['index']),dict(row=row,resource_release_authorized=False)):
            raise ValueError('durable original case start history differs')
    return dict(complete=result['complete'],original_completed_cases=len(completed),**counts,
        raw_pairs_reparsed=n,external_children_settled=True,worker_settlement_required=True,
        parent_terminal_proved=False,resource_release_authorized=False)
