#!/usr/bin/env python3
"""Qualify DNG /1 routing and legacy /0 preference compatibility.

Supply isolated compiler-matched current and frozen v0 Make snapshots. All DNG
bytes are independently assembled here; no Adobe or photographic inputs are
used. Work, terminal logs, owned-group cleanup and source/binary pins are kept.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

from test_positional_sync import run_owned


V0, V1 = "org.firstpair.dng-xmp/0", "org.firstpair.dng-xmp/1"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(value=b"one", *, big=False, little=True, camera=False, opaque=65):
    """A fixed XMP packet, one raw strip and optional independent CR graph."""
    data = bytearray(2 * 1024 * 1024)
    endian, order = ("<", b"II") if little else (">", b"MM")
    xmp = b"<x>" + value + b"</x>" + b" " * 32
    width = {1: 1, 2: 1, 4: 4, 10: 8, 16: 8}

    def directory(at, entries, *, end, is_big):
        inline, count_width, entry_size = (8, 8, 20) if is_big else (4, 2, 12)
        struct.pack_into(end + ("Q" if is_big else "H"), data, at, len(entries))
        for index, (tag, typ, count, content) in enumerate(entries):
            entry = at + count_width + index * entry_size
            struct.pack_into(end + ("HHQ" if is_big else "HHI"), data, entry, tag, typ, count)
            value_at = entry + (12 if is_big else 8)
            if isinstance(content, bytes):
                assert len(content) == count * width[typ] <= inline
                data[value_at:value_at + len(content)] = content
            else:
                struct.pack_into(end + ("Q" if is_big else "I"), data, value_at, content)
        # All next-directory offsets remain explicitly zero.

    pointer = 16 if big else 4
    entries = [(273, pointer, 1, 4096), (279, pointer, 1, 1024),
               (700, 1, len(xmp), 1024), (50706, 1, 4, b"\x01\x04\x00\x00")]
    if camera:
        entries.append((50933, pointer, 1, 6144))
        # CR headers always use their own endian and classic 32-bit offsets,
        # including when the outer file is BigTIFF. Offsets are header-relative.
        camera_end, camera_order = (">", b"MM") if little else ("<", b"II")
        struct.pack_into(camera_end + "2sHI", data, 6144, camera_order, 0x4352, 8)
        directory(6152, [(50721, 10, 9, 128), (50936, 2, 12, 256)],
                  end=camera_end, is_big=False)
        for index in range(9):
            struct.pack_into(camera_end + "ii", data, 6272 + index * 8, index + 1, 10)
        data[6400:6412] = b"TestCamera\0\0"
    if big:
        struct.pack_into(endian + "2sHHHQ", data, 0, order, 43, 8, 0, 16)
        directory(16, entries, end=endian, is_big=True)
    else:
        struct.pack_into(endian + "2sHI", data, 0, order, 42, 8)
        directory(8, entries, end=endian, is_big=False)
    data[1024:1024 + len(xmp)] = xmp
    data[4096:5120] = bytes(range(256)) * 4
    data[-1] = opaque
    return bytes(data)


def objects(makefile, name):
    match = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S)
    if not match:
        raise RuntimeError("missing Make object list: " + name)
    body = match.group(1).replace("\\\n", " ").replace("$(SYSTEM)", "generic")
    body = body.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
    return body.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()


class Qualification:
    def __init__(self, current, old, compiler, work, other=None):
        self.current, self.old, self.compiler, self.work = current, old, compiler, work
        self.other = other
        self.other_peer = None
        self.commands, self.cases, self.usage_rejections, self.pins = [], [], [], {}
        self.retained_sources = {}

    def command(self, name, command, environment, timeout=90, expected_exit=0):
        result = run_owned(command, environment, timeout)
        index = len(self.commands)
        log = self.work / f"{index:03d}-{name}.log"
        text = result["capture"]["stdout"]["text"] + result["capture"]["stderr"]["text"]
        log.write_text(text)
        for stream in result["capture"].values():
            assert not stream["truncated"], str(log)
        assert not result["timed_out"], str(log)
        assert result["client_cleanup"]["reaped"], str(log)
        assert result["client_cleanup"]["group_cleanup_before_leader_reap"], str(log)
        self.commands.append({"name": name, "result": result,
                              "log": str(log), "log_sha256": sha(log)})
        if expected_exit is None:
            assert result["exit"] != 0, str(log)
        else:
            assert result["exit"] == expected_exit, str(log)
        return text

    def preferences(self):
        build = self.current / "src"
        makefile = (build / "Makefile.OCaml").read_text()
        modules = objects(makefile, "OCAMLOBJS")
        modules = modules[:modules.index("semanticFormats.cmx") + 1]
        includes = [build, build / "ubase", build / "system", build / "system/generic",
                    build / "lwt", build / "lwt/generic"]
        flags = [flag for path in includes for flag in ("-I", str(path))] + ["-I", "+unix", "-I", "+str"]
        source = self.work / "preferences.ml"
        source.write_bytes((HERE / "dng_profile_v1_preferences.ml").read_bytes())
        binary = self.work / "preferences"
        linked = [build / obj for obj in modules + objects(makefile, "COBJS")]
        for path in linked:
            self.pins[str(path)] = sha(path)
            if path.suffix == ".cmx":
                self.pins[str(path.with_suffix(".o"))] = sha(path.with_suffix(".o"))
        command = [str(self.compiler)] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules] + [str(source)]
        command += [str(build / obj) for obj in objects(makefile, "COBJS")]
        command += ["-o", str(binary)]
        environment = dict(os.environ, UNISON=str(self.work / "pref-state"))
        self.command("prefs-link", command, environment, timeout=180)
        log = self.command("prefs-boundary", [str(binary)], environment)
        assert "legacy wire, stale alias clearing, final intersection, local retention and typo rejection" in log
        self.pins[str(binary)] = sha(binary)
        self.pins[str(source)] = sha(source)
        self.cases.append({"name": "actual preference wire boundary", "result": log.strip()})

    def exercise(self, name, client, servers, options, variants):
        directory = self.work / name
        directory.mkdir()
        left, right, client_state = (directory / item for item in ("left", "right", "client-state"))
        for path in (left, right, client_state):
            path.mkdir()
        mapping = {}
        roots = []
        for index, (path, server) in enumerate(zip((left, right), servers)):
            if server is None:
                roots.append(str(path))
            else:
                host = "fixture-left" if index == 0 else "fixture-right"
                state = directory / (host + "-state")
                state.mkdir()
                mapping[host] = (str(server), str(state))
                roots.append("ssh://" + host + "/" + str(path))
        launcher = directory / "loopback.py"
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
            "mapping=" + repr(mapping) + "\nargs=sys.argv[1:]\n"
            "host=next(x for x in args if x in mapping)\n"
            "binary,state=mapping[host]\ni=args.index('unison-fixture-server')\n"
            "os.environ['UNISON']=state\nos.execv(binary,[binary]+args[i+1:])\n")
        launcher.chmod(0o700)
        command = [str(client)] + roots + ["-sshcmd", str(launcher), "-servercmd", "unison-fixture-server",
            "-batch", "-auto", "-fastcheck", "false", "-times", "-debug", "semantic",
            "-semanticworkers", "1", "-semanticmaxinflight", "2"] + options
        environment = dict(os.environ, UNISON=str(client_state))
        source, target = left / "image.dng", right / "image.dng"

        def sync(label, expected_profile):
            log = self.command(name + "-" + label, command, environment)
            transfers = re.findall(r"Remote semantic clone wrote[^\n]*\((?:[^\n]*; )?(org\.firstpair\.dng-xmp/[01])\)", log)
            if expected_profile:
                assert transfers == [expected_profile], (name, label, transfers, log)
            else:
                assert not transfers and "Remote semantic clone wrote" not in log, (name, label, log)
            for path in (left, right):
                assert {entry.name for entry in path.iterdir()} == {"image.dng"}, str(path)
            return log

        for variant, parameters, profile in variants:
            # Separate archives/root identities for each TIFF container prevent
            # a layout replacement from masquerading as the XMP-only test.
            if source.exists():
                raise RuntimeError("one variant per exercise required")
            source.write_bytes(fixture(**parameters)); sync(variant + "-baseline", None)
            source.write_bytes(fixture(b"two", **parameters)); sync(variant + "-remote-receive", profile)
            assert source.read_bytes() == target.read_bytes()
            target.write_bytes(fixture(b"six", **parameters)); sync(variant + "-reverse-receive", profile)
            assert source.read_bytes() == target.read_bytes()
            source.write_bytes(fixture(b"new", opaque=90, **parameters)); sync(variant + "-opaque-fallback", None)
            assert source.read_bytes() == target.read_bytes()
            source.write_bytes(fixture(b"longer packet", opaque=90, **parameters)); sync(variant + "-layout-fallback", None)
            assert source.read_bytes() == target.read_bytes()
            inodes = source.stat().st_ino, target.stat().st_ino
            sync(variant + "-noop", None)
            assert inodes == (source.stat().st_ino, target.stat().st_ino)
            self.cases.append({"name": name, "variant": variant, "expected_profile": profile,
                               "both_directions_exact": True, "opaque_and_layout_fallback": True,
                               "exact_directory_inventories": True, "noop_inodes_stable": True,
                               "fixture_sha256": hashlib.sha256(fixture(**parameters)).hexdigest()})

    def typo(self):
        directory = self.work / "unknown-profile"
        directory.mkdir()
        left, right, state = (directory / item for item in ("left", "right", "state"))
        for path in (left, right, state):
            path.mkdir()
        contents = fixture()
        (left / "image.dng").write_bytes(contents)
        command = [str(self.current / "src/unison"), str(left), str(right), "-batch", "-auto",
                   "-semanticprofile", "org.firstpair.dng-xmp/typo"]
        log = self.command("unknown-profile", command, dict(os.environ, UNISON=str(state)), expected_exit=None)
        assert "Unknown semantic profile: org.firstpair.dng-xmp/typo" in log
        assert (left / "image.dng").read_bytes() == contents and not list(right.iterdir())
        self.cases.append({"name": "unknown explicit profile rejected before transfer"})

    def two_remote_rejection(self, name, servers):
        """Observe the existing public CLI contract; do not bypass its guard."""
        directory = self.work / name
        directory.mkdir()
        left,right,state = (directory / item for item in ("left","right","state"))
        for path in (left,right,state):
            path.mkdir()
        before = fixture()
        source = left / "image.dng"
        source.write_bytes(before)
        inode = source.stat().st_ino
        launcher = directory / "loopback.py"
        mapping = {"fixture-left":str(servers[0]),"fixture-right":str(servers[1])}
        launcher.write_text("#!/usr/bin/env python3\nimport os,sys\n"
            "mapping=" + repr(mapping) + "\nargs=sys.argv[1:]\n"
            "host=next(x for x in args if x in mapping)\ni=args.index('unison-fixture-server')\n"
            "os.execv(mapping[host],[mapping[host]]+args[i+1:])\n")
        launcher.chmod(0o700)
        command = [str(self.current / "src/unison"),"ssh://fixture-left/"+str(left),
                   "ssh://fixture-right/"+str(right),"-sshcmd",str(launcher),
                   "-servercmd","unison-fixture-server","-batch","-auto","-semanticdng"]
        log = self.command(name,command,dict(os.environ,UNISON=str(state)),expected_exit=None)
        assert "cannot synchronize more than one remote root" in log
        assert "Remote semantic clone wrote" not in log
        assert source.read_bytes()==before and source.stat().st_ino==inode
        assert {path.name for path in left.iterdir()}=={"image.dng"}
        assert not list(right.iterdir())
        self.usage_rejections.append({"name":name,"diagnostic":"cannot synchronize more than one remote root",
                                      "source_bytes_and_inode_preserved":True,"target_empty":True,
                                      "limits":"expected public CLI rejection before negotiation; no two-remote transfer proof"})

    def run(self):
        new, old = self.current / "src/unison", self.old / "src/unison"
        self.preferences()
        for big in (False, True):
            for little in (True, False):
                for camera in (False, True):
                    label = ("big" if big else "classic") + ("-le" if little else "-be") + ("-cr" if camera else "")
                    self.exercise("new-alias-" + label, new, (None, new), ["-semanticdng"],
                                  [(label, {"big": big, "little": little, "camera": camera}, V1)])
        self.exercise("new-explicit-v1", new, (None, new), ["-semanticprofile", V1],
                      [("big-cr", {"big": True, "camera": True}, V1)])
        for label, parameters, profile in (("classic", {}, V0), ("big", {"big": True}, None),
                                           ("cr", {"camera": True}, None)):
            self.exercise("new-explicit-v0-" + label, new, (None, new), ["-semanticprofile", V0],
                          [(label, parameters, profile)])
        for policy, options in (("alias", ["-semanticdng"]),
                                ("mixed", ["-semanticprofile", V0, "-semanticprofile", V1]),
                                ("v1-only", ["-semanticprofile", V1])):
            for label, parameters in (("classic", {}), ("big-cr", {"big": True, "camera": True})):
                profile = V0 if policy != "v1-only" and label == "classic" else None
                self.exercise("old-server-" + policy + "-" + label, new, (None, old), options,
                              [(label, parameters, profile)])
        self.exercise("old-client-new-server", old, (None, new), ["-semanticdng"], [("classic", {}, V0)])
        if self.other:
            version = self.command("other-compiler-version",[str(self.other),"-version"],dict(os.environ))
            self.other_peer = {"binary":str(self.other),"sha256":sha(self.other),"version":version.strip()}
            for label,parameters in (("classic-cr",{"camera":True}),
                                     ("big-cr",{"big":True,"camera":True})):
                self.exercise("mixed-compiler-"+label,new,(None,self.other),["-semanticdng"],
                              [(label,parameters,V1)])
        for order, servers in (("new-first", (new, old)), ("old-first", (old, new))):
            self.two_remote_rejection("two-remote-"+order,servers)
        self.typo()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current-build", required=True, type=Path)
    parser.add_argument("--v0-build", required=True, type=Path)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--other-unison",type=Path,
                        help="optional current /1 peer built by the other compiler")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    current, old = args.current_build.resolve(), args.v0_build.resolve()
    other = args.other_unison.resolve() if args.other_unison else None
    if other is not None and not other.is_file():
        parser.error("other compiler peer missing: "+str(other))
    for build in (current, old):
        if not (build / "src/unison").is_file():
            parser.error("snapshot binary missing: " + str(build))
    for relative in ("src/semanticFormats.ml", "src/dngExtended.ml", "src/dngExtended.mli",
                     "src/dngSemantic.ml", "src/dngSemantic.mli", "src/Makefile.OCaml",
                     "src/ubase/prefs.ml", "src/ubase/prefs.mli"):
        if sha(current / relative) != sha(ROOT / relative):
            parser.error("current snapshot source differs: " + relative)
    work = Path(tempfile.mkdtemp(prefix="unison-dng-v1-routing-", dir="/private/tmp"))
    print("Retained qualification work:", work, flush=True)
    qualification = Qualification(current, old, Path(compiler).resolve(), work,other)
    if other:
        qualification.pins[str(other)]=sha(other)
    for path in (Path(__file__).resolve(), HERE / "dng_profile_v1_preferences.ml",
                 HERE / "test_positional_sync.py", ROOT / "bench/sync/ownership.py",
                 ROOT / "bench/sync/measure.py", Path(compiler).resolve()):
        qualification.pins[str(path)] = sha(path)
        if path.is_relative_to(ROOT):
            target = work / "sources" / path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(path.read_bytes())
            qualification.retained_sources[str(path)] = {"path":str(target),"sha256":sha(target)}
    for build in (current, old):
        for relative in ("src/unison", "src/dngSemantic.ml", "src/dngSemantic.mli",
                         "src/semanticFormats.ml", "src/Makefile.OCaml",
                         "src/ubase/prefs.ml", "src/ubase/prefs.mli"):
            qualification.pins[str(build / relative)] = sha(build / relative)
    for relative in ("src/dngExtended.ml", "src/dngExtended.mli"):
        qualification.pins[str(current / relative)] = sha(current / relative)
    try:
        qualification.run()
        status = "passed"
    except BaseException as error:
        status = "failed"
        (work / "failure.txt").write_text(repr(error) + "\n")
        raise
    finally:
        receipt = {"status": status, "work": str(work), "current_build": str(current),
                   "v0_build": str(old), "compiler": str(Path(compiler).resolve()),
                   "other_compiler_peer":qualification.other_peer,
                   "pins": qualification.pins, "cases": qualification.cases,
                   "retained_sources": qualification.retained_sources,
                   "case_count": len(qualification.cases), "commands": qualification.commands,
                   "command_count": len(qualification.commands),
                   "usage_rejections": qualification.usage_rejections,
                   "expected_usage_rejection_count": len(qualification.usage_rejections),
                   "limits": ["synthetic finite TIFF fixtures; no DNG validity/rendering or SDK proof",
                              "two-remote roots are rejected by production CLI; both feature orders are wire-boundary controls only",
                              "one CPU worker per endpoint; no all-core or physical-I/O performance claim",
                              "owned group signaling precedes leader reap; wait4 follows platform semantics"]}
        target = args.report.resolve() if args.report else work / "qualification.json"
        target.write_text(json.dumps(receipt, indent=2) + "\n")
        print("Receipt:", target, "status:", status, "cases:", len(qualification.cases), flush=True)


if __name__ == "__main__":
    main()
