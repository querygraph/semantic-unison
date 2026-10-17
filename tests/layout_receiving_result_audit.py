"""Pure request-bound post-run audit; no acquisition, execution or release.

Caller authenticates request/result/raw receipt provenance and separately obtains
the actual owner terminal. This consumes captured evidence, never live PIDs.
Kept outside the frozen worker closure so pending requests remain unchanged.
"""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bench/sync'))
from shared_audit import audit_shared
from run import internal_counters
from artifact_pins import parse

PROFILE='org.firstpair.dng-layout/0'

def require(condition,reason):
    if not condition:raise ValueError(reason)

def options(command,name):
    values=[]
    for at,word in enumerate(command):
        if word==name:
            require(at+1<len(command),'missing command option value')
            values.append(command[at+1])
    return values

def labels(command,name):
    result={}
    for value in options(command,name):
        label,separator,path=value.partition('=')
        require(separator and label in ('stock','ox') and label not in result and path.startswith('/'),
                'exact stock/Ox path labels required')
        result[label]=path
    require(set(result)=={'stock','ox'},'stock/Ox path coverage')
    return result

def audit(result,request):
    require(request['schema']=='unison-layout-only-receiving-request/1','layout request schema')
    fields=request['admission_fields'];command=fields['command']
    require(fields['target']=='sync-functional' and fields['cpu_credits']==8
            and '--layout-only-controls' in command and '--shared-qualification' in command
            and '--property-removal-controls' not in command,'exact layout request mode')
    params=result['parameters']
    require(params.get('layout_only_controls') is True
            and params.get('property_removal_controls',False) is False,
            'returned mode does not match requested layout controls')
    packets=options(command,'--packet-bytes')
    require(len(packets)<=1,'duplicate packet size')
    packet_bytes=int(packets[0]) if packets else 8192  # Frozen runner default.
    require(256<=packet_bytes<=1048576 and type(params['packet_bytes']) is int
            and params['packet_bytes']==packet_bytes,'packet size differs from requested command/default')
    expected_binary=parse(options(command,'--expected-binary-sha256'))
    expected_compiler=parse(options(command,'--expected-compiler-sha256'))
    require(set(expected_binary)==set(expected_compiler)=={'stock','ox'},'exact artifact labels')
    require(result['admitted_binary_sha256']==expected_binary
            and result['admitted_compiler_sha256']==expected_compiler,'returned artifact pins differ')
    binaries=labels(command,'--binary');compilers=labels(command,'--compiler')
    path_observations={}
    for label in ('stock','ox'):
        observed_binary=result['binaries'][label]['path'];observed_compiler=result['compilers'][label]['path']
        require(type(observed_binary) is str and observed_binary.startswith('/')
                and result['binaries'][label]['sha256']==expected_binary[label]
                and type(observed_compiler) is str and observed_compiler.startswith('/'),
                'selected artifact path/hash differs')
        # The runner resolves executable paths (e.g. /var -> /private/var and
        # ocamlopt -> ocamlopt.opt). Bind bytes by the admitted SHA, retain both
        # names as observations, and never resolve filesystem paths during audit.
        path_observations[label]={'requested_binary':binaries[label],'observed_binary':observed_binary,
                                  'requested_compiler':compilers[label],'observed_compiler':observed_compiler}
    source_directory=Path(command[1]).parent
    expected_scripts={Path(path).name:digest for path,digest in fields['execution_source_sha256'].items()
                      if Path(path).parent==source_directory}
    require('run.py' in expected_scripts and result['runner_sha256']==expected_scripts,
            'captured runner source set differs from exact request')
    summary=audit_shared(result)
    semantic_rows=0
    for sample in result['samples']:
        for stage in ('seed_sync','update_sync','noop_sync'):
            require(sample[stage]['command'][0]==result['binaries'][sample['label']]['path'],
                    'call uses a different client binary')
        for index,item in enumerate(sample['fixtures']):
            require(item['name']==f'image-{index:04d}.dng' and item['size_bytes']==2097152
                    and item['packet_offset']==1024 and item['packet_bytes']==params['packet_bytes'],
                    'generated fixture identity/geometry differs')
        if sample['mode']!='semantic':continue
        raw=sample['update_sync']
        log=raw['stdout']+raw['stderr']+raw['supervisor_output']
        derived=internal_counters(log,'semantic',2,2097152,primary_reads=False)
        require(derived['semantic_profiles']==[PROFILE] and derived['semantic_updates']==2,
                'raw SDE output does not prove two exact-layout updates')
        for key in ('semantic_profiles','semantic_updates','semantic_logical_write_bytes',
                    'semantic_write_attempts','semantic_payload_bytes','semantic_comparison_windows'):
            require(sample['counters'][key]==derived[key],'reported counter differs from raw output: '+key)
        require(derived['semantic_payload_bytes']==sum(item['packet_bytes'] for item in sample['fixtures']),
                'raw SDE payload does not match generated packets')
        semantic_rows+=1
    require(semantic_rows==6,'exact six semantic rows required')
    return {**summary,'semantic_rows':semantic_rows,'layout_profile_bound_to_request_and_raw_logs':True,
            'artifact_path_observations':path_observations,
            'scope':'Authenticated captured functional evidence only; actual parent terminal/raw process receipt authentication are separate. No release, SDK, camera, pixels, physical IO or timing authority.'}
