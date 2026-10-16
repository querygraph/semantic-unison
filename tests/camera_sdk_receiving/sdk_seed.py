"""Source-only one-seed case; no CLI, SDK dispatch or admission on import.

The admitted owner must supply a verified disposable source clone, pin every
binary/tool/script, journal the invocation, and retain native child ownership.
"""
import copy
import os
from pathlib import Path
import sys
import time

import sdk_audit as audit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'private_camera_receiving'))
import case as fallback
from shared_cpu_pool import UnresolvedOwnership


def exercise(directory, *, expected_sha256, expected_bytes, check_borrowed,
             invoke, save, deadline_monotonic, build_id=audit.BUILD):
    directory = Path(directory)
    source, target = directory/'left/image.dng', directory/'right/image.dng'
    fallback.require(directory.is_absolute() and not directory.is_symlink()
                     and not target.exists() and not target.is_symlink(),
                     'owned unused receiving case required')
    before = fallback.identity(source)
    fallback.require(before['st_size'] == expected_bytes
                     and before['st_mode'] == 0o100600 and before['st_nlink'] == 1
                     and before['st_uid'] == os.getuid(),
                     'private independently disposable sender required')
    fallback.require(fallback.sha(source) == expected_sha256,
                     'disposable sender differs from historical copy hash')
    result = {'schema': 'unison-camera-sdk-seed/1', 'complete': False,
              'stage': 'PREPARING_NO_CALL', 'candidate_sha256': expected_sha256,
              'candidate_bytes': expected_bytes, 'semantic_eligibility_claimed': False,
              'pixel_equivalence_claimed': False}
    persist = lambda: save(copy.deepcopy(result))
    persist()
    try:
        check_borrowed()
        fallback.require(time.monotonic()+135 < deadline_monotonic,
                         'no SDK receiving call near owner observation deadline')
        # Owner's invoke must persist intent BEFORE actual process creation.
        result['stage'] = 'RECEIVING_CALL_MAY_HAVE_STARTED'; persist()
        outcome = invoke()
        result['outcome'] = outcome; persist()
        log = outcome['stdout']+outcome['stderr']+outcome['supervisor_output']
        try:
            _, settled = audit.settled_helper(log, candidate_sha256=expected_sha256,
                                             candidate_bytes=expected_bytes)
        except BaseException as error:
            # No ordinary failed-prefix audit may turn absent/unknown helper
            # ownership into permission to drop the outer IO/CPU descriptions.
            raise UnresolvedOwnership('SDK receiving helper proof unresolved; retain owner') from error
        result['helper_settlement'] = settled; persist()
        fallback.require(outcome['returncode'] == 0 and outcome.get('fault') is None
                         and outcome['timed_out'] is False
                         and outcome['capture_truncated'] is False
                         and outcome['supervisor_capture_truncated'] is False,
                         'receiving invocation did not succeed with complete capture')
        verdict = audit.receiving_verdict(log, candidate_sha256=expected_sha256,
                                         candidate_bytes=expected_bytes, build_id=build_id)
        fallback.require(fallback.sha(target) == expected_sha256
                         and fallback.identity(source) == before,
                         'receiving bytes or disposable sender epoch changed')
        check_borrowed()
        result.update(complete=True, stage='VERIFIED_ONE_SEED', sdk=verdict,
                      receiver_identity=fallback.identity(target))
        persist()
        return result
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        result.update(complete=False, failure=repr(error)); persist()
        raise
