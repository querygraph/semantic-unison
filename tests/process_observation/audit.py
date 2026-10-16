"""Independent returned-record audit; never establishes parent/FD settlement."""
import json

COUNTERS=('resident_bytes','virtual_bytes','threads','running_threads',
          'total_user_native_units','total_system_native_units')


def require(condition,message):
    if not condition:raise ValueError(message)


def unique(pairs):
    value={}
    for key,item in pairs:
        require(key not in value,'duplicate raw observation field')
        value[key]=item
    return value


def settled(outcome):
    child=outcome.get('client_cleanup',{})
    require(type(child.get('pid')) is int and child['pid']>0
            and child.get('reaped') is True and type(child.get('returncode')) is int
            and type(outcome.get('returncode')) is int and child['returncode']==outcome['returncode']
            and child.get('other_group_members_absent_before_reap') is True
            and child.get('group_cleanup_before_leader_reap') is True
            and child.get('hard_kill_required') is False and outcome.get('timed_out') is False,
            'actual child/group settlement missing')
    return child['pid']


def audit(observed,probes,*,probe_path,probe_sha256,recorded_probe_sha256):
    require(type(probe_sha256) is str and len(probe_sha256)==64
            and all(c in '0123456789abcdef' for c in probe_sha256)
            and recorded_probe_sha256==probe_sha256,'probe artifact pin differs')
    pid=settled(observed); report=observed.get('process_observations',{})
    require(type(report.get('pid')) is int and report['pid']==pid
            and report.get('process_settlement_proved') is False
            and report.get('resource_release_authorized') is False,'non-releasing PID-bound report required')
    samples=report.get('samples');limit=report.get('sample_limit')
    require(type(limit) is int and 1<=limit<=1024 and type(samples) is list
            and len(samples)<=limit and type(probes) is list and len(probes)==len(samples),
            'every bounded sample needs exactly one probe outcome')
    pids={pid};last=0;available=0
    for sample,probe in zip(samples,probes):
        before=sample.get('before_monotonic_ns');after=sample.get('after_monotonic_ns')
        require(type(before) is int and type(after) is int and last<=before<=after,
                'ordered monotonic query brackets required')
        last=after
        probe_pid=settled(probe)
        require(probe_pid not in pids,'probe PID duplicated or aliases observed child');pids.add(probe_pid)
        require(probe.get('command')==[probe_path,str(pid)] and probe['returncode']==0
                and probe.get('capture_truncated') is False and probe.get('stderr')==''
                and type(probe.get('stdout')) is str and len(probe['stdout'])<=4096,
                'exact bounded normal probe invocation required')
        raw=json.loads(probe['stdout'],object_pairs_hook=unique)
        require(type(raw) is dict and type(raw.get('pid')) is int and raw['pid']==pid
                and type(raw.get('available')) is bool,'raw observation PID/type differs')
        expected=dict(pid=pid,available=raw['available'])
        if raw['available']:
            require(raw.get('backend')=='Darwin-PROC_PIDTASKINFO','OS backend differs')
            require(all(type(raw.get(k)) is int and raw[k]>=0 for k in COUNTERS),'invalid OS counters')
            require(raw['threads']>=1 and raw['running_threads']<=raw['threads'],'invalid thread counters')
            expected.update({k:raw[k] for k in COUNTERS});available+=1
        observed_value=sample.get('observation')
        require(type(observed_value) is dict and observed_value.keys()==expected.keys()
                and all(type(observed_value[k]) is type(v) and observed_value[k]==v
                        for k,v in expected.items()),
                'sample differs from independently parsed raw frame')
    return dict(samples=len(samples),available_samples=available,missing_samples=len(samples)-available,
                probe_children_settled=len(probes),observed_child_settled=True,
                parent_and_fd_settlement_proved=False,resource_release_authorized=False,
                scope='returned sampled per-process records; no peak, tree total, hard cap or artifact rehash proof')
