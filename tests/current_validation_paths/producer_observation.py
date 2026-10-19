"""Observe a generated external-copy stage before owned receiver interruption.

The proxy owns the receiver child. It must signal only that unreaped child,
then publish the one-use fixture release marker. The original copy helper
returns normally for its native supervisor to reap; no PID from a counter is
signalled. This module owns metadata FDs only, not native child settlement.
"""
import hashlib,json
from current_validation_paths.files import Files,epoch


class Observer:
    def __init__(self,config):
        if type(config) is not dict or set(config)!={'root','identity','name','kind','source_bytes','source_sha256','staged_bytes','staged_sha256'}:
            raise ValueError('exact original generated-copy observer configuration required')
        if (config['kind'] not in ('complete','partial') or config['name']!='resumed.DNG'
            or type(config['source_bytes']) is not int or not 1048576<config['source_bytes']<=16*1048576
            or type(config['staged_bytes']) is not int or config['staged_bytes']!=(config['source_bytes'] if config['kind']=='complete' else config['source_bytes']//2)):
            raise ValueError('original complete/partial generated source scope required')
        for key in ('source_sha256','staged_sha256'):
            value=config[key]
            if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('exact expected generated digest required')
        self.config=dict(config);self.observed=None;self.release_attempted=False;self.released=False
        self.files=Files(config['root'],tuple(config['identity']));self.root=self.files.Path(config['root'])
        self.source=self.root/'left'/config['name'];self.target=self.root/'right'/config['name']
        self.copy=self.root/'external-copy.py';self.marker=self.copy.with_suffix('.release')
    def observe(self):
        if self.observed is not None:raise ValueError('one-use stage observation already consumed')
        if self.marker.exists():raise ValueError('unexpected preexisting copy release marker')
        counter=self.copy.with_suffix('.calls.jsonl')
        if not counter.exists():return None
        raw=counter.read_text()
        # A single append write may be observed before its final newline. Do
        # not parse a partial row as a successful event; re-observe boundedly.
        if not raw.endswith('\n'):return None
        values=[json.loads(line) for line in raw.splitlines()]
        if len(values)!=1:raise ValueError('one initial copy producer counter required')
        value=values[0];candidate=self.root.__class__(value['destination'])
        if (value['source']!=str(self.source) or candidate.parent!=self.target.parent or candidate==self.target
            or not candidate.name.endswith('.unison.tmp') or value['interrupt']!=self.config['kind']
            or value['size']!=self.config['staged_bytes'] or value['sha256']!=self.config['staged_sha256']
            or any(type(value[k]) is not int or not 0<value[k]<2**63 for k in ('pid','group','device','inode'))):
            raise ValueError('exact private generated copy record required')
        if self.target.exists():raise ValueError('external producer published before native validation')
        for endpoint in ('client','server'):
            p=self.root/(endpoint+'-validator.calls.jsonl')
            if p.exists() and p.read_bytes():raise ValueError('receiving validator started before external copy completion')
        source=self.source.read_bytes();stage=candidate.read_bytes();st=candidate.lstat()
        if (len(source)!=self.config['source_bytes'] or hashlib.sha256(source).hexdigest()!=self.config['source_sha256']
            or stage!=source[:self.config['staged_bytes']] or (st.st_dev,st.st_ino)!=(value['device'],value['inode'])):
            raise ValueError('durable complete/partial stage differs from original generated source')
        self.observed=dict(record=value,stage_identity=list(epoch(st)),source_sha256=self.config['source_sha256'],
            staged_sha256=self.config['staged_sha256'],staged_bytes=len(stage),old_destination_absent=True,
            validator_calls_before_copy_return=0,resource_release_authorized=False)
        return self.observed
    def release(self,signal):
        if self.release_attempted or self.observed is None:raise ValueError('one release only after observed copy stage')
        self.release_attempted=True
        if (type(signal) is not dict or signal.get('signal')!=9 or signal.get('owned_unreaped_before_signal') is not True
            or type(signal.get('pid')) is not int or signal['pid']<=0 or signal['pid'] in (self.observed['record']['pid'],self.observed['record']['group'])):
            raise ValueError('only exact owned receiver interruption may release copy fixture')
        candidate=self.root.__class__(self.observed['record']['destination'])
        if list(epoch(candidate.lstat()))!=self.observed['stage_identity'] or self.target.exists() or self.marker.exists():
            raise ValueError('observed stage/binding changed before receiver interruption release')
        self.marker.write_bytes(b'owned receiver interrupted; copy fixture may return normally\n')
        self.released=True
        return dict(marker=str(self.marker),copy_fixture_released=True,producer_signalled=False,resource_release_authorized=False)
    def close(self):self.files.close()
