(* A packed directory: the files of one directory D stored as members of one
   SQLite archive D.sqlar (docs/packdir-design.md). The standard sqlar table is
   what stock tools read (sqlite3 D.sqlar -AxC D); unison_member keeps what
   Unison needs (nanosecond mtime, archive fingerprint, SHA-256, retained
   deletions); unison_container the format and an epoch bumped by every
   committed batch. Blobs are stored raw. *)

module N = Dng_archive.Native

let format = "unison-packdir/1"
let fpalg = "unison-md5/1" (* Unison's archive fingerprint: MD5 of the bytes *)

type journal = Delete | Wal

type t = { db : Sqlite3.db; path : string; journal : journal }

type member = {
  name : string; size : int64; mtime_ns : int64; fp : string; fpalg : string;
  sha256 : string; retained : bool;
}

let check db what rc =
  if not (Sqlite3.Rc.is_success rc) then
    failwith (Printf.sprintf "%s: %s (%s)" what (Sqlite3.Rc.to_string rc) (Sqlite3.errmsg db))

let exec db sql = check db sql (Sqlite3.exec db sql)

let query db sql params =
  let st = Sqlite3.prepare db sql in
  Fun.protect ~finally:(fun () -> ignore (Sqlite3.finalize st)) (fun () ->
    List.iteri (fun i p -> check db "bind" (Sqlite3.bind st (i + 1) p)) params;
    let rec rows acc = match Sqlite3.step st with
      | Sqlite3.Rc.ROW -> rows (Sqlite3.row_data st :: acc)
      | Sqlite3.Rc.DONE -> List.rev acc
      | rc -> check db sql rc; List.rev acc in
    rows [])

let run db sql params = ignore (query db sql params)
let text s = Sqlite3.Data.TEXT s
let blob s = Sqlite3.Data.BLOB s
let int64 n = Sqlite3.Data.INT n
let to_int64 = function Sqlite3.Data.INT n -> n | _ -> failwith "expected an integer"
let to_string = function Sqlite3.Data.TEXT s | Sqlite3.Data.BLOB s -> s | _ -> failwith "expected text"

let schema = {|
CREATE TABLE IF NOT EXISTS sqlar(name TEXT PRIMARY KEY, mode INT, mtime INT, sz INT, data BLOB);
CREATE TABLE IF NOT EXISTS unison_member(name TEXT PRIMARY KEY REFERENCES sqlar(name),
  mtime_ns INT NOT NULL, fp BLOB NOT NULL, fpalg TEXT NOT NULL, sha256 BLOB NOT NULL,
  retained_deleted INT NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS unison_container(key TEXT PRIMARY KEY, value TEXT);
|}

(* Open D.sqlar, creating it with its page size and vacuum mode, which must be
   set before the first table. The journal is set on every open. *)
let open_ ?(journal = Delete) path =
  let fresh = not (Sys.file_exists path) in
  let db = Sqlite3.db_open path in
  Sqlite3.busy_timeout db 60000;
  if fresh then (exec db "PRAGMA page_size = 65536"; exec db "PRAGMA auto_vacuum = INCREMENTAL");
  (* A rollback journal deleted at each commit: about one transaction per
     container per run, and no -journal file left beside it. *)
  exec db (match journal with Delete -> "PRAGMA journal_mode = DELETE" | Wal -> "PRAGMA journal_mode = WAL");
  exec db "PRAGMA synchronous = FULL";
  (* F_FULLFSYNC on macOS: flush the drive's cache, which fsync does not. *)
  exec db "PRAGMA fullfsync = ON";
  exec db "PRAGMA checkpoint_fullfsync = ON";
  exec db schema;
  (match query db "SELECT value FROM unison_container WHERE key='format'" [] with
   | [] -> run db "INSERT INTO unison_container VALUES ('format', ?), ('epoch', '0')" [text format]
   | [ [| Sqlite3.Data.TEXT f |] ] when f = format -> ()
   | _ -> ignore (Sqlite3.db_close db); failwith (path ^ ": not a " ^ format ^ " container"));
  { db; path; journal }

let close c =
  if c.journal = Wal then exec c.db "PRAGMA wal_checkpoint(TRUNCATE)";
  ignore (Sqlite3.db_close c.db)

let epoch c = match query c.db "SELECT value FROM unison_container WHERE key='epoch'" [] with
  | [ [| Sqlite3.Data.TEXT e |] ] -> int_of_string e | _ -> 0

(* The member table: one indexed query, no member data read. *)
let members c =
  List.map (fun r -> {
      name = to_string r.(0); size = to_int64 r.(1); mtime_ns = to_int64 r.(2); fp = to_string r.(3);
      fpalg = to_string r.(4); sha256 = to_string r.(5); retained = to_int64 r.(6) <> 0L })
    (query c.db "SELECT m.name, s.sz, m.mtime_ns, m.fp, m.fpalg, m.sha256, m.retained_deleted \
                 FROM unison_member m JOIN sqlar s ON s.name = m.name ORDER BY m.name" [])

let read c name = match query c.db "SELECT data FROM sqlar WHERE name = ?" [text name] with
  | [ [| d |] ] -> to_string d | _ -> raise Not_found

type put = { member : string; source : string } (* member name, plain file to store *)

let crash_after = match Sys.getenv_opt "UNISON_PACKDIR_CRASH_AFTER" with
  | Some n -> int_of_string_opt n | None -> None (* tests: exit inside a transaction *)

(* One batch: every put and retained deletion in transactions of at most
   [batch_bytes] of member data, the epoch bumped in each; then the changed
   blobs are read back and their SHA-256 compared, before the caller may
   record them anywhere. Returns the bytes stored. *)
let apply ?(batch_bytes = 256 * 1048576) c ~puts ~retain =
  let stored = ref 0 and in_txn = ref 0 and done_puts = ref 0 in
  let begin_ () = exec c.db "BEGIN IMMEDIATE" in
  let commit () =
    run c.db "UPDATE unison_container SET value = CAST(value AS INTEGER) + 1 WHERE key = 'epoch'" [];
    exec c.db "COMMIT" in
  begin_ ();
  (try
     List.iter (fun p ->
       if String.contains p.member '/' then failwith ("member name with a slash: " ^ p.member);
       let st = N.stat p.source in
       if st.N.kind <> `Reg then failwith (p.source ^ ": not a regular file");
       let data = In_channel.with_open_bin p.source In_channel.input_all in
       let st' = N.stat p.source in
       (* Reading moves atime; identity, size, mtime and ctime must hold. *)
       if Int64.of_int (String.length data) <> st.N.size || st'.N.ino <> st.N.ino || st'.N.size <> st.N.size
          || st'.N.mtime_ns <> st.N.mtime_ns || st'.N.ctime_ns <> st.N.ctime_ns then
         failwith (p.source ^ ": changed while read");
       if !in_txn > 0 && !in_txn + String.length data > batch_bytes then (commit (); begin_ (); in_txn := 0);
       run c.db "INSERT OR REPLACE INTO sqlar(name, mode, mtime, sz, data) VALUES (?, ?, ?, ?, ?)"
         [text p.member; int64 (Int64.of_int (0o100000 lor st.N.mode));
          int64 (Int64.div st.N.mtime_ns 1_000_000_000L); int64 st.N.size; blob data];
       run c.db "INSERT OR REPLACE INTO unison_member(name, mtime_ns, fp, fpalg, sha256, retained_deleted) \
                 VALUES (?, ?, ?, ?, ?, 0)"
         [text p.member; int64 st.N.mtime_ns; blob (Digest.string data); text fpalg; blob (N.sha_string data)];
       in_txn := !in_txn + String.length data; stored := !stored + String.length data;
       incr done_puts;
       if crash_after = Some !done_puts then Unix._exit 3) puts;
     List.iter (fun name -> run c.db "UPDATE unison_member SET retained_deleted = 1 WHERE name = ?" [text name]) retain;
     commit ()
   with e -> ignore (Sqlite3.exec c.db "ROLLBACK"); raise e);
  (* Read back what this batch wrote. *)
  List.iter (fun p ->
    match query c.db "SELECT s.data, m.sha256 FROM sqlar s JOIN unison_member m ON m.name = s.name WHERE s.name = ?"
            [text p.member] with
    | [ [| d; h |] ] when N.sha_string (to_string d) = to_string h -> ()
    | _ -> failwith (c.path ^ ": " ^ p.member ^ " did not read back")) puts;
  !stored

(* Problems found: the structure check, then every member's SHA-256 and the
   pairing of the two tables. *)
let verify c =
  let problems = ref [] in
  (match query c.db "PRAGMA integrity_check" [] with
   | [ [| Sqlite3.Data.TEXT "ok" |] ] -> ()
   | rows -> List.iter (fun r -> problems := ("integrity: " ^ to_string r.(0)) :: !problems) rows);
  List.iter (fun r ->
    let name = to_string r.(0) in
    match r.(1), r.(2) with
    | Sqlite3.Data.NULL, _ -> problems := (name ^ ": no unison_member row") :: !problems
    | h, d ->
        let d = to_string d in
        if N.sha_string d <> to_string h then problems := (name ^ ": SHA-256 mismatch") :: !problems
        else if Digest.string d <> to_string r.(3) then problems := (name ^ ": fingerprint mismatch") :: !problems)
    (query c.db "SELECT s.name, m.sha256, s.data, m.fp FROM sqlar s LEFT JOIN unison_member m ON m.name = s.name" []);
  List.iter (fun r -> problems := (to_string r.(0) ^ ": unison_member row without data") :: !problems)
    (query c.db "SELECT m.name FROM unison_member m LEFT JOIN sqlar s ON s.name = m.name WHERE s.name IS NULL" []);
  List.rev !problems

(* Bring D.sqlar up to date with the plain directory [dir]: new and changed
   files (by size and nanosecond mtime) are stored, files gone from [dir] are
   kept and marked retained. Names in [skip] (plain files already beside the
   container) are left out. Returns (stored, retained, bytes). *)
let update ?batch_bytes ?(skip = []) c dir =
  let have = Hashtbl.create 256 in
  List.iter (fun m -> Hashtbl.replace have m.name m) (members c);
  let names = List.sort compare (List.filter (fun n ->
      match N.stat ~follow:false (Filename.concat dir n) with
      | s -> s.N.kind = `Reg && not (List.mem n skip) | exception Unix.Unix_error _ -> false)
      (Array.to_list (Sys.readdir dir))) in
  let puts = List.filter_map (fun n ->
    let st = N.stat (Filename.concat dir n) in
    match Hashtbl.find_opt have n with
    | Some m when m.size = st.N.size && m.mtime_ns = st.N.mtime_ns && not m.retained -> None
    | _ -> Some { member = n; source = Filename.concat dir n }) names in
  let present = Hashtbl.create 256 in
  List.iter (fun n -> Hashtbl.replace present n ()) names;
  let retain = Hashtbl.fold (fun n m acc -> if Hashtbl.mem present n || m.retained then acc else n :: acc) have [] in
  let bytes = if puts = [] && retain = [] then 0 else apply ?batch_bytes c ~puts ~retain in
  List.length puts, List.length retain, bytes

(* Write every member to [out] with its mode and nanosecond mtime, SHA-256
   checked; retained deletions too unless [skip_retained]. *)
let restore ?(skip_retained = false) c out =
  N.mkdir_p out;
  List.iter (fun m ->
    if not (skip_retained && m.retained) then begin
      let d = read c m.name in
      if N.sha_string d <> m.sha256 then failwith (m.name ^ ": SHA-256 mismatch");
      let target = Filename.concat out m.name in
      if Sys.file_exists target then failwith (target ^ " exists");
      Out_channel.with_open_bin target (fun oc -> output_string oc d);
      (match query c.db "SELECT mode FROM sqlar WHERE name = ?" [text m.name] with
       | [ [| Sqlite3.Data.INT mode |] ] -> Unix.chmod target (Int64.to_int mode land 0o7777)
       | _ -> ());
      N.utimens target m.mtime_ns m.mtime_ns
    end) (members c)
