"""Independent readback of a mixed-peer worker result; no process/FD authority."""
import hashlib
from pathlib import Path
from component_remote.io import load, read, identity
from mixed_peer_compatibility.audit import audit, require
from mixed_peer_compatibility.contract import CASES, STAGES
from mixed_peer_compatibility.worker import fixture


def audit_saved(result, artifacts, workspace):
    workspace=Path(workspace)
    raw=[]
    for index,entry in enumerate(result['invocations']):
        case,phase=divmod(index,3)
        require(case < len(CASES),'too many mixed-peer calls')
        raw.append(load(workspace/str(case)/STAGES[phase]/'proxy.json'))
    closure=audit(result,artifacts,str(workspace),raw)
    require(type(result['complete']) is bool,'typed completion required')
    if not result['complete']:
        return dict(closure,functional='FAILED_OR_INCOMPLETE',bytes_verified=False)
    require(len(result['invocations'])==12 and len(result['cases'])==4,
            'complete result requires twelve calls/four cases')
    for index,case in enumerate(result['cases']):
        require(type(case['index']) is int and case['index']==index
                and [s['stage'] for s in case['stages']]==list(STAGES), 'case order/stages differ')
        for phase,record in enumerate(case['stages']):
            expected=fixture(phase!=0)
            require(record['sha256']==hashlib.sha256(expected).hexdigest(), 'stage expected hash differs')
            for key in ('source_identity','target_identity'):
                stamp=record[key]
                require(stamp['st_size']==8192 and stamp['st_nlink']==1,'fixture identity differs')
            call=result['invocations'][index*3+phase]['outcome']
            require(call['returncode']==0 and call['supervisor_cleanup']['returncode']==0
                    and call['proxy']['server_returncode']==0 and call['proxy']['fault'] is None
                    and call['proxy']['pump_errors']==[] and call['timed_out'] is False,
                    'functional result has failed/timed-out call')
        require(case['stages'][1]['target_identity']==case['stages'][2]['target_identity'],
                'noop did not preserve target identity')
        expected=fixture(True)
        for side,key in (('left','source_identity'),('right','target_identity')):
            directory=workspace/str(index)/side
            require(sorted(p.name for p in directory.iterdir())==['item.dng'], 'unexpected replica content')
            path=directory/'item.dng'
            require(identity(path)==case['stages'][-1][key]
                    and read(path,8192)==expected, 'independent final bytes/identity differ')
    return dict(closure,functional='PASS',bytes_verified=True,
                scope='four generated mixed-peer cases only; no physical IO or semantic equivalence claim')
