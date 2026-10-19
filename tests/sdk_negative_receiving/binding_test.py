"""Actual shared verifier with fabricated native observations; no real FD/grant."""
import os,unittest
from types import SimpleNamespace
from unittest.mock import patch
from sdk_host_matrix import shared_binding


class NegativeBinding(unittest.TestCase):
    def test_real_verifier_accepts_exact_new_target_with_eight_cpu_and_io(self):
        identities=[(1,800+i) for i in range(9)];command=['/qualified/python','/qualified/negative-worker']
        rows=[dict(fd=700+i,device=d,inode=n) for i,(d,n) in enumerate(identities)]
        start=dict(owner_pid=101,child_pid=102,target='current-sdk-negative-receiving',command=command,
            cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',inherited_resource_fds=rows)
        def observe(fd):
            d,n=identities[fd-700]
            return SimpleNamespace(st_dev=d,st_ino=n,st_mode=0o100600,st_uid=os.getuid(),st_nlink=1,st_size=0)
        with patch.object(shared_binding,'inventory',return_value=identities):
            value=shared_binding.verify(start,command,parent_pid=101,worker_pid=102,
                target='current-sdk-negative-receiving',observe=observe)
        self.assertEqual(value['inherited_fds'],tuple(range(700,709)))
        self.assertFalse(value['lock_ownership_independently_proved']);self.assertFalse(value['resource_release_authorized'])
    def test_new_target_cannot_borrow_eighteen_or_accept_unknown_target(self):
        for target,credits in (('current-sdk-negative-receiving',18),('unknown',8)):
            with self.assertRaises(ValueError):shared_binding.verify({},[],parent_pid=101,worker_pid=102,
                target=target,credits=credits,observe=lambda _:self.fail('should refuse before FD observation'))

if __name__=='__main__':unittest.main()
