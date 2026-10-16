#!/usr/bin/env python3
"""Exercise Unison's commit gate using a locally qualified real Adobe SDK driver."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--unison", type=Path, required=True)
parser.add_argument("--sdk-build", type=Path, required=True)
args = parser.parse_args()
binary = str(args.unison.resolve())
sdk = args.sdk_build.resolve()
manifest = json.loads((sdk / "build-manifest.json").read_text())
driver = Path(manifest["executable"])
assert hashlib.sha256(driver.read_bytes()).hexdigest() == manifest["executable_sha256"]
fixtures = sdk / "fixtures"
with tempfile.TemporaryDirectory(prefix="unison-adobe-sync-") as tmp:
    root = Path(tmp)
    left, right, state, receiver_state = (root / name for name in
                                        ("left", "right", "state", "receiver-state"))
    for directory in (left, right, state, receiver_state):
        directory.mkdir()
    (receiver_state / "endpoint.prf").write_text(
        f"adobevalidator = {driver}\n"
        f"adobevalidatorhash = {manifest['executable_sha256']}\n"
        f"adobevalidatorbuild = {manifest['build_id']}\n"
        "adobevalidatorthreads = 1\n")
    loopback = root / "loopback.py"
    loopback.write_text("#!/usr/bin/python3\nimport os,sys\n"
                        "os.environ['UNISON']=" + repr(str(receiver_state)) + "\n"
                        "a=sys.argv[1:]\ni=a.index(" + repr(binary) + ")\nos.execv(a[i],a[i:])\n")
    loopback.chmod(0o700)
    command = [binary, str(left), "ssh://localhost/" + str(right), "-sshcmd", str(loopback),
               "-servercmd", binary, "-batch", "-auto", "-fastcheck", "false", "-semanticdng",
               "-debug", "semantic", "-adobevalidator", str(driver),
               "-adobevalidatorhash", manifest["executable_sha256"],
               "-adobevalidatorbuild", manifest["build_id"]]
    env = dict(os.environ, UNISON=str(state))
    def sync(policy="require", success=True):
        child = subprocess.run(command + ["-adobevalidate", policy], env=env,
                               capture_output=True, text=True, timeout=120)
        log = child.stdout + child.stderr
        if (child.returncode == 0) != success:
            raise AssertionError(log)
        return log
    original = (fixtures / "valid-xmp.dng").read_bytes()
    (left / "image.dng").write_bytes(original)
    sync()
    assert (right / "image.dng").read_bytes() == original
    changed = original.replace(b'rdf:about=""', b"rdf:about=''")
    assert changed != original and len(changed) == len(original)
    (left / "image.dng").write_bytes(changed)
    log = sync()
    assert "Remote semantic clone wrote" in log, log
    assert (right / "image.dng").read_bytes() == changed
    for fixture in ("corrupt-raw", "corrupt-digest", "bad-xmp", "bad-structure"):
        (left / "image.dng").write_bytes((fixtures / (fixture + ".dng")).read_bytes())
        log = sync(success=False)
        assert "Adobe DNG validation rejected" in log, log
        assert (right / "image.dng").read_bytes() == changed
    (left / "image.dng").write_bytes(changed)
    sync()
    (left / "album").mkdir()
    for i in range(36):
        (left / "album" / f"image-{i}.dng").write_bytes(original)
    sync()
    assert len(list((right / "album").glob("*.dng"))) == 36
    assert all(p.read_bytes() == original for p in (right / "album").glob("*.dng"))
    print("Actual Adobe SDK: new file, remote XMP patch, four rejected corruption controls, recovery, and 36-file staged directory passed.")
