#!/usr/bin/env python3
"""Exercise semantic producer handoffs with actual workers and disposable FDs.

An isolated private copy of each production implementation supplies narrow
failure hooks. The remote ownership unit uses in-process delivery of its real
source planner, encoding/decoding and materializer; transport qualification is
separate. Native staging and final producer adoption remain actual code. No
Adobe tools, photos, catalogs, caches or preview operations are used.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PREFIX = r'''
module HandoffFault = struct
  exception Injected
  let target=ref ""
  let captured : Unix.file_descr list ref = ref []
  let hit phase=if phase= !target then
    if phase="register-release-before" || phase="publication-release-before"
    then raise Out_of_memory else raise Injected
  let wrap phase f=hit phase; f ()
  let resource phase resource={resource with Remote.register=(fun value ->
    hit (phase ^ "-before"); let value=resource.Remote.register value in
    hit (phase ^ "-after"); value);
    Remote.release_noerr=(fun value->hit (phase ^ "-release-before");resource.Remote.release_noerr value)}
end
module Fs = struct
  include Fs
  let clone_stage_handles basis stage=
    let result=Fs.clone_stage_handles basis stage in
    (match result with Shared_stage_handles (basis,output,parent) ->
      HandoffFault.captured:=basis::output::!(HandoffFault.captured)
    | Declined_stage_handles _ -> ()); result
  let openfile path flags mode=
    let fd=Fs.openfile path flags mode in
    fd
end
module StagePublication = struct
  include StagePublication
  let adopt context ~parent ~stage=
    StagePublication.adopt context ~parent ~stage;
    HandoffFault.hit "adopt-after"
  let adopt_owned context ~parent ~stage=
    StagePublication.adopt_owned context ~parent ~stage;
    HandoffFault.hit "adopt-after"
end
'''

HARNESS = r'''
module S = SemanticSyncForHandoff
module R = SemanticRemoteForHandoff
module P = FinalPublicationForHandoff
external count_fds : unit -> int = "final_publication_fixture_fd_count" [@@noalloc]
external attribute_fault : int -> int -> unit = "stage_publication_fixture_attribute_fault"
let closed fd=try ignore(Unix.fstat fd);false with Unix.Unix_error(Unix.EBADF,_,_)->true
let count=ref 0 and serial=ref 0
let test name body=(try body() with error -> Printf.eprintf "FAIL %s\n%!" name;raise error);
  incr count;Printf.printf "PASS %s\n%!" name
let rec remove path=match(Unix.lstat path).Unix.st_kind with
  | Unix.S_DIR -> Array.iter(fun name->remove(Filename.concat path name))(Sys.readdir path);Unix.rmdir path
  | _ -> Unix.unlink path
  | exception Unix.Unix_error(Unix.ENOENT,_,_) -> ()
let exists path=try ignore(Unix.lstat path);true with Unix.Unix_error(Unix.ENOENT,_,_)->false
let expect expected body=match body() with
  | _ -> failwith "expected handoff rejection"
  | exception error -> if not(expected error) then raise error
let marker=Failure "original producer callback failure"
let unix_marker=Unix.Unix_error(Unix.EIO,"producer callback","fixture")
let transient=function Util.Transient _->true|_->false
let case_fixture top body=
  incr serial;let directory_name=Filename.concat top("case-" ^ string_of_int !serial) in
  Unix.mkdir directory_name 0o700;
  let directory=Fspath.canonize(Some directory_name) in
  let path name=Fspath.concat directory(Path.fromString name) in
  let native name=Filename.concat directory_name name in
  let original=fixture() and incoming=fixture ~xmp:"<x>two</x>      " () in
  write(native "basis") original;write(native "source") incoming;
  write(native "live") "OLD LIVE";write(native "sentinel") "REUSE SENTINEL";
  let before=count_fds() in
  let owner=P.prepare ~logical_root:directory_name ~working_dir:directory_name
    ~candidate:"normal" ~target:"live" ~check_apple_double:false in
  let callbacks=ref 0 and output=ref None in
  let producer descriptor=
    incr callbacks;output:=Some descriptor;
    require(not(closed descriptor)) "actual output was closed before producer callback";
    let held=Unix.LargeFile.fstat descriptor and named=Unix.LargeFile.lstat(native "normal") in
    require(held.Unix.LargeFile.st_dev=named.Unix.LargeFile.st_dev && held.st_ino=named.st_ino)
      "callback descriptor does not denote promoted output";
    require(read(native "normal")=incoming) "callback observed incorrect semantic bytes";
    P.adopt_mutable owner ~candidate:descriptor;
    P.check_producer_fd owner ~candidate:descriptor in
  Fun.protect ~finally:(fun()->attribute_fault 0 0;P.close_noerr owner;
    S.HandoffFault.target:="";R.HandoffFault.target:="";
    Remote.clientCloseRootConnection(Common.Local,directory);
    remove directory_name;remove(directory_name ^ ".held"))
    (fun()->
      body directory path native original incoming owner callbacks output producer;
      P.release owner;
      let actual_directory=if exists(directory_name ^ ".held") then directory_name ^ ".held" else directory_name in
      require(read(Filename.concat actual_directory "basis")=original) "semantic handoff modified live basis";
      require(read(Filename.concat actual_directory "source")=incoming) "semantic handoff modified source";
      require(count_fds()=before) "semantic producer fixture leaked descriptors")
let run local directory path callback=
  if local then S.try_local_async_with_producer ~producer:callback ~source:(path "source")
    ~basis:(path "basis") ~directory ~staging:(Path.fromString "normal")
  else R.try_transfer_with_producer ~producer:callback ~connection:(Obj.magic 0)
    ~source:(path "source") ~basis:(path "basis") ~directory
    ~staging:(Path.fromString "normal") ~expected_size:8192L
let captured local=if local then !(S.HandoffFault.captured) else !(R.HandoffFault.captured)
let reset local=if local then S.HandoffFault.captured:=[] else R.HandoffFault.captured:=[]
let fault local phase=if local then S.HandoffFault.target:=phase else R.HandoffFault.target:=phase
let reused_descriptor descriptor native directory=
  let replacement=Unix.openfile(native "sentinel")[Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  if replacement<>descriptor then begin Unix.dup2 replacement descriptor;Unix.close replacement end;
  Fun.protect ~finally:(fun()->Unix.close descriptor)(fun()->
    Remote.clientCloseRootConnection(Common.Local,directory);
    require(not(closed descriptor)) "retained cleanup closed a reused descriptor";
    let bytes=Bytes.create 14 in
    require(Unix.read descriptor bytes 0 14=14 && Bytes.to_string bytes="REUSE SENTINEL")
      "retained cleanup affected descriptor reuse")
let ()=
  let top=Sys.argv.(1) in
  if not(StagePublication.available() && P.available()) then exit 77;
  Prefs.loadStrings["semanticdng = true";"semanticworkers = 2"];
  Features.setEnabled(Features.all());
  let runtime=SemanticRuntime.get() in
  List.iter(fun local->
    let label=if local then "local" else "remote planner" in
    test(label ^ " actual output adoption survives semantic close and final publication") (fun()->
      case_fixture top(fun directory path native _ incoming owner callbacks output producer ->
        reset local;
        require(Lwt_unix.run(run local directory path producer)) "bound semantic fixture declined";
        require(!callbacks=1) "producer was omitted or repeated";
        List.iter(fun fd->require(closed fd) "semantic transaction retained a raw descriptor")(captured local);
        (match !output with Some fd->require(closed fd) "producer output retained after handoff"|_->assert false);
        P.check_producer owner;P.freeze_producer owner;P.check_candidate owner;
        P.observe_target owner;P.publish owner;P.check_published owner;
        require(read(native "live")=incoming && not(exists(native "normal"))) "retained producer did not publish exact bytes"));
    List.iter(fun error->test(label ^ " original callback exception is terminal") (fun()->
      case_fixture top(fun directory path native _ _ _ callbacks _ producer ->
        reset local;
        expect(fun actual->actual==error)(fun()->ignore(Lwt_unix.run(run local directory path
          (fun fd->producer fd;raise error))));
        require(!callbacks=1) "failed producer callback repeated";
        require(not(exists(native "normal")) && read(native "live")="OLD LIVE") "failed callback exposed output";
        List.iter(fun fd->require(closed fd) "callback failure retained raw fd")(captured local))))
      [marker;unix_marker;Out_of_memory];
    test(label ^ " callback replacement sentinel is preserved by captured owner") (fun()->
      case_fixture top(fun directory path native _ incoming _ _ _ _ ->
        reset local;
        expect(fun error->error==marker)(fun()->ignore(Lwt_unix.run(run local directory path(fun fd->
          require(not(closed fd)) "callback output closed";
          Unix.rename(native "normal")(native "normal.moved");write(native "normal") "FOREIGN";raise marker))));
        require(read(native "normal")="FOREIGN" && read(native "normal.moved")=incoming) "foreign replacement was deleted";
        require(read(native "live")="OLD LIVE") "replacement failure changed live"));
    test(label ^ " callback parent rebound cleans only captured original namespace") (fun()->
      case_fixture top(fun directory path native _ _ _ _ _ _ ->
        reset local;
        let root=Fspath.toString directory in
        expect(fun error->error==marker)(fun()->ignore(Lwt_unix.run(run local directory path(fun _ ->
          Unix.rename root(root ^ ".held");Unix.mkdir root 0o700;write(native "normal") "FOREIGN";raise marker))));
        require(read(native "normal")="FOREIGN") "rebound namespace sentinel removed";
        require(not(exists(Filename.concat(root ^ ".held")"normal"))) "captured owned output survived callback failure";
        require(read(Filename.concat(root ^ ".held")"live")="OLD LIVE") "callback failure changed held live"));
    List.iter(fun phase->test(label ^ " adopted stage settles " ^ phase ^ " failure") (fun()->
      case_fixture top(fun directory path native _ _ _ callbacks _ producer ->
        reset local;fault local phase;
        let expected=if local then S.HandoffFault.Injected else R.HandoffFault.Injected in
        expect(fun error->error==expected)(fun()->ignore(Lwt_unix.run(run local directory path producer)));
        fault local "";
        require(!callbacks=0 && not(exists(native "normal"))) "pre-callback failure promoted output";
        List.iter(fun fd->require(closed fd) "handoff allocation/register failure leaked fd")(captured local);
        require(Array.length(Sys.readdir(Fspath.toString directory))=4) "adopted private stage leaked")))
      ["adopt-after";"record";"register-before";"register-after"];
    List.iter(fun phase->test(label ^ " unregister OOM closes witnesses and preserves callback exception") (fun()->
      case_fixture top(fun directory path native _ _ _ callbacks _ producer ->
        reset local;fault local phase;
        expect(fun error->error==marker)(fun()->ignore(Lwt_unix.run(run local directory path(fun descriptor->
          producer descriptor;raise marker))));
        fault local "";
        require(!callbacks=1 && not(exists(native "normal"))) "unregister failure retained an owned normal name";
        List.iter(fun fd->require(closed fd) "unregister failure retained a raw descriptor")(captured local);
        reused_descriptor(List.nth(captured local)1)native directory)))
      ["publication-release-before";"register-release-before"];
    test(label ^ " initial native identity unavailability declines before creation") (fun()->
      case_fixture top(fun directory path native _ _ _ callbacks _ producer ->
        reset local;attribute_fault 13 1;
        require(not(Lwt_unix.run(run local directory path producer))) "unavailable preparation was accepted";
        attribute_fault 0 0;
        require(!callbacks=0 && captured local=[]) "unavailable preparation created a native stage";
        require(not(exists(native "normal"))) "unavailable preparation exposed output"));
    test(label ^ " ineligible opaque change falls back without producer handoff") (fun()->
      case_fixture top(fun directory path native _ incoming _ callbacks _ producer ->
        write(native "source")(fixture ~opaque:'Z' ~xmp:"<x>two</x>      " ());reset local;
        require(not(Lwt_unix.run(run local directory path producer))) "opaque change incorrectly accepted";
        require(!callbacks=0 && not(exists(native "normal"))) "ineligible plan reached producer";
        write(native "source")incoming));
  ) [true;false];
  test "local cleanup waits for a borrowed stage before closing or unlinking" (fun()->
    case_fixture top(fun directory path native _ _ _ _ _ _ ->
      let stage=Path.fromString "pending-stage" in
      let transaction,publication,_,output=match S.create_bound_transaction (S.create_publication_scope()) ~basis:(path "basis") ~directory
        ~staging:(Path.fromString "normal") stage(path "pending-stage") with Some x->x|None->failwith "stage declined" in
      let pending=Lwt.wait() in
      let work=S.with_publication_borrowed(Some publication)transaction(fun()->pending) in
      Remote.clientCloseRootConnection(Common.Local,directory);
      require(not(closed output) && exists(native "pending-stage")) "disconnect closed borrowed output too early";
      Lwt.wakeup pending();expect transient(fun()->ignore(Lwt_unix.run work));
      require(closed output && not(exists(native "pending-stage"))) "settled borrowed stage was retained"));
  test "remote cleanup waits for a borrowed stage before closing or unlinking" (fun()->
    case_fixture top(fun directory path native _ _ _ _ _ _ ->
      let stage=Path.fromString "pending-stage" in
      let candidate,publication=match R.create_bound_candidate (R.create_publication_scope()) ~basis:(path "basis") ~directory
        ~staging:(Path.fromString "normal") stage(path "pending-stage") with Some x->x|None->failwith "stage declined" in
      let pending=Lwt.wait() in
      let work=R.borrowed_with_publication(Some publication)candidate(fun()->pending) in
      Remote.clientCloseRootConnection(Common.Local,directory);
      require(not(closed candidate.output) && exists(native "pending-stage")) "disconnect closed borrowed output too early";
      Lwt.wakeup pending();expect transient(fun()->ignore(Lwt_unix.run work));
      require(closed candidate.output && not(exists(native "pending-stage"))) "settled borrowed stage was retained"));
  test "local unregister OOM defers borrowed FD and name cleanup and later reuse is safe" (fun()->
    case_fixture top(fun directory path native _ _ _ _ _ _ ->
      let stage=Path.fromString "pending-stage" in
      let transaction,publication,_,output=match S.create_bound_transaction (S.create_publication_scope()) ~basis:(path "basis") ~directory
        ~staging:(Path.fromString "normal") stage(path "pending-stage") with Some x->x|None->failwith "stage declined" in
      let pending=Lwt.wait() in
      let work=S.with_publication_borrowed(Some publication)transaction(fun()->pending) in
      fault true "publication-release-before";S.release_publication_noerr publication;
      fault true "register-release-before";S.release_transaction_noerr transaction;fault true "";
      require(not(closed output) && exists(native "pending-stage")) "unregister OOM prematurely closed borrowed local stage";
      Lwt.wakeup pending();expect transient(fun()->ignore(Lwt_unix.run work));
      require(closed output && not(exists(native "pending-stage"))) "unregister OOM retained settled local stage";
      reused_descriptor output native directory));
  test "remote unregister OOM defers borrowed FD and name cleanup and later reuse is safe" (fun()->
    case_fixture top(fun directory path native _ _ _ _ _ _ ->
      let stage=Path.fromString "pending-stage" in
      let candidate,publication=match R.create_bound_candidate (R.create_publication_scope()) ~basis:(path "basis") ~directory
        ~staging:(Path.fromString "normal") stage(path "pending-stage") with Some x->x|None->failwith "stage declined" in
      let pending=Lwt.wait() in
      let work=R.borrowed_with_publication(Some publication)candidate(fun()->pending) in
      fault false "publication-release-before";R.release_publication_noerr publication;
      fault false "register-release-before";R.release_candidate_noerr candidate;fault false "";
      require(not(closed candidate.output) && exists(native "pending-stage")) "unregister OOM prematurely closed borrowed remote stage";
      Lwt.wakeup pending();expect transient(fun()->ignore(Lwt_unix.run work));
      require(closed candidate.output && not(exists(native "pending-stage"))) "unregister OOM retained settled remote stage";
      reused_descriptor candidate.output native directory));
  let usage=SemanticAdmission.usage runtime.admission in
  require(usage.transactions=0 && usage.pending=0 && usage.descriptors=0 && usage.payload_bytes=0) "semantic admission leaked";
  require(HelperSupervisor.usage runtime.supervisor=(0,0)) "semantic CPU permits leaked";
  Lwt_unix.run(SemanticWorkers.shutdown runtime.pool);
  Printf.printf "Semantic producer handoff: %d cases passed; remote transport is separate\n%!" !count
'''

def replace_once(source,old,new):
    if source.count(old)!=1:
        raise AssertionError('handoff seam changed: '+old[:90])
    return source.replace(old,new,1)

def instrument(source,local):
    source=replace_once(source,'let publications = Remote.resourceWithConnCleanup\n  close_publication close_publication_noerr',
        'let publications = HandoffFault.resource "publication" (Remote.resourceWithConnCleanup close_publication close_publication_noerr)')
    if local:
        source=replace_once(source,'let transaction_resources = Remote.resourceWithConnCleanup\n  cleanup_transaction cleanup_transaction_noerr',
            'let transaction_resources = HandoffFault.resource "register" (Remote.resourceWithConnCleanup cleanup_transaction cleanup_transaction_noerr)')
        source=replace_once(source,'{path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=false;publication_pending=false;retained=false}',
            'HandoffFault.wrap "record" (fun () -> {path;fds=[basis_fd;output_fd];busy=false;abandoned=false;owned=false;publication_pending=false;retained=false})')
    else:
        source=replace_once(source,'let candidates = Remote.resourceWithConnCleanup cleanup cleanup_noerr',
            'let candidates = HandoffFault.resource "register" (Remote.resourceWithConnCleanup cleanup cleanup_noerr)')
        source=replace_once(source,'{basis;output;files=hold [basis;output];path;owned=false}',
            'HandoffFault.wrap "record" (fun () -> {basis;output;files=hold [basis;output];path;owned=false})')
        source=replace_once(source,'let supported connection =\n  SemanticFormats.peer_enabled () <> [] && Remote.connectionVersion connection >= 1 &&\n  Features.enabled transport',
            'let supported _ = SemanticFormats.peer_enabled () <> [] && Features.enabled transport')
        source=replace_once(source,'~maxArgs:request_limit ~maxResult:response_limit args result make_plan',
            '~maxArgs:request_limit ~maxResult:response_limit args result make_plan\nlet request_plan connection args = make_plan connection args')
    return PREFIX+source

def objects(make,name):
    match=re.search(r'^'+name+r' = (.*?)(?=\n\n)',make,re.M|re.S)
    return match.group(1).replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    parser.add_argument('--ocamlopt',required=True)
    parser.add_argument('--keep-work',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];src=args.build.resolve()/'src'
    environment=os.environ.copy()
    for name in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):
        environment.pop(name,None)
    work=Path(tempfile.mkdtemp(prefix='unison-semantic-handoff-',dir='/private/tmp'))
    print('work',work,flush=True)
    try:
        for name,local in [('semanticSync',True),('semanticRemote',False)]:
            data=(root/'src'/f'{name}.ml').read_bytes()
            print('source',name,hashlib.sha256(data).hexdigest(),flush=True)
            (work/f'{name}ForHandoff.ml').write_text(instrument(data.decode(),local))
        for name in ['finalPublication.ml','finalPublication.mli','finalPublication_stubs.c','stagePublication_stubs.c']:
            shutil.copy2(root/'src'/name,work/name)
        (work/'finalPublicationForHandoff.ml').write_bytes((work/'finalPublication.ml').read_bytes())
        for source,name in [('tests/final_publication/fixture.c','finalFixture.c'),('tests/stage_publication/fixture.c','stageFixture.c')]:
            shutil.copy2(root/source,work/name)
        fixture=(root/'tests/semantic/test.ml').read_text().split('let () =',1)[0]
        (work/'handoffTest.ml').write_text(fixture+HARNESS)
        state=work/'state';state.mkdir();environment['UNISON']=str(state)
        includes=[src,src/'lwt',src/'ubase',src/'system',src/'system/generic',src/'lwt/generic']
        flags=[value for p in includes for value in ['-I',str(p)]]+['-I','+unix','-I','+str']
        make=(src/'Makefile.OCaml').read_text();modules=objects(make,'OCAMLOBJS')
        modules=modules[:modules.index('semanticSync.cmx')]
        if 'stagePublication.cmx' not in modules:
            modules.append('stagePublication.cmx')
        for name in ['stagePublication.ml','stagePublication.mli','semanticWorkers.mli','semanticDelta.mli','fs.mli']:
            assert (src/name).read_bytes()==(root/'src'/name).read_bytes(), name+' dependency differs from snapshot'
        cobjects=[name for name in objects(make,'COBJS') if name not in ('stagePublication_stubs.o','finalPublication_stubs.o')]
        print('Compiler',subprocess.check_output([args.ocamlopt,'-version'],env=environment,text=True).strip(),flush=True)
        with (work/'build.log').open('w+') as log:
            try:
                for name in ['stageFixture.c','finalFixture.c','finalPublicationForHandoff.ml','semanticSyncForHandoff.ml','semanticRemoteForHandoff.ml']:
                    subprocess.run([args.ocamlopt,*flags,'-c',name],cwd=work,env=environment,stdout=log,stderr=log,check=True)
                subprocess.run([args.ocamlopt,*flags,'unix.cmxa','str.cmxa',*[str(src/name) for name in modules],
                    'finalPublicationForHandoff.cmx','semanticSyncForHandoff.cmx','semanticRemoteForHandoff.cmx','handoffTest.ml',
                    *[str(src/name) for name in cobjects],'stageFixture.o','finalFixture.o','-o','semantic-handoff-test'],
                    cwd=work,env=environment,stdout=log,stderr=log,check=True)
            except subprocess.CalledProcessError:
                log.seek(0);print(log.read());raise
        fixtures=work/'fixtures';fixtures.mkdir()
        result=subprocess.run([str(work/'semantic-handoff-test'),str(fixtures)],cwd=work,env=environment,
            text=True,capture_output=True,timeout=60)
        (work/'test.log').write_text(result.stdout+result.stderr)
        print(result.stdout,end='');print(result.stderr,end='')
        if result.returncode==77:
            print('SKIP native semantic handoff requires macOS 10.12+')
        else:
            result.check_returncode()
    finally:
        if not args.keep_work:
            shutil.rmtree(work)

if __name__=='__main__':
    main()
