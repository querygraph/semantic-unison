"""Exact source-only slice contract; validation grants no payload access."""
from pathlib import Path
import re

from private_maker_slice import FIELDS,MAX_READ

ROOT=Path(__file__).resolve().parents[1]
TARGET='private-maker-slice'
SOURCE='/private/tmp/unison-dng-da-copy-57c830f336da4ef099150958b2f3d666/source-clone.DNG'
IDENTITY=dict(st_dev=16777223,st_ino=307228717,st_size=193851848,
              st_mtime_ns=1792099229810540469,st_ctime_ns=1792113844382073309,
              st_mode=33024,st_nlink=1,st_uid=501)
GEOMETRY=dict(payload_offset=10990,payload_length=6556,original_offset=1404,
              byte_order='little',ifd_offset=0,max_requested_read_bytes=MAX_READ)


def check(value):
    """Pin an existing framing observation, never infer a vendor grammar."""
    keys={'schema','target','workspace','source','geometry','worker_seconds',
          'cpu_credits','io_mode','semantic_eligibility','sdk_validation',
          'source_hash_requested','pointed_values_requested'}
    if type(value) is not dict or set(value)!=keys:
        raise ValueError('exact slice plan fields required')
    if (value['schema']!='unison-private-maker-slice-plan/1'
            or value['target']!=TARGET or type(value['worker_seconds']) is not int
            or value['worker_seconds']!=10 or type(value['cpu_credits']) is not int
            or value['cpu_credits']!=8 or value['io_mode']!='EX_GLOBAL'
            or any(value[k] is not False for k in ('semantic_eligibility','sdk_validation',
                       'source_hash_requested','pointed_values_requested'))):
        raise ValueError('one diagnostic-only shared8 slice scope required')
    workspace=value['workspace']
    if (type(workspace) is not str
            or re.fullmatch(r'/private/tmp/unison-private-maker-slice-[0-9a-f]{32}',workspace) is None):
        raise ValueError('fresh private slice namespace required')
    source=value['source']
    if (type(source) is not dict or set(source)!={'path','identity'}
            or source['path']!=SOURCE or type(source['identity']) is not dict
            or set(source['identity'])!=set(FIELDS)
            or any(type(n) is not int for n in source['identity'].values())
            or source['identity']!=IDENTITY):
        raise ValueError('exact retained clone identity required')
    geometry=value['geometry']
    if (type(geometry) is not dict or set(geometry)!=set(GEOMETRY)
            or any(type(geometry[k]) is not int for k in GEOMETRY if k!='byte_order')
            or geometry!=GEOMETRY):
        raise ValueError('exact saved payload geometry required')
    return value


def worker_argv(value,*,interpreter,plan_path,plan_sha256):
    check(value)
    for name in (interpreter,plan_path):
        if type(name) is not str or not Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('absolute interpreter and plan paths required')
    if type(plan_sha256) is not str or re.fullmatch('[0-9a-f]{64}',plan_sha256) is None:
        raise ValueError('exact plan digest required')
    return [interpreter,str(ROOT/'tests/private_maker_execute.py'),'--worker',
            '--plan',plan_path,'--plan-sha256',plan_sha256,'--workspace',value['workspace']]
