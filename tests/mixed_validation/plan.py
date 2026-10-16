"""Pure exact mixed-work plan contract. Parsing grants no runtime permission."""
from pathlib import PurePosixPath
import re

SCHEMA='unison-mixed-validation-plan/1'
TARGET='mixed-sdk-metadata-hash'
LIMITS=dict(cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',
            probes=2,sdk_helpers=2,metadata_helpers=2,hash_tasks_per_probe=16,
            observation_seconds=300,probe_seconds=120,helper_seconds=10,
            backend_payload_bytes=2192*1048576,backend_descriptor_credits=64,
            declared_io_bytes=8*1024**3,physical_io_budget_enforced=False)


def require(value,message):
    if not value:raise ValueError(message)


def path(value):
    require(type(value) is str and 0<len(value)<=4096 and '\0' not in value
            and value.startswith('/') and str(PurePosixPath(value))==value
            and '..' not in PurePosixPath(value).parts,'canonical absolute path required')
    return value


def artifact(value):
    require(type(value) is dict and set(value)=={'path','sha256','bytes'},'exact artifact fields required')
    path(value['path'])
    require(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'artifact SHA required')
    require(type(value['bytes']) is int and 0<value['bytes']<=128*1048576,'bounded artifact bytes required')


def commands(plan):
    """Validate exact declarations and derive both argv; performs zero IO."""
    require(type(plan) is dict and set(plan)=={'schema','target','workspace','probes',
            'sdk','metadata','input','input_epoch','ancestry','source_pins','limits'},'exact plan fields required')
    require(plan['schema']==SCHEMA and plan['target']==TARGET,'mixed plan version/target differs')
    workspace=path(plan['workspace'])
    require(workspace.startswith('/private/tmp/unison-mixed-') and workspace!='/private/tmp/unison-mixed-','private mixed workspace required')
    require(type(plan['limits']) is dict and plan['limits']==LIMITS
            and all(type(plan['limits'][k]) is type(v) for k,v in LIMITS.items())
            and all(type(i) is int for i in plan['limits']['token_indexes']),'exact typed mixed limits required')
    probes=plan['probes']
    require(type(probes) is list and len(probes)==2,'exact stock/Ox pair required')
    for row,label in zip(probes,('stock','ox')):
        require(type(row) is dict and set(row)=={'label','executable','build_receipt'}
                and row['label']==label,'stock then Ox required')
        artifact(row['executable']);artifact(row['build_receipt'])
    require(probes[0]['executable']['path']!=probes[1]['executable']['path'],'distinct compiled probes required')
    sdk=plan['sdk'];metadata=plan['metadata']
    require(type(sdk) is dict and set(sdk)=={'executable','manifest','build_id'}
            and sdk['build_id']=='unison-sdk171-2724-v1-single','qualified single-thread SDK only')
    artifact(sdk['executable']);artifact(sdk['manifest'])
    require(type(metadata) is dict and set(metadata)=={'executable','version','inventory'}
            and type(metadata['version']) is str and re.fullmatch(r'[0-9]+\.[0-9]+',metadata['version']) is not None,
            'exact metadata version/inventory required')
    artifact(metadata['executable']);artifact(metadata['inventory'])
    artifact(plan['input'])
    epoch=plan['input_epoch']
    require(type(epoch) is dict and set(epoch)=={'st_dev','st_ino','st_size','st_mtime_ns',
            'st_ctime_ns','st_mode','st_nlink','st_uid'} and all(type(v) is int and v>=0 for v in epoch.values()),'exact eight-field input epoch required')
    require(epoch['st_size']==plan['input']['bytes'] and epoch['st_nlink']==1
            and epoch['st_mode'] in (0o100400,0o100644),'single-link readonly/source fixture required')
    ancestry=plan['ancestry'];pins=plan['source_pins']
    require(type(ancestry) is list and 1<=len(ancestry)<=16,'bounded input ancestry required')
    require(type(pins) is list and 1<=len(pins)<=512,'bounded execution inventory required')
    for group in (ancestry,pins):
        for item in group:artifact(item)
        require(len({item['path'] for item in group})==len(group),'duplicate inventory paths')
    # No fixture/tool may be prepared inside the disposable workspace itself.
    external=[plan['input'],sdk['executable'],sdk['manifest'],metadata['executable'],metadata['inventory']]
    external+=ancestry+pins+[r[k] for r in probes for k in ('executable','build_receipt')]
    require(all(not (a['path']==workspace or a['path'].startswith(workspace+'/')) for a in external),'pinned inputs/tools must precede private workspace')
    return [[row['executable']['path'],sdk['executable']['path'],metadata['executable']['path'],
             workspace+'/'+row['label']+'/uncompressed.dng',sdk['executable']['sha256'],
             sdk['build_id'],plan['input']['sha256'],str(plan['input']['bytes'])] for row in probes]
