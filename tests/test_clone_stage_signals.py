#!/usr/bin/env python3
"""Qualify clone-stage path-buffer cleanup at a pending-signal boundary.

Build only private copies of the production stub. A flagged synthetic source
declines before cloning; this does not qualify successful-result asynchronous
ownership transfer. The negative control restores the old runtime release call.
"""

import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import tempfile


HELPERS = r"""
#include <dirent.h>
#include <signal.h>
#include <caml/signals.h>

static void *test_allocations[16];
static int test_live_allocations;
static int test_signal_injected;

static void *test_track(void *pointer)
{
  if (!pointer) return pointer;
  for (int i = 0; i < 16; i++) {
    if (!test_allocations[i]) {
      test_allocations[i] = pointer;
      test_live_allocations++;
      return pointer;
    }
  }
  abort();
}

static char *test_strdup(const char *text)
{
  return test_track(strdup(text));
}

static void *test_malloc(size_t size)
{
  return test_track(malloc(size));
}

static void *test_scratch_malloc(size_t size)
{
  void *pointer = test_malloc(size);
  if (pointer) {
    if (test_signal_injected) abort();
    test_signal_injected = 1;
    /* The OS handler records a pending OCaml signal while all three path
     * buffers are owned. No OCaml callback or hand-written unwind is used. */
    if (raise(SIGUSR1)) abort();
  }
  return pointer;
}

static void test_free(void *pointer)
{
  if (!pointer) return;
  for (int i = 0; i < 16; i++) {
    if (test_allocations[i] == pointer) {
      test_allocations[i] = NULL;
      test_live_allocations--;
      free(pointer);
      return;
    }
  }
  abort();
}

CAMLprim value test_live_buffers(value unit)
{
  return Val_int(test_live_allocations);
}

CAMLprim value test_open_descriptors(value unit)
{
  DIR *directory = opendir("/dev/fd");
  struct dirent *entry;
  int count = 0;
  if (!directory) return Val_int(-1);
  int own = dirfd(directory);
  while ((entry = readdir(directory))) {
    char *end;
    long descriptor = strtol(entry->d_name, &end, 10);
    if (end != entry->d_name && *end == '\0' && descriptor != own)
      count++;
  }
  closedir(directory);
  return Val_int(count);
}

CAMLprim value test_dispatch_pending(value unit)
{
  CAMLparam1(unit);
  caml_process_pending_actions();
  CAMLreturn(Val_unit);
}

"""

HARNESS = r"""
(* This fixture creates no threads/domains. Its signal counter is deliberately
   local to that single execution context. *)
[@@@alert "-unsafe_multidomain"]

let with_async_exns f = f ()

type decline =
  | Platform_unavailable | Non_regular_source | Source_flags
  | Cross_device | Operation_unsupported
type stage_result =
  | Shared_stage of (Unix.file_descr * Unix.file_descr)
  | Declined_stage of decline

external clone_stage : string -> string -> stage_result = "unison_clone_stage_status"
external live_buffers : unit -> int = "test_live_buffers" [@@noalloc]
external open_descriptors : unit -> int = "test_open_descriptors" [@@noalloc]
external dispatch_pending : unit -> unit = "test_dispatch_pending"

let () =
  let mode = Sys.argv.(1) in
  let delivered = ref 0 in
  let saw_break = ref false in
  Sys.set_signal Sys.sigusr1
    (Sys.Signal_handle (fun _ -> incr delivered; raise Sys.Break));
  let before = open_descriptors () in
  if before < 0 then failwith "cannot enumerate fixture descriptors";
  (try
     with_async_exns (fun () ->
       match clone_stage Sys.argv.(2) Sys.argv.(3) with
       | Declined_stage Source_flags -> ()
       | Declined_stage _ -> failwith "wrong native decline"
       | Shared_stage (basis, stage) ->
           Unix.close basis; Unix.close stage;
           failwith "flagged fixture unexpectedly cloned")
   with Sys.Break -> saw_break := true);
  (* A corrected no-pending boundary may defer delivery until after the C
     result returns. Explicitly poll so scheduling cannot hide a lost signal. *)
  (try with_async_exns dispatch_pending with Sys.Break -> saw_break := true);
  Sys.set_signal Sys.sigusr1 Sys.Signal_ignore;
  let after = open_descriptors () in
  let live = live_buffers () in
  if not !saw_break || !delivered <> 1 then
    failwith "pending Sys.Break was lost or delivered more than once";
  if after <> before then failwith "native descriptors escaped the declined stage";
  if mode = "fixed" then (
    if live <> 0 then failwith "pending signal abandoned native path buffers"
  ) else if mode = "negative" then (
    if live <> 3 then failwith "old release boundary did not expose its three-buffer leak"
  ) else failwith "unknown fixture mode";
  Printf.printf "%s: signal=%d live_buffers=%d descriptors=%d->%d\n%!"
    mode !delivered live before after
"""


def instrument(source, *, negative):
    start = source.index("static value unsn_clone_stage_impl(")
    end = source.index("\nCAMLprim value unison_clone_stage(", start)
    body = source[start:end]
    boundary = r"\bcaml_enter_blocking_section_no_pending\s*\(\s*\)\s*;"
    if len(re.findall(boundary, body)) != 1:
        raise AssertionError("production stage must have exactly one no-pending entry")
    if "caml_process_pending_actions();" not in body:
        raise AssertionError("production stage must dispatch before native ownership")
    for name in ("strdup", "malloc", "free"):
        body = re.sub(r"\b" + name + r"\(", "test_" + name + "(", body)
    body, injected = re.subn(r"scratch\s*=\s*test_malloc\(",
                             "scratch = test_scratch_malloc(", body)
    if injected != 1:
        raise AssertionError("scratch allocation injection point changed")
    if negative:
        body = re.sub(boundary, "caml_release_runtime_system();", body)
    return source[:start] + HELPERS + body + source[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocamlopt", required=True)
    args = parser.parse_args()
    if platform.system() != "Darwin":
        print("SKIP: native clone-stage signal fixture requires macOS")
        return
    compiler = shutil.which(args.ocamlopt)
    if compiler is None:
        parser.error("native compiler unavailable")
    environment = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        environment.pop(name, None)
    root = Path(__file__).resolve().parent.parent
    original = (root / "src/copy_stubs.c").read_bytes()
    print("source src/copy_stubs.c " + hashlib.sha256(original).hexdigest(), flush=True)
    version = subprocess.check_output([compiler, "-version"], env=environment, text=True).strip()
    print("Compiler " + version, flush=True)
    # Ox delivers asynchronous Sys.Break to an explicitly installed async
    # boundary, rather than ordinary try handlers inside the interrupted code.
    # Use that documented API when exported by this compiler's Sys interface.
    library = Path(subprocess.check_output([compiler, "-where"], env=environment, text=True).strip())
    harness = HARNESS
    if "val with_async_exns" in (library / "sys.mli").read_text():
        harness = harness.replace("let with_async_exns f = f ()",
                                  "let with_async_exns = Sys.with_async_exns")

    with tempfile.TemporaryDirectory(prefix="unison-clone-signals-", dir="/private/tmp") as tmp:
        work = Path(tmp)
        payload = bytes(range(256)) * 8
        source = work / "source"
        source.write_bytes(payload)
        source.chmod(0o400)
        os.chflags(source, stat.UF_NODUMP)
        before = source.stat()
        try:
            for mode in ("fixed", "negative"):
                build = work / mode
                build.mkdir()
                (build / "copy_stubs.c").write_text(
                    instrument(original.decode(), negative=(mode == "negative")))
                (build / "signals.ml").write_text(harness)
                subprocess.run([compiler, "-I", "+unix", "-c", "copy_stubs.c"],
                               cwd=build, env=environment, check=True)
                subprocess.run([compiler, "-I", "+unix", "unix.cmxa", "copy_stubs.o",
                                "signals.ml", "-o", "signals"],
                               cwd=build, env=environment, check=True)
                destination = work / (mode + "-stage")
                subprocess.run([str(build / "signals"), mode, str(source), str(destination)],
                               cwd=build, env=environment, check=True, timeout=10)
                assert not destination.exists(), "declined operation left a stage"
                assert not list(work.glob("*.basis.*")), "declined operation left a basis"
                after = source.stat()
                for attribute in ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid",
                                  "st_size", "st_flags", "st_mtime_ns", "st_ctime_ns"):
                    assert getattr(before, attribute) == getattr(after, attribute), attribute
                assert source.read_bytes() == payload, "fixture source was changed"
        finally:
            os.chflags(source, 0)
    print("Pending-signal path-buffer cleanup qualified; old boundary reproduced its leak")


if __name__ == "__main__":
    main()
