"""Bounded owner diagnostic parsing; never process or publication authority."""
from __future__ import annotations

from dataclasses import dataclass
import re

MAX_LOG_BYTES = 4 * 1024 * 1024
MAX_LINE = 20000
PREFIX = re.compile(r'^\[(server: )?validation-process\] ')
DECIMAL = r'(?:0|[1-9][0-9]{0,18})'
PATTERN = re.compile(
    r'Helper result v0 pid=(none|[1-9][0-9]{0,9}) '
    r'status=(none|(?:exit|signal|stopped):-?(?:0|[1-9][0-9]{0,9})) '
    r'outcome=(completed|cancelled|timed-out|output-limit|failed) '
    r'candidate-sha256=([0-9a-f]{64}) candidate-bytes=(' + DECIMAL + r') '
    r'capture-truncated=(true|false) stdout-truncated=(true|false) '
    r'stderr-truncated=(true|false) stdout-hex=([0-9a-f]{0,8192}) '
    r'stderr-hex=([0-9a-f]{0,8192})')


@dataclass(frozen=True)
class Record:
    endpoint: str
    pid: int | None
    status: tuple[str, int] | None
    outcome: str
    candidate_sha256: str
    candidate_bytes: int
    capture_truncated: bool
    stdout_truncated: bool
    stderr_truncated: bool
    stdout: bytes
    stderr: bytes

    @property
    def complete_capture(self):
        # Not a verdict: an exit-zero child may still report validation errors.
        return not (self.capture_truncated or self.stdout_truncated or self.stderr_truncated)


def parse(log):
    if not isinstance(log, str) or len(log) > MAX_LOG_BYTES:
        raise ValueError('diagnostic log size/type limit')
    if len(log.encode('utf-8')) > MAX_LOG_BYTES:
        raise ValueError('diagnostic log byte limit')
    result = []
    for line in log.splitlines():
        prefix = PREFIX.match(line)
        if prefix is None:
            continue
        if len(line) > MAX_LINE:
            raise ValueError('diagnostic line size limit')
        fields = PATTERN.fullmatch(line[prefix.end():])
        if fields is None:
            raise ValueError('malformed or unknown helper diagnostic')
        pid, status, outcome, digest, size, capture_clip, out_clip, err_clip, out, err = fields.groups()
        pid = None if pid == 'none' else int(pid)
        status = None if status == 'none' else status.split(':')
        if status is not None:
            if str(int(status[1])) != status[1]:
                raise ValueError('noncanonical process status')
            status = (status[0], int(status[1]))
            if not -(2**31) <= status[1] < 2**31:
                raise ValueError('process status overflow')
            if status[0] == 'exit' and not 0 <= status[1] <= 255:
                raise ValueError('invalid exit status')
        if pid is not None and pid >= 2**31:
            raise ValueError('PID overflow')
        if pid is None and status is not None or outcome == 'completed' and (pid is None or status is None):
            raise ValueError('inconsistent direct-child identity/status')
        if int(size) >= 2**63:
            raise ValueError('candidate size overflow')
        try:
            stdout, stderr = bytes.fromhex(out), bytes.fromhex(err)
        except ValueError as error:
            raise ValueError('odd-length diagnostic hex') from error
        if out_clip == 'true' and len(stdout) != 4096 or err_clip == 'true' and len(stderr) != 4096:
            raise ValueError('clipped stream does not contain its bounded prefix')
        result.append(Record('server' if prefix.group(1) else 'client', pid, status,
                             outcome, digest, int(size), capture_clip == 'true',
                             out_clip == 'true', err_clip == 'true', stdout, stderr))
        if len(result) > 4096:
            raise ValueError('diagnostic record count limit')
    return result
