module Q=SemanticMailbox
type job={id:int;packet:string;file:Unix.file_descr;cancel:bool Atomic.t}
type result={id:int;checksum:int;cancelled:bool}
let check x why=if not x then failwith why
let rec send q value=match Q.push q value with
  | Added -> () | Full -> Domain.cpu_relax ();send q value | Closed -> failwith "closed send"
let checksum s=let total=ref 0 in String.iter (fun c -> total:= !total+Char.code c) s; !total
let () =
  List.iter (fun n -> check (try ignore(Q.create ~capacity:n);false with Invalid_argument _ -> true) "capacity") [0;-1;65537;max_int];
  let q=Q.create ~capacity:3 in
  check (Q.pop q=Empty) "initial empty";
  List.iter (fun n -> check (Q.push q n=Added) "push") [1;2;3];
  check (Q.push q 4=Full) "capacity overflow";
  check ((Q.usage q).pending=3) "full changed count";
  check (Q.pop q=Item 1) "FIFO first";
  check (Q.push q 4=Added) "reuse slot";
  Q.close q;Q.close q;
  check (Q.push q 5=Closed) "closed push";
  List.iter (fun n -> check(Q.pop q=Item n) "FIFO after close") [2;3;4];
  check (Q.pop q=Drained && (Q.usage q).pending=0 && (Q.usage q).closed) "close drain";
  print_endline "PASS capacity FIFO close and drain";
  let racing : int Q.t=Q.create ~capacity:17 in
  let producer=Domain.Safe.spawn (fun () ->
    let rec loop i=match Q.push racing i with
      | Added -> loop(i+1)
      | Full -> Domain.cpu_relax ();loop i
      | Closed -> i in loop 0) in
  while (Q.usage racing).pending<8 do Domain.cpu_relax () done;
  Q.close racing;
  let accepted=Domain.join producer in
  check(accepted>=8 && accepted<=17) "close racing count";
  for id=0 to accepted-1 do check(Q.pop racing=Item id) "close race lost FIFO item" done;
  check(Q.pop racing=Drained && Q.push racing 42=Closed) "close race not closed";
  print_endline "PASS close races producer and preserves accepted FIFO prefix";
  List.iter (fun (seed:int) ->
    let input : job Q.t=Q.create ~capacity:31 and output : result Q.t=Q.create ~capacity:2000 in
    let consumers=List.init 3 (fun _ -> Domain.Safe.spawn (fun () ->
      let rec loop ()=match Q.pop input with
        | Empty -> Domain.cpu_relax ();loop ()
        | Drained -> ()
        | Item (job:job) ->
            check (job.file=Unix.stdin) "descriptor carrier differs";
            let cancelled=Atomic.get job.cancel in
            send output {id=job.id;checksum=(if cancelled then 0 else checksum job.packet);cancelled};loop () in loop ())) in
    let producers=List.init 2 (fun (producer:int) -> Domain.Safe.spawn (fun () ->
      for i=0 to 999 do
        let id=producer*1000+i in
        let cancel=Atomic.make(id mod 7=0) in
        send input {id;packet=string_of_int(seed+id);file=Unix.stdin;cancel}
      done)) in
    List.iter Domain.join producers;Q.close input;List.iter Domain.join consumers;Q.close output;
    check ((Q.usage input).pending=0 && (Q.usage output).pending=2000) "concurrent settlement";
    let seen=Array.make 2000 false in
    for _=1 to 2000 do
      match Q.pop output with
      | Item result ->
          check(result.id>=0 && result.id<2000 && not seen.(result.id)) "duplicate/missing result";
          seen.(result.id)<-true;
          check(result.cancelled=(result.id mod 7=0)) "cancellation payload";
          check(result.checksum=(if result.cancelled then 0 else checksum(string_of_int(seed+result.id)))) "immutable packet result"
      | _ -> failwith "missing result"
    done;
    check(Array.for_all Fun.id seen && Q.pop output=Drained && (Q.usage output).pending=0) "undrained output";
    Printf.printf "PASS concurrent immutable jobs seed=%d jobs=2000 producers=2 consumers=3\n%!" seed
  ) [1;17;103;4099;65537;20261014]
