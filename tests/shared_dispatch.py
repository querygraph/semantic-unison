"""Canonical token owner for fixed Adobe-free build/parser entry points.

Loopback sync has separately-sessioned server owners. Complete runs require
functional matrix proofs; failed runs require every attempted call's lifecycle
proof before the runner is reaped or tokens close. Neither infers the other.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from shared_cpu_pool import Pool, authorized_unison_tokens, require, UnresolvedOwnership
from shared_process_owner import settle, retain_after_record, require_ownership_support

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bench/sync'))
from ownership import OwnedGroup

POLICY = ROOT.parent / 'photo/preview-generator/SHARED-DEVELOPMENT-RESOURCE-POLICY-v3.json'
MANIFEST = ROOT.parent / 'photo/preview-generator/engine-v3-native-control/ROOT-CPU-POOL-v1.json'
MANIFEST_SHA = '4d19610edf6b400f99c00962cf52644ad93c924786b376faba91577808b693fd'
SDK_MATRIX_TARGET = 'shared-sdk-host-matrix'
SDK_MULTI_TARGET = 'sdk-multifile-receive'
SDK_COMPARE_TARGET = 'sdk-receiving-comparison'
SDK_SCAN_TARGET = 'all-scanned-sdk-validate'
MIXED_TARGET = 'mixed-sdk-metadata-hash'
SLICE_TARGET = 'private-maker-slice'
MODEL_TARGET = 'private-maker-model'
RECEIVING_TARGETS = ('camera-receive','camera-sdk-receive','synthetic-concurrent-receive')
TARGETS = {SLICE_TARGET,MODEL_TARGET, MIXED_TARGET, SDK_MATRIX_TARGET, SDK_MULTI_TARGET, SDK_COMPARE_TARGET, SDK_SCAN_TARGET, 'synthetic-concurrent-receive', 'camera-sdk-receive', 'camera-receive', 'stock-build', 'ox-build', 'stock-check', 'ox-check', 'stock-dune-check', 'ox-dune-check', 'read-parser', 'group-parser',
           'aggregate-preflight', 'host-interface', 'shared-entrypoints', 'shared-sync-controls',
           'sync-functional', 'inspect-stock', 'inspect-ox', 'inspect-file', 'inspector-reuse-controls',
           'sde-conformance', 'shared-io-controls', 'dng-private-framing', 'dng-private-diagnostic', 'private-dng-framing-input', 'private-dng-local-clone'}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def checked_io_request(request, target, argv, output, credits):
    """Read admission metadata only; this does not acquire IO/CPU locks."""
    from shared_io_pool import GlobalPool, read_manifest, CANONICAL_MANIFEST, CANONICAL_SHA256
    require(target in (SLICE_TARGET,MODEL_TARGET, MIXED_TARGET, SDK_MATRIX_TARGET, SDK_MULTI_TARGET, SDK_COMPARE_TARGET, SDK_SCAN_TARGET, 'synthetic-concurrent-receive', 'camera-sdk-receive', 'camera-receive', 'inspect-file', 'private-dng-local-clone', 'private-dng-framing-input', 'sync-functional'),
            'IO mode requires a complete job with qualified external-owner audit')
    require(isinstance(request, dict) and set(request) == {'path', 'sha256'},
            'explicit pinned IO admission required')
    value = read_manifest(request['path'], request['sha256'])
    require(value['state'] == 'ROOT_ADMITTED_ONE_SHARED_DISPATCH_IO_JOB'
            and value['target'] == target and value['command'] == argv
            and value['workspace'] == str(output) and value['cpu_credits'] == credits
            and value['io_manifest_sha256'] == CANONICAL_SHA256
            and value['start_deadline_unix'] > time.time(),
            'fresh exact shared-dispatch IO job admission required')
    source_paths = {Path(__file__), ROOT / 'tests/manual.py', ROOT / 'tests/shared_io_pool.py',
                    ROOT / 'tests/shared_cpu_pool.py', ROOT / 'tests/shared_process_owner.py',
                    ROOT / 'bench/sync/ownership.py', Path(argv[1])}
    if target == 'inspect-file':
        from inspector_io_contract import check
        require(credits == 8, 'inspector IO requires exact shared8 ownership')
        source_paths.add(ROOT / 'tests/inspector_io_contract.py')
        source_paths.update(check(value, argv, ROOT))
    if target == SDK_SCAN_TARGET:
        from all_scanned_sdk_boundary import checked_plan, current_sources
        from all_scanned_sdk_entry import child_argv
        require(credits == 8 and len(argv) == 9, 'exact all-scanned shared8 worker required')
        packet = checked_plan(argv[4], argv[6])
        require(argv == child_argv(argv[4], argv[6], output)
                and packet['workspace'] == str(output), 'all-scanned command/namespace differs')
        source_paths.update(Path(path) for path in current_sources())
    if target == MODEL_TARGET:
        from private_maker_identity_entry import checked_plan, sources, child_argv
        require(credits == 8 and len(argv) == 9, 'exact model shared8 worker required')
        packet = checked_plan(argv[4], argv[6])
        require(argv == child_argv(argv[4], argv[6], output)
                and packet['workspace'] == str(output), 'model exact worker namespace differs')
        source_paths.update(sources())
    if target == SLICE_TARGET:
        from private_maker_execute import checked_plan,sources
        from private_maker_plan import worker_argv
        require(credits==8 and len(argv)==9,'exact slice shared8 worker required')
        packet=checked_plan(argv[4],argv[6])
        require(argv==worker_argv(packet,interpreter=sys.executable,plan_path=argv[4],plan_sha256=argv[6])
                and packet['workspace']==str(output),'slice exact worker namespace differs')
        source_paths.update(sources())
    if target == MIXED_TARGET:
        from mixed_validation.execute import checked_plan
        from mixed_validation.boundary import worker_argv
        from mixed_validation.inventory import paths
        require(credits==8 and len(argv)==9,'exact mixed worker shared8 argv required')
        packet=checked_plan(argv[4],argv[6])
        require(argv==worker_argv(packet,interpreter=sys.executable,plan_path=argv[4],plan_sha256=argv[6])
                and packet['workspace']==str(output),'mixed worker launch/namespace differs')
        source_paths.update(paths())
    if target == SDK_MATRIX_TARGET:
        entry=ROOT/'tests/sdk_host_matrix/shared_execute.py'
        require(credits==8 and len(argv)==9 and argv[0]==sys.executable and argv[1]==str(entry)
            and argv[2:4]==['--worker','--plan'] and argv[5]=='--plan-sha256'
            and argv[7:]==['--workspace',str(output)],'exact shared SDK worker command required')
        sys.path.insert(0,str(entry.parent))
        import shared_execute
        packet=shared_execute.checked_plan(argv[4],argv[6])
        require(packet['workspace']==str(output),'shared SDK namespace differs')
        source_paths.update(Path(name) for name in shared_execute.sources())
    if target in (SDK_MULTI_TARGET,SDK_COMPARE_TARGET):
        entry=ROOT/('tests/sdk_multifile/entry.py' if target==SDK_MULTI_TARGET else 'tests/sdk_throughput/entry.py')
        require(credits==8 and len(argv)==9 and argv[0]==sys.executable and argv[1]==str(entry)
                and argv[2:4]==['--worker','--plan'] and argv[5]=='--plan-sha256'
                and argv[7:]==['--workspace',str(output)],'exact multi-file SDK worker argv required')
        if target==SDK_MULTI_TARGET:
            from sdk_multifile.entry import checked_plan,sources
        else:
            from sdk_throughput.entry import checked_plan,sources
        packet=checked_plan(argv[4],argv[6]);require(packet['workspace']==str(output),'multi-file namespace differs')
        source_paths.update(Path(name) for name in sources())
    if target in RECEIVING_TARGETS:
        sdk = target!='camera-receive'
        entry=ROOT/'tests'/('camera_sdk_concurrency/execute.py' if target=='synthetic-concurrent-receive' else 'camera_sdk_receiving/sdk_execute.py' if sdk else 'private_camera_receiving/execute.py')
        require(credits==8 and len(argv)==9 and argv[0]==sys.executable
                and argv[1]==str(entry)
                and argv[2:4]==['--worker','--plan'] and argv[5]=='--plan-sha256'
                and argv[7:]==['--workspace',str(output)],'exact camera worker command required')
        plan=read_manifest(argv[4],argv[6])
        require(plan['workspace']==str(output),'camera plan output differs')
        source_paths.update((ROOT/'tests/private_camera_receiving').glob('*.py'))
        if target=='synthetic-concurrent-receive':
            source_paths.update((ROOT/'tests/camera_sdk_concurrency').glob('*.py'))
        if sdk:
            source_paths.update((ROOT/'tests/camera_sdk_receiving').glob('*.py'))
            source_paths.add(ROOT/'tests/validation_process/records.py')
        source_paths.update((ROOT/'bench/sync').glob('*.py'))
    if target == 'sync-functional':
        from artifact_pins import parse as artifact_pin_set
        require(credits == 8 and '--shared-qualification' in argv and '--reference' not in argv,
                'IO sync requires the finite shared8 qualification matrix')
        for option in ('--expected-binary-sha256', '--expected-compiler-sha256'):
            positions = [i for i, word in enumerate(argv) if word == option]
            require(len(positions) == 2 and all(i+1 < len(argv) for i in positions),
                    'two expected stock/Ox artifact hashes required')
            require(set(artifact_pin_set([argv[i+1] for i in positions])) == {'stock','ox'},
                    'exact stock/Ox artifact hash labels required')
        source_paths.update((ROOT / 'bench/sync').glob('*.py'))
    if target == 'private-dng-framing-input':
        source_paths.update({ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
            ROOT / 'tools/private-dng-framing/inspect.ml', ROOT / 'tools/private-dng-framing/controls.py'})
    expected = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    require(value['execution_source_sha256'] == expected, 'exact IO execution source set changed')
    return GlobalPool.read(CANONICAL_MANIFEST, CANONICAL_SHA256), value['start_deadline_unix']


def run(target, argv, output, credits, *, io_admission=None):
    require(target in TARGETS, 'target has no shared owner scope')
    require(type(credits) is int and 1 <= credits <= 8, 'shared credit count differs')
    # Every supported target uses an explicit repository script. Reject e.g.
    # Python -m before acquiring descriptions, rather than failing while
    # constructing its source pin and retaining an idle no-child owner.
    require(isinstance(argv, list) and len(argv) >= 2 and type(argv[1]) is str,
            'shared target requires explicit script argv')
    script = Path(argv[1])
    require(script.is_absolute() and script.is_relative_to(ROOT) and script.is_file()
            and script.resolve() == script, 'shared target requires canonical repository script path')
    require(target not in ('private-dng-framing-input',SLICE_TARGET,MODEL_TARGET) or io_admission is not None,
            'framing input has no CPU-only runtime route')
    require(target not in (*RECEIVING_TARGETS,SLICE_TARGET,MODEL_TARGET,MIXED_TARGET,SDK_MATRIX_TARGET,SDK_MULTI_TARGET,SDK_COMPARE_TARGET,SDK_SCAN_TARGET) or (io_admission is not None and credits==8),
            'camera receiving requires exact shared8 IO admission')
    require(not any(flag in argv for flag in ('--property-removal-controls','--layout-only-controls')) or io_admission is not None,
            'property-removal matrix has no CPU-only runtime route')
    require_ownership_support()
    authorized = authorized_unison_tokens(POLICY.read_bytes())
    indexes = authorized[:credits]
    pool = Pool.read(MANIFEST, MANIFEST_SHA)
    io_lease = None
    try:
        io_pool, io_deadline = (checked_io_request(io_admission, target, argv, output, credits)
                                if io_admission is not None else (None, None))
    except UnresolvedOwnership as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {
            'owner_pid':os.getpid(),'stage':'metadata_preflight_before_acquisition',
            'error':repr(error),'retained_fds':list(error.retained_fds),
            'uncertain_fd':error.uncertain_fd,
            'uncertain_closes':list(getattr(error,'uncertain_closes',()))}))
    if io_pool is not None:
        write(output / 'SHARED-IO-ATTEMPT.json', {'admission': io_admission, 'target': target,
              'owner_pid': os.getpid(), 'command': argv})
    try:
        if io_pool is None:
            lease = pool.try_acquire(indexes)
        else:
            from shared_io_pool import try_io_cpu_bundle
            bundle = try_io_cpu_bundle(io_pool, pool, indexes)
            if bundle is None:
                lease = None
            else:
                io_lease, lease = bundle
    except UnresolvedOwnership as error:
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'stage': 'acquisition',
              'retained_fds': list(error.retained_fds), 'uncertain_fd': error.uncertain_fd,
              'uncertain_closes': list(getattr(error, 'uncertain_closes', ()))}))
    if lease is None:
        write(output / 'SHARED-NOT-STARTED.json', {'state': 'CONTENDED_PARTIAL_SET_CLOSED',
                                                'token_indexes': list(indexes)})
        return 2
    child = None
    resources_closed = False
    try:
        sources = [Path(__file__), ROOT / 'tests/manual.py', ROOT / 'tests/shared_cpu_pool.py',
                   ROOT / 'tests/shared_process_owner.py', ROOT / 'bench/sync/ownership.py',
                   Path(argv[1])]
        if target == 'inspect-file' and io_lease is not None:
            from inspector_io_contract import check
            from shared_io_pool import read_manifest
            sources.append(ROOT / 'tests/inspector_io_contract.py')
            sources.extend(check(read_manifest(io_admission['path'], io_admission['sha256']), argv, ROOT))
        if target == SDK_SCAN_TARGET:
            from all_scanned_sdk_boundary import current_sources
            sources.extend(Path(path) for path in current_sources())
        if target in ('inspect-stock', 'inspect-ox', 'inspect-file',
                      'inspector-reuse-controls', 'shared-entrypoints'):
            sources.append(ROOT / 'tools/semantic-inspect/run.py')
        if target in ('sync-functional', 'shared-sync-controls'):
            sources.extend((ROOT / 'bench/sync').glob('*.py'))
        if target == SDK_MATRIX_TARGET:
            sys.path.insert(0,str(ROOT/'tests/sdk_host_matrix'))
            import shared_execute
            sources.extend(Path(name) for name in shared_execute.sources())
        if target == MODEL_TARGET:
            from private_maker_identity_entry import sources as model_sources
            sources.extend(model_sources())
        if target == SLICE_TARGET:
            from private_maker_execute import sources as slice_sources
            sources.extend(slice_sources())
        if target == MIXED_TARGET:
            from mixed_validation.inventory import paths
            sources.extend(paths())
        if target in (SDK_MULTI_TARGET,SDK_COMPARE_TARGET):
            if target==SDK_MULTI_TARGET:
                from sdk_multifile.entry import sources as multi_sources
            else:
                from sdk_throughput.entry import sources as multi_sources
            sources.extend(Path(name) for name in multi_sources())
        if target in RECEIVING_TARGETS:
            if target=='synthetic-concurrent-receive':
                sources.extend((ROOT/'tests/camera_sdk_concurrency').glob('*.py'))
            if target!='camera-receive':
                sources.extend((ROOT/'tests/camera_sdk_receiving').glob('*.py'))
                sources.append(ROOT/'tests/validation_process/records.py')
            sources.extend((ROOT/'tests/private_camera_receiving').glob('*.py'))
            sources.extend((ROOT/'bench/sync').glob('*.py'))
        if io_lease is not None:
            sources.append(ROOT / 'tests/shared_io_pool.py')
        if target == 'dng-private-framing':
            sources.extend([ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
                            ROOT / 'tests/dng_private_data/test.ml'])
        if target == 'dng-private-diagnostic':
            sources.extend([ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
                            ROOT / 'tools/private-dng-framing/inspect.ml'])
        if target == 'private-dng-framing-input':
            sources.extend([ROOT / 'src/dngPrivateData.ml', ROOT / 'src/dngPrivateData.mli',
                ROOT / 'tools/private-dng-framing/inspect.ml', ROOT / 'tools/private-dng-framing/controls.py'])
        if target == 'shared-io-controls':
            sources.append(ROOT / 'tests/shared_io_plan.py')
        pins = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in set(sources)}
        if io_pool is not None:
            # Metadata-only final source/admission check immediately before
            # launch. A known refusal with no child is rollback, not unknown.
            try:
                checked_pool, checked_deadline = checked_io_request(io_admission, target, argv, output, credits)
                require(checked_pool == io_pool and checked_deadline == io_deadline
                        and time.time() < io_deadline, 'IO admission expired or changed before launch')
            except ValueError as refusal:
                from shared_io_pool import close_unstarted
                close_unstarted(lease)
                close_unstarted(io_lease)
                resources_closed = True
                write(output / 'SHARED-NOT-STARTED.json', {'state': 'PRELAUNCH_REFUSAL_KNOWN_CLOSED',
                                                        'error': str(refusal)})
                return 2
        inspector_binding = None
        if target == 'inspect-file' and io_lease is not None:
            from shared_io_pool import read_manifest
            inspector_binding = read_manifest(io_admission['path'], io_admission['sha256'])['inspector_contract']
        with (output / 'SHARED-STDOUT.txt').open('x') as stdout, (output / 'SHARED-STDERR.txt').open('x') as stderr:
            child = OwnedGroup(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=stdout,
                               stderr=stderr, pass_fds=lease.fds + (io_lease.fds if io_lease else ()))
            write(output / 'SHARED-START.json', {'owner_pid': os.getpid(), 'child_pid': child.pid,
                  'target': target, 'command': argv, 'token_indexes': list(indexes),
                  'io_mode': 'EX_GLOBAL' if io_lease is not None else 'NOT_ACQUIRED',
                  'io_admission': io_admission,
                  'cpu_credits': credits, 'unix': time.time(),
                  'inherited_resource_fds': [dict(fd=fd,device=os.fstat(fd).st_dev,inode=os.fstat(fd).st_ino)
                      for fd in lease.fds+(io_lease.fds if io_lease else ())] if target in (*RECEIVING_TARGETS,SLICE_TARGET,MODEL_TARGET,MIXED_TARGET,SDK_MATRIX_TARGET,SDK_MULTI_TARGET,SDK_COMPARE_TARGET,SDK_SCAN_TARGET) else [],
                  'sources': pins})
            seconds = 300 if target == 'sync-functional' or target.startswith('inspect-') else 600 if target.endswith(('-build', '-check')) else 60
            if target in ('sync-functional',*RECEIVING_TARGETS,SLICE_TARGET,MODEL_TARGET,MIXED_TARGET,SDK_MATRIX_TARGET,SDK_MULTI_TARGET,SDK_COMPARE_TARGET,SDK_SCAN_TARGET):
                # Separate server sessions retain their own coordinator. Do
                # not kill it on an outer deadline and discard live handles.
                if not child.await_terminal((60 if target==SLICE_TARGET else 300 if target==MIXED_TARGET else 600 if target in (*RECEIVING_TARGETS,SDK_MATRIX_TARGET,SDK_MULTI_TARGET,SDK_COMPARE_TARGET,SDK_SCAN_TARGET) else seconds) - 2):
                    raise RuntimeError('shared sync batch deadline; live coordinator retained')
                from shared_audit import audit_shared
                report_path = output / 'RESULT.json'
                info = report_path.lstat()
                import stat
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                        and info.st_uid == os.getuid() and 0 < info.st_size <= 16 * 1048576,
                        'bounded private shared result required')
                if target == SDK_SCAN_TARGET:
                    from all_scanned_sdk_boundary import read_document
                    from camera_sdk_concurrency.invocation import artifact_sha
                    result = read_document(report_path, artifact_sha(report_path), limit=1048576)
                    raw = None
                elif target == MODEL_TARGET:
                    from private_maker_execute import document
                    result = document(report_path)
                    raw = None
                else:
                    raw = report_path.read_bytes()
                after = report_path.lstat()
                require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                        and (raw is None or len(raw) == info.st_size), 'shared result changed')
                if raw is not None:
                    result = json.loads(raw)
                require(type(result.get('complete')) is bool, 'typed completion state required')
                if target == MODEL_TARGET:
                    from private_maker_identity_entry import checked_plan, audit_worker
                    from private_maker_slice import stamp
                    plan = checked_plan(argv[4], argv[6])
                    external = audit_worker(result, plan, parent_pid=os.getpid(), worker_pid=child.pid)
                    require(stamp(os.lstat(plan['source']['path'])) == plan['source']['identity'],
                            'model source epoch changed before resource release')
                elif target == SLICE_TARGET:
                    from private_maker_execute import checked_plan
                    from private_maker_audit import audit_worker
                    plan=checked_plan(argv[4],argv[6])
                    external=audit_worker(result,plan['geometry'],parent_pid=os.getpid(),worker_pid=child.pid)
                    from private_maker_slice import stamp
                    require(stamp(os.lstat(plan['source']['path']))==plan['source']['identity'],
                            'slice source epoch changed before resource release')
                elif target == MIXED_TARGET:
                    from mixed_validation.execute import checked_plan
                    from mixed_validation.parent import audit as mixed_audit
                    plan=checked_plan(argv[4],argv[6])
                    external=mixed_audit(result,plan)
                elif target == SDK_MATRIX_TARGET:
                    from shared_io_pool import read_manifest
                    sys.path.insert(0,str(ROOT/'tests/sdk_host_matrix'))
                    from shared_parent_audit import audit as sdk_matrix_audit
                    plan=read_manifest(argv[4],argv[6])
                    external=sdk_matrix_audit(result,reference=plan['tools']['reference'],experimental=plan['tools']['experimental'],
                        fixtures=plan['fixtures'],memory_bytes=plan['host_memory_bytes'],
                        observation_contract=plan.get('process_observation'))
                    for fixture in plan['fixtures']:
                        observed=os.lstat(fixture['path'])
                        require(all(getattr(observed,k)==v for k,v in fixture['identity'].items()),'SDK fixture epoch changed before release')
                elif target == SDK_SCAN_TARGET:
                    from all_scanned_sdk_boundary import checked_plan
                    from all_scanned_sdk_entry import audit_result
                    plan = checked_plan(argv[4], argv[6])
                    external = audit_result(result, plan, output)
                elif target in (SDK_MULTI_TARGET,SDK_COMPARE_TARGET):
                    from shared_io_pool import read_manifest
                    from sdk_multifile.entry import artifact_sha
                    plan=read_manifest(argv[4],argv[6])
                    if target==SDK_MULTI_TARGET:
                        from sdk_multifile.parent import audit as multi_audit
                        directories=[output/label for label in ('stock','ox')]
                    else:
                        from sdk_throughput.audit import audit as multi_audit
                        from sdk_throughput.plan import comparison
                        directories=[Path(r['directory']) for r in comparison(plan['binaries'],plan['tool'],output)['rows']]
                    proxies=[]
                    for i,entry in enumerate(result.get('invocations',[])):
                        require(i<len(directories) and entry['identity']['label'] in ('stock','ox')
                                and entry['identity']['directory']==str(directories[i]),'bounded exact proxy namespace required')
                        path=directories[i]/'seed-proxy.json'
                        proxies.append(read_manifest(path,artifact_sha(path)))
                    external=multi_audit(result,plan,raw_proxy_receipts=proxies)
                    for item in plan['inputs']:
                        observed=os.lstat(item['path'])
                        require(all(getattr(observed,k)==v for k,v in item['identity'].items()),'multi-file borrowed input epoch changed')
                    if result['complete']:
                        for directory in directories:
                            for source in plan['sources']:
                                for side in ('left','right'):
                                    path=directory/side/source['candidate_id']
                                    require(path.lstat().st_size==source['bytes'] and artifact_sha(path)==source['sha256'],
                                            'multi-file input/received candidate bytes differ at parent')
                        external['receiving_bytes_reverified']=True
                elif target in RECEIVING_TARGETS:
                    import importlib.util
                    from shared_io_pool import read_manifest
                    audit_path=ROOT/('tests/camera_sdk_concurrency/result_audit.py' if target=='synthetic-concurrent-receive' else 'tests/camera_sdk_receiving/sdk_result_audit.py'
                                     if target=='camera-sdk-receive' else 'tests/private_camera_receiving/audit.py')
                    sys.path.insert(0,str(audit_path.parent))
                    spec=importlib.util.spec_from_file_location('camera_receiving_result_audit',audit_path)
                    camera_audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(camera_audit)
                    plan=read_manifest(argv[4],argv[6])
                    external=camera_audit.audit(result,plan,output)
                    # Fresh borrowed-input metadata fence, no payload/hash.
                    if target!='synthetic-concurrent-receive':
                        expected=plan['source']['identity'];observed=os.lstat(plan['source']['path'])
                        require(all(getattr(observed,k)==v for k,v in expected.items()),
                                'borrowed input changed before resource release')
                elif result['complete']:
                    external = audit_shared(result)
                else:
                    from invocation_journal import audit_attempted
                    require(type(result.get('failure')) is str and result['failure'],
                            'failed result must preserve original failure')
                    external = audit_attempted(result)
                    external['functional_result'] = 'FAILED'
                write(output / 'SHARED-SERVER-AUDIT.json', external)
                closure = settle(child, time.monotonic() + 2)
                if target == MIXED_TARGET:
                    from mixed_validation.parent import bind_exit
                    exit_proof=bind_exit(external,closure['returncode'])
                    write(output / 'SHARED-WORKER-EXIT-AUDIT.json',exit_proof)
                if target in (SLICE_TARGET,MODEL_TARGET,SDK_MATRIX_TARGET,SDK_MULTI_TARGET,SDK_COMPARE_TARGET,SDK_SCAN_TARGET):
                    require(not result['complete'] or closure['returncode']==0,'complete SDK matrix contradicts failed worker exit')
                require(result['complete'] or closure['returncode'] != 0,
                        'failed result contradicts successful coordinator exit')
            else:
                closure = settle(child, time.monotonic() + seconds)
        inspector_post = None
        if inspector_binding is not None:
            from inspector_io_contract import postcheck
            inspector_post = postcheck(inspector_binding)
        source_unchanged = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
                               for name, digest in pins.items())
        lease.close_after_verified_settlement(owner_reaped=closure['reaped'],
                    groups_settled=closure['other_group_members_absent_before_reap'],
                    external_children_settled=True)
        if io_lease is not None:
            io_lease.close_after_verified_settlement(owner_reaped=closure['reaped'],
                groups_settled=closure['other_group_members_absent_before_reap'],
                external_children_settled=True)
        resources_closed = True
        write(output / 'SHARED-CLOSED.json', {'child': closure, 'tokens_closed': True,
                                            'io_barrier_acquired_and_closed': io_lease is not None,
                                            'source_pins_unchanged': source_unchanged,
                                            'inspector_input_postcheck': inspector_post,
                                            'parent_terminal': 'collect separately from owning tool'})
        return 124 if closure['timed_out'] else 3 if (not source_unchanged or inspector_post is not None and not inspector_post['unchanged']) else closure['returncode']
    except BaseException as error:
        if resources_closed:
            # A reporting failure after known close is not live FD/process
            # uncertainty. Preserve the exception, without inventing a hold.
            raise
        retain_after_record(lambda: write(output / 'SHARED-OWNERSHIP-RETAINED.json', {'error': repr(error),
              'owner_pid': os.getpid(), 'child_pid': child.pid if child else None,
              'retained_io_fds': list(io_lease.fds) if io_lease is not None and not io_lease.closed else [],
              'retained_cpu_fds': list(lease.fds) if not lease.closed else [],
              'error_retained_fds': list(getattr(error, 'retained_fds', ())),
              'uncertain_fd': getattr(error, 'uncertain_fd', None),
              'uncertain_closes': list(getattr(error, 'uncertain_closes', ())) }))
