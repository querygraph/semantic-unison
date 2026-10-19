"""Source-bound per-process clock/wait4 observations, never hard tree caps."""
import math
from measure import receipt


def validate(value,pid):
    fields={'schema','pid','started_ns','terminal_observed_ns','reaped_ns','wall_to_terminal_ns',
            'wait4','scope','resource_release_authorized'}
    if (type(value) is not dict or set(value)!=fields or value['schema']!='unison-batch-process-observation/1'
            or type(value['pid']) is not int or value['pid']!=pid
            or value['resource_release_authorized'] is not False):
        raise ValueError('exact bound process observation required')
    times=[value[k] for k in ('started_ns','terminal_observed_ns','reaped_ns')]
    if (any(type(n) is not int or n<=0 for n in times) or times!=sorted(times)
            or type(value['wall_to_terminal_ns']) is not int or value['wall_to_terminal_ns']!=times[1]-times[0]):
        raise ValueError('ordered actual process clock readings required')
    fields={'wait4_user_seconds','wait4_system_seconds','wait4_maxrss_native_units',
            'minor_faults','major_faults','block_input_operations','block_output_operations'}
    usage=value['wait4']
    if type(usage) is not dict or set(usage)!=fields:raise ValueError('exact raw wait4 fields required')
    for name,n in usage.items():
        if name in ('wait4_user_seconds','wait4_system_seconds'):
            if type(n) not in (int,float) or not math.isfinite(n) or n<0:raise ValueError('finite nonnegative CPU observation required')
        elif type(n) is not int or n<0:raise ValueError('nonnegative raw wait4 counter required')
    if value['scope']!=SCOPE:raise ValueError('observation scope differs')
    return value


SCOPE='per-process wait4; CPU may include reaped descendants; maxrss Darwin bytes/Linux KiB; not simultaneous tree peak/hardcap; do not sum overlapping client/proxy observations'


def capture(owner):
    if owner.reaped is not True:raise ValueError('actual reaped process owner required')
    value=dict(schema='unison-batch-process-observation/1',pid=owner.pid,
        started_ns=owner.started_ns,terminal_observed_ns=owner.terminal_observed_ns,
        reaped_ns=owner.reaped_ns,wall_to_terminal_ns=owner.terminal_observed_ns-owner.started_ns,
        wait4=receipt(owner.last_wait4_usage),scope=SCOPE,resource_release_authorized=False)
    return validate(value,owner.pid)


def read(store,pin,pid):
    if type(pin) is not dict or set(pin)!={'name','sha256','bytes'} or type(pin['bytes']) is not int or not 0<pin['bytes']<=16384:
        raise ValueError('bounded process observation pin required')
    raw=store.read(pin['name'],expected_sha256=pin['sha256'])
    if len(raw)!=pin['bytes']:raise ValueError('process observation byte pin differs')
    return validate(store.read_json(pin['name'],expected_sha256=pin['sha256']),pid)


def pair(store,pin,joined):
    if type(pin) is not dict or set(pin)!={'name','sha256','bytes'} or type(pin['bytes']) is not int or not 0<pin['bytes']<=16384:
        raise ValueError('bounded pair observation pin required')
    raw=store.read(pin['name'],expected_sha256=pin['sha256'])
    if len(raw)!=pin['bytes']:raise ValueError('pair observation byte pin differs')
    value=store.read_json(pin['name'],expected_sha256=pin['sha256'])
    if (type(value) is not dict or set(value)!={'schema','started_ns','evidence_ready_ns','elapsed_ns',
            'client','proxy','scope','resource_release_authorized'}
            or value['schema']!='unison-batch-pair-observation/1'
            or any(type(value[k]) is not int or value[k]<=0 for k in ('started_ns','evidence_ready_ns','elapsed_ns'))
            or value['evidence_ready_ns']-value['started_ns']!=value['elapsed_ns']
            or value['resource_release_authorized'] is not False
            or value['scope']!='pair orchestration through captured evidence persistence; not bare native runtime'):
        raise ValueError('exact pair orchestration clock scope required')
    return dict(elapsed_ns=value['elapsed_ns'],client=read(store,value['client'],joined['client_pid']),
                proxy=read(store,value['proxy'],joined['proxy_pid']),scope=value['scope'])
