"""Canonical manifest metadata plus injected fstat frames; no pool acquisition."""
import copy,os,stat,unittest
from types import SimpleNamespace
from shared_binding import inventory,verify,TARGET
class Binding(unittest.TestCase):
    def fixture(self):
        self.identities=inventory();self.command=['/inert','--worker']
        return dict(owner_pid=11,child_pid=22,target=TARGET,command=self.command,cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',
            inherited_resource_fds=[dict(fd=100+i,device=dev,inode=ino) for i,(dev,ino) in enumerate(self.identities)])
    def observe(self,fd):
        dev,ino=self.identities[fd-100]
        return SimpleNamespace(st_dev=dev,st_ino=ino,st_mode=stat.S_IFREG|0o600,st_uid=os.getuid(),st_nlink=1,st_size=0)
    def call(self,start,observe=None):return verify(start,self.command,parent_pid=11,worker_pid=22,observe=observe or self.observe)
    def test_exact_canonical_metadata_not_lock_or_release_authority(self):
        d=self.call(self.fixture());self.assertEqual(d['inherited_fds'],tuple(range(100,109)))
        self.assertTrue(d['canonical_metadata_bound']);self.assertFalse(d['lock_ownership_independently_proved']);self.assertFalse(d['resource_release_authorized'])
    def test_parent_target_command_or_grant_refused(self):
        for k,v in [('owner_pid',12),('child_pid',23),('target','old'),('command',['other']),('cpu_credits',True),('token_indexes',list(range(8,16))),('io_mode','none')]:
            s=self.fixture();s[k]=v
            with self.assertRaises(ValueError):self.call(s)
    def test_missing_duplicate_reordered_or_noncanonical_descriptors(self):
        for mode in ['missing','duplicate','reordered','wrong','bool','stdio']:
            s=self.fixture();rows=s['inherited_resource_fds']
            if mode=='missing':rows.pop()
            elif mode=='duplicate':rows[1]['fd']=rows[0]['fd']
            elif mode=='reordered':rows.reverse()
            elif mode=='wrong':rows[0]['inode']+=1
            elif mode=='bool':rows[0]['fd']=True
            else:rows[0]['fd']=0
            with self.assertRaises(ValueError):self.call(s)
    def test_fresh_description_mismatch_refused(self):
        s=self.fixture()
        for k,v in [('st_ino',0),('st_mode',stat.S_IFDIR|0o600),('st_uid',os.getuid()+1),('st_nlink',2),('st_size',1)]:
            def changed(fd):
                st=self.observe(fd);setattr(st,k,v);return st
            with self.assertRaises(ValueError):self.call(s,changed)
if __name__=='__main__':unittest.main()
