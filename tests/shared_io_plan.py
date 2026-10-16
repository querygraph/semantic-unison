"""Pure physical-IO claim planning; no topology discovery or lock acquisition.

Only a separately qualified local adapter may assert a complete physical member
set. st_dev, mount names and filesystem type alone cannot do so. A provider's
qualification is supplied by its trusted owner, not inferred by this module.
"""
from dataclasses import dataclass
import re

KEY = re.compile(r'[a-z0-9][a-z0-9._:-]{0,127}\Z')


@dataclass(frozen=True)
class Observation:
    volume_binding: str
    topology_binding: str
    physical_members: tuple | None


@dataclass(frozen=True)
class Claim:
    storage_domain: str
    barrier_mode: str
    physical_members: tuple
    reason: str

    def __post_init__(self):
        require(isinstance(self.storage_domain, str) and KEY.fullmatch(self.storage_domain), 'invalid claim domain')
        require(self.barrier_mode in ('shared', 'exclusive'), 'invalid barrier mode')
        require(type(self.physical_members) is tuple and len(self.physical_members) <= 64
                and all(isinstance(key, str) and KEY.fullmatch(key) for key in self.physical_members)
                and self.physical_members == tuple(sorted(set(self.physical_members))),
                'noncanonical physical resource set')
        require((self.barrier_mode == 'exclusive' and not self.physical_members
                 and self.reason == 'unresolved_or_unqualified_topology')
                or (self.barrier_mode == 'shared' and self.physical_members
                    and self.reason == 'complete_stable_qualified_member_sets'),
                'barrier/member/reason mismatch')

    def requests(self):
        return (('barrier', self.barrier_mode),) + tuple(
            ('device:' + member, 'exclusive') for member in self.physical_members)


def require(value, message):
    if not value:
        raise ValueError(message)


def plan(storage_domain, observations, *, adapter_qualified=False):
    require(isinstance(storage_domain, str) and KEY.fullmatch(storage_domain), 'canonical storage domain required')
    require(type(adapter_qualified) is bool, 'typed adapter qualification required')
    require(isinstance(observations, (tuple, list)) and 1 <= len(observations) <= 16,
            'one to16 bounded before/after observation pairs required')
    members = set()
    resolved = adapter_qualified
    for pair in observations:
        require(isinstance(pair, (tuple, list)) and len(pair) == 2, 'before/after pair required')
        before, after = pair
        require(type(before) is Observation and type(after) is Observation, 'typed observation required')
        for item in pair:
            require(isinstance(item.volume_binding, str) and KEY.fullmatch(item.volume_binding)
                    and isinstance(item.topology_binding, str) and KEY.fullmatch(item.topology_binding),
                    'bounded volume/topology binding required')
            if item.physical_members is not None:
                require(type(item.physical_members) is tuple and 1 <= len(item.physical_members) <= 32,
                        'bounded complete physical-member tuple required')
                require(all(isinstance(key, str) and KEY.fullmatch(key) for key in item.physical_members),
                        'invalid physical resource key')
        if before != after or before.physical_members is None:
            resolved = False
        if before.physical_members is not None:
            members.update(before.physical_members)
    require(len(members) <= 64, 'physical claim set limit')
    if not resolved:
        # This exclusive barrier conflicts with EVERY known-device job, which
        # must itself hold a shared description of the SAME barrier inode.
        return Claim(storage_domain, 'exclusive', (), 'unresolved_or_unqualified_topology')
    return Claim(storage_domain, 'shared', tuple(sorted(members)), 'complete_stable_qualified_member_sets')


def conflicts(left, right):
    require(type(left) is Claim and type(right) is Claim, 'typed claims required')
    require(left.storage_domain == right.storage_domain, 'different canonical storage domains cannot be compared')
    return (left.barrier_mode == 'exclusive' or right.barrier_mode == 'exclusive'
            or bool(set(left.physical_members) & set(right.physical_members)))
