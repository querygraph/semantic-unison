#!/usr/bin/env python3
"""Build the 2724 validator or an isolated 2768 fixture writer on macOS.

No Adobe source is copied into this repository. SDK notices remain in place.
The official Xcode source manifests are consumed without requiring Xcode.app.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from object_cache import compile_object
from sdk_source_identity import require_release

parser = argparse.ArgumentParser()
parser.add_argument("--sdk-root", type=Path, required=True)
parser.add_argument("--build-dir", type=Path, required=True)
parser.add_argument("--jobs", type=int, default=min(2, os.cpu_count() or 1))
parser.add_argument("--fixture-writer-build-only", action="store_true",
                    help="fresh SDK2768 fixture writer only; never builds or replaces a validator")
parser.add_argument("--fixture-only", action="store_true",
                    help="rebuild test fixture writer using existing SDK libraries; preserve validator and manifest")
parser.add_argument("--experimental-area-task-host", action="store_true",
                    help="build a separately named UNQUALIFIED capped area-task adapter; never replaces the qualified v1 driver")
parser.add_argument("--experimental-memory-budget", action="store_true",
                    help="build a separately named UNQUALIFIED host-allocation budget adapter")
args = parser.parse_args()
sdk = args.sdk_root.resolve()
build = args.build_dir.resolve()
here = Path(__file__).resolve().parent
if sys.platform != "darwin":
    parser.error("this qualified build currently supports macOS only")
if args.jobs < 1:
    parser.error("--jobs must be positive")
if args.fixture_writer_build_only and (args.fixture_only or args.experimental_area_task_host or args.experimental_memory_budget):
    parser.error("standalone fixture writer cannot select a validator or existing-driver mode")
if args.fixture_writer_build_only and args.jobs > 2:
    parser.error("standalone fixture writer permits at most two compiler jobs")
if args.fixture_only and (args.experimental_area_task_host or args.experimental_memory_budget):
    parser.error("--fixture-only cannot select an experimental validator build")
try:
    reviewed_sdk_release = require_release((sdk / "DNG_ReadMe.txt").read_text(), 2768 if args.fixture_writer_build_only else 2724)
except ValueError as error:
    parser.error(str(error))
if not (sdk / "LICENSE.txt").is_file():
    parser.error("SDK license missing")
if args.fixture_writer_build_only:
    if build.exists() or build.is_relative_to(sdk) or sdk.is_relative_to(build):
        parser.error("standalone fixture writer requires a fresh build directory disjoint from SDK source")
    build.mkdir(parents=True, exist_ok=False)
else:
    build.mkdir(parents=True, exist_ok=True)
preserved_manifest = None
if args.fixture_only:
    preserved_manifest = (build / "build-manifest.json").read_bytes()
    qualified = json.loads(preserved_manifest)
    if (qualified.get("sdk_root") != str(sdk) or
        hashlib.sha256((build / "unison-adobe-validator").read_bytes()).hexdigest() != qualified.get("executable_sha256")):
        parser.error("--fixture-only requires the matching existing driver manifest and executable pin")

def run(command):
    result = subprocess.run([str(s) for s in command], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    if result.returncode:
        print(result.stdout, file=sys.stderr)
        raise RuntimeError("command failed: " + " ".join(map(str, command)))
    return result.stdout

def sources(project, target):
    data = json.loads(run(["plutil", "-convert", "json", "-o", "-", project]))
    objects = data["objects"]
    base = project.parent.parent / objects[data["rootObject"]].get("projectDirPath", "")
    native = next(o for o in objects.values()
                  if o.get("isa") == "PBXNativeTarget" and o["name"] == target)
    result = []
    for phase in native["buildPhases"]:
        phase = objects[phase]
        if phase["isa"] == "PBXSourcesBuildPhase":
            for source in phase["files"]:
                item = objects[objects[source]["fileRef"]]
                path = (base / item["path"]).resolve()
                if not path.is_file():
                    raise RuntimeError("source manifest path missing: " + str(path))
                result.append(path)
    return result

jxl = build / "jxl"
if not args.fixture_only:
    print("Building bundled JPEG XL dependencies...", flush=True)
    run(["cmake", "-S", sdk / "libjxl/libjxl", "-B", jxl,
     "-DBUILD_TESTING=OFF", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_BUILD_TYPE=Release",
     "-DJPEGXL_ENABLE_TOOLS=OFF", "-DJPEGXL_ENABLE_EXAMPLES=OFF",
     "-DJPEGXL_ENABLE_BENCHMARK=OFF", "-DJPEGXL_ENABLE_MANPAGES=OFF",
     "-DJPEGXL_ENABLE_JNI=OFF", "-DJPEGXL_ENABLE_JPEGLI=OFF",
         "-DJPEGXL_ENABLE_SJPEG=OFF", "-DJPEGXL_ENABLE_OPENEXR=OFF"])
    run(["cmake", "--build", jxl, "--target", "jxl", "jxl_threads", "--parallel", args.jobs])

xmp = sdk / "xmp/toolkit"
dng = sdk / "dng_sdk/source"
common = ["-O2", "-DNDEBUG=1", "-DMAC_ENV=1", "-DXMP_StaticBuild=1", "-DXMP_64=1",
          "-DENABLE_CPP_DOM_MODEL=0", "-DXML_STATIC=1", "-DHAVE_EXPAT_CONFIG_H=1"]
includes = [dng, sdk / "libjpeg", xmp, xmp / "public/include",
            xmp / "third-party/expat/public/lib", xmp / "XMPCore/resource/mac",
            sdk / "libjxl/libjxl/lib/include", jxl / "lib/include",
            sdk / "libjxl/client_projects/include"]
common += [flag for path in includes for flag in ("-I", str(path))]
dng_flags = ["-DqDNGValidate=1", "-DqDNGValidateTarget=1", "-DqDNGReportErrors=1",
             "-DqDNGXMPFiles=0", "-DqDNGXMPDocOps=0", "-DqDNGUseLibJPEG=1",
             "-DqMacOS=1", "-DqWinOS=0", "-DqDNGUseStdInt=1", "-DMacintosh=1"]
xmp_flags = ["-DBUILDING_XMPCORE_LIB=1", "-DBUILDING_XMPCORE_AS_STATIC=1",
             "-DXMP_COMPONENT_INT_NAMESPACE=AdobeXMPCore_Int"]
dng_sources = sources(sdk / "dng_sdk/projects/mac/dng_validate.xcodeproj/project.pbxproj",
                      "dng_validate release")
dng_sources = [p for p in dng_sources if p.name != "dng_validate.cpp"]
xmp_sources = sources(xmp / "XMPCore/build/CMake64_libcpp_Static/XMPCore64.xcodeproj/project.pbxproj",
                      "XMPCoreStaticRelease")
jobs = [(p, dng_flags) for p in dng_sources] + [(p, xmp_flags) for p in xmp_sources]
if not args.fixture_only and not args.fixture_writer_build_only:
    driver_flags = dng_flags + (["-DUNISON_EXPERIMENTAL_AREA_TASK_HOST=1"]
                               if args.experimental_area_task_host else [])
    if args.experimental_memory_budget: driver_flags += ["-DUNISON_EXPERIMENTAL_MEMORY_BUDGET=1"]
    jobs.append((here / "driver.cpp", driver_flags))

def compile_one(job):
    source, flags = job
    signature = hashlib.sha256((str(source) + repr(common + flags)).encode()).hexdigest()[:16]
    obj = build / (source.stem + "-" + signature + ".o")
    cxx = source.suffix != ".c"
    options = list(common) + list(flags)
    if cxx:
        options += ["-std=c++17", "-funsigned-char", "-fno-common"]
    if source.name == "dng_exceptions.cpp":
        # Keep SDK implementation/notices untouched. Other SDK units still call
        # ReportError/Warning, which our driver counts and forwards to these.
        options += ["-DReportError=UnisonSdkReportError", "-DReportWarning=UnisonSdkReportWarning"]
    result, _ = compile_object("clang++" if cxx else "clang", options, source, obj, run)
    return result

print(f"Compiling {len(jobs)} SDK/driver units with {args.jobs} build workers...", flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
    objects = list(pool.map(compile_one, jobs))
libraries = [jxl / p for p in ["lib/libjxl.a", "lib/libjxl_cms.a", "lib/libjxl_threads.a",
    "third_party/highway/libhwy.a", "third_party/brotli/libbrotlienc.a",
    "third_party/brotli/libbrotlidec.a", "third_party/brotli/libbrotlicommon.a"]]
mode = ("area-memory" if args.experimental_area_task_host else "memory") if args.experimental_memory_budget else ("area" if args.experimental_area_task_host else "single")
binary = build / ("unison-adobe-validator" if mode == "single" else "unison-adobe-validator-" + mode + "-unqualified")
link_flags = [*libraries, "-lz", "-framework", "CoreFoundation", "-framework", "CoreServices",
              "-framework", "Security"]
if not args.fixture_only and not args.fixture_writer_build_only:
    run(["clang++", "-std=c++17", *objects, *link_flags, "-o", binary])
fixture_object = compile_one((here / "fixture_writer.cpp", dng_flags))
fixture_sdk_objects = objects if args.fixture_only or args.fixture_writer_build_only else objects[:-1]
run(["clang++", "-std=c++17", *fixture_sdk_objects, fixture_object, *link_flags,
     "-o", build / "fixture-writer"])
if args.fixture_writer_build_only:
    if (build / "build-manifest.json").exists() or any(p.name.startswith("unison-adobe-validator") for p in build.iterdir()):
        raise RuntimeError("standalone fixture build unexpectedly produced validator artifacts")
    fixture_binary = build / "fixture-writer"
    fixture_manifest = {
        "schema": "unison-sdk-fixture-writer-build/1",
        "sdk": "Adobe DNG SDK 1.7.1 build 2768",
        "sdk_root": str(sdk), "reviewed_release": reviewed_sdk_release,
        "sdk_readme_sha256": hashlib.sha256((sdk / "DNG_ReadMe.txt").read_bytes()).hexdigest(),
        "sdk_license_sha256": hashlib.sha256((sdk / "LICENSE.txt").read_bytes()).hexdigest(),
        "build_id": "unison-sdk171-2768-fixture-writer-build-v1",
        "executable": str(fixture_binary),
        "executable_sha256": hashlib.sha256(fixture_binary.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256((here / "fixture_writer.cpp").read_bytes()).hexdigest(),
        "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "release_selector_sha256": hashlib.sha256((here / "sdk_source_identity.py").read_bytes()).hexdigest(),
        "object_cache_sha256": hashlib.sha256((here / "object_cache.py").read_bytes()).hexdigest(),
        "linked_objects": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [*fixture_sdk_objects, fixture_object, *libraries]},
        "compiler_jobs": args.jobs, "validator_written": False,
        "runtime_qualified": False, "SDK_fixture_generation_calls": 0,
        "qualification": "BUILD ONLY: no fixture writer or validator invocation; separate native qualification required"
    }
    (build / "fixture-writer-build-manifest.json").write_text(json.dumps(fixture_manifest, indent=2) + "\n")
    print(json.dumps(fixture_manifest, indent=2))
    raise SystemExit(0)
if args.fixture_only:
    assert (build / "build-manifest.json").read_bytes() == preserved_manifest
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == qualified["executable_sha256"]
    print("Fixture writer rebuilt; qualified driver and manifest unchanged.")
    raise SystemExit(0)
digest = hashlib.sha256(binary.read_bytes()).hexdigest()
experimental = mode != "single"
manifest = {"sdk": "Adobe DNG SDK 1.7.1 build 2724", "reviewed_release": reviewed_sdk_release,
            "sdk_readme_sha256": hashlib.sha256((sdk / "DNG_ReadMe.txt").read_bytes()).hexdigest(),
            "sdk_license_sha256": hashlib.sha256((sdk / "LICENSE.txt").read_bytes()).hexdigest(),
            "release_selector_sha256": hashlib.sha256((here / "sdk_source_identity.py").read_bytes()).hexdigest(), "sdk_root": str(sdk),
            "sdk_license": str(sdk / "LICENSE.txt"), "executable": str(binary),
            "executable_sha256": digest, "build_id": {"single":"unison-sdk171-2724-v1-single", "area":"unison-sdk171-2724-v2-area-unqualified", "memory":"unison-sdk171-2724-v3-memory-unqualified", "area-memory":"unison-sdk171-2724-v3-area-memory-unqualified"}[mode],
            "source_sha256": hashlib.sha256((here / "driver.cpp").read_bytes()).hexdigest(),
            "adapter_headers_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (here / name for name in ("area_scheduler.h", "area_task_host.h", "memory_budget.h", "memory_allocator.h"))},
            "object_cache": {"implementation_sha256": hashlib.sha256((here / "object_cache.py").read_bytes()).hexdigest(),
                             "scope": "compiler/source/transitive-header/flag/environment/object content checks; not SDK runtime qualification"},
            "qualification": ("SOURCE ONLY: Adobe runtime and multithread mode unqualified"
                if experimental else "not yet tested; run qualify.py"),
            "threads": {"minimum": 1, "maximum": 128, "includes_caller": True}
                if args.experimental_area_task_host else 1,
            "protocol": {"single":"--unison-dng-validation-v1", "area":"--unison-dng-validation-area-source-v0", "memory":"--unison-dng-validation-memory-source-v0", "area-memory":"--unison-dng-validation-area-memory-source-v0"}[mode],
            "host_allocation_budget": "explicit --host-memory-bytes; not RSS/full-process memory" if args.experimental_memory_budget else None}
(build / ("build-manifest-" + mode + "-unqualified.json" if experimental else "build-manifest.json"))\
    .write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
