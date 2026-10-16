"""Reuse the qualified owned transport/journal with explicit four-slot flags."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/camera_sdk_concurrency'))
from invocation import Invoker as OwnedInvoker
from plan import plan


class Invoker(OwnedInvoker):
    def __init__(self,directory,*,binary,tool,journal,script_pins,deadline):
        # Inherited __call__ owns the one-use latch, source/binary pin checks,
        # intent-before-dispatch and outcome-before-return journal ordering.
        super().__init__(directory,binary=binary,tool=tool,journal=journal,
                         script_pins=script_pins,deadline=deadline)
        contract=plan(binary,tool,directory)
        self.contract['argv']=contract['command']
        self.contract['environment_overrides']['UNISON_SYNC_BENCH_SERVER_FLAGS']=json.dumps(contract['server_flags'])
        self.contract['environment_overrides'].pop('UNISON_CONCURRENT_SYNTHETIC_ROOT')
        self.contract['resources']=contract
        self.contract['runtime_admitted']=False
