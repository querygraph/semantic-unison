#!/usr/bin/env python3
"""Fault-qualify production ML acquisition guards in private compiler snapshots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
ROOT=Path(__file__).resolve().parents[2]
OLD_GUARD_COMMIT="e9be47381d35af82d816b1f80df348ddf7409180"
SOURCES=[
 "src/lwt/lwt.mli","src/lwt/lwt.ml","src/lwt/pqueue.mli","src/lwt/pqueue.ml",
 "src/lwt/generic/lwt_unix_impl.ml","src/lwt/lwt_unix.mli","src/lwt/lwt_unix.ml",
 "src/borrowedWork.mli","src/borrowedWork.ml",
 "src/helperSupervisor_stubs.c","src/helperSupervisor.mli","src/helperSupervisor.ml",
 "src/semanticAdmission.mli","src/semanticAdmission.ml","src/ioAdmission.mli","src/ioAdmission.ml",
 "src/semanticHash_stubs.c","src/semanticHash.mli","src/semanticHash.ml",
 "src/semanticFile_stubs.c","src/semanticFile.mli","src/semanticFile.ml",
 "src/formatRecognition.mli","src/formatRecognition.ml",
 "src/formatExtension.mli","src/formatExtension.ml","src/xmpObservation.mli","src/xmpObservation.ml", "src/xmpMerge.mli", "src/xmpMerge.ml",
 "src/dngSemantic.mli","src/dngSemantic.ml","src/semanticDelta.mli","src/semanticDelta.ml",
 "tests/fd_ownership/fault.ml","src/semanticMailbox.mli", "src/semanticMailbox.ml", "src/semanticWorkers.mli","src/semanticWorkers.ml",
 "tests/fd_ownership/fixture.c","tests/fd_ownership/test.ml","tests/fd_ownership/run.py"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise AssertionError("fault seam not unique: "+a)
 return s.replace(a,b)
def section(source,start,end):
 a=source.index(start);b=source.index(end,a);return a,b,source[a:b]
def instrument_file(source):
 source=source.replace("Unix.in_channel_of_descr","Fault.channel")
 source=source.replace("close_in_noerr channel","Fault.close_channel_noerr channel")
 source=source.replace("close_in channel","Fault.close_channel channel")
 if "owned_channel := Some channel" in source:
  source=once(source,"owned_channel := Some channel",'(Fault.hit "semantic-channel-register"; owned_channel := Some channel)')
 return once(source,"let t = {channel;initial;check_cancel} in",'Fault.hit "semantic-record"; let t = {channel;initial;check_cancel} in')
def instrument_workers(source):
 if "(match Mailbox.push t.shared.jobs" in source:
  source=once(source,"(match Mailbox.push t.shared.jobs",'(Fault.hit "submit-mailbox"; match Mailbox.push t.shared.jobs')
 source=source.replace("Unix.close","Fault.close_fd")
 source=once(source,"Unix.set_nonblock read_fd;",'Fault.set_nonblock "pool-read-flags" read_fd;')
 source=once(source,"Unix.set_nonblock write_fd;",'Fault.set_nonblock "pool-write-flags" write_fd;')
 source=once(source,"let shared = { mutex = Mutex.create ();",'Fault.hit "pool-shared"; let shared = { mutex = Mutex.create ();')
 spawn="Domain.spawn (* ox-safe-worker-spawn *) (fun () -> worker shared ())" if "(* ox-safe-worker-spawn *)" in source else "Domain.spawn (worker shared)"
 source=once(source,spawn,'Domain.spawn (fun () -> Fault.adjust 1; Fun.protect ~finally:(fun () -> Fault.adjust (-1)) (fun () -> worker shared ()))')
 if "domains := domain :: !domains" in source:
  source=once(source,"domains := domain :: !domains",'(Fault.hit "pool-domain-link"; domains := domain :: !domains)')
 source=once(source,"let reader = Lwt_unix.of_unix_file_descr read_fd in",'Fault.hit "pool-reader"; let reader = Lwt_unix.of_unix_file_descr read_fd in')
 source=once(source,"let t = { shared; domains = !domains;",'Fault.hit "pool-record"; let t = { shared; domains = !domains;')
 source=once(source,"Lwt.ignore_result (pump t (Bytes.create 4096));",'Fault.hit "pool-pump"; Lwt.ignore_result (pump t (Bytes.create 4096));')
 source=once(source,"(try Apply (extension, plan, owned)",'(try Fault.hit "submit-operation"; Apply (extension, plan, owned)')
 source=once(source,"H.on_cancel cancellation stop",'(Fault.hit "submit-listener"; H.on_cancel cancellation stop)')
 source=once(source,"Lwt.ignore_result (monitor ());",'Fault.hit "submit-monitor"; Lwt.ignore_result (monitor ());')
 return once(source,"t.admission <- t.admission @ [id];",'Fault.hit "submit-admission"; t.admission <- t.admission @ [id];')
def command(argv,work,env,log):
 start=time.monotonic()
 with log.open("w") as out:r=subprocess.run(argv,cwd=work,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=90)
 text=log.read_text()
 if text.strip():print(text if r.returncode else text.strip().splitlines()[-1],flush=True)
 return {"argv":argv,"exit":r.returncode,"elapsed":time.monotonic()-start,"log":str(log),"sha256":sha(log)}
def main():
 p=argparse.ArgumentParser();p.add_argument("--ocamlopt",required=True);p.add_argument("--receipt",type=Path);p.add_argument("--fixed-only",action="store_true");a=p.parse_args()
 compiler=shutil.which(a.ocamlopt)
 if compiler is None:p.error("compiler unavailable")
 env=os.environ.copy()
 for name in ("OCAMLLIB","OCAMLPATH","CAML_LD_LIBRARY_PATH","OCAMLRUNPARAM"):env.pop(name,None)
 original={name:(ROOT/name).read_bytes() for name in SOURCES}
 old={name:subprocess.check_output(["git","show",OLD_GUARD_COMMIT+":"+name],cwd=ROOT).decode() for name in ("src/semanticFile.ml","src/semanticWorkers.ml")}
 work=Path(tempfile.mkdtemp(prefix="unison-early-fd-",dir="/private/tmp"));print("Retained",work,flush=True)
 receipt={"schema":"unison-early-fd-qualification/1","compiler":compiler,"compiler_version":subprocess.check_output([compiler,"-version"],text=True).strip(),"compiler_sha256":sha(Path(compiler)),"sources":{n:hashlib.sha256(d).hexdigest() for n,d in original.items()},"old_guard_commit":OLD_GUARD_COMMIT,"old_sources":{n:hashlib.sha256(d.encode()).hexdigest() for n,d in old.items()},"artifacts":str(work),"negative_representation_adapter":"Historical guard sections only: Queue allocation/enqueue and stop/counter representation adapted to current mailbox/atomic shared-record ABI; no acquisition/listener ownership guards changed", "runs":[]}
 for mode in (["fixed"] if a.fixed_only else ["fixed","old-file-channel","old-pool-pipe","old-submit-listener"]):
  build=work/mode;build.mkdir()
  for name,data in original.items():
   if name.endswith((".ml",".mli",".c")):(build/Path(name).name).write_bytes(data)
  f=original["src/semanticFile.ml"].decode();w=original["src/semanticWorkers.ml"].decode()
  if mode=="old-file-channel":
   x,y,_=section(f,"let with_fd ","let bounds ");_,_,previous=section(old["src/semanticFile.ml"],"let with_fd ","let bounds ");f=f[:x]+previous+f[y:]
  if mode in ("old-pool-pipe","old-submit-listener"):
   start,end=("let create_internal ","let create ~workers") if mode=="old-pool-pipe" else ("let submit ","let digest t ")
   x,y,_=section(w,start,end);_,_,previous=section(old["src/semanticWorkers.ml"],start,end);# Historical acquisition guards remain unchanged; adapt only the
   # queue representation needed by today's shared record/worker ABI.
   if mode=="old-pool-pipe":
    previous=previous.replace("shared.stopping <- true", "Atomic.set shared.stopping true").replace("stopping = false; running = 0; peak = 0", "stopping = Atomic.make false; running = Atomic.make 0; peak = Atomic.make 0")
    previous=previous.replace("jobs = Queue.create (); completions = Queue.create ();", "jobs = SemanticMailbox.create ~capacity:max_pending; completions = SemanticMailbox.create ~capacity:max_pending;")
   else:
    previous=previous.replace("Queue.add {id; fd = owned; cancelled; operation} t.shared.jobs;", "(match SemanticMailbox.push t.shared.jobs {id; fd = owned; cancelled; operation} with Added -> () | _ -> failwith \"historical queue adapter invariant\");")
   w=w[:x]+previous+w[y:]
  (build/"semanticFile.ml").write_text(instrument_file(f));(build/"semanticWorkers.ml").write_text(instrument_workers(w))
  fault=(build/"fault.ml").read_text();fault += '\nlet channel fd = hit "semantic-channel"; Unix.in_channel_of_descr fd\n';(build/"fault.ml").write_text(fault)
  order=[name for name in SOURCES if name.endswith((".c",".ml",".mli")) and Path(name).name!="test.ml"]
  order.remove("tests/fd_ownership/fault.ml");order.insert(order.index("src/semanticFile.mli"),"tests/fd_ownership/fault.ml")
  commands=[]
  for name in order:
   r=command([compiler,"-I","+unix","-c",Path(name).name],build,env,build/(Path(name).name+".compile.log"));commands.append(r)
   if r["exit"]:raise AssertionError("private production compilation failed")
  objects=[Path(n).stem+(".o" if n.endswith(".c") else ".cmx") for n in order if n.endswith((".c",".ml"))]
  r=command([compiler,"-I","+unix","unix.cmxa",*objects,"test.ml","-o","early-fd-test"],build,env,build/"link.log");commands.append(r)
  if r["exit"]:raise AssertionError("private link failed")
  files=build/"files";files.mkdir();case={"fixed":"all","old-file-channel":"semantic-channel","old-pool-pipe":"pool-read-flags","old-submit-listener":"submit-listener"}[mode]
  argv=[str(build/"early-fd-test"),str(files),case]
  if mode!="fixed":argv.append("negative")
  r=command(argv,build,env,build/"run.log")
  expected={"old-file-channel":"semantic owned duplicate escaped","old-pool-pipe":"pool pipe descriptors escaped","old-submit-listener":"submit owned duplicate escaped"}.get(mode)
  if mode=="fixed":
   if r["exit"]:raise AssertionError("fixed ownership controls failed")
  elif r["exit"]!=2 or expected not in (build/"run.log").read_text():raise AssertionError("negative did not expose designated kernel FD leak")
  receipt["runs"].append({"mode":mode,"commands":commands,"execution":r,"designated_negative":expected,"binary":str(build/"early-fd-test"),"binary_sha256":sha(build/"early-fd-test"),"build_files":{x.name:sha(x) for x in sorted(build.iterdir()) if x.is_file() and x.suffix in (".ml",".mli",".c",".cmx",".o")}})
 receipt["terminal"]="passed";destination=a.receipt or work/"qualification.json";destination.write_text(json.dumps(receipt,indent=2)+"\n");print("Receipt",destination,flush=True)
if __name__=="__main__":main()
