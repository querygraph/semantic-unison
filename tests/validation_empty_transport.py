"""Real Invoker/proxy/launcher/current Unison on empty roots, inert SDK sentinel.

Adobe-free finite transport control, not a camera or SDK runtime admission. The
SDK executable is non-executable original text; zero selected files/helpers.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'bench/sync'),
               str(ROOT / 'tests/camera_sdk_concurrency')]
from all_scanned_sdk_transport import Invoker
from all_scanned_sdk_plan import BUILD
from all_scanned_sdk_groups import audit as audit_group
from all_scanned_sdk_paths import parse as parse_inputs
from all_scanned_sdk_boundary import read_document
from camera_sdk_concurrency.invocation import artifact_sha, SCRIPT_NAMES
from camera_sdk_concurrency.worker import prepare_scripts
from camera_sdk_concurrency.persistence import save
from invocation_journal import Journal, audit_validation_attempted
from validation_process import records
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def main():
    root = Path(tempfile.mkdtemp(prefix='u-empty-transport-', dir='/private/tmp'))
    sentinel = root / 'never-executable-sdk'; sentinel.write_text('Original inert sentinel; not SDK code.\n'); sentinel.chmod(0o400)
    tool = dict(path=str(sentinel), sha256=artifact_sha(sentinel), build_id=BUILD, threads=1)
    result = dict(complete=False, cases=[], scope='Actual current stock/Ox empty-root Invoker and proxy; SDK sentinel inert. No canonical IO/SDK/camera or full worker qualification.')
    journal = Journal(result, lambda: save(root, result))
    for label in ('stock', 'ox'):
        rpath = Path('/private/tmp/unison-validation-scope-' + label + '-007-20261017/RESULT.json')
        build = read_document(rpath, artifact_sha(rpath), limit=1048576)
        assert build['complete'] and build['build_exit'] == 0
        binary = dict(label=label, path=build['binary'], sha256=build['binary_sha256'])
        directory = root / label; directory.mkdir(mode=0o700)
        for name in ('left', 'right', 'state'): (directory / name).mkdir(mode=0o700)
        pins = prepare_scripts(directory, {n: artifact_sha(ROOT / 'bench/sync' / n) for n in SCRIPT_NAMES})
        for phase in ('baseline', 'validate'):
            call = Invoker(directory, binary=binary, tool=tool, phase=phase, journal=journal,
                           script_pins=pins, deadline=time.monotonic() + 300)
            try: outcome = call()
            except BaseException as error:
                raise UnresolvedOwnership('empty transport call failed; preserve actual prefix for audit') from error
            group = audit_group(outcome)
            raw = read_document(directory / (phase + '-proxy.json'), artifact_sha(directory / (phase + '-proxy.json')))
            assert raw == outcome['proxy'] and outcome['returncode'] == 0
            log = '\n'.join(outcome[k] for k in ('stdout', 'stderr', 'supervisor_output'))
            assert not records.parse(log) and not records.parse_groups(log) and not parse_inputs(log)
            assert 'Nothing to do:' in log
            assert not list((directory / 'left').iterdir()) and not list((directory / 'right').iterdir())
            result['cases'].append(dict(label=label, phase=phase, actual_server_group=group)); save(root, result)
    proof = audit_validation_attempted(result)
    assert proof['attempted_cli_invocations'] == 4
    result.update(complete=True, lifecycle=proof, SDK_invoked=False, retained_media_opened=False)
    save(root, result)
    print(json.dumps(dict(workspace=str(root), actual_client_calls=4, actual_servers=4, SDK_calls=0)), flush=True)


if __name__ == '__main__':
    try: main()
    except UnresolvedOwnership as error: retain_after_record(lambda: print(repr(error), flush=True))
