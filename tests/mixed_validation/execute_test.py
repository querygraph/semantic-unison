"""Inert worker-entry and original metadata controls; zero native helpers."""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import execute as entry
from plan_test import fixture
from shared_cpu_pool import UnresolvedOwnership


class Entry(unittest.TestCase):
    def test_document_hash_duplicate_key_and_symlink(self):
        with tempfile.TemporaryDirectory(prefix='unison-mixed-document-') as directory:
            p=Path(directory)/'plan.json';p.write_text('{"value":1}')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(entry.document(p,digest),{'value':1})
            with self.assertRaises(ValueError):entry.document(p,'0'*64)
            p.write_text('{"value":1,"value":2}')
            with self.assertRaises(ValueError):entry.document(p)
            link=Path(directory)/'link';link.symlink_to(p)
            with self.assertRaises(OSError):entry.document(link)

    def run_worker(self,guard_failure=None):
        p=fixture();args=SimpleNamespace(workspace=p['workspace'],plan='/prepared/plan.json',plan_sha256='a'*64)
        calls=[];prepared=[];verified=[];writes=[]
        def kernel(plan,**callbacks):
            for index,command in enumerate(entry.commands(plan)):
                callbacks['check_sources']();callbacks['prepare'](index,command)
                callbacks['invoke'](index,command,callbacks['deadline'])
                callbacks['verify_input'](index,command)
            callbacks['persist']({'inert':True})
        with patch.object(entry,'document',return_value={'actual':'start'}),\
             patch.object(entry,'bind',side_effect=guard_failure or (lambda *a,**k:dict(inherited_fds=tuple(range(100,109))))),\
             patch.object(entry,'verified_hash'),patch.object(entry,'verify_build'),patch.object(entry,'verify_metadata'),patch.object(entry,'verify_sources'),\
             patch.object(entry,'prepare_input',side_effect=lambda p,i:prepared.append(i) or dict(index=i)),\
             patch.object(entry,'verify_input',side_effect=lambda p,i,r:verified.append((i,r))),\
             patch.object(entry,'invoke',side_effect=lambda command,env,end,**kw:calls.append((command,env,kw)) or {}),\
             patch.object(entry,'save',side_effect=lambda *a:writes.append(a)),\
             patch.object(entry,'execute_plan',side_effect=kernel):
            value=entry.worker(args,p)
        return value,calls,prepared,verified,writes

    def test_inherited_fds_private_state_and_callbacks_bound(self):
        code,calls,prepared,verified,writes=self.run_worker()
        self.assertEqual(code,0);self.assertEqual(prepared,[0,1])
        self.assertEqual(verified,[(0,{'index':0}),(1,{'index':1})])
        for index,(command,env,kw) in enumerate(calls):
            self.assertEqual(kw['pass_fds'],tuple(range(100,109)))
            self.assertEqual(env['UNISON'],fixture()['workspace']+'/'+('stock' if index==0 else 'ox')+'/state')
            self.assertNotIn('HOME',env)
        self.assertEqual(len(writes),1)

    def test_guard_refusal_and_uncertainty_do_not_prepare_or_invoke(self):
        for error in (ValueError('guard refused'),UnresolvedOwnership('FD unknown')):
            with patch.object(entry,'prepare_input') as prepare,patch.object(entry,'invoke') as invoke:
                with self.assertRaises(type(error)):self.run_worker(guard_failure=error)
                prepare.assert_not_called();invoke.assert_not_called()


if __name__=='__main__':unittest.main()
