"""Source-owned successor suites on the named receiving owner, keyed by plan schema.

Each contract declares its cases, calls, limits and options; its cases module
binds one function per case to the retained Session. The original named suite
is not a successor and keeps its legacy-derived plan.
"""
from current_validation_paths import dng_contract,dng_cases,fs_contract,fs_cases

# schema: (contract, cases, freeze directory prefix, workspace prefix)
SUITES={
    dng_contract.SCHEMA:(dng_contract,dng_cases,'current-dng-merge-receiving-','/private/tmp/u-dmerge-'),
    fs_contract.SCHEMA:(fs_contract,fs_cases,'current-fs-properties-receiving-','/private/tmp/u-fsprop-'),
}


def contract(schema):
    """The successor contract for a plan schema, or None for the original named suite."""
    entry=SUITES.get(schema)
    return None if entry is None else entry[0]


def cases(schema):return SUITES[schema][1]
