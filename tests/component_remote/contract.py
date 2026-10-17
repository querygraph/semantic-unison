"""Fixed source contract. Checking it never grants IO or dispatch rights."""
from pathlib import Path
import sys
import re
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'bench/sync')]
from component_remote.io import sha
from shared_cpu_pool import require
from shared_io_pool import CANONICAL_SHA256
from shared_dispatch import MANIFEST_SHA

CASES=(('stock','stock','supported'),('stock','ox','supported'),
       ('ox','stock','supported'),('ox','ox','supported'),
       ('stock','old-stock','no-capability'),('ox','old-stock','no-capability'),
       ('stock','stock','unsupported'),('ox','ox','disabled'))
PARAMETERS={'cases':8,'file_bytes':8192,'client_workers':2,'server_workers':2,
            'owner_credits':2,'total_grant':8,'call_seconds':30,'owner_seconds':300,
            'logical_IO_budget_bytes':1073741824,'logical_IO_budget_enforced':False}
FLAGS=['-semanticworkers','2','-maxthreads','2','-adobevalidate','off']
MODULES=('io.py','contract.py','audit.py','case.py','call.py','coordinator.py')
HELPERS=('tests/shared_cpu_pool.py','tests/shared_io_pool.py','tests/shared_dispatch.py',
 'tests/manual.py','tests/shared_process_owner.py','tests/private_camera_receiving/close.py',
 'tests/report/remote_probe.ml','tests/sdk_host_matrix/shared_child.py','bench/sync/measure.py',
 'bench/sync/ownership.py','bench/sync/proxy.py','bench/sync/launcher.py',
 'bench/sync/invocation_journal.py','bench/sync/fixtures.py','bench/sync/partitions.py',
 'bench/sync/artifact_pins.py','bench/sync/properties.py','bench/sync/read_stats.py')
def sources():
    files=[ROOT/'tests/component_remote'/name for name in MODULES]+[ROOT/name for name in HELPERS]
    files += [p for p in (ROOT/'src').rglob('*') if p.is_file() and
      p!=ROOT/'src/ubase/projectInfo.ml' and (p.suffix in ('.ml','.mli','.c','.h') or
      p.name in ('Makefile','Makefile.OCaml','dune') or p.name.endswith('.ox.mli.in'))]
    return {str(p):sha(p) for p in sorted(set(files))}
def checked_plan(plan):
    require(plan['schema']=='unison-component-remote/1' and plan['parameters']==PARAMETERS and
      all(type(plan['parameters'][key]) is type(value) for key,value in PARAMETERS.items()),'fixed component scope differs')
    require(plan['execution_source_sha256']==sources(),'component source pins differ')
    workspace=Path(plan['workspace'])
    require(workspace.parent==Path('/private/tmp') and
      re.fullmatch(r'u-cr-[0-9a-f]{8,16}',workspace.name) is not None,'fresh short private workspace required')
    require(set(plan['artifacts'])=={'stock-probe','ox-probe','stock','ox','old-stock'},'exact probe/server artifacts required')
    for value in list(plan['artifacts'].values())+plan['prerequisites']+[plan['interpreter']]:
        require(Path(value['path']).is_absolute() and type(value['sha256']) is str and
          len(value['sha256'])==64 and all(c in '0123456789abcdef' for c in value['sha256']),'malformed artifact pin')
    require(len(plan['prerequisites'])>=3 and plan['interpreter']['path']==sys.executable and
      plan['io_manifest_sha256']==CANONICAL_SHA256 and plan['cpu_manifest_sha256']==MANIFEST_SHA,
      'qualified interpreter/prerequisites/canonical pools required')
    return workspace
def check_artifacts(plan):
    for value in list(plan['artifacts'].values())+plan['prerequisites']+[plan['interpreter']]:
        require(sha(value['path'])==value['sha256'],'runtime artifact/prerequisite changed')
def command(plan,index):
    client,server,mode=CASES[index];directory=Path(plan['workspace'])/str(index)
    return [plan['artifacts'][client+'-probe']['path'],str(directory/'left'),str(directory/'right'),
            plan['artifacts'][server]['path'],str(directory/'launcher.py'),mode]
