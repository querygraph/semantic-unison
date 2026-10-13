#!/usr/bin/env python3
"""Actual receiving validation from format claims, with synthetic drivers only."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
from fixtures import container, different, fixtures, unrelated_tiff, unrelated_jpeg

dependency = ROOT / "tests/validation_paths/run.py"
spec = importlib.util.spec_from_file_location("validation_path_dependency", dependency)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

SOURCE_MODULES = ("formatRecognition", "dngRecognition", "candidateValidator",
                  "candidateValidators", "dngCandidateValidation", "candidateValidation",
                  "semanticWorkers", "semanticRuntime", "semanticAdmission",
                  "semanticFormats", "semanticFile", "helperSupervisor", "dngValidation")
SOURCES = tuple("src/" + name + suffix for name in SOURCE_MODULES for suffix in (".ml", ".mli"))
INPUTS = ("tests/validation_recognition/fixtures.py", "tests/validation_recognition/run.py",
          "tests/validation_recognition/genericValidator.ml", "tests/validation_recognition/README.md",
          "tests/validation_paths/run.py")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Session(base.Session):
    def __init__(self, root, binary, executions, *, remote=True):
        self.remote, self.executions = remote, executions
        super().__init__(root, binary)
        # Only the generated private helper is adapted: original DRIVER has a
        # shallow-directory destination oracle. Preserve full relative paths
        # for our recursive staged-directory case without changing its source.
        old = "    destination=destination/candidate.name\n    assert candidate!=destination and candidate.parent.parent==destination.parent.parent"
        new = ("    stage=candidate.parent\n"
               "    while stage.parent!=destination.parent:\n"
               "        assert stage!=stage.parent\n"
               "        stage=stage.parent\n"
               "    destination=destination/candidate.relative_to(stage)\n"
               "    assert candidate!=destination")
        require(base.DRIVER.count(old) == 1, "private directory driver anchor changed")
        driver = base.DRIVER.replace(old, new)
        for path in self.drivers.values():
            path.write_text(driver)
        self.server_settings(self.config("server"))
        self.control("image.dng")

    @property
    def receiver(self):
        return "server" if self.remote else "client"

    def receiving(self):
        return self.calls(self.receiver)

    def server_settings(self, config):
        config = dict(config)
        if base.ADMISSION_OPTIONS:
            config["semanticvolumejobs"] = base.ADMISSION_OPTIONS[-1]
        (self.server_state / "endpoint.prf").write_text(
            "".join(f"{key} = {value}\n" for key, value in config.items()))

    def control(self, name, *, client="pass", server="pass", directory=False):
        super().control(name, client=client, server=server)
        for endpoint in ("client", "server"):
            path = self.drivers[endpoint].with_suffix(".control.json")
            record = json.loads(path.read_text())
            if not self.remote and endpoint == "client":
                record["destination"] = str(self.right / name)
            record["directory"] = directory
            path.write_text(json.dumps(record))

    def command(self, *, policy="require", options=()):
        if self.remote:
            command = super().command(policy=policy, options=options)
        else:
            settings = [value for key, setting in self.config("client").items()
                        for value in ("-" + key, setting)]
            command = [self.binary, str(self.left), str(self.right), "-batch", "-auto",
                       "-fastcheck", "false", "-clone", "off", "-semanticworkers", "2",
                       "-maxthreads", "1", "-adobevalidate", policy,
                       "-debug", "copy", "-debug", "semantic"] + settings + base.ADMISSION_OPTIONS + list(options)
        # No transfer profile is selected by default. Per-case explicit true
        # options come after this override, allowing one ineligible fallback.
        at = command.index("-batch")
        command[at:at] = ["-semanticdng=false"]
        return command

    def raw_sync(self, *, policy="require", options=()):
        self.sequence += 1
        command = self.command(policy=policy, options=options)
        started = time.monotonic()
        result = subprocess.run(command, env=dict(os.environ, UNISON=str(self.client_state)),
                                capture_output=True, text=True, timeout=90)
        log = self.root / f"run-{self.sequence:02d}.log"
        log.write_text(result.stdout + result.stderr)
        self.executions.append({"argv": command, "cwd": os.getcwd(),
            "endpoint_state": str(self.client_state), "exit_code": result.returncode,
            "elapsed_seconds": time.monotonic() - started, "log": str(log),
            "log_sha256": sha_file(log)})
        return result.returncode, log.read_text()

    def sync(self, *, policy="require", options=(), success=True):
        status, log = self.raw_sync(policy=policy, options=options)
        require((status == 0) == success,
                self.root.name + ": unexpected receiving outcome\n" + log)
        return log


def verify(session, call, data, previous=None, endpoint=None):
    base.verify_call(call, data, previous=previous, endpoint=endpoint or session.receiver)


def rejected_then_retry(session, name, data, *, options=()):
    session.control(name, client="error", server="error")
    (session.left / name).write_bytes(data)
    status, log = session.raw_sync(options=options)
    calls = session.receiving()
    require(len(calls) == 1, "content-recognized .bin bypassed required receiving validator")
    verify(session, calls[0], data)
    require(status != 0 and "Adobe DNG validation rejected" in log, "require did not reject recognized receive")
    require(not (session.right / name).exists(), "recognized rejected new receive was published")
    require(not Path(calls[0]["candidate"]).exists(), "recognized rejected stage remained reusable")
    require((session.left / name).read_bytes() == data, "recognition changed source bytes")
    session.control(name)
    session.sync(options=options)
    require(len(session.receiving()) == 2, "recognized fresh retry omitted validation")
    verify(session, session.receiving()[-1], data)
    require((session.right / name).read_bytes() == data, "recognized retry committed different bytes")
    base.no_op(session, name, data)
    return {"receiving_calls": 2, "required_rejection_before_publication": True, "fresh_retry": True}


def updates(session):
    name, original = "update.bin", container(big=True, little=False, profile=True)
    session.control(name)
    (session.left / name).write_bytes(original)
    session.sync()
    incoming = different(original, "rejected-opaque-update")
    (session.left / name).write_bytes(incoming)
    session.control(name, client="error", server="error")
    session.sync(success=False)
    require(len(session.receiving()) == 2, "renamed update receiving gate absent")
    verify(session, session.receiving()[-1], incoming, original)
    require((session.right / name).read_bytes() == original, "rejected update replaced old live bytes")
    require(not Path(session.receiving()[-1]["candidate"]).exists(), "rejected update retained staging")
    session.control(name)
    session.sync()
    verify(session, session.receiving()[-1], incoming, original)
    require((session.right / name).read_bytes() == incoming, "update retry bytes differ")
    base.no_op(session, name, incoming)
    return {"calls": 3, "old_live_preserved_on_reject": True}


def unrelated(session):
    values = {"ordinary-tiff.bin": unrelated_tiff(), "ordinary.jpeg": unrelated_jpeg(),
              "jpeg-renamed.bin": unrelated_jpeg(),
              "literal.txt": b"DNGVersion 50706 II MM TIFF TOY0: not a format header"}
    for name, data in values.items():
        session.control(name, client="error", server="error")
        (session.left / name).write_bytes(data)
        session.sync()
        require(not session.calls("client") and not session.calls("server"), "unrelated file invoked DNG helper")
        require((session.right / name).read_bytes() == data, "unrelated receive changed bytes")
    return {"files": list(values), "helper_calls": 0}


def ineligible_update(session):
    name = "ineligible.bin"
    data = container(private=True) + bytes(range(256)) * 8192
    session.control(name)
    (session.left / name).write_bytes(data)
    options = ("-semanticdng=true", "-clone", "auto")
    session.sync(options=options)
    changed = bytearray(data)
    changed[515] ^= 1
    changed = bytes(changed)
    (session.left / name).write_bytes(changed)
    session.control(name, server="error")
    log = session.sync(options=options, success=False)
    require("Remote semantic fallback: no negotiated profile proves eligibility" in log,
            "test did not exercise semantic inspection decline")
    require(len(session.receiving()) == 2, "ineligible ordinary fallback skipped receiving validation")
    verify(session, session.receiving()[-1], changed, data)
    require((session.right / name).read_bytes() == data, "ineligible fallback rejection replaced old live")
    session.control(name)
    retry = session.sync(options=options)
    require("Remote semantic fallback: no negotiated profile proves eligibility" in retry and len(session.receiving()) == 3,
            "ineligible fallback retry failed route/gate")
    require((session.right / name).read_bytes() == changed, "ineligible fallback result differs")
    return {"enabled_profiles_declined_private_tag": True,
            "ordinary_fallback_validated": True, "old_live_preserved_on_reject": True}


def policies(session):
    name, data = "policy.bin", container(private=True)
    session.control(name, server="error")
    (session.left / name).write_bytes(data)
    log = session.sync(policy="warn")
    require("validation warning" in log and len(session.receiving()) == 1, "warn skipped recognized validation")
    verify(session, session.receiving()[-1], data)
    changed = different(data, "off-policy-update")
    (session.left / name).write_bytes(changed)
    session.sync(policy="off")
    require(len(session.receiving()) == 1, "off invoked validation")
    require((session.right / name).read_bytes() == changed, "off failed exact ordinary update")
    return {"warn_calls": 1, "off_new_calls": 0}


def missing_tool(session):
    name, data = "no-local-validator.bin", container(xmp=False)
    session.control(name)
    (session.left / name).write_bytes(data)
    config = session.config("server")
    config["adobevalidator"] = ""
    session.server_settings(config)
    log = session.sync(success=False)
    require("Adobe DNG validation rejected" in log, "missing receiver tool did not reject renamed DNG")
    require(not session.calls("client") and not session.calls("server"), "sender tool rescued missing receiver")
    require(not (session.right / name).exists(), "missing receiver tool published required candidate")
    session.server_settings(session.config("server"))
    session.sync()
    require(len(session.receiving()) == 1, "missing-tool retry did not validate")
    verify(session, session.receiving()[-1], data)
    return {"missing_local_tool_rejected": True, "sender_invocations": 0}


def reverse(session):
    name, data = "reverse.bin", container(little=False, profile=True)
    session.control(name)
    (session.left / name).write_bytes(data)
    session.sync()
    incoming = different(data, "reverse")
    (session.right / name).write_bytes(incoming)
    session.control(name, client="error")
    session.sync(success=False)
    require(len(session.calls("client")) == 1 and len(session.calls("server")) == 1,
            "reverse receiving helper ran on wrong endpoint")
    verify(session, session.calls("client")[-1], incoming, data, endpoint="client")
    require((session.left / name).read_bytes() == data, "reverse rejection replaced client live file")
    session.control(name)
    session.sync()
    verify(session, session.calls("client")[-1], incoming, data, endpoint="client")
    require((session.left / name).read_bytes() == incoming, "reverse retry result differs")
    base.no_op(session, name, incoming)
    return {"client_receiving_calls": 2, "server_receiving_calls": 1}


def directory(session):
    name = "mixed-tree"
    album = session.left / name
    album.mkdir()
    (album / "sub").mkdir()
    values = {"one.bin": container(), "sub/two.bin": container(big=True, profile=True),
              "sub/no-xmp.data": container(xmp=False),
              "ordinary.tiff": unrelated_tiff(), "sub/ordinary.jpeg": unrelated_jpeg()}
    for relative, data in values.items():
        (album / relative).write_bytes(data)
    session.control(name, server="error", directory=True)
    session.sync(success=False)
    first = session.receiving()
    require(first and len(first) <= 3, "tree validation did not recognize exact DNG subset")
    require(not (session.right / name).exists(), "required mixed tree was partially published")
    require(all(not Path(call["candidate"]).exists() for call in first), "failed tree left resumable candidate")
    session.control(name, directory=True)
    before = len(session.receiving())
    session.sync()
    calls = session.receiving()[before:]
    require(len(calls) == 3, "mixed recursive tree recognized wrong file subset")
    expected = {str(session.right / name / relative): data for relative, data in values.items()
                if relative in ("one.bin", "sub/two.bin", "sub/no-xmp.data")}
    require({call["destination"] for call in calls} == set(expected), "tree receiving destination map differs")
    for call in calls:
        verify(session, call, expected[call["destination"]])
    for relative, data in values.items():
        require((session.right / name / relative).read_bytes() == data, "tree final exact bytes differ")
    before = len(session.receiving())
    inodes = {(session.right / name / relative).stat().st_ino for relative in values}
    session.sync()
    require(len(session.receiving()) == before, "no-op tree invoked validator")
    require({(session.right / name / relative).stat().st_ino for relative in values} == inodes,
            "no-op tree replaced an inode")
    return {"recognized_files": 3, "unrelated_files": 2, "recursive_destinations_proven": True}


def external(session):
    name, data = "external.bin", container(big=True, little=False, profile=True)
    session.control(name, server="error")
    (session.left / name).write_bytes(data)
    options = ("-copythreshold", "0", "-copyprog", str(session.copy),
               "-copyprogrest", str(session.copy), "-xferbycopying=false")
    log = session.sync(options=options, success=False)
    produced = base.records(session.copy.with_suffix(".calls.jsonl"))
    require(len(produced) == 1 and str(session.copy) in log, "external producer route not exercised")
    require(len(session.receiving()) == 1, "external recognized file omitted receiver validation")
    verify(session, session.receiving()[0], data)
    require(session.receiving()[0]["candidate"] == produced[0]["destination"], "wrong external candidate validated")
    require(not (session.right / name).exists(), "external require rejection was published")
    require(not Path(produced[0]["destination"]).exists(), "rejected external stage stayed reusable")
    session.control(name)
    session.sync(options=options)
    require(len(session.receiving()) == 2, "external fresh retry omitted receiver gate")
    require((session.right / name).read_bytes() == data, "external result bytes differ")
    return {"external_producer": True, "required_receiver_calls": 2}


def reused(session):
    donor, name, data = "z-donor.bin", "a-reused.bin", container(profile=True)
    session.control(donor)
    (session.left / donor).write_bytes(data)
    session.sync()
    session.control(name, server="error")
    (session.left / name).write_bytes(data)
    log = session.sync(success=False)
    require("Shortcut: copied " in log and "from local file " in log, "actual local donor reuse absent")
    require(len(session.receiving()) == 2, "recognized reused output omitted validation")
    verify(session, session.receiving()[-1], data)
    require(not (session.right / name).exists(), "reused require rejection committed")
    require((session.right / donor).read_bytes() == data, "reuse donor changed")
    session.control(name)
    retry = session.sync()
    require("Shortcut: copied " in retry and len(session.receiving()) == 3, "reuse retry path/gate absent")
    require((session.right / name).read_bytes() == data, "reuse bytes differ")
    return {"real_hint_copy": True, "donor_preserved": True, "calls": 3}


def resumed(session, kind):
    name = "resumed.bin"
    data = container(big=True, profile=True) + bytes(range(256)) * 8192
    produced = session.interruption(name, data, kind)
    session.control(name, server="error")
    log = session.sync(success=False, options=("-xferbycopying=false",))
    marker = "has already been transferred" if kind == "complete" else " bytes previously transferred for file resumed.bin"
    require(marker in log, "named recognized resumed route absent")
    require(len(session.receiving()) == 1, "recognized resumed candidate omitted validator")
    call = session.receiving()[0]
    verify(session, call, data)
    require((call["device"], call["inode"]) == (produced["device"], produced["inode"]),
            "resume silently rebuilt a different staged output")
    require(not (session.right / name).exists(), "recognized resumed rejection committed")
    require(not Path(produced["destination"]).exists(), "rejected resumed candidate stayed reusable")
    session.control(name)
    retry = session.sync(options=("-xferbycopying=false",))
    require("has already been transferred" not in retry and len(session.receiving()) == 2,
            "resume retry reused rejected staging or skipped validation")
    require((session.right / name).read_bytes() == data, "resumed result bytes differ")
    return {"interruption": kind, "same_resumed_inode_validated": True, "fresh_retry": True}


def merged(session):
    name, original = "merged.bin", container(big=True, little=False, profile=True)
    first, second, result = (different(original, label) for label in ("first", "second", "merged-result"))
    session.control(name)
    (session.left / name).write_bytes(original)
    session.sync()
    (session.left / name).write_bytes(first)
    (session.right / name).write_bytes(second)
    session.merger.with_suffix(".result").write_bytes(result)
    session.control(name, server="error")
    before = {endpoint: len(session.calls(endpoint)) for endpoint in ("client", "server")}
    options = ("-merge", "Name *.bin -> " + str(session.merger) + " CURRENT1 CURRENT2 NEW")
    session.sync(options=options, success=False)
    outputs = base.records(session.merger.with_suffix(".calls.jsonl"))
    require(len(outputs) == 1 and outputs[0]["inputs"] == [sha(first), sha(second)], "real merge conflict inputs differ")
    client, server = (session.calls(endpoint)[before[endpoint]:] for endpoint in ("client", "server"))
    require(len(client) == len(server) == 1, "recognized merge omitted a receiving endpoint")
    verify(session, client[0], result, first, endpoint="client")
    verify(session, server[0], result, second)
    require((session.left / name).read_bytes() == result and (session.right / name).read_bytes() == second,
            "merge did not preserve independent first-commit/second-reject behavior")
    require(not Path(server[0]["candidate"]).exists(), "rejected merge result stayed reusable")
    session.control(name)
    retry = session.sync(options=options)
    require("Merge command:" in retry, "merge recovery silently became one-sided overwrite")
    require((session.left / name).read_bytes() == (session.right / name).read_bytes() == result, "merge recovery bytes differ")
    require(len(session.calls("server")) - before["server"] == 2, "merge retry skipped receiving validation")
    base.no_op(session, name, result)
    return {"both_receivers_validated": True, "partial_commit_preserved": True, "fresh_conflict_retry": True}


def objects(build, name):
    text = (build / "Makefile.OCaml").read_text()
    value = re.search(r"^" + name + r" = (.*?)(?=\n\n)", text, re.M | re.S).group(1)
    return (value.replace("\\\n", " ").replace("$(SYSTEM)", "generic")
            .replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
            .replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split())


def generic_binary(build, compiler, work, commands):
    work.mkdir()
    source = ROOT / "tests/validation_recognition/genericValidator.ml"
    (work / source.name).write_bytes(source.read_bytes())
    includes = [work, build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [value for directory in includes for value in ("-I", str(directory))] + ["-I", "+unix", "-I", "+str"]
    env = os.environ.copy()
    for key in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(key, None)
    compile = [compiler, *flags, "-c", source.name]
    module_objects = objects(build, "OCAMLOBJS")
    link = [compiler, *flags, "unix.cmxa", "str.cmxa"]
    for name in module_objects:
        if name == "main.cmx":
            link.append("genericValidator.cmx")
        link.append(str(build / name))
    link += [str(build / "linktext.cmx"), *[str(build / name) for name in objects(build, "COBJS")],
             "-o", str(work / "unison-generic-validator")]
    for label, command in (("compile", compile), ("link", link)):
        log = work / (label + ".log")
        with log.open("w") as output:
            result = subprocess.run(command, cwd=work, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=120)
        commands.append({"argv": command, "cwd": str(work), "exit_code": result.returncode,
                         "log": str(log), "log_sha256": sha_file(log)})
        require(result.returncode == 0, log.read_text())
    return str(work / "unison-generic-validator")


def generic(session):
    name, data = "declared-format.bin", b"TOY0fixture payload with no DNG or transfer profile"
    client_log, server_log = session.root / "client-toy.tsv", session.root / "server-toy.tsv"
    session.server_settings(dict(session.config("server"), testvalidatorlog=str(server_log),
                                 testvalidatormode="reject"))
    options = ("-testvalidatorlog", str(client_log), "-testvalidatormode", "reject")
    (session.left / name).write_bytes(data)
    log = session.sync(policy="off", options=options, success=False)
    require("synthetic registered validator rejected" in log, "generic declared companion was not selected")
    require(server_log.exists() and len(server_log.read_text().splitlines()) == 1 and not client_log.exists(),
            "generic receiving callback ran on wrong endpoint")
    record = server_log.read_text().splitlines()[0].split("\t")
    require(record[1:] == [sha(data), str(len(data)), "reject"], "generic complete snapshot transport differs")
    require(not (session.right / name).exists() and not Path(record[0]).exists(), "generic rejection published/retained staging")
    require(not session.calls("client") and not session.calls("server"), "generic companion invoked DNG driver with Adobe off")
    session.server_settings(dict(session.config("server"), testvalidatorlog=str(server_log),
                                 testvalidatormode="pass"))
    session.sync(policy="off", options=options)
    require((session.right / name).read_bytes() == data and len(server_log.read_text().splitlines()) == 2,
            "generic companion fresh retry failed")
    incoming = data + b"-reverse"
    (session.right / name).write_bytes(incoming)
    session.sync(policy="off", options=options, success=False)
    require(client_log.exists() and len(client_log.read_text().splitlines()) == 1,
            "reverse generic receiver did not own callback")
    require((session.left / name).read_bytes() == data, "reverse generic rejection replaced live bytes")
    return {"adobe_off": True, "transfer_profiles_disabled": True,
            "generic_registry_receiver_rejection": True, "both_endpoint_callbacks": True}


def inventory(work):
    entries = {}
    for path in sorted(work.rglob("*")):
        if path.is_file():
            st = path.stat()
            entries[str(path.relative_to(work))] = {"size": st.st_size, "sha256": sha_file(path)}
        elif path.is_symlink():
            entries[str(path.relative_to(work))] = {"symlink": os.readlink(path)}
        elif path.is_dir():
            entries[str(path.relative_to(work))] = {"directory": True}
    return entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unison", type=Path, required=True)
    ap.add_argument("--build", type=Path, required=True)
    ap.add_argument("--ocamlopt", required=True)
    ap.add_argument("--negative-unison", type=Path)
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--volume-jobs", type=int, default=1)
    args = ap.parse_args()
    require(args.volume_jobs >= 0, "filesystem jobs must be nonnegative")
    base.ADMISSION_OPTIONS[:] = ["-semanticvolumejobs", str(args.volume_jobs)]
    binary, build = str(args.unison.resolve()), args.build.resolve() / "src"
    compiler = shutil.which(args.ocamlopt)
    require(compiler is not None, "native compiler unavailable")
    work = Path(tempfile.mkdtemp(prefix="unison-validation-recognition-", dir="/private/tmp"))
    print("Private synthetic receiving artifacts", work, flush=True)
    sources = {relative: sha_file(ROOT / relative) for relative in SOURCES + INPUTS}
    for relative in SOURCES:
        require(sha_file(build / Path(relative).name) == sources[relative], "stale production snapshot " + relative)
    for relative in SOURCES + INPUTS:
        destination = work / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    results, executions, builds = [], [], []

    def case(name, operation, *, remote=True, executable=binary):
        session = Session(work / name, executable, executions, remote=remote)
        result = operation(session)
        results.append({"name": name, "status": "passed", **result})
        print("PASS", name, flush=True)

    for name, data in fixtures():
        case("recognized-" + name, lambda session, data=data:
             rejected_then_retry(session, "received.bin", data))
    case("local-new", lambda session: rejected_then_retry(session, "local.bin", container()), remote=False)
    case("local-update-noop", updates, remote=False)
    case("loopback-reverse-noop", reverse)
    case("malformed-filename-claim", lambda session: rejected_then_retry(session, "claimed.DNG", b"malformed claimed DNG"))
    case("transfer-enabled-ineligible-private", ineligible_update)
    case("unrelated-no-helper", unrelated)
    case("warn-and-off", policies)
    case("missing-endpoint-tool", missing_tool)
    case("recursive-mixed-tree", directory)
    case("external-producer", external)
    case("hint-copy-reuse", reused)
    for kind in ("complete", "partial"):
        case("recognized-resume-" + kind, lambda session, kind=kind: resumed(session, kind))
    case("generated-merge-two-receivers", merged)
    companion = generic_binary(build, compiler, work / "generic-build", builds)
    case("generic-declaration-adobe-off", generic, executable=companion)
    negative = None
    if args.negative_unison:
        old = str(args.negative_unison.resolve())
        session = Session(work / "obsolete-suffix-only-negative", old, executions)
        name, data = "recognized.bin", container()
        session.control(name, server="error")
        (session.left / name).write_bytes(data)
        status, log = session.raw_sync()
        require(status == 0 and not session.receiving() and (session.right / name).read_bytes() == data,
                "old suffix-only negative did not reproduce actual unvalidated publication\n" + log)
        negative = {"binary": old, "binary_sha256": sha_file(Path(old)),
                    "actual_cli_exit": status, "receiving_helper_calls": 0,
                    "published_sha256": sha_file(session.right / name),
                    "detected_defect": "Recognizable renamed DNG published despite required synthetic validator rejection"}
        print("PASS obsolete suffix-only actual-publication negative", flush=True)
    require(all(sha_file(ROOT / relative) == expected for relative, expected in sources.items()),
            "source changed during qualification")
    manifest = work / "artifact-manifest.json"
    manifest.write_text(json.dumps(inventory(work), indent=2) + "\n")
    receipt = {"schema": "unison-validation-content-recognition-receive/1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Actual compiler-matched Unison receiving gates and private TOY0 companion; independent synthetic format claims/driver receipts, no Adobe/Photo/pixel/SDK validation claim",
        "binary": binary, "binary_sha256": sha_file(Path(binary)),
        "compiler": compiler, "compiler_version": subprocess.check_output([compiler, "-version"], text=True).strip(),
        "compiler_sha256": sha_file(Path(compiler)), "build": str(args.build.resolve()),
        "sources_sha256": sources,
        "linked_objects_sha256": {name: sha_file(build / name)
                                  for name in objects(build, "OCAMLOBJS") + objects(build, "COBJS") + ["linktext.cmx"]},
        "artifact_directory": str(work), "retained": args.keep_work,
        "filesystem_jobs": args.volume_jobs, "cases": results,
        "executions": executions, "generic_build_commands": builds,
        "obsolete_suffix_only_negative": negative,
        "artifact_manifest": str(manifest), "artifact_manifest_sha256": sha_file(manifest),
        "current_sources_match_snapshot": True, "terminal": "passed",
        "limitations": ["Arbitrary synthetic payloads are not Adobe-valid images",
            "No SDK, renderer, preview/cache/catalog/Photo or production volume access",
            "Merge commits remain independent per replica; no cross-replica atomicity",
            "Interrupted producer proves actual resumed inode/routing, not crash-durable publication",
            "Private directory helper maps staged relative paths; original21-case harness source is unchanged",
            "Runtime workers/operational fault internals are independently qualified in the integration owner's controls"]}
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print("All", len(results), "receiving recognition cases passed; receipt", args.receipt, flush=True)
    if not args.keep_work:
        shutil.rmtree(work)


if __name__ == "__main__":
    main()
