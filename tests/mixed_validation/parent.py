import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
"""Parent-side exact prefix and stored-input audit under retained IO ownership."""
import os

from mixed_validation.plan import commands
from mixed_validation.audit import audit_prefix
from mixed_validation.artifacts import verified_hash,verify_sources
from sdk_multifile.clone import stamp


def audit(result,plan,*,check_files=True):
    argv=commands(plan)
    proof=audit_prefix(result,commands=argv,metadata_version=plan['metadata']['version'],require_admission=True)
    if check_files:
        from mixed_validation.build_receipts import verify as verify_build
        for row in plan['probes']:verify_build(row)
        verify_sources(plan)
        # Hash only disposable candidates for calls with actual outcomes.
        # The retained source remains an exact metadata-only fence.
        for entry in result['invocations']:
            index=entry['index']
            verified_hash(dict(path=argv[index][3],sha256=plan['input']['sha256'],bytes=plan['input']['bytes']))
        if stamp(os.lstat(plan['input']['path']))!=plan['input_epoch']:
            raise ValueError('borrowed generated input changed before parent release')
    return dict(proof,parent_input_bytes_reverified=check_files,
                execution_source_bytes_reverified=check_files,
                worker_exit_bound=False,resource_release_authorized=False)


def bind_exit(proof,returncode):
    """Consume actual worker wait status separately from prefix evidence."""
    if (type(returncode) is not int
            or (proof['functional_status']=='PASSED')!=(returncode==0)):
        raise ValueError('mixed result contradicts actual worker exit')
    return dict(proof,worker_exit_bound=True,resource_release_authorized=False)
