"""Callable bounded private-payload slice reader; caller owns exact IO admission."""
import os
from pathlib import Path
import stat
import time

from private_maker_shape import inspect,MAX_READ
from private_camera_receiving.close import close_descriptors

FIELDS=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns','st_nlink','st_uid')


class InputChanged(RuntimeError):pass
class ObservationExpired(RuntimeError):pass


def stamp(s):return {k:getattr(s,k) for k in FIELDS}


def read_source(source,geometry,*,deadline):
    if (type(source) is not dict or set(source)!={'path','identity'}
            or type(source['path']) is not str or not Path(source['path']).is_absolute()
            or '..' in Path(source['path']).parts):
        raise ValueError('exact absolute source identity required')
    expected=source['identity']
    if (type(expected) is not dict or set(expected)!=set(FIELDS)
            or any(type(v) is not int or v<0 for v in expected.values())):
        raise ValueError('typed native eight-field identity required')
    keys={'payload_offset','payload_length','original_offset','byte_order','ifd_offset','max_requested_read_bytes'}
    if (type(geometry) is not dict or set(geometry)!=keys
            or any(type(geometry[k]) is not int for k in keys-{'byte_order'})
            or geometry['max_requested_read_bytes']!=MAX_READ
            or geometry['byte_order'] not in ('little','big')
            or not 6<=geometry['payload_length']<=64*1048576
            or not 0<=geometry['payload_offset']<=expected['st_size']
            or geometry['payload_length']>expected['st_size']-geometry['payload_offset']
            or not 0<=geometry['original_offset']<2**32
            or not 0<=geometry['ifd_offset']<=geometry['payload_length']-2):
        raise ValueError('exact bounded payload geometry required')
    if type(deadline) not in (int,float) or not time.monotonic()<deadline<float('inf'):
        raise ValueError('fresh finite observation deadline required')
    fd=os.open(source['path'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        def fence():
            if stamp(os.fstat(fd))!=expected or stamp(os.lstat(source['path']))!=expected:
                raise InputChanged('private source epoch/name binding changed')
        fence();s=os.fstat(fd)
        if (not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_uid!=os.getuid()
                or stat.S_IMODE(s.st_mode) not in (0o400,0o600,0o644)
                or not 0<s.st_size<=512*1048576):
            raise ValueError('owned regular retained input required')
        ranges=[];requested=0;received=0
        def read(offset,count):
            nonlocal requested,received
            if time.monotonic()>=deadline:raise ObservationExpired('slice observation expired')
            if (type(offset) is not int or type(count) is not int
                    or not 0<=offset<=geometry['payload_length']
                    or not 0<=count<=geometry['payload_length']-offset
                    or requested+count>MAX_READ):
                raise RuntimeError('slice reader escaped declared geometry/budget')
            fence();absolute=geometry['payload_offset']+offset;requested+=count
            raw=os.pread(fd,count,absolute);received+=len(raw)
            ranges.append(dict(offset=absolute,requested=count,received=len(raw)))
            fence();return raw
        try:
            shape=inspect(read,length=geometry['payload_length'],original_offset=geometry['original_offset'],
                          byte_order=geometry['byte_order'],ifd_offset=geometry['ifd_offset'])
            outcome='CANDIDATE_SHAPE';reason=None
        except ValueError as error:
            shape=None;outcome='DECLINED_CANDIDATE_SHAPE';reason=str(error)
        fence()
        return dict(schema='unison-private-maker-slice/1',diagnostic_complete=True,
                    outcome=outcome,reason=reason,shape=shape,read_ranges=ranges,
                    requested_read_bytes=requested,received_read_bytes=received,
                    max_requested_read_bytes=MAX_READ,source_epoch_unchanged=True,
                    semantic_eligibility=False,private_reference_closure_proved=False,
                    full_input_hash_computed=False,raw_payload_disclosed=False,
                    fd_closure_proved_by_return=True,
                    scope='Bounded candidate geometry only; return occurs only after qualified descriptor close.')
    finally:close_descriptors([fd])
