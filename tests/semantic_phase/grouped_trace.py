"""Decode saved legacy grouped Trace callbacks, preserving inherited-prefix evidence."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
import phase_stats as strict

ORDER={'hash':0,'parse':1,'verify':2,'write':3}


def decode(text, *, endpoint, stream):
    if endpoint not in ('client','server') or type(text) is not str or len(text)>strict.MAX_LOG:
        raise ValueError('bounded endpoint-specific stream required')
    prefix='[server: semantic-timings] ' if endpoint=='server' else '[semantic-timings] '
    records=[];context=None;seen=set()
    for index,line in enumerate(text.splitlines()):
        inherited=False
        if strict.PREFIX.match(line):
            value=strict.parse(line)['records'][0]
            if value['endpoint']!=endpoint:raise ValueError('endpoint prefix crossed stream')
            context=None
            if value['kind']=='worker':
                context=dict(job=value['job'],order=ORDER[value['stage']],line=index,raw=line)
        elif line.startswith('Semantic worker job '):
            if context is None:raise ValueError('orphan unprefixed worker phase')
            value=strict.parse(prefix+line)['records'][0]
            if value['kind']!='worker' or value['job']!=context['job'] or ORDER[value['stage']]<=context['order']:
                raise ValueError('group continuation changed job/kind/order')
            context['order']=ORDER[value['stage']];inherited=True
        else:
            context=None;continue
        if len(records)>=strict.MAX_RECORDS:raise ValueError('grouped trace record limit')
        if value['kind'].startswith('worker'):
            key=value['job'],value.get('stage')
            if key in seen:raise ValueError('duplicate grouped worker phase')
            seen.add(key)
        decoded={k:v for k,v in value.items() if k!='raw_line'}
        records.append(dict(stream=stream,line_index=index,raw_line=line,decoded=decoded,
            inherited_prefix=inherited,group_anchor=None if not inherited else
            dict(line_index=context['line'],raw_line=context['raw'],endpoint=endpoint)))
    return records
