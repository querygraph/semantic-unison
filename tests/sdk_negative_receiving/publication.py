"""Pure exact destination fences for designated negative require/warn receiving.

Caller must obtain both observations by full private-file hashing under owned IO
and bind them to the scheduled endpoint. This function never acquires or releases
anything and does not turn caller assertions into filesystem observations.
"""
import re
from sdk_merge_receiving.admission import exact
from sdk_merge_receiving.data import FIELDS
from sdk_merge_receiving.plan import require


def observed(value):
    require(type(value) is dict and set(value)=={'sha256','bytes','identity'},
            'complete destination observation required')
    require(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256'])
        and type(value['bytes']) is int and 0<value['bytes']<=128*1048576,
        'bounded complete destination hash/size required')
    epoch=value['identity']
    require(type(epoch) is dict and set(epoch)==set(FIELDS)
        and all(type(v) is int and v>=0 for v in epoch.values())
        and epoch['st_size']==value['bytes'] and epoch['st_nlink']==1
        and epoch['st_mode']==0o100600,'exact owned private destination epoch required')
    return value


def verify(*,policy,before,after,candidate):
    require(policy in ('require','warn'),'exact negative receiving policy required')
    observed(before);observed(after)
    require(type(candidate) is dict and set(candidate)=={'sha256','bytes'}
        and type(candidate['sha256']) is str and re.fullmatch('[0-9a-f]{64}',candidate['sha256'])
        and type(candidate['bytes']) is int and 0<candidate['bytes']<=128*1048576,
        'exact expected negative candidate hash/size required')
    require(before['sha256']!=candidate['sha256'],'negative update must change candidate bytes')
    if policy=='require':
        require(exact(before,after),'rejected candidate changed destination bytes or native epoch')
    else:
        require(after['sha256']==candidate['sha256'] and after['bytes']==candidate['bytes'],
                'warn did not publish exact expected negative candidate')
    return dict(policy=policy,destination_preserved=policy=='require',
        exact_candidate_published=policy=='warn',fresh_payload_observations_required=True,
        helper_audit_required=True,worker_settlement_required=True,resource_release_authorized=False)
