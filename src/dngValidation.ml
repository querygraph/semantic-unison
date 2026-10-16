open Lwt

type policy = Off | Warn | Require
exception Candidate_changed
type snapshot = { sha256 : string; size : int64; identity : string }
type tool = {
  executable : string;
  executable_sha256 : string;
  build_id : string;
  arguments : string array;
  environment : string array;
  cpu_weight : int;
  limits : HelperSupervisor.limits;
}
type raw_digest = Valid | Missing | Mismatch | Unsupported | Not_checked
type report = {
  candidate_sha256 : string;
  candidate_size : int64;
  driver_build : string;
  structure : string;
  decode : string;
  raw_digest : raw_digest;
  errors : int;
  warnings : int;
}

let all_chars predicate s =
  let rec loop i = i = String.length s || predicate s.[i] && loop (i + 1) in
  loop 0
let sha256 s = String.length s = 64 && all_chars (function
  | '0' .. '9' | 'a' .. 'f' -> true | _ -> false) s
let build_id s = String.length s > 0 && String.length s <= 128 &&
  all_chars (function
    | 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '.' | '_' | '-' -> true
    | _ -> false) s
let decimal s = s <> "" && (String.length s = 1 || s.[0] <> '0') &&
  all_chars (function '0' .. '9' -> true | _ -> false) s
let field name line =
  let prefix = name ^ " " in
  let n = String.length prefix in
  if String.length line <= n || String.sub line 0 n <> prefix then
    failwith ("missing or malformed field: " ^ name);
  String.sub line n (String.length line - n)
let number name s =
  if not (decimal s) then failwith ("invalid decimal: " ^ name);
  try int_of_string s with Failure _ -> failwith ("decimal overflow: " ^ name)
let size s =
  if not (decimal s) then failwith "invalid candidate-size";
  try Int64.of_string s with Failure _ -> failwith "candidate-size overflow"
let one_of name values s =
  if not (List.mem s values) then failwith ("invalid " ^ name); s

let parse_report text =
  try
    if String.length text > 4096 then failwith "validation receipt exceeds 4096 bytes";
    match String.split_on_char '\n' text with
    | ["UNISON-DNG-VALIDATION 1"; hash; bytes; build; structure; decode;
       raw; errors; warnings; "END"; ""] ->
        let candidate_sha256 = field "candidate-sha256" hash in
        if not (sha256 candidate_sha256) then failwith "invalid candidate-sha256";
        let candidate_size = size (field "candidate-size" bytes) in
        let driver_build = field "driver-build" build in
        if not (build_id driver_build) then failwith "invalid driver-build";
        let structure = one_of "structure" ["valid"; "invalid"; "unsupported"]
          (field "structure" structure) in
        let decode = one_of "decode" ["success"; "failure"; "unsupported"; "not_checked"]
          (field "decode" decode) in
        let raw_digest = match field "raw-digest" raw with
          | "valid" -> Valid | "missing" -> Missing | "mismatch" -> Mismatch
          | "unsupported" -> Unsupported | "not_checked" -> Not_checked
          | _ -> failwith "invalid raw-digest" in
        let errors = number "errors" (field "errors" errors) in
        let warnings = number "warnings" (field "warnings" warnings) in
        Ok { candidate_sha256; candidate_size; driver_build; structure; decode;
             raw_digest; errors; warnings }
    | _ -> Error "malformed validation receipt (expected protocol v1 exact fields)"
  with Failure message -> Error message

type receipt = {
  candidate : snapshot;
  executable_sha256 : string;
  build_id : string;
  report : report;
  process : HelperSupervisor.result;
}
type result =
  | Skipped
  | Passed of receipt
  | Warning of string * HelperSupervisor.result option
  | Rejected of string * HelperSupervisor.result option

let same_snapshot a b =
  a.sha256 = b.sha256 && a.size = b.size && a.identity = b.identity
let check_snapshot s =
  if not (sha256 s.sha256) || s.size < 0L || s.identity = "" then
    failwith "invalid inspected snapshot"
exception Candidate_inspection_failed of string

let validate_with_execution ?process_limits ?observe_group ?observe_alive ~execute supervisor cancellation ~policy ~(tool : tool option) ~inspect ~candidate ~expected =
  match policy with
  | Off -> return Skipped
  | Warn | Require ->
    let process = ref None in
    let execution_started = ref false in
    let inspected_tool = ref None in
    let reject message = return (match policy with
      | Warn -> Warning (message, !process)
      | Require -> Rejected (message, !process)
      | Off -> assert false) in
    let validation () = BorrowedWork.catch (fun () ->
      (try
        if Filename.is_relative candidate || String.contains candidate '\000' then
          failwith "candidate must be an absolute NUL-free path";
        check_snapshot expected
       with exn -> raise (Candidate_inspection_failed (Printexc.to_string exn)));
      let tool = match tool with Some tool -> tool
        | None -> failwith "DNG validation requested but no qualified SDK driver configured" in
      if not (sha256 tool.executable_sha256) || not (build_id tool.build_id) then
        failwith "invalid configured SDK driver pin/build ID";
      BorrowedWork.bind (fun () -> BorrowedWork.catch (fun () ->
        BorrowedWork.bind (fun () -> inspect candidate) (fun before ->
        check_snapshot before;
        if not (same_snapshot before expected) then raise Candidate_changed;
        return before))
        (function
          | Candidate_changed as exn -> fail exn
          | exn -> fail (Candidate_inspection_failed (Printexc.to_string exn)))) (fun before ->
      BorrowedWork.bind (fun () -> inspect tool.executable) (fun tool_before ->
      check_snapshot tool_before;
      if tool_before.sha256 <> tool.executable_sha256 then failwith "SDK driver content pin mismatch";
      inspected_tool := Some (tool.executable, tool_before);
      let arguments = Array.append tool.arguments [|
        "--unison-dng-validation-v1";
        "--expected-sha256"; expected.sha256;
        "--expected-size"; Int64.to_string expected.size;
        "--threads"; string_of_int tool.cpu_weight;
        "--"; candidate |] in
      BorrowedWork.bind (fun () -> execute (fun () ->
        execution_started := true;
        HelperSupervisor.run ?process_limits ?observe_group ?observe_alive supervisor ~weight:tool.cpu_weight cancellation
          ~limits:tool.limits ~executable:tool.executable ~arguments
          ~environment:tool.environment)) (fun child ->
      process := Some child;
      (match child.HelperSupervisor.outcome with
       | HelperSupervisor.Completed -> ()
       | HelperSupervisor.Cancelled -> failwith "SDK driver cancelled"
       | HelperSupervisor.Timed_out -> failwith "SDK driver timed out"
       | HelperSupervisor.Output_limit -> failwith "SDK driver exceeded output limit"
       | HelperSupervisor.Failed message -> failwith ("SDK driver unavailable: " ^ message));
      if child.output_truncated then failwith "SDK driver output truncated";
      if child.status <> Some (Unix.WEXITED 0) then failwith "SDK driver exited unsuccessfully";
      let report = match parse_report child.stdout with
        | Ok report -> report | Error message -> failwith message in
      if report.candidate_sha256 <> expected.sha256 || report.candidate_size <> expected.size then
        failwith "SDK driver receipt identifies a different candidate";
      if report.driver_build <> tool.build_id then failwith "SDK driver build ID mismatch";
      if report.errors <> 0 then failwith "SDK driver reported validation errors";
      if report.structure <> "valid" then failwith "DNG structure invalid or unsupported";
      if report.decode <> "success" then failwith "DNG raw decode failed or was not completed";
      (match report.raw_digest with
       | Valid | Missing -> ()
       | Mismatch -> failwith "DNG raw digest mismatch"
       | Unsupported | Not_checked -> failwith "DNG raw digest verification unsupported or not completed");
      return (Passed { candidate = before; executable_sha256 = tool.executable_sha256;
                       build_id = tool.build_id; report; process = child })))))
      (function
        | Candidate_changed -> return (Rejected ("candidate changed before validation", !process))
        | Candidate_inspection_failed message ->
            return (Rejected ("candidate inspection failed: " ^ message, !process))
        | exn -> reject (Printexc.to_string exn)) in
    BorrowedWork.bind validation (fun verdict ->
    (* Warn relaxes validator findings, never the immutable-candidate fence or
       the user's cancellation. Check even malformed/nonzero helper results. *)
    if HelperSupervisor.is_cancelled cancellation then
      return (Rejected ("DNG validation cancelled", !process))
    else if not !execution_started then return verdict
    else BorrowedWork.catch (fun () ->
      BorrowedWork.bind (fun () -> inspect candidate) (fun after ->
      check_snapshot after;
      if not (same_snapshot expected after) then
        failwith "candidate changed during validation";
      BorrowedWork.bind (fun () -> match !inspected_tool with
       | None -> fail (Failure "SDK driver identity unavailable")
       | Some (path, before) -> BorrowedWork.bind (fun () -> inspect path) (fun after ->
           check_snapshot after;
           if not (same_snapshot before after) then
             failwith "SDK driver changed during validation";
           return ())) (fun () -> return verdict)))
      (fun exn -> return (Rejected (Printexc.to_string exn, !process))))

let validate supervisor cancellation ~policy ~tool ~inspect ~candidate ~expected =
  validate_with_execution ~execute:(fun run -> run ()) supervisor cancellation
    ~policy ~tool ~inspect ~candidate ~expected
