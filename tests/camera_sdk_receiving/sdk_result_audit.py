"""Pure combined CLI/SDK result audit; no owner terminal, FD or PID authority."""
from pathlib import Path
import sys

import sdk_audit
import sdk_budget
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
from invocation_journal import audit_attempted


def require(value,message):
    if not value:
        raise ValueError(message)


def audit(result,plan,workspace,*,finishing=False):
    require(result['schema']=='unison-camera-sdk-receiving-worker/1'
            and type(result['complete']) is bool,'typed SDK receiving result required')
    require(result['camera_validity_claimed'] is False
            and result['semantic_eligibility_claimed'] is False,'no corpus/semantic claim allowed')
    entries=result['invocations']
    require(type(entries) is list and len(entries)<=2,'at most two seed calls required')
    complete=result['complete'] or finishing
    if not complete:
        require(type(result.get('failure')) is str and result['failure'],'original failure required')
        if not entries:
            require(result['phase']=='PREPARING_NO_TRANSPORT_DISPATCH',
                    'empty SDK journal after possible dispatch remains unknown')
            return {'functional_status':'FAILED','attempted_cli_invocations':0,
                    'helper_invocations':0,'preparation_before_transport_proved':True}
    proof=audit_attempted(result)
    require(result['phase'] in ('TRANSPORT_MAY_HAVE_STARTED','FINISHED'),'SDK result phase differs')
    helper_proofs=[]
    for index,entry in enumerate(entries):
        identity=entry['identity'];outcome=entry['outcome'];label=('stock','ox')[index]
        directory=Path(workspace)/label;argv=entry['command']
        require(identity=={'label':label,'mode':'semantic','workers':2,
                           'directory':str(directory),'stage':'seed'},'SDK case journal identity differs')
        require(argv[:3]==[plan['binaries'][label]['path'],str(directory/'left'),
                           'ssh://localhost/'+str(directory/'right')], 'SDK roots/binary differ')
        for flag,value in (('-adobevalidate','require'),('-adobevalidator',plan['tool']['path']),
                           ('-adobevalidatorhash',plan['tool']['sha256']),
                           ('-adobevalidatorbuild',plan['tool']['build_id']),
                           ('-adobevalidatorthreads','1'),
                           ('-adobevalidatorworkspace',str(sdk_budget.WORKSPACE_MIB)),
                           ('-semanticpayloadbudget',str(sdk_budget.GATE_MIB)),
                           ('-validationtreememory','0'),('-semanticdescriptorbudget','64')):
            require(argv.count(flag)==1 and argv.index(flag)+1<len(argv)
                    and argv[argv.index(flag)+1]==value,'SDK invocation policy/tool differs')
        log=outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
        if outcome['proxy']['server_command'] is None:
            require(not sdk_audit.records.parse(log) and not sdk_audit.records.parse_groups(log),
                    'no-server branch contradicts helper observations')
            require(not complete,'complete seed cannot have no server')
            continue
        # Mandatory even on failed results: absent/unknown SDK child proof is
        # never downgraded to a known failed-prefix resource release.
        _,settlement=sdk_audit.settled_helper(log,
            candidate_sha256=plan['source']['historical_sha256'],
            candidate_bytes=plan['source']['identity']['st_size'])
        helper_proofs.append(settlement)
        if complete:
            sdk_audit.receiving_verdict(log,candidate_sha256=plan['source']['historical_sha256'],
                candidate_bytes=plan['source']['identity']['st_size'],build_id=plan['tool']['build_id'])
            require(outcome['returncode']==outcome['supervisor_cleanup']['returncode']==
                    outcome['proxy']['server_returncode']==outcome['proxy']['server_cleanup']['returncode']==0
                    and outcome['proxy'].get('fault') is None
                    and outcome['proxy']['pump_errors']==[]
                    and outcome['timed_out'] is False
                    and outcome['capture_truncated'] is False
                    and outcome['supervisor_capture_truncated'] is False,
                    'successful SDK seed requires successful CLI owners/capture/pumps')
    if complete:
        require(len(entries)==len(helper_proofs)==2 and 'failure' not in result,
                'two successful seeded SDK calls required')
        rows=result['cases'];require([r['label'] for r in rows]==['stock','ox'],'SDK row order differs')
        for row,entry in zip(rows,entries):
            require(row['clone']['backend']=='native-fclonefileat-only'
                    and row['clone']['source_identity']==plan['source']['identity'],'SDK clone ancestry differs')
            expected_sdk=sdk_audit.receiving_verdict(
                entry['outcome']['stdout']+entry['outcome']['stderr']+entry['outcome']['supervisor_output'],
                candidate_sha256=plan['source']['historical_sha256'],
                candidate_bytes=plan['source']['identity']['st_size'],build_id=plan['tool']['build_id'])
            case=row['case'];require(case['sdk']==expected_sdk and case['complete'] is True and case['stage']=='VERIFIED_ONE_SEED'
                    and case['candidate_sha256']==plan['source']['historical_sha256']
                    and case['candidate_bytes']==plan['source']['identity']['st_size']
                    and case['outcome']==entry['outcome'] and case['semantic_eligibility_claimed'] is False
                    and case['pixel_equivalence_claimed'] is False,'SDK verified seed evidence differs')
    return dict(proof,helper_invocations=len(helper_proofs),helper_settlements=helper_proofs,
                functional_status='PASSED' if complete else 'FAILED',
                scope='one copied candidate per compiler; no semantic/pixel/corpus claim')
