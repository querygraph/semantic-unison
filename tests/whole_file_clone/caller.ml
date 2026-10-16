open WholeCommon
module Copy = CopyForTest
module N = Copy.WholeCloneForTest
module W = N.W
let directory = Sys.argv.(1)
let selected = if Array.length Sys.argv>2 then Sys.argv.(2) else "current"
let expected_errno = ref Unix.EIO
let behavior = ref "shared"
let raw_failed ?(completed=0L) ?(mutation_tag=0) ?(phase=9) error =
  (2,completed,1,phase,Some error,mutation_tag,0,22L)
let decode expected raw = W.decode_native ~expected_length:expected raw
let shared expected = decode expected (0,expected,1,12,None,1,0,0L)
let no_work () = decode 0L (3,0L,0,12,None,0,0,0L)
let unavailable expected = decode expected (1,0L,0,0,None,0,1,0L)
let set_hook mode =
  behavior:=mode;
  N.file_hook := (fun ~expected_length source destination ->
    if size source <> expected_length then
      decode expected_length (raw_failed ~phase:4 Unix.EBUSY)
    else match mode with
    | "shared" ->
        if expected_length=0L then no_work () else begin
          Fault.exact_copy source destination expected_length;shared expected_length end
    | "decline" -> unavailable expected_length
    | "throw" -> raise Fault.primary
    | "error" -> decode expected_length (raw_failed !expected_errno)
    | "full-error" ->
        Fault.exact_copy source destination expected_length;
        decode expected_length(raw_failed ~completed:expected_length ~mutation_tag:1 ~phase:12 !expected_errno)
    | "unknown-extra" ->
        Fault.exact_copy source destination (min expected_length 3L);
        Fault.write_at destination (Int64.add expected_length 7L) "?";
        decode expected_length(raw_failed ~mutation_tag:2 !expected_errno)
    | "indeterminate-decline" ->
        Fault.write_at destination (Int64.add expected_length 7L) "?";
        decode expected_length(1,0L,0,0,None,2,1,0L)
    | "short-success" ->
        Fault.exact_copy source destination 3L;
        decode expected_length(0,3L,1,12,None,1,0,0L)
    | "typed-invalid-decline" ->
        (match unavailable expected_length with
         | W.Declined(scope,receipt)->W.Declined(scope,{receipt with mutation=W.Indeterminate})
         | _->assert false)
    | "typed-short-success" ->
        (match shared expected_length with
         | W.Native_shared receipt->W.Native_shared{receipt with completed=3L}
         | _->assert false)
    | "typed-wrong-request" ->
        (match shared expected_length with
         | W.Native_shared receipt->W.Native_shared{receipt with requested=Int64.succ expected_length}
         | _->assert false)
    | _ -> invalid_arg "unrecognized fixture behavior");
  N.legacy_file_hook := (fun source destination ->
    if mode="unknown-extra" then begin
      Fault.write_at destination 20L "?";false
    end else begin Fault.exact_copy source destination(size source);true end)
let reset () =
  N.file_calls:=[];N.path_calls:=[];N.range_calls:=0;
  N.legacy_file_calls:=0;N.legacy_path_calls:=0;
  N.poison_legacy := not(String.starts_with ~prefix:"parent-" selected);
  set_hook "shared"
let invoke ?(owned=true) ?expected f =
  let length=match expected with None->Int64.of_int(String.length f.data)|Some n->n in
  let fallback_lengths=ref [] and progress=ref [] in
  let fallback remaining =
    fallback_lengths:=Uutil.Filesize.toInt64 remaining::!fallback_lengths;
    Uutil.readWriteBounded f.input f.output remaining
      (fun count->progress:=Int64.of_int count::!progress) in
  Copy.copyFile ~clone_owned:owned f.input f.output `DATA
    (Uutil.Filesize.ofInt64 length) fallback
    (fun n->progress:=Uutil.Filesize.toInt64 n::!progress);
  !fallback_lengths,!progress
let completion f =
  check(bytes f.destination_path=f.data) "cloned whole bytes differ";
  let ending=Int64.of_int(String.length f.data) in
  check(size f.destination_fd=ending) "DESIGNATED whole clone accepted wrong expected EOF";
  check(LargeFile.pos_out f.output=ending && position f.destination_fd=ending)
    "DESIGNATED whole clone left cached/native output cursor before EOF";
  output_string f.output "!";flush f.output;
  check(bytes f.destination_path=f.data^"!")
    "DESIGNATED following literal overwrote cloned bytes instead of appending"
let () =
  let baseline=Fault.fd_count() in
  if selected="parent-cursor" then begin
    reset();fixture directory(fun f->ignore(invoke f);completion f)
  end else if selected="parent-length" then begin
    reset();fixture directory ~length:17(fun f->
      ignore(invoke ~expected:16L f);flush f.output;
      check(size f.destination_fd=16L)
        "DESIGNATED whole clone accepted wrong expected EOF")
  end else if selected="parent-error" then begin
    reset();set_hook "unknown-extra";
    fixture directory ~length:17(fun f->
      ignore(invoke f);flush f.output;
      check(!(N.range_calls)=0)
        "DESIGNATED failed clone authorized ordinary fallback after unknown effects")
  end else if selected="negative-decline-effects" then begin
    reset();set_hook "indeterminate-decline";
    fixture directory(fun f->
      let result=try ignore(invoke f);None with error->Some error in
      let actual=bytes f.destination_path in
      check(result<>None && !(N.range_calls)=0 &&
            String.length actual=String.length f.data+8 &&
            actual.[String.length f.data+7]='?')
        "DESIGNATED indeterminate decline authorized fallback or erased extra effect")
  end else begin
    test "native whole success reconciles output before following literal"(fun()->
      reset();fixture directory(fun f->
        let fallback,progress=invoke f in
        check(fallback=[] && progress=[Int64.of_int(String.length f.data)] &&
              List.length !(N.file_calls)=1 && !(N.range_calls)=0)
          "whole success routes/progress differ";
        completion f));
    test "buffered logical-zero source survives eligible clone unchanged"(fun()->
      reset();fixture directory(fun f->
        ignore(Fault.prefetch f.input);
        let logical=LargeFile.pos_in f.input and native=position f.source_fd in
        check(logical=0L && native>0L) "fixture did not establish logical-zero native read-ahead";
        ignore(invoke f);
        check(LargeFile.pos_in f.input=logical && position f.source_fd=native)
          "whole clone consumed or reset buffered input";
        check(input_char f.input=f.data.[0]) "whole clone changed next unread source byte";
        completion f));
    test "consumed input and absent ownership skip whole optimization"(fun()->
      List.iter(fun consumed->reset();fixture directory(fun f->
        if consumed then ignore(input_char f.input);
        set_hook "throw";ignore(invoke ~owned:consumed f);flush f.output;
        check(!(N.file_calls)=[] && !(N.range_calls)>0 && bytes f.destination_path=f.data)
          "ineligible input/ownership reached native whole clone or changed ordinary DATA behavior")) [false;true]);
    test "pending output and native/logical offsets preserve ordinary prefix"(fun()->
      List.iter(fun kind->reset();fixture directory(fun f->
        (match kind with
         | "buffered" -> output_string f.output "PREFIX"
         | "flushed" -> output_string f.output "PREFIX";flush f.output
         | "native-only" -> ignore(Unix.LargeFile.lseek f.destination_fd 6L Unix.SEEK_SET)
         | _ -> LargeFile.seek_out f.output 6L);
        set_hook "throw";ignore(invoke f);flush f.output;
        let prefix=if kind="hole" ||kind="native-only" then String.make 6 '\000' else "PREFIX" in
        check(!(N.file_calls)=[] && bytes f.destination_path=prefix^f.data)
          "ineligible output was overwritten by whole clone"))
        ["buffered";"flushed";"hole";"native-only"]);
    test "nonempty offset-zero output skips whole acceleration without resetting ordinary DATA"(fun()->
      reset();fixture directory(fun f->
        Fault.write_at f.destination_fd 0L "KEEP";set_hook "throw";
        ignore(invoke f);flush f.output;
        check(!(N.file_calls)=[] && !(N.range_calls)=1 &&bytes f.destination_path=f.data)
          "nonempty native output was incorrectly treated as owned empty clone destination"));
    test "valid no-effect decline performs bounded ordinary fallback once"(fun()->
      reset();set_hook "decline";fixture directory(fun f->
        let fallback,progress=invoke f in
        check(fallback=[Int64.of_int(String.length f.data)] &&
              List.length !(N.file_calls)=1 && !(N.range_calls)=1)
          "scoped decline retried or failed to use exact fallback";
        check(List.fold_left Int64.add 0L progress=Int64.of_int(String.length f.data))
          "fallback double counted progress";
        completion f));
    test "expected EOF mismatches and Int64 extremes never fall back"(fun()->
      List.iter(fun expected->reset();fixture directory ~length:17(fun f->
        let error=failed(fun()->ignore(invoke ~expected f)) in
        let _=error in
        check(!(N.range_calls)=0 && size f.destination_fd=0L && LargeFile.pos_out f.output=0L)
          "length mismatch created bytes or selected fallback")) [0L;16L;18L;Int64.max_int]);
    test "zero FD request returns no-work without sharing or fallback"(fun()->
      reset();fixture directory ~length:0(fun f->
        let fallback,progress=invoke f in
        check(fallback=[] && !(N.range_calls)=0 && size f.destination_fd=0L &&
              LargeFile.pos_out f.output=0L && position f.source_fd=0L &&
              List.for_all((=)0L)progress) "zero FD operation copied or claimed positive progress"));
    test "terminal errno-looking failures never become fallback"(fun()->
      List.iter(fun error->List.iter(fun mode->reset();expected_errno:=error;set_hook mode;
        fixture directory(fun f->
          let thrown=failed(fun()->ignore(invoke f)) in
          check(errno error thrown) "native operational errno/context was lost";
          check(!(N.range_calls)=0 && List.length !(N.file_calls)=1)
            "operational clone failure retried/fell back";
          check(size f.destination_fd=(if mode="full-error" then Int64.of_int(String.length f.data) else 0L))
            "terminal full/empty error effects changed")) ["error";"full-error"])
        [Unix.EINVAL;Unix.EIO;Unix.ENOSPC;Unix.EACCES;Unix.EBADF;Unix.ESPIPE;
         Unix.ENOTSOCK;Unix.EUNKNOWNERR(-1);Unix.EUNKNOWNERR(-50)]);
    test "indeterminate extra writes survive failure without retry"(fun()->
      reset();set_hook "unknown-extra";
      fixture directory(fun f->
        ignore(failed(fun()->ignore(invoke f)));
        let actual=bytes f.destination_path in
        check(!(N.range_calls)=0 && String.length actual=String.length f.data+8 &&
              actual.[String.length f.data+7]='?')
          "DESIGNATED failed clone authorized ordinary fallback after unknown effects"));
    test "malformed decline and short whole success stop without fallback"(fun()->
      List.iter(fun mode->reset();set_hook mode;fixture directory(fun f->
        ignore(failed(fun()->ignore(invoke f)));
        check(!(N.range_calls)=0 && List.length !(N.file_calls)=1)
          "malformed whole receipt retried or fell back"))
        ["indeterminate-decline";"short-success";"typed-invalid-decline";
         "typed-short-success";"typed-wrong-request"]);
    test "callback and synchronous native exceptions retain original failure"(fun()->
      reset();set_hook "throw";fixture directory(fun f->
        check(failed(fun()->ignore(invoke f))=Fault.primary && !(N.range_calls)=0)
          "synchronous clone exception was replaced/retried");
      reset();fixture directory(fun f->
        check(failed(fun()->Copy.copyFile ~clone_owned:true f.input f.output `DATA
          (Uutil.Filesize.ofInt(String.length f.data))(fun _->failwith "fallback reached")
          (fun _->raise Fault.primary))=Fault.primary)
          "progress callback exception was replaced";
        check(!(N.range_calls)=0 && List.length !(N.file_calls)=1)
          "callback error caused another copy operation"));
    check(!(N.legacy_file_calls)=0 && !(N.legacy_path_calls)=0)
      "production routed through poisoned legacy boolean clone API"
  end;
  check(Fault.fd_count()=baseline) "whole caller fixture leaked descriptors";
  Printf.printf "Whole Copy caller: %d groups, %d assertions; synthetic sharing only\n%!" !groups !assertions
