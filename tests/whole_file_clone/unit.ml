open WholeCommon
module W=WholeFileClone
let expected=17L
let decode length raw=W.decode_native ~expected_length:length raw
let rejected raw=
  try ignore(decode expected raw);false with W.Invalid_native_status _->true
let shared=(0,17L,1,12,None,1,0,0L)
let ()=
  test "exact positive Linux/macOS whole completions use Int64"(fun()->
    List.iter(fun backend->List.iter(fun length->
      check((match decode length(0,length,backend,12,None,1,0,0L)with
        W.Native_shared r->r.completed=length &&r.requested=length|_->false))
        "exact whole completion lost Int64 length") [1L;17L;2147483648L;Int64.max_int]) [1;2]);
  test "zero FD work attests no sharing and named empty remains explicit decline"(fun()->
    check((match decode 0L(3,0L,0,12,None,0,0,0L)with W.No_work _->true|_->false))
      "empty FD result changed";
    check((match decode 0L(1,0L,2,4,None,0,6,0L)with W.Declined(W.Empty_source,_)->true|_->false))
      "empty named source became missing-name success";
    check((try ignore(decode 0L(0,0L,1,12,None,1,0,0L));false
      with W.Invalid_native_status _->true)) "zero native sharing was accepted");
  test "valid scoped declines are zero and no-effect with phase-specific evidence"(fun()->
    List.iter(fun raw->check((match decode expected raw with
      W.Declined(_,r)->r.completed=0L &&r.mutation=W.No_effect|_->false))
      "consistent decline failed")
      [(1,0L,0,0,None,0,1,0L);(1,0L,1,9,Some Unix.ENOSYS,0,2,38L);
       (1,0L,1,9,Some Unix.ENOTTY,0,2,25L);
       (1,0L,1,9,Some Unix.EOPNOTSUPP,0,3,95L);
       (1,0L,2,9,Some Unix.EXDEV,0,4,18L);
       (1,0L,1,3,None,0,4,0L);(1,0L,2,8,None,0,4,0L);
       (1,0L,1,2,None,0,5,0L)]);
  test "operational errno-looking failures remain terminal with exact context"(fun()->
    List.iter(fun error->List.iter(fun mutation_tag->
      let result=decode expected(2,0L,1,9,Some error,mutation_tag,0,22L)in
      check((match result with W.Failed r->r.errno=Some error &&r.native_code=22L|_->false))
        "operational error became decline";
      let raised=try(match result with W.Failed r->W.raise_failed ~argument:"fixture" r|_->assert false)
        with exception_value->exception_value in
      check((match raised with Unix.Unix_error(actual,operation,"fixture")->actual=error &&
        String.length operation>0|_->false)) "native error lost errno/context") [0;2])
      [Unix.EINVAL;Unix.EIO;Unix.ENOSPC;Unix.EBADF;Unix.EACCES;Unix.EPERM;
       Unix.ESPIPE;Unix.ENOTSOCK;Unix.EINTR;Unix.EUNKNOWNERR(-1);Unix.EUNKNOWNERR(-50)]);
  test "authoritative full completion on later error never becomes success"(fun()->
    check((match decode expected(2,17L,2,14,Some Unix.EIO,1,0,5L)with
      W.Failed r->r.completed=17L|_->false)) "full-accounted error became success");
  test "all unknown status/backend/phase/effect/scope tags reject"(fun()->
    List.iter(fun raw->check(rejected raw) "unknown whole-file tag accepted")
      [(9,17L,1,12,None,1,0,0L);(0,17L,9,12,None,1,0,0L);
       (0,17L,1,99,None,1,0,0L);(0,17L,1,12,None,9,0,0L);
       (1,0L,0,0,None,0,99,0L)]);
  test "negative oversized and short completion reject including Int64 bounds"(fun()->
    List.iter(fun count->check(rejected(0,count,1,12,None,1,0,0L))
      "partial/invalid whole completion accepted")[-1L;0L;3L;18L;Int64.max_int];
    check(rejected(2,3L,1,9,Some Unix.EIO,1,0,5L)) "partial error prefix accepted");
  test "success errno/decline/effect/backend/phase contradictions reject"(fun()->
    List.iter(fun raw->check(rejected raw) "malformed sharing authority accepted")
      [(0,17L,1,12,Some Unix.EIO,1,0,5L);(0,17L,1,12,None,1,1,0L);
       (0,17L,1,12,None,0,0,0L);(0,17L,1,12,None,2,0,0L);
       (0,17L,0,12,None,1,0,0L);(0,17L,1,9,None,1,0,0L)]);
  test "decline mutation or progress never grants fallback"(fun()->
    List.iter(fun raw->check(rejected raw) "unsafe decline accepted")
      [(1,0L,0,0,None,2,1,0L);(1,17L,1,9,Some Unix.EOPNOTSUPP,1,3,95L);
       (1,0L,1,9,Some Unix.EINVAL,0,3,22L);
       (1,0L,1,9,Some Unix.EIO,0,3,5L);
       (1,0L,1,2,Some Unix.EOPNOTSUPP,0,3,95L);
       (1,0L,0,0,Some Unix.EINVAL,0,1,22L)]);
  test "scope/backend/native-error contradictions reject"(fun()->
    List.iter(fun raw->check(rejected raw) "contradictory scope accepted")
      [(1,0L,2,9,Some Unix.ENOTTY,0,2,25L);
       (1,0L,0,9,Some Unix.EOPNOTSUPP,0,3,95L);
       (1,0L,1,9,Some Unix.ENOSYS,0,2,0L);
       (1,0L,1,9,None,0,3,95L);
       (1,0L,1,4,None,0,6,0L)]);
  test "failure phase/count/effect contradictions reject"(fun()->
    List.iter(fun raw->check(rejected raw) "invalid terminal receipt accepted")
      [(2,0L,1,9,None,2,0,0L);(2,0L,0,0,Some Unix.EIO,0,0,5L);
       (2,0L,0,9,Some Unix.EIO,2,0,5L);(2,17L,1,4,Some Unix.EIO,1,0,5L);
       (2,0L,1,4,Some Unix.EIO,2,0,5L);(2,0L,1,9,Some Unix.EIO,1,0,5L);
       (2,17L,1,12,Some Unix.EIO,0,0,5L)]);
  test "current native errno widths do not accept arbitrary signed/64-bit codes"(fun()->
    List.iter(fun code->check(rejected(2,0L,1,9,Some Unix.EIO,2,0,code))
      "unsupported native code width accepted")[-1L;2147483648L;Int64.max_int]);
  test "platform preflight retains opaque unsigned DWORD bits in Int64"(fun()->
    check((match decode expected(2,0L,0,1,Some Unix.EBADF,0,0,4294967295L)with
      W.Failed r->r.native_code=4294967295L|_->false))
      "platform failure truncated opaque unsigned native code";
    check(rejected(2,0L,0,1,Some Unix.EBADF,0,0,4294967296L))
      "platform failure accepted wider than DWORD" );
  test "typed receipts receive same consistency checks as decoded values"(fun()->
    let receipt=match decode expected shared with W.Native_shared r->r|_->assert false in
    List.iter(fun result->check((try ignore(W.validate_result ~expected_length:expected result);false
      with W.Invalid_native_status _->true)) "typed invalid result bypassed checks")
      [W.Native_shared{receipt with requested=18L};
       W.Declined(W.Platform_unavailable,{receipt with completed=0L;backend=W.Platform;
         phase=W.Unavailable;mutation=W.Indeterminate});
       W.Failed{receipt with errno=None}]);
  test "negative expected length is rejected before trusting any receipt"(fun()->
    check((try ignore(decode (-1L)shared);false with Invalid_argument _->true))
      "negative request accepted");
  Printf.printf "Whole typed result: %d groups/%d assertions\n%!" !groups !assertions
