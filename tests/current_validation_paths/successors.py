"""Source-owned successor suites on the named receiving owner, keyed by plan schema.

Each contract declares its cases, calls, limits and options; its cases module
binds one function per case to the retained Session. The original named suite
is not a successor and keeps its legacy-derived plan.
"""
from current_validation_paths import dng_contract,dng_cases,fs_contract,fs_cases,cross_contract,cross_cases

# schema: (contract, cases, freeze directory prefix, workspace prefix)
SUITES={
    dng_contract.SCHEMA:(dng_contract,dng_cases,'current-dng-merge-receiving-','/private/tmp/u-dmerge-'),
    fs_contract.SCHEMA:(fs_contract,fs_cases,'current-fs-properties-receiving-','/private/tmp/u-fsprop-'),
    cross_contract.SCHEMA:(cross_contract,cross_cases,'current-cross-peer-receiving-','/private/tmp/u-xpeer-'),
}


def contract(schema):
    """The successor contract for a plan schema, or None for the original named suite."""
    entry=SUITES.get(schema)
    return None if entry is None else entry[0]


def cases(schema):return SUITES[schema][1]


def peered(schema):
    """Whether a plan schema pins a peer server built by the other compiler."""
    return schema==cross_contract.SCHEMA


def server_binary(packet):
    """The endpoint binary that serves the right replica: the pinned peer, else the client's own."""
    return packet['peer']['binary']['path'] if 'peer' in packet else packet['binary']['path']
