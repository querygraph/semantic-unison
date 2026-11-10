(* Unison file synchronizer: src/skeletonDelta.ml *)
(* A small binary delta: a target string written as COPY (a range of a base
   string) and INSERT (literal bytes) operations.  It is meant for successive
   skeletons of one file, which differ in a few metadata bytes and some
   offsets; it needs no external compressor.

   Format:
     "SKD1"  varint(base length)  varint(target length)
     then operations until the end:
       0x01 varint(offset in base) varint(length)   COPY
       0x02 varint(length) bytes                    INSERT
       0x00                                         END
   A varint is little-endian base 128.  [apply] checks every bound and both
   lengths; the caller checks the result's SHA-256. *)

let magic = "SKD1"
let window = 16

let add_varint b n =
  if n < 0 then invalid_arg "SkeletonDelta: negative number";
  let rec go n =
    if n < 0x80 then Buffer.add_char b (Char.chr n)
    else begin Buffer.add_char b (Char.chr (0x80 lor (n land 0x7f))); go (n lsr 7) end in
  go n

exception Corrupt of string

let read_varint s pos =
  let rec go acc shift =
    if !pos >= String.length s || shift > 56 then raise (Corrupt "bad number");
    let c = Char.code s.[!pos] in
    incr pos;
    let acc = acc lor ((c land 0x7f) lsl shift) in
    if c land 0x80 = 0 then acc else go acc (shift + 7) in
  go 0 0

(* A multiplicative hash of the [window] bytes at [o]. *)
let hash_at s o =
  let h = ref 0 in
  for k = o to o + window - 1 do
    h := (!h * 0x01000193) lxor Char.code (String.unsafe_get s k)
  done;
  !h land max_int

let make ~base ~target =
  let nb = String.length base and nt = String.length target in
  let out = Buffer.create (64 + nt / 8) in
  Buffer.add_string out magic;
  add_varint out nb;
  add_varint out nt;
  let insert from upto =
    if upto > from then begin
      Buffer.add_char out '\002';
      add_varint out (upto - from);
      Buffer.add_substring out target from (upto - from)
    end in
  if nb >= window && nt >= window then begin
    (* Index the base: every position of a small base, every [step]-th of a
       large one.  A slot keeps the first position that hashed to it. *)
    let step = if nb <= 1 lsl 22 then 1 else window in
    let bits =
      let rec fit k = if k < 24 && (1 lsl k) < 2 * (nb / step + 1) then fit (k + 1) else k in
      fit 10 in
    let mask = (1 lsl bits) - 1 in
    let table = Array.make (1 lsl bits) (-1) in
    let slot h = (h lxor (h lsr 17) lxor (h lsr 31)) land mask in
    let o = ref 0 in
    while !o + window <= nb do
      let k = slot (hash_at base !o) in
      if table.(k) < 0 then table.(k) <- !o;
      o := !o + step
    done;
    let literal = ref 0 and pos = ref 0 in
    while !pos + window <= nt do
      let cand = table.(slot (hash_at target !pos)) in
      let matched =
        if cand < 0 then 0 else begin
          let n = ref 0 in
          while cand + !n < nb && !pos + !n < nt
                && String.unsafe_get base (cand + !n) = String.unsafe_get target (!pos + !n) do
            incr n
          done;
          !n
        end in
      if matched >= window then begin
        (* Extend backwards over bytes waiting to be inserted. *)
        let back = ref 0 in
        while cand - !back > 0 && !pos - !back > !literal
              && String.unsafe_get base (cand - !back - 1)
                 = String.unsafe_get target (!pos - !back - 1) do
          incr back
        done;
        insert !literal (!pos - !back);
        Buffer.add_char out '\001';
        add_varint out (cand - !back);
        add_varint out (matched + !back);
        pos := !pos + matched;
        literal := !pos
      end else incr pos
    done;
    insert !literal nt
  end else insert 0 nt;
  Buffer.add_char out '\000';
  Buffer.contents out

let apply ~base ~delta =
  let n = String.length delta in
  if n < 4 || String.sub delta 0 4 <> magic then raise (Corrupt "not a skeleton delta");
  let pos = ref 4 in
  let nb = read_varint delta pos in
  let nt = read_varint delta pos in
  if nb <> String.length base then raise (Corrupt "delta is against another base");
  let out = Buffer.create nt in
  let rec go () =
    if !pos >= n then raise (Corrupt "delta has no end");
    let op = delta.[!pos] in
    incr pos;
    match op with
    | '\000' -> ()
    | '\001' ->
        let o = read_varint delta pos in
        let l = read_varint delta pos in
        if o > nb || l > nb - o || l > nt - Buffer.length out then raise (Corrupt "copy out of range");
        Buffer.add_substring out base o l;
        go ()
    | '\002' ->
        let l = read_varint delta pos in
        if l > n - !pos || l > nt - Buffer.length out then raise (Corrupt "insert out of range");
        Buffer.add_substring out delta !pos l;
        pos := !pos + l;
        go ()
    | _ -> raise (Corrupt "unknown operation") in
  go ();
  if !pos <> n then raise (Corrupt "bytes after the end of a delta");
  if Buffer.length out <> nt then raise (Corrupt "delta gives another length");
  Buffer.contents out
