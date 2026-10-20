(* A length/count slice, not an absolute end offset. No media input. *)
let () =
 with_connection(fun c _->
  let buffer=Bytearray.of_string"__abc__"in
  Lwt_unix.run(R.fillBuffer c.R.outputBuffer[buffer,2,3]);
  require(c.R.outputBuffer.R.length=3 && Bytes.sub_string c.R.outputBuffer.R.buffer 0 3="abc")
    "DESIGNATED output slice length changed");
 print_endline"RPC output slices: nonzero count golden PASS"

let output_bad thunk message =
 try thunk();failwith message with Invalid_argument _->()
let () =
 let backing=Bytearray.of_string"__abc__"in
 List.iter(fun(pos,len)->
  output_bad(fun()->ignore(R.output_slice_end backing pos len))"DESIGNATED invalid output slice accepted")
  [-1,1;0,-1;8,0;7,1;1,max_int;max_int,0;max_int,max_int];
 require(R.output_slice_end backing 7 0=7)"exact-end empty slice refused";
 require(R.output_length_add max_int 0=max_int)"exact output length refused";
 List.iter(fun(total,len)->output_bad(fun()->ignore(R.output_length_add total len))
   "DESIGNATED output length arithmetic wrapped")[-1,0;0,-1;max_int,1;1,max_int];
 require(R.output_slices_length[backing,2,3;backing,7,0]=3)"slice count summary wrong";
 with_connection(fun c _->
  output_bad(fun()->Lwt_unix.run(R.fillBuffer c.R.outputBuffer
    [backing,2,2;backing,1,max_int]))"invalid trailing slice copied prefix";
  require(c.R.outputBuffer.R.length=0)"DESIGNATED invalid list copied earlier prefix";
  (* Zero-length slices must neither write nor flush an already full buffer. *)
  c.R.outputBuffer.R.length<-R.bufferSize;
  let before= !(R.emittedBytes)in
  Lwt_unix.run(R.fillBuffer c.R.outputBuffer[backing,7,0]);
  require(c.R.outputBuffer.R.length=R.bufferSize && !(R.emittedBytes)=before)
    "DESIGNATED empty slice flushed buffer";
  c.R.outputBuffer.R.length<-0;
  pause_output c;
  List.iter(fun dump->
   let before=Queue.length c.R.outputQueue.R.writes+Queue.length c.R.outputQueue.R.idleWrites+
      Queue.length c.R.outputQueue.R.urgentWrites in
   output_bad(fun()->ignore(dump c[backing,1,max_int]))"DESIGNATED invalid output was queued";
   require(Queue.length c.R.outputQueue.R.writes+Queue.length c.R.outputQueue.R.idleWrites+
      Queue.length c.R.outputQueue.R.urgentWrites=before)"invalid output changed queue")
    [R.dump;R.dumpIdle;R.dumpUrgent]);
 (* Actual private pipe bytes, independently read across multiple flush boundaries.
    No file/Photo payload or mocked copy/write primitive. *)
 let check_pipe mode =
 let input,writer=Lwt_unix.pipe_in()in
 let reader,output=Lwt_unix.pipe_out()in
 let reader=Lwt_unix.of_unix_file_descr reader in
 let outputBuffer=R.makeBuffer output in
 let pendingFlush=ref false and flushes=ref []in
 let q=R.makeOutputQueue false(fun q->
   (* Observe the actual production flush promise; no copying/write primitive
      or scheduler is replaced. Closing waits for each returned borrower. *)
   let work=R.maybeFlush pendingFlush q outputBuffer in
   flushes:=work:: !flushes;work)in
 let c={R.version=1;inputBuffer=R.makeBuffer input;outputBuffer;outputQueue=q}in
 let n=3*R.bufferSize+7 in
 let text=String.init n(fun i->Char.chr(i mod 251))in
 let payload=Bytearray.of_string("-----" ^ text ^ "-----")in
 let expected="[" ^ text ^ "]"in
 let actual=Bytes.create(String.length expected)in
 let rec drain offset =
  if offset=Bytes.length actual then Lwt.return()else
  BorrowedWork.bind(fun()->Lwt_unix.read reader actual offset (Bytes.length actual-offset))(fun count->
   require(count>0)"short private output pipe";drain(offset+count))in
 let rec settle_flushes ()=match !flushes with
  | []->Lwt.return()
  | borrowed->flushes:=[];
    BorrowedWork.bind(fun()->BorrowedWork.all(List.map(fun work->fun()->work)borrowed))
      (fun _->settle_flushes())in
 let cleanup ()=
  let failure=ref None in
  List.iter(fun close->try close()with e->if !failure=None then failure:=Some e)
    [(fun()->Unix.close writer);(fun()->R.closeConnection c);(fun()->Lwt_unix.close reader)];
  match !failure with None->()|Some e->raise e in
 let outcome=try
   let parts=[Bytearray.of_string"[",0,1;payload,5,n;payload,5+n,0;
              Bytearray.of_string"__]",2,1]in
   let write ()=match mode with
    | "fill"->BorrowedWork.bind(fun()->R.fillBuffer c.R.outputBuffer parts)
        (fun()->R.flushBuffer c.R.outputBuffer)
    | "normal"->R.dump c parts
    | "idle"->R.dumpIdle c parts
    | "urgent"->R.dumpUrgent c parts
    | _->assert false in
   ignore(Lwt_unix.run(BorrowedWork.all[write;(fun()->drain 0)]));
   Lwt_unix.run(settle_flushes());
   require(Bytes.to_string actual=expected)"DESIGNATED flushed nonzero slice bytes differ";
   None
  with e->Some e in
 cleanup();(match outcome with None->()|Some e->raise e)in
 List.iter check_pipe["fill";"normal";"idle";"urgent"];
 print_endline"RPC output slices: all-list bounds, checked counts, empty/full behavior and actual multiple-buffer pipe bytes PASS"
