"""Read back exact generated hash objects/configuration after finite builds."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests/sdk_host_matrix')]
from shared_child import invoke
from camera_sdk_concurrency.persistence import save
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record


def pin(path):
    p = Path(path); raw = p.read_bytes()
    return dict(path=str(p.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def main():
    assert len(sys.argv) == 2
    packet = Path(sys.argv[1]); result = json.loads(packet.read_text())
    assert result['complete'] and len(result['builds']) == 5
    work = Path(tempfile.mkdtemp(prefix='unison-hash-audit-', dir='/private/tmp'))
    proof = dict(complete=False, input=pin(packet), rows=[], source_checks=0,
                 SDK_invoked=False, non_Apple_qualified=False)
    for row in result['builds']:
        report = json.loads(Path(row['report']['path']).read_text())
        assert pin(row['report']['path']) == row['report']
        assert pin(row['binary']['path']) == row['binary']
        for relative, expected in report['source_sha256'].items():
            assert pin(ROOT / relative)['sha256'] == expected
            proof['source_checks'] += 1
        source = Path(report['workspace']) / ('src' if row['system'] == 'make' else '_build/default/src')
        obj = source / 'semanticHash_stubs.o'
        outcome = invoke(['/usr/bin/nm', '-g', str(obj)], dict(os.environ), time.monotonic()+10)
        closed = outcome['client_cleanup']
        if not (closed['reaped'] and closed['other_group_members_absent_before_reap']):
            raise UnresolvedOwnership('hash object inspector group unresolved')
        assert outcome['returncode'] == 0 and not outcome['capture_truncated']
        symbols = outcome['stdout']
        if row['backend'] == 'openssl':
            assert '_unison_semantic_evp_create' in symbols and '_EVP_MD_fetch' in symbols
            assert '_CC_SHA256_Init' not in symbols
        else:
            assert '_CC_SHA256_Init' in symbols and '_unison_semantic_evp_create' not in symbols
        configured = source / ('Makefile.cfg' if row['system'] == 'make' else 'semantic_hash_cflags.sexp')
        text = configured.read_text()
        assert ('-DUNISON_SEMANTIC_HASH_OPENSSL' in text) == (row['backend'] == 'openssl')
        proof['rows'].append(dict(label=row['label'], backend=row['backend'], system=row['system'],
                                  object=pin(obj), configuration=pin(configured), inspector=outcome))
        save(work, proof)
    proof['complete'] = True; save(work, proof); print(work, flush=True)


if __name__ == '__main__':
    try: main()
    except UnresolvedOwnership as error:
        retain_after_record(lambda: print(repr(error), file=sys.stderr, flush=True))
