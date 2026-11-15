(* The SQLite guard: only a quiet database is synchronized.
   See docs/sqlite-semantic-design.md, "The guard", and sqliteGuard.mli. *)

let debug = Trace.debug "sqliteguard"

(* ---- Preferences and the feature ---- *)

(* Whether this run asks for a guard the other host cannot give; set once the
   preferences exist. *)
let unmet = ref (fun () -> None)

(* Both hosts must treat the same names as companions, or one would offer a
   write-ahead log the other had skipped.  So the guard is a negotiated
   feature, and its preferences reach only a peer that offers it. *)
let feature =
  Features.register "sqlite-guard-v0" ~arcFormatChange:false
    (Some (fun _ enabled -> if enabled then None else !unmet ()))

let send () = Features.enabled feature

let sqlitedb =
  Pred.create "sqlitedb" ~category:(`Advanced `Sync) ~send
    ("Including the preference \\texttt{-sqlitedb \\ARG{pathspec}} names the "
     ^ "paths that are SQLite databases.  For such a path Unison never "
     ^ "propagates the files SQLite keeps beside it (\\verb|-journal|, "
     ^ "\\verb|-wal| and \\verb|-shm|), and, as the \\verb|sqlitequiet| "
     ^ "preference says, synchronizes the database only while it is "
     ^ "{\\em quiet}: while no unfinished transaction or write-ahead log "
     ^ "beside it holds changes the file itself lacks.  A matching path "
     ^ "that is not a SQLite file is an ordinary file.  Both hosts must "
     ^ "offer this feature.")

let sqlitequiet =
  Prefs.createString "sqlitequiet" "require" ~send
    ~category:(`Advanced `Sync)
    "what to do with a SQLite database that is not quiet (off, warn or require)"
    ("This preference applies to the paths named by \\verb|sqlitedb|.  With "
     ^ "\\verb|require|, the default, a database that is not quiet is not "
     ^ "propagated, replaced or deleted; the path fails with a message "
     ^ "naming the file that shows it, and the next run tries again.  With "
     ^ "\\verb|warn| the same message is printed and the path is "
     ^ "synchronized anyway.  With \\verb|off| nothing is checked.  The "
     ^ "files beside a database are not propagated in any of the three.")

type policy = Off | Warn | Require

let policy () =
  match String.lowercase_ascii (Prefs.read sqlitequiet) with
  | "off" -> Off
  | "warn" -> Warn
  | "require" -> Require
  | other ->
      raise (Util.Fatal
        ("The preference sqlitequiet must be off, warn or require, not '"
         ^ other ^ "'"))

let warned = ref false

let () =
  unmet := (fun () ->
    if Pred.extern sqlitedb = [] then None
    else if policy () = Require then
      Some "The sqlitedb preference needs a Unison with the SQLite guard \
            (sqlite-guard-v0) on both hosts; without it set sqlitequiet to \
            warn or off, and the files beside a database are synchronized \
            as ordinary files"
    else begin
      if not !warned then begin
        warned := true;
        Util.warn
          "The other host has no SQLite guard: the sqlitedb preference is \
           without effect in this run."
      end;
      None
    end)

let suffixes = ["-journal"; "-wal"; "-shm"]

let stem s =
  List.find_map (fun suffix ->
    if String.ends_with ~suffix s && String.length s > String.length suffix
    then Some (String.sub s 0 (String.length s - String.length suffix))
    else None) suffixes

let companion s =
  Features.enabled feature &&
  (match stem s with
   | None -> false
   | Some database -> Pred.test sqlitedb database)

let guarded path =
  Features.enabled feature && Pred.test sqlitedb (Path.toString path) &&
  policy () <> Off

(* ---- Reading ---- *)

let with_file fspath f =
  match Fs.openfile fspath [Unix.O_RDONLY] 0 with
  | exception Unix.Unix_error ((Unix.ENOENT | Unix.ENOTDIR), _, _) -> None
  | fd ->
      Some (Fun.protect ~finally:(fun () -> try Unix.close fd with _ -> ())
              (fun () -> f fd))

(* Read up to [len] bytes at [pos]; the count is short only at end of file. *)
let read_at fd pos buf len =
  ignore (Unix.LargeFile.lseek fd pos Unix.SEEK_SET);
  let rec loop got =
    if got = len then got else
    match Unix.read fd buf got (len - got) with
    | 0 -> got
    | n -> loop (got + n) in
  loop 0

let size_of fd = (Unix.LargeFile.fstat fd).Unix.LargeFile.st_size

let be32 b off = Int32.to_int (Bytes.get_int32_be b off) land 0xffffffff
let le32 b off = Int32.to_int (Bytes.get_int32_le b off) land 0xffffffff

let power_of_two n = n > 0 && n land (n - 1) = 0

(* ---- The main file ---- *)

let magic = "SQLite format 3\000"

(* The page size, or None for a header this guard doesn't understand. *)
let page_size header =
  match Bytes.get_uint16_be header 16 with
  | 1 -> Some 65536
  | n when n >= 512 && n <= 32768 && power_of_two n -> Some n
  | _ -> None

(* ---- The rollback journal ---- *)

let journal_magic = "\xd9\xd5\x05\xf9\x20\xa1\x63\xd7"

type journal = No_journal | Finished | Hot | Unrecognised

(* SQLite ends a transaction by deleting the journal, truncating it, or
   overwriting its 28-byte header with zeros.  A journal that still has its
   header belongs to a transaction that is running or was interrupted.  That
   header starts with the magic number once the journal has been synced;
   until then SQLite leaves the magic and the record count zero and the rest
   of the header (nonce, sizes) in place, which is as much a transaction. *)
let journal fspath =
  match
    with_file fspath (fun fd ->
      let b = Bytes.make 28 '\000' in
      let n = read_at fd 0L b 28 in
      if n = 0 then Finished
      else if n >= 8 && Bytes.sub_string b 0 8 = journal_magic then Hot
      else if Bytes.for_all (fun c -> c = '\000') b then Finished
      else if n = 28 && Bytes.sub_string b 0 12 = String.make 12 '\000' then Hot
      else Unrecognised)
  with
  | None -> No_journal
  | Some j -> j

(* ---- The write-ahead log ---- *)

(* The log's checksum: two running sums over 32-bit words, in the byte order
   the header's magic number names. *)
let checksum ~le buf off len (s0, s1) =
  let get = if le then le32 else be32 in
  let s0 = ref s0 and s1 = ref s1 and i = ref off in
  while !i < off + len do
    s0 := (!s0 + get buf !i + !s1) land 0xffffffff;
    s1 := (!s1 + get buf (!i + 4) + !s0) land 0xffffffff;
    i := !i + 8
  done;
  (!s0, !s1)

type wal = {
  wal_page_size : int;
  valid : int;        (* frames valid from the start of the log *)
  committed : int;    (* of those, frames up to the last commit *)
  db_pages : int;     (* the database's size after the last commit *)
  last : (int, int) Hashtbl.t;
      (* page number -> index of the frame with its last committed version *)
  unfinished : bool;
      (* the log ends at a frame that carries its salts but is cut short or
         fails its checksum: one being written, or left by a crash *)
}

let wal_header = 32 and frame_header = 24

(* Walk the log as SQLite's recovery does: a frame counts while its salts
   match the header's and the running checksum agrees; the first that fails
   ends the log, whatever follows.  None when the header itself is not a
   valid one, which SQLite treats as an empty log.

   Recovery ignores a frame with the right salts and a wrong checksum.  The
   guard doesn't: SQLite rewrites the frames a large transaction spills and
   corrects their checksums only when it commits, so such a frame is how a
   transaction in progress looks from outside. *)
let scan_wal fd =
  let size = size_of fd in
  let h = Bytes.create wal_header in
  if size < Int64.of_int wal_header || read_at fd 0L h wal_header < wal_header
  then None else
  let m = be32 h 0 in
  let ps = be32 h 8 in
  if (m <> 0x377f0682 && m <> 0x377f0683) || be32 h 4 <> 3007000
     || ps < 512 || ps > 65536 || not (power_of_two ps) then None else
  let le = m = 0x377f0682 in
  let sum = checksum ~le h 0 24 (0, 0) in
  if sum <> (be32 h 24, be32 h 28) then None else
  let salt1 = be32 h 16 and salt2 = be32 h 20 in
  let frame = frame_header + ps in
  let b = Bytes.create frame in
  let last = Hashtbl.create 64 in
  let rec walk i sum pending valid committed db_pages =
    let pos = Int64.add (Int64.of_int wal_header)
                (Int64.mul (Int64.of_int i) (Int64.of_int frame)) in
    let finish unfinished =
      Some { wal_page_size = ps; valid; committed; db_pages; last; unfinished } in
    let got = read_at fd pos b frame in
    let ours () =
      be32 b 0 <> 0 && be32 b 8 = salt1 && be32 b 12 = salt2 in
    if got < frame then finish (got >= frame_header && ours ()) else
    if not (ours ()) then finish false else
    let page = be32 b 0 in
    let sum = checksum ~le b frame_header ps (checksum ~le b 0 8 sum) in
    if sum <> (be32 b 16, be32 b 20) then finish true else
    let pending = (page, i) :: pending in
    match be32 b 4 with
    | 0 -> walk (i + 1) sum pending (valid + 1) committed db_pages
    | pages ->
        List.iter (fun (page, i) -> Hashtbl.replace last page i)
          (List.rev pending);
        walk (i + 1) sum [] (valid + 1) (valid + 1) pages in
  walk 0 sum [] 0 0 0

(* Does the main file already hold everything the log committed? *)
let wal_adds_nothing ~main ~main_page_size wal_fd wal =
  wal.wal_page_size = main_page_size
  && size_of main =
       Int64.mul (Int64.of_int wal.db_pages) (Int64.of_int main_page_size)
  && begin
    let ps = main_page_size in
    let a = Bytes.create ps and b = Bytes.create ps in
    let frame = frame_header + ps in
    try
      Hashtbl.iter (fun page i ->
        if page <= wal.db_pages then begin
          let in_wal = Int64.add (Int64.of_int (wal_header + frame_header))
                         (Int64.mul (Int64.of_int i) (Int64.of_int frame)) in
          let in_main = Int64.mul (Int64.of_int (page - 1)) (Int64.of_int ps) in
          if read_at wal_fd in_wal a ps < ps || read_at main in_main b ps < ps
             || not (Bytes.equal a b) then raise Exit
        end) wal.last;
      true
    with Exit -> false
  end

(* ---- The verdict ---- *)

type state = Not_database | Quiet | Redundant_wal of int | Busy of string

let beside root path suffix =
  Fspath.concat root (Path.addSuffixToFinalName path suffix)

let plural n what = Printf.sprintf "%d %s%s" n what (if n = 1 then "" else "s")

let inspect root path =
  let fspath = Fspath.concat root path in
  let name = Filename.basename (Fspath.toString fspath) in
  Util.convertUnixErrorsToTransient ("checking the SQLite database " ^ name)
    (fun () ->
      let found =
        with_file fspath (fun main ->
          let header = Bytes.make 100 '\000' in
          if read_at main 0L header 100 < 100
             || Bytes.sub_string header 0 16 <> magic then Not_database
          else
          match journal (beside root path "-journal") with
          | Hot ->
              Busy (name ^ "-journal holds a transaction that is running or \
                            was interrupted")
          | Unrecognised ->
              Busy (name ^ "-journal is neither empty nor a finished journal")
          | No_journal | Finished ->
          match
            with_file (beside root path "-wal") (fun wal_fd ->
              match scan_wal wal_fd with
              | None -> Quiet
              | Some wal when wal.valid > wal.committed || wal.unfinished ->
                  Busy (name ^ "-wal holds frames of a transaction that is \
                                running or was interrupted")
              | Some wal when wal.committed = 0 -> Quiet
              | Some wal ->
                  match page_size header with
                  | Some main_page_size
                    when wal_adds_nothing ~main ~main_page_size wal_fd wal ->
                      Redundant_wal wal.committed
                  | _ ->
                      Busy (Printf.sprintf
                        "%s-wal holds %s the database file lacks" name
                        (plural wal.committed "committed frame")))
          with
          | None -> Quiet
          | Some state -> state) in
      match found with
      | None -> Not_database   (* no such file *)
      | Some state -> state)

let advice = "; close the application that has it open, or checkpoint it"

let report path reason =
  let message =
    Printf.sprintf "The SQLite database %s is not quiet: %s%s"
      (Path.toString path) reason advice in
  match policy () with
  | Require -> raise (Util.Transient message)
  | Warn -> Util.warn message
  | Off -> ()

let check_sending root path =
  if guarded path then
    match inspect root path with
    | Not_database | Quiet | Redundant_wal _ -> ()
    | Busy reason -> report path reason

let check_receiving_file root path =
  if guarded path then
    match inspect root path with
    | Not_database | Quiet -> ()
    | Redundant_wal frames ->
        report path
          (Printf.sprintf
             "%s-wal holds %s, and replacing or deleting the database under \
              it would corrupt the next open"
             (Filename.basename (Path.toString path))
             (plural frames "valid frame"))
    | Busy reason -> report path reason

(* A directory about to be replaced or deleted takes its databases with it. *)
let rec check_receiving_tree root path =
  match (Fs.lstat (Fspath.concat root path)).Unix.LargeFile.st_kind with
  | exception Unix.Unix_error _ -> ()
  | Unix.S_REG -> check_receiving_file root path
  | Unix.S_DIR ->
      List.iter (fun name -> check_receiving_tree root (Path.child path name))
        (try Os.childrenOf root path with Util.Transient _ -> [])
  | _ -> ()

let check_receiving root path =
  if Features.enabled feature && Pred.extern sqlitedb <> [] && policy () <> Off
  then begin
    debug (fun () ->
      Util.msg "check_receiving %s\n" (Path.toString path));
    check_receiving_tree root path
  end
