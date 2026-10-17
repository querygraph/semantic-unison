#!/usr/bin/env python3
"""Fault-test actual Files setup/copy/final publication with disposable roots.

The runner requires a fresh compiler-matched Make snapshot. It recompiles the
full Files implementation and its CLI dependents privately. Hooks delegate to
actual validation, destination checking, backups, native publication and archive
functions; no public switch is added. Real local and loopback remote transfers
exercise the additive protocol. The native fixture includes byte-identical
production C under private syscall fault wrappers. No Adobe SDK, photo/cache or
preview input, throughput measurement or crash-durability claim is involved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unicodedata


PREFIX = r'''
module FinalCallerFault = struct
  type location = {
    root : Fspath.t; local : Path.local; working : Fspath.t;
    candidate : Path.local; target : Path.local;
  }
  let current : location option ref = ref None
  let resume_holds : Unix.file_descr list ref = ref []
  let fired = ref false
  let env name = match Sys.getenv_opt name with Some value -> value | None -> ""
  let log fields =
    let file = env "UNISON_FINAL_TEST_LOG" in
    if file <> "" then begin
      let fd = Unix.openfile file [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_APPEND;Unix.O_CLOEXEC] 0o600 in
      let channel = Unix.out_channel_of_descr fd in
      Fun.protect ~finally:(fun () -> close_out channel)
        (fun () -> output_string channel (String.concat "\t" fields ^ "\n"))
    end
  let selected location = Fspath.toString location.root = env "UNISON_FINAL_TEST_ROOT"
  let active () = match !current with Some location when selected location -> Some location | _ -> None
  let absolute directory path = Fspath.toString (Fspath.concat directory path)
  let candidate location = absolute location.working location.candidate
  let target location = absolute location.working location.target
  let rec archive = function
    | Update.NoArchive -> "NONE"
    | Update.ArchiveFile (_, fp, _, _) -> Os.fullfingerprint_to_string fp
    | Update.ArchiveSymlink link -> "LINK:" ^ link
    | Update.ArchiveDir (_, children) ->
        "DIR{" ^ String.concat ";" (Update.NameMap.fold (fun name value rest ->
          (Name.toString name ^ "=" ^ archive value) :: rest) children []) ^ "}"
  let snapshot label root path =
    try log [label;Fspath.toString root;Path.toString path;archive (Update.updateArchive root path Common.NoUpdates)]
    with error -> log [label;Fspath.toString root;Path.toString path;"ERROR:" ^ Printexc.to_string error]
  let write path bytes =
    let fd = Unix.openfile path [Unix.O_WRONLY;Unix.O_CREAT;Unix.O_EXCL;Unix.O_CLOEXEC] 0o600 in
    Fun.protect ~finally:(fun () -> Unix.close fd) (fun () ->
      let rec loop offset = if offset < String.length bytes then begin
        let count = Unix.write_substring fd bytes offset (String.length bytes-offset) in
        if count=0 then failwith "fixture write stopped"; loop (offset+count)
      end in loop 0)
  let read path = let channel=open_in_bin path in
    Fun.protect ~finally:(fun () -> close_in channel)
      (fun () -> really_input_string channel (in_channel_length channel))
  let replace path bytes =
    let before=Unix.stat path in
    let saved = path ^ ".fixture-original" in
    Unix.rename path saved; write path bytes;
    Unix.chmod path before.Unix.st_perm;
    Unix.utimes path before.Unix.st_atime before.Unix.st_mtime
  let rec remove path = match (Unix.lstat path).Unix.st_kind with
    | Unix.S_DIR -> Array.iter (fun name -> remove (Filename.concat path name)) (Sys.readdir path); Unix.rmdir path
    | _ -> Unix.unlink path
    | exception Unix.Unix_error (Unix.ENOENT,_,_) -> ()
  external rename_fault : int -> unit = "final_publication_fixture_rename_fault"
  let hit phase = match active () with
    | None -> ()
    | Some location ->
      log ["phase";phase;candidate location;target location];
      let mode=env "UNISON_FINAL_TEST_MODE" in
      let trigger = match mode with
        | "candidate-before-attach" | "candidate-replaced-before-attach" -> "rename-entry"
        | "candidate-after-validation" | "candidate-replaced-after-validation" |
          "target-after-validation" | "target-samebytes-after-validation" | "root-after-validation" |
          "reject-validation" | "sidecar-after-validation" -> "validation-after"
        | "target-after-update" | "target-disappears-after-update" |
          "target-appears-after-update" | "follow-after-update" -> "update-after"
        | "target-after-backup" | "candidate-after-backup" -> "backup-after"
        | "post-native-exception" | "post-native-OOM" | "post-native-target-replaced" -> "publish-after"
        | "native-rename-EIO" | "native-result-stat-EIO" -> "publish-before"
        | "candidate-sidecar" | "target-sidecar" | "sidecar-second-rename-error" -> "rename-entry"
        | "archive-before-exception" -> "archive-before"
        | _ -> "" in
      if not !fired && phase=trigger then begin
        fired := true;
        log ["injected";mode;phase];
        snapshot "archive-at-injection" location.root location.local;
        let cp=candidate location and tp=target location in
        (match mode with
        | "candidate-before-attach" | "candidate-after-validation" | "candidate-after-backup" ->
            let channel=open_out_bin cp in output_string channel "BAD COMPLETED CANDIDATE"; close_out channel
        | "candidate-replaced-before-attach" | "candidate-replaced-after-validation" -> replace cp (read cp)
        | "target-after-validation" | "target-after-update" | "target-after-backup" |
          "post-native-target-replaced" -> replace tp "FOREIGN LIVE SENTINEL"
        | "target-samebytes-after-validation" -> replace tp (read tp)
        | "target-disappears-after-update" -> Unix.rename tp (tp ^ ".fixture-original")
        | "target-appears-after-update" -> write tp "FOREIGN LIVE SENTINEL"
        | "follow-after-update" ->
            let logical=absolute location.root location.local in
            Unix.unlink logical; Unix.symlink (env "UNISON_FINAL_TEST_FOLLOW") logical
        | "root-after-validation" ->
            let root=Fspath.toString location.root in
            Unix.rename root (root ^ ".fixture-original"); Unix.mkdir root 0o700;
            write (Filename.concat root (Path.toString location.local)) "FOREIGN ROOT SENTINEL"
        | "sidecar-after-validation" | "candidate-sidecar" ->
            write (Filename.concat (Filename.dirname cp) ("._" ^ Filename.basename cp)) "SYNTHETIC FINDER SIDECAR"
        | "target-sidecar" ->
            write (Filename.concat (Filename.dirname tp) ("._" ^ Filename.basename tp)) "OLD FINDER SIDECAR"
        | "sidecar-second-rename-error" ->
            write (Filename.concat (Filename.dirname cp) ("._" ^ Filename.basename cp)) "SYNTHETIC FINDER SIDECAR";
            let auxiliary=Filename.concat (Filename.dirname tp) ("._" ^ Filename.basename tp) in
            Unix.mkdir auxiliary 0o700; write (Filename.concat auxiliary "sentinel") "FOREIGN AUXILIARY SENTINEL"
        | "native-rename-EIO" -> rename_fault 1
        | "native-result-stat-EIO" -> rename_fault 4
        | "reject-validation" -> raise (Util.Transient "controlled settled validation rejection")
        | "post-native-exception" | "archive-before-exception" -> raise (Util.Transient "controlled publication observer failure")
        | "post-native-OOM" -> raise Out_of_memory
        | _ -> ())
      end
  let enter root local working candidate target =
    let location={root;local;working;candidate;target} in current:=Some location;
    if selected location then begin
      log ["rename";Fspath.toString root;Path.toString local;Fspath.toString working;
        Path.toString candidate;Path.toString target];
      snapshot "archive-before" root local;
      hit "rename-entry"
    end
  let setup root (working,target,candidate,local) =
    let location={root;local;working;candidate;target} in
    if selected location then begin
      let mode=env "UNISON_FINAL_TEST_MODE" in
      let cp=absolute working candidate and tp=absolute working target in
      let auxiliary path=Filename.concat (Filename.dirname path) ("._" ^ Filename.basename path) in
      let inject ()=current:=Some location; fired:=true;
        log ["injected";mode;"setup-before-producer"] in
      (match mode with
       | "candidate-sidecar" -> inject (); write (auxiliary cp) "SYNTHETIC FINDER SIDECAR"
       | "target-sidecar" -> inject (); write (auxiliary tp) "OLD FINDER SIDECAR"
       | "sidecar-second-rename-error" ->
           inject (); write (auxiliary cp) "SYNTHETIC FINDER SIDECAR";
           Unix.mkdir (auxiliary tp) 0o700;
           write (Filename.concat (auxiliary tp) "sentinel") "FOREIGN AUXILIARY SENTINEL"
       | "resume-complete" | "resume-prefix" | "resume-invalid" | "resume-empty" ->
           inject ();
           let bytes=read (env "UNISON_FINAL_TEST_INCOMING") in
           let bytes=match mode with
             | "resume-prefix" -> String.sub bytes 0 (String.length bytes / 2)
             | "resume-invalid" -> String.make (String.length bytes / 2) 'Z'
             | "resume-empty" -> "" | _ -> bytes in
           write cp bytes;
           resume_holds:=Unix.openfile cp [Unix.O_RDONLY;Unix.O_CLOEXEC] 0 :: !resume_holds;
           log ["resume-created";cp;string_of_int (Unix.stat cp).Unix.st_ino;string_of_int (String.length bytes)]
       | _ -> ())
    end
  let finish root path = snapshot "archive-after" root path
  let () = at_exit (fun () ->
    let logical=env "UNISON_FINAL_TEST_PATH" in
    if logical<>"" then List.iter (fun name ->
      let root=env name in if root<>"" then
      try snapshot "archive-exit" (Fspath.canonize (Some root)) (Path.fromString logical)
      with _ -> ()) ["UNISON_FINAL_TEST_LEFT";"UNISON_FINAL_TEST_ROOT"])
end
module CandidateValidation = struct
  include CandidateValidation
  let before_commit_with_reservation ~reservation ~directory ~candidate ~destination =
    FinalCallerFault.hit "validation-before";
    Lwt.bind (CandidateValidation.before_commit_with_reservation ~reservation ~directory ~candidate ~destination)
      (fun result -> FinalCallerFault.hit "validation-after"; Lwt.return result)
end
module Update = struct
  include Update
  let checkNoUpdates ?fastCheck root path ui =
    FinalCallerFault.hit "update-before";
    let result=Update.checkNoUpdates ?fastCheck root path ui in
    FinalCallerFault.hit "update-after"; result
  let replaceArchiveLocal root path archive =
    (match FinalCallerFault.active () with
     | Some location when Fspath.compare location.root root=0 -> FinalCallerFault.hit "archive-before"
     | _ -> ());
    Update.replaceArchiveLocal root path archive;
    FinalCallerFault.snapshot "archive-replaced" root path
end
module Stasher = struct
  include Stasher
  let backup root path disposition archive =
    FinalCallerFault.hit "backup-before";
    Stasher.backup root path disposition archive;
    FinalCallerFault.hit "backup-after"
  let stashCurrentVersion root path source =
    FinalCallerFault.hit "stash-before";
    Stasher.stashCurrentVersion root path source;
    FinalCallerFault.hit "stash-after"
end
module FinalPublication = struct
  include FinalPublication
  let publish context =
    FinalCallerFault.hit "publish-before";
    FinalPublication.publish context;
    FinalCallerFault.log ["native-published";string_of_bool (FinalPublication.published context)];
    FinalCallerFault.hit "publish-after"
  let check_published context =
    FinalCallerFault.hit "published-check-before";
    FinalPublication.check_published context;
    FinalCallerFault.hit "published-check-after"
end
module TargetBinding = struct
  include TargetBinding
  let supported () =
    let result=TargetBinding.supported () in
    FinalCallerFault.log ["supported";string_of_bool result]; result
  let recheck_resolution binding =
    if FinalCallerFault.env "UNISON_FINAL_TEST_NEGATIVE" <> "resolution"
    then TargetBinding.recheck_resolution binding
  let legacy_handoff binding =
    FinalCallerFault.log ["legacy-handoff"];
    TargetBinding.legacy_handoff binding
  let with_binding ?connection ~token ~logical_root ~local_path ~working_dir ~candidate ~target f =
    let finish error =
      FinalCallerFault.finish logical_root local_path;
      match error with None -> () | Some error ->
        if FinalCallerFault.env "UNISON_FINAL_TEST_NEGATIVE"="live-cleanup" then
          (try Unix.unlink (FinalCallerFault.absolute working_dir target) with _ -> ());
        FinalCallerFault.log ["bound-error";Printexc.to_string error] in
    Lwt.try_bind
      (fun () -> TargetBinding.with_binding ?connection ~token ~logical_root ~local_path
        ~working_dir ~candidate ~target f)
      (fun result -> finish None; Lwt.return result)
      (fun error -> finish (Some error); Lwt.fail error)
end
'''


COPY_WRAP = r'''
let copy =
  let actual=copy in
  fun update rootFrom pathFrom uiFrom propsFrom rootTo pathTo uiTo propsTo notDefault id ->
    let finish () =
      FinalCallerFault.snapshot "source-archive-after" (snd rootFrom) (Path.forceLocal pathFrom);
      FinalCallerFault.snapshot "destination-archive-after" (snd rootTo) (Path.forceLocal pathTo) in
    Lwt.try_bind
      (fun () -> actual update rootFrom pathFrom uiFrom propsFrom rootTo pathTo uiTo propsTo notDefault id)
      (fun result -> finish (); Lwt.return result)
      (fun error -> finish (); Lwt.fail error)
'''

ARCHIVE_QUERY = r'''
let final_test_read_archive = Remote.registerRootCmd "privateFinalCallerArchive"
  Path.m Umarshal.string
  (fun (root,path) ->
    Lwt.return (FinalCallerFault.archive (Update.updateArchive root (Path.forceLocal path) Common.NoUpdates)))
let final_test_dump () =
  let path=FinalCallerFault.env "UNISON_FINAL_TEST_PATH" in
  if path<>"" && TargetBinding.supported () then
    try Lwt_unix.run (Globals.allRootsIter (fun root ->
      Lwt.bind (final_test_read_archive root (Path.fromString path)) (fun archive ->
        FinalCallerFault.log ["archive-committed";Fspath.toString (snd root);path;archive]; Lwt.return ())))
    with error -> FinalCallerFault.log ["archive-query-error";Printexc.to_string error]
'''


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise AssertionError('caller seam is no longer unique: ' + old[:100])
    return source.replace(old, new, 1)


def instrument(source):
    declaration = ('let renameLocalWithBinding ?binding\n'
                   '      (fspathTo,\n'
                   '       ((localPathTo, workingDir, pathFrom, pathTo), (ui, archOpt, notDefault))) =')
    source = replace_once(source, declaration, declaration +
        '\n  FinalCallerFault.enter fspathTo localPathTo workingDir pathFrom pathTo;')
    source = replace_once(source, '\nlet moveArchiveLocal ', COPY_WRAP + '\nlet moveArchiveLocal ')
    source = replace_once(source, 'let returnBoundSetup connection root paths token =\n',
                          'let returnBoundSetup connection root paths token =\n  FinalCallerFault.setup root paths;\n')
    return PREFIX + source + ARCHIVE_QUERY


PRODUCER_PREFIX = r'''
module ProducerCallerFault = struct
  let env name=match Sys.getenv_opt name with Some value->value|None->""
  let log fields=
    let file=env "UNISON_FINAL_TEST_LOG" in if file<>"" then begin
      let channel=open_out_gen [Open_wronly;Open_creat;Open_append;Open_binary] 0o600 file in
      Fun.protect ~finally:(fun()->close_out channel)
        (fun()->output_string channel (String.concat "\t" fields ^ "\n"))
    end
  let fd label descriptor=let info=Unix.LargeFile.fstat descriptor in
    log [label;string_of_int info.Unix.LargeFile.st_ino;Int64.to_string info.st_size]
end
module Fs = struct
  include Fs
  let clone_stage_handles source stage=
    if ProducerCallerFault.env "UNISON_FINAL_TEST_SEMANTIC"="local" &&
       Fspath.toString source=ProducerCallerFault.env "UNISON_FINAL_TEST_INCOMING" then begin
      ProducerCallerFault.log ["source-clone-declined"];
      Declined_stage_handles Cross_device
    end else Fs.clone_stage_handles source stage
  let clone_stage_handles_sized ~expected_length source stage=
    if ProducerCallerFault.env "UNISON_FINAL_TEST_SEMANTIC"="local" &&
       Fspath.toString source=ProducerCallerFault.env "UNISON_FINAL_TEST_INCOMING" then begin
      ProducerCallerFault.log ["source-clone-declined"];
      Declined_stage_handles Cross_device
    end else Fs.clone_stage_handles_sized ~expected_length source stage
end
module FinalPublication = struct
  include FinalPublication
  let adopt_resume context=
    FinalPublication.adopt_resume context;
    ProducerCallerFault.log ["resume-admitted"]
end
module TargetBinding = struct
  include TargetBinding
  let legacy_handoff binding=
    ProducerCallerFault.log ["legacy-handoff"];
    TargetBinding.legacy_handoff binding
end
module SemanticSync = struct
  include SemanticSync
  let try_local_async_with_producer ~producer ~source ~basis ~directory ~staging=
    SemanticSync.try_local_async_with_producer
      ~producer:(fun descriptor->ProducerCallerFault.fd "local-semantic-output" descriptor;producer descriptor)
      ~source ~basis ~directory ~staging
  let try_local_async_reserved ~reservation ~producer ~source ~basis ~directory ~staging=
    let producer=Option.map (fun producer descriptor->
      ProducerCallerFault.fd "local-semantic-output" descriptor;producer descriptor) producer in
    SemanticSync.try_local_async_reserved ~reservation ~producer ~source ~basis ~directory ~staging
end
module SemanticRemote = struct
  include SemanticRemote
  let try_transfer_with_producer ~producer ~connection ~source ~basis ~directory ~staging ~expected_size=
    SemanticRemote.try_transfer_with_producer
      ~producer:(fun descriptor->ProducerCallerFault.fd "remote-semantic-output" descriptor;producer descriptor)
      ~connection ~source ~basis ~directory ~staging ~expected_size
  let try_transfer_reserved ~reservation ~producer ~connection ~source ~basis ~directory ~staging ~expected_size=
    let producer=Option.map (fun producer descriptor->
      ProducerCallerFault.fd "remote-semantic-output" descriptor;producer descriptor) producer in
    SemanticRemote.try_transfer_reserved ~reservation ~producer ~connection ~source ~basis ~directory ~staging ~expected_size
end
'''


def instrument_copy(source):
    declaration='let openProducerOutput ?clone_owned producer fspath path kind len =\n'
    source=replace_once(source,declaration,declaration+
        '  ProducerCallerFault.log ["producer-writer";Fspath.toString fspath;Path.toString path;'+
        '(match kind with `DATA->"create"|`RESS->"resource"|`DATA_APPEND n->"append:" ^ Int64.to_string (Uutil.Filesize.toInt64 n))];\n')
    declaration='let withProducer connection root localPath workingDir candidate target token f =\n'
    source=replace_once(source,declaration,declaration+
        '  ProducerCallerFault.log ["producer-owner";Fspath.toString root;'+
        '(match connection with None->"local"|Some _->"connection")];\n')
    source=replace_once(source,'          (fun value -> if clone_scope.uncertain then pending else Lwt.return value)',
        '          (fun value -> if clone_scope.uncertain then pending else begin\n'+
        '            ProducerCallerFault.log ["producer-finished";Fspath.toString root;'+
        'string_of_bool producer.frozen;string_of_bool producer.legacy]; Lwt.return value end)')
    return PRODUCER_PREFIX+source


def objects(makefile, name):
    match = re.search(r'^' + name + r' = (.*?)(?=\n\n)', makefile, re.M | re.S)
    if match is None:
        raise RuntimeError('missing object list ' + name)
    body = match.group(1).replace('\\\n', ' ').replace('$(SYSTEM)', 'generic')
    return body.replace('$(WINOBJS)', '').replace('$(WINCOBJS)', '').replace('$(OBJ_EXT)', '.o').replace('.cmo', '.cmx').split()


def compile_private(root, build, compiler, work, environment):
    names = subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'], cwd=root)
    count = 0
    manifest={}
    for raw in names.split(b'\0'):
        if not raw:
            continue
        name = os.fsdecode(raw)
        source = root/name
        if name.startswith('src/') and name != 'src/.depend' and source.is_file():
            if not (build/name).is_file() or (build/name).read_bytes() != source.read_bytes():
                raise AssertionError(name + ' differs from current source; refresh frozen snapshot')
            count += 1
            manifest[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    (work/'production-source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('matching production source inputs', count, flush=True)
    src = build/'src'
    modules = objects((src/'Makefile.OCaml').read_text(), 'OCAMLOBJS')
    index = modules.index('copy.cmx')
    before, after = modules[:index], modules[index+1:]
    includes = [work,src,src/'lwt',src/'ubase',src/'system',src/'system/generic',src/'lwt/generic']
    flags = [flag for path in includes for flag in ['-I',str(path)]] + ['-I','+unix','-I','+str']
    private = instrument((src/'files.ml').read_text())
    (work/'files.ml').write_text(private)
    (work/'copy.ml').write_text(instrument_copy((src/'copy.ml').read_text()))
    shutil.copy2(src/'copy.mli',work/'copy.mli')
    shutil.copy2(src/'files.mli',work/'files.mli')
    with (work/'files.mli').open('a') as interface:
        interface.write('\nval final_test_dump : unit -> unit\n')
    fixture = root/'tests/final_publication/fixture.c'
    shutil.copy2(fixture,work/'finalFixture.c')
    shutil.copy2(src/'finalPublication_stubs.c',work/'finalPublication_stubs.c')
    for name in after + ['linktext.cmx']:
        if name=='files.cmx':
            continue
        for suffix in ['.ml','.mli']:
            source=src/Path(name).with_suffix(suffix)
            if source.is_file():
                shutil.copy2(source,work/source.name)
    text=(work/'uitext.ml').read_text()
    assert text.count('Update.commitUpdates ();')==4, 'text CLI archive checkpoint sites changed'
    (work/'uitext.ml').write_text(text.replace('Update.commitUpdates ();',
                                             'Update.commitUpdates (); Files.final_test_dump ();'))
    version=subprocess.check_output([compiler,'-version'],env=environment,text=True).strip()
    print('Compiler',version,flush=True)
    print('compiled files.ml',hashlib.sha256(private.encode()).hexdigest(),flush=True)
    print('native source',hashlib.sha256((src/'finalPublication_stubs.c').read_bytes()).hexdigest(),flush=True)
    with (work/'build.log').open('w+') as log:
        commands=[]
        def execute(arguments):
            commands.append(arguments)
            (work/'build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
            subprocess.run(arguments,cwd=work,env=environment,stdout=log,stderr=log,check=True)
        try:
            execute([compiler,*flags,'-c','finalFixture.c'])
            for name in ['copy.cmx',*after,'linktext.cmx']:
                stem=Path(name).stem
                if (work/(stem+'.mli')).is_file():
                    execute([compiler,*flags,'-c',stem+'.mli'])
                execute([compiler,*flags,'-c',stem+'.ml'])
            cobjects=[name for name in objects((src/'Makefile.OCaml').read_text(),'COBJS') if name!='finalPublication_stubs.o']
            execute([compiler,*flags,'unix.cmxa','str.cmxa',
                            *[str(src/name) for name in before], 'copy.cmx', *[Path(name).name for name in after],
                            'linktext.cmx',*[str(src/name) for name in cobjects],'finalFixture.o','-o','unison-final-test'])
        except subprocess.CalledProcessError:
            log.seek(0); print(log.read()); raise
    binary=work/'unison-final-test'
    (work/'build-receipt.json').write_text(json.dumps({
        'snapshot':str(build),'compiler':compiler,'compiler_version':version,
        'production_source_inputs':count,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'private_source_sha256':hashlib.sha256(private.encode()).hexdigest(),
        'private_copy_sha256':hashlib.sha256((work/'copy.ml').read_bytes()).hexdigest(),
        'native_fixture_sha256':hashlib.sha256((work/'finalFixture.c').read_bytes()).hexdigest(),
        'native_source_sha256':hashlib.sha256((work/'finalPublication_stubs.c').read_bytes()).hexdigest(),
        'build_log_sha256':hashlib.sha256((work/'build.log').read_bytes()).hexdigest(),
    },indent=2)+'\n')
    return binary


OLD = bytes((i*37 ^ i//19) & 255 for i in range(8197))
NEW = b'NEW-TRANSFERRED-PREFIX' + OLD[137:] + b'new-tail'
SENTINEL = b'FOREIGN LIVE SENTINEL'


def semantic_fixture(value):
    data=bytearray(8192)
    struct.pack_into('<2sHIH',data,0,b'II',42,8,4)
    xmp=b'<x>'+value+b'</x>      '
    for index,entry in enumerate(((273,4,1,4096),(279,4,1,1024),
                                  (700,1,len(xmp),1024),(50706,1,4,1025))):
        struct.pack_into('<HHII',data,10+12*index,*entry)
    data[1024:1024+len(xmp)]=xmp
    data[4096:5120]=b'R'*1024
    data[-1]=65
    return bytes(data)


def set_resource(path, data):
    subprocess.run(['/usr/bin/xattr','-wx','com.apple.ResourceFork',data.hex(),str(path)],check=True)


def get_resource(path):
    text=subprocess.check_output(['/usr/bin/xattr','-px','com.apple.ResourceFork',str(path)],text=True)
    return bytes.fromhex(''.join(text.split()))


def event_rows(log):
    return [line.split('\t') for line in log.read_text().splitlines()] if log.exists() else []


def archive_assert(rows, root, data, label='archive-committed'):
    valid=[row[3] for row in rows if len(row)>3 and row[0]==label and row[1]==str(root)
           and not row[3].startswith('ERROR:')]
    if not valid and label=='archive-committed':
        valid=[row[3] for row in rows if len(row)>3 and row[0] in ('archive-after','source-archive-after','archive-exit')
               and row[1]==str(root) and not row[3].startswith('ERROR:')]
    assert valid, f'no actual {label} snapshot for {root}'
    digest=hashlib.md5(data).hexdigest()
    assert digest in valid[-1], (label,root,digest,valid[-1])


class Suite:
    def __init__(self,binary,peer,work,environment,negative,only):
        self.binary=binary; self.peer=peer; self.work=work; self.environment=environment
        self.negative=negative; self.count=0
        self.only=only
        self.passed=[]

    def report(self,name):
        self.passed.append(name)
        print('PASS',name,flush=True)

    def case(self,name,mode='observe',remote=False,follow=False,validate=False,extra=(),new_target=False,
             filename='item.bin',expect_success=None,recover=True,backup=False,native_fork=False):
        if self.only and mode != self.only:
            return
        self.count+=1
        root=self.work/f'case-{self.count}'
        left,right,state,receiver=(root/name for name in ('left','right','state','receiver-state'))
        for path in (left,right,state,receiver):
            path.mkdir(parents=True)
        log=root/'events.tsv'
        a,b=root/'follow-a',root/'follow-b'
        if follow:
            a.mkdir(); b.mkdir(); (a/'live').write_bytes(OLD); (b/'live').write_bytes(OLD)
            os.utime(b/'live',ns=((a/'live').stat().st_atime_ns,(a/'live').stat().st_mtime_ns))
            (right/filename).symlink_to(a/'live')
        target=a/'live' if follow else right/filename
        (left/filename).write_bytes(OLD)
        if not follow:
            target.write_bytes(OLD)
        base_env=dict(self.environment,UNISON=str(state),UNISON_FINAL_TEST_LOG=str(log),
                      UNISON_FINAL_TEST_ROOT=str(right),UNISON_FINAL_TEST_LEFT=str(left),
                      UNISON_FINAL_TEST_PATH=filename,UNISON_FINAL_TEST_FOLLOW=str(b/'live'))
        loopback=root/'loopback.py'
        loopback.write_text('#!/usr/bin/python3\nimport os,sys\n'
            'os.environ["UNISON"]='+repr(str(receiver))+'\n'
            'a=sys.argv[1:]; i=a.index('+repr(str(self.binary))+'); os.execv(a[i],a[i:])\n')
        loopback.chmod(0o700)
        command=[str(self.binary),str(left),('ssh://localhost/'+str(right)) if remote else str(right),
                 '-batch','-auto','-fastcheck','false','-times','-clone','off','-semanticworkers','2','-path',filename]
        if remote:
            command += ['-sshcmd',str(loopback),'-servercmd',str(self.binary)]
        if follow:
            command += ['-follow','Name '+filename]
        command += list(extra)
        if backup:
            command += ['-backup','Name '+filename,'-backuplocation','local',
                        '-backupprefix','.backup-$VERSION-','-backupsuffix','']

        def sync(injection='observe',success=True,negative=''):
            log.write_text('')
            env=dict(base_env,UNISON_FINAL_TEST_MODE=injection,UNISON_FINAL_TEST_NEGATIVE=negative or '')
            result=subprocess.run(command,env=env,text=True,capture_output=True,timeout=90)
            (root/(injection+'-run.log')).write_text(result.stdout+result.stderr)
            if (result.returncode==0) != success:
                raise AssertionError(name+'\n'+result.stdout+result.stderr)
            return event_rows(log)

        sync()
        assert target.read_bytes()==OLD, name
        if new_target:
            # A new independent profile/archives makes this an absent target
            # from scan through observe_target; no deletion reconciliation.
            shutil.rmtree(state); state.mkdir(); shutil.rmtree(receiver); receiver.mkdir()
            target.unlink()
        (left/filename).write_bytes(NEW)
        if native_fork:
            os.chmod(left/filename,0o640)
            set_resource(left/filename,b'SYNTHETIC NATIVE RESOURCE FORK')
        if validate:
            command += ['-adobevalidate','warn']  # ordinary non-DNG: real gate, no external helper
        if expect_success is None:
            expect_success=mode in ('observe','candidate-sidecar','target-sidecar')
        rows=sync(mode,expect_success,self.negative)
        if mode!='observe':
            assert any(row[:2]==['injected',mode] for row in rows), (name,'fault seam did not execute',rows)
        assert (left/filename).read_bytes()==NEW, name+' changed source data'
        if backup:
            backups=[path for path in right.iterdir() if path.name.startswith('.backup-') and path.is_file()]
            assert backups and any(path.read_bytes()==OLD for path in backups), name+' did not preserve real old-file backup'
        publications=[row for row in rows if row[:2]==['native-published','true']]
        renames=[row for row in rows if row[0]=='rename']
        if renames:
            stage=Path(renames[-1][3])/renames[-1][4]
            if mode=='root-after-validation':
                stage=Path(str(right)+'.fixture-original')/stage.relative_to(right)
            if mode in ('candidate-replaced-before-attach','candidate-replaced-after-validation'):
                assert stage.read_bytes()==NEW, name+' deleted a foreign replacement candidate'
                assert stage.with_name(stage.name+'.fixture-original').read_bytes()==NEW
            else:
                assert not stage.exists(), name+' retained an owned main candidate after settlement'
        if mode in ('observe',):
            assert target.read_bytes()==NEW and publications, (name,'native caller not exercised')
            archive_assert(rows,left,NEW); archive_assert(rows,right,NEW)
            if native_fork:
                assert get_resource(target)==b'SYNTHETIC NATIVE RESOURCE FORK'
                assert get_resource(left/filename)==b'SYNTHETIC NATIVE RESOURCE FORK'
                assert target.stat().st_mode & 0o777==0o640, 'source-selected native-fork candidate mode changed'
            if filename!='item.bin':
                rename_rows=[row for row in rows if row[0]=='rename']
                assert rename_rows and rename_rows[-1][-1]==filename, 'Update normalized an existing basename'
        elif mode in ('candidate-sidecar','target-sidecar'):
            assert target.read_bytes()==NEW and not publications, name
            assert any(row[0]=='legacy-handoff' for row in rows), 'sidecar did not choose explicit legacy handoff'
            auxiliary=target.with_name('._'+target.name)
            if mode=='candidate-sidecar':
                assert auxiliary.read_bytes()==b'SYNTHETIC FINDER SIDECAR'
            else:
                assert not auxiliary.exists(), 'legacy stale sidecar behavior changed'
            archive_assert(rows,left,NEW); archive_assert(rows,right,NEW)
        else:
            if mode in ('post-native-exception','post-native-OOM','native-result-stat-EIO','archive-before-exception',
                        'sidecar-second-rename-error'):
                assert target.exists() and target.read_bytes()==NEW, name+' deleted or rolled back successfully published live output'
            elif mode=='post-native-target-replaced':
                assert target.read_bytes()==SENTINEL, name+' deleted foreign post-publication replacement'
            elif mode in ('target-after-validation','target-after-update','target-after-backup','target-appears-after-update'):
                assert target.read_bytes()==SENTINEL, name+' overwrote/removed rebound live sentinel'
            elif mode=='target-samebytes-after-validation':
                assert target.read_bytes()==OLD and target.with_name(target.name+'.fixture-original').read_bytes()==OLD
                assert target.stat().st_ino!=target.with_name(target.name+'.fixture-original').stat().st_ino
            elif mode=='target-disappears-after-update':
                assert not target.exists() and target.with_name(target.name+'.fixture-original').read_bytes()==OLD
            elif mode=='root-after-validation':
                assert (right/filename).read_bytes()==b'FOREIGN ROOT SENTINEL'
                assert (Path(str(right)+'.fixture-original')/filename).read_bytes()==OLD
            elif mode=='follow-after-update':
                assert (a/'live').read_bytes()==OLD and (b/'live').read_bytes()==OLD, name+' committed to stale followed target'
            else:
                assert target.read_bytes()==OLD, name+' changed prior live destination'
            if not new_target:
                archive_assert(rows,left,OLD); archive_assert(rows,right,OLD)
            else:
                assert any(row[0]=='archive-after' and row[3]=='NONE' for row in rows), 'absent target archive advanced'
            if mode=='sidecar-second-rename-error':
                assert target.with_name('._'+target.name).joinpath('sentinel').read_bytes()==b'FOREIGN AUXILIARY SENTINEL'
            if recover and mode not in ('root-after-validation','sidecar-second-rename-error'):
                if follow:
                    (right/filename).unlink(); (right/filename).symlink_to(a/'live')
                if new_target:
                    target.unlink()
                elif not target.exists() or target.read_bytes()!=NEW:
                    target.write_bytes(OLD)
                recovery=sync()
                assert target.read_bytes()==NEW and (left/filename).read_bytes()==NEW, name+' follow-up transfer failed'
                archive_assert(recovery,left,NEW); archive_assert(recovery,right,NEW)
        self.report(name)

    def legacy_and_properties(self):
        for remote in (False,True):
            label='remote' if remote else 'local'
            self.case(label+' actual candidate AppleDouble legacy handoff','candidate-sidecar',remote,extra=('-rsrc','true'))
            self.case(label+' existing Finder-only sidecar legacy handoff','target-sidecar',remote,extra=('-rsrc','true'))
            self.case(label+' DATA committed then sidecar rename fails without live cleanup','sidecar-second-rename-error',remote,
                      extra=('-rsrc','true'),recover=False)
            self.case(label+' source-selected props and native resource fork',remote=remote,
                      extra=('-rsrc','true'),native_fork=True)
            self.case(label+' actual old-file backup before native replacement',remote=remote,backup=True)
            self.case(label+' Update preserves decomposed existing basename',remote=remote,
                      filename='cafe\u0301.bin',extra=('-unicode','true','-ignorecase','false'))

    def producer_case(self,kind,orientation):
        if self.only and self.only!=kind:
            return
        self.count+=1
        root=self.work/f'case-{self.count}'
        left,right,state,receiver=(root/name for name in ('left','right','state','receiver-state'))
        for path in (left,right,state,receiver):
            path.mkdir(parents=True)
        remote=orientation!='local'
        source,destination=(right,left) if orientation=='local-receiver' else (left,right)
        semantic=kind=='semantic'
        filename='image.dng' if semantic else 'resume.bin'
        if semantic:
            old,new=semantic_fixture(b'one'),semantic_fixture(b'two')
        else:
            old=(OLD*513)[:4*1024*1024]
            new=b'NEW-'+old[4:]
        incoming=source/filename;target=destination/filename
        incoming.write_bytes(old);target.write_bytes(old)
        log=root/'events.tsv'
        loopback=root/'loopback.py'
        loopback.write_text('#!/usr/bin/python3\nimport os,sys\nos.environ["UNISON"]='+repr(str(receiver))+
            '\na=sys.argv[1:]; i=a.index('+repr(str(self.binary))+'); os.execv(a[i],a[i:])\n')
        loopback.chmod(0o700)
        command=[str(self.binary),str(left),('ssh://localhost/'+str(right)) if remote else str(right),
            '-batch','-auto','-fastcheck','false','-times','-clone','auto' if semantic else 'off',
            '-semanticworkers','2','-path',filename,'-debug','semantic','-debug','copy']
        if remote:
            command+=['-sshcmd',str(loopback),'-servercmd',str(self.binary)]
        if semantic:
            command+=['-semanticdng']
        env=dict(self.environment,UNISON=str(state),UNISON_FINAL_TEST_LOG=str(log),
            UNISON_FINAL_TEST_ROOT=str(destination),UNISON_FINAL_TEST_LEFT=str(source),
            UNISON_FINAL_TEST_PATH=filename,UNISON_FINAL_TEST_INCOMING=str(incoming),
            UNISON_FINAL_TEST_NEGATIVE='',UNISON_FINAL_TEST_SEMANTIC='local' if semantic and not remote else '')
        def sync(mode):
            log.write_text('')
            child=subprocess.run(command,env=dict(env,UNISON_FINAL_TEST_MODE=mode),
                capture_output=True,text=True,timeout=90)
            text=child.stdout+child.stderr
            (root/(mode+'-run.log')).write_text(text)
            assert child.returncode==0, (kind,orientation,text)
            return event_rows(log),text
        sync('observe');incoming.write_bytes(new)
        rows,text=sync('observe' if semantic else kind)
        assert incoming.read_bytes()==new and target.read_bytes()==new, (kind,orientation,'bytes')
        archive_assert(rows,source,new);archive_assert(rows,destination,new)
        assert any(row[:2]==['native-published','true'] for row in rows), 'producer bypassed actual native publication'
        owner=[row for row in rows if row[0]=='producer-owner' and row[1]==str(destination)]
        assert owner and owner[-1][2]==('connection' if orientation=='remote-receiver' else 'local'), owner
        completed=[row for row in rows if row[0]=='producer-finished' and row[1]==str(destination)]
        assert completed and completed[-1][2:]==['true','false'], 'producer completion was not guarded'
        if semantic:
            label='local-semantic-output' if not remote else 'remote-semantic-output'
            outputs=[row for row in rows if row[0]==label]
            assert len(outputs)==1 and int(outputs[0][1])==target.stat().st_ino, 'semantic output witness was omitted or replaced'
            assert ('Local semantic workers wrote' if not remote else 'Remote semantic clone wrote') in text
            if not remote:
                assert any(row[0]=='source-clone-declined' for row in rows), 'local semantic source-clone seam did not fire'
        else:
            created=[row for row in rows if row[0]=='resume-created']
            assert len(created)==1 and any(row[:2]==['injected',kind] for row in rows), 'resume fixture was not admitted'
            inode=int(created[0][2]);prefix=int(created[0][3])
            if remote:
                assert len([row for row in rows if row[0]=='resume-admitted'])==1, 'existing receiver temporary was not admitted before hashing'
                assert inode==target.stat().st_ino, 'resume writer replaced admitted inode'
                writers=[row[3] for row in rows if row[0]=='producer-writer' and row[1]==str(destination)]
                expected=[] if kind=='resume-complete' else ['append:'+str(prefix if kind=='resume-prefix' else 0)]
                assert writers==expected, (kind,'writer mode',writers,expected)
                if kind=='resume-prefix':
                    assert prefix>=1024*1024 and 'Keeping '+str(prefix)+' bytes' in text
            else:
                assert not any(row[0]=='resume-admitted' for row in rows), 'local copier unexpectedly resumed an old stage'
                assert inode!=target.stat().st_ino, 'local copy did not rebuild old temporary'
            assert not Path(created[0][1]).exists(), 'normal resume name survived publication'
        self.report(orientation+' '+kind+' retained producer and exact archives')

    def simple_compatibility(self,kind,remote=False):
        if self.only and self.only!=kind:
            return
        self.count+=1
        root=self.work/f'case-{self.count}'
        left,right,state,receiver=(root/name for name in ('left','right','state','receiver-state'))
        for path in (left,right,state,receiver):
            path.mkdir(parents=True)
        log=root/'events.tsv'
        filename='cafe\u0301.bin' if kind=='NFC-copy' else ('album' if kind=='directory' else 'item.bin')
        loopback=root/'loopback.py'
        loopback.write_text('#!/usr/bin/python3\nimport os,sys\nos.environ["UNISON"]='+repr(str(receiver))+
                           '\na=sys.argv[1:]; i=a.index('+repr(str(self.binary))+'); os.execv(a[i],a[i:])\n')
        loopback.chmod(0o700)
        command=[str(self.binary),str(left),('ssh://localhost/'+str(right)) if remote else str(right),
                 '-batch','-auto','-fastcheck','false','-times','-clone','off','-semanticworkers','2','-path',filename]
        if remote:
            command += ['-sshcmd',str(loopback),'-servercmd',str(self.binary)]
        if kind=='NFC-copy':
            command += ['-unicode','true','-ignorecase','false']
            (left/filename).write_bytes(NEW)
        elif kind=='directory':
            (left/filename).write_bytes(OLD); (right/filename).write_bytes(OLD)
        else:
            (left/filename).write_bytes(OLD); (right/filename).write_bytes(OLD)
        env=dict(self.environment,UNISON=str(state),UNISON_FINAL_TEST_LOG=str(log),
                 UNISON_FINAL_TEST_ROOT=str(right),UNISON_FINAL_TEST_LEFT=str(left),
                 UNISON_FINAL_TEST_PATH=filename,UNISON_FINAL_TEST_MODE='observe',UNISON_FINAL_TEST_NEGATIVE='')
        def sync():
            log.write_text('')
            child=subprocess.run(command,env=env,text=True,capture_output=True,timeout=90)
            (root/'compatibility-run.log').write_text(child.stdout+child.stderr)
            assert child.returncode==0, kind+'\n'+child.stdout+child.stderr
            return event_rows(log)
        if kind=='NFC-copy':
            rows=sync()
            target=unicodedata.normalize('NFC',filename)
            assert (right/target).read_bytes()==NEW
            rename_rows=[row for row in rows if row[0]=='rename']
            assert rename_rows and rename_rows[-1][-1]==target, 'Copy did not select normalized native target'
            assert any(row[:2]==['native-published','true'] for row in rows), 'normalized copy bypassed native binding'
            assert [path.name for path in right.iterdir()]==[target], 'unexpected normalization stage or second name'
        else:
            sync()
            if kind=='directory':
                (left/filename).unlink(); (left/filename).mkdir()
                (left/filename/'child.bin').write_bytes(NEW)
                rows=sync()
                assert (right/filename/'child.bin').read_bytes()==NEW
                assert not any(row[0]=='native-published' for row in rows), 'directory was misqualified as regular native publication'
            else:
                (left/filename).write_bytes(NEW); (right/filename).write_bytes(SENTINEL)
                command += ['-prefer',str(left),'-copyonconflict']
                rows=sync()
                assert (right/filename).read_bytes()==NEW
                copies=[path for path in right.iterdir() if '(conflict' in path.name]
                assert copies and any(path.read_bytes()==SENTINEL for path in copies), 'actual conflicting old version was lost'
                assert any(row[0]=='legacy-handoff' for row in rows), 'conflict-copy branch was not explicitly handed off'
                assert not any(row[0]=='native-published' for row in rows), 'conflict transaction acquired regular-only publication claim'
        self.report(('remote' if remote else 'local')+' '+kind+' actual caller compatibility')

    def old_peers(self):
        if self.only and self.only!='old-peer':
            return
        if self.peer is None:
            print('SKIP old-peer protocol controls: supply --old-peer',flush=True)
            return
        for old_client in (False,True):
            self.count+=1
            root=self.work/f'case-{self.count}'; left,right,state,receiver=(root/name for name in ('left','right','state','receiver-state'))
            for path in (left,right,state,receiver):
                path.mkdir(parents=True)
            client=self.peer if old_client else self.binary
            server=self.binary if old_client else self.peer
            log=root/'events.tsv'; filename='item.bin'
            loopback=root/'loopback.py'
            loopback.write_text('#!/usr/bin/python3\nimport os,sys\nos.environ["UNISON"]='+repr(str(receiver))+
                               '\na=sys.argv[1:]; i=a.index('+repr(str(server))+'); os.execv(a[i],a[i:])\n')
            loopback.chmod(0o700)
            command=[str(client),str(left),'ssh://localhost/'+str(right),'-batch','-auto','-fastcheck','false',
                     '-sshcmd',str(loopback),'-servercmd',str(server)]
            env=dict(self.environment,UNISON=str(state),UNISON_FINAL_TEST_LOG=str(log),
                     UNISON_FINAL_TEST_ROOT=str(right),UNISON_FINAL_TEST_LEFT=str(left),
                     UNISON_FINAL_TEST_PATH=filename,UNISON_FINAL_TEST_MODE='observe',UNISON_FINAL_TEST_NEGATIVE='')
            for data in (OLD,NEW):
                (left/filename).write_bytes(data); log.write_text('')
                child=subprocess.run(command,env=env,text=True,capture_output=True,timeout=90)
                (root/'old-peer-run.log').write_text(child.stdout+child.stderr)
                assert child.returncode==0, child.stdout+child.stderr
                assert (right/filename).read_bytes()==data
                rows=event_rows(log)
                assert not any(row[0]=='native-published' for row in rows), 'old peer acquired unnegotiated final binding'
                if not old_client:
                    assert any(row[:2]==['supported','false'] for row in rows), 'new sender did not record feature fallback'
            self.report('old peer '+('sender' if old_client else 'receiver')+' negotiation and ordinary exact transfer')

    def run(self):
        if self.negative=='resolution':
            self.case('negative resolution guard detects stale followed target','follow-after-update',follow=True,recover=False)
            raise AssertionError('negative control unexpectedly passed')
        if self.negative=='live-cleanup':
            self.case('negative cleanup guard preserves newly live output','post-native-exception',recover=False)
            raise AssertionError('negative control unexpectedly passed')
        for remote in (False,True):
            label='remote' if remote else 'local'
            self.case(label+' ordinary bound replacement and exact archive advancement',remote=remote)
            for mode in ('candidate-before-attach','candidate-replaced-before-attach',
                         'candidate-after-validation','candidate-replaced-after-validation','target-after-validation',
                         'target-samebytes-after-validation',
                         'reject-validation','sidecar-after-validation','target-after-update',
                         'target-disappears-after-update','target-after-backup','candidate-after-backup',
                         'post-native-exception','post-native-OOM','post-native-target-replaced',
                         'native-rename-EIO','native-result-stat-EIO','archive-before-exception'):
                self.case(label+' '+mode,mode,remote,validate=('validation' in mode),
                          extra=('-rsrc','true') if mode=='sidecar-after-validation' else (),
                          backup=(mode in ('target-after-backup','candidate-after-backup')))
            self.case(label+' absent target appearance is preserved','target-appears-after-update',remote,new_target=True)
            self.case(label+' followed-link retarget after destination check fails','follow-after-update',remote,follow=True)
            self.case(label+' root rebinding during settled validation preserves replacement','root-after-validation',remote,
                      validate=True,recover=False)
        self.legacy_and_properties()
        for orientation in ('local','remote-receiver','local-receiver'):
            for kind in ('resume-complete','resume-prefix','resume-invalid','resume-empty','semantic'):
                self.producer_case(kind,orientation)
        for remote in (False,True):
            for kind in ('NFC-copy','conflict','directory'):
                self.simple_compatibility(kind,remote)
        self.old_peers()
        print('Final Files publication:',self.count,'actual CLI caller cases passed; synthetic cooperative scope',
              flush=True)


def arguments(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    parser.add_argument('--ocamlopt',required=True)
    parser.add_argument('--old-peer',type=Path)
    parser.add_argument('--keep-work',action='store_true')
    parser.add_argument('--negative-control',choices=['resolution','live-cleanup'])
    parser.add_argument('--only',help='run just the named mutation mode, NFC-copy, directory, conflict or old-peer')
    args=parser.parse_args(argv)
    modes={'observe','candidate-before-attach','candidate-replaced-before-attach',
           'candidate-after-validation','candidate-replaced-after-validation','target-after-validation',
           'target-samebytes-after-validation','reject-validation','sidecar-after-validation',
           'target-after-update','target-disappears-after-update','target-after-backup',
           'candidate-after-backup','post-native-exception','post-native-OOM',
           'post-native-target-replaced','native-rename-EIO','native-result-stat-EIO',
           'archive-before-exception','target-appears-after-update','follow-after-update',
           'root-after-validation','candidate-sidecar','target-sidecar','sidecar-second-rename-error',
           'resume-complete','resume-prefix','resume-invalid','resume-empty','semantic',
           'NFC-copy','directory','conflict','old-peer'}
    if args.only is not None and args.only not in modes:
        parser.error('unknown selected case: '+args.only)
    if args.only=='old-peer' and args.old_peer is None:
        parser.error('--only old-peer requires --old-peer')
    if args.only and args.negative_control:
        parser.error('--only cannot be combined with --negative-control')
    return args


def main():
    args=arguments()
    root=Path(__file__).resolve().parents[1]
    environment=os.environ.copy()
    for name in ('OCAMLLIB','OCAMLPATH','CAML_LD_LIBRARY_PATH','OCAMLRUNPARAM'):
        environment.pop(name,None)
    work=Path(tempfile.mkdtemp(prefix='unison-final-caller-',dir='/private/tmp'))
    print('work',work,flush=True)
    shutil.copy2(__file__,work/'runner.py')
    receipt={'command':sys.argv,'scope':'Disposable actual Files/CLI/archives and retained producer handoff; cooperative namespace',
             'negative_control':args.negative_control,'only':args.only}
    try:
        binary=compile_private(root,args.build.resolve(),args.ocamlopt,work,environment)
        suite=Suite(binary,args.old_peer,work,environment,args.negative_control,args.only)
        try:
            suite.run()
            assert suite.passed, 'selected suite completed no cases'
            receipt['status']='PASS_SELECTED_CASES'
        except AssertionError as error:
            if not args.negative_control:
                raise
            expected='stale followed target' if args.negative_control=='resolution' else 'deleted or rolled back'
            if expected not in str(error):
                raise
            print('PASS expected negative-control failure:',error,flush=True)
            receipt['status']='PASS_NEGATIVE_CONTROL_DETECTED'; receipt['detected']=str(error)
        finally:
            receipt['passed_cases']=suite.passed
            receipt['attempted_cases']=suite.count
            receipt.setdefault('status','FAIL_OR_OPEN_GAP')
            (work/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    finally:
        if not args.keep_work:
            shutil.rmtree(work)


if __name__=='__main__':
    main()
