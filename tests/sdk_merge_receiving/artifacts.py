"""Hash declared executable payloads ONLY inside already-owned IO/CPU."""
import hashlib
from cached_benchmark.contract import read_bytes
from sdk_merge_receiving.plan import require


def verify(packet):
    refs=[packet['interpreter'],packet['tool'],*packet['binaries'].values(),
          *(b['compiler'] for b in packet['builds'].values())]
    require(len({r['path'] for r in refs})==6,'exact distinct executable set required')
    result={}
    for ref in refs:
        actual=hashlib.sha256(read_bytes(ref['path'],256*1048576)).hexdigest()
        require(actual==ref['sha256'],'executable changed: '+ref['path'])
        result[ref['path']]=actual
    return dict(executable_sha256=result,io_ownership_independently_proved=False,requires_owned_io=True,
                resource_release_authorized=False)
