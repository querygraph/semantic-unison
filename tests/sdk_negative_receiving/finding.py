"""Pure negative-finding parser, deliberately separate from success acceptance.

No execution/admission/FD authority. An expected rejection is not settlement of
CLI/server/worker resources or proof that a destination remained unpublished.
"""
import re
from camera_sdk_receiving.sdk_audit import FIELDS,BUILD,settled_helper,require


def digest_mismatch(raw,*,candidate_sha256,candidate_bytes,build_id=BUILD):
    require(type(candidate_sha256) is str and re.fullmatch('[0-9a-f]{64}',candidate_sha256)
        and type(candidate_bytes) is int and 0<candidate_bytes<=128*1048576
        and build_id==BUILD,'exact qualified candidate/build required')
    require(type(raw) is bytes and 0<len(raw)<=4096,'bounded full raw receipt required')
    try:lines=raw.decode('ascii').split('\n')
    except UnicodeDecodeError as error:raise ValueError('ASCII SDK receipt required') from error
    require(len(lines)==11 and lines[0]=='UNISON-DNG-VALIDATION 1'
        and lines[-2:]==['END',''],'exact negative receipt framing required')
    values={}
    for name,line in zip(FIELDS,lines[1:9]):
        prefix=name+' ';require(line.startswith(prefix),'exact ordered negative receipt fields required')
        values[name]=line[len(prefix):]
    require(values['candidate-sha256']==candidate_sha256
        and values['candidate-size']==str(candidate_bytes)
        and values['driver-build']==build_id,'negative candidate binding differs')
    for key in ('errors','warnings'):
        require(re.fullmatch(r'(?:0|[1-9][0-9]{0,18})',values[key]) is not None
            and int(values[key])<=2**62-1,'canonical bounded finding counts required')
    require(values['structure']=='valid' and values['decode']=='success'
        and values['raw-digest']=='mismatch' and int(values['errors'])>0,
        'expected post-decode raw digest mismatch with errors required')
    return dict(values,expected_negative_finding=True,validation_passed=False,
                receiving_publication_proved=False,resource_release_authorized=False)


def helper(log,*,candidate_sha256,candidate_bytes):
    process,settlement=settled_helper(log,candidate_sha256=candidate_sha256,
                                     candidate_bytes=candidate_bytes,endpoint='server')
    require(process.outcome=='completed' and process.status==('exit',0)
            and process.complete_capture,'fully captured normal SDK helper receipt required')
    report=digest_mismatch(process.stdout,candidate_sha256=candidate_sha256,
                           candidate_bytes=candidate_bytes)
    return dict(report=report,settlement=settlement,raw_stdout_hex=process.stdout.hex(),
        raw_stderr_hex=process.stderr.hex(),parent_cli_audit_required=True,
        destination_fence_required=True,resource_release_authorized=False)
