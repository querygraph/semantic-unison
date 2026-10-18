module T=TransferForTest
module F=RemoteFieldsForTest
let checks=ref 0
let check x why=incr checks;if not x then failwith why
let transient f=match f()with
 | _->failwith "malformed transfer accepted"
 | exception Util.Transient _->incr checks
let fatal f=match f()with
 | _->failwith "malformed integer accepted"
 | exception Util.Fatal _->incr checks
let read name=let c=open_in_bin name in
 Fun.protect ~finally:(fun()->close_in c)(fun()->really_input_string c(in_channel_length c))
let write name s=let c=open_out_bin name in
 Fun.protect ~finally:(fun()->close_out c)(fun()->output_string c s)
let data s=Bytearray.of_string s
let string_token s="S"^String.init 2(fun i->Char.chr((String.length s lsr(i*8))land 255))^s
let block n k="B"^String.init 3(fun i->Char.chr((n lsr(i*8))land 255))^String.make 1(Char.chr k)
let with_channels f=
 write "basis" "abcdefgh";
 let input=open_in_bin "basis" and output=open_out_bin "output"in
 Fun.protect ~finally:(fun()->close_in input;close_out output)(fun()->f input output)
let malformed mode bytes=
 with_channels(fun input output->T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
     transient(fun()->if mode then T.Rsync.rsyncDecompress 4 input output ignore(data bytes,0,String.length bytes)
                      else T.receive output ignore(data bytes,0,String.length bytes))));
 check(read "output"="")"syntactically malformed frame wrote output"
let ()=
 let field,_,_=F.encodeInt 17 in
 check(F.decodeInt field 0=17)"valid integer changed";
 List.iter(fun i->fatal(fun()->F.decodeInt field i))[-1;min_int;max_int;1;5];
 for length=0 to F.intSize-1 do
  fatal(fun()->F.decodeInt(Bytearray.create length)0)
 done;
 let _,decode=CopyWireForTest.marshalTransferInstruction in
 List.iter(fun n->fatal(fun()->decode ()(Bytearray.create n)0))[0;1;2;3;4];
 let frame=data("xx"^Bytearray.to_string field^"payload")in
 let id,(same,pos,len)=decode () frame 2 in
 check(id=17&&same==frame&&pos=7&&len=7)"copy wire is not exact raw-buffer view";
 List.iter(fun pos->fatal(fun()->decode ()frame pos))[-1;min_int;max_int;Bytearray.length frame];
 (* Valid literal prefix followed by invalid framing must not emit that prefix. *)
 List.iter(fun mode->List.iter(malformed mode)
   [string_token "ok"^"?";"S";"S\001";"S\004\000abc";"E?";"EE";"?"])[false;true];
 List.iter(malformed true)["B";"B\000";"B\000\000";"B\000\000\000";block 0 0];
 malformed false(block 0 1);
 List.iter(fun mode->with_channels(fun input output->
   List.iter(fun(pos,len)->T.test_forbid_io:=true;
     Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->transient(fun()->
       if mode then T.Rsync.rsyncDecompress 4 input output ignore(data"E",pos,len)
       else T.receive output ignore(data"E",pos,len))))
     [-1,1;min_int,0;max_int,0;0,-1;0,max_int;1,1]))[false;true];
 with_channels(fun input output->
   List.iter(fun size->transient(fun()->T.Rsync.rsyncDecompress size input output ignore(data"E",0,1)))
    [0;-1];
   check(T.Rsync.rsyncDecompress max_int input output ignore(data"E",0,1))
     "unused large positive block size refused EOF";
   List.iter(fun token->transient(fun()->T.Rsync.rsyncDecompress max_int input output
     ~copyFn:(fun _ _ ~fallback:_->failwith "overflow reached copy callback")
     ignore(data token,0,String.length token)))[block 0 2;block 3 1]);
 with_channels(fun input output->T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
     transient(fun()->T.Rsync.rsyncDecompress 4 input output
       ~copyFn:(fun _ _ ~fallback:_->failwith "DESIGNATED invalid basis range reached copy callback")
       ignore(data(block 2 1),0,5))));
 check(read"output"="")"out-of-basis block wrote output";
 with_channels(fun input output->
   List.iter(fun copied->transient(fun()->T.Rsync.rsyncDecompress 4 input output
     ~copyFn:(fun _ _ ~fallback->fallback(Uutil.Filesize.ofInt copied))
     ignore(data(block 0 1),0,5)))[-1;5]);
 (* Concurrent truncation after range inspection, before fallback read. The
    normal channel read really returns short; no stale buffer bytes may write. *)
 with_channels(fun input output->T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
    transient(fun()->T.Rsync.rsyncDecompress 4 input output
     ~copyFn:(fun _ _ ~fallback->Unix.truncate "basis" 3;fallback(Uutil.Filesize.ofInt 0))
     ignore(data(block 0 2),0,5))));
 check(read"output"="")"short basis read wrote stale bytes";
 with_channels(fun _ output->
   check(not(T.receive output ignore(data"",0,0)))"empty frame marked EOF";
   let s=string_token"ab"^string_token"cd"^"E"in
   check(T.receive output ignore(data s,0,String.length s))"valid literal EOF missing");
 check(read"output"="abcd")"valid literal bytes changed";
 with_channels(fun input output->
   let s=block 1 1^string_token"XY"^"E"in
   check(T.Rsync.rsyncDecompress 4 input output ignore(data s,0,String.length s))"valid block EOF missing");
 check(read"output"="efghXY")"valid rsync bytes changed";
 (* A block group larger than the copy buffer exercises the recursive arm;
    a later short chunk must never re-emit stale buffer contents. *)
 let big=String.init 24576(fun i->Char.chr((i*13+9)land 255))in
 with_channels(fun input output->write"basis"big;
   let token=block 0 3^"E"in
   check(T.Rsync.rsyncDecompress 8192 input output ignore(data token,0,String.length token))
     "multi-buffer block group EOF missing");
 check(read"output"=big)"multi-buffer block copy duplicated or lost bytes";
 with_channels(fun input output->write"basis"big;T.test_write_budget:=8192;
   Fun.protect ~finally:(fun()->T.test_write_budget:=max_int)(fun()->
    transient(fun()->T.Rsync.rsyncDecompress 8192 input output
      ~copyFn:(fun _ _ ~fallback->Unix.truncate "basis" 8195;fallback(Uutil.Filesize.ofInt 0))
      ignore(data(block 0 3),0,5))));
 check(read"output"=String.sub big 0 8192)"chunked short read changed valid prefix";
 (* Both endpoints must obey a nonzero view offset and its selected end,
    even when complete token bytes exist outside the allowed slice. *)
 List.iter(fun rsync->with_channels(fun input output->
   let body=if rsync then block 1 1^"E"else string_token"slice"^"E"in
   let bytes=data("xx"^body^"outside")in
   check((if rsync then T.Rsync.rsyncDecompress 4 input output ignore(bytes,2,String.length body)
          else T.receive output ignore(bytes,2,String.length body)))"nonzero view lost EOF");
   check(read"output"=(if rsync then "efgh"else "slice"))"nonzero view consumed outside bytes") [false;true];
 List.iter(fun rsync->with_channels(fun input output->T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
    let body=if rsync then block 0 1 else string_token"abc"in
    let bytes=data("xx"^body^"outside")in
    transient(fun()->if rsync then T.Rsync.rsyncDecompress 4 input output ignore(bytes,2,4)
                     else T.receive output ignore(bytes,2,3)))))[false;true];
 (* Partial/full optimized callbacks and a prepopulated receiver-basis skip.
    These are callback contracts, not native clone or physical-sharing proof. *)
 List.iter(fun copied->with_channels(fun input output->
   let s=block 1 1^"E"in
   check(T.Rsync.rsyncDecompress 4 input output
     ~copyFn:(fun offset length ~fallback->
       check(Uutil.Filesize.toInt offset=4 && Uutil.Filesize.toInt length=4)"copy callback range changed";
       output_string output(String.sub "efgh" 0 copied);
       fallback(Uutil.Filesize.ofInt copied))
     ignore(data s,0,String.length s))"partial fallback EOF missing");
   check(read"output"="efgh")"partial/full optimized fallback bytes changed") [0;2;4];
 with_channels(fun input output->
   write"output""abcdefgh";
   let called=ref 0 and s=block 0 1^"E"in
   check(T.Rsync.rsyncDecompress 4 input output
     ~copyFn:(fun offset length ~fallback:_->
       incr called;check(Uutil.Filesize.toInt offset=0 && Uutil.Filesize.toInt length=4)"skip range changed";
       flush output;LargeFile.seek_out output 4L)
     ignore(data s,0,String.length s))"prepopulated skip EOF missing";
   check(!called=1 && LargeFile.pos_out output=4L)"prepopulated receiver skip not used");
 check(read"output"="abcdefgh")"receiver-basis skip changed inherited bytes";
 (* Actual production encoders exercise token packing/EOF without transport. *)
 let source=String.init 16384(fun i->Char.chr((i*31+7)land 255))in
 write"source"source;write"basis"(String.init 16384(fun i->if i=8000 then 'z'else source.[i]));
 List.iter(fun rsync->
  let input=open_in_bin"source"and basis=open_in_bin"basis"and output=open_out_bin"output"in
  Fun.protect ~finally:(fun()->close_in input;close_in basis;close_out output)(fun()->
   let packets=ref 0 and ended=ref false in
   let info,block_size=T.Rsync.rsyncPreprocess basis(Uutil.Filesize.ofInt 16384)(Uutil.Filesize.ofInt 16384)in
   let transmit instruction=
    incr packets;check(not !ended)"encoder emitted after EOF";
    ended:=(if rsync then T.Rsync.rsyncDecompress block_size basis output ignore instruction
            else T.receive output ignore instruction);
    Lwt.return()in
   Lwt_unix.run(if rsync then T.Rsync.rsyncCompress info input(Uutil.Filesize.ofInt 16384)ignore transmit
               else T.send input(Uutil.Filesize.ofInt 16384)ignore transmit);
   check(!packets>0&& !ended)"encoder roundtrip did not finish");
  check(read"output"=source)"production encoder/decoder roundtrip changed bytes") [false;true];
 Printf.printf "PASS %d transfer checks; original tiny framing/blocks/truncation and production generic/rsync roundtrips\n%!" !checks
