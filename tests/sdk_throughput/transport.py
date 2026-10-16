"""Exact-row adapter around the already qualified one-shot owned transport."""
import json
import copy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from sdk_multifile.transport import Invoker as OwnedInvoker
from sdk_throughput.plan import row_plan


class RowJournal:
    """Bind legacy transport's fixed identity to the exact executed row flags.

    The underlying owned transport's begin identity has workers3. That value
    is not evidence for this successor; only the independently rebuilt command
    and scheduled row authorize writing workers1 or3 to its outer journal.
    """
    def __init__(self,row,journal):self.row=row;self.journal=journal
    def begin(self,identity,command):
        r=self.row
        expected=dict(label=r['label'],mode='semantic',workers=3,directory=r['directory'],stage='seed')
        if identity!=expected or command!=r['command']:raise ValueError('owned transport identity/command differs from scheduled row')
        self.journal.begin(dict(identity,workers=r['endpoint_workers']),command)
    def finish(self,outcome):return self.journal.finish(outcome)


class Invoker(OwnedInvoker):
    def __init__(self,row,*,binary,tool,journal,script_pins,deadline):
        if type(row) is not dict or type(row.get('directory')) is not str:raise ValueError('exact scheduled row required')
        row=copy.deepcopy(row)
        directory=Path(row['directory'])
        if len(directory.parents)<2 or row!=row_plan(binary,tool,directory.parents[1],row.get('index')):
            raise ValueError('row command/limits/namespace differs')
        super().__init__(directory,binary=binary,tool=tool,journal=RowJournal(row,journal),script_pins=script_pins,deadline=deadline)
        self.contract['argv']=list(row['command'])
        self.contract['environment_overrides']['UNISON_SYNC_BENCH_SERVER_FLAGS']=json.dumps(row['server_flags'])
        self.contract['resources']=dict(row)
        self.contract['runtime_admitted']=False
