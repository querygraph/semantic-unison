"""Pure serial negative receiving schedule, not a runtime grant or native result."""
from copy import deepcopy
from pathlib import PurePosixPath
import re
from sdk_merge_receiving.plan import schedule as merge_schedule,require

LIMITS=dict(cpu_credits=8,endpoint_workers=2,owner_credits=2,cli_calls=12,sdk_calls=6,
    observation_seconds=600,worker_seconds=570,per_cli_seconds=120,per_sdk_seconds=90,
    declared_logical_io_bytes=32*1024**3,physical_io_budget_enforced=False,retry_allowed=False)


def schedule(binaries,tool,workspace):
    root=PurePosixPath(workspace)
    require(type(workspace) is str and str(root)==workspace and root.parent==PurePosixPath('/private/tmp')
        and re.fullmatch('u-snr-[0-9a-f]{16}',root.name) is not None,'fresh short negative receiving namespace required')
    # Reuse the qualified resource/tool/peer command contract, never execute its
    # positive-merge rows or consume any prior workspace/admission.
    template=merge_schedule(binaries,tool,'/private/tmp/u-smg-'+root.name[6:])
    rows=[]
    for codec in ('uncompressed','jpeg','jxl'):
        original=next(r for r in template['rows'] if r['codec']==codec and r['stage']=='seed')
        common=deepcopy(original['server_flags'])
        index=common.index('-merge');del common[index:index+2]
        common.remove('-semanticmergebasecache')
        index=common.index('-adobevalidate');del common[index:index+2]
        for policy in ('require','warn'):
            directory=root/(codec+'-'+policy)
            for stage in ('seed','negative'):
                flags=[*common,'-adobevalidate','off' if stage=='seed' else policy]
                command=[binaries['stock']['path'],str(directory/'left'),'ssh://localhost/'+str(directory/'right'),
                    '-sshcmd',str(directory/'launcher.py'),'-servercmd',binaries['ox']['path'],
                    '-batch','-auto','-fastcheck','false','-times','-force',str(directory/'left'),
                    '-xferbycopying=false',*flags]
                require(len(str(directory/(stage+'.sock')).encode())<100,'bounded native socket path required')
                rows.append(dict(codec=codec,policy=policy,stage=stage,directory=str(directory),
                    command=command,server_flags=flags,
                    server_command=[binaries['ox']['path'],'-server','__new-rpc-mode',*flags],
                    expected_client_exit=1 if stage=='negative' and policy=='require' else 0,
                    expected_sdk_helpers=1 if stage=='negative' else 0,
                    destination_preserved=stage=='negative' and policy=='require'))
    return dict(rows=rows,limits=deepcopy(LIMITS),token_indexes=list(range(8)),
        configured_endpoint_plus_owner_credits=6,runtime_admitted=False,SDK_invoked=False,
        physical_io_cap=False,OS_thread_cap=False)
