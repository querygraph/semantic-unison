module C = CloneRange

let check condition message = if not condition then failwith message
let tests = ref 0
let test name body =
  (try body () with error -> Printf.eprintf "FAIL %s\n%!" name; raise error);
  incr tests;
  Printf.printf "PASS %s\n%!" name

type request = {
  source_offset : int64;
  destination_offset : int64;
  length : int64;
}

type action = {
  kind : string;
  request : request;
  written : int64;
}

type memory = {
  basis : string;
  original_basis : string;
  stage : bytes;
  initial_stage : string;
  writes : int array;
  mutable authorized : request;
  mutable actions : action list;
}

let i64 = Int64.of_int
let request source destination length = {
  source_offset = i64 source; destination_offset = i64 destination; length = i64 length
}

let memory ?(size=192) ?(stage_from_basis=false) authorized =
  let basis = String.init size (fun i -> Char.chr ((i * 73 + 19) land 255)) in
  let stage = if stage_from_basis then Bytes.of_string basis
              else Bytes.init size (fun i -> Char.chr ((i * 31 + 211) land 255)) in
  { basis; original_basis = basis; stage; initial_stage = Bytes.to_string stage;
    writes = Array.make size 0; authorized; actions = [] }

(* This oracle checks the requested envelope and relative byte mapping directly.
   It does not calculate heads, aligned interiors or planner chunk boundaries. *)
let verify_request fixture operation =
  let allowed = fixture.authorized in
  let displacement = Int64.sub operation.destination_offset allowed.destination_offset in
  check (operation.length > 0L) "backend received a nonpositive request";
  check (displacement >= 0L && displacement <= allowed.length &&
         operation.length <= Int64.sub allowed.length displacement)
    "backend request escaped authorized destination interval";
  check (operation.source_offset >= allowed.source_offset &&
         Int64.sub operation.source_offset allowed.source_offset = displacement)
    "backend request used the wrong immutable-source offset";
  check (operation.source_offset >= 0L && operation.destination_offset >= 0L &&
         operation.length <= Int64.sub (i64 (String.length fixture.basis)) operation.source_offset &&
         operation.length <= Int64.sub (i64 (Bytes.length fixture.stage)) operation.destination_offset)
    "backend request exceeded source or destination EOF"

let write fixture kind operation written =
  verify_request fixture operation;
  check (written > 0L && written <= operation.length) "fake write count invalid";
  let source = Int64.to_int operation.source_offset in
  let destination = Int64.to_int operation.destination_offset in
  let length = Int64.to_int written in
  for offset = 0 to length - 1 do
    Bytes.set fixture.stage (destination + offset) fixture.basis.[source + offset];
    fixture.writes.(destination + offset) <- fixture.writes.(destination + offset) + 1
  done;
  fixture.actions <- {kind; request = operation; written} :: fixture.actions

let record_no_effect fixture kind operation =
  verify_request fixture operation;
  fixture.actions <- {kind; request = operation; written = 0L} :: fixture.actions

let verify_bytes fixture completed =
  let allowed = fixture.authorized in
  let source = Int64.to_int allowed.source_offset in
  let destination = Int64.to_int allowed.destination_offset in
  let length = Int64.to_int completed in
  for offset = 0 to Bytes.length fixture.stage - 1 do
    let inside = offset >= destination && offset < destination + length in
    let expected = if inside then fixture.basis.[source + offset - destination]
                   else fixture.initial_stage.[offset] in
    check (Bytes.get fixture.stage offset = expected) "byte mismatch or sentinel modified";
    check (fixture.writes.(offset) = if inside then 1 else 0)
      "byte skipped, rewritten or written outside completed prefix"
  done;
  check (fixture.basis = fixture.original_basis) "immutable source changed"

let check_actions fixture expected =
  let actual = List.rev_map (fun action ->
    action.kind, action.request.source_offset, action.request.destination_offset,
    action.request.length, action.written) fixture.actions in
  if actual <> expected then begin
    let describe entries = String.concat "; " (List.map (fun (kind,s,d,n,w) ->
      Printf.sprintf "%s(%Ld,%Ld,%Ld)->%Ld" kind s d n w) entries) in
    failwith ("backend request sequence differs: expected " ^ describe expected ^
              ", actual " ^ describe actual)
  end

exception Cancelled
exception Observer_failure

let empty_prefix : C.prefix = {shared = 0L; copied = 0L}
let prefix ?(shared=0) ?(copied=0) () : C.prefix = {shared = i64 shared; copied = i64 copied}
let total (p : C.prefix) = Int64.add p.shared p.copied
let c_request (r : request) : C.request = {
  source_offset = r.source_offset; destination_offset = r.destination_offset; length = r.length
}
let from_operation (op : C.operation) : request = {
  source_offset = op.source_offset; destination_offset = op.destination_offset; length = op.length
}
let kind_name = function C.Copy -> "Copy" | C.Share -> "Share"

let capabilities ?(alignment=4L) ?(maximum=10L) ?(copy_maximum=7L)
    ?(same_volume_only=true) ?(same_file_allowed=false) () : C.capabilities = {
  native_whole = false; composed_whole = false;
  range = Some {alignment; max_bytes = maximum; same_volume_only; same_file_allowed};
  max_copy_bytes = copy_maximum
}

let bindings fixture : C.bindings = {
  owner_instance = "owner-one"; backend_revision = "constrained-fake-v1";
  source = {volume_id = "volume-A"; generation = 7L; file_id = "immutable-basis";
            size = i64 (String.length fixture.basis)};
  destination = {volume_id = "volume-A"; generation = 7L; file_id = "private-stage";
                 size = i64 (Bytes.length fixture.stage)}
}

type fake = {
  memory : memory;
  capabilities : C.capabilities;
  expected : C.bindings;
  mutable observed : C.bindings;
  mutable calls : C.operation list;
  mutable notices : (C.operation * C.prefix) list;
  mutable observe_count : int;
}

let fake ?caps ?expected fixture =
  let expected = match expected with Some b -> b | None -> bindings fixture in
  let capabilities = match caps with Some c -> c | None -> capabilities () in
  {memory = fixture; capabilities; expected; observed = expected;
   calls = []; notices = []; observe_count = 0}

let same_file (b : C.bindings) =
  b.source.volume_id = b.destination.volume_id && b.source.file_id = b.destination.file_id

(* A fake adapter enforces actual legal calls rather than recomputing a plan.
   Its modulus, maximum, EOF, identity and overlap guards apply even to injected
   responses. If execute sends an illegal call, the test fails before writing. *)
let verify_backend fake (op : C.operation) =
  let request = from_operation op in
  verify_request fake.memory request;
  check (fake.observed = fake.expected) "adapter invoked with a stale binding";
  if same_file fake.observed then
    check (Int64.add op.source_offset op.length <= op.destination_offset ||
           Int64.add op.destination_offset op.length <= op.source_offset)
      "adapter invoked with overlapping source/stage ranges";
  match op.kind with
  | C.Copy -> check (op.length <= fake.capabilities.max_copy_bytes) "copy exceeded actual maximum"
  | C.Share ->
      (match fake.capabilities.range with
       | None -> failwith "share invoked without a range capability"
       | Some rule ->
           check (rule.alignment > 0L && op.length <= rule.max_bytes)
             "share exceeded actual maximum";
           check (Int64.rem op.source_offset rule.alignment = 0L &&
                  Int64.rem op.destination_offset rule.alignment = 0L &&
                  Int64.rem op.length rule.alignment = 0L)
             "share violated independent alignment constraints";
           check (not rule.same_volume_only ||
                  fake.observed.source.volume_id = fake.observed.destination.volume_id)
             "share crossed an incompatible volume pair";
           check (rule.same_file_allowed || not (same_file fake.observed))
             "share used a forbidden source/stage alias")

let reported (result : C.adapter_result) : C.prefix = match result with
  | C.Shared n -> {shared = n; copied = 0L}
  | C.Copied n -> {shared = 0L; copied = n}
  | C.Unsupported r -> r.prefix
  | C.Error r -> r.prefix

let valid_report fake (op : C.operation) (result : C.adapter_result) =
  let p = reported result in
  let bounded = p.shared >= 0L && p.copied >= 0L && p.shared <= op.length &&
                p.copied <= Int64.sub op.length p.shared in
  let shared_legal = p.shared = 0L || match op.kind, fake.capabilities.range with
    | C.Share, Some rule -> Int64.rem p.shared rule.alignment = 0L
    | _ -> false in
  let positive_success = match result with
    | C.Shared n | C.Copied n -> n > 0L
    | C.Unsupported _ | C.Error _ -> true in
  bounded && shared_legal && positive_success

let successful (op : C.operation) = match op.kind with
  | C.Copy -> C.Copied op.length
  | C.Share -> C.Shared op.length

let run ?(check_cancel=(fun () -> ()))
    ?(observe=(fun f -> Ok f.observed))
    ?(response=(fun _ op -> successful op, None))
    ?(notify=(fun _ _ _ -> ())) fake =
  C.execute ~check_cancel ~capabilities:fake.capabilities ~expected:fake.expected
    ~request:(c_request fake.memory.authorized)
    ~observe:(fun () ->
      fake.observe_count <- fake.observe_count + 1;
      match observe fake with
      | Ok b -> fake.observed <- b; Ok b
      | Error e -> Error e)
    ~perform:(fun op ->
      verify_backend fake op;
      fake.calls <- op :: fake.calls;
      let result, actual_override = response (List.length fake.calls) op in
      let actual = match actual_override with
        | Some n -> n
        | None -> if valid_report fake op result then total (reported result) else 0L in
      if actual = 0L then record_no_effect fake.memory (kind_name op.kind) (from_operation op)
      else write fake.memory (kind_name op.kind) (from_operation op) actual;
      result)
    ~notify:(fun op p ->
      check (total p > 0L) "zero progress was notified";
      fake.notices <- (op,p) :: fake.notices;
      notify fake op p) ()

let receipt fake (r : C.receipt) ~shared ~copied =
  check (r.bindings = fake.expected && r.request = c_request fake.memory.authorized)
    "receipt changed request or binding evidence";
  check (r.progress.shared = i64 shared && r.progress.copied = i64 copied)
    "receipt shared/copied accounting incorrect"

let complete fake outcome ~shared ~copied = match outcome with
  | C.Complete r -> receipt fake r ~shared ~copied
  | C.Stopped _ -> failwith "valid reconstruction stopped"

let stopped fake outcome ~shared ~copied fault mutation = match outcome with
  | C.Stopped s ->
      receipt fake s.receipt ~shared ~copied;
      check (fault s.fault) "wrong terminal fault";
      check (s.mutation = mutation) "wrong terminal effect certainty"
  | C.Complete _ -> failwith "failed reconstruction reported complete"

let notices fake expected =
  let actual = List.rev_map (fun (_, (p:C.prefix)) -> p.shared,p.copied) fake.notices in
  check (actual = expected) "completed-prefix notification lost, duplicated or misclassified"

let shared n = i64 n,0L
let copied n = 0L,i64 n
let system_error errno = Unix.Unix_error (errno,"constrained-fake","owned-stage")
let adapter_error errno prefix mutation =
  C.Error {prefix; error = system_error errno; mutation}
let unsupported prefix mutation = C.Unsupported {prefix; reason = "pair-only decline"; mutation}

let adapter_fault errno = function C.Adapter_error e -> e = system_error errno | _ -> false
let invalid_result = function C.Invalid_result _ -> true | _ -> false
let invalid_request = function C.Invalid_request _ -> true | _ -> false
let invalid_capability = function C.Invalid_capability _ -> true | _ -> false
let binding_changed = function C.Binding_changed _ -> true | _ -> false
let adapter_unsupported = function C.Adapter_unsupported s -> s = "pair-only decline" | _ -> false

let action kind source destination length written = kind,i64 source,i64 destination,i64 length,i64 written

let () =
  let cases = [
    "empty", request 5 9 0, [], 0, 0;
    "head only", request 1 9 2, [action "Copy" 1 9 2 2], 0, 2;
    "tail only", request 4 12 3, [action "Copy" 4 12 3 3], 0, 3;
    "exact alignment", request 4 12 4, [action "Share" 4 12 4 4], 4, 0;
    "below maximum", request 0 16 7,
      [action "Share" 0 16 4 4; action "Copy" 4 20 3 3], 4, 3;
    "exact usable maximum", request 0 16 8, [action "Share" 0 16 8 8], 8, 0;
    "one byte beyond maximum", request 0 16 9,
      [action "Share" 0 16 8 8; action "Copy" 8 24 1 1], 8, 1;
    "head, two chunks and tail", request 5 9 22,
      [action "Copy" 5 9 3 3; action "Share" 8 12 8 8;
       action "Share" 16 20 8 8; action "Copy" 24 28 3 3], 16, 6;
    "multiple exact chunks", request 0 32 24,
      [action "Share" 0 32 8 8; action "Share" 8 40 8 8;
       action "Share" 16 48 8 8], 24, 0;
    "unequal residues", request 1 2 17,
      [action "Copy" 1 2 7 7; action "Copy" 8 9 7 7; action "Copy" 15 16 3 3], 0, 17;
    "source boundary EOF", request 188 180 4, [action "Share" 188 180 4 4], 4, 0;
    "destination boundary EOF", request 180 188 4, [action "Share" 180 188 4 4], 4, 0;
  ] in
  List.iter (fun (name,requested,expected,shared_bytes,copied_bytes) ->
    test ("hand-written request: " ^ name) (fun () ->
      let f = fake (memory requested) in
      complete f (run f) ~shared:shared_bytes ~copied:copied_bytes;
      verify_bytes f.memory requested.length;
      check_actions f.memory expected;
      check (List.length f.notices = List.length expected) "notification count differs from completed calls";
      check (f.observe_count = List.length f.calls + 1) "missing per-call or final binding observation")) cases;

  test "deterministic residue/length/max matrix preserves exact bytes" (fun () ->
    let combinations = ref 0 in
    List.iter (fun alignment ->
      List.iter (fun maximum ->
        List.iter (fun source ->
          List.iter (fun destination ->
            List.iter (fun length ->
              let f = fake ~caps:(capabilities ~alignment:(i64 alignment)
                  ~maximum:(i64 maximum) ~copy_maximum:5L ())
                  (memory (request source destination length)) in
              let outcome = run f in
              (match outcome with
               | C.Complete r ->
                   check (total r.progress = i64 length) "matrix lost requested progress";
                   let native = List.fold_left (fun n a ->
                     if a.kind = "Share" then Int64.add n a.written else n) 0L f.memory.actions in
                   check (r.progress.shared = native && r.progress.copied = Int64.sub (i64 length) native)
                     "matrix misclassified ordinary/native bytes"
               | C.Stopped _ -> failwith "valid constrained matrix request stopped");
              verify_bytes f.memory (i64 length);
              incr combinations)
              [0;1;alignment-1;alignment;alignment+1;3*alignment+3])
            [64+source;65+source]) [0;1;3;7]) [1;3;8;10;17]) [1;2;4;8];
    check (!combinations = 960) "matrix cases were accidentally omitted");

  test "maximum smaller than alignment declines sharing and copies bounded chunks" (fun () ->
    let f = fake ~caps:(capabilities ~maximum:2L ()) (memory (request 0 16 12)) in
    complete f (run f) ~shared:0 ~copied:12;
    verify_bytes f.memory 12L;
    check (List.for_all (fun op -> op.C.kind=C.Copy) f.calls)
      "unusable native maximum still triggered sharing");

  test "whole/composed capability flags never authorize range sharing" (fun () ->
    let caps = { (capabilities ()) with C.range = None; native_whole = true; composed_whole = true } in
    let f = fake ~caps (memory (request 0 16 17)) in
    complete f (run f) ~shared:0 ~copied:17;
    verify_bytes f.memory 17L;
    check (List.for_all (fun op -> op.C.kind = C.Copy) f.calls) "whole-file flag enabled range sharing");

  test "a native ordinary-copy success never becomes explicit shared accounting" (fun () ->
    let f = fake (memory (request 0 16 20)) in
    complete f (run ~response:(fun _ op -> C.Copied op.C.length,None) f) ~shared:0 ~copied:20;
    verify_bytes f.memory 20L;
    notices f [copied 8; copied 8; copied 4];
    check (List.for_all (fun op -> op.C.kind = C.Share) f.calls) "native-copy case did not use native adapter");

  test "short aligned Shared prefix advances exact source and stage offsets" (fun () ->
    let f = fake (memory (request 5 9 22)) in
    let response call op = if call = 2 then C.Shared 4L,None else successful op,None in
    complete f (run ~response f) ~shared:16 ~copied:6;
    verify_bytes f.memory 22L;
    check_actions f.memory [action "Copy" 5 9 3 3; action "Share" 8 12 8 4;
      action "Share" 12 16 8 8; action "Share" 20 24 4 4; action "Copy" 24 28 3 3];
    notices f [copied 3; shared 4; shared 8; shared 4; copied 3]);

  test "short unaligned Copied native prefix realigns through ordinary copying" (fun () ->
    let f = fake (memory (request 5 9 22)) in
    let response call op = if call = 2 then C.Copied 3L,None else successful op,None in
    complete f (run ~response f) ~shared:12 ~copied:10;
    verify_bytes f.memory 22L;
    check_actions f.memory [action "Copy" 5 9 3 3; action "Share" 8 12 8 3;
      action "Copy" 11 15 1 1; action "Share" 12 16 8 8;
      action "Share" 20 24 4 4; action "Copy" 24 28 3 3];
    notices f [copied 3; copied 3; copied 1; shared 8; shared 4; copied 3]);

  test "short copy head advances only its actual prefix" (fun () ->
    let f = fake (memory (request 5 9 22)) in
    let response call op = if call = 1 then C.Copied 1L,None else successful op,None in
    complete f (run ~response f) ~shared:16 ~copied:6;
    verify_bytes f.memory 22L;
    check_actions f.memory [action "Copy" 5 9 3 1; action "Copy" 6 10 2 2;
      action "Share" 8 12 8 8; action "Share" 16 20 8 8; action "Copy" 24 28 3 3]);

  test "Unsupported sharing copies only the exact suffix once" (fun () ->
    List.iter (fun failure_call -> List.iter (fun prefix_bytes ->
      let f = fake (memory (request 0 32 24)) in
      let response call op = if call = failure_call
        then unsupported (prefix ~shared:prefix_bytes ()) C.Known_prefix,None
        else successful op,None in
      let earlier = if failure_call = 1 then 0 else 8 in
      let completed = earlier + prefix_bytes in
      complete f (run ~response f) ~shared:completed ~copied:(24-completed);
      verify_bytes f.memory 24L;
      let chronological = List.rev f.calls in
      let rec after n = function [] -> [] | _::rest when n>0 -> after (n-1) rest | rest -> rest in
      check (List.for_all (fun op -> op.C.kind = C.Copy) (after failure_call chronological))
        "sharing was retried after pair-scoped Unsupported";
      check (List.length f.calls <= 6) "suffix fallback was unbounded") [0;4]) [1;2]);

  test "mixed known Unsupported prefix retains both accounting classes" (fun () ->
    let f = fake (memory (request 0 32 20)) in
    let response call op = if call = 1
      then unsupported (prefix ~shared:4 ~copied:2 ()) C.Known_prefix,None
      else successful op,None in
    complete f (run ~response f) ~shared:4 ~copied:16;
    verify_bytes f.memory 20L;
    check_actions f.memory [action "Share" 0 32 8 6;
      action "Copy" 6 38 7 7; action "Copy" 13 45 7 7];
    notices f [4L,2L; copied 7; copied 7]);

  test "Unsupported copying is terminal with no recursive fallback" (fun () ->
    List.iter (fun copied_bytes ->
      let f = fake (memory (request 1 2 17)) in
      let response _ _ = unsupported (prefix ~copied:copied_bytes ()) C.Known_prefix,None in
      stopped f (run ~response f) ~shared:0 ~copied:copied_bytes adapter_unsupported C.Known_prefix;
      verify_bytes f.memory (i64 copied_bytes);
      check (List.length f.calls = 1) "unsupported Copy was retried";
      notices f (if copied_bytes=0 then [] else [copied copied_bytes])) [0;3]);

  test "EIO/ENOSPC/permission/invalid-handle errors retain prefixes and never copy a suffix" (fun () ->
    List.iter (fun errno ->
      List.iter (fun failure_call -> List.iter (fun prefix_bytes ->
        let f = fake (memory (request 0 32 24)) in
        let response call op = if call = failure_call
          then adapter_error errno (prefix ~shared:prefix_bytes ()) C.Known_prefix,None
          else successful op,None in
        let completed = (if failure_call=1 then 0 else 8) + prefix_bytes in
        stopped f (run ~response f) ~shared:completed ~copied:0 (adapter_fault errno) C.Known_prefix;
        verify_bytes f.memory (i64 completed);
        check (List.length f.calls = failure_call) "operational error was retried as copying";
        let expected = (if failure_call=1 then [] else [shared 8]) @
          (if prefix_bytes=0 then [] else [shared prefix_bytes]) in
        notices f expected) [0;4]) [1;2])
      [Unix.EIO; Unix.ENOSPC; Unix.EACCES; Unix.EPERM; Unix.EROFS;
       Unix.EBADF; Unix.EINVAL; Unix.EINTR; Unix.EUNKNOWNERR 12345]);

  test "ordinary-copy operational errors do not become sharing capability results" (fun () ->
    List.iter (fun errno ->
      let f = fake (memory (request 1 2 17)) in
      stopped f (run ~response:(fun _ _ -> adapter_error errno (prefix ~copied:3 ()) C.Known_prefix,None) f)
        ~shared:0 ~copied:3 (adapter_fault errno) C.Known_prefix;
      verify_bytes f.memory 3L;
      check (List.length f.calls = 1) "failed ordinary copying continued";
      notices f [copied 3]) [Unix.EIO;Unix.ENOSPC;Unix.EACCES;Unix.EPERM]);

  test "indeterminate mutation stops with known prefix and requires candidate discard" (fun () ->
    List.iter (fun is_error ->
      let f = fake (memory (request 0 32 20)) in
      let result = if is_error then adapter_error Unix.EIO (prefix ~shared:4 ()) C.Indeterminate
                   else unsupported (prefix ~shared:4 ()) C.Indeterminate in
      let outcome = run ~response:(fun _ _ -> result,Some 5L) f in
      stopped f outcome ~shared:4 ~copied:0
        (if is_error then adapter_fault Unix.EIO else adapter_unsupported) C.Indeterminate;
      check (List.length f.calls = 1) "indeterminate result authorized fallback";
      notices f [shared 4];
      check (f.memory.writes.(36)=1 && Bytes.get f.memory.stage 36=f.memory.basis.[4])
        "indeterminate fake did not actually mutate beyond known prefix";
      for i=0 to 191 do
        check (f.memory.writes.(i)=(if i>=32 && i<37 then 1 else 0))
          "indeterminate mutation was recopied or escaped authorized interval"
      done) [true;false]);

  test "invalid success counts never notify or authorize suffix fallback" (fun () ->
    List.iter (fun result -> List.iter (fun failure_call ->
      let f = fake (memory (request 0 32 24)) in
      let response call op = if call=failure_call then result,None else successful op,None in
      let completed = if failure_call=1 then 0 else 8 in
      stopped f (run ~response f) ~shared:completed ~copied:0 invalid_result C.Indeterminate;
      verify_bytes f.memory (i64 completed);
      check (List.length f.calls=failure_call) "invalid count was retried";
      notices f (if completed=0 then [] else [shared 8])) [1;2])
      [C.Shared 0L; C.Shared (-1L); C.Shared 9L; C.Shared 3L;
       C.Copied 0L; C.Copied (-1L); C.Copied 9L]);

  test "invalid typed prefixes are terminal and discard only their untrusted claim" (fun () ->
    List.iter (fun p -> List.iter (fun make ->
      let f = fake (memory (request 0 32 24)) in
      let response call op = if call=2 then make p,None else successful op,None in
      stopped f (run ~response f) ~shared:8 ~copied:0 invalid_result C.Indeterminate;
      verify_bytes f.memory 8L;
      check (List.length f.calls=2) "invalid prefix continued work";
      notices f [shared 8])
      [(fun p -> unsupported p C.Known_prefix); (fun p -> adapter_error Unix.EIO p C.Known_prefix)])
      [{C.shared=(-1L);copied=0L}; {C.shared=4L;copied=(-1L)};
       {C.shared=8L;copied=1L}; {C.shared=3L;copied=0L};
       {C.shared=Int64.max_int;copied=Int64.max_int}]);

  test "ordinary Copy cannot report explicit Shared bytes" (fun () ->
    List.iter (fun result ->
      let f = fake (memory (request 1 2 17)) in
      stopped f (run ~response:(fun _ _ -> result,None) f) ~shared:0 ~copied:0 invalid_result C.Indeterminate;
      verify_bytes f.memory 0L;
      notices f []) [C.Shared 4L; unsupported (prefix ~shared:4 ()) C.Known_prefix;
        adapter_error Unix.EIO (prefix ~shared:4 ()) C.Known_prefix]);

  test "shifted, inserted, deleted and duplicate references read only immutable basis" (fun () ->
    let m = memory (request 8 0 8) in
    let f = fake m in
    let shared_bytes = ref 0L and copied_bytes = ref 0L in
    let append source destination length =
      m.authorized <- request source destination length;
      match run f with
      | C.Complete r ->
          check (total r.progress=i64 length) "sequential reference lost range bytes";
          shared_bytes := Int64.add !shared_bytes r.progress.shared;
          copied_bytes := Int64.add !copied_bytes r.progress.copied
      | C.Stopped _ -> failwith "sequential reference reconstruction stopped" in
    append 8 0 8;
    Bytes.blit_string "XY" 0 m.stage 8 2;
    m.writes.(8) <- m.writes.(8)+1; m.writes.(9) <- m.writes.(9)+1;
    append 0 10 12;
    append 0 22 8;
    append 20 30 5;
    let reference = String.sub m.basis 8 8 ^ "XY" ^ String.sub m.basis 0 12 ^
      String.sub m.basis 0 8 ^ String.sub m.basis 20 5 in
    check (Bytes.sub_string m.stage 0 35 = reference) "reference bytes were read from evolving stage";
    for i=0 to 191 do
      check (m.writes.(i)=(if i<35 then 1 else 0)) "sequence rewrote bytes or escaped output envelope";
      if i>=35 then check (Bytes.get m.stage i=m.initial_stage.[i]) "sequence changed a trailing sentinel"
    done;
    check (m.basis=m.original_basis && Int64.add !shared_bytes !copied_bytes=33L)
      "sequence corrupted basis or counted inserted bytes as range bytes");

  test "cross-volume compatibility selects copy without probing an illegal native call" (fun () ->
    let m = memory (request 0 32 16) in
    let b = bindings m in
    let b = {b with C.destination = {b.destination with volume_id="volume-B"}} in
    let f = fake ~expected:b m in
    complete f (run f) ~shared:0 ~copied:16;
    verify_bytes m 16L;
    check (List.for_all (fun op -> op.C.kind=C.Copy) f.calls) "incompatible pair was attempted natively";
    let g = fake ~expected:b ~caps:(capabilities ~same_volume_only:false ()) (memory (request 0 32 16)) in
    complete g (run g) ~shared:16 ~copied:0;
    verify_bytes g.memory 16L);

  test "same-file disjoint requests obey the explicit alias constraint" (fun () ->
    List.iter (fun allowed ->
      let m = memory ~stage_from_basis:true (request 0 32 12) in
      let b = bindings m in
      let b = {b with C.destination={b.destination with file_id=b.source.file_id}} in
      let f = fake ~expected:b ~caps:(capabilities ~same_file_allowed:allowed ()) m in
      complete f (run f) ~shared:(if allowed then 12 else 0) ~copied:(if allowed then 0 else 12);
      verify_bytes m 12L;
      check (List.for_all (fun op -> op.C.kind=(if allowed then C.Share else C.Copy)) f.calls)
        "same-file constraint ignored") [false;true]);

  test "same-file overlap rejects before effects even when sharing is unavailable" (fun () ->
    List.iter (fun has_range -> List.iter (fun requested ->
      let m = memory ~stage_from_basis:true requested in
      let b = bindings m in
      let b = {b with C.destination={b.destination with file_id=b.source.file_id}} in
      let caps = capabilities ~same_file_allowed:true () in
      let caps = if has_range then caps else {caps with C.range=None} in
      let f = fake ~expected:b ~caps m in
      stopped f (run f) ~shared:0 ~copied:0 invalid_request C.Known_prefix;
      verify_bytes m 0L;
      check (f.calls=[] && f.notices=[] && f.observe_count=0) "overlap validation performed callbacks")
      [request 4 8 12; request 8 4 12; request 8 8 4]) [false;true]);

  test "same-file touching boundaries are disjoint rather than overlapping" (fun () ->
    List.iter (fun requested ->
      let m = memory ~stage_from_basis:true requested in
      let b = bindings m in
      let b = {b with C.destination={b.destination with file_id=b.source.file_id}} in
      let f = fake ~expected:b ~caps:(capabilities ~same_file_allowed:true ()) m in
      complete f (run f) ~shared:4 ~copied:0;
      verify_bytes m 4L) [request 4 8 4;request 8 4 4]);

  test "invalid offsets/overflow/source EOF/destination EOF reject before callbacks" (fun () ->
    List.iter (fun requested ->
      let m = memory requested in
      let f = fake m in
      stopped f (run f) ~shared:0 ~copied:0 invalid_request C.Known_prefix;
      check (f.calls=[] && f.notices=[] && f.observe_count=0) "invalid range performed callbacks";
      check (Bytes.to_string m.stage=m.initial_stage && Array.for_all ((=) 0) m.writes)
        "invalid range changed stage")
      [{source_offset=(-1L);destination_offset=0L;length=0L};
       {source_offset=0L;destination_offset=(-1L);length=0L};
       {source_offset=0L;destination_offset=0L;length=(-1L)};
       {source_offset=Int64.max_int;destination_offset=0L;length=1L};
       {source_offset=0L;destination_offset=Int64.max_int;length=1L};
       {source_offset=Int64.sub Int64.max_int 1L;destination_offset=0L;length=2L};
       request 191 0 2; request 0 191 2; request 193 0 0; request 0 193 0]);

  test "malformed capabilities reject before observations or writes" (fun () ->
    List.iter (fun caps ->
      let f = fake ~caps (memory (request 0 32 8)) in
      stopped f (run f) ~shared:0 ~copied:0 invalid_capability C.Known_prefix;
      check (f.calls=[] && f.notices=[] && f.observe_count=0) "invalid capability performed callbacks";
      verify_bytes f.memory 0L)
      [capabilities ~alignment:0L (); capabilities ~alignment:(-1L) ();
       capabilities ~maximum:0L (); capabilities ~maximum:(-1L) ();
       capabilities ~copy_maximum:0L (); capabilities ~copy_maximum:(-1L) ()]);

  test "malformed expected binding identities/generations/sizes reject before callbacks" (fun () ->
    let mutations = [
      (fun (b:C.bindings) -> {b with owner_instance=""});
      (fun b -> {b with C.backend_revision=""});
      (fun b -> {b with C.source={b.source with volume_id=""}});
      (fun b -> {b with C.source={b.source with file_id=""}});
      (fun b -> {b with C.source={b.source with generation=(-1L)}});
      (fun b -> {b with C.source={b.source with size=(-1L)}});
      (fun b -> {b with C.destination={b.destination with volume_id=""}});
      (fun b -> {b with C.destination={b.destination with file_id=""}});
      (fun b -> {b with C.destination={b.destination with generation=(-1L)}});
      (fun b -> {b with C.destination={b.destination with size=(-1L)}});
      (fun b -> {b with C.destination={b.destination with file_id=b.source.file_id;size=191L}})
    ] in
    List.iter (fun mutate ->
      let m = memory (request 0 32 8) in
      let f = fake ~expected:(mutate (bindings m)) m in
      stopped f (run f) ~shared:0 ~copied:0 invalid_request C.Known_prefix;
      check (f.calls=[] && f.notices=[] && f.observe_count=0) "malformed binding performed callbacks";
      verify_bytes m 0L) mutations);

  let binding_mutations = [
    "owner restart", (fun (b:C.bindings) -> {b with owner_instance="owner-restarted"});
    "backend revision", (fun b -> {b with C.backend_revision="constrained-fake-v2"});
    "source volume", (fun b -> {b with C.source={b.source with volume_id="replacement-volume"}});
    "source generation", (fun b -> {b with C.source={b.source with generation=8L}});
    "source file", (fun b -> {b with C.source={b.source with file_id="replacement-basis"}});
    "source size", (fun b -> {b with C.source={b.source with size=191L}});
    "destination volume", (fun b -> {b with C.destination={b.destination with volume_id="replacement-volume"}});
    "destination generation", (fun b -> {b with C.destination={b.destination with generation=8L}});
    "destination file", (fun b -> {b with C.destination={b.destination with file_id="replacement-stage"}});
    "destination size", (fun b -> {b with C.destination={b.destination with size=191L}})
  ] in
  test "all stale binding fields stop before first mutation" (fun () ->
    List.iter (fun (_,mutate) ->
      let f = fake (memory (request 0 32 24)) in
      f.observed <- mutate f.expected;
      stopped f (run f) ~shared:0 ~copied:0
        (function C.Binding_changed actual -> actual=f.observed | _ -> false) C.Known_prefix;
      verify_bytes f.memory 0L;
      check (f.calls=[] && f.notices=[]) "stale token selected a replacement target") binding_mutations);

  test "all mid-transfer binding changes retain prefix and stop before another mutation" (fun () ->
    List.iter (fun (_,mutate) ->
      let f = fake (memory (request 0 32 24)) in
      let notify f _ _ = f.observed <- mutate f.expected in
      stopped f (run ~notify f) ~shared:8 ~copied:0 binding_changed C.Known_prefix;
      verify_bytes f.memory 8L;
      check (List.length f.calls=1) "stale mid-transfer binding continued mutation";
      notices f [shared 8]) binding_mutations);

  test "final binding observation prevents complete receipt after last callback changes generation" (fun () ->
    List.iter (fun source_side ->
      let f = fake (memory (request 0 32 8)) in
      let notify f _ _ = f.observed <- if source_side
        then {f.expected with C.source={f.expected.source with generation=8L}}
        else {f.expected with C.destination={f.expected.destination with generation=8L}} in
      stopped f (run ~notify f) ~shared:8 ~copied:0 binding_changed C.Known_prefix;
      verify_bytes f.memory 8L;
      check (List.length f.calls=1 && f.observe_count=2) "final identity check omitted") [false;true]);

  test "empty requests still require fresh matching bindings" (fun () ->
    let f = fake (memory (request 0 32 0)) in
    f.observed <- {f.expected with C.destination={f.expected.destination with generation=8L}};
    stopped f (run f) ~shared:0 ~copied:0 binding_changed C.Known_prefix;
    check (f.calls=[] && f.notices=[] && f.observe_count=1) "empty request skipped binding check");

  test "typed observer failures retain exact earlier prefix without fallback" (fun () ->
    List.iter (fun fail_after_prefix ->
      let f = fake (memory (request 0 32 24)) in
      let exception_ = system_error Unix.EIO in
      let observe f = if not fail_after_prefix || f.calls<>[] then Error exception_ else Ok f.observed in
      let completed = if fail_after_prefix then 8 else 0 in
      stopped f (run ~observe f) ~shared:completed ~copied:0
        (function C.Observation_failed e -> e=exception_ | _ -> false) C.Known_prefix;
      verify_bytes f.memory (i64 completed);
      check (List.length f.calls=(if fail_after_prefix then 1 else 0)) "observation failure continued work")
      [false;true]);

  test "cancellation before and between bounded calls propagates unchanged" (fun () ->
    List.iter (fun completed_calls ->
      let f = fake (memory (request 0 32 24)) in
      let check_cancel () = if List.length f.calls=completed_calls then raise Cancelled in
      let escaped = try ignore(run ~check_cancel f); false with Cancelled -> true in
      check (escaped && List.length f.calls=completed_calls) "cancellation was classified or ignored";
      verify_bytes f.memory (i64 (8*completed_calls));
      notices f (if completed_calls=0 then [] else [shared 8])) [0;1]);

  test "notification exceptions do not enter native error/fallback handling" (fun () ->
    List.iter (fun thrown ->
      let f = fake (memory (request 0 32 24)) in
      let escaped = try ignore(run ~notify:(fun _ _ _ -> raise thrown) f); false
        with e -> e=thrown in
      check (escaped && List.length f.calls=1) "notification exception swallowed or retried";
      verify_bytes f.memory 8L;
      notices f [shared 8]) [Observer_failure;Cancelled;system_error Unix.ENOSYS;system_error Unix.EINVAL]);

  test "notification exceptions on typed error prefixes still propagate without extra work" (fun () ->
    let f = fake (memory (request 0 32 24)) in
    let escaped = try
      ignore(run ~response:(fun _ _ -> adapter_error Unix.EIO (prefix ~shared:4 ()) C.Known_prefix,None)
        ~notify:(fun _ _ _ -> raise Observer_failure) f); false
      with Observer_failure -> true in
    check (escaped && List.length f.calls=1) "typed-error observer exception was classified";
    verify_bytes f.memory 4L;
    notices f [shared 4]);

  test "unexpected adapter/observer/cancellation Unix exceptions remain exceptions" (fun () ->
    List.iter (fun location ->
      let f = fake (memory (request 0 32 24)) in
      let thrown = system_error Unix.ENOSYS in
      let escaped = try
        ignore (match location with
          | "adapter" -> run ~response:(fun _ _ -> raise thrown) f
          | "observer" -> run ~observe:(fun _ -> raise thrown) f
          | _ -> run ~check_cancel:(fun () -> raise thrown) f); false
        with e -> e=thrown in
      check escaped "unexpected Unix exception became an unsupported status";
      check (List.length f.calls=(if location="adapter" then 1 else 0)) "unexpected exception continued work";
      verify_bytes f.memory 0L) ["adapter";"observer";"cancellation"]);

  test "huge valid Int64 request streams bounded operations before cancellation" (fun () ->
    let b = bindings (memory (request 0 32 0)) in
    let b = {b with C.source={b.source with size=Int64.max_int};
                   destination={b.destination with size=Int64.max_int}} in
    let calls = ref 0 and noticed = ref 0L in
    let escaped = try
      ignore(C.execute ~capabilities:(capabilities ~maximum:8L ~copy_maximum:1L ()) ~expected:b
        ~request:{C.source_offset=0L;destination_offset=0L;length=Int64.max_int}
        ~observe:(fun () -> Ok b)
        ~check_cancel:(fun () -> if !calls=5 then raise Cancelled)
        ~perform:(fun op ->
          check (op.C.kind=C.Share && op.length=8L &&
                 op.source_offset=i64 (!calls*8) && op.destination_offset=i64 (!calls*8))
            "huge request lost bounded exact offsets";
          incr calls; C.Shared op.length)
        ~notify:(fun _ p -> noticed := Int64.add !noticed (total p)) ()); false
      with Cancelled -> true in
    check (escaped && !calls=5 && !noticed=40L) "huge range was eagerly expanded or cancellation ignored");

  test "extreme valid offsets and empty maximum offsets preserve checked arithmetic" (fun () ->
    let original = bindings (memory (request 0 32 0)) in
    let b = {original with C.source={original.source with size=Int64.max_int};
                          destination={original.destination with size=Int64.max_int}} in
    List.iter (fun length ->
      let start = Int64.sub Int64.max_int (i64 length) in
      let calls = ref [] and noticed = ref 0L in
      let outcome = C.execute ~capabilities:(capabilities ~alignment:1L ~maximum:2L ()) ~expected:b
        ~request:{C.source_offset=start;destination_offset=start;length=i64 length}
        ~observe:(fun () -> Ok b)
        ~perform:(fun op -> calls := op :: !calls; C.Shared op.C.length)
        ~notify:(fun _ p -> noticed := Int64.add !noticed (total p)) () in
      (match outcome with
       | C.Complete r -> check (r.progress.shared=i64 length && r.progress.copied=0L)
           "extreme valid range lost progress"
       | C.Stopped _ -> failwith "extreme valid range stopped");
      check (!noticed=i64 length) "extreme range notification overflow";
      if length=0 then check (!calls=[]) "empty maximum-offset range invoked adapter"
      else match List.rev !calls with
        | [first;last] ->
            check (first.C.source_offset=start && first.destination_offset=start && first.length=2L &&
                   last.source_offset=Int64.sub Int64.max_int 1L &&
                   last.destination_offset=Int64.sub Int64.max_int 1L && last.length=1L)
              "extreme request offsets wrapped"
        | _ -> failwith "extreme bounded request emitted wrong calls") [0;3]);

  test "fake adapter itself rejects illegal calls independently before mutation" (fun () ->
    let f = fake (memory (request 0 32 24)) in
    List.iter (fun op ->
      let rejected = try verify_backend f op; false with Failure _ -> true in
      check rejected "fake backend accepted an illegal request")
      [{C.kind=C.Share;source_offset=1L;destination_offset=33L;length=4L};
       {C.kind=C.Share;source_offset=0L;destination_offset=32L;length=9L};
       {C.kind=C.Share;source_offset=0L;destination_offset=32L;length=12L};
       {C.kind=C.Copy;source_offset=0L;destination_offset=32L;length=8L};
       {C.kind=C.Copy;source_offset=1L;destination_offset=32L;length=4L};
       {C.kind=C.Copy;source_offset=0L;destination_offset=31L;length=1L};
       {C.kind=C.Copy;source_offset=24L;destination_offset=56L;length=1L}];
    verify_bytes f.memory 0L);

  Printf.printf "CloneRange: %d portable constrained-backend tests passed; no native sharing claim\n%!" !tests
