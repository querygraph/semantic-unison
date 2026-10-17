"""Bounded external-process diagnostics; never owned handles or release authority."""
from dataclasses import dataclass
import re

MAX_LOG_BYTES = 4 * 1024 * 1024
MAX_LINE = 512
MAX_RECORDS = 4096
PREFIX = re.compile(r'^\[(server: )?external-process\] ')
PATTERN = re.compile(
    r'External result v0 pid=(none|[1-9][0-9]{0,9}) '
    r'status=(none|(?:exit|signal|stopped):-?(?:0|[1-9][0-9]{0,9})) '
    r'outcome=(completed|cancelled|timed-out|output-limit|failed) '
    r'cpu-weight=([1-9][0-9]{0,18}) '
    r'other-members=(unobserved|unknown|0|[1-9][0-9]{0,9}) '
    r'capture-truncated=(true|false)')


@dataclass(frozen=True)
class Record:
    endpoint: str
    pid: int | None
    status: tuple[str, int] | None
    outcome: str
    cpu_weight: int
    group_observation: str
    other_members: int | None
    capture_truncated: bool
    # A merged output stream can contain helper-authored lookalike lines.
    producer_authenticated: bool = False
    resource_release_authorized: bool = False


def parse(log):
    if type(log) is not str or len(log) > MAX_LOG_BYTES:
        raise ValueError('bounded diagnostic text required')
    try:
        size = len(log.encode('utf-8'))
    except UnicodeError as error:
        raise ValueError('invalid diagnostic encoding') from error
    if size > MAX_LOG_BYTES:
        raise ValueError('diagnostic byte limit')
    records = []
    for line in log.splitlines():
        prefix = PREFIX.match(line)
        if prefix is None:
            continue
        if len(line) > MAX_LINE or len(records) >= MAX_RECORDS:
            raise ValueError('diagnostic line/count limit')
        match = PATTERN.fullmatch(line[prefix.end():])
        if match is None:
            raise ValueError('malformed or unknown external-process record')
        pid, status, outcome, weight, members, clipped = match.groups()
        pid = None if pid == 'none' else int(pid)
        if pid is not None and pid >= 2**31:
            raise ValueError('PID overflow')
        if status == 'none':
            status = None
        else:
            kind, number = status.split(':')
            value = int(number)
            if str(value) != number or not -(2**31) <= value < 2**31:
                raise ValueError('noncanonical or overflowing process status')
            if kind == 'exit' and not 0 <= value <= 255:
                raise ValueError('invalid exit status')
            status = kind, value
        if pid is None and status is not None or outcome == 'completed' and (pid is None or status is None):
            raise ValueError('inconsistent child identity/status')
        weight = int(weight)
        if weight >= 2**63:
            raise ValueError('CPU declaration overflow')
        observation = members if members in ('unknown', 'unobserved') else 'observed'
        count = None if observation != 'observed' else int(members)
        if count is not None and (pid is None or count >= 2**31):
            raise ValueError('invalid group observation')
        records.append(Record('server' if prefix.group(1) else 'client', pid, status,
                              outcome, weight, observation, count, clipped == 'true'))
    return records
