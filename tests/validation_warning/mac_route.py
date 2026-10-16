#!/usr/bin/env python3
"""Test verbatim macOS warning routing with private OCaml/Foundation-only sinks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PARENT = "31980e3d286f5b7a408613faf7a983dc37d1f017"
SOURCES = ("src/uimacbridge.ml", "src/uimac/MyController.m")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(source, begin, end):
    if source.count(begin) != 1:
        raise RuntimeError("source extraction anchor must occur exactly once: " + begin)
    first = source.index(begin)
    last = source.index(end, first)
    return source[first:last]


ML_PRELUDE = r'''
module Prefs = struct let read value = !value end
module Globals = struct let batch = ref false end
module Util = struct let warnPrinter : (string -> unit) option ref = ref None end
module Trace = struct
  let logging = ref false
  let calls = ref []
  let log message = if !logging then calls := !calls @ [message]
end
let panels = ref []
let statuses = ref []
let unlocks = ref 0
let displayWarnPanel message = panels := !panels @ [message]; false
let displayStatus message = statuses := !statuses @ [message]
module Lwt_unix = struct let run value = value end
module Update = struct let unlockArchives () = incr unlocks end
module Uicommon = struct let fatalExit = 55 end
'''


ML_ORACLE = r'''
let warning = "Adobe DNG validation warning for /private/tmp/reconitems.dng: child failed"
let require name condition =
  if not condition then (Printf.eprintf "FAIL oracle: %s\n%!" name; exit 1)
let run_case name batch logging =
  Globals.batch := batch; Trace.logging := logging;
  Trace.calls := []; panels := []; statuses := []; unlocks := 0;
  setWarnPrinter ();
  (match !Util.warnPrinter with None -> failwith "missing actual warning printer"
   | Some printer -> printer warning);
  if batch then begin
    require "mac-batch-warning-exact" (!statuses = ["Warning: " ^ warning]);
    require "mac-batch-no-panel" (!panels = [])
  end else begin
    require "mac-interactive-panel-exact" (!panels = [warning]);
    require "mac-interactive-no-status" (!statuses = [])
  end;
  require "mac-no-unlock-on-proceed" (!unlocks = 0);
  require "mac-log-policy" (!Trace.calls =
    (if logging then ["Warning: " ^ warning ^ "\n"] else []));
  Printf.printf "PASS mac-route %s\n%!" name
let () =
  match Array.to_list Sys.argv with
  | [_] ->
      run_case "batch-log-disabled" true false;
      run_case "batch-log-enabled" true true;
      run_case "interactive-log-disabled" false false;
      run_case "interactive-log-enabled" false true
  | [_; "batch-log-disabled"] -> run_case "batch-log-disabled" true false
  | _ -> failwith "unexpected route fixture arguments"
'''


OBJC_PRELUDE = r'''
#import <Foundation/Foundation.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

@interface MockText : NSObject {
@public NSMutableArray *values;
}
- (void)setStringValue:(NSString *)value;
@end
@implementation MockText
- (id)init { self = [super init]; if (self) values = [NSMutableArray new]; return self; }
- (void)setStringValue:(NSString *)value { [values addObject:value]; }
- (void)dealloc { [values release]; [super dealloc]; }
@end

@interface SourceController : NSObject {
@public MockText *statusText;
}
- (void)statusTextSet:(NSString *)value;
@end
@implementation SourceController
'''


OBJC_ORACLE = r'''
@end
static void require(const char *name, BOOL condition) {
  if (!condition) { fprintf(stderr, "FAIL oracle: %s\n", name); exit(1); }
}
static void run_case(SourceController *controller, const char *name,
                     NSString *message, BOOL expected) {
  [controller->statusText->values removeAllObjects];
  [controller statusTextSet:message];
  NSArray *wanted = expected ? [NSArray arrayWithObject:message] : [NSArray array];
  require(name, [controller->statusText->values isEqualToArray:wanted]);
  printf("PASS mac-filter %s\n", name);
}
int main(int argc, const char **argv) {
  @autoreleasepool {
    SourceController *controller = [SourceController new];
    controller->statusText = [MockText new];
    run_case(controller, "mac-filter-warning-marker-exact",
      @"Warning: Adobe DNG validation warning for /private/tmp/reconitems.dng: child failed", YES);
    if (argc == 1) {
      run_case(controller, "normal-reconitems-filtered", @"There are 2 reconitems", NO);
      run_case(controller, "ordinary-status-exact", @"ordinary status", YES);
      run_case(controller, "warning-without-marker-exact", @"Warning: child failed", YES);
      run_case(controller, "embedded-warning-prefix-filtered", @"note Warning: reconitems", NO);
      run_case(controller, "lowercase-warning-prefix-filtered", @"warning: reconitems", NO);
    } else {
      require("mac-filter-fixture-argument", argc == 2 && strcmp(argv[1], "warning-marker") == 0);
    }
    [controller->statusText release];
    [controller release];
  }
  return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--ocamlopt", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("the Foundation-only native filter fixture requires macOS")
    compiler = Path(shutil.which(args.ocamlopt) or args.ocamlopt).resolve()
    clang = Path(shutil.which("clang") or "/usr/bin/clang").resolve()
    build = args.build.resolve()
    for name in SOURCES:
        if not (build / name).is_file() or sha(build / name) != sha(ROOT / name):
            raise RuntimeError("snapshot and workspace source differ: " + name)
    if not (build / "src/unison").is_file():
        raise RuntimeError("complete build snapshot required")
    current = {name: (build / name).read_text() for name in SOURCES}
    work = Path(tempfile.mkdtemp(prefix="unison-validation-warning-mac-route-", dir="/private/tmp"))
    env = os.environ.copy()
    for name in ("OCAMLLIB", "OCAMLPATH", "CAML_LD_LIBRARY_PATH", "OCAMLRUNPARAM"):
        env.pop(name, None)
    receipt = {
        "schema": "unison-validation-warning-mac-source-route/0",
        "success": False, "work": str(work), "retained": True,
        "parent": PARENT, "build_snapshot": str(build),
        "build_binary": {"path": str(build / "src/unison"), "sha256": sha(build / "src/unison")},
        "source_pins": {name: sha(build / name) for name in SOURCES},
        "test_pin": {"path": str(Path(__file__).resolve()), "sha256": sha(Path(__file__))},
        "compiler": {"path": str(compiler), "sha256": sha(compiler)},
        "clang": {"path": str(clang), "sha256": sha(clang)},
        "commands": [], "runs": [], "extractions": {},
        "controls": {"ocaml_routes": 4, "objective_c_filters": 6, "designated_negatives": 2},
        "scope": "Verbatim setWarnPrinter with private mocked OCaml sinks and verbatim statusTextSet with a Foundation-only mock text sink.",
        "limits": ["No full bridge/app linkage or GUI initialization", "No AppKit/UI creation or paint observation", "Status-field transience and user-observed visibility unqualified", "No worker/helper/publication integration qualification from this fixture"],
        "Photo_or_Adobe_access": False,
    }

    def command(argv, directory, label, *, failure_oracle=None):
        log = directory / (label + ".log")
        try:
            result = subprocess.run([str(arg) for arg in argv], cwd=directory, env=env,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        except subprocess.TimeoutExpired as error:
            output = error.stdout or b""
            log.write_text(output.decode(errors="replace") if isinstance(output, bytes) else output)
            receipt["commands"].append({"argv": [str(arg) for arg in argv], "cwd": str(directory),
                "timeout": 30, "log": str(log), "log_sha256": sha(log)})
            raise
        log.write_text(result.stdout)
        entry = {"argv": [str(arg) for arg in argv], "cwd": str(directory), "exit": result.returncode,
            "log": str(log), "log_sha256": sha(log)}
        receipt["commands"].append(entry)
        if failure_oracle is None:
            result.check_returncode()
        elif result.returncode != 1 or "FAIL oracle: " + failure_oracle not in result.stdout:
            raise RuntimeError("negative control missed designated independent oracle: " + label)
        return result, entry

    try:
        receipt["compiler"]["version"] = command([compiler, "-version"], work, "compiler-version")[0].stdout.strip()
        receipt["clang"]["version"] = command([clang, "--version"], work, "clang-version")[0].stdout.strip()
        parent = {}
        for name in SOURCES:
            result, _ = command(["git", "-C", str(ROOT), "show", PARENT + ":" + name], work, "parent-" + Path(name).name.replace(".", "-"))
            parent[name] = result.stdout
        for mode, inputs in (("current", current), ("parent", parent)):
            directory = work / mode
            directory.mkdir()
            for name, source in inputs.items():
                (directory / Path(name).name).write_text(source)
            ml = extract(inputs[SOURCES[0]], "let setWarnPrinter() =", "\nlet doInOtherThread f =")
            objc = extract(inputs[SOURCES[1]], "- (void)statusTextSet:(NSString *)s {", "\n\n// Called from ocaml to display progress bar")
            ml_fragment = directory / "setWarnPrinter-extracted.ml"
            objc_fragment = directory / "statusTextSet-extracted.m"
            ml_fragment.write_text(ml)
            objc_fragment.write_text(objc)
            receipt["extractions"][mode] = {
                "full_sources": {name: sha(directory / Path(name).name) for name in SOURCES},
                "setWarnPrinter": {"path": str(ml_fragment), "sha256": sha(ml_fragment)},
                "statusTextSet": {"path": str(objc_fragment), "sha256": sha(objc_fragment)},
                "edits": "None; each extracted production definition is compiled verbatim inside private mocked context."}
            ml_test = directory / "mac_route_test.ml"
            objc_test = directory / "mac_filter_test.m"
            ml_test.write_text(ML_PRELUDE + ml + ML_ORACLE)
            objc_test.write_text(OBJC_PRELUDE + objc + OBJC_ORACLE)
            ml_binary = directory / "mac-route-test"
            objc_binary = directory / "mac-filter-test"
            command([compiler, ml_test.name, "-o", ml_binary.name], directory, "compile-ocaml")
            command([clang, "-Wall", "-Wextra", "-Werror", "-framework", "Foundation",
                objc_test.name, "-o", objc_binary.name], directory, "compile-foundation")
            if mode == "current":
                for binary, label, count in ((ml_binary, "fixed-ocaml-routes", 4), (objc_binary, "fixed-objective-c-filters", 6)):
                    result, entry = command([binary], directory, label)
                    if len([line for line in result.stdout.splitlines() if line.startswith("PASS ")]) != count:
                        raise RuntimeError("fixed fixture control count mismatch: " + label)
                    receipt["runs"].append({"name": label, "mode": mode, "controls": count, **entry})
            else:
                for binary, arg, label, oracle in (
                    (ml_binary, "batch-log-disabled", "negative-old-batch-handler", "mac-batch-warning-exact"),
                    (objc_binary, "warning-marker", "negative-old-status-filter", "mac-filter-warning-marker-exact")):
                    _, entry = command([binary, arg], directory, label, failure_oracle=oracle)
                    receipt["runs"].append({"name": label, "mode": mode, "designated_oracle": oracle, **entry})
        receipt["success"] = True
        print("PASS mac warning source routes: 4 OCaml controls, 6 Foundation filter controls, 2 designated parent negatives")
    finally:
        receipt["artifacts"] = {str(path.relative_to(work)): {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}
            for path in sorted(work.rglob("*")) if path.is_file()}
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("Receipt:", args.receipt)


if __name__ == "__main__":
    main()
