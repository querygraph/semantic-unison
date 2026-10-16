#!/usr/bin/env python3
"""Precommit validation tests with a synthetic protocol driver, not Adobe SDK."""
import hashlib
import os
from pathlib import Path
import subprocess
import stat
import sys
import tempfile

DRIVER = '''#!/usr/bin/python3
import hashlib,os,pathlib,stat,sys,time
here=pathlib.Path(__file__)
mode=here.with_suffix('.mode').read_text().strip()
candidate=pathlib.Path(sys.argv[-1])
data=candidate.read_bytes()
with here.with_suffix('.calls').open('a') as log:
    log.write(str(candidate)+'\\n')
if mode=='mutate':
    candidate.write_bytes(data+b'changed by bad helper')
    sys.exit(1)
if mode=='inject':
    candidate.with_name('.unison.unexpected.unison.tmp').write_text('unexpected helper output')
if mode=='immutable-inject':
    extra=candidate.with_name('.unison.immutable.unison.tmp')
    extra.write_text('undeletable rejected helper output')
    os.chflags(extra,stat.UF_IMMUTABLE)
if mode=='replace-link':
    link=candidate.with_name('link')
    link.unlink()
    link.symlink_to('different-target')
if mode=='late-chmod' and candidate.name=='later.dng':
    time.sleep(0.5)
    candidate.with_name('earlier.dng').chmod(0o600)
if mode=='sibling-failure':
    if candidate.name=='earlier.dng':
        time.sleep(0.1)
        sys.exit(1)
    time.sleep(0.5)
    if not candidate.exists():
        here.with_suffix('.early-cleanup').write_text('stage removed with helper active')
if mode=='delay':
    def event(kind):
        fd=os.open(str(here.with_suffix('.events')),os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
        try:
            record=(kind+' '+str(os.getpid())+'\\n').encode()
            assert os.write(fd,record)==len(record)
        finally:
            os.close(fd)
    event('start')
    time.sleep(0.4)
    event('end')
print('UNISON-DNG-VALIDATION 1')
print('candidate-sha256 '+hashlib.sha256(data).hexdigest())
print('candidate-size '+str(len(data)))
print('driver-build sync-fixture-v1')
print('structure valid')
print('decode success')
print('raw-digest missing')
print('errors '+('1' if mode=='error' else '0'))
print('warnings 0')
print('END')
'''

def main():
    binary = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory(prefix="unison-validation-sync-") as tmp:
        root = Path(tmp)
        left, right, state = (root / n for n in ("left", "right", "state"))
        for p in (left, right, state):
            p.mkdir()
        driver = root / "driver.py"
        driver.write_text(DRIVER)
        driver.chmod(0o700)
        driver.with_suffix(".mode").write_text("pass")
        digest = hashlib.sha256(driver.read_bytes()).hexdigest()
        env = dict(os.environ, UNISON=str(state))
        command = [binary, str(left), str(right), "-batch", "-auto", "-fastcheck", "false",
                   "-clone", "off", "-semanticworkers", "4", "-adobevalidator", str(driver),
                   "-adobevalidatorhash", digest, "-adobevalidatorbuild", "sync-fixture-v1"]
        def sync(policy="require", success=True):
            result = subprocess.run(command + ["-adobevalidate", policy], env=env,
                                    capture_output=True, text=True, timeout=60)
            if (result.returncode == 0) != success:
                raise AssertionError(result.stdout + result.stderr)
            return result.stdout + result.stderr
        def calls():
            p = driver.with_suffix(".calls")
            return p.read_text().splitlines() if p.exists() else []
        original = b"synthetic DNG protocol fixture: no actual SDK assertion\n" * 128
        (left / "image.DNG").write_bytes(original)
        sync()
        assert len(calls()) == 1
        assert (right / "image.DNG").read_bytes() == original
        sync()
        assert len(calls()) == 1, "unchanged files are outside received scope"
        driver.with_suffix(".mode").write_text("error")
        changed = original + b"changed metadata"
        (left / "image.DNG").write_bytes(changed)
        sync(success=False)
        assert (right / "image.DNG").read_bytes() == original
        log = sync("warn")
        assert "validation warning" in log
        assert (right / "image.DNG").read_bytes() == changed
        driver.with_suffix(".mode").write_text("mutate")
        latest = changed + b"source update"
        (left / "image.DNG").write_bytes(latest)
        sync("warn", success=False)
        assert (right / "image.DNG").read_bytes() == changed, "warn published mutated stage"
        driver.with_suffix(".mode").write_text("pass")
        sync()
        assert (right / "image.DNG").read_bytes() == latest
        (left / "album").mkdir()
        (left / "album" / "nested.dng").write_bytes(original)
        (left / "album" / "notes.txt").write_text("not a DNG")
        before = len(calls())
        sync()
        assert len(calls()) == before + 1
        assert (right / "album" / "nested.dng").read_bytes() == original
        driver.with_suffix(".mode").write_text("delay")
        (left / "parallel").mkdir()
        for i in range(18):
            (left / "parallel" / f"image-{i}.dng").write_bytes(original)
        sync()
        # Each helper appends a complete record in one O_APPEND write. Preserve
        # that order: /usr/bin/python3 on macOS can be Python 3.9, whose
        # monotonic clock has a different origin in each process. Sorting those
        # timestamps falsely puts every start before every end.
        events = [line.split() for line in driver.with_suffix(".events").read_text().splitlines()]
        active, peak = set(), 0
        for kind, pid in events:
            if kind == "start":
                assert pid not in active
                active.add(pid)
                peak = max(peak, len(active))
            elif kind == "end":
                assert pid in active
                active.remove(pid)
            else:
                raise AssertionError(f"unknown helper event: {kind}")
        assert not active and len(events) == 36
        assert 2 <= peak <= 4, f"directory validators exceeded CPU budget or ran serially: {peak}"
        synced = list((right / "parallel").glob("*.dng"))
        assert len(synced) == 18 and all(p.read_bytes() == original for p in synced)
        for mode in ("inject", "replace-link", "late-chmod", "sibling-failure"):
            name = "tree-" + mode
            album = left / name
            if mode == "inject":
                # Replace an existing live file with a directory only after
                # validation succeeds; failed helpers must preserve the file.
                driver.with_suffix(".mode").write_text("pass")
                album.write_bytes(b"original live target")
                sync()
                album.unlink()
            album.mkdir()
            (album / "earlier.dng").write_bytes(original)
            (album / "earlier.dng").chmod(0o644)
            if mode == "replace-link":
                (album / "link").symlink_to("original-target")
            if mode in ("late-chmod", "sibling-failure"):
                (album / "later.dng").write_bytes(original)
            driver.with_suffix(".mode").write_text(mode)
            for policy in (("require",) if mode == "sibling-failure" else ("require", "warn")):
                log = sync(policy, success=False)
                if mode != "sibling-failure":
                    assert "candidate tree changed" in log, log
                if mode == "inject":
                    assert (right / name).read_bytes() == b"original live target"
                else:
                    assert not (right / name).exists(), "published helper-mutated tree"
                assert not driver.with_suffix('.early-cleanup').exists(), "cleanup preceded helper settlement"
            driver.with_suffix(".mode").write_text("pass")
            sync()
            assert (right / name / "earlier.dng").read_bytes() == original
            assert (right / name / "earlier.dng").stat().st_mode & 0o777 == 0o644
            assert not (right / name / ".unison.unexpected.unison.tmp").exists()
            if mode == "replace-link":
                assert os.readlink(right / name / "link") == "original-target"
        quarantine_test = "not available on this platform"
        if sys.platform == "darwin" and hasattr(os, "chflags") and hasattr(stat, "UF_IMMUTABLE"):
            name = "tree-quarantine-failure"
            album = left / name
            album.write_bytes(b"original quarantine target")
            sync()
            album.unlink()
            album.mkdir()
            (album / "image.dng").write_bytes(original)
            immutable_name = ".unison.immutable.unison.tmp"
            try:
                driver.with_suffix(".mode").write_text("immutable-inject")
                log = sync(success=False)
                assert "candidate tree changed" in log, log
                assert "could not discard private staging" in log, log
                assert (right / name).read_bytes() == b"original quarantine target"
                rejected = list(right.rglob(immutable_name))
                assert len(rejected) == 1, rejected
                original_stage = Path(calls()[-1]).parent
                # Unison may truncate the human-readable part of temporary
                # names; prove relocation by the original helper path instead.
                assert not original_stage.exists(), "rejected staging remained resumable"
                assert rejected[0].parent.resolve() != original_stage.resolve()
                assert rejected[0].lstat().st_flags & stat.UF_IMMUTABLE
                # Leave the failed quarantine intact during retry. A fresh
                # candidate must succeed without publishing that old child.
                driver.with_suffix(".mode").write_text("pass")
                sync()
                assert (right / name / "image.dng").read_bytes() == original
                assert not (right / name / immutable_name).exists()
                assert rejected[0].exists(), "fixture did not preserve cleanup failure through retry"
                quarantine_test = "passed"
            finally:
                # Only this test-created filename inside the disposable root
                # is touched, even if an assertion failed before discovery.
                for path in right.rglob(immutable_name):
                    info = path.lstat()
                    if stat.S_ISREG(info.st_mode):
                        os.chflags(path, info.st_flags & ~stat.UF_IMMUTABLE)
        print(f"Rejected-stage quarantine after cleanup failure: {quarantine_test}.")
        print(f"Validation precommit: new/update/fallback/tree, require/warn, mutation/retry, tree integrity and bounded parallel directory passed (peak {peak}/4; synthetic driver).")

if __name__ == "__main__":
    main()
