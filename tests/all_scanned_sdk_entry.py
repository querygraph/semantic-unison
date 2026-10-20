"""One-use admitted all-scanned SDK entry; no CPU-only runtime route."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests/camera_sdk_concurrency')]
from all_scanned_sdk_boundary import checked_plan, current_sources, read_document, PYTHON
from camera_sdk_concurrency.invocation import artifact_sha
from camera_sdk_concurrency.persistence import save
from sdk_multifile.clone import stamp
from shared_cpu_pool import UnresolvedOwnership
from shared_process_owner import retain_after_record

TARGET = 'all-scanned-sdk-validate'


def require(value, message):
    if not value: raise ValueError(message)


def child_argv(path, digest, workspace):
    return [sys.executable, str(Path(__file__).resolve()), '--worker', '--plan', str(path),
            '--plan-sha256', digest, '--workspace', str(workspace)]


def worker_entry(args, contract):
    from sdk_host_matrix.shared_binding import verify
    from all_scanned_sdk_prepare import prepare
    from all_scanned_sdk_worker import execute
    root = Path(args.workspace)
    require(str(root) == contract['workspace'], 'worker namespace differs')
    deadline = time.monotonic() + 3
    while True:
        try:
            path = root / 'SHARED-START.json'
            start = read_document(path, artifact_sha(path))
            break
        except (OSError, ValueError):
            require(time.monotonic() < deadline, 'actual parent START absent')
            time.sleep(.005)
    verify(start, child_argv(args.plan, args.plan_sha256, root),
           parent_pid=os.getppid(), worker_pid=os.getpid(), target=TARGET)
    require(artifact_sha(PYTHON) == contract['interpreter']['sha256'], 'interpreter changed under IO')
    for item in [*contract['binaries'].values(), contract['tool']]:
        require(artifact_sha(item['path']) == item['sha256'], 'execution artifact changed under IO')
    source = contract['source']
    def check():
        require(current_sources() == contract['execution_source_sha256'], 'execution sources changed')
        require(stamp(os.lstat(source['path'])) == source['identity'], 'borrowed source epoch changed')
    return execute(contract, root, time.monotonic() + 570,
        prepare_sources=lambda directory, label: prepare(source['path'], source['identity'], source['sha256'], directory),
        check_sources=check, read_proxy=lambda path: read_document(path, artifact_sha(path)),
        persist=lambda value: save(root, value))


def audit_result(result, contract, workspace):
    from all_scanned_sdk_parent import audit_complete
    from all_scanned_sdk_prefix import audit_failed
    from all_scanned_sdk_verify import verify_roots
    root = Path(workspace); proxies = []
    require(root.is_absolute() and str(root) == contract['workspace'], 'parent audit namespace differs')
    entries = result.get('invocations')
    require(type(entries) is list and len(entries) <= 4, 'bounded attempted journal required')
    for index, entry in enumerate(entries):
        label, phase = ('stock', 'ox')[index // 2], ('baseline', 'validate')[index % 2]
        require(entry['identity']['label'] == label and entry['identity']['stage'] == phase,
                'proxy namespace derivation order differs')
        path = root / label / (phase + '-proxy.json')
        proxies.append(read_document(path, artifact_sha(path)))
    proof = (audit_complete if result['complete'] else audit_failed)(
        result, contract, raw_proxy_receipts=proxies)
    source = contract['source']
    require(stamp(os.lstat(source['path'])) == source['identity'], 'borrowed source epoch changed before release')
    if result['complete']:
        cases = result.get('cases')
        require(type(cases) is list and [r.get('label') for r in cases] == ['stock', 'ox'],
                'exact complete compiler preparation pair required')
        proof['fresh_root_verifications'] = [verify_roots(root / row['label'], row['preparation'], source=source)
                                             for row in cases]
        proof['source_bytes_reverified'] = True
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'plan-sha256'): parser.add_argument('--' + name, required=True)
    for name in ('workspace', 'admission', 'admission-sha256'): parser.add_argument('--' + name)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    contract = checked_plan(args.plan, args.plan_sha256)
    root = Path(contract['workspace'])
    if args.worker:
        try: worker_entry(args, contract); return 0
        except UnresolvedOwnership: raise
        except BaseException as error:
            if not (root / 'RESULT.json').exists():
                save(root, dict(schema='unison-all-scanned-sdk-worker/1', complete=False,
                    phase='PREPARING_NO_CALL', invocations=[], cases=[], failure=repr(error)))
            raise
    require(args.admission and args.admission_sha256 and not args.workspace,
            'fresh exact IO admission required')
    require(not root.exists() and not root.is_symlink(), 'workspace consumed; never replay')
    from shared_dispatch import checked_io_request, run
    command = child_argv(args.plan, args.plan_sha256, root)
    admission = dict(path=args.admission, sha256=args.admission_sha256)
    checked_io_request(admission, TARGET, command, root, 8)
    os.umask(0o077); root.mkdir(mode=0o700)
    return run(TARGET, command, root, 8, io_admission=admission)


if __name__ == '__main__':
    try: raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda: print(json.dumps(dict(state='ALL_SCANNED_SDK_OWNERSHIP_RETAINED',
            error=repr(error), retained_fds=list(getattr(error, 'retained_fds', ())),
            uncertain_closes=list(getattr(error, 'uncertain_closes', ())))), file=sys.stderr, flush=True))
