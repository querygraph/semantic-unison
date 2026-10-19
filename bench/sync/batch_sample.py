"""One-use corpus phase composition, not a resource-owning dispatcher.

Caller must own fresh IO/CPU admission, binaries, roots, transport and evidence
Store. A callback return is not independently proved process closure. This layer
never releases resources, catches/retries a failure, or removes partial outputs.
"""
import os
from pathlib import Path
import stat
from corpus_workloads import plan
from workload_fixtures import create_corpus, edit
from batch_verify import verify, verify_expected


def sample(corpus, left, right, *, invoke, record):
    expected = plan(corpus.workload, count=len(corpus.files), file_bytes=corpus.file_bytes,
                    packet_bytes=corpus.packet_bytes)
    if corpus != expected or not callable(invoke) or not callable(record):
        raise ValueError('exact unshrunk corpus and owned callbacks required')
    roots = [Path(left), Path(right)]
    identities = []
    for root in roots:
        value = os.lstat(root)
        if not (root.is_absolute() and stat.S_ISDIR(value.st_mode)
                and stat.S_IMODE(value.st_mode) == 0o700 and value.st_uid == os.getuid()
                and not os.listdir(root)):
            raise ValueError('fresh empty private replicas required')
        identities.append((value.st_dev, value.st_ino))
    if identities[0] == identities[1]: raise ValueError('distinct replica roots required')
    metadata = {}
    def fence():
        for root, identity in zip(roots, identities):
            value = os.lstat(root)
            if not (stat.S_ISDIR(value.st_mode) and stat.S_IMODE(value.st_mode) == 0o700
                    and value.st_uid == os.getuid() and (value.st_dev, value.st_ino) == identity):
                raise ValueError('replica root replaced')
    def create(file):
        fence()
        path = roots[0] / file.relative_path
        if not path.parent.exists(): path.parent.mkdir(mode=0o700)
        metadata[file.relative_path] = create_corpus(path, corpus.file_bytes,
                                                   corpus.packet_bytes, file.seed_index)
    record(dict(stage='seed-intent', planned_files=corpus.before_files))
    for file in corpus.files:
        if file.before_present: create(file)
    seed = [dict(path=path, sha256=value['before_sha256'], bytes=value['size_bytes'])
            for path, value in metadata.items()]
    record(dict(stage='seed-inventory', files=seed))
    verify_expected(roots[0], seed); verify_expected(roots[1], [])
    fence(); invoke('seed')
    verify_expected(roots[0], seed); verify_expected(roots[1], seed)
    record(dict(stage='seed-verified', files=len(seed)))
    rows = []
    for file in corpus.files:
        if not file.before_present: create(file)
        value = metadata[file.relative_path]
        before = value['before_sha256'] if file.before_present else None
        target = edit(roots[0] / file.relative_path, value, file.edit) if file.before_present else value['before_sha256']
        rows.append(dict(path=file.relative_path, before_present=file.before_present,
                         before_sha256=before, target_sha256=target, target_bytes=corpus.file_bytes,
                         expected_class='new-file' if not file.before_present else
                         'semantic-update' if file.semantic_update_expected else 'ordinary-fallback'))
    record(dict(stage='update-inventory', files=rows))
    verify(roots[0], rows, phase='target'); verify_expected(roots[1], seed)
    fence(); invoke('update')
    verify(roots[0], rows, phase='target')
    updated = verify(roots[1], rows, phase='target')
    record(dict(stage='update-verified', observations=updated))
    fence(); invoke('noop')
    verify(roots[0], rows, phase='target')
    final = verify(roots[1], rows, phase='target')
    if final != updated: raise ValueError('no-op changed receiver file identity or bytes')
    fence(); record(dict(stage='noop-verified', observations=final))
    return dict(files=len(rows), verified_phases=3, process_audit_required=True,
                resource_release_authorized=False, qualification='filesystem phase composition only')
