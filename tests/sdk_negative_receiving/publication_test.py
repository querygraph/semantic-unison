import copy,unittest
from sdk_merge_receiving.data import FIELDS
from sdk_negative_receiving.publication import verify


def original():
    epoch={name:1 for name in FIELDS};epoch.update(st_mode=0o100600,st_size=4096)
    return dict(sha256='a'*64,bytes=4096,identity=epoch)
CANDIDATE=dict(sha256='b'*64,bytes=4096)


class Publication(unittest.TestCase):
    def test_require_preserves_complete_observation(self):
        before=original();r=verify(policy='require',before=before,after=copy.deepcopy(before),candidate=CANDIDATE)
        self.assertTrue(r['destination_preserved']);self.assertFalse(r['resource_release_authorized'])
        self.assertTrue(r['fresh_payload_observations_required'])
    def test_each_epoch_hash_and_size_change_refuses_require(self):
        for field in FIELDS:
            before=original();after=copy.deepcopy(before);after['identity'][field]+=1
            with self.subTest(field=field),self.assertRaises(ValueError):verify(policy='require',before=before,after=after,candidate=CANDIDATE)
        before=original();after=copy.deepcopy(before);after['sha256']=CANDIDATE['sha256']
        with self.assertRaises(ValueError):verify(policy='require',before=before,after=after,candidate=CANDIDATE)
    def test_warn_requires_exact_candidate_not_just_changed_destination(self):
        before=original();after=copy.deepcopy(before);after['sha256']=CANDIDATE['sha256']
        self.assertTrue(verify(policy='warn',before=before,after=after,candidate=CANDIDATE)['exact_candidate_published'])
        for digest in (before['sha256'],'c'*64):
            after['sha256']=digest
            with self.assertRaises(ValueError):verify(policy='warn',before=before,after=after,candidate=CANDIDATE)
    def test_missing_epoch_bool_size_and_unchanged_candidate_refuse(self):
        for field in FIELDS:
            before=original();del before['identity'][field]
            with self.assertRaises(ValueError):verify(policy='require',before=before,after=before,candidate=CANDIDATE)
        before=original();before['bytes']=True
        with self.assertRaises(ValueError):verify(policy='require',before=before,after=before,candidate=CANDIDATE)
        before=original()
        with self.assertRaises(ValueError):verify(policy='require',before=before,after=before,candidate={k:before[k] for k in ('sha256','bytes')})

if __name__=='__main__':unittest.main()
