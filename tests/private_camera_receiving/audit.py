"""Pure worker-result audit; never a substitute for actual parent/group closure."""
import re
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bench/sync'))
from invocation_journal import audit_attempted


def require(value,message):
    if not value:raise ValueError(message)


def audit(result,plan,workspace):
    require(result['schema']=='unison-camera-receiving-worker/1'
            and type(result['complete']) is bool,'typed camera worker result required')
    require(result['camera_validity_claimed'] is False and result['semantic_eligibility_claimed'] is False,
            'receiving control cannot infer camera or semantic eligibility')
    entries=result['invocations']
    require(type(entries) is list and len(entries)<=6,'bounded six-call journal required')
    if not result['complete']:
        require(type(result.get('failure')) is str and result['failure'],'original failure required')
        if not entries:
            require(result['phase']=='PREPARING_NO_TRANSPORT_DISPATCH',
                    'empty journal after possible dispatch is unknown')
            return {'functional_status':'FAILED','attempted_cli_invocations':0,
                    'preparation_before_transport_proved':True,
                    'scope':'pinned worker preparation phase only; aggregate exit still required'}
    require(result['phase'] in ('TRANSPORT_MAY_HAVE_STARTED','FINISHED'),
            'journal conflicts with worker phase')
    proof=audit_attempted(result)
    # Bind every call to the admitted same-compiler case and its exact binary.
    for entry in entries:
        identity=entry['identity'];label=identity['label'];argv=entry['command']
        require(label in ('stock','ox') and identity['workers']==2 and identity['mode']=='semantic'
                and identity['directory']==str(Path(workspace)/label),
                'case identity/workspace differs')
        require(argv[0]==plan['binaries'][label]['path']
                and argv[1]==str(Path(workspace)/label/'left')
                and argv[2]=='ssh://localhost/'+str(Path(workspace)/label/'right'),
                'camera call binary or roots differ')
    if not result['complete']:
        return dict(proof,functional_status='FAILED')
    require(result['phase']=='FINISHED' and len(entries)==6,'complete six-call result required')
    require('failure' not in result,'complete result preserves a conflicting failure')
    rows=result['cases'];require(type(rows) is list and len(rows)==2,'two compiler cases required')
    require([row['label'] for row in rows]==['stock','ox'],'case order differs')
    for row in rows:
        require(row['clone']['source_identity']==plan['source']['identity']
                and row['clone']['backend']=='native-fclonefileat-only',
                'clone source identity or backend differs')
        value=row['case']
        require(all(value[k] is True for k in ('complete','exact_receiving',
                    'retained_old_receiver_unchanged','noop_epoch_unchanged')),
                'exact case verification missing')
        require(value['photographic_validity_claimed'] is False
                and value['semantic_eligibility_claimed'] is False
                and value['initial_sha256']==plan['source']['historical_sha256']
                and type(value['expected_sha256']) is str
                and re.fullmatch('[0-9a-f]{64}',value['expected_sha256']) is not None,
                'receiving digest or scope differs')
        matching=[e for e in entries if e['identity']['label']==row['label']]
        require([e['identity']['stage'] for e in matching]==['seed','update','noop'],
                'case stage journal differs')
        require(set(value['calls'])=={'seed','update','noop'},'case calls missing')
        for entry in matching:
            outcome=entry['outcome']
            require(value['calls'][entry['identity']['stage']]==outcome
                    and outcome['returncode']==0 and outcome['timed_out'] is False
                    and outcome.get('fault') is None,'case success conflicts with journal')
            require(outcome['supervisor_cleanup']['returncode']==0
                    and outcome['proxy']['server_returncode']==0
                    and outcome['proxy']['server_cleanup']['returncode']==0
                    and outcome['proxy'].get('fault') is None
                    and outcome['proxy']['pump_errors']==[],
                    'functional success requires successful supervisor/server/pumps')
    return dict(proof,functional_status='PASSED',cases=2,
                scope='one camera-derived exact fallback control; not corpus/SDK/photographic validity')
