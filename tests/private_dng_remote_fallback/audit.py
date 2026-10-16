"""Strict tiny remote-fallback audit; separate from performance/shared matrices."""
import re

PAIRS = {('stock','stock'),('stock','ox'),('ox','stock'),('ox','ox')}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def invocation(run):
    require(run['returncode'] == 0 and run['timed_out'] is False
            and run['capture_truncated'] is False and run['supervisor_capture_truncated'] is False,
            'remote fallback invocation failed')
    for key in ('client_cleanup','supervisor_cleanup'):
        owner=run[key]
        require(owner['reaped'] is True and owner['returncode'] == 0
                and owner['cancel_reason'] is None
                and owner['group_cleanup_before_leader_reap'] is True
                and owner['other_group_members_absent_before_reap'] is True,
                'remote direct owner settlement missing')
    proxy=run['proxy'];server=proxy['server_cleanup']
    require(server['reaped'] is True and server['returncode'] == 0
            and server['cancel_reason'] is None and proxy['server_returncode'] == 0
            and type(server['pid']) is int and server['pid'] > 0
            and proxy['server_pid'] == server['pid'] and proxy['fault'] is None
            and proxy['pump_errors'] == [] and proxy['input_pump_joined'] is True,
            'remote server/pump settlement missing')


def audit(result):
    schema = result['schema']
    require(schema in ('unison-private-dng-remote-fallback/1',
                       'unison-private-dng-remote-fallback/2')
            and result['complete'] is True, 'complete fallback result required')
    parameters = {'file_bytes':1048576,'files':1,'client_workers':2,
            'server_workers':2,'owner_credits':2,'total_grant':8,'tag':50740,
            'adobe_validation':'off'}
    distinct = schema == 'unison-private-dng-remote-fallback/2'
    if distinct:
        parameters['payload_layout'] = 'distinct-raw-v1'
    require(result['parameters']==parameters, 'fixed fallback scope differs')
    seen=set();calls=0
    for case in result['cases']:
        pair=tuple(case['compiler_pair'])
        require(pair in PAIRS and pair not in seen,'unexpected/duplicate compiler pair')
        seen.add(pair)
        if distinct:
            require(case['payload_layout']=='distinct-raw-v1', 'distinct fixture binding missing')
        require(all(case[k] is True for k in ('exact_output','basis_unchanged','noop_five_unchanged',
                    'source_complement_unchanged','staging_cleaned')),'fallback preservation failed')
        for stage in ('seed','update','noop'):
            invocation(case['calls'][stage]);calls+=1
        run=case['calls']['update']
        log=run['stdout']+run['stderr']+run['supervisor_output']
        require('Remote semantic fallback: no negotiated profile proves eligibility' in log,
                'semantic decline not observed')
        require('Remote semantic clone wrote' not in log
                and 'Local source clone completed' not in log
                and 'Local semantic workers wrote' not in log,
                'test accidentally selected semantic or local source clone')
        require(log.count('Using immutable receiver clone basis')==1,
                'one receiver basis clone required')
        preserved=re.findall(r'(?<!Local )Receiver clone preserved (\d+) logical bytes',log)
        require(len(preserved)==1 and 0<int(preserved[0])<1048576,
                'receiver clone preserving known unchanged bytes not proved')
        if distinct:
            require(int(preserved[0]) >= 1048576-65536,
                    'distinct unchanged blocks did not establish substantial same-offset reuse')
    require(seen==PAIRS and calls==12,'four compiler pairs/twelve calls required')
    return {'compiler_pairs':4,'cli_calls':12,'receiver_basis_fallback_cases':4,
            'payload_layout':'distinct-raw-v1' if distinct else 'uniform-v1',
            'scope':'finite generated opaque-tag fallback only; not real-camera or SDK/pixel/performance proof'}
