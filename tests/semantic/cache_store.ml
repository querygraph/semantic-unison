module D=DngComponents
external mode : int -> unit = "unison_cache_control_mode"
external closes : unit -> int = "unison_cache_control_closes"
external syncs : unit -> int = "unison_cache_control_syncs"
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let invalid f=try ignore(f());false with ComponentHash.Invalid _ -> true
let ()=
 let baseline=Array.length(Sys.readdir "/dev/fd") in
 let parent_path=Filename.temp_file "cache-parent-owner-" "" in
 Sys.remove parent_path;Unix.mkdir parent_path 0o700;
 mode 0;let parent=D.open_cache_parent parent_path in
 ignore(D.cache_parent_descriptor parent);D.settle_cache_parent parent None;
 check(closes()=1) "normal async parent not closed once";
 check(invalid(fun () -> D.settle_cache_parent parent None)) "normal parent double close accepted";
 mode 0;let parent=D.open_cache_parent parent_path in
 let original=Failure "original-parent-operation" in mode 1;
 let failure=try D.settle_cache_parent parent (Some original);failwith "close EIO expected"
  with D.Cache_ownership_uncertain state -> state in
 check(D.cache_ownership_cause failure=Some original) "parent close lost original cause";
 check(List.length(D.cache_uncertain_descriptors failure)=1 && closes()=1)
  "parent close identity/retry differs";
 check(invalid(fun () -> D.settle_cache_parent parent None)) "uncertain parent close retried";
 mode 0;let parent=D.open_cache_parent parent_path in
 let descriptor=D.cache_parent_descriptor parent in
 let namespace=D.prepare_cache_namespace ~parent:descriptor () in
 D.provision_cache_namespace namespace ~parent:descriptor;
 mode 1;
 let nested=try D.with_cache_namespace namespace ~parent:descriptor ignore;
  failwith "namespace close EIO expected" with D.Cache_ownership_uncertain _ as error -> error in
 let retained=try D.settle_cache_parent parent (Some nested);failwith "nested carrier expected"
  with D.Cache_ownership_uncertain state -> state in
 check(closes()=1) "nested uncertainty closed known parent";
 check(List.length(D.cache_retained_descriptors retained)=1) "known async parent missing";
 List.iter(fun (fd,_) -> Unix.close fd)(D.cache_retained_descriptors retained);
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "async parent owner leaked known descriptor";
 let link=parent_path^"-link" in Unix.symlink parent_path link;
 check((try ignore(D.open_cache_parent link);false with Unix.Unix_error _ -> true)) "parent symlink followed";
 let source=Filename.temp_file "cache-store-input-" "" in
 let out=open_out_bin source in output_string out (String.make 128 's');close_out out;
 let fd=Unix.openfile source [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let checkpoint=SemanticFile.with_borrowed_fd fd (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:128L file
   {ComponentHash.id="dng";schema="dng-physical-partition/0";role=Structural;
    offset=0L;length=128L;children=[]}
   (fun session snapshot -> ComponentHash.checkpoint session snapshot)) in
 Unix.close fd;
 mode 0;let owner=D.open_component_source(fun () -> Unix.openfile source
  [Unix.O_RDONLY;Unix.O_CLOEXEC;Unix.O_NONBLOCK] 0) in
 ignore(D.component_source_descriptor owner);mode 1;
 let state=try D.settle_component_source owner None;failwith "source close EIO expected"
  with D.Cache_ownership_uncertain state -> state in
 check(closes()=1) "source close retried";
 check((match D.cache_origin_descriptor state with _,Some stat -> stat.Unix.LargeFile.st_kind=Unix.S_REG
  | _ -> false)) "source uncertainty lost regular-file identity";
 check(invalid(fun () -> D.settle_component_source owner None)) "uncertain source close replayed";
 check(Array.length(Sys.readdir "/dev/fd")=baseline) "disposable source fault leaked descriptor";
 let entry=D.make_owner_entry ~root_identity:"store-root" ~path:"one"
  ~generation_sha256:(SemanticHash.string "store-generation") ~checkpoint ~outcomes:[] in
 List.iter(fun ordinal ->
  let path=Filename.temp_file "cache-store-fault-" "" in Sys.remove path;Unix.mkdir path 0o700;
  let parent=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  mode 0;let namespace=D.prepare_cache_namespace ~parent () in
  D.provision_cache_namespace namespace ~parent;
  let store=D.prepare_managed_cache_store ~entry ~checkpoint
   ~index:(D.empty_owner_index ~max_entries:4 ~max_bytes:524288)
   ~expected_entry_sha256:None ~binding:(SemanticHash.string "store-binding")
   ~max_bytes:4194304L ~max_entries:2 in
  mode ordinal;
  let state=try ignore(D.execute_managed_cache_store store ~namespace ~parent);
   failwith "expected uncertain store close" with D.Cache_ownership_uncertain state -> state in
  check(closes()=ordinal) "uncertainty retried close or continued cleanup";
  check(List.length(D.cache_uncertain_descriptors state)=1) "uncertain descriptor missing";
  check(D.cache_ownership_cause state=None) "normal callback fabricated original failure";
  check(invalid(fun () -> D.managed_cache_store_reference store)) "uncertain store exposed reference";
  let reserved,record,entry,manifest,completed=D.managed_cache_store_effects store in
  check(reserved && record && entry && not completed) "uncertainty lost published effects";
  check(manifest=(ordinal>=3)) "manifest ran after earlier uncertainty";
  check(List.length(D.cache_retained_descriptors state)=(if ordinal=1 then 2 else if ordinal=4 then 0 else 1))
   "uncertainty lost known outer descriptors";
  (* Wrapper actually closed the uncertain FD before reporting EIO. Never retry
     its number. Only known retained descriptors are explicitly retired here. *)
  List.iter(fun (fd,_) -> Unix.close fd)(D.cache_retained_descriptors state);
  Unix.close parent;
  check(Array.length(Sys.readdir "/dev/fd")=baseline) "store failure leaked known descriptor") [1;2;3;4];
 let fresh ()=
  let path=Filename.temp_file "cache-store-operational-" "" in Sys.remove path;Unix.mkdir path 0o700;
  let parent=Unix.openfile path [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
  mode 0;let namespace=D.prepare_cache_namespace ~parent () in D.provision_cache_namespace namespace ~parent;
  let store=D.prepare_managed_cache_store ~entry ~checkpoint
   ~index:(D.empty_owner_index ~max_entries:4 ~max_bytes:524288)
   ~expected_entry_sha256:None ~binding:(SemanticHash.string "store-binding")
   ~max_bytes:4194304L ~max_entries:2 in parent,namespace,store in
 let parent,namespace,store=fresh () in mode 0;
 check(D.execute_managed_cache_store store ~namespace ~parent) "fault object normal store failed";
 let sync_count=syncs() in Unix.close parent;
 check(sync_count>2) "normal store did not sync publication";
 List.iter(fun injected ->
  let parent,namespace,store=fresh () in mode injected;
  let refused=try ignore(D.execute_managed_cache_store store ~namespace ~parent);false
   with Unix.Unix_error(Unix.EIO,_,_) -> true in
  check refused "injected store operation did not fail";
  check(invalid(fun () -> D.managed_cache_store_reference store)) "operational failure exposed reference";
  let _,_,_,_,complete=D.managed_cache_store_effects store in
  check(not complete) "operational failure completed store";
  check(invalid(fun () -> D.execute_managed_cache_store store ~namespace ~parent)) "failed store replay accepted";
  Unix.close parent;
  check(Array.length(Sys.readdir "/dev/fd")=baseline) "operational failure leaked descriptor")
  ([201;202;203;204] @ List.init sync_count (fun n ->100+n));
 Printf.printf "PASS %d composed store close-uncertainty checks; no reference/retry/false rollback\n%!" !checks
