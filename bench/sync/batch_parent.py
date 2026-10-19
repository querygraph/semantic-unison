"""Independent complete batch audit; no process signaling or resource grant."""
import hashlib,json
from pathlib import Path
from batch_artifacts import read
from batch_pair import audit as audit_pair
from batch_commands import schedule
from batch_inventory import validate
from batch_verify import verify
from batch_transport import restore
from sdk_merge_receiving.parent import pinned
from cached_benchmark.contract import read_bytes


def audit(store,pin,corpus,binaries,*,mode,workers):
    result=pinned(store,pin,'BATCH-RESULT.json')
    expected=schedule(binaries['client'],binaries['server'],store.root,mode=mode,workers=workers)
    if (result['schema']!='unison-generated-batch-runtime/1' or result['contract']!=expected
            or len(result['events'])!=6 or set(result['pairs'])!={'seed','update','noop'}):
        raise ValueError('exact complete batch contract required')
    events=[]
    stages=('seed-intent','seed-inventory','seed-verified','update-inventory','update-verified','noop-verified')
    for i,eventpin in enumerate(result['events']):
        event=pinned(store,eventpin,f'event-{i:02d}.json')
        if event['stage']!=stages[i] or event['resource_release_authorized'] is not False:
            raise ValueError('event order/release flag differs')
        value=event['value']
        if isinstance(value,dict):
            if set(value)!={'count','shards'} or type(value['count']) is not int or not 0<=value['count']<=16384:
                raise ValueError('bounded row shards required')
            rows=[]
            if len(value['shards'])!=(value['count']+1023)//1024:raise ValueError('shard count differs')
            for shard in value['shards']:
                part=json.loads(read(store,shard))
                if type(part) is not list or len(part)!=min(1024,value['count']-len(rows)):
                    raise ValueError('row shard extent differs')
                rows.extend(part)
            value=rows
        events.append(value)
    rows=validate(events[3])
    if len(rows)!=len(corpus.files) or events[0]!=corpus.before_files or events[2]!=corpus.before_files:
        raise ValueError('sample shrank or seed scope differs')
    for file,row in zip(corpus.files,rows):
        classification='new-file' if not file.before_present else 'semantic-update' if file.semantic_update_expected else 'ordinary-fallback'
        if (row['path']!=file.relative_path or row['before_present']!=file.before_present
                or row['expected_class']!=classification or row['target_bytes']!=corpus.file_bytes):
            raise ValueError('per-file planned identity/class differs')
    if len(events[1])!=corpus.before_files:raise ValueError('seed inventory missing')
    seed={r['path']:r for r in events[1]}
    for row in rows:
        if row['before_present']:
            if seed.get(row['path'])!=dict(path=row['path'],sha256=row['before_sha256'],bytes=row['target_bytes']):
                raise ValueError('seed bytes differ from target ancestry')
        elif row['path'] in seed:raise ValueError('fabricated new-file basis')
    reports=[];logs={}
    for row in expected['rows']:
        stage=row['stage'];pair=pinned(store,result['pairs'][stage],stage+'-pair.json')
        intent=store.read_json(stage+'-INTENT.json',expected_sha256=None)
        if intent['row']!=row or pair['schema']!='unison-batch-pair/1':raise ValueError('call intent differs')
        from sdk_merge_receiving.admission import PYTHON
        proxy_command=[PYTHON,'-B',str(Path(store.root)/(stage+'-proxy.py'))]
        joined=audit_pair(store,pair['evidence'],client_command=row['command'],proxy_command=proxy_command,
                          server_command=row['server_command'])
        if pair['audit']!=joined:raise ValueError('saved child audit differs')
        client=restore(store,pair['evidence']['client'],row['command'])
        proxy=restore(store,pair['evidence']['proxy'],proxy_command)
        logs[stage]=client['stdout']+client['stderr']+proxy['stdout']+proxy['stderr']
        reports.append(joined)
    for path,script in result['scripts'].items():
        if hashlib.sha256(read_bytes(path,65536)).hexdigest()!=script['sha256']:raise ValueError('generated script changed')
    left=verify(Path(store.root)/'left',rows,phase='target')
    right=verify(Path(store.root)/'right',rows,phase='target')
    if right!=events[4] or right!=events[5]:raise ValueError('fresh receiver differs from no-op/update observations')
    from batch_counters import audit as audit_counters
    counters=audit_counters(logs['update'],mode,corpus)
    return dict(files=len(rows),calls=3,peer_reports=reports,counters=counters,
                fresh_exact_left_right=True,unchanged_receiver_noop=True,
                external_children_settled=True,source_bound_validation_off=True,
                no_sdk_invoked=True,parent_tool_terminal_proved=False,resource_release_authorized=False)
