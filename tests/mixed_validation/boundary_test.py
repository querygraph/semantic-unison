"""Injected inherited-FD observations only; never acquires pool locks."""
import copy
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from boundary import bind,worker_argv
from mixed_validation.plan import TARGET
from plan_test import fixture


class Boundary(unittest.TestCase):
    def setUp(self):
        self.plan=fixture();self.options=dict(interpreter='/prepared/python',
            plan_path='/prepared/plan.json',plan_sha256='a'*64,parent_pid=11,worker_pid=22)
        self.argv=worker_argv(self.plan,**{k:v for k,v in self.options.items() if k not in ('parent_pid','worker_pid')})
        self.ids=tuple((1,1000+i) for i in range(9))
        self.start=dict(owner_pid=11,child_pid=22,target=TARGET,command=self.argv,
            cpu_credits=8,token_indexes=list(range(8)),io_mode='EX_GLOBAL',
            inherited_resource_fds=[dict(fd=100+i,device=d,inode=n) for i,(d,n) in enumerate(self.ids)])
    def observe(self,fd):
        dev,ino=self.ids[fd-100]
        return SimpleNamespace(st_dev=dev,st_ino=ino,st_mode=0o100600,
                               st_uid=os.getuid(),st_nlink=1,st_size=0)
    def call(self,start=None,argv=None):
        with patch('shared_binding.inventory',return_value=self.ids):
            return bind(self.plan,self.start if start is None else start,
                        self.argv if argv is None else argv,observe=self.observe,**self.options)
    def test_exact_launch_and_nine_inherited_identities(self):
        p=self.call();self.assertEqual(p['inherited_fds'],tuple(range(100,109)))
        self.assertTrue(p['canonical_metadata_bound'])
        self.assertFalse(p['lock_ownership_independently_proved'])
        self.assertFalse(p['resource_release_authorized'])
    def test_launch_changes_refused_even_if_parent_record_agrees(self):
        for index in (0,1,2,4,6,8):
            argv=list(self.argv);argv[index]+='changed'
            start=copy.deepcopy(self.start);start['command']=argv
            with self.subTest(index=index),self.assertRaises(ValueError):self.call(start,argv)
    def test_grant_target_and_parent_mismatch(self):
        for key,value in [('target','old'),('owner_pid',12),('child_pid',23),
                          ('cpu_credits',18),('token_indexes',[False,1,2,3,4,5,6,7]),('io_mode','none')]:
            start=copy.deepcopy(self.start);start[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.call(start)
    def test_missing_or_alias_descriptor_refuses(self):
        for mode in ('missing','alias','identity'):
            start=copy.deepcopy(self.start);rows=start['inherited_resource_fds']
            if mode=='missing':rows.pop()
            elif mode=='alias':rows[1]['fd']=rows[0]['fd']
            else:rows[0]['inode']+=1
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.call(start)


if __name__=='__main__':unittest.main()
