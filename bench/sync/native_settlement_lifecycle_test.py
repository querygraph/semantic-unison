#!/usr/bin/env python3
"""Finite original Python children only; invoke after resource coordination."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from ownership import NativeChild
from run import measure_invocation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/sdk_container_receive'))
from live_merge_aggregate import supervise


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def reaped(pid):
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return
    raise AssertionError('direct child remains waitable')


def worker(work):
    cases = []
    # Each child signals readiness only after installing any signal policy,
    # then closes stdout before its delayed exit. EOF alone is never a reap.
    for name, delay, code, ignore_term, reason, timeout, expected_signals in (
        ('normal-delayed', 0.6, 0, False, None, 2.0, []),
        ('legacy-grace-refusal', 3, 0, False, None, None, [signal.SIGTERM]),
        ('known-fault', 20, 0, False, 'original transport fault', 2.0, [signal.SIGTERM]),
        ('term-ignoring', 20, 0, True, None, 0.05, [signal.SIGTERM, signal.SIGKILL]),
        ('nonzero-native-exit', 0, 19, False, None, 2.0, []),
        ('expired-normal-budget', 20, 0, False, None, 0.0, [signal.SIGTERM]),
    ):
        source = ('import os,signal,time\n'
                  + ('signal.signal(signal.SIGTERM,signal.SIG_IGN)\n' if ignore_term else '')
                  + 'os.write(1,b"R");os.close(1)\n'
                  + f'time.sleep({delay});os._exit({code})\n')
        child = NativeChild([sys.executable, '-c', source], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        observed = []
        original_signal = child.signal

        def observe(number):
            observed.append(number)
            original_signal(number)

        child.signal = observe
        try:
            assert child.process.stdout.read() == b'R'
            result, _ = child.finish(cancel_reason=reason, normal_exit_timeout=timeout)
            assert result['reaped'] and observed == expected_signals, (name, result, observed)
            assert result['hard_kill_required'] == ignore_term
            assert result['returncode'] == (-int(expected_signals[-1]) if expected_signals else code)
            assert (result['cancel_reason'] is None) == (not expected_signals)
            reaped(child.pid)
            cases.append({'case': name, 'cleanup': result, 'signals': observed,
                          'independent_echild': True})
            write(work / (name + '-CLOSED.json'), cases[-1])
        finally:
            child.process.stdout.close()

    # Exercise the actual proxy caller and outer client/supervisor ownership.
    fake = work / 'delayed_echo.py'
    fake.write_text('#!' + sys.executable + '\nimport os,time\n'
                    'while True:\n'
                    ' data=os.read(0,65536)\n'
                    ' if not data:break\n'
                    ' os.write(1,data)\n'
                    'os.close(1);time.sleep(0.6)\n')
    fake.chmod(0o700)
    env = dict(os.environ, UNISON_SYNC_BENCH_BINARY=str(fake),
               UNISON_SYNC_BENCH_SOCKET=str(work / 'echo.sock'),
               UNISON_SYNC_BENCH_PROXY_RECEIPT=str(work / 'proxy.json'),
               UNISON_SYNC_BENCH_SERVER_FLAGS='[]')
    client = ('import json,os,socket,struct\n'
              's=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\n'
              's.connect(os.environ["UNISON_SYNC_BENCH_SOCKET"])\n'
              'h=json.dumps([os.environ["UNISON_SYNC_BENCH_BINARY"],"-server"]).encode()\n'
              's.sendall(struct.pack(">I",len(h))+h+b"hello");s.shutdown(socket.SHUT_WR)\n'
              'r=bytearray()\n'
              'while True:\n'
              ' b=s.recv(65536)\n'
              ' if not b:break\n'
              ' r.extend(b)\n'
              'assert r==b"hello"\n')
    result = measure_invocation([sys.executable, '-c', client], env, 8,
                                ROOT / 'bench/sync/proxy.py')
    for key in ('client_cleanup', 'supervisor_cleanup'):
        assert result[key]['reaped'] and result[key]['returncode'] == 0
        assert result[key]['group_cleanup_before_leader_reap']
        reaped(result[key]['pid'])
    proxy = result['proxy']
    assert proxy['server_cleanup']['reaped'] and proxy['server_returncode'] == 0
    assert proxy['server_cleanup']['normal_exit_timeout_seconds'] > 0.6
    assert proxy['server_cleanup']['cancel_reason'] is None
    assert proxy['input_pump_joined'] and not proxy['fault'] and not proxy['pump_errors']
    cases.append({'case': 'actual-proxy-delayed-echo', 'outcome': result})
    write(work / 'CASES-COMPLETE.json', {'cases': cases, 'complete': True,
          'scope': 'seven original Python lifecycle fixtures; no SDK/Unison/Photo/benchmark'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    args.workspace.mkdir(mode=0o700)
    closure = supervise(lambda _deadline: worker(args.workspace), args.workspace,
                        seconds=45, maximum_seconds=60, expected_helper_calls=0)
    assert closure['reaped'] and closure['returncode'] == 0
    assert closure['other_cli_group_members_absent_before_reap']
    reaped(closure['pid'])
    assert not list(args.workspace.glob('*UNRESOLVED*'))
    write(args.workspace / 'RESULT.json', {'complete': True, 'aggregate': closure,
          'cases': json.loads((args.workspace / 'CASES-COMPLETE.json').read_text()),
          'scope': 'finite fake-child lifecycle only; no timing or SDK qualification'})
    print('PASS seven finite lifecycle cases; aggregate and original children reaped', flush=True)


if __name__ == '__main__':
    main()
