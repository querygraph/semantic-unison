"""Source successor: inode-bound cooperative tokens; qualification pending.

No pool or token file is created, rewritten, or explicitly LOCK_UN'd. Each
attempt opens fresh descriptions; inherited copies retain their locks until
closed. This module produces no process-settlement proof. The runner must
verify its actual owners/children/groups, and keep ownership on unknown results.
There is deliberately no context manager or destructor that unlocks on errors.
"""
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

DEFAULT_UNISON_TOKENS = tuple(range(8))
POLICY_SHA256 = '1dbe12eb97dfe885a0ec94057c476f4b825adc2d37085f0ecd48fbdf7b047352'


def authorized_unison_tokens(raw):
    """Derive the standing grant from the exact policy, never caller indexes."""
    require(hashlib.sha256(raw).hexdigest() == POLICY_SHA256, 'standing policy pin differs')
    policy = json.loads(raw, object_pairs_hook=unique_object)
    require(policy['version'] == 3
            and policy['defaultShared']['unison']['cpuCredits'] == 8
            and policy['locking']['defaultUnisonTokenIndexes'] == list(DEFAULT_UNISON_TOKENS),
            'standing Unison grant differs')
    return DEFAULT_UNISON_TOKENS


class UnresolvedOwnership(RuntimeError):
    def __init__(self, message, *, retained_fds=(), uncertain_fd=None):
        super().__init__(message)
        self.retained_fds = tuple(retained_fds)
        self.uncertain_fd = uncertain_fd


def require(value, message):
    if not value:
        raise ValueError(message)


def same_inode(a, b):
    return a.st_dev == b.st_dev and a.st_ino == b.st_ino


def close_descriptors(fds):
    # On a failed close, do not retry that numeric fd or start another attempt.
    # Preserve all not-yet-closed descriptions for the retaining coordinator.
    pending = list(fds)
    while pending:
        fd = pending.pop()
        try:
            os.close(fd)
        except BaseException as error:
            raise UnresolvedOwnership('token close outcome unknown; retain owner',
                                      retained_fds=pending, uncertain_fd=fd) from error


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate manifest key')
        result[key] = value
    return result


@dataclass(frozen=True)
class Pool:
    path: str
    device: int
    inode: int
    token_identities: tuple
    manifest_sha256: str

    @classmethod
    def read(cls, manifest, expected_sha256):
        """Read only a trusted pinned regular manifest; do not touch the pool."""
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        fd = os.open(manifest, flags)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                    and before.st_uid == os.getuid() and 0 < before.st_size <= 65536,
                    'manifest type/owner/link/size differs')
            raw = bytearray()
            while len(raw) <= 65536:
                block = os.read(fd, min(8192, 65537 - len(raw)))
                if not block:
                    break
                raw.extend(block)
            after = os.fstat(fd)
            visible = os.stat(manifest, follow_symlinks=False)
            stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(stamp(before) == stamp(after) == stamp(visible)
                    and stat.S_ISREG(visible.st_mode) and len(raw) == before.st_size,
                    'manifest changed while reading')
            require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'manifest pin differs')
        finally:
            os.close(fd)
        value = json.loads(raw, object_pairs_hook=unique_object)
        require(value['state'] == 'ROOT_SHARED_NATIVE_AND_STAGE_CPU_POOL_V1', 'pool schema differs')
        path = value['path']
        require(isinstance(path, str) and Path(path).is_absolute(), 'absolute pool path required')
        directory = value['directoryIdentity']
        identities = []
        require(len(value['credits']) == 18, 'exact existing18-token pool required')
        for index, item in enumerate(value['credits']):
            require(item['name'] == 'cpu-%02d.lock' % index, 'token order/name differs')
            require(all(type(item[key]) is int and item[key] > 0 for key in ('device', 'inode')),
                    'token identity malformed')
            identities.append((item['device'], item['inode']))
        require(len(set(identities)) == 18, 'aliased token identities')
        require(all(type(directory[key]) is int and directory[key] > 0 for key in ('device', 'inode')),
                'pool identity malformed')
        return cls(path, directory['device'], directory['inode'], tuple(identities), expected_sha256)

    def _directory_bound(self, fd):
        held, visible = os.fstat(fd), os.stat(self.path, follow_symlinks=False)
        require(stat.S_ISDIR(held.st_mode) and stat.S_ISDIR(visible.st_mode)
                and held.st_uid == visible.st_uid == os.getuid()
                and not (held.st_mode | visible.st_mode) & 0o077
                and (held.st_dev, held.st_ino) == (self.device, self.inode)
                and same_inode(held, visible), 'pool directory identity/owner/mode changed')

    def _token_bound(self, directory, index, fd):
        held = os.fstat(fd)
        visible = os.stat('cpu-%02d.lock' % index, dir_fd=directory, follow_symlinks=False)
        require(stat.S_ISREG(held.st_mode) and stat.S_ISREG(visible.st_mode)
                and held.st_uid == visible.st_uid == os.getuid()
                and held.st_nlink == visible.st_nlink == 1
                and not (held.st_mode | visible.st_mode) & 0o077 and same_inode(held, visible)
                and (held.st_dev, held.st_ino) == self.token_identities[index],
                'token identity/type/owner/mode changed')

    def try_acquire(self, indexes=DEFAULT_UNISON_TOKENS):
        """One nonblocking attempt. None means all partial FDs were closed.

        An explicit set is an accounting input, not authorization to borrow.
        The caller must bind it to its standing or separately scheduled grant.
        UnresolvedOwnership must retain the coordinator, never start a retry.
        """
        require(isinstance(indexes, (tuple, list)) and 0 < len(indexes) <= 18,
                'bounded explicit token sequence required')
        indexes = tuple(indexes)
        require(indexes and all(type(i) is int and 0 <= i < 18 for i in indexes)
                and indexes == tuple(sorted(set(indexes))), 'ascending unique explicit token set required')
        tokens = []
        lease = None
        failure = None
        directory = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                            | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            self._directory_bound(directory)
            for index in indexes:
                fd = os.open('cpu-%02d.lock' % index, os.O_RDWR | os.O_NOFOLLOW
                             | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
                try:
                    tokens.append(fd)
                except BaseException:
                    try:
                        os.close(fd)
                    except BaseException as close_error:
                        raise UnresolvedOwnership('unregistered token close unknown; retain owner',
                                                  retained_fds=tokens, uncertain_fd=fd) from close_error
                    raise
                self._token_bound(directory, index, fd)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as error:
                    if error.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                        raise
                    close_descriptors(tokens)
                    tokens.clear()
                    return None
            self._directory_bound(directory)
            for index, fd in zip(indexes, tokens):
                self._token_bound(directory, index, fd)
            lease = Lease(tuple(tokens), indexes, os.getpid())
            tokens.clear()
            return lease
        except UnresolvedOwnership as error:
            # A close already became indeterminate: never retry its fd number.
            failure = error
            raise
        except BaseException as error:
            failure = error
            try:
                close_descriptors(tokens)
            except UnresolvedOwnership as rollback_error:
                failure = rollback_error
                raise rollback_error from error
            tokens.clear()
            raise
        finally:
            try:
                os.close(directory)
            except BaseException as error:
                if failure is not None:
                    # Keep the first failure and its exact still-owned token
                    # set; do not substitute already-closed descriptor IDs.
                    failure.add_note('pool directory close outcome unknown; do not retry fd%d: %r'
                                     % (directory, error))
                else:
                    raise UnresolvedOwnership('pool directory close outcome unknown; retain owner',
                                              retained_fds=lease.fds if lease else (),
                                              uncertain_fd=directory) from error


@dataclass
class Lease:
    fds: tuple
    indexes: tuple
    owner_pid: int
    closed: bool = False

    def close_after_verified_settlement(self, *, owner_reaped, groups_settled, external_children_settled):
        """Consume a caller's current-run settlement attestation, not prove it.

        Pass these only after actual owned receipts are checked. Unknown keeps
        all descriptors open. Use fds with subprocess pass_fds for inheritance;
        do not LOCK_UN inherited descriptions or signal historical receipt PIDs.
        """
        if (os.getpid() != self.owner_pid or self.closed
                or owner_reaped is not True or groups_settled is not True
                or external_children_settled is not True):
            raise UnresolvedOwnership('actual owner/child/group settlement not established',
                                      retained_fds=self.fds)
        # Mark before attempting close: a close failure cannot be retried on
        # potentially reused descriptor numbers through this lease.
        self.closed = True
        close_descriptors(self.fds)
