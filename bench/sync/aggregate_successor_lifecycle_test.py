#!/usr/bin/env python3
"""Reuse finite original worker fixtures with explicit benchmark ceiling branch."""
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/sdk_container_receive'))
import live_merge_aggregate as aggregate
original=aggregate.supervise

def benchmark_ceiling(function,workspace,**kwargs):
    # Fixture seconds remains12. No two-hour wait or benchmark is invoked.
    return original(function,workspace,maximum_seconds=7200,**kwargs)

aggregate.supervise=benchmark_ceiling
try:
    runpy.run_path(str(ROOT/'tests/sdk_container_receive/live_merge_aggregate_test.py'),run_name='__main__')
finally:
    aggregate.supervise=original
