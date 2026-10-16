"""Original disposable descriptor faults; no canonical pool or payload."""
import os
import unittest
from unittest.mock import patch
import close


class CloseTests(unittest.TestCase):
    def test_ordinary_failure_becomes_unresolved(self):
        fd = os.open('/dev/null', os.O_RDONLY)
        original = ValueError('ordinary refusal')
        try:
            with patch.object(close.os, 'close', side_effect=OSError('uncertain')) as call:
                try:
                    try:
                        raise original
                    finally:
                        close.close_descriptors([fd])
                except close.UnresolvedIOOwnership as error:
                    self.assertIs(error.original_failure, original)
                    self.assertEqual(error.uncertain_fds, (fd,))
                    self.assertIsNotNone(error.uncertain_closes[0]['observed_before_close'])
                else:
                    self.fail('ordinary error escaped')
                self.assertEqual(call.call_count, 1)
        finally:
            os.close(fd)  # test fault never actually closed this fixture FD

    def test_nested_failures_preserve_both_and_pending(self):
        fds = [os.open('/dev/null', os.O_RDONLY) for _ in range(3)]
        try:
            with patch.object(close.os, 'close', side_effect=OSError('uncertain')) as call:
                try:
                    try:
                        close.close_descriptors([fds[0]])
                    finally:
                        close.close_descriptors(fds[1:])
                except close.UnresolvedIOOwnership as error:
                    self.assertEqual(error.uncertain_fds, (fds[0], fds[2]))
                    self.assertEqual(error.retained_fds, (fds[1],))
                    self.assertIsInstance(error.original_failure, close.UnresolvedIOOwnership)
                else:
                    self.fail('uncertainty lost')
                self.assertEqual(call.call_count, 2)
        finally:
            for fd in fds:
                os.close(fd)  # fault injection left all fixture FDs open

    def test_successful_outer_close_preserves_inner(self):
        a, b = [os.open('/dev/null', os.O_RDONLY) for _ in range(2)]
        original = close.UnresolvedIOOwnership('inner', uncertain_closes=[
            close.descriptor_observation(a, 'fixture')])
        try:
            try:
                try:
                    raise original
                finally:
                    close.close_descriptors([b])
            except close.UnresolvedIOOwnership as error:
                self.assertIs(error, original)
        finally:
            os.close(a)
