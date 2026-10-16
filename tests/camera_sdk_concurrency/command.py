"""Pure command construction for one future two-file receiving seed; no dispatch."""
import json
import os
from pathlib import Path
import re
from planning import plan


def command(directory, *, binary, tool):
    directory=Path(directory)
    if not directory.is_absolute() or '..' in directory.parts:
        raise ValueError('absolute owned namespace required')
    for item in (binary,tool):
        if (type(item) is not dict or not Path(item.get('path','')).is_absolute()
                or re.fullmatch('[0-9a-f]{64}',item.get('sha256','')) is None):
            raise ValueError('exact absolute executable and SHA pins required')
    if binary.get('label') not in ('stock','ox'):
        raise ValueError('exact same-compiler case label required')
    if tool.get('threads')!=1 or type(tool.get('threads')) is not int:
        raise ValueError('single-thread validator only')
    build=tool.get('build_id')
    if type(build) is not str or re.fullmatch('[A-Za-z0-9_.-]{1,128}',build) is None:
        raise ValueError('bounded exact validator build ID required')
    resources=plan()
    flags=['-clone','auto','-semanticworkers','3','-maxthreads','3',
        '-semanticmaxinflight','3','-semanticvolumejobs','2',
        '-adobevalidate','require','-adobevalidator',tool['path'],
        '-adobevalidatorhash',tool['sha256'],'-adobevalidatorbuild',build,
        '-adobevalidatorthreads','1','-adobevalidatetimeout','90',
        '-adobevalidatorworkspace','2048','-semanticpayloadbudget','6144',
        '-validationtreememory','0','-semanticdescriptorbudget','64',
        '-debug','validation-process','-debug','validation-group','-debug','validation-live']
    socket=directory/'seed.sock'
    if len(os.fsencode(socket))>=100:raise ValueError('bounded Darwin socket path required')
    argv=[binary['path'],str(directory/'left'),'ssh://localhost/'+str(directory/'right'),
        '-sshcmd',str(directory/'launcher.py'),'-servercmd',binary['path'],
        '-batch','-auto','-fastcheck','false','-times',*flags]
    overrides={'UNISON_CONCURRENT_SYNTHETIC_ROOT':str(directory),'UNISON':str(directory/'state'),'UNISON_SYNC_BENCH_BINARY':binary['path'],
        'UNISON_SYNC_BENCH_SERVER_FLAGS':json.dumps(flags),
        'UNISON_SYNC_BENCH_PROXY_RECEIPT':str(directory/'seed-proxy.json'),
        'UNISON_SYNC_BENCH_SOCKET':str(socket),'UNISON_SYNC_BENCH_DEADLINE_SECONDS':'125'}
    if any('\0' in value for value in argv+list(overrides.values())):
        raise ValueError('NUL in command contract')
    return {'argv':argv,'environment_overrides':overrides,'resources':resources,
        'one_seed':True,'expected_candidates':2,'maximum_validator_calls':2,
        'per_cli_observation_seconds':120,'runtime_admitted':False,
        'requires_existing_exglobal_then_unison_00_07':True}
