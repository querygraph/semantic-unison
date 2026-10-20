"""Immutable worker events and independently re-read per-call pair evidence."""
from copy import deepcopy
from sdk_merge_receiving.evidence import bind
from sdk_merge_receiving.plan import CODECS,STAGES,require


class Journal:
    def __init__(self,store,proxy_commands):
        require(type(proxy_commands) is dict and set(proxy_commands)=={
            (codec,stage) for codec in CODECS for stage in STAGES},'exact nine proxy commands required')
        require(all(type(command) is list and command and all(type(x) is str for x in command)
                    for command in proxy_commands.values()),'typed proxy commands required')
        self.store=store;self.commands=deepcopy(proxy_commands)
        self.pair_pins={};self.events=[];self.next_event=0

    def name(self,row):
        require(row['codec'] in CODECS and row['stage'] in STAGES,'exact schedule row identity required')
        return row['codec']+'-'+row['stage']+'-PAIR.json'

    def persist_pair(self,row,pair,raw):
        name=self.name(row)
        require(name not in self.pair_pins,'pair evidence is one-use; no replacement')
        require(type(raw) is bytes and 0<len(raw)<=65536,'bounded raw proxy evidence required')
        record=dict(schema='unison-merge-pair-evidence/1',identity=deepcopy(row['identity']),
            command=deepcopy(row['command']),pair=deepcopy(pair),raw_proxy_hex=raw.hex())
        self.pair_pins[name]=self.store.write(name,record)

    def audit_transport(self,row,outcome):
        name=self.name(row)
        require(name in self.pair_pins,'durable pair evidence missing')
        record=self.store.read_json(name,expected_sha256=self.pair_pins[name]['sha256'])
        require(type(record) is dict and set(record)=={'schema','identity','command','pair','raw_proxy_hex'}
            and record['schema']=='unison-merge-pair-evidence/1'
            and record['identity']==row['identity'] and record['command']==row['command'],
            'saved pair identity/command differs')
        require(type(record['raw_proxy_hex']) is str and len(record['raw_proxy_hex'])<=131072,
                'bounded raw frame hex required')
        raw=bytes.fromhex(record['raw_proxy_hex'])
        require(raw.hex()==record['raw_proxy_hex'],'canonical raw frame hex required')
        expected=bind(row,record['pair'],expected_proxy_command=self.commands[row['codec'],row['stage']],
                      raw_proxy_bytes=raw)
        require(outcome==expected,'worker outcome differs from independently read evidence')

    def persist(self,snapshot):
        require(self.next_event<19,'exact bounded worker event count exceeded')
        name='EVENT-%02d.json'%self.next_event
        self.next_event+=1  # A failed write never permits retry of its namespace.
        record=dict(schema='unison-merge-worker-event/1',snapshot=deepcopy(snapshot),
                    pair_pins=deepcopy(self.pair_pins),resource_release_authorized=False)
        self.events.append(self.store.write(name,record))
