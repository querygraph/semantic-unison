"""Caller-admitted aggregate kernel, not a CLI or runtime admission route.

Preparation and source checks must be supplied by the pinned outer executor
under its existing IO/CPU grant. Fresh root verification is mandatory here.
Unknown always escapes as
a retained ownership carrier; no cleanup, retry or broad signal occurs here.
"""
import copy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'bench/sync'),
               str(ROOT / 'tests/camera_sdk_concurrency')]
from invocation_journal import Journal, audit_validation_attempted
from shared_cpu_pool import UnresolvedOwnership
from camera_sdk_concurrency.worker import prepare_scripts
from all_scanned_sdk_transport import Invoker
from all_scanned_sdk_audit import settled_helpers, successful_helpers
from all_scanned_sdk_parent import audit_complete
from all_scanned_sdk_verify import verify_roots
from all_scanned_sdk_paths import audit as audit_paths


def execute(contract, workspace, deadline, *, prepare_sources,
            read_proxy, persist, check_sources):
    root = Path(workspace)
    if (str(root) != contract['workspace'] or not root.is_absolute()
            or root.is_symlink() or not root.is_dir()):
        raise ValueError('exact owned prepared namespace required')
    result = dict(schema='unison-all-scanned-sdk-worker/1', complete=False,
                  phase='PREPARING_NO_CALL', cases=[])
    def save():
        if result.get('invocations') and not result['complete']:
            result['phase'] = 'CALL_MAY_HAVE_STARTED'
        persist(copy.deepcopy(result))
    def unknown(message, error):
        if isinstance(error, UnresolvedOwnership):
            # Preserve nested retained/uncertain FD identities and original cause.
            if not hasattr(error, 'result'):
                error.result = copy.deepcopy(result)
            raise error
        held = UnresolvedOwnership(message)
        held.result = copy.deepcopy(result)
        raise held from error
    journal = Journal(result, save)
    save()
    proxies = []
    try:
        for label in ('stock', 'ox'):
            check_sources()
            directory = root / label
            directory.mkdir(mode=0o700)
            for name in ('left', 'right', 'state'):
                (directory / name).mkdir(mode=0o700)
            pins = prepare_scripts(directory, contract['transport_source_sha256'])
            preparation = prepare_sources(directory, label)
            row = dict(label=label, preparation=preparation, calls=[])
            result['cases'].append(row); save()
            row['initial_root_verification'] = verify_roots(directory, preparation,
                                                           source=contract['source']); save()
            for phase in ('baseline', 'validate'):
                check_sources()
                before = len(result['invocations'])
                call = Invoker(directory, binary=contract['binaries'][label],
                               tool=contract['tool'], phase=phase, journal=journal,
                               script_pins=pins, deadline=deadline)
                error = None
                try: call()
                except UnresolvedOwnership: raise
                except BaseException as caught: error = caught
                if len(result['invocations']) == before:
                    if error is None:
                        unknown('transport returned without an authenticated intent', None)
                    raise error
                entry = result['invocations'][-1]
                if entry['state'] != 'OUTCOME' or journal.pending is not None:
                    unknown('possible call or outcome persistence unresolved', error)
                outcome = entry['outcome']
                try:
                    lifecycle = audit_validation_attempted(result)
                    raw = read_proxy(directory / (phase + '-proxy.json'))
                    if raw != outcome['proxy']:
                        raise ValueError('raw proxy binding differs')
                    server = raw['server_cleanup']
                    if server is not None and (
                            server.get('group_cleanup_before_leader_reap') is not True
                            or server.get('other_group_members_absent_before_reap') is not True):
                        raise ValueError('server retained group settlement missing')
                    log = '\n'.join(outcome[k] for k in ('stdout', 'stderr', 'supervisor_output'))
                    helpers = settled_helpers(log, candidate_sha256=contract['source']['sha256'],
                                              candidate_bytes=contract['source']['bytes'], phase=phase)
                except BaseException as audit_error:
                    unknown('attempted CLI/helper prefix settlement unresolved', audit_error)
                proofs = dict(phase=phase, lifecycle=lifecycle, helpers_settled=helpers)
                row['calls'].append(proofs); proxies.append(raw)
                try: save()
                except BaseException as record_error:
                    unknown('settlement record persistence unresolved', record_error)
                if error is not None: raise error
                if (outcome['returncode'] != 0 or outcome['supervisor_cleanup']['returncode'] != 0
                        or raw['server_returncode'] != 0 or raw.get('fault') is not None
                        or outcome.get('fault') is not None or raw['pump_errors'] != []
                        or outcome.get('timed_out') is not False):
                    raise ValueError('known settled transport failure')
                proofs['helper_verdict'] = successful_helpers(log,
                    candidate_sha256=contract['source']['sha256'],
                    candidate_bytes=contract['source']['bytes'], phase=phase)
                proofs['private_owner_inputs'] = audit_paths(log, directory=directory,
                    helpers=proofs['helper_verdict'], phase=phase,
                    endpoint_pids=dict(client=outcome['client_cleanup']['pid'], server=raw['server_pid']))
                expected_status = 'Nothing to do: replicas have not changed since last sync.'
                allowed = {expected_status}
                if phase == 'baseline':
                    allowed.add('Nothing to do: replicas have been changed only in identical ways since last sync.')
                if sum(line in allowed for line in (outcome['stdout'] + '\n' + outcome['stderr']).splitlines()) != 1:
                    raise ValueError('no-op branch status missing or duplicated')
                proofs['root_verification'] = verify_roots(directory, preparation,
                                                          source=contract['source'])
                check_sources(); save()
        candidate = dict(result, complete=True, phase='FINISHED')
        proof = audit_complete(candidate, contract, raw_proxy_receipts=proxies)
        result.update(complete=True, phase='FINISHED', parent_audit=proof)
        save()
        return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result.update(complete=False, failure=repr(error))
        try: save()
        except BaseException as record_error:
            unknown('failed worker record persistence unresolved', record_error)
        raise
