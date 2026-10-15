#!/usr/bin/env python3
"""Pure wait/signal policy controls; no subprocess, signal or sleep occurs."""
from types import SimpleNamespace
from unittest.mock import patch
import signal

from ownership import NativeChild


def check(outcomes, *, reason=None, normal=None, waits=(), signals=(), forced=False):
    child = NativeChild.__new__(NativeChild)
    child.process = SimpleNamespace(pid=42, returncode=None)
    child.status = child.usage = None
    observed_waits, observed_signals = [], []
    answers = iter(outcomes)

    def await_reap(timeout):
        observed_waits.append(timeout)
        value = next(answers)
        if value:
            child.status, child.usage, child.process.returncode = 0, 'usage', 0
        return value

    child.await_reap = await_reap
    child.signal = observed_signals.append
    with patch('ownership.os.wait4', return_value=(42, 9, 'forced-usage')) as wait4:
        with patch('ownership.time.monotonic', side_effect=[10.0, 10.25]):
            result, _ = child.finish(cancel_reason=reason, normal_exit_timeout=normal)
        assert wait4.call_count == int(forced)
        if forced:
            wait4.assert_called_once_with(42, 0)
    assert observed_waits == list(waits)
    assert observed_signals == list(signals)
    assert result['reaped'] and result['hard_kill_required'] == forced
    assert result['settlement_wall_seconds'] == 0.25
    assert result['normal_exit_timeout_seconds'] == (0.2 if normal is None else normal)
    if signals and reason is None:
        assert result['cancel_reason'] == 'native child did not settle after output EOF'
    else:
        assert result['cancel_reason'] == reason


check([True], waits=[0.2])                 # Legacy caller keeps its policy.
check([True], normal=2.0, waits=[2.0])     # Delayed normal exit needs no signal.
check([False, True], normal=2.0, waits=[2.0, 0.2], signals=[signal.SIGTERM])
check([False, False], normal=2.0, waits=[2.0, 0.2],
      signals=[signal.SIGTERM, signal.SIGKILL], forced=True)
check([True], reason='transport fault', normal=2.0, waits=[0.2], signals=[signal.SIGTERM])
check([True], normal=0.0, waits=[0.0])     # Expired protocol gets no new normal wait.
print('PASS six pure native-settlement policy cases; no child/reap/timing qualification')
