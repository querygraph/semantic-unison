"""One finite private cancellation-registration fault against production IO admission."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--compiler',required=True)
p.add_argument('--report',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
sources=['src/lwt/lwt.mli','src/lwt/lwt.ml','src/lwt/pqueue.mli','src/lwt/pqueue.ml',
'src/lwt/generic/lwt_unix_impl.ml','src/lwt/lwt_unix.mli','src/lwt/lwt_unix.ml',
'src/borrowedWork.mli','src/borrowedWork.ml','src/helperSupervisor_stubs.c',
'src/helperSupervisor.mli','src/helperSupervisor.ml','src/ioAdmission.mli','src/ioAdmission.ml']
w=Path(tempfile.mkdtemp(prefix='unison-io-registration-'));pins={}
for name in sources:
 b=(root/name).read_bytes();pins[name]=hashlib.sha256(b).hexdigest();(w/Path(name).name).write_bytes(b)
f=w/'helperSupervisor.ml';s=f.read_text();anchor='let on_cancel c notify =';assert s.count(anchor)==1
f.write_text(s.replace(anchor,'let registration_fault = ref false\nlet test_fail_registration () = registration_fault := true\nlet cancel_registration = ref false\nlet test_cancel_registration () = cancel_registration := true\n'+anchor+'\n  if !registration_fault then (registration_fault := false; raise Out_of_memory);\n  if !cancel_registration then (cancel_registration := false; cancel c);'))
s=f.read_text()
s='let unregister_fault = ref false\nlet test_fail_unregister () = unregister_fault := true\nlet test_unregister_consumed () = not !unregister_fault\n'+s
seam='listener.listening <- false;\n      c#state.listeners <- List.filter'
assert s.count(seam)==1
f.write_text(s.replace(seam,'listener.listening <- false;\n      if !unregister_fault then (unregister_fault := false; raise Out_of_memory);\n      c#state.listeners <- List.filter'))
with (w/'helperSupervisor.mli').open('a') as f:f.write('\nval test_fail_registration : unit -> unit\nval test_cancel_registration : unit -> unit\nval test_fail_unregister : unit -> unit\nval test_unregister_consumed : unit -> bool\n')
(w/'test.ml').write_text('''open Lwt
let check b s = if not b then failwith s
let () =
 let t=IoAdmission.create ~per_device:1 ~max_pending:2 in
 let release=Lwt.wait () in
 let active=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1] (fun () -> release) in
 HelperSupervisor.test_fail_registration ();
 let entered=ref false in
 let raised=try ignore(IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1]
   (fun () -> entered:=true;return ()));false with Out_of_memory -> true in
 check raised "registration failure not injected";
 check ((IoAdmission.usage t).pending=0) "registration failure published unreachable IO ticket";
 HelperSupervisor.test_cancel_registration ();
 let cancelled=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1]
   (fun () -> entered:=true;return ()) in
 check (Lwt_unix.run cancelled=None && (IoAdmission.usage t).pending=0)
   "immediate registration cancellation was published";
 Lwt.wakeup release (); ignore(Lwt_unix.run active);
 ignore(Lwt_unix.run(Lwt_unix.sleep 0.02));
 check (not !entered && (IoAdmission.usage t).active_jobs=0) "failed IO owner later acquired credits";
 check (Lwt_unix.run(IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1]
   (fun () -> return 7))=Some 7) "registration failure poisoned later IO work";
 let release2=Lwt.wait () in
 let active2=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1] (fun () -> release2) in
 let queued=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1] (fun () -> return 9) in
 HelperSupervisor.test_fail_unregister ();
 let failed=try Lwt.wakeup release2 (); ignore(Lwt_unix.run active2);
   ignore(Lwt_unix.run(Lwt_unix.sleep 0.02));false with Out_of_memory -> true in
 check (not failed && Lwt.poll queued=Some(Some 9)) "unregister failure lost granted IO owner";
 check (HelperSupervisor.test_unregister_consumed ()) "unregister failure was not injected";
 check ((IoAdmission.usage t).active_jobs=0 && (IoAdmission.usage t).pending=0)
   "unregister failure leaked IO credit";
 let release3=Lwt.wait () and cancellation=HelperSupervisor.cancellation () in
 let active3=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1] (fun () -> release3) in
 let cancelled=IoAdmission.with_devices t cancellation ~devices:[1]
   (fun () -> failwith "cancelled IO callback started") in
 let sibling=IoAdmission.with_devices t (HelperSupervisor.cancellation ()) ~devices:[1] (fun () -> return 11) in
 HelperSupervisor.test_fail_unregister (); HelperSupervisor.cancel cancellation;
 check (HelperSupervisor.test_unregister_consumed ()) "cancel unregister failure was not injected";
 check (Lwt.poll cancelled=Some None && (IoAdmission.usage t).pending=1)
   "unregister failure lost cancelled IO reply or sibling";
 Lwt.wakeup release3 (); ignore(Lwt_unix.run active3);
 check (Lwt_unix.run sibling=Some 11) "cancel unregister failure stranded later IO owner";
 check ((IoAdmission.usage t).active_jobs=0 && (IoAdmission.usage t).pending=0)
   "cancel unregister failure leaked IO credits";
 print_endline "PASS registration, grant-unregister and cancellation-unregister controls"


''')
log=w/'control.log'
with log.open('w') as out:
 for name in sources:subprocess.run([a.compiler,'-I','+unix','-c',Path(name).name],cwd=w,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=20)
 objs=[Path(n).stem+('.o' if n.endswith('.c') else '.cmx') for n in sources if n.endswith(('.c','.ml'))]
 subprocess.run([a.compiler,'-I','+unix','unix.cmxa',*objs,'test.ml','-o','control'],cwd=w,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=20)
 r=subprocess.run([str(w/'control')],cwd=w,stdout=out,stderr=subprocess.STDOUT,timeout=10)
a.report.write_text(json.dumps({'passed':r.returncode==0,'exit_code':r.returncode,'workspace':str(w),
 'source_pins':pins,'compiler':a.compiler,'log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
 'scope':'finite original registration/unregister OOM; synthetic owner-loop promises; no SDK/Photo/native IO'},indent=2)+'\n')
print(log.read_text(),end='');raise SystemExit(r.returncode)
