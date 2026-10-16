"""Strict bounded receiving live-span diagnostics; no process/FD authority."""
from dataclasses import dataclass
from decimal import Decimal, DecimalException, ROUND_CEILING, ROUND_FLOOR
import math
import re
from intervals import IncompleteEvidence

PREFIX=re.compile(r'^\[(server: )?validation-live\] ')
NUMBER=r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:e[+-]?[0-9]+)?'
PATTERN=re.compile(r'Live span v0 owner-pid=([1-9][0-9]{0,9}) pid=(none|[1-9][0-9]{0,9}) '
    r'candidate-sha256=([0-9a-f]{64}) candidate-bytes=(0|[1-9][0-9]{0,18}) '
    r'clock=monotonic-seconds-v0 samples=(0|[1-9][0-9]{0,4}) valid=(true|false) '
    r'first=(none|'+NUMBER+r') last=(none|'+NUMBER+r')')

@dataclass(frozen=True)
class LiveRecord:
    endpoint:str
    owner_pid:int
    pid:int|None
    candidate_sha256:str
    candidate_bytes:int
    samples:int
    valid:bool
    first:Decimal|None
    last:Decimal|None


def parse(log):
    if type(log) is not str or len(log)>4*1024*1024:
        raise IncompleteEvidence('bounded diagnostic text required')
    result=[]
    for line in log.splitlines():
        prefix=PREFIX.match(line)
        if prefix is None:continue
        if len(line)>2048:raise IncompleteEvidence('live diagnostic line limit')
        match=PATTERN.fullmatch(line[prefix.end():])
        if match is None:raise IncompleteEvidence('unknown or malformed live diagnostic')
        owner,pid,digest,size,count,valid,first,last=match.groups()
        owner=int(owner);pid=None if pid=='none' else int(pid)
        size=int(size);count=int(count);valid=valid=='true'
        try:
            first=None if first=='none' else Decimal(first)
            last=None if last=='none' else Decimal(last)
        except DecimalException as error:
            raise IncompleteEvidence('invalid timestamp exponent') from error
        if owner>=2**31 or (pid is not None and pid>=2**31) or size>=2**63 or count>65536:
            raise IncompleteEvidence('live diagnostic numeric bound')
        if valid:
            if (pid is None or count==0 or first is None or last is None
                    or first<0 or last<first or last>=2**53):
                raise IncompleteEvidence('inconsistent valid live span')
        elif first is not None or last is not None:
            raise IncompleteEvidence('invalid span carries trusted timestamps')
        result.append(LiveRecord('server' if prefix.group(1) else 'client',owner,pid,
                                 digest,size,count,valid,first,last))
        if len(result)>4096:raise IncompleteEvidence('live diagnostic record limit')
    return result


def bound(record, *, endpoint, owner_pid, helper_pid, candidate_sha256, candidate_bytes):
    if (endpoint not in ('client','server') or type(owner_pid) is not int or not 0<owner_pid<2**31
            or type(helper_pid) is not int or not 0<helper_pid<2**31
            or type(candidate_bytes) is not int or not 0<=candidate_bytes<2**63
            or type(candidate_sha256) is not str or re.fullmatch('[0-9a-f]{64}',candidate_sha256) is None):
        raise IncompleteEvidence('typed independent binding required')
    if (record.endpoint,record.owner_pid,record.pid,record.candidate_sha256,record.candidate_bytes)!=(
            endpoint,owner_pid,helper_pid,candidate_sha256,candidate_bytes):
        raise IncompleteEvidence('live span differs from independent call/helper binding')
    if not record.valid or record.samples<2:
        raise IncompleteEvidence('two valid nonterminal samples required')
    # Contract the observed span rather than expanding it through decimal/binary
    # float representation and nanosecond rounding. This is not clock calibration.
    def inner(value,first):
        f=float(value);d=Decimal.from_float(f);margin=2*Decimal.from_float(math.ulp(f))
        n=(d+margin if first else d-margin)*10**9
        return int(n.to_integral_value(rounding=ROUND_CEILING if first else ROUND_FLOOR))
    start=inner(record.first,True);end=inner(record.last,False)
    if end<=start:raise IncompleteEvidence('no conservative positive live span')
    return {'first_ns':start,'last_ns':end,'clock_id':f'{endpoint}:owner-{owner_pid}:monotonic-seconds-v0',
            'settlement_proved':False,'sdk_activity_proved':False}
