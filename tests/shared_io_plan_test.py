"""Finite pure claim cases; no live topology, IO pool, device or child access."""
import unittest
from shared_io_plan import Observation as O, Claim, plan, conflicts


def known(volume, members):
    observation = O(volume, 'epoch1', members)
    return plan('morrobay', [(observation, observation)], adapter_qualified=True)


class ClaimControls(unittest.TestCase):
    def test_apfs_siblings_conflict_despite_different_volume_bindings(self):
        self.assertTrue(conflicts(known('vol-a', ('disk0',)), known('vol-b', ('disk0',))))

    def test_known_independent_devices_can_overlap(self):
        self.assertFalse(conflicts(known('vol-a', ('disk0',)), known('vol-b', ('disk1',))))

    def test_composite_member_union_conflicts_on_any_member(self):
        self.assertTrue(conflicts(known('raid', ('disk1', 'disk0')), known('other', ('disk1',))))
        self.assertEqual(known('raid', ('disk1', 'disk0')).requests(),
                         (('barrier', 'shared'), ('device:disk0', 'exclusive'), ('device:disk1', 'exclusive')))

    def test_unknown_fallback_conflicts_with_all_known_devices(self):
        unknown = O('softraid', 'epoch1', None)
        claim = plan('morrobay', [(unknown, unknown)], adapter_qualified=True)
        self.assertEqual(claim.requests(), (('barrier', 'exclusive'),))
        for key in ('disk0', 'disk1', 'disk99'):
            self.assertTrue(conflicts(claim, known('known', (key,))))

    def test_unqualified_provider_cannot_claim_independence(self):
        observation = O('apfs', 'epoch1', ('disk0',))
        self.assertEqual(plan('morrobay', [(observation, observation)]).barrier_mode, 'exclusive')

    def test_changed_volume_or_topology_forces_global_barrier(self):
        first = O('a', 'epoch1', ('disk0',))
        for after in (O('b', 'epoch1', ('disk0',)), O('a', 'epoch2', ('disk0',)),
                      O('a', 'epoch1', ('disk1',))):
            self.assertEqual(plan('morrobay', [(first, after)], adapter_qualified=True).barrier_mode, 'exclusive')

    def test_two_volume_jobs_take_union_and_deduplicate(self):
        a, b = O('a', 'epoch1', ('disk0',)), O('b', 'epoch1', ('disk0', 'disk1'))
        self.assertEqual(plan('morrobay', [(a, a), (b, b)], adapter_qualified=True).physical_members,
                         ('disk0', 'disk1'))

    def test_bad_or_unbounded_claims_refused(self):
        for pairs in ([], [(O('a', 'epoch', ()),) * 2], [(O('a', 'epoch', ('../bad',)),) * 2],
                      [(O('a', 'epoch', ('Disk0',)),) * 2],
                      [(O('a', 'epoch', ('disk0',)),) * 2] * 17):
            with self.subTest(pairs=pairs), self.assertRaises(ValueError):
                plan('morrobay', pairs, adapter_qualified=True)

    def test_caller_cannot_split_one_domain_by_label(self):
        a = known('a', ('disk0',))
        other = O('b', 'epoch1', ('disk0',))
        b = plan('different-domain', [(other, other)], adapter_qualified=True)
        with self.assertRaises(ValueError):
            conflicts(a, b)

    def test_invalid_claim_cannot_bypass_barrier(self):
        with self.assertRaises(ValueError):
            Claim('morrobay', 'shared', (), 'unresolved_or_unqualified_topology')


if __name__ == '__main__':
    unittest.main()
