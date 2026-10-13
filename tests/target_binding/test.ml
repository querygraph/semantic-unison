exception Marker
let root = Sys.argv.(1)
let check condition message = if not condition then failwith message
let transient = function Util.Transient _ -> true | _ -> false
let oom = function Out_of_memory -> true | _ -> false
let marker = function Marker -> true | _ -> false
let io = function Unix.Unix_error (Unix.EIO, _, _) -> true | _ -> false
let busy = function Unix.Unix_error (Unix.EBUSY, _, _) -> true | _ -> false
let unavailable = function Unix.Unix_error (Unix.ENOSYS, _, _) -> true | _ -> false
let expect_error predicate action =
  match action () with
  | _ -> failwith "expected operation to fail"
  | exception error -> check (predicate error) ("unexpected exception: " ^ Printexc.to_string error)
let value promise = match Lwt.poll promise with
  | Some value -> value
  | None -> failwith "unexpected sleeping result"
let expect_lwt_error predicate action = expect_error predicate (fun () -> value (action ()))
let latest () = List.hd !(FinalPublication.contexts)
let prepare ?connection ?(require_producer=false) ?(logical_root=root) ?(local_path="image.raw")
    ?(working_dir=root) ?(candidate=".image.tmp") ?target ?(normalize=false) () =
  let target = match target with Some target -> target | None -> local_path in
  TargetBinding.prepare ?connection ~require_producer ~logical_root ~local_path ~working_dir
    ~candidate ~target ~normalize ~check_apple_double:!(Osx.rsrc) ()
let ticket ?connection ?require_producer ?logical_root ?local_path ?working_dir ?candidate ?target ?normalize () =
  match prepare ?connection ?require_producer ?logical_root ?local_path ?working_dir ?candidate ?target ?normalize () with
  | Some token -> token
  | None -> failwith "unexpected preparation decline"
let use ?connection ?(logical_root=root) ?(local_path="image.raw")
    ?(working_dir=root) ?(candidate=".image.tmp") ?target token action =
  let target = match target with Some target -> target | None -> local_path in
  TargetBinding.with_binding ?connection ~token ~logical_root ~local_path
    ~working_dir ~candidate ~target action
let produce ?connection ?(logical_root=root) ?(local_path="image.raw")
    ?(working_dir=root) ?(candidate=".image.tmp") ?target token action =
  let target = match target with Some target -> target | None -> local_path in
  TargetBinding.with_producer ?connection ~token ~logical_root ~local_path
    ~working_dir ~candidate ~target action
let release ?connection ?(logical_root=root) token =
  TargetBinding.release_ticket ?connection ~logical_root ~token ()
let reset () =
  FinalPublication.prepare_fault := None;
  FinalPublication.resolution_fault := None;
  FinalPublication.abort_fault := None;
  FinalPublication.handoff_fault := None;
  FinalPublication.adopt_fault := None;
  FinalPublication.producer_check_fault := None;
  FinalPublication.freeze_fault := None;
  FinalPublication.finalized_fault := None;
  FinalPublication.candidate_fault := None;
  FinalPublication.on_prepare := (fun () -> ());
  FinalPublication.on_adopt := (fun () -> ());
  FinalPublication.on_producer_check := (fun () -> ());
  FinalPublication.on_freeze := (fun () -> ());
  FinalPublication.on_candidate_check := (fun () -> ());
  Lwt.test_fail_waiters 0;
  Lwt.test_fail_dispatch 0;
  Remote.disconnect ();
  check (FinalPublication.open_count () = 0) "previous test retained a native fd";
  FinalPublication.enabled := true;
  Features.negotiated := false;
  Features.producer_negotiated := false;
  Fileinfo.fault := None;
  Fspath.resolver := Fspath.default_resolution;
  Path.follow := false;
  Case.current := Case.Sensitive;
  Osx.rsrc := false;
  Name.calls := 0
let cases = ref 0
let candidate_serial = ref 0
let candidate_bytes = "private producer candidate\000payload"
let fd_alive fd =
  try ignore (Unix.fstat fd); true with Unix.Unix_error (Unix.EBADF, _, _) -> false
let with_candidate action =
  incr candidate_serial;
  let path = Filename.concat root ("producer-candidate-" ^ string_of_int !candidate_serial) in
  let fd = Unix.openfile path [Unix.O_RDWR; Unix.O_CREAT; Unix.O_EXCL; Unix.O_CLOEXEC] 0o600 in
  ignore (Unix.write_substring fd candidate_bytes 0 (String.length candidate_bytes));
  ignore (Unix.LargeFile.lseek fd 7L Unix.SEEK_SET);
  Fun.protect ~finally:(fun () -> Unix.close fd; Unix.unlink path) (fun () -> action fd)
let strict_ticket ?connection () = ticket ?connection ~require_producer:true ()
let receipt = Os.Actual "actual full data-and-resource fingerprint"
let freeze_receipt binding fingerprint =
  let owner = TargetBinding.native binding in
  FinalPublication.check_producer owner;
  FinalPublication.freeze_producer owner;
  TargetBinding.record_fingerprint binding fingerprint
let materialize binding candidate fingerprint =
  FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate;
  freeze_receipt binding fingerprint
let ready_producer ?connection token candidate fingerprint =
  let saved = ref None in
  let answer, completion = value (produce ?connection token (fun binding ->
    saved := Some binding;
    materialize binding candidate fingerprint;
    Lwt.return 73)) in
  check (answer = 73 && completion = TargetBinding.Guarded_producer) "producer result or completion differs";
  Option.get !saved
let run name action =
  reset ();
  match action () with
  | () ->
      check (FinalPublication.open_count () = 0) (name ^ ": native fd leak");
      incr cases; Printf.printf "PASS %s\n%!" name
  | exception error ->
      Printf.eprintf "FAIL %s: %s\n%!" name (Printexc.to_string error); exit 1
let () =
  run "support is negotiation only" (fun () ->
    FinalPublication.enabled := false;
    Features.negotiated := true;
    check (TargetBinding.supported ()) "native unavailability hid negotiated protocol";
    Features.negotiated := false;
    check (not (TargetBinding.supported ())) "support ignored feature negotiation");
  run "native unavailable declines without preparation" (fun () ->
    FinalPublication.enabled := false;
    let calls = !(FinalPublication.calls) in
    check (prepare () = None) "expected None";
    check (!(FinalPublication.calls) = calls) "native prepare called despite unavailable endpoint");
  run "ordinary file root uses legacy branch" (fun () ->
    let file = Filename.concat root "file-root" in
    let channel = open_out file in output_string channel "root"; close_out channel;
    let calls = !(FinalPublication.calls) in
    check (prepare ~logical_root:file () = None) "file root did not decline";
    check (!(FinalPublication.calls) = calls) "native opened for file root";
    Sys.remove file);
  run "missing root is an error" (fun () ->
    expect_error transient (fun () -> prepare ~logical_root:(Filename.concat root "missing-root") ()));
  run "root operational error propagates" (fun () ->
    Fileinfo.fault := Some (Unix.Unix_error (Unix.EIO, "root-stat", root));
    expect_error io prepare);
  run "token is 256-bit lowercase hex and unique" (fun () ->
    let first = ticket () in let second = ticket () in
    check (first <> second && String.length first = 64 && String.length second = 64) "wrong nonce length or reuse";
    String.iter (fun c -> check ((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f')) "nonhex nonce") first;
    release first; release second);
  run "normal scope closes native owner" (fun () ->
    let token = ticket () in let owner = latest () in
    check (FinalPublication.alive owner) "prepared fd missing";
    check (value (use token (fun binding ->
      TargetBinding.check_open binding;
      check (not (TargetBinding.closing binding)) "new borrow marked closing";
      Lwt.return 42)) = 42) "scope changed result";
    check owner.closed "scope left owner open";
    check (owner.aborts = 1) "scope failed to delegate cleanup");
  run "token replay is rejected" (fun () ->
    let token = ticket () in ignore (value (use token (fun _ -> Lwt.return ())));
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "replay dispatched")));
  run "wrong connection does not revoke owner ticket" (fun () ->
    let connection = ref 7 in let other = ref 7 in
    let token = ticket ~connection () in
    expect_lwt_error transient (fun () -> use ~connection:other token (fun _ -> failwith "wrong connection dispatched"));
    ignore (value (use ~connection token (fun _ -> Lwt.return ())));
    check (!(FinalPublication.calls) > 0) "no native owner");
  run "local and remote connection scopes differ" (fun () ->
    let connection = ref 1 in let token = ticket () in
    expect_lwt_error transient (fun () -> use ~connection token (fun _ -> failwith "wrong owner dispatched"));
    ignore (value (use token (fun _ -> Lwt.return ())));
    let token = ticket ~connection () in
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "wrong owner dispatched"));
    release ~connection token);
  run "wrong logical root does not revoke owner ticket" (fun () ->
    let token = ticket () in
    expect_lwt_error transient (fun () -> use ~logical_root:(root ^ "-other") token (fun _ -> failwith "wrong root dispatched"));
    ignore (value (use token (fun _ -> Lwt.return ()))));
  List.iter (fun (name, invoke) -> run name (fun () ->
    let token = ticket () in
    expect_lwt_error transient (fun () -> invoke token (fun _ -> failwith "mismatched path dispatched"));
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "consumed mismatched ticket dispatched"))))
    ["wrong selected path consumes ticket", (fun token action -> use ~local_path:"other.raw" token action);
     "wrong working directory consumes ticket", (fun token action -> use ~working_dir:(root ^ "-other") token action);
     "wrong candidate consumes ticket", (fun token action -> use ~candidate:"other.tmp" token action);
     "wrong publication name consumes ticket", (fun token action -> use ~target:"other.raw" token action)];
  run "malformed tokens do not affect prepared owner" (fun () ->
    let token = ticket () in
    List.iter (fun malformed ->
      expect_lwt_error transient (fun () -> use malformed (fun _ -> failwith "malformed dispatched"));
      expect_error transient (fun () -> release malformed))
      [""; String.make 63 '0'; String.make 64 'A'; String.make 64 'g'; String.make 65 '0'];
    release token);
  run "unknown release is idempotent" (fun () ->
    release (String.make 64 '0'); release (String.make 64 '0');
    expect_lwt_error transient (fun () -> use (String.make 64 '0') (fun _ -> failwith "unknown dispatched")));
  run "ready release closes once and permits reuse" (fun () ->
    let token = ticket () in let owner = latest () in
    release token; release token;
    check (owner.aborts = 1 && owner.closed) "release was not idempotent";
    let next = ticket () in release next);
  run "wrong-owner release does not revoke" (fun () ->
    let connection = ref 1 in let other = ref 2 in let token = ticket ~connection () in
    expect_error transient (fun () -> release ~connection:other token);
    expect_error transient (fun () -> release ~connection ~logical_root:(root ^ "-other") token);
    release ~connection token);
  run "128-slot backstop rejects before native prepare" (fun () ->
    let tokens = Array.init 128 (fun _ -> ticket ()) in
    let calls = !(FinalPublication.calls) in
    expect_error transient ticket;
    check (!(FinalPublication.calls) = calls && FinalPublication.open_count () = 128) "overload opened native owner";
    release tokens.(0);
    let replacement = ticket () in release replacement;
    Array.iter release tokens);
  run "native preparation decline releases reservation" (fun () ->
    FinalPublication.prepare_fault := Some (Unix.Unix_error (Unix.ENOSYS, "final_publication.prepare.root_identity", root));
    for _ = 1 to 160 do check (prepare () = None) "identity absence did not decline" done;
    FinalPublication.prepare_fault := None;
    release (ticket ()));
  run "operational prepare failures release reservation" (fun () ->
    FinalPublication.prepare_fault := Some (Unix.Unix_error (Unix.EIO, "final_publication.prepare.root_identity", root));
    for _ = 1 to 160 do expect_error io prepare done;
    FinalPublication.prepare_fault := None; release (ticket ()));
  run "unsupported path phase remains an error" (fun () ->
    FinalPublication.prepare_fault := Some (Unix.Unix_error (Unix.ENOSYS, "final_publication.prepare.root_open", root));
    expect_error unavailable prepare);
  run "post-prepare classifier-shaped error does not decline" (fun () ->
    FinalPublication.resolution_fault := Some (Unix.Unix_error (Unix.ENOSYS, "final_publication.prepare.root_identity", root));
    expect_error unavailable prepare;
    check (latest ()).closed "post-prepare error leaked native owner");
  run "initial resolution mismatch closes preparation" (fun () ->
    expect_error busy (fun () -> prepare ~target:"wrong.raw" ());
    check (latest ()).closed "bad setup resolution leaked native owner");
  run "connection loss during prepare closes returned native owner" (fun () ->
    FinalPublication.on_prepare := Remote.disconnect;
    expect_error transient prepare;
    check (latest ()).closed "prepare returned after expired session without close");
  run "synchronous callback failure closes and preserves error" (fun () ->
    let token = ticket () in
    expect_lwt_error marker (fun () -> use token (fun _ -> raise Marker)));
  run "failed promise closes and preserves error" (fun () ->
    let token = ticket () in let helper = Lwt.wait () in
    let scope = use token (fun _ -> helper) in
    check (FinalPublication.open_count () = 1) "helper fd closed before failure settlement";
    Lwt.wakeup_exn helper Marker;
    expect_error marker (fun () -> value scope));
  run "cleanup error does not replace callback failure" (fun () ->
    let token = ticket () in
    FinalPublication.abort_fault := Some (Unix.Unix_error (Unix.EIO, "abort", ""));
    expect_lwt_error marker (fun () -> use token (fun _ -> Lwt.fail Marker)));
  run "cleanup error on successful scope is visible" (fun () ->
    let token = ticket () in
    FinalPublication.abort_fault := Some (Unix.Unix_error (Unix.EIO, "abort", ""));
    expect_lwt_error io (fun () -> use token (fun _ -> Lwt.return ())));
  run "second borrow cannot steal sleeping owner" (fun () ->
    let token = ticket () in let helper = Lwt.wait () in
    let scope = use token (fun _ -> helper) in
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "second borrow dispatched"));
    check (FinalPublication.open_count () = 1) "second borrow closed first owner's fd";
    Lwt.wakeup helper (); ignore (value scope));
  run "connection close defers borrowed cleanup until settlement" (fun () ->
    let token = ticket () in let helper = Lwt.wait () in let saved = ref None in
    let scope = use token (fun binding -> saved := Some binding; helper) in
    let binding = Option.get !saved in let owner = latest () in
    Remote.disconnect ();
    check (TargetBinding.closing binding && FinalPublication.alive owner) "disconnect closed outstanding helper fd";
    expect_error transient (fun () -> TargetBinding.check_open binding);
    Lwt.wakeup helper ();
    expect_error transient (fun () -> value scope);
    check owner.closed "settled disconnect leaked owner");
  run "borrowed release defers cleanup and fails closing scope" (fun () ->
    let token = ticket () in let helper = Lwt.wait () in let owner = latest () in
    let scope = use token (fun _ -> helper) in
    release token; release token;
    check (FinalPublication.alive owner) "release closed outstanding helper fd";
    Lwt.wakeup helper (); expect_error transient (fun () -> value scope);
    release token);
  run "ready disconnect revokes old session" (fun () ->
    let token = ticket () in Remote.disconnect ();
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "expired session dispatched"));
    release (ticket ()));
  run "borrowed capacity survives disconnect" (fun () ->
    let tokens = Array.init 128 (fun _ -> ticket ()) in let helper = Lwt.wait () in
    let scope = use tokens.(0) (fun _ -> helper) in
    for index = 1 to 127 do release tokens.(index) done;
    let next = Array.init 127 (fun _ -> ticket ()) in
    let calls = !(FinalPublication.calls) in expect_error transient ticket;
    check (!(FinalPublication.calls) = calls) "borrowed slot was not counted";
    Remote.disconnect ();
    check (FinalPublication.open_count () = 1) "disconnect failed ready/borrowed distinction";
    ignore next;
    Lwt.wakeup helper (); expect_error transient (fun () -> value scope));
  run "legacy handoff releases without abort" (fun () ->
    let token = ticket () in let owner = latest () in let saved = ref None in
    ignore (value (use token (fun binding ->
      saved := Some binding; TargetBinding.legacy_handoff binding;
      TargetBinding.legacy_handoff binding;
      expect_error transient (fun () -> ignore (TargetBinding.native binding));
      Lwt.return ())));
    check (owner.closed && owner.aborts = 0) "legacy handoff selected abort";
    check (not (TargetBinding.published (Option.get !saved))) "handoff invented publication");
  run "publication remains queryable after scope close" (fun () ->
    let token = ticket () in let saved = ref None in
    ignore (value (use token (fun binding ->
      saved := Some binding; FinalPublication.publish (TargetBinding.native binding); Lwt.return ())));
    let binding = Option.get !saved in
    check (TargetBinding.published binding) "cleanup erased publication receipt";
    expect_error transient (fun () -> ignore (TargetBinding.native binding)));
  run "published disconnect receipt survives deferred close" (fun () ->
    let token = ticket () in let saved = ref None in let helper = Lwt.wait () in
    let scope = use token (fun binding ->
      saved := Some binding; FinalPublication.publish (TargetBinding.native binding); helper) in
    Remote.disconnect (); check (FinalPublication.open_count () = 1) "published helper owner closed early";
    Lwt.wakeup helper (); expect_error transient (fun () -> value scope);
    check (TargetBinding.published (Option.get !saved)) "published receipt lost on disconnect");
  run "quarantine derives private name and preserves validation failure" (fun () ->
    let token = ticket () in let owner = latest () in
    expect_lwt_error marker (fun () -> use token (fun binding ->
      FinalPublication.attach (TargetBinding.native binding);
      TargetBinding.quarantine binding; Lwt.fail Marker));
    check (owner.quarantines = [".unison.validation-rejected-" ^ token ^ ".unison.tmp"])
      "wrong quarantine name");
  run "changed follow policy consumes ticket" (fun () ->
    let token = ticket () in Path.follow := true;
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "changed follow dispatched")));
  run "changed case policy consumes ticket" (fun () ->
    let token = ticket () in Case.current := Case.UnicodeInsensitive;
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "changed mode dispatched")));
  run "changed resource-fork policy consumes ticket" (fun () ->
    let token = ticket () in Osx.rsrc := true;
    expect_lwt_error transient (fun () -> use token (fun _ -> failwith "changed rsrc dispatched")));
  run "resource-fork policy reaches native preparation" (fun () ->
    Osx.rsrc := true; let token = ticket () in
    check (latest ()).auxiliary "native auxiliary policy missing"; release token);
  run "Copy normalization is retained for rechecks" (fun () ->
    let token = ticket ~local_path:"decomposed" ~target:"composed" ~normalize:true () in
    ignore (value (use ~local_path:"decomposed" ~target:"composed" token (fun binding ->
      TargetBinding.recheck_resolution binding; Lwt.return ())));
    check (!(Name.calls) > 0) "normalization was not applied");
  run "Update spelling does not normalize" (fun () ->
    let token = ticket ~local_path:"decomposed" ~normalize:false () in
    ignore (value (use ~local_path:"decomposed" token (fun binding ->
      TargetBinding.recheck_resolution binding; Lwt.return ())));
    check (!(Name.calls) = 0) "Update unexpectedly normalized filename");
  run "fresh resolution mismatch consumes ticket" (fun () ->
    let token = ticket () in Fspath.resolver := (fun _ _ -> root, "other.raw");
    expect_lwt_error busy (fun () -> use token (fun _ -> failwith "rebound target dispatched")));
  run "mid-callback policy change is rejected" (fun () ->
    let token = ticket () in
    expect_lwt_error transient (fun () -> use token (fun binding ->
      Path.follow := true; TargetBinding.recheck_resolution binding; Lwt.return ())));
  run "pre-dispatch continuation allocation failure closes owner" (fun () ->
    let token = ticket () in Lwt.test_fail_dispatch 2;
    expect_lwt_error oom (fun () -> use token (fun _ -> failwith "faulted dispatch ran callback")));
  run "waiter allocation failure retains sleeping helper fd" (fun () ->
    let token = ticket () in let owner = latest () in let helper = Lwt.wait () in
    Lwt.test_fail_waiters 1;
    expect_lwt_error oom (fun () -> use token (fun _ -> helper));
    check (FinalPublication.alive owner) "waiter exception closed fd before helper settled";
    Lwt.wakeup helper (); check owner.closed "recovery waiter did not close settled owner");
  run "repeated waiter faults retain capacity and recover on admission" (fun () ->
    let token = ticket () in let owner = latest () in let helper = Lwt.wait () in
    Lwt.test_fail_waiters 3;
    expect_lwt_error oom (fun () -> use token (fun _ -> helper));
    release token;
    check (FinalPublication.alive owner) "repeated waiter faults closed running owner";
    let next = ticket () in release next;
    check (FinalPublication.alive owner) "admission closed sleeping recovered owner";
    Lwt.wakeup helper (); check owner.closed "admission did not restore settlement observer");
  run "producer support requires both separately registered negotiations" (fun () ->
    check (List.mem_assoc "target-binding-v0" !(Features.registered) &&
      List.mem_assoc "target-binding-producer-v0" !(Features.registered)) "missing registered feature";
    List.iter (fun (base, producer, expected) ->
      Features.negotiated := base; Features.producer_negotiated := producer;
      check (TargetBinding.producer_supported () = expected) "producer negotiation ignored base or new feature")
      [false, false, false; true, false, false; false, true, false; true, true, true];
    FinalPublication.enabled := false;
    check (TargetBinding.producer_supported ()) "native unavailability hid negotiated producer protocol");
  run "strict producer retains actual owner and fingerprint through idle source checks" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      let binding = ready_producer token fd receipt in
      let witness = Option.get owner.producer_fd in
      check (TargetBinding.requires_producer binding && TargetBinding.finalized binding) "producer origin receipt missing";
      check (TargetBinding.fingerprint binding = Some receipt && owner.aborts = 0 && FinalPublication.alive owner && fd_alive witness)
        "Finalized idle owner was closed or receipt lost";
      expect_error transient (fun () -> TargetBinding.check_open binding);
      check (Unix.LargeFile.lseek fd 0L Unix.SEEK_CUR = 7L) "producer moved borrowed FD";
      check (value (use token (fun commit ->
        check (commit == binding) "commit replaced producer registry owner";
        check (TargetBinding.fingerprint commit = Some receipt) "commit substituted source archive fingerprint";
        FinalPublication.publish (TargetBinding.native commit);
        Lwt.return 19)) = 19) "strict commit altered result";
      check (owner.closed && not (fd_alive witness) && fd_alive fd && TargetBinding.published binding &&
        TargetBinding.finalized binding && TargetBinding.fingerprint binding = Some receipt)
        "close lost receipt or failed actual witness ownership"));
  run "legacy ticket rejects producer without revoking legacy commit" (fun () ->
    let token = ticket () in let owner = latest () in
    expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "legacy producer dispatched"));
    check (FinalPublication.alive owner) "legacy producer attempt revoked ready owner";
    ignore (value (use token (fun binding ->
      check (not (TargetBinding.requires_producer binding)) "legacy default became strict";
      Lwt.return ()))));
  run "strict commit before producer preserves legitimate producer authorization" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "unproduced commit dispatched"));
      check (FinalPublication.alive owner) "premature commit revoked Ready strict owner";
      ignore (ready_producer token fd receipt);
      ignore (value (use token (fun _ -> Lwt.return ())))));
  run "finalized producer replay preserves legitimate commit" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      ignore (ready_producer token fd receipt);
      expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "second producer dispatched"));
      check (FinalPublication.alive owner) "producer replay revoked Finalized owner";
      ignore (value (use token (fun _ -> Lwt.return ())))));
  run "busy producer rejects both replays without closing running helper" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let helper = Lwt.wait () and saved = ref None in
      let scope = produce token (fun binding -> saved := Some binding;
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; helper) in
      expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "concurrent producer dispatched"));
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "commit during producer dispatched"));
      check (FinalPublication.alive owner && fd_alive (Option.get owner.producer_fd)) "replay closed producer helper FD";
      freeze_receipt (Option.get !saved) receipt;
      Lwt.wakeup helper 91;
      check (value scope = (91, TargetBinding.Guarded_producer)) "sleeping producer did not finalize";
      ignore (value (use token (fun _ -> Lwt.return ())))));
  run "busy strict commit rejects producer and commit replays" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      ignore (ready_producer token fd receipt);
      let helper = Lwt.wait () in let scope = use token (fun _ -> helper) in
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "second commit dispatched"));
      expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "producer during commit dispatched"));
      check (FinalPublication.alive owner) "strict commit replay closed first helper";
      Lwt.wakeup helper (); ignore (value scope)));
  run "producer physical connection and receiver-local scope cannot be substituted" (fun () ->
    with_candidate (fun fd ->
      let connection = ref 5 and other = ref 5 in let token = strict_ticket ~connection () in
      expect_lwt_error transient (fun () -> produce ~connection:other token (fun _ -> failwith "wrong producer owner dispatched"));
      expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "remote owner treated as local"));
      ignore (ready_producer ~connection token fd receipt);
      ignore (value (use ~connection token (fun _ -> Lwt.return ())));
      let local = strict_ticket () in
      expect_lwt_error transient (fun () -> produce ~connection local (fun _ -> failwith "source connection became receiver owner"));
      ignore (ready_producer local fd receipt);
      ignore (value (use local (fun _ -> Lwt.return ())))));
  run "producer wrong root preserves correct owner authorization" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in
      expect_lwt_error transient (fun () -> produce ~logical_root:(root ^ "-wrong") token (fun _ -> failwith "wrong producer root dispatched"));
      ignore (ready_producer token fd receipt);
      ignore (value (use token (fun _ -> Lwt.return ())))));
  List.iter (fun (name, invoke) -> run name (fun () ->
    let token = strict_ticket () in let owner = latest () in
    expect_lwt_error transient (fun () -> invoke token (fun _ -> failwith "mismatched producer dispatched"));
    check owner.closed "producer path mismatch retained native owner";
    expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "consumed producer path ticket replayed"))))
    ["producer wrong selected path consumes eligible phase", (fun token action -> produce ~local_path:"other.raw" token action);
     "producer wrong workdir consumes eligible phase", (fun token action -> produce ~working_dir:(root ^ "-other") token action);
     "producer wrong candidate consumes eligible phase", (fun token action -> produce ~candidate:"other.tmp" token action);
     "producer wrong target consumes eligible phase", (fun token action -> produce ~target:"other.raw" token action)];
  run "malformed producer nonce does not revoke valid Ready owner" (fun () ->
    let token = strict_ticket () in
    List.iter (fun bad -> expect_lwt_error transient (fun () -> produce bad (fun _ -> failwith "invalid producer nonce dispatched")))
      [""; String.make 63 '0'; String.make 64 'A'; String.make 64 'g'; String.make 65 '0'];
    release token);
  List.iter (fun (name, change) -> run name (fun () ->
    let token = strict_ticket () in let owner = latest () in change ();
    expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "changed producer policy dispatched"));
    check owner.closed "producer policy mismatch retained owner"))
    ["producer follow policy is bound", (fun () -> Path.follow := true);
     "producer case policy is bound", (fun () -> Case.current := Case.UnicodeInsensitive);
     "producer resource-fork policy is bound", (fun () -> Osx.rsrc := true)];
  run "mid-producer policy change fails without legacy fallback" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error transient (fun () -> produce token (fun binding ->
        materialize binding fd receipt; Path.follow := true; Lwt.return ()));
      check owner.closed "mid-producer policy change retained owner"));
  run "producer preserves Copy normalization through both phases" (fun () ->
    with_candidate (fun fd ->
      let token = ticket ~require_producer:true ~local_path:"decomposed" ~target:"composed" ~normalize:true () in
      check (value (produce ~local_path:"decomposed" ~target:"composed" token (fun binding ->
        materialize binding fd receipt; Lwt.return ())) = ((), TargetBinding.Guarded_producer)) "normalized producer failed";
      ignore (value (use ~local_path:"decomposed" ~target:"composed" token (fun _ -> Lwt.return ())));
      check (!(Name.calls) >= 3) "producer or commit dropped recorded normalization"));
  run "producer without native adoption cannot qualify" (fun () ->
    let token = strict_ticket () in let owner = latest () in
    expect_lwt_error transient (fun () -> produce token (fun _ -> Lwt.return ()));
    check (owner.closed && not owner.producer && not owner.frozen) "missing adoption produced a native receipt");
  run "mutable witness without freeze cannot qualify" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error transient (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; Lwt.return ()));
      check (owner.closed && not owner.frozen && fd_alive fd) "unfrozen producer qualified or consumed borrowed FD"));
  run "named attachment is not producer-origin freezing" (fun () ->
    let token = strict_ticket () in let owner = latest () in
    expect_lwt_error transient (fun () -> produce token (fun binding ->
      FinalPublication.attach (TargetBinding.native binding);
      TargetBinding.record_fingerprint binding receipt; Lwt.return ()));
    check (owner.closed && not (FinalPublication.producer_finalized owner)) "named attachment invented producer origin");
  run "freeze without actual fingerprint cannot qualify" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let saved = ref None in
      expect_lwt_error transient (fun () -> produce token (fun binding ->
        saved := Some binding;
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        FinalPublication.freeze_producer (TargetBinding.native binding); Lwt.return ()));
      check (owner.closed && TargetBinding.fingerprint (Option.get !saved) = None) "missing fingerprint was manufactured";
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "missing-receipt producer committed"))));
  run "missing retained witness fails freeze and preserves borrowed FD" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error busy (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        FinalPublication.drop_witness owner;
        FinalPublication.freeze_producer owner; Lwt.return ()));
      check (owner.closed && fd_alive fd && not owner.frozen) "missing witness qualified or borrowed FD closed"));
  run "fingerprint setter rejects premature pseudo and repeated values" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in
      let actual = Os.Actual "actual receipt distinct from pseudo source" in
      let binding = Option.get (fst (value (produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        expect_error transient (fun () -> TargetBinding.record_fingerprint binding actual);
        FinalPublication.freeze_producer (TargetBinding.native binding);
        expect_error transient (fun () -> TargetBinding.record_fingerprint binding (Os.Pseudo "source-archive"));
        TargetBinding.record_fingerprint binding actual;
        expect_error transient (fun () -> TargetBinding.record_fingerprint binding (Os.Actual "replacement"));
        Lwt.return (Some binding))))) in
      check (TargetBinding.fingerprint binding = Some actual) "setter replaced actual receipt";
      expect_error transient (fun () -> TargetBinding.record_fingerprint binding receipt);
      ignore (value (use token (fun commit ->
        expect_error transient (fun () -> TargetBinding.record_fingerprint commit receipt); Lwt.return ())));
      check (TargetBinding.fingerprint binding = Some actual) "receipt lost after close";
      expect_error transient (fun () -> TargetBinding.record_fingerprint binding receipt)));
  List.iter (fun ordinal -> run ("fingerprint fence " ^ string_of_int ordinal ^ " rejects identity and operational errors without receipt") (fun () ->
    List.iter (fun failure -> with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let saved = ref None in
      expect_lwt_error (fun actual -> actual == failure) (fun () -> produce token (fun binding ->
        saved := Some binding;
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        FinalPublication.freeze_producer owner;
        FinalPublication.candidate_fault := Some (ordinal, failure);
        TargetBinding.record_fingerprint binding receipt; Lwt.return ()));
      FinalPublication.candidate_fault := None;
      check (owner.closed && TargetBinding.fingerprint (Option.get !saved) = None && fd_alive fd)
        "failed fingerprint fence retained partial receipt or closed borrowed FD"))
      [Unix.Unix_error (Unix.EBUSY, "changed-frozen-identity", "candidate");
       Unix.Unix_error (Unix.EIO, "candidate-fence", "candidate")])) [1; 2];
  run "witness disappearance between fingerprint fences stores no receipt" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let saved = ref None in
      expect_lwt_error busy (fun () -> produce token (fun binding ->
        saved := Some binding;
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        FinalPublication.freeze_producer owner;
        FinalPublication.on_candidate_check := (fun () ->
          if owner.candidate_checks = 1 then FinalPublication.drop_witness owner);
        TargetBinding.record_fingerprint binding receipt; Lwt.return ()));
      check (owner.closed && TargetBinding.fingerprint (Option.get !saved) = None && fd_alive fd)
        "post-fence witness loss published receipt"));
  run "native producer errors preserve identity without selecting legacy" (fun () ->
    List.iter (fun point -> List.iter (fun failure -> with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      (match point with
       | 0 -> FinalPublication.adopt_fault := Some failure
       | 1 -> FinalPublication.producer_check_fault := Some failure
       | 2 -> FinalPublication.freeze_fault := Some failure
       | _ -> FinalPublication.finalized_fault := Some failure);
      expect_lwt_error (fun actual -> actual == failure) (fun () -> produce token (fun binding ->
        materialize binding fd receipt; Lwt.return ()));
      check (owner.closed && owner.releases = 0 && fd_alive fd) "native producer failure selected legacy or consumed caller FD";
      FinalPublication.adopt_fault := None; FinalPublication.producer_check_fault := None;
      FinalPublication.freeze_fault := None; FinalPublication.finalized_fault := None;
      release (strict_ticket ())))
      [Unix.Unix_error (Unix.EIO, "producer-native", "candidate");
       Unix.Unix_error (Unix.ENOSYS, "producer-native", "candidate")]) [0; 1; 2; 3]);
  run "explicit producer legacy handoff is the only legacy completion" (fun () ->
    List.iter (fun adopted -> with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      let result = value (produce token (fun binding ->
        if adopted then FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        TargetBinding.legacy_handoff binding; TargetBinding.legacy_handoff binding;
        Lwt.return 81)) in
      check (result = (81, TargetBinding.Legacy_backend) && owner.closed && owner.aborts = 0 && owner.releases > 0 && fd_alive fd)
        "legacy producer handoff aborted, invented guard or consumed borrower";
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "legacy producer nonce committed")))) [false; true]);
  run "producer failure closes and preserves callback error despite cleanup error" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      FinalPublication.abort_fault := Some (Unix.Unix_error (Unix.EIO, "producer-cleanup", ""));
      expect_lwt_error marker (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; raise Marker));
      check (owner.closed && fd_alive fd) "callback failure kept or consumed wrong FD"));
  run "successful producer does not abort idle finalized owner" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      FinalPublication.abort_fault := Some (Unix.Unix_error (Unix.EIO, "unexpected-early-abort", ""));
      ignore (ready_producer token fd receipt);
      check (owner.aborts = 0 && FinalPublication.alive owner) "producer success cleaned Finalized owner";
      FinalPublication.abort_fault := None; release token));
  run "ready producer disconnect expires owner before callback" (fun () ->
    let token = strict_ticket () in let owner = latest () in Remote.disconnect ();
    check owner.closed "Ready strict owner not closed on disconnect";
    expect_lwt_error transient (fun () -> produce token (fun _ -> failwith "expired producer dispatched"));
    release (strict_ticket ()));
  run "idle finalized disconnect closes retained witness and preserves fingerprint history" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let binding = ready_producer token fd receipt in
      let witness = Option.get owner.producer_fd in Remote.disconnect ();
      check (owner.closed && not (fd_alive witness) && fd_alive fd && TargetBinding.fingerprint binding = Some receipt &&
        TargetBinding.finalized binding) "idle disconnect lost receipt or retained native FD";
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "expired finalized commit dispatched"))));
  run "finalized release closes once and removes commit authorization" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let binding = ready_producer token fd receipt in
      release token; release token;
      check (owner.aborts = 1 && owner.closed && TargetBinding.fingerprint binding = Some receipt) "Finalized release lost idempotence or history";
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "released finalized ticket committed"))));
  List.iter (fun disconnected -> run
    (if disconnected then "busy producer disconnect defers actual FD close" else "busy producer release defers actual FD close") (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let helper = Lwt.wait () and saved = ref None in
      let scope = produce token (fun binding -> saved := Some binding;
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; helper) in
      let witness = Option.get owner.producer_fd in
      if disconnected then Remote.disconnect () else (release token; release token);
      check (FinalPublication.alive owner && fd_alive witness && TargetBinding.closing (Option.get !saved)) "closing producer released running helper FD";
      expect_error transient (fun () -> TargetBinding.check_open (Option.get !saved));
      Lwt.wakeup helper (); expect_error transient (fun () -> value scope);
      check (owner.closed && not (fd_alive witness) && fd_alive fd && TargetBinding.fingerprint (Option.get !saved) = None)
        "settled closing producer retained FD or invented receipt"))) [false; true];
  run "busy strict commit disconnect defers witness close and retains published history" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let binding = ready_producer token fd receipt in
      let witness = Option.get owner.producer_fd and helper = Lwt.wait () in
      let scope = use token (fun commit -> FinalPublication.publish (TargetBinding.native commit); helper) in
      Remote.disconnect ();
      check (FinalPublication.alive owner && fd_alive witness) "disconnect closed strict commit helper FD";
      Lwt.wakeup helper (); expect_error transient (fun () -> value scope);
      check (owner.closed && not (fd_alive witness) && TargetBinding.published binding && TargetBinding.fingerprint binding = Some receipt)
        "strict commit settlement lost published/fingerprint history"));
  run "128-slot backstop includes Ready Producing Finalized and Committing" (fun () ->
    with_candidate (fun fd ->
      let ready = Array.init 32 (fun _ -> strict_ticket ()) in
      let producer_helpers = Array.init 32 (fun _ -> Lwt.wait ()) in
      let producers = Array.init 32 (fun index ->
        let token = strict_ticket () in produce token (fun binding ->
          FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; producer_helpers.(index))) in
      let finalized = Array.init 32 (fun _ ->
        let token = strict_ticket () in ignore (ready_producer token fd receipt); token) in
      let commit_helpers = Array.init 32 (fun _ -> Lwt.wait ()) in
      let commits = Array.init 32 (fun index ->
        let token = strict_ticket () in ignore (ready_producer token fd receipt);
        use token (fun _ -> commit_helpers.(index))) in
      let calls = !(FinalPublication.calls) in
      expect_error transient strict_ticket;
      check (!(FinalPublication.calls) = calls && FinalPublication.open_count () = 128) "mixed phase overload opened native owner";
      release ready.(0); let replacement = strict_ticket () in ignore replacement;
      Remote.disconnect ();
      check (FinalPublication.open_count () = 64) "mixed disconnect did not distinguish idle and busy phases";
      ignore finalized;
      Array.iteri (fun index helper -> Lwt.wakeup helper (); expect_error transient (fun () -> value producers.(index))) producer_helpers;
      Array.iteri (fun index helper -> Lwt.wakeup helper (); expect_error transient (fun () -> value commits.(index))) commit_helpers));
  run "producer pre-dispatch Lwt allocation fault closes ready owner" (fun () ->
    let token = strict_ticket () in let owner = latest () in Lwt.test_fail_dispatch 2;
    expect_lwt_error oom (fun () -> produce token (fun _ -> failwith "faulted producer dispatch ran"));
    check owner.closed "producer pre-dispatch fault retained owner");
  run "producer waiter allocation fault retains sleeping helper witness until settlement" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let helper = Lwt.wait () in
      Lwt.test_fail_waiters 1;
      expect_lwt_error oom (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; helper));
      let witness = Option.get owner.producer_fd in
      check (FinalPublication.alive owner && fd_alive witness) "producer waiter exception closed fd before helper settled";
      expect_lwt_error transient (fun () -> use token (fun _ -> failwith "faulted producer became Finalized"));
      Lwt.wakeup helper ();
      check (owner.closed && not (fd_alive witness) && fd_alive fd) "producer recovery waiter failed exact FD lifecycle"));
  run "repeated producer waiter faults retain slot and recover on admission" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let helper = Lwt.wait () in
      Lwt.test_fail_waiters 3;
      expect_lwt_error oom (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd; helper));
      release token;
      check (FinalPublication.alive owner) "producer repeated faults closed running helper";
      release (strict_ticket ());
      check (FinalPublication.alive owner) "producer admission recovery closed sleeping helper";
      Lwt.wakeup helper (); check owner.closed "producer recovery did not observe settlement"));
  run "strict commit pre-dispatch Lwt fault closes retained producer owner" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let binding = ready_producer token fd receipt in
      Lwt.test_fail_dispatch 2;
      expect_lwt_error oom (fun () -> use token (fun _ -> failwith "faulted strict commit dispatched"));
      check (owner.closed && TargetBinding.fingerprint binding = Some receipt) "strict dispatch fault lost ownership or history"));
  run "strict commit waiter fault retains producer witness until helper settles" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in let binding = ready_producer token fd receipt in
      let witness = Option.get owner.producer_fd and helper = Lwt.wait () in
      Lwt.test_fail_waiters 1;
      expect_lwt_error oom (fun () -> use token (fun _ -> helper));
      check (FinalPublication.alive owner && fd_alive witness) "strict commit waiter fault closed running helper";
      Lwt.wakeup helper ();
      check (owner.closed && not (fd_alive witness) && TargetBinding.fingerprint binding = Some receipt)
        "strict commit recovery lost witness lifecycle or history"));
  run "repeated strict commit waiter faults recover on admission" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in ignore (ready_producer token fd receipt);
      let helper = Lwt.wait () in Lwt.test_fail_waiters 3;
      expect_lwt_error oom (fun () -> use token (fun _ -> helper));
      release token; check (FinalPublication.alive owner) "repeated strict fault closed active helper";
      release (strict_ticket ()); check (FinalPublication.alive owner) "strict admission recovery closed sleeping helper";
      Lwt.wakeup helper (); check owner.closed "strict commit recovery missed settlement"));
  run "planned mutable handoff rechecks producer before no-unlink release" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      let _, completion = value (produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        ignore (Unix.lseek fd 0 Unix.SEEK_END);
        ignore (Unix.write_substring fd "planned fork/property changes" 0 29);
        TargetBinding.legacy_handoff binding; Lwt.return ())) in
      check (completion = TargetBinding.Legacy_backend && owner.aborts = 0 &&
             owner.closed && fd_alive fd)
        "planned family selected destructive cleanup"));
  run "rebound resolution cannot select legacy backend" (fun () ->
    let token = strict_ticket () in let owner = latest () in
    expect_lwt_error busy (fun () -> produce token (fun binding ->
      Fspath.resolver := (fun _ _ -> root, "rebound.raw");
      TargetBinding.legacy_handoff binding; Lwt.return ()));
    check (owner.releases = 0 && owner.closed) "rebound resolution became legacy release");
  List.iter (fun (name, change) -> run name (fun () ->
    let token = strict_ticket () in let owner = latest () in
    expect_lwt_error transient (fun () -> produce token (fun binding ->
      change (); TargetBinding.legacy_handoff binding; Lwt.return ()));
    check (owner.releases = 0 && owner.closed) "changed policy became legacy release"))
    ["changed follow policy cannot select legacy backend", (fun () -> Path.follow := true);
     "changed case policy cannot select legacy backend", (fun () -> Case.current := Case.UnicodeInsensitive);
     "changed resource-fork policy cannot select legacy backend", (fun () -> Osx.rsrc := true)];
  List.iter (fun named -> run
    (if named then "legacy named handoff native refusal remains terminal"
     else "prepared handoff native operational refusal remains terminal") (fun () ->
      let token = ticket () in let owner = latest () in
      let failure = Unix.Unix_error
        ((if named then Unix.EBUSY else Unix.EIO), "native_handoff", "candidate") in
      expect_lwt_error (fun error -> error == failure) (fun () -> use token (fun binding ->
        if named then FinalPublication.attach (TargetBinding.native binding);
        FinalPublication.handoff_fault := Some failure;
        TargetBinding.legacy_handoff binding; Lwt.return ()));
      check (owner.releases = 0 && owner.closed) "native refusal became legacy release"))
    [false; true];
  run "lost mutable producer witness cannot select legacy backend" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error busy (fun () -> produce token (fun binding ->
        FinalPublication.adopt_mutable (TargetBinding.native binding) ~candidate:fd;
        FinalPublication.drop_witness owner;
        TargetBinding.legacy_handoff binding; Lwt.return ()));
      check (owner.releases = 0 && owner.closed && fd_alive fd)
        "lost producer became legacy release or closed borrowed descriptor"));
  run "changed frozen producer cannot select legacy backend" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      expect_lwt_error busy (fun () -> produce token (fun binding ->
        materialize binding fd receipt;
        ignore (Unix.lseek fd 0 Unix.SEEK_END);
        ignore (Unix.write_substring fd "late" 0 4);
        TargetBinding.legacy_handoff binding; Lwt.return ()));
      check (owner.releases = 0 && owner.closed && fd_alive fd)
        "changed frozen producer became legacy release"));
  run "unchanged frozen producer may explicitly hand off a planned family" (fun () ->
    with_candidate (fun fd ->
      let token = strict_ticket () in let owner = latest () in
      let _, completion = value (produce token (fun binding ->
        materialize binding fd receipt;
        TargetBinding.legacy_handoff binding; Lwt.return ())) in
      check (completion = TargetBinding.Legacy_backend && owner.aborts = 0 &&
             owner.closed && fd_alive fd)
        "unchanged planned family lost no-unlink handoff"));
  reset ();
  Printf.printf "PASS %d focused registry cases\n%!" !cases
