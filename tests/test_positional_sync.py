#!/usr/bin/env python3
"""Fail the second actual metadata pwrite in isolated Unison receive callers.

The only fault is a C-only wrapper in a private compiler-matched snapshot.
Synthetic source flags decline source cloning, allowing the normal local SDE
receiver to run. No production fault hook, Adobe helper or photographic input
is used. Archive checks are raw fingerprint-byte observations; this runner does
not decode archive headers or bind a decoded node to the image pathname.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bench/sync"))
from ownership import OwnedGroup
from measure import CapturedStream, receipt as resource_receipt


NATIVE = r'''
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

/* This private control admits one output job per process. */
static unsigned positional_sync_calls;
static off_t positional_sync_first_offset;
static unsigned char positional_sync_first_bytes[16];

static ssize_t positional_sync_write(int fd, const void *data, size_t count,
                                    off_t position)
{
  unsigned call = ++positional_sync_calls;
  ssize_t result;
  int error, matches = 0;
  if (call == 2) { result = -1; error = EIO; }
  else { result = pwrite(fd, data, count, position); error = result < 0 ? errno : 0; }
  if (call == 1 && result > 0) {
    unsigned char *readback = malloc((size_t)result);
    if (!readback) abort();
    size_t got = 0;
    while (got < (size_t)result) {
      ssize_t n = pread(fd, readback + got, (size_t)result - got, position + got);
      if (n < 0 && errno == EINTR) continue;
      if (n <= 0) break;
      got += (size_t)n;
    }
    matches = got == (size_t)result && !memcmp(readback, data, got);
    free(readback);
    positional_sync_first_offset = position;
    if (result >= sizeof(positional_sync_first_bytes))
      memcpy(positional_sync_first_bytes, data, sizeof(positional_sync_first_bytes));
  } else if (call == 2) {
    unsigned char prefix[sizeof(positional_sync_first_bytes)];
    ssize_t n = pread(fd, prefix, sizeof(prefix), positional_sync_first_offset);
    matches = n == sizeof(prefix) && !memcmp(prefix, positional_sync_first_bytes, sizeof(prefix));
  }
  struct stat held;
  char path[PATH_MAX], row[PATH_MAX + 512];
  if (fstat(fd, &held) || fcntl(fd, F_GETPATH, path)) abort();
  int length = snprintf(row, sizeof(row), "%ld\t%u\t%zu\t%jd\t%jd\t%d\t%ju\t%ju\t%ju\t%d\t%s\t%ld\n",
      (long)getpid(), call, count, (intmax_t)result, (intmax_t)position, error,
      (uintmax_t)held.st_dev, (uintmax_t)held.st_ino, (uintmax_t)held.st_nlink, matches, path, (long)getpgrp());
  if (length <= 0 || length >= sizeof(row)) abort();
  int trace = open(TRACE_PATH, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0600);
  if (trace < 0) abort();
  size_t sent = 0;
  while (sent < (size_t)length) {
    ssize_t n = write(trace, row + sent, (size_t)length - sent);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) abort();
    sent += (size_t)n;
  }
  if (close(trace)) abort();
  errno = error;
  return result;
}
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(value):
    packet = b"<x>" + value * (192 * 1024 - 7) + b"</x>"
    data = bytearray(512 * 1024)
    struct.pack_into("<2sHIH", data, 0, b"II", 42, 8, 4)
    for index, entry in enumerate(((273, 4, 1, 262144), (279, 4, 1, 65536),
                                   (700, 1, len(packet), 1024), (50706, 1, 4, 1025))):
        struct.pack_into("<HHII", data, 10 + index * 12, *entry)
    data[1024:1024 + len(packet)] = packet
    data[262144:327680] = bytes(range(256)) * 256
    return bytes(data)


def archive_snapshot(states, expected, forbidden):
    result = {}
    for state in states:
        for path in sorted(state.iterdir()):
            if re.fullmatch(r"ar[0-9a-f]{32}", path.name):
                data = path.read_bytes()
                assert expected in data and forbidden not in data, (str(path), "raw archive fingerprint-byte observation differed")
                result[str(path)] = sha(path)
    assert len(result) >= 2, "fewer than two archive-named fingerprint-byte observations"
    return result


def inventories(left, right):
    for directory in (left, right):
        actual = {path.name for path in directory.iterdir()}
        assert actual == {"image.dng"}, (str(directory), actual)


def run_owned(command, environment, timeout, after_start=None):
    """Retain the leader PID through group cleanup; preserve primary errors."""
    owner = OwnedGroup(command, env=environment, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    captures, output = {}, {}
    primary, cleanup_errors, settled, usage = None, [], None, None
    timed_out = False
    try:
        captures["stdout"] = CapturedStream(owner.process.stdout)
        captures["stderr"] = CapturedStream(owner.process.stderr)
        if after_start:
            after_start(owner)
        timed_out = not owner.await_terminal(timeout)
    except BaseException as error:
        primary = (error, error.__traceback__)
    finally:
        try:
            settled, usage = owner.finish(cancel_reason="capture interrupted" if primary else
                                         "native client deadline" if timed_out else None)
        except BaseException as error:
            if primary is None:
                primary = (error, error.__traceback__)
            else:
                cleanup_errors.append(repr(error))
        for name, stream in (("stdout", owner.process.stdout), ("stderr", owner.process.stderr)):
            try:
                if name in captures:
                    output[name] = captures[name].finish()
                else:
                    stream.close()
                    output[name] = {"text": "", "bytes": 0, "truncated": False}
            except BaseException as error:
                if primary is None:
                    primary = (error, error.__traceback__)
                else:
                    cleanup_errors.append(repr(error))
    if primary:
        error, traceback = primary
        error.owned_cleanup = settled
        error.owned_cleanup_errors = cleanup_errors
        raise error.with_traceback(traceback)
    return {"command": command, "pid": owner.pid, "exit": settled["returncode"],
            "timed_out": timed_out, "client_cleanup": settled,
            "resources": resource_receipt(usage), "capture": output}


def cleanup_controls(work):
    """Finite controls for deadlines, exited leaders and assertion cleanup."""
    environment = dict(os.environ)
    controls = []
    deadline = run_owned([sys.executable, "-c", "import time;time.sleep(30)"], environment, 0.02)
    assert deadline["timed_out"] and deadline["client_cleanup"]["reaped"]
    assert deadline["client_cleanup"]["group_cleanup_before_leader_reap"]
    controls.append({"name": "forced deadline", "result": deadline})
    descendant = ("import os,time,json\nr,w=os.pipe()\npid=os.fork()\n"
        "if pid==0:\n os.close(r)\n print(json.dumps({'child':os.getpid(),'pgid':os.getpgrp()}),flush=True)\n"
        " os.write(w,b'R');os.close(w);time.sleep(30)\n"
        "else:\n os.close(w);os.read(r,1);os.close(r);os._exit(0)\n")
    terminal = run_owned([sys.executable, "-c", descendant], environment, 3)
    assert terminal["exit"] == 0 and not terminal["timed_out"]
    child = json.loads(terminal["capture"]["stdout"]["text"])
    assert child["pgid"] == terminal["pid"]
    assert terminal["client_cleanup"]["group_cleanup_before_leader_reap"]
    controls.append({"name": "terminal leader with descendant retaining stdout", "result": terminal})
    outer = run_owned([sys.executable, "-c", descendant], environment, 3)
    error = AssertionError("private outer assertion")
    try:
        raise error
    except AssertionError as caught:
        assert caught is error and outer["client_cleanup"]["reaped"]
        assert outer["client_cleanup"]["group_cleanup_before_leader_reap"]
    controls.append({"name": "outer assertion after settled group", "result": outer})
    primary = AssertionError("private primary exception")
    original_finish, calls = CapturedStream.finish, []

    def finish(capture):
        result = original_finish(capture)
        calls.append(result)
        if len(calls) == 1:
            raise RuntimeError("private secondary capture exception")
        return result

    def inject(_):
        raise primary

    CapturedStream.finish = finish
    try:
        try:
            run_owned([sys.executable, "-c", "import time;time.sleep(30)"], environment, 3, inject)
            raise RuntimeError("primary exception control did not execute")
        except AssertionError as caught:
            assert caught is primary and len(calls) == 2
            assert caught.owned_cleanup["reaped"] and caught.owned_cleanup["group_cleanup_before_leader_reap"]
            assert any("private secondary capture exception" in item for item in caught.owned_cleanup_errors)
            controls.append({"name": "primary exception preserved and both captures settled",
                             "client_cleanup": caught.owned_cleanup,
                             "secondary_errors": caught.owned_cleanup_errors})
    finally:
        CapturedStream.finish = original_finish
    (work / "cleanup-controls.json").write_text(json.dumps(controls, indent=2) + "\n")
    return controls


def run_case(work, normal, faulty, trace, remote):
    case = work / ("remote" if remote else "local")
    case.mkdir()
    left, right, state, receiver = (case / name for name in ("left", "right", "state", "receiver-state"))
    for path in (left, right, state, receiver):
        path.mkdir()
    source, target = left / "image.dng", right / "image.dng"
    old, new = fixture(b"A"), fixture(b"B")
    source.write_bytes(old)
    child_log = case / "child-pids.jsonl"
    launcher = case / "loopback.py"
    launcher.write_text("#!/usr/bin/env python3\nimport os,sys,json\n"
        "a=sys.argv[1:]\ni=next(i for i,s in enumerate(a) if os.path.basename(s)=='unison')\n"
        "with open(" + repr(str(child_log)) + ",'a') as f: f.write(json.dumps({'pid':os.getpid(),'pgid':os.getpgrp(),'binary':a[i]})+'\\n')\n"
        "os.environ['UNISON']=" + repr(str(receiver)) + "\n"
        "os.execv(a[i],a[i:])\n")
    launcher.chmod(0o700)
    base = [str(left), "ssh://localhost/" + str(right) if remote else str(right),
            "-batch", "-auto", "-fastcheck", "false", "-times", "-semanticdng",
            "-clone", "auto", "-semanticworkers", "1", "-semanticmaxinflight", "2",
            "-maxthreads", "1", "-debug", "semantic", "-debug", "copy"]
    environment = dict(os.environ, UNISON=str(state))

    def sync(binary, phase, success):
        command = [str(binary), *base]
        if remote:
            command += ["-sshcmd", str(launcher), "-servercmd", str(binary)]
        before_children = child_log.read_text().splitlines() if child_log.exists() else []
        process = run_owned(command, environment, 90)
        output = process["capture"]["stdout"]["text"] + process["capture"]["stderr"]["text"]
        (case / (phase + ".log")).write_text(output)
        assert not process["timed_out"] and not any(value["truncated"] for value in process["capture"].values())
        assert (process["exit"] == 0) == success, (phase, process["exit"], output)
        children = [json.loads(line) for line in child_log.read_text().splitlines()[len(before_children):]] if child_log.exists() else []
        for child in children:
            assert child["pgid"] == process["pid"], "loopback escaped owned group"
        process["observed_child_processes"] = children
        return process, output

    baseline, _ = sync(normal, "baseline", True)
    inventories(left, right)
    assert target.read_bytes() == old
    old_identity = (target.stat().st_dev, target.stat().st_ino)
    old_digest, new_digest = hashlib.md5(old).digest(), hashlib.md5(new).digest()
    states = (state, receiver)
    before_archives = archive_snapshot(states, old_digest, new_digest)
    for name, digest in before_archives.items():
        copy = case / (Path(name).parent.name + "-before-" + Path(name).name)
        shutil.copy2(name, copy)
        assert sha(copy) == digest
    source.write_bytes(new)
    # Decline the local source clone through its actual Source_flags rule. The
    # retained receiver basis stays unflagged and supports semantic cloning.
    os.chflags(source, stat.UF_NODUMP)
    source_identity = (source.stat().st_dev, source.stat().st_ino)
    trace.unlink(missing_ok=True)
    failed, output = sync(faulty, "partial-error", False)
    assert "semantic pwrite" in output and "Input/output error" in output, output
    rows = [line.split("\t") for line in trace.read_text().splitlines()]
    assert len(rows) == 2 and [int(row[1]) for row in rows] == [1, 2], rows
    assert int(rows[0][2]) == 65536 and int(rows[0][3]) == 65536 and int(rows[0][4]) == 1024, rows
    assert int(rows[1][2]) == 65536 and int(rows[1][3]) == -1 and int(rows[1][4]) == 66560, rows
    assert int(rows[1][5]) == 5 and [row[9] for row in rows] == ["1", "1"], rows
    assert rows[0][6:9] == rows[1][6:9] and rows[0][8] == "1", rows
    assert len({row[0] for row in rows}) == 1, rows
    writer_pid = int(rows[0][0])
    assert int(rows[0][11]) == failed["pid"] and rows[0][11] == rows[1][11]
    assert writer_pid == failed["pid"] if not remote else any(
        child["pid"] == writer_pid for child in failed["observed_child_processes"])
    stage = Path(rows[0][10])
    assert stage != target and not stage.exists(), "partial stage remained or named live target"
    assert (target.stat().st_dev, target.stat().st_ino) == old_identity and target.read_bytes() == old
    assert (source.stat().st_dev, source.stat().st_ino) == source_identity and source.read_bytes() == new
    inventories(left, right)
    after_archives = archive_snapshot(states, old_digest, new_digest)
    assert set(after_archives) == set(before_archives), "Main archive names changed after failed transfer"
    shutil.copy2(trace, case / "partial-error-trace.tsv")
    retry, retry_output = sync(normal, "retry", True)
    assert ("Remote semantic clone wrote" if remote else "Local semantic workers wrote") in retry_output, retry_output
    assert target.read_bytes() == new and source.read_bytes() == new
    assert target.stat().st_ino != old_identity[1], "successful retry did not replace old live inode"
    inventories(left, right)
    after_retry = archive_snapshot(states, new_digest, old_digest)
    new_identity = (target.stat().st_dev, target.stat().st_ino)
    noop, noop_output = sync(normal, "noop", True)
    assert (target.stat().st_dev, target.stat().st_ino) == new_identity and target.read_bytes() == new
    assert "semantic clone wrote" not in noop_output and "Local semantic workers wrote" not in noop_output
    inventories(left, right)
    return {"name": case.name, "baseline": baseline, "failed": failed, "retry": retry, "noop": noop,
            "old_sha256": hashlib.sha256(old).hexdigest(), "target_sha256": hashlib.sha256(new).hexdigest(),
            "old_live_identity": old_identity, "successful_live_identity": new_identity,
            "raw_archive_fingerprint_bytes_before": before_archives,
            "raw_archive_fingerprint_bytes_after_failure": after_archives,
            "raw_archive_fingerprint_bytes_after_retry": after_retry, "trace_rows": rows,
            "partial_prefix_readback_bytes": 65536, "second_error_prefix_rechecked_bytes": 16,
            "partial_stage_discarded": str(stage), "observed_writer_pid_in_owned_group": writer_pid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("This native APFS receive-path fixture requires macOS")
    root = Path(__file__).resolve().parent.parent
    snapshot = args.build.resolve()
    source_names = [os.fsdecode(name) for name in subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root).split(b"\0")
        if name and os.fsdecode(name).startswith("src/") and os.fsdecode(name) != "src/.depend"]
    manifest = {name: sha(root / name) for name in source_names if (root / name).is_file()}
    assert all(sha(snapshot / name) == digest for name, digest in manifest.items()), "refresh compiler-matched snapshot"
    compiler = Path(args.ocamlopt).resolve()
    assert subprocess.check_output([str(compiler), "-version"], text=True).strip() in ("5.5.1", "5.2.0+ox")
    work = Path(tempfile.mkdtemp(prefix="unison-positional-sync-", dir="/private/tmp"))
    print("work", work, flush=True)
    complete = False
    try:
        controls = cleanup_controls(work)
        private = work / "build"
        shutil.copytree(snapshot, private)
        shutil.copy2(__file__, work / "runner.py")
        trace = work / "pwrite-trace.tsv"
        original = (private / "src/semanticFile_stubs.c").read_text()
        call = "ssize_t written = pwrite(fd, buffer, (size_t)count, native_offset);"
        insertion = "CAMLprim value unison_semantic_pwrite("
        assert original.count(call) == 1 and original.count(insertion) == 1
        # F_GETPATH is a Darwin-only observation in this private fixture;
        # production deliberately exposes only its portable POSIX interface.
        mutated = "#define _DARWIN_C_SOURCE 1\n" + original.replace(insertion,
            "#define TRACE_PATH " + json.dumps(str(trace)) + "\n" + NATIVE + "\n" + insertion)
        mutated = mutated.replace(call, "ssize_t written = positional_sync_write(fd, buffer, (size_t)count, native_offset);")
        (private / "src/semanticFile_stubs.c").write_text(mutated)
        environment = dict(os.environ, PATH=str(compiler.parent) + os.pathsep + os.environ.get("PATH", ""))
        for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
            environment.pop(name, None)
        command = ["make", "-C", "src", "tui", "-j4", "NATIVE=true", "TOOL_PREFIX=" + str(compiler.parent) + "/"]
        with (work / "build.log").open("w") as log:
            subprocess.run(command, cwd=private, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
        results = [run_case(work, snapshot / "src/unison", private / "src/unison", trace, remote)
                   for remote in (False, True)]
        receipt = {"status": "PASS", "compiler": str(compiler), "compiler_version": subprocess.check_output(
            [str(compiler), "-version"], text=True).strip(), "production_manifest": manifest,
            "normal_snapshot": str(snapshot), "normal_binary_sha256": sha(snapshot / "src/unison"),
            "private_build": str(private), "private_build_command": command,
            "private_c_sha256": sha(private / "src/semanticFile_stubs.c"),
            "private_object_sha256": sha(private / "src/semanticFile_stubs.o"),
            "private_binary_sha256": sha(private / "src/unison"), "build_log_sha256": sha(work / "build.log"),
            "runner_sha256": sha(work / "runner.py"), "cases": results, "cleanup_controls": controls,
            "ownership_sources": {str(root / name): sha(root / name) for name in
                ("bench/sync/ownership.py", "bench/sync/measure.py")},
            "limits": ["Synthetic own APFS files only; no Adobe/Photo.",
                "Native trace/readback proves one real 64KiB private-stage prefix before injected EIO and cleanup.",
                "Raw archive fingerprint-byte observations do not decode a header or bind an image.dng node; normal retry and stable noop exercise actual subsequent archive behavior.",
                "Owned leader wait4/reap and guarded process-group cleanup are observed; no claim that PID absence proves descendant reap, or that all in-process credit/FD counters were inspected.",
                "OwnedGroup keeps its qualified wait4-after-SIGKILL OS-semantics limit; this fixture adds no absolute OS settlement-deadline promise.",
                "Private C fault wrapper is single-output-per-process; no production fault hook or new preference."]}
        (work / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print("PASS local and remote partial native pwrite error: preserved live, raw archive observations, discarded stage, exact retry, stable noop", flush=True)
        print("receipt", work / "verification.json", flush=True)
        complete = True
    finally:
        if not args.keep_work and complete:
            shutil.rmtree(work)


if __name__ == "__main__":
    main()
