"""Export either the working tree or one exact local Git commit for a build."""
import os
import re
import shutil
import subprocess
import tarfile


def populate(root, work, revision=None):
    if revision is None:
        paths = subprocess.check_output(
            ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root)
        for raw in paths.split(b'\0'):
            if raw:
                source, target = root / os.fsdecode(raw), work / os.fsdecode(raw)
                if source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
        return paths, {'kind': 'working-tree'}
    if re.fullmatch('[0-9a-f]{40}', revision) is None:
        raise ValueError('source revision must be an exact lowercase40-hex commit')
    commit = subprocess.check_output(
        ['git', 'rev-parse', '--verify', revision + '^{commit}'], cwd=root, text=True).strip()
    if commit != revision:
        raise ValueError('source revision did not resolve to the exact commit')
    paths = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', commit], cwd=root)
    if b'SOURCE.tar' in paths.split(b'\0'):
        raise ValueError('source tree collides with reserved archive path')
    archive = work / 'SOURCE.tar'
    subprocess.run(['git', 'archive', '--format=tar', '--output=' + str(archive), commit],
                   cwd=root, check=True)
    with tarfile.open(archive) as source:
        members = source.getmembers()
        if len(members) > 20000 or sum(m.size for m in members) > 256 * 1048576:
            raise ValueError('source archive exceeds declared member/byte budget')
        source.extractall(work, members=members, filter='data')
    return paths, {'kind': 'git-commit', 'commit': commit, 'archive': str(archive)}
