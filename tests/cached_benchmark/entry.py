"""Exact admitted shared8/EXglobal cached synthetic benchmark entry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cached_benchmark.contract import (ROOT, TARGET, PYTHON, LIMITS, checked_plan,
    document, read_bytes, worker_argv, benchmark_argv, benchmark_sources, audit)
from private_camera_receiving.close import close_descriptors
from shared_cpu_pool import UnresolvedOwnership, require
from shared_process_owner import retain_after_record
from sdk_host_matrix.shared_binding import verify


def write(path, value):
    raw = (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    require(len(raw) <= 1048576, 'bounded worker metadata required')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        at = 0
        while at < len(raw):
            n = os.write(fd, raw[at:])
            require(n > 0, 'worker metadata write made no progress')
            at += n
        os.fsync(fd)
    finally:
        close_descriptors([fd])


def worker(args, plan):
    require(sys.executable == PYTHON and args.workspace == plan['workspace'],
            'exact interpreter/workspace required')
    workspace = Path(args.workspace)
    deadline = time.monotonic()+3
    while True:
        try:
            start = document(workspace/'SHARED-START.json')
            break
        except FileNotFoundError:
            require(time.monotonic() < deadline, 'actual parent START absent')
            time.sleep(.005)
    argv = worker_argv(plan, args.plan, args.plan_sha256)
    binding = verify(start, argv, parent_pid=os.getppid(), worker_pid=os.getpid(), target=TARGET)
    write(workspace/'BENCHMARK-BINDING.json', dict(parent_pid=os.getppid(), worker_pid=os.getpid(),
          start_sha256=hashlib.sha256(read_bytes(workspace/'SHARED-START.json',1048576)).hexdigest(),
          inherited_resource_fds=start['inherited_resource_fds'], scope='metadata only, not a new grant'))
    for name in ('home','tmp'):
        (workspace/name).mkdir(mode=0o700)
    os.environ.clear()
    os.environ.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',
                      HOME=str(workspace/'home'),TMPDIR=str(workspace/'tmp'))
    sys.argv = benchmark_argv(plan, binding['inherited_fds'])
    runpy.run_path(str(ROOT/'bench/semantic/run.py'), run_name='__main__')
    proof = audit(document(workspace/'RESULT.json'), plan, start['inherited_resource_fds'])
    require(proof['functional_status'] == 'PASSED', 'incomplete benchmark')
    write(workspace/'WORKER-BENCHMARK-AUDIT.json', proof)
    return 0


def parent_audit(result, command, workspace, *, parent_pid, worker_pid):
    plan = checked_plan(command[4], command[6])
    start = document(workspace/'SHARED-START.json')
    verify(start, command, parent_pid=parent_pid, worker_pid=worker_pid, target=TARGET)
    proof = audit(result, plan, start['inherited_resource_fds'])
    if not result['complete']:
        failure = document(workspace/'WORKER-FAILURE.json')
        require(type(failure.get('error')) is str and bool(failure['error']),
                'original worker failure required')
        return dict(proof, original_failure=failure['error'],
                    external_sessions_expected=0, group_settlement_still_required=True)
    binding = document(workspace/'BENCHMARK-BINDING.json')
    require(binding['parent_pid'] == parent_pid and binding['worker_pid'] == worker_pid
            and binding['inherited_resource_fds'] == start['inherited_resource_fds'],
            'worker ownership observation differs')
    work = Path(result['retained_workspace'])
    require(work.parent == workspace and work.name.startswith('unison-sha-bench-')
            and work.resolve() == work, 'owned benchmark workspace required')
    require(set(result['compilers']) == {'stock', 'ox'}, 'exact measured compiler pair required')
    for build in plan['builds']:
        observed = result['compilers'][build['label']]
        expected = {p: h for p,h in plan['artifact_sha256'].items()
                    if Path(p).is_relative_to(Path(build['src']))}
        require(observed['linked_object_sha256'] == expected
                and observed['actual_production_build'] == build['src']
                and observed['executable_sha256'] == plan['artifact_sha256'][build['compiler']],
                'production object/compiler binding differs')
        binary = work/build['label']/'hash-bench'
        require(observed['benchmark_binary_path'] == str(binary)
                and hashlib.sha256(read_bytes(binary,256*1048576)).hexdigest()
                    == observed['benchmark_binary_sha256'], 'measured executable changed')
    return dict(proof, measured_executable_hashes_reverified=True,
                external_sessions_expected=0, group_settlement_still_required=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', action='store_true')
    for name in ('plan', 'plan-sha256'):
        parser.add_argument('--'+name, required=True)
    for name in ('workspace', 'admission', 'admission-sha256'):
        parser.add_argument('--'+name)
    args = parser.parse_args()
    plan = checked_plan(args.plan, args.plan_sha256)
    if not args.worker:
        require(args.admission and args.admission_sha256 and not args.workspace,
                'fresh exact admission required')
        workspace = Path(plan['workspace'])
        require(not os.path.lexists(workspace), 'workspace consumed; no replay')
        from shared_dispatch import checked_io_request, run
        command = worker_argv(plan, args.plan, args.plan_sha256)
        admission = dict(path=args.admission, sha256=args.admission_sha256)
        checked_io_request(admission, TARGET, command, workspace, 8)
        os.umask(0o077)
        workspace.mkdir(mode=0o700)
        return run(TARGET, command, workspace, 8, io_admission=admission)
    require(not args.admission and not args.admission_sha256 and args.workspace == plan['workspace'],
            'worker consumes exact actual parent binding only')
    try:
        return worker(args, plan)
    except UnresolvedOwnership:
        raise
    except BaseException as error:
        # Preserve partial samples; failure metadata never claims successful calls.
        write(Path(args.workspace)/'WORKER-FAILURE.json', dict(error=repr(error)))
        if not os.path.lexists(Path(args.workspace)/'RESULT.json'):
            write(Path(args.workspace)/'RESULT.json', dict(complete=False, samples=[],
                  source_sha256={k: plan['source_sha256'][k] for k in benchmark_sources()},
                  runner_sha256=plan['source_sha256']['bench/semantic/run.py'],
                  inherited_resource_fds=document(Path(args.workspace)/'SHARED-START.json')['inherited_resource_fds'],
                  parameters=dict(file_mib=32, jobs=6, workers=[1, 2, 4, 6],
                                  warmups_per_configuration=1, measured_repetitions=5)))
        raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except UnresolvedOwnership as error:
        retain_after_record(lambda: print(json.dumps(dict(state='BENCHMARK_OWNERSHIP_RETAINED',
            error=repr(error), retained_fds=list(error.retained_fds),
            uncertain_closes=list(getattr(error, 'uncertain_closes', ())))), flush=True))
