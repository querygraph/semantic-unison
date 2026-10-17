module D=DngComponents
external mode : int -> unit = "unison_cache_control_mode"
external closes : unit -> int = "unison_cache_control_closes"
external opens : unit -> int = "unison_cache_control_opens"
external syncs : unit -> int = "unison_cache_control_syncs"
let checks=ref 0
let check yes why=incr checks;if not yes then failwith why
let refused f=try ignore(f());false with Unix.Unix_error _ -> true
let invalid f=try ignore(f());false with Invalid_argument _ -> true
let root ()=let p=Filename.temp_file "cache-namespace-" "" in Sys.remove p;Unix.mkdir p 0o700;
 p,Unix.openfile p [Unix.O_RDONLY;Unix.O_CLOEXEC] 0
let identity fd=let s=Unix.fstat fd in s.Unix.st_dev,s.st_ino
let child p=Filename.concat p D.cache_namespace_name
let uncertain f=try ignore(f());failwith "expected retained ownership"
 with D.Cache_ownership_uncertain state -> state
let write p bytes=let oc=open_out_gen [Open_wronly;Open_creat;Open_excl;Open_binary] 0o600 p in
 output_string oc bytes;close_out oc
let ()=
 let start=Array.length(Sys.readdir "/dev/fd") in
 let p,parent=root () in let baseline=Array.length(Sys.readdir "/dev/fd") in
 let census ()=check(Array.length(Sys.readdir "/dev/fd")=baseline) "namespace FD leak" in
 mode 0;
 let ticket=D.prepare_cache_namespace ~parent () in
 check(not(D.cache_namespace_created ticket) && invalid(fun () -> D.cache_namespace_identity ticket))
  "preparation claimed creation/identity";
 D.provision_cache_namespace ticket ~parent;
 let id=D.cache_namespace_identity ticket in
 check(D.cache_namespace_created ticket && (Unix.lstat(child p)).Unix.st_perm land 0o7777=0o700)
  "fresh namespace missing/private mode differs";
 check(syncs()=1) "fresh creation did not sync parent once";
 let first=D.with_cache_namespace ticket ~parent (fun directory ->
  check(identity directory=id) "opened namespace identity differs";
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(ComponentHash.reserve_metadata_slot q directory) "initial namespace quota unavailable";
  ComponentHash.metadata_slot_name q) in
 check(opens()=1 && closes()=1) "namespace normal open/close count differs";census();
 check(invalid(fun () -> D.provision_cache_namespace ticket ~parent)) "provision replay accepted";
 check(invalid(fun () -> D.with_cache_namespace ticket ~parent ignore)) "scoped open replay accepted";
 let reopen ()=let t=D.prepare_cache_namespace ~expected:id ~parent () in
  D.provision_cache_namespace t ~parent;t in
 mode 0;let t=reopen () in
 check(not(D.cache_namespace_created t) && syncs()=0) "existing reopen created/synced namespace";
 let second=D.with_cache_namespace t ~parent (fun directory ->
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(ComponentHash.reserve_metadata_slot q directory) "existing namespace quota lost";
  ComponentHash.metadata_slot_name q) in
 check(first<>second && opens()=1 && closes()=1) "namespace quota slot replayed";census();
 let t=reopen () in
 D.with_cache_namespace t ~parent (fun directory ->
  let q=ComponentHash.prepare_metadata_quota ~directory ~max_bytes:4194304L ~max_entries:2 in
  check(not(ComponentHash.reserve_metadata_slot q directory)) "namespace quota reset after reopen");census();
 let foreign=D.prepare_cache_namespace ~parent () in
 check(refused(fun () -> D.provision_cache_namespace foreign ~parent) && not(D.cache_namespace_created foreign))
  "fresh ticket adopted existing namespace";
 check(invalid(fun () -> D.with_cache_namespace foreign ~parent ignore)) "failed provision opened";census();
 let dev,ino=id in let wrong=D.prepare_cache_namespace ~expected:(dev,ino+1) ~parent () in
 check(refused(fun () -> D.provision_cache_namespace wrong ~parent) && not(D.cache_namespace_created wrong))
  "wrong expected identity adopted existing namespace";
 check(invalid(fun () -> D.cache_namespace_identity wrong)) "refused identity became observed authority";
 Unix.chmod(child p) 0o755;
 let wrong=D.prepare_cache_namespace ~expected:id ~parent () in
 check(refused(fun () -> D.provision_cache_namespace wrong ~parent)) "accepted nonprivate child";
 Unix.chmod(child p) 0o700;
 Unix.chmod p 0o755;
 check(refused(fun () -> D.prepare_cache_namespace ~parent ())) "accepted nonprivate parent";
 Unix.chmod p 0o700;census();
 let t=reopen () in mode 0;
 check(refused(fun () -> D.with_cache_namespace t ~parent (fun directory -> Unix.fchmod directory 0o755)))
  "postcallback namespace mutation escaped fence";
 check((Unix.lstat(child p)).Unix.st_perm land 0o7777=0o755 && closes()=1)
  "failure secretly restored permissions or skipped close";
 Unix.chmod(child p) 0o700;census();
 let inspect state retained cause =
  check(List.length(D.cache_uncertain_descriptors state)=1 &&
   List.length(D.cache_retained_descriptors state)=retained) "namespace uncertain inventory differs";
  check((D.cache_ownership_cause state<>None)=cause) "namespace original failure lost";
  check(closes()=1) "uncertain namespace numeric close retried";
  check(List.exists(fun (fd,_)->fd=parent) (D.cache_borrowed_directories state) &&
   (Unix.fstat parent).Unix.st_kind=Unix.S_DIR) "borrowed outer namespace parent lost/closed";
  List.iter(fun ((_,observed),error) ->
   check(observed<>None && (match error with Unix.Unix_error(Unix.EIO,_,_)->true|_->false))
    "namespace close identity/error lost") (D.cache_uncertain_descriptors state);
  List.iter(fun (fd,observed) -> check(observed<>None) "known namespace ancestor identity lost";
    ignore(Unix.fstat fd);Unix.close fd) (D.cache_retained_descriptors state);
  census() in
 let t=reopen () in mode 1;
 inspect (uncertain(fun () -> D.with_cache_namespace t ~parent ignore)) 0 false;
 let t=reopen () in mode 1;
 let failure=uncertain(fun () -> D.with_cache_namespace t ~parent (fun _ -> raise Exit)) in
 check((match D.cache_ownership_cause failure with Some Exit -> true | _ -> false))
  "callback cause not retained across close failure";
 inspect failure 0 true;
 let data=Filename.concat p "original-fixture.bin" in write data (String.make 128 'a');
 let input=Unix.openfile data [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 in
 let cp=SemanticFile.with_borrowed_fd input (fun file ->
  ComponentHash.with_snapshot ~max_read_bytes:128L file
   {ComponentHash.id="dng";schema="dng-physical-partition/0";role=Structural;
    offset=0L;length=128L;children=[]} (fun session snap -> ComponentHash.checkpoint session snap)) in
 Unix.close input;
 let entry=D.make_owner_entry ~root_identity:"namespace-original" ~path:"fixture.bin"
  ~generation_sha256:(SemanticHash.string "namespace-original-generation") ~checkpoint:cp ~outcomes:[] in
 let ledger=match D.replace_owner_entry (D.empty_owner_index ~max_entries:1 ~max_bytes:4096)
  ~expected_entry_sha256:None entry with Ok v->v | Error why->failwith why in
 let binding=SemanticHash.string "namespace-original-binding" in
 let manifest=D.owner_index_bytes ~binding ledger in let digest=SemanticHash.string manifest in
 write (Filename.concat(child p)(SemanticHash.hex digest)) manifest;
 write (Filename.concat(child p)(SemanticHash.hex(D.owner_entry_sha256 entry))) (D.owner_entry_bytes entry);
 let t=reopen () in mode 1;
 let failure=uncertain(fun () -> D.with_cache_namespace t ~parent (fun directory ->
  D.load_owner_index ~directory ~expected_manifest_sha256:digest ~binding ~max_entries:1 ~max_bytes:4096 ())) in
 let directories=D.cache_borrowed_directories failure in
 check(List.length directories=2 && List.exists(fun (fd,_)->fd=parent) directories)
  "nested leaf uncertainty lost borrowed parent/child scope";
 check((match D.cache_uncertain_descriptors failure with [((_,Some s),_)]->s.Unix.LargeFile.st_kind=Unix.S_REG|_->false))
  "nested uncertainty did not identify failed entry FD";
 check(List.exists(fun (_,observed)->match observed with Some s->s.Unix.LargeFile.st_kind=Unix.S_DIR|_->false)
  (D.cache_retained_descriptors failure)) "nested namespace FD not retained";
 inspect failure 2 false;
 let t=reopen () in mode 0;
 let held=child p^"-held" in Sys.rename(child p) held;Unix.mkdir(child p) 0o700;
 check(refused(fun () -> D.with_cache_namespace t ~parent ignore) && opens()=0 && closes()=0)
  "replaced directory escaped before-open binding";
 check(invalid(fun () -> D.with_cache_namespace t ~parent ignore)) "failed scoped open replayed";
 Unix.rmdir(child p);Sys.rename held (child p);census();
 let other,other_parent=root () in let target,target_parent=root () in
 let fresh=D.prepare_cache_namespace ~parent:other_parent () in
 check(refused(fun () -> D.provision_cache_namespace fresh ~parent:target_parent) && not(D.cache_namespace_created fresh))
  "ticket accepted different empty parent";
 check(not(Sys.file_exists(child other)) && not(Sys.file_exists(child target)))
  "wrong-parent refusal created child";
 Unix.close other_parent;Unix.close target_parent;census();
 let failpath,failparent=root () in
 let failed=D.prepare_cache_namespace ~parent:failparent () in mode 100;
 check(refused(fun () -> D.provision_cache_namespace failed ~parent:failparent)) "mkdir parent-sync EIO accepted";
 let observed=Unix.lstat(child failpath) in
 check(D.cache_namespace_created failed && observed.Unix.st_kind=Unix.S_DIR && syncs()=1)
  "mkdir effect lost after sync failure";
 check(D.cache_namespace_identity failed=(observed.Unix.st_dev,observed.st_ino)) "failed mkdir identity lost";
 check(invalid(fun () -> D.with_cache_namespace failed ~parent:failparent ignore) && opens()=0)
  "failed provision granted open";
 check(invalid(fun () -> D.provision_cache_namespace failed ~parent:failparent) && syncs()=1)
  "failed provision retried";
 Unix.close failparent;census();
 let symlinkpath,symlinkparent=root () in
 Unix.symlink (child p) (child symlinkpath);
 let t=D.prepare_cache_namespace ~expected:id ~parent:symlinkparent () in mode 0;
 check(refused(fun () -> D.provision_cache_namespace t ~parent:symlinkparent) && opens()=0)
  "existing namespace followed symlink";
 Unix.close symlinkparent;census();
 let missing,missingparent=root () in
 let t=D.prepare_cache_namespace ~expected:id ~parent:missingparent () in
 check(refused(fun () -> D.provision_cache_namespace t ~parent:missingparent) && not(Sys.file_exists(child missing)))
  "existing-only ticket created missing child";
 Unix.close missingparent;census();
 Unix.close parent;
 check(Array.length(Sys.readdir "/dev/fd")=start) "namespace suite leaked final descriptor";
 Printf.printf "PASS %d namespace controls; exact create/reopen, retained effects, quota continuity, nested close uncertainty\n%!" !checks
