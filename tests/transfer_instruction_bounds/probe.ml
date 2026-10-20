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
 (* One persistent logical allowance spans packets, independent of physical
    output offsets (append/AppleDouble), and counts optimized block skips. *)
 let budget n=T.make_output_limit(Uutil.Filesize.ofInt n)in
 with_channels(fun _ output->let limit=budget 2 in T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
    let s=string_token"abc"^"E"in
    transient(fun()->T.receive ~output_limit:limit output ignore(data s,0,String.length s)));
   check(limit.T.output_remaining=2L && not limit.T.output_ended)"overrun changed budget");
 with_channels(fun input output->let limit=budget 7 in
   transient(fun()->T.Rsync.rsyncDecompress ~output_limit:limit 4 input output
     ~copyFn:(fun _ _ ~fallback:_->failwith "DESIGNATED output overrun reached copy callback")
     ignore(data(block 0 2^"E"),0,6));
   check(limit.T.output_remaining=7L)"block overrun debited budget");
 with_channels(fun _ output->let limit=budget 4 in
   let first=string_token"ab"in
   check(not(T.receive ~output_limit:limit output ignore(data first,0,String.length first)))"first payload ended";
   check(limit.T.output_remaining=2L)"cross-packet debit missing";
   T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
    let extra=string_token"cde"in
    transient(fun()->T.receive ~output_limit:limit output ignore(data extra,0,String.length extra)));
   let last=string_token"cd"^"E"in
   check(T.receive ~output_limit:limit output ignore(data last,0,String.length last))"exact EOF refused";
   check(limit.T.output_remaining=0L && limit.T.output_ended)"EOF reservation missing";
   transient(fun()->T.receive ~output_limit:limit output ignore(data"E",0,1)));
 check(read"output"="abcd")"cross-packet limit changed bytes";
 with_channels(fun _ output->let limit=budget 3 in T.test_forbid_io:=true;
   Fun.protect ~finally:(fun()->T.test_forbid_io:=false)(fun()->
    let short=string_token"ab"^"E"in
    transient(fun()->T.receive ~output_limit:limit output ignore(data short,0,String.length short)));
   check(limit.T.output_remaining=3L)"short EOF debited payload");
 with_channels(fun _ output->let limit=budget 0 in
   T.check_output_limit limit;incr checks;
   check(T.receive ~output_limit:limit output ignore(data"E",0,1))"zero-size EOF refused";
   transient(fun()->T.check_output_limit limit));
 (* A failed write has already consumed its reservation, so reusing that owner
    cannot authorize a second copy. No rollback is inferred from a callback. *)
 with_channels(fun _ output->let limit=budget 1 in
   let s=string_token"x"^"E"in T.test_forbid_io:=true;
   (try ignore(T.receive ~output_limit:limit output ignore(data s,0,String.length s));
     failwith "write fault not injected"
    with Failure why->check(why="DESIGNATED transfer IO before validation")"wrong write fault");
   T.test_forbid_io:=false;
   check(limit.T.output_remaining=0L && limit.T.output_ended)"failed IO refunded budget";
   transient(fun()->T.receive ~output_limit:limit output ignore(data s,0,String.length s)));
 with_channels(fun input output->let limit=budget 8 in let calls=ref 0 in
   let token=block 0 1 in
   let consume ending=T.Rsync.rsyncDecompress ~output_limit:limit 4 input output
     ~copyFn:(fun _ _ ~fallback:_->incr calls;LargeFile.seek_out output(Int64.add(LargeFile.pos_out output)4L))
     ignore(data ending,0,String.length ending)in
   check(not(consume token))"first inherited range ended";
   check(limit.T.output_remaining=4L)"skip callback bypassed logical debit";
   check(consume(token^"E") && !calls=2)"exact skipped output refused";
   check(limit.T.output_remaining=0L)"skipped output not fully charged");
 List.iter(fun header->with_channels(fun _ output->output_string output header;
   let limit=budget 3 and token=string_token"abc"^"E"in
   check(T.receive ~output_limit:limit output ignore(data token,0,String.length token))"payload-relative offset refused");
   check(read"output"=header^"abc")"physical header/append prefix counted as payload") ["prefix";"AppleDouble-header"];
 List.iter(fun(kind,total,remaining)->
   let limit=CopyLimitForTest.transferOutputLimit kind(Uutil.Filesize.ofInt64 total)in
   check(limit.T.output_remaining=remaining)"Copy output allowance wrong")
   [`DATA,9L,9L;`RESS,9L,9L;`DATA_APPEND(Uutil.Filesize.ofInt 6),9L,3L;
    `DATA_APPEND(Uutil.Filesize.ofInt 0),0L,0L;
    `DATA_APPEND(Uutil.Filesize.ofInt64 Int64.max_int),Int64.max_int,0L];
 List.iter(fun(kind,total)->transient(fun()->CopyLimitForTest.transferOutputLimit kind(Uutil.Filesize.ofInt total)))
   [`DATA,-1;`RESS,-1;`DATA_APPEND(Uutil.Filesize.ofInt(-1)),9;`DATA_APPEND(Uutil.Filesize.ofInt 10),9];
 (try ignore(T.make_output_limit(Uutil.Filesize.ofInt(-1)));failwith "negative allowance accepted"
  with Invalid_argument _->incr checks);
 (* Actual production encoders exercise token packing/EOF without transport. *)
 let source=String.init 73728(fun i->Char.chr((i*31+7)land 255))in
 write"source"source;write"basis"(String.make 73728 'z');
 List.iter(fun rsync->
  let input=open_in_bin"source"and basis=open_in_bin"basis"and output=open_out_bin"output"in
  Fun.protect ~finally:(fun()->close_in input;close_in basis;close_out output)(fun()->
   let packets=ref 0 and ended=ref false and limit=budget 73728 in
   let info,block_size=T.Rsync.rsyncPreprocess basis(Uutil.Filesize.ofInt 73728)(Uutil.Filesize.ofInt 73728)in
   let transmit instruction=
    incr packets;check(not !ended)"encoder emitted after EOF";
    let _,_,encoded_bytes=instruction in
    check(encoded_bytes<=T.maxInstructionBytes)"producer exceeded declared instruction bytes";
    ended:=(if rsync then T.Rsync.rsyncDecompress ~output_limit:limit block_size basis output ignore instruction
            else T.receive ~output_limit:limit output ignore instruction);
    Lwt.return()in
   Lwt_unix.run(if rsync then T.Rsync.rsyncCompress info input(Uutil.Filesize.ofInt 73728)ignore transmit
               else T.send input(Uutil.Filesize.ofInt 73728)ignore transmit);
   check(!packets>1&& !ended)"encoder multi-frame roundtrip did not finish";
   check(limit.T.output_remaining=0L && limit.T.output_ended)"encoder output allowance not exhausted");
  check(read"output"=source)"production encoder/decoder roundtrip changed bytes") [false;true];
 (* The real generic encoder may reach EOF before its full-size argument
    after a resumed prefix; the caller's remaining-payload allowance is exact. *)
 write"source"source;write"output"(String.sub source 0 4096);
 let input=open_in_bin"source"and output=open_out_gen[Open_wronly;Open_binary]0o600"output"in
 Fun.protect ~finally:(fun()->close_in input;close_out output)(fun()->
  seek_in input 4096;seek_out output 4096;
  let limit=CopyLimitForTest.transferOutputLimit(`DATA_APPEND(Uutil.Filesize.ofInt 4096))
    (Uutil.Filesize.ofInt 73728)in
  let ended=ref false in
  Lwt_unix.run(T.send input(Uutil.Filesize.ofInt 73728)ignore(fun instruction->
    ended:=T.receive ~output_limit:limit output ignore instruction;Lwt.return()));
  check(!ended && limit.T.output_remaining=0L)"resumed encoder did not exhaust payload");
 check(read"output"=source)"resumed production encoding changed file";
 write"resource-source"("input-resource-header"^source);
 let input=open_in_bin"resource-source"and output=open_out_bin"output"in
 Fun.protect ~finally:(fun()->close_in input;close_out output)(fun()->
  seek_in input(String.length"input-resource-header");output_string output"output-resource-header";
  let limit=CopyLimitForTest.transferOutputLimit `RESS(Uutil.Filesize.ofInt 73728)in
  let ended=ref false in
  Lwt_unix.run(T.send input(Uutil.Filesize.ofInt 73728)ignore(fun instruction->
    ended:=T.receive ~output_limit:limit output ignore instruction;Lwt.return()));
  check(!ended && limit.T.output_remaining=0L)"resource payload did not finish");
 check(read"output"="output-resource-header"^source)"resource payload counted physical headers";
 Printf.printf "PASS %d transfer checks; original tiny framing/blocks/truncation and production generic/rsync roundtrips\n%!" !checks
