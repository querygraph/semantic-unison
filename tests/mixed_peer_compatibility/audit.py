"""Pure attempted-prefix lifecycle audit; no wait, signal, IO or FD release."""
import json
from mixed_peer_compatibility.contract import CASES, STAGES, command


def require(value, message):
    if not value:
        raise ValueError(message)


def audit(result, artifacts, workspace, raw_proxies):
    entries = result['invocations']
    require(type(entries) is list and 0 < len(entries) <= 12
            and len(raw_proxies) == len(entries), 'nonempty exact attempted prefix required')
    rows = []
    for index, entry in enumerate(entries):
        case, phase = divmod(index, 3)
        current, orientation = CASES[case]
        stage = STAGES[phase]
        argv, flags = command(artifacts, workspace, case, stage)
        require(type(entry['index']) is int and entry['index'] == index
                and entry['state'] == 'OUTCOME' and entry['command'] == argv,
                'pending, reordered or substituted invocation')
        require(entry['identity'] == {'case':case,'label':current,
                'orientation':orientation,'stage':stage}, 'case identity differs')
        run = entry['outcome']
        require(run['command'] == argv and type(run['returncode']) is int
                and run['capture_truncated'] is False
                and run['supervisor_capture_truncated'] is False, 'call binding/capture missing')
        pids = []
        for name in ('client_cleanup','supervisor_cleanup'):
            owner = run[name]
            pid = owner['pid']
            require(type(pid) is int and pid > 0 and pid not in pids
                    and type(owner['returncode']) is int and owner['reaped'] is True
                    and owner['group_cleanup_before_leader_reap'] is True
                    and owner['other_group_members_absent_before_reap'] is True,
                    'client/supervisor group unsettled')
            pids.append(pid)
        require(run['client_cleanup']['returncode'] == run['returncode'], 'client wait mismatch')
        proxy = run['proxy']
        require(proxy == raw_proxies[index]
                and proxy['schema'] == 'unison-loopback-protocol-count/1', 'raw proxy differs')
        if proxy['server_cleanup'] is None:
            from invocation_journal import audit_no_server_creation
            audit_no_server_creation(run)
            rows.append({'index':index,'server_created':False})
            continue
        server = artifacts[current if orientation == 'old-client' else 'old-stock']
        native = proxy['server_cleanup']; pid = native['pid']
        base = [server,'-server']
        args = proxy['server_command']
        # Both upstream RPC startup dialects are explicit; arbitrary suffixes
        # or injected endpoint flags cannot become audited server commands.
        if args == base + ['__new-rpc-mode'] + flags:
            base += ['__new-rpc-mode']
        require(args == base + flags and type(pid) is int and pid > 0 and pid not in pids
                and native['reaped'] is True and type(native['returncode']) is int
                and proxy['server_pid'] == pid and proxy['server_returncode'] == native['returncode']
                and proxy['input_pump_joined'] is True
                and proxy['launcher_control_header_bytes_excluded'] == 4 + len(json.dumps(base).encode()),
                'server command/wait/pump proof missing')
        require(proxy['server_group_binding'] == dict(native_pid=pid,native_process_group=pids[1],
                supervisor_pid=pids[1],supervisor_process_group=pids[1],observed_before_native_reap=True),
                'server group binding differs')
        rows.append({'index':index,'server_created':True})
    return {'attempted_calls':len(rows),'rows':rows,'all_attempted_groups_settled':True,
            'functional_success_inferred':False,'aggregate_or_parent_terminal_inferred':False}
