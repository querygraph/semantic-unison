"""Pure warm generated-input receiving comparison; no execution or admission."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from sdk_multifile.plan import plan as seed_plan


CONFIGURATIONS=(('stock',1),('ox',1),('stock',3),('ox',3))


def configuration(index):
    if type(index) is not int or not 0<=index<24:raise ValueError('exact finite row index required')
    round_index=index//4;offset=round_index%4
    return (CONFIGURATIONS[offset:]+CONFIGURATIONS[:offset])[index%4]


def row_matches(actual,expected):
    """Exact values and scalar types; bool must never stand in for an int."""
    return (type(actual) is dict and actual==expected
            and all(type(actual[k]) is type(v) for k,v in expected.items()))


def row_plan(binary,tool,workspace,index):
    label,workers=configuration(index)
    if binary.get('label')!=label:raise ValueError('compiler identity differs from scheduled row')
    w=Path(workspace)
    if not w.is_absolute() or '..' in w.parts:raise ValueError('absolute private comparison namespace required')
    directory=w/('r'+str(index//4))/(label+'-w'+str(workers))
    seed=seed_plan(binary,tool,directory);command=seed['command'];flags=seed['server_flags']
    for argv in (command,flags):
        for option in ('-semanticworkers','-maxthreads'):
            at=argv.index(option);argv[at+1]=str(workers)
    assert command[-len(flags):]==flags
    return dict(index=index,round=index//4,phase='warmup' if index<4 else 'measured',
                label=label,endpoint_workers=workers,directory=str(directory),command=command,server_flags=flags,
                reserved_cpu_credits=8,configured_endpoint_and_owner_credits=workers*2+2,
                maximum_sdk_calls=2,sdk_threads_per_helper=1)


def comparison(binaries,tool,workspace):
    if type(binaries) is not dict or set(binaries)!={'stock','ox'}:
        raise ValueError('exact stock/Ox comparison required')
    # Rotate configuration order; preserve every raw result and its sequence.
    # This does not randomize caches or remove shared-machine activity.
    rows=[row_plan(binaries[configuration(index)[0]],tool,workspace,index) for index in range(24)]
    return dict(schema='unison-sdk-receiving-throughput-comparison/1',rows=rows,
                warmup_rows=4,measured_rows=20,maximum_cli_calls=24,maximum_sdk_calls=48,
                distinct_generated_inputs=2,maximum_native_clone_preparations=48,
                cpu_token_indexes=list(range(8)),reserved_cpu_credits=8,io_mode='EX_GLOBAL',
                owner_observation_seconds=600,worker_observation_seconds=570,per_cli_observation_seconds=120,
                declared_logical_io_bytes=32*1073741824,io_budget_instrumented=False,
                runtime_admitted=False,runtime_dispatcher_qualified=False,
                expected_results='Exact source/output SHA plus complete raw SDK and client/server/pump/helper/group/FD proofs for every attempted call; unknown retains.',
                interpretation='Warm single-host generated-input end-to-end receiving validation comparison. Worker1 vs3 changes hashing/transfer/scheduling as well as helper concurrency; not isolated SDK decode throughput. Same8 reserved credits for both. Five measured repetitions per configuration, all samples retained; no quiet/cache-control or speedup claim from source preparation.')
