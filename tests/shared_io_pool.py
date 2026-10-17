"""Existing-only EX_GLOBAL backend for the jointly pinned single-barrier pool.

No topology/device lanes, provisioning, payload admission or dispatcher integration.
Unknown descriptor settlement retains ownership; no LOCK_UN or numeric-FD retry.
"""
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

from shared_cpu_pool import (Lease, UnresolvedOwnership, close_descriptors, require,
                             same_inode, unique_object)

CANONICAL_MANIFEST = '/Users/alexy/src/photo/preview-generator/SHARED-PHYSICAL-IO-POOL-v1.json'
CANONICAL_SHA256 = 'f7b553987b484ee706ced90f828fb143a3a87ce445653a2d2e5a6030cc590636'


class UnresolvedIOOwnership(UnresolvedOwnership):
    """All close uncertainties, with only pre-close identity observations.

    uncertain_fd is populated only for the unambiguous single-close case.
    uncertain_closes is authoritative for combined failures; never retry any
    recorded numeric descriptor or inspect it after an uncertain close.
    """
    def __init__(self, message, *, retained_fds=(), uncertain_closes=(),
                 original_failure=None, close_failure=None):
        self.uncertain_closes = tuple(uncertain_closes)
        self.uncertain_fds = tuple(item['fd'] for item in self.uncertain_closes)
        super().__init__(message, retained_fds=tuple(dict.fromkeys(retained_fds)),
                         uncertain_fd=self.uncertain_fds[0] if len(self.uncertain_fds) == 1 else None)
        self.original_failure = original_failure
        self.close_failure = close_failure


def descriptor_observation(fd, role):
    # Call BEFORE attempting close, never on a descriptor with uncertain close.
    try:
        s = os.fstat(fd)
        identity = {'device': s.st_dev, 'inode': s.st_ino, 'uid': s.st_uid,
                    'mode': s.st_mode, 'nlink': s.st_nlink}
        error = None
    except BaseException as failure:
        identity = None
        error = repr(failure)
    return {'fd': fd, 'role': role, 'observed_before_close': identity,
            'identity_observation_error': error}


def uncertainty_records(error, observations):
    if isinstance(error, UnresolvedIOOwnership):
        # A generic qualified closer may already carry the same pre-close FD.
        # Keep that observation as well as the outer owner's more precise role;
        # never inspect the numeric descriptor again after close uncertainty.
        return tuple(dict(observations[item['fd']], upstream_observation=item)
                     if item['fd'] in observations else item
                     for item in error.uncertain_closes)
    if isinstance(error, UnresolvedOwnership) and error.uncertain_fd is not None:
        fd = error.uncertain_fd
        return (observations.get(fd, {'fd': fd, 'role': 'upstream_descriptor',
                'observed_before_close': None,
                'identity_observation_error': 'upstream carrier supplied no pre-close identity'}),)
    return ()


def read_manifest(path, digest):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        first = os.fstat(fd)
        stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        require(stat.S_ISREG(first.st_mode) and first.st_nlink == 1
                and first.st_uid == os.getuid() and 0 < first.st_size <= 65536,
                'bounded owned IO manifest required')
        raw = bytearray()
        while len(raw) <= 65536:
            block = os.read(fd, min(8192, 65537 - len(raw)))
            if not block:
                break
            raw.extend(block)
        visible = os.lstat(path)
        require(stamp(first) == stamp(os.fstat(fd)) == stamp(visible)
                and stat.S_ISREG(visible.st_mode) and len(raw) == first.st_size,
                'IO manifest changed')
        require(hashlib.sha256(raw).hexdigest() == digest, 'IO manifest SHA differs')
        return json.loads(raw, object_pairs_hook=unique_object)
    finally:
        from private_camera_receiving.close import close_descriptors as qualified_close
        qualified_close([fd])


@dataclass(frozen=True)
class GlobalPool:
    path: str
    directory_identity: dict
    barrier_identity: dict
    storage_domain: str
    manifest_sha256: str

    @classmethod
    def read(cls, path, digest):
        value = read_manifest(path, digest)
        require(value['schema'] == 'firstpair-physical-io-pool/1'
                and value['state'] == 'PROVISIONED_SINGLE_BARRIER_NOT_RUNTIME_QUALIFIED'
                and value['permittedClaimMode'] == 'EXCLUSIVE_GLOBAL_BARRIER_ONLY_UNTIL_PINNED_SUCCESSOR'
                and value['physicalLanes'] == [] and value['topologyQualified'] is False,
                'only pinned unqualified single EX_GLOBAL barrier is supported')
        lifecycle = value['lifecycle']
        require(all(lifecycle[k] is True for k in ('openExistingOnly', 'nonblocking',
                'closeOnly', 'lockUnForbidden', 'partialBundleRollbackBeforeWait',
                'unknownSettlementRetainsOwner')) and lifecycle['recreateMissing'] is False,
                'IO lifecycle contract differs')
        directory = value['directoryIdentity']
        barrier = value['barrier']
        require(Path(value['namespace']).is_absolute()
                and barrier['name'] == 'all-devices.lock'
                and barrier['path'] == str(Path(value['namespace']) / barrier['name'])
                and isinstance(value['storageDomain'], str) and 0 < len(value['storageDomain']) <= 128,
                'canonical IO path/domain malformed')
        for item, mode in ((directory, 0o700), (barrier['identity'], 0o600)):
            require(all(type(item[k]) is int and item[k] >= 0
                        for k in ('device', 'inode', 'uid', 'mode', 'nlink'))
                    and item['device'] > 0 and item['inode'] > 0
                    and item['uid'] == os.getuid() and item['mode'] == mode,
                    'IO pinned identity/mode malformed')
        require(barrier['identity']['nlink'] == 1, 'single-link IO barrier required')
        return cls(value['namespace'], directory, barrier['identity'],
                   value['storageDomain'], digest)

    def _directory_bound(self, fd):
        held, visible = os.fstat(fd), os.lstat(self.path)
        item = self.directory_identity
        require(stat.S_ISDIR(held.st_mode) and stat.S_ISDIR(visible.st_mode)
                and held.st_uid == visible.st_uid == item['uid'] == os.getuid()
                and stat.S_IMODE(held.st_mode) == stat.S_IMODE(visible.st_mode) == item['mode']
                and (held.st_dev, held.st_ino) == (item['device'], item['inode'])
                and same_inode(held, visible), 'IO directory identity/type/owner/mode changed')

    def _barrier_bound(self, directory, fd):
        held = os.fstat(fd)
        visible = os.stat('all-devices.lock', dir_fd=directory, follow_symlinks=False)
        item = self.barrier_identity
        require(stat.S_ISREG(held.st_mode) and stat.S_ISREG(visible.st_mode)
                and held.st_uid == visible.st_uid == item['uid'] == os.getuid()
                and stat.S_IMODE(held.st_mode) == stat.S_IMODE(visible.st_mode) == item['mode']
                and held.st_nlink == visible.st_nlink == item['nlink'] == 1
                and held.st_size == visible.st_size == 0
                and (held.st_dev, held.st_ino) == (item['device'], item['inode'])
                and same_inode(held, visible), 'IO barrier identity/type/owner/mode/size/link changed')

    def try_acquire(self):
        """EX_GLOBAL only; one NB attempt; known contention closes partial FDs."""
        directory = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                            | os.O_NONBLOCK | os.O_CLOEXEC)
        owned = []
        observations = {directory: descriptor_observation(directory, "io_directory")}
        lease = None
        failure = None
        try:
            self._directory_bound(directory)
            fd = os.open('all-devices.lock', os.O_RDWR | os.O_NOFOLLOW
                         | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
            try:
                owned.append(fd)
            except BaseException:
                close_descriptors([fd])
                raise
            observations[fd] = descriptor_observation(fd, "io_barrier")
            self._barrier_bound(directory, fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                if error.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
                close_descriptors(owned)
                owned.clear()
                return None
            self._directory_bound(directory)
            self._barrier_bound(directory, fd)
            # Reuse the proven close-only ownership carrier; indexes empty
            # because this is an IO barrier, not authority to CPU token indexes.
            lease = Lease(tuple(owned), (), os.getpid())
            owned.clear()
            return lease
        except UnresolvedOwnership as error:
            failure = error
            raise
        except BaseException as error:
            failure = error
            try:
                close_descriptors(owned)
            except UnresolvedOwnership as rollback:
                failure = rollback
                raise rollback from error
            owned.clear()
            raise
        finally:
            try:
                os.close(directory)
            except BaseException as error:
                prior = uncertainty_records(failure, observations)
                retained = failure.retained_fds if isinstance(failure, UnresolvedOwnership) else ()
                if lease is not None:
                    retained = tuple(retained) + lease.fds
                carrier = UnresolvedIOOwnership(
                    'IO directory close unknown; retain all descriptor ownership',
                    retained_fds=retained,
                    uncertain_closes=prior + (observations[directory],),
                    original_failure=failure, close_failure=error)
                raise carrier from (failure if failure is not None else error)


def close_unstarted(lease):
    """Known no-child/pre-dispatch rollback only, never a child settlement proof."""
    lease.close_after_verified_settlement(owner_reaped=True, groups_settled=True,
                                          external_children_settled=True)


def try_io_cpu_bundle(io_pool, cpu_pool, authorized_indexes):
    """Trusted caller must derive CPU authorization from its pinned policy.

    No native/UI acquisition implemented here. A consumer requiring that lease
    must attempt it NB AFTER this bundle and roll back all stages on contention.
    """
    io = io_pool.try_acquire()
    if io is None:
        return None
    try:
        cpu = cpu_pool.try_acquire(authorized_indexes)
    except UnresolvedOwnership as error:
        raise UnresolvedIOOwnership('CPU acquisition unknown; retain IO plus CPU ownership',
              retained_fds=io.fds + error.retained_fds,
              uncertain_closes=uncertainty_records(error, {}),
              original_failure=error) from error
    except BaseException:
        close_unstarted(io)
        raise
    if cpu is None:
        close_unstarted(io)
        return None
    return io, cpu
