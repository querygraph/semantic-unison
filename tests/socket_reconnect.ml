(* Private harness: production socket commandLoop and resource admission, with
   deterministic source replies. No archive, photo or live destination writes. *)
open Lwt
module R = RemoteForTest
module A = SemanticAdmission
module H = HelperSupervisor
let require value message = if not value then failwith message
let socket_path = Sys.getenv "UNISON_SCOPE_SOCKET"
let status_path = Sys.getenv "UNISON_SCOPE_STATUS"
let mode = Sys.getenv "UNISON_SCOPE_MODE"
let packet_bytes = 1048576
let cost : A.cost = {payload_bytes=8 * packet_bytes + 262144;descriptors=8}
let admission = A.create ~source_headroom:(Some cost) ~max_transactions:3
  ~max_payload_bytes:(17 * 1048576) ~max_descriptors:16 ~max_pending:16
let calls = ref 0 and disconnects = ref 0
let status () =
  let u = A.usage admission in
  Printf.sprintf "%d %d %d %d %d %d %d"
    (Unix.getpid ()) u.transactions u.pending u.payload_bytes u.descriptors !calls !disconnects
let publish () =
  if mode = "server" then begin
    let temporary = status_path ^ ".new" in
    let channel = open_out temporary in
    output_string channel (status ()); close_out channel;
    Unix.rename temporary status_path
  end
let cancellations = R.resourceWithConnCleanup H.cancel H.cancel_and_cleanup
let scope _ _ f =
  let cancellation = cancellations.register (H.cancellation ()) in
  let result = A.with_lease admission cancellation ~role:A.Source ~cost f in
  publish ();
  try_bind (fun () -> result)
    (fun result -> cancellations.release cancellation; publish ();
      match result with Some () -> return ()
      | None -> fail (Util.Transient "source admission cancelled"))
    (fun error -> cancellations.release_noerr cancellation; publish (); fail error)
let contents value = String.init packet_bytes (fun i -> Char.chr ((i * 71 + value) land 255))
let request = R.registerBoundedServerCmd ~withScope:scope "persistentSourceTest"
  ~maxArgs:64 ~maxResult:(packet_bytes + 1024) Umarshal.int Umarshal.string
  (fun _ value -> incr calls; publish (); return (contents value))
let stats = R.registerBoundedServerCmd "persistentSourceStats"
  ~maxArgs:64 ~maxResult:256 Umarshal.unit Umarshal.string
  (fun _ () -> return (status ()))
let connect () =
  let fd = Unix.socket ~cloexec:true Unix.PF_UNIX Unix.SOCK_STREAM 0 in
  Unix.connect fd (Unix.ADDR_UNIX socket_path);
  fd,Lwt_unix.of_unix_file_descr fd
let parse_status value = match String.split_on_char ' ' value |> List.map int_of_string with
  | [pid;active;pending;payload;descriptors;calls;disconnects] ->
      pid,active,pending,payload,descriptors,calls,disconnects
  | _ -> failwith "malformed test server status"
let read_status () =
  let channel = open_in status_path in
  let value = really_input_string channel (in_channel_length channel) in
  close_in channel; parse_status value
let rec wait_queued remaining =
  let ready = try
    let _,active,pending,payload,descriptors,_,_ = read_status () in
    active=2 && pending=1 && payload=2 * cost.payload_bytes && descriptors=16
    with Sys_error _ -> false in
  if ready then return () else if remaining=0 then failwith "source replies never saturated admission"
  else Lwt_unix.sleep 0.01 >>= fun () -> wait_queued (remaining-1)
let send fd chunks = List.iter (fun (b,p,n) ->
  let s = Bytearray.sub b p n in
  require (Unix.write_substring fd s 0 n=n) "short test request write") chunks
let drop () =
  let fd,socket = connect () in
  let conn = R.makeConnection false socket socket in
  Lwt_unix.run (R.checkHeader conn >>= R.checkServerVersion conn);
  (* Receive the server's initial half-duplex write token, then deliberately
     send requests directly without ever returning that token. The server
     queues replies without an active socket write, reproducing the old leak. *)
  let token = Bytearray.create R.intSize in
  Lwt_unix.run (R.grab conn.R.inputBuffer token R.intSize);
  require (R.decodeInt token 0=0) "server did not relinquish half-duplex write permission";
  List.iter (fun value ->
    let body = Bytearray.of_string ("persistentSourceTest-args" ^ Umarshal.to_string Umarshal.int value) in
    send fd (R.encodeInt (700 + value) ::
      R.marshalHeader conn (R.Request "persistentSourceTest")
        [R.encodeInt (Bytearray.length body);body,0,Bytearray.length body])) [1;2;3];
  Lwt_unix.run (wait_queued 500);
  let pid,_,_,_,_,_,_ = read_status () in
  Lwt_unix.close socket;
  Printf.printf "Dropped half-duplex client after two held source replies and one queued request; server PID %d\n%!" pid
let check () =
  let _,socket = connect () in
  let conn = Lwt_unix.run (R.initConnection socket socket) in
  let pid,active,pending,payload,descriptors,_,closed = parse_status (Lwt_unix.run (stats conn ())) in
  require (pid=int_of_string (Sys.getenv "UNISON_SCOPE_EXPECTED_PID")) "server PID changed on reconnect";
  require (active=0 && pending=0 && payload=0 && descriptors=0 && closed >= 1)
    "socket disconnect retained source admission credits";
  let jobs = List.map (fun value -> value,request conn value) [17;18;19] in
  List.iter (fun (value,job) ->
    require (Lwt_unix.run job=contents value) "reconnected source returned different bytes") jobs;
  let again,active,pending,payload,descriptors,_,_ = parse_status (Lwt_unix.run (stats conn ())) in
  require (again=pid && active=0 && pending=0 && payload=0 && descriptors=0)
    "successful reconnected replies retained resource credits";
  R.clientConnClose conn;
  Printf.printf "Persistent server PID %d: reconnected session completed three exact 1 MiB replies with zero retained admission credits\n%!" pid
let () =
  Sys.set_signal Sys.sigpipe Sys.Signal_ignore;
  match mode with
  | "server" ->
      R.at_conn_close ~only_server:true (fun () -> incr disconnects; publish ());
      publish (); R.waitOnPort [] socket_path
  | "drop" -> drop ()
  | "check" -> check ()
  | _ -> failwith "unknown socket reconnect test mode"
