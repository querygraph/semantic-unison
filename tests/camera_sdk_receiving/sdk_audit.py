"""Pure candidate/helper audit; no execution, SDK load, FD or signaling authority.

Helper process/group settlement is independent of receipt validity. Empty,
duplicate or unknown helper observations cannot prove the expected one call.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/validation_process'))
import records

FIELDS = ('candidate-sha256', 'candidate-size', 'driver-build', 'structure',
          'decode', 'raw-digest', 'errors', 'warnings')
BUILD = 'unison-sdk171-2724-v1-single'


def require(value, message):
    if not value:
        raise ValueError(message)


def receipt(raw, *, candidate_sha256, candidate_bytes, build_id):
    """Independent exact framing; optional missing digest remains explicitly missing."""
    require(type(raw) is bytes and len(raw) <= 4096, 'bounded full SDK receipt required')
    try:
        lines = raw.decode('ascii').split('\n')
    except UnicodeDecodeError as error:
        raise ValueError('SDK receipt is not ASCII') from error
    require(len(lines) == 11 and lines[0] == 'UNISON-DNG-VALIDATION 1'
            and lines[-2:] == ['END', ''], 'exact SDK receipt framing required')
    values = {}
    for name, line in zip(FIELDS, lines[1:9]):
        prefix = name + ' '
        require(line.startswith(prefix), 'SDK receipt field order or spelling differs')
        values[name] = line[len(prefix):]
    require(values['candidate-sha256'] == candidate_sha256
            and values['candidate-size'] == str(candidate_bytes)
            and values['driver-build'] == build_id, 'SDK receipt candidate/build binding differs')
    for name in ('errors', 'warnings'):
        require(re.fullmatch(r'(?:0|[1-9][0-9]{0,18})', values[name]) is not None
                and int(values[name]) <= 2**62 - 1, 'SDK receipt count is not canonical')
    require(values['structure'] == 'valid' and values['decode'] == 'success'
            and values['errors'] == '0', 'SDK structure/decode/errors finding rejected')
    require(values['raw-digest'] in ('valid', 'missing'),
            'SDK digest mismatch, unsupported or unchecked is not a pass')
    return dict(values, raw_digest_verified=values['raw-digest'] == 'valid')


def settled_helper(log, *, candidate_sha256, candidate_bytes, endpoint='server'):
    """Consume diagnostics from the pinned owner; never signal historical PIDs."""
    require(endpoint in ('client', 'server') and type(candidate_bytes) is int
            and 0 < candidate_bytes < 2**63
            and re.fullmatch('[0-9a-f]{64}', candidate_sha256) is not None,
            'exact expected helper/candidate identity required')
    processes, groups = records.parse(log), records.parse_groups(log)
    require(len(processes) == len(groups) == 1, 'exactly one helper process and group proof required')
    process, group = processes[0], groups[0]
    require(process.endpoint == group.endpoint == endpoint
            and process.pid is not None and process.pid == group.pid
            and process.candidate_sha256 == group.candidate_sha256 == candidate_sha256
            and process.candidate_bytes == candidate_bytes,
            'helper process/group/candidate binding differs')
    require(process.status is not None and process.status[0] in ('exit', 'signal'),
            'actual terminal helper wait status required')
    require(group.observation == 'observed' and group.other_members == 0,
            'helper group settlement unknown; retain owner')
    return process, {'helper_pid': process.pid, 'endpoint': endpoint,
                     'candidate_sha256': candidate_sha256, 'candidate_bytes': candidate_bytes,
                     'wait_status': list(process.status), 'outcome': process.outcome,
                     'observed_other_group_members_before_reap': 0,
                     'settlement_only': True}


def receiving_verdict(log, *, candidate_sha256, candidate_bytes, build_id=BUILD):
    """A successful require receiving additionally needs CLI/publication proof outside here."""
    process, settlement = settled_helper(log, candidate_sha256=candidate_sha256,
                                        candidate_bytes=candidate_bytes)
    require(process.outcome == 'completed' and process.status == ('exit', 0)
            and process.complete_capture, 'SDK helper did not complete with full capture')
    report = receipt(process.stdout, candidate_sha256=candidate_sha256,
                     candidate_bytes=candidate_bytes, build_id=build_id)
    return {'settlement': settlement, 'report': report,
            'raw_stdout_hex': process.stdout.hex(), 'raw_stderr_hex': process.stderr.hex(),
            'scope': 'one receiving candidate SDK receipt; not pixels or semantic eligibility'}
