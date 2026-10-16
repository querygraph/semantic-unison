"""Exact launch and inherited metadata binding; no locks or release authority."""
import os
from pathlib import Path
import re
import sys
from plan import commands,path,TARGET

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tests/sdk_host_matrix')]
from shared_binding import verify


def worker_argv(plan,*,interpreter,plan_path,plan_sha256):
    commands(plan)
    path(interpreter);path(plan_path)
    if type(plan_sha256) is not str or re.fullmatch('[0-9a-f]{64}',plan_sha256) is None:
        raise ValueError('exact frozen plan SHA required')
    return [interpreter,'-B',str(ROOT/'tests/mixed_validation/execute.py'),'--worker',
            '--plan',plan_path,'--plan-sha256',plan_sha256,'--workspace',plan['workspace']]


def bind(plan,start,command,*,interpreter,plan_path,plan_sha256,parent_pid,worker_pid,
         observe=os.fstat):
    expected=worker_argv(plan,interpreter=interpreter,plan_path=plan_path,plan_sha256=plan_sha256)
    if command!=expected:raise ValueError('mixed worker exact launch differs')
    if parent_pid==worker_pid:raise ValueError('distinct actual parent and worker required')
    return verify(start,expected,parent_pid=parent_pid,worker_pid=worker_pid,
                  target=TARGET,observe=observe)
