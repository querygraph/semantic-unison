"""Pure bounded measured-sample schedule; raw samples are never replaced."""
import itertools,statistics


def schedule(*,workers=(1,),warmups=1,repetitions=5):
    if (type(workers) is not tuple or not workers or len(set(workers))!=len(workers)
            or any(type(n) is not int or n not in (1,2,3) for n in workers)
            or type(warmups) is not int or warmups!=1
            or type(repetitions) is not int or repetitions!=5):
        raise ValueError('versionedshared8 one warmup/five measured schedule required')
    configs=list(itertools.product(('stock','ox'),('ordinary','receiver-clone','semantic'),workers))
    rows=[]
    for phase,count in (('warmup',warmups),('measured',repetitions)):
        for repetition in range(1,count+1):
            order=configs if repetition%2 else list(reversed(configs))
            for label,mode,worker in order:
                rows.append(dict(index=len(rows),phase=phase,repetition=repetition,label=label,mode=mode,workers=worker))
    return rows


def summarize(rows,*,workers=(1,)):
    expected=schedule(workers=workers)
    if type(rows) is not list or len(rows)!=len(expected):raise ValueError('complete unshrunk series required')
    groups={}
    for identity,row in zip(expected,rows):
        if row.get('identity')!=identity or row.get('complete') is not True:
            raise ValueError('ordered successful sample identity required')
        metric=row['update']
        for name in ('pair_elapsed_ns','client_elapsed_ns'):
            if type(metric[name]) is not int or metric[name]<=0:raise ValueError('actual positive clock observation required')
        if identity['phase']=='measured':
            groups.setdefault((identity['label'],identity['mode'],identity['workers']),[]).append(metric)
    result=[]
    for key,metrics in sorted(groups.items()):
        if len(metrics)!=5:raise ValueError('exact five measured samples per configuration required')
        value=dict(label=key[0],mode=key[1],workers=key[2],measured_samples=5)
        for name in ('client_elapsed_ns','pair_elapsed_ns'):
            raw=[r[name]/1e9 for r in metrics]
            value[name.replace('_ns','_seconds')]=dict(median=statistics.median(raw),minimum=min(raw),maximum=max(raw),raw=raw,
                tail_scope='five observations only; maximum descriptive, not population tail guarantee')
        for role in ('client','proxy'):
            if all(role+'_wait4' in r for r in metrics):
                cpu=[r[role+'_wait4']['wait4_user_seconds']+r[role+'_wait4']['wait4_system_seconds'] for r in metrics]
                rss=[r[role+'_wait4']['wait4_maxrss_native_units'] for r in metrics]
                value[role+'_cpu_seconds']=dict(median=statistics.median(cpu),raw=cpu)
                value[role+'_maxrss_native_units']=dict(maximum_observed=max(rss),raw=rss,
                    scope='per-process wait4 maxrss; Darwin bytes/Linux KiB; not simultaneous tree peak')
        if all('protocol_bytes' in r for r in metrics):
            value['protocol_bytes']={direction:[r['protocol_bytes'][direction] for r in metrics]
                for direction in ('client_to_server_bytes','server_to_client_bytes')}
        if all('counters' in r for r in metrics):value['path_counters_raw']=[r['counters'] for r in metrics]
        result.append(value)
    return result
