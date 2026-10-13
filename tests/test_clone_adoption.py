#!/usr/bin/env python3
"""Inject synchronous clone-descriptor handoff failures in production ML.

Requires a compiler-matched isolated Make build. Current production consumers
are compiled as private modules; only explicit failure hooks and FD observation
are added. Negative controls remove the handoff guards in those private copies.
All files, clones and generated modules live in a temporary directory.
"""
from pathlib import Path
import argparse
import os
import re
import subprocess
import tempfile


FAULT = r'''
exception Injected
let target = ref ""
let occurrence = ref 1
let count = ref 0
let oom = ref false
let captured : Unix.file_descr list ref = ref []
let hit phase =
  if phase = !target then begin
    incr count;
    if !count = !occurrence then
      if !oom then raise Out_of_memory else raise Injected
  end
let wrap phase f = hit phase; f ()
let resource label resource =
  let before = label ^ "-before" and after = label ^ "-after" in
  {resource with Remote.register = (fun value ->
    hit before;
    let result = resource.Remote.register value in
    hit after;
    result)}
let arm phase nth allocation =
  target := phase; occurrence := nth; count := 0; oom := allocation;
  captured := []
let disarm () = target := ""
'''

PREFIX = r'''
module Fs = struct
  include Fs
  let clone_stage_status source destination =
    let result = Fs.clone_stage_status source destination in
    begin match result with
    | Shared_stage (basis, output) ->
        AdoptionFault.captured := basis :: output :: !AdoptionFault.captured
    | Declined_stage _ -> ()
    end;
    result
  let openfile path flags mode =
    let fd = Fs.openfile path flags mode in
    AdoptionFault.captured := fd :: !AdoptionFault.captured;
    fd
end
'''

TEST = r'''
let closed fd =
  try ignore (Unix.fstat fd); false with Unix.Unix_error (Unix.EBADF,_,_) -> true
let directory = Fspath.canonize (Some (Sys.getcwd ()))
let path name = Fspath.concat directory (Path.fromString name)
let staging = Path.fromString "output"
let raw_stage () =
  write "output" (read "basis");
  let basis = Unix.openfile "basis" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  let output = Unix.openfile "output" [Unix.O_RDWR;Unix.O_CLOEXEC] 0 in
  AdoptionFault.captured := [basis;output];
  basis,output
let run mode = match mode with
  | "copy" | "copy-source" ->
      ignore (CopyForAdoption.copyLocalCloned (path "source") (path "basis")
        directory staging (Uutil.Filesize.ofInt (String.length (read "source"))) None)
  | "sync" ->
      ignore (SemanticSyncForAdoption.try_local ~source:(path "source")
        ~basis:(path "basis") ~directory ~staging)
  | "async" ->
      ignore (Lwt_unix.run (SemanticSyncForAdoption.try_local_async
        ~source:(path "source") ~basis:(path "basis") ~directory ~staging))
  | "candidate" ->
      let basis,output = raw_stage () in
      let candidate = SemanticRemoteForAdoption.register_candidate (path "output") basis output in
      SemanticRemoteForAdoption.candidates.release candidate
  | "held" ->
      let fd = Unix.openfile "basis" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
      AdoptionFault.captured := [fd];
      let files = SemanticRemoteForAdoption.register_held_fd fd in
      SemanticRemoteForAdoption.held_files.release files
  | _ -> failwith "unknown adoption mode"
let stages () =
  Array.to_list (Sys.readdir ".")
  |> List.filter (fun name -> name <> "basis" && name <> "source" &&
       name <> "sentinel" && name <> "state")
let () =
  let mode = Sys.argv.(1) and phase = Sys.argv.(2) in
  let nth = int_of_string Sys.argv.(3) and allocation = Sys.argv.(4) = "oom"
  and negative = Sys.argv.(5) = "negative" in
  Prefs.loadStrings ["semanticdng = true";"semanticworkers = 2"];
  Features.setEnabled (Features.all ());
  write "basis" (fixture ());
  write "source" (fixture ~xmp:"<x>two</x>      " ());
  write "sentinel" "fd-reuse-sentinel";
  let runtime = SemanticRuntime.get () in
  AdoptionFault.arm phase nth allocation;
  let rejected = try run mode; false with
    | AdoptionFault.Injected -> require (not allocation) "changed failure identity"; true
    | Out_of_memory -> require allocation "changed OOM identity"; true in
  AdoptionFault.disarm ();
  require rejected "failure hook did not fire";
  require (!AdoptionFault.captured <> []) "no real descriptor was observed";
  let leaked = List.filter (fun fd -> not (closed fd)) !AdoptionFault.captured in
  require (read "basis" = fixture ()) "handoff failure changed source basis";
  if negative then begin
    require (leaked <> []) "old-handoff negative control did not leak a descriptor";
    Printf.printf "PASS old-handoff leak reproduced: %s %s\n%!" mode phase
  end else begin
    require (leaked = []) "handoff failure leaked a descriptor";
    require (stages () = []) "handoff failure retained an owned stage";
    (* Reuse closed integers before registry cleanup: stale entries must refer
       to closed channels/records, never close these newly opened files. *)
    let sentinels = List.init 16 (fun _ ->
      Unix.openfile "sentinel" [Unix.O_RDONLY;Unix.O_CLOEXEC] 0) in
    require (List.exists (fun fd -> List.mem fd !AdoptionFault.captured) sentinels)
      "descriptor reuse control did not reuse a captured integer";
    Remote.clientCloseRootConnection (Common.Local,directory);
    List.iter (fun fd -> require (not (closed fd)) "registry cleanup closed a reused fd";
      Unix.close fd) sentinels;
    (* Direct follow-up uses the same production adoption path after cleanup. *)
    run mode;
    require (List.for_all closed !AdoptionFault.captured) "follow-up retained descriptors";
    if Sys.file_exists "output" then begin
      require (read "output" = read "source") "follow-up reconstructed wrong bytes";
      Sys.remove "output"
    end;
    require (stages () = []) "follow-up retained an owned stage";
    let usage = SemanticAdmission.usage runtime.admission in
    require (usage.transactions=0 && usage.pending=0 && usage.descriptors=0 && usage.payload_bytes=0)
      "handoff failure retained admission";
    require (HelperSupervisor.usage runtime.supervisor=(0,0)) "handoff failure retained CPU permits";
    Lwt_unix.run (SemanticWorkers.shutdown runtime.pool);
    Printf.printf "PASS guarded handoff: %s %s %s\n%!" mode phase Sys.argv.(4)
  end
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError(f"production hook is no longer unique: {old[:70]}")
    return source.replace(old, new, 1)


def instrument(repository, negative):
    copy = (repository / "src/copy.ml").read_text()
    sync = (repository / "src/semanticSync.ml").read_text()
    remote = (repository / "src/semanticRemote.ml").read_text().split("let nonce () =", 1)[0]
    # Candidate/holder functions are unchanged; do not register a second RPC.
    remote = re.sub(r"let request_plan = .*?(?=\ntype candidate =)", "", remote, flags=re.S)
    remote = replace_once(remote, '"semantic-delta-v0"', '"adoption-private-semantic-delta"')
    if negative:
        copy = re.sub(r"let cloneChannels basisFd outputFd =.*?(?=\nlet cloneOwnerIdentity)",
            "let cloneChannels basisFd outputFd =\n"
            "  let basis = inFdResource.register (Unix.in_channel_of_descr basisFd)\n"
            "  and output = outFdResource.register (Unix.out_channel_of_descr outputFd) in\n"
            "  (basis, output)\n", copy, flags=re.S)
        sync = re.sub(r"let register_transaction path basis_fd output_fd =.*?(?=\nlet retain_source_fd)",
            "let register_transaction path basis_fd output_fd =\n"
            "  transaction_resources.register\n"
            "    {path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=true}\n", sync, flags=re.S)
        sync = re.sub(r"let retain_source_fd transaction fd =.*?(?=\nlet with_borrowed)",
            "let retain_source_fd transaction fd =\n  transaction.fds <- fd :: transaction.fds\n", sync, flags=re.S)
        # Remove only the synchronous initialization guard, preserving its body.
        start = sync.index("      let close, cleanup, committed =")
        finish = sync.index("      try\n        let rec select", start)
        body = sync[start:finish]
        body = body.replace("        try\n", "", 1)
        body = body[:body.index("        with error ->")].rstrip() + " in\n"
        sync = sync[:start] + body + sync[finish:]
        remote = re.sub(r"let register_held_fd fd =.*?(?=\nlet borrowed)",
            "let register_held_fd fd = held_files.register (hold [fd])\n", remote, flags=re.S)
        remote = re.sub(r"let register_candidate path basis output =.*$",
            "let register_candidate path basis output =\n"
            "  candidates.register {basis;output;files=hold [basis;output];path;owned=true}\n", remote, flags=re.S)

    copy = copy.replace("Unix.out_channel_of_descr outputFd",
        'AdoptionFault.wrap "copy-output-create" (fun () -> Unix.out_channel_of_descr outputFd)')
    copy = copy.replace("Unix.in_channel_of_descr basisFd",
        'AdoptionFault.wrap "copy-input-create" (fun () -> Unix.in_channel_of_descr basisFd)')
    copy = replace_once(copy,
        "let inFdResource = Remote.resourceWithConnCleanup close_in close_in_noerr",
        'let inFdResource = AdoptionFault.resource "copy-input-register" '
        '(Remote.resourceWithConnCleanup close_in close_in_noerr)')
    copy = replace_once(copy,
        "let outFdResource = Remote.resourceWithConnCleanup close_out close_out_noerr",
        'let outFdResource = AdoptionFault.resource "copy-output-register" '
        '(Remote.resourceWithConnCleanup close_out close_out_noerr)')
    sync = replace_once(sync, "let closed = ref false and committed = ref false in",
        'let closed = AdoptionFault.wrap "sync-init" (fun () -> ref false) and committed = ref false in')
    sync = replace_once(sync,
        "let transaction_resources = Remote.resourceWithConnCleanup\n  cleanup_transaction cleanup_transaction_noerr",
        'let transaction_resources = AdoptionFault.resource "sync-register" '
        '(Remote.resourceWithConnCleanup cleanup_transaction cleanup_transaction_noerr)')
    record = "{path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=true}"
    sync = replace_once(sync, record, '(AdoptionFault.wrap "sync-record" (fun () -> ' + record + '))')
    retained = "fd :: transaction.fds" if negative else "fd :: previous"
    sync = replace_once(sync, retained, 'AdoptionFault.wrap "sync-retain" (fun () -> ' + retained + ')')
    remote = replace_once(remote,
        "let held_files = Remote.resourceWithConnCleanup close_files close_files_noerr",
        'let held_files = AdoptionFault.resource "remote-held-register" '
        '(Remote.resourceWithConnCleanup close_files close_files_noerr)')
    remote = replace_once(remote,
        "let hold descriptors = {descriptors;busy=false;closing=false;closed=false}",
        'let hold descriptors = AdoptionFault.wrap "remote-holder" (fun () -> '
        '{descriptors;busy=false;closing=false;closed=false})')
    remote = replace_once(remote,
        "let candidates = Remote.resourceWithConnCleanup cleanup cleanup_noerr",
        'let candidates = AdoptionFault.resource "remote-candidate-register" '
        '(Remote.resourceWithConnCleanup cleanup cleanup_noerr)')
    record = "{basis;output;files=hold [basis;output];path;owned=true}"
    remote = replace_once(remote, record, '(AdoptionFault.wrap "remote-record" (fun () -> ' + record + '))')
    return {"copyForAdoption": PREFIX + copy,
            "semanticSyncForAdoption": PREFIX + sync,
            "semanticRemoteForAdoption": PREFIX + remote}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path)
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    build = args.build.resolve() / "src"
    makefile = (build / "Makefile.OCaml").read_text()

    def objects(name):
        body = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S).group(1)
        body = body.replace("\\\n", " ").replace("$(SYSTEM)", "generic")
        body = body.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
        return body.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()

    modules = objects("OCAMLOBJS")
    modules = modules[:modules.index("copy.cmx")]
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]]
    flags += ["-I", "+unix", "-I", "+str"]
    compiler = os.environ.get("OCAMLOPT", "ocamlopt")
    cases = [("copy", "copy-output-create", 1), ("copy", "copy-input-create", 1)]
    cases += [("copy", f"copy-{kind}-register-{when}", 1)
              for kind in ("input", "output") for when in ("before", "after")]
    cases += [("copy-source", f"copy-input-register-{when}", 2) for when in ("before", "after")]
    cases += [("sync", "sync-init", 1), ("async", "sync-record", 1), ("async", "sync-retain", 1)]
    cases += [("async", f"sync-register-{when}", 1) for when in ("before", "after")]
    cases += [("candidate", phase, 1) for phase in ("remote-record", "remote-holder",
              "remote-candidate-register-before", "remote-candidate-register-after")]
    cases += [("held", phase, 1) for phase in ("remote-holder", "remote-held-register-before",
              "remote-held-register-after")]
    with tempfile.TemporaryDirectory(prefix="unison-clone-adoption-", dir="/private/tmp") as tmp:
        for negative in ([False, True] if args.negative_control else [False]):
            work = Path(tmp) / ("old" if negative else "current")
            work.mkdir()
            (work / "adoptionFault.ml").write_text(FAULT)
            sources = instrument(repository, negative)
            for name, source in sources.items():
                (work / (name + ".ml")).write_text(source)
            for name in ["adoptionFault"] + list(sources):
                subprocess.run([compiler] + flags + ["-c", name + ".ml"], cwd=work, check=True)
            fixture = (repository / "tests/semantic/test.ml").read_text().split("let () =", 1)[0]
            (work / "adoptionTest.ml").write_text(fixture + TEST)
            command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
            command += [str(build / obj) for obj in modules]
            command += [name + ".cmx" for name in ["adoptionFault"] + list(sources)]
            command += ["adoptionTest.ml"] + [str(build / obj) for obj in objects("COBJS")]
            subprocess.run(command + ["-o", "adoption-test"], cwd=work, check=True)
            for mode, phase, nth in cases:
                # The old local source registration path remains guarded by the
                # current producer; its prior native-adoption leaks are covered
                # separately. It is not a negative control for that adjacent fix.
                if negative and mode == "copy-source":
                    continue
                for allocation in ("failure", "oom"):
                    case = work / f"{mode}-{phase}-{nth}-{allocation}"
                    case.mkdir()
                    state = case / "state"
                    state.mkdir()
                    subprocess.run([str(work / "adoption-test"), mode, phase, str(nth), allocation,
                                    "negative" if negative else "current"], cwd=case,
                                   env=dict(os.environ, UNISON=str(state)), check=True, timeout=30)


if __name__ == "__main__":
    main()
