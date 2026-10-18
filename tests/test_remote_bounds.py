#!/usr/bin/env python3
"""Test RPC preallocation limits against header-only pipes in a private build.
Usage: python3 tests/test_remote_bounds.py /private/tmp/isolated-unison-build
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import nullcontext


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--compiler', default=os.environ.get('OCAMLOPT', 'ocamlopt'))
    parser.add_argument('--negative-family', choices=('all','framing','body','decoded','stream','pending','result','errors','outbound','queue'), default='all')
    args = parser.parse_args()
    repository = Path(__file__).resolve().parent.parent
    build = args.build.resolve() / "src"
    makefile = (build / "Makefile.OCaml").read_text()
    def objects(name):
        body = re.search(r"^" + name + r" = (.*?)(?=\n\n)", makefile, re.M | re.S).group(1)
        body = body.replace("\\\n", " ").replace("$(SYSTEM)", "generic")
        body = body.replace("$(WINOBJS)", "").replace("$(WINCOBJS)", "")
        return body.replace("$(OBJ_EXT)", ".o").replace(".cmo", ".cmx").split()
    modules = objects("OCAMLOBJS")
    modules = modules[:modules.index("remote.cmx")]
    includes = [build, build / "lwt", build / "ubase", build / "system",
                build / "system/generic", build / "lwt/generic"]
    flags = [flag for path in includes for flag in ["-I", str(path)]] + ["-I", "+unix", "-I", "+str"]
    workspace = nullcontext(tempfile.mkdtemp(prefix="unison-rpc-bounds-", dir="/private/tmp")) if args.report else tempfile.TemporaryDirectory(prefix="unison-rpc-bounds-", dir="/private/tmp")
    with workspace as tmp:
        work = Path(tmp)
        def controlled(source):
            anchor='let perform_owned_output q kind parts consume ='
            assert source.count(anchor)==1
            source=source.replace(anchor,'let output_test_before_admit : (unit->unit) option ref=ref None\n'+anchor,1)
            anchor='    reserve_output_owner owner;'
            assert source.count(anchor)==1
            source=source.replace(anchor,'    (match !output_test_before_admit with None->()|Some f->output_test_before_admit:=None;f());\n'+anchor,1)
            anchor='let receivePacket ?maxBytes'
            assert source.count(anchor)==1
            source=source.replace(anchor,'let header_test_guard : int option ref=ref None\nlet startup_test_fail_allocation=ref false\n'+anchor,1)
            anchor='  let buf = Bytearray.create length in'
            assert source.count(anchor)==1
            source=source.replace(anchor,'  (match !header_test_guard with Some cap when length>cap->failwith "DESIGNATED header payload allocation reached" | _->());\n'+anchor,1)
            anchor='    let inp=Bytearray.create maximum and buf=Bytearray.create 1 in'
            assert source.count(anchor)==1
            return source.replace(anchor,'    if !startup_test_fail_allocation then failwith "DESIGNATED startup allocation failure";\n'+anchor,1)
        (work / "remoteForTest.ml").write_text(controlled((repository / "src/remote.ml").read_text()))
        (work / "remoteTest.ml").write_text((repository / "tests/remote_bounds.ml").read_text()+'\n'+(repository/'tests/remote_output_slices.ml').read_text()+'\n'+(repository/'tests/remote_header_bounds.ml').read_text()+'\n'+(repository/'tests/remote_startup_bounds.ml').read_text()+'\n'+(repository/'tests/remote_packet_bounds.ml').read_text()+'\n'+(repository/'tests/remote_stream_limits.ml').read_text()+'\n'+(repository/'tests/remote_body_input.ml').read_text()+'\n'+(repository/'tests/remote_pending_limits.ml').read_text()+'\n'+(repository/'tests/remote_stream_errors.ml').read_text()+'\n'+(repository/'tests/remote_body_retained.ml').read_text()+'\n'+(repository/'tests/remote_result_input.ml').read_text()+'\n'+(repository/'tests/remote_decoded_input.ml').read_text()+'\n'+(repository/'tests/remote_output_owners.ml').read_text())
        compiler = args.compiler
        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        record = dict(schema='unison-rpc-input-bounds/1', status='failed',
                      negative_family=args.negative_family,
                      compiler=compiler, build_snapshot=str(build.parent),
                      tested_sources={'src/remote.ml': sha(repository/'src/remote.ml'),
                                      'tests/remote_bounds.ml': sha(repository/'tests/remote_bounds.ml'),
                                      'tests/remote_output_slices.ml': sha(repository/'tests/remote_output_slices.ml'),
                                      'tests/remote_output_owners.ml': sha(repository/'tests/remote_output_owners.ml'),
                                      'tests/remote_header_bounds.ml': sha(repository/'tests/remote_header_bounds.ml'),
                                      'tests/remote_startup_bounds.ml': sha(repository/'tests/remote_startup_bounds.ml'),
                                      'tests/remote_packet_bounds.ml': sha(repository/'tests/remote_packet_bounds.ml'),
                                      'tests/remote_stream_limits.ml': sha(repository/'tests/remote_stream_limits.ml'),
                                      'tests/remote_pending_limits.ml': sha(repository/'tests/remote_pending_limits.ml'),
                                      'tests/remote_result_input.ml': sha(repository/'tests/remote_result_input.ml'),
                                      'tests/remote_stream_errors.ml': sha(repository/'tests/remote_stream_errors.ml'),
                                      'tests/remote_body_input.ml': sha(repository/'tests/remote_body_input.ml'),
                                      'tests/remote_body_retained.ml': sha(repository/'tests/remote_body_retained.ml'),
                                      'tests/remote_decoded_input.ml': sha(repository/'tests/remote_decoded_input.ml'),
                                      'tests/test_remote_bounds.py': sha(Path(__file__))},
                      linked_objects={name: sha(build/name) for name in modules+objects('COBJS')},
                      commands=[])
        def execute(command, **kwargs):
            result = subprocess.run(command, cwd=work, **kwargs)
            record['commands'].append(dict(argv=command, exit_code=result.returncode))
            result.check_returncode()
        command = [compiler] + flags + ["unix.cmxa", "str.cmxa"]
        command += [str(build / obj) for obj in modules]
        command += ["remoteForTest.cmx", "remoteTest.ml"]
        command += [str(build / obj) for obj in objects("COBJS")]
        command += ["-o", "remote-test"]
        try:
            execute([compiler] + flags + ["-c", "remoteForTest.ml"])
            execute(command)
            execute([str(work / "remote-test")], timeout=15,
                    env=dict(os.environ, UNISON=str(work / "state")))
            record['workspace']=str(work)
            record['binary_sha256']=sha(work/'remote-test')
            source=(repository/'src/remote.ml').read_text()
            if args.negative_family in ('all','framing'):
                # Remove only the selected decoded limits; unit-list payload is
                # 2000 elements, so this counterexample never asks for huge memory.
                negative=work/'negative';negative.mkdir(mode=0o700)
                source=(repository/'src/remote.ml').read_text()
                old='(boundedMarshalingFunctions maxArgs mArg) (boundedMarshalingFunctions maxResult mRet) f in'
                assert source.count(old)==1
                bad=source.replace(old,'(defaultMarshalingFunctions mArg) (defaultMarshalingFunctions mRet) f in')
                arg_scope='~decodeArgs:(with_decoded_args (Some maxArgs) mArg tag) name'
                assert bad.count(arg_scope)==1
                bad=bad.replace(arg_scope,'name',1)
                (negative/'remoteForTest.ml').write_text(controlled(bad))
                (negative/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                private_flags=['-I',str(negative),*flags]
                for argv in [[compiler,*private_flags,'-c','remoteForTest.ml'],
                             [compiler,*private_flags,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','remote-negative']]:
                    c=subprocess.run(argv,cwd=negative,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(negative/'remote-negative')],cwd=negative,env=dict(os.environ,UNISON=str(negative/'state')),capture_output=True,text=True,timeout=15)
                (negative/'test.log').write_text(c.stdout+c.stderr)
                assert c.returncode==2 and 'DESIGNATED decoded collection reached server' in c.stderr,c.stdout+c.stderr
                record['negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(negative/'remoteForTest.ml'),binary_sha256=sha(negative/'remote-negative'),scope='Only bounded registrations use legacy decoder;2000zero-payload elements, no huge allocation')
                # Restore only unbounded header routing. The test-only allocation
                # guard fails before a body allocation/read; no large allocation.
                header=work/'header-negative';header.mkdir(mode=0o700)
                old='receiveHeader conn >>= (fun req ->'
                assert source.count(old)==1
                bad_header=source.replace(old,'receivePacket conn >>= (fun buffer -> let req=unmarshalHeader conn buffer in')
                (header/'remoteForTest.ml').write_text(controlled(bad_header))
                (header/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                hf=['-I',str(header),*flags]
                for argv in [[compiler,*hf,'-c','remoteForTest.ml'],[compiler,*hf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','header-negative']]:
                    c=subprocess.run(argv,cwd=header,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(header/'header-negative')],cwd=header,env=dict(os.environ,UNISON=str(header/'state')),capture_output=True,text=True,timeout=15)
                (header/'test.log').write_text(c.stdout+c.stderr)
                assert c.returncode==2 and 'DESIGNATED header payload allocation reached' in c.stderr,c.stdout+c.stderr
                record['header_negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(header/'remoteForTest.ml'),binary_sha256=sha(header/'header-negative'))
                startup=work/'startup-negative';startup.mkdir(mode=0o700)
                old='if !consumed=maximum then startup_exceeds ();'
                assert source.count(old)==1
                bad_startup=source.replace(old,'(* designated finite startup cap omission *)')
                (startup/'remoteForTest.ml').write_text(controlled(bad_startup))
                (startup/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                sf=['-I',str(startup),*flags]
                for argv in [[compiler,*sf,'-c','remoteForTest.ml'],[compiler,*sf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','startup-negative']]:
                    c=subprocess.run(argv,cwd=startup,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(startup/'startup-negative')],cwd=startup,env=dict(os.environ,UNISON=str(startup/'state')),capture_output=True,text=True,timeout=15)
                (startup/'test.log').write_text(c.stdout+c.stderr)
                assert c.returncode==2 and 'startup limit ignored' in c.stderr,c.stdout+c.stderr
                record['startup_negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(startup/'remoteForTest.ml'),binary_sha256=sha(startup/'startup-negative'),scope='Only delimiter byte limit omitted; nine original bytes, existing fixed8byte destination, no large allocation')
                packet=work/'packet-negative';packet.mkdir(mode=0o700)
                old='let maximum=match maxBytes with None->maximum | Some n->min maximum n in'
                assert source.count(old)==1
                bad_packet=source.replace(old,'let maximum=match maxBytes with None->(ignore maximum;max_int) | Some n->(ignore maximum;n) in')
                (packet/'remoteForTest.ml').write_text(controlled(bad_packet))
                (packet/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                pf=['-I',str(packet),*flags]
                for argv in [[compiler,*pf,'-c','remoteForTest.ml'],[compiler,*pf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','packet-negative']]:
                    c=subprocess.run(argv,cwd=packet,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(packet/'packet-negative')],cwd=packet,env=dict(os.environ,UNISON=str(packet/'state')),capture_output=True,text=True,timeout=15)
                (packet/'test.log').write_text(c.stdout+c.stderr)
                assert c.returncode==2 and 'DESIGNATED header payload allocation reached' in c.stderr,c.stdout+c.stderr
                record['packet_negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(packet/'remoteForTest.ml'),binary_sha256=sha(packet/'packet-negative'),scope='Only global outer cap omitted; private guard prevents nine-byte allocation/body wait')
            body_negatives=[
                ('body-decoder-negative',
                 'with_body_packet packet (fun buf ->',
                 '(fun f -> f (fst packet)) (fun buf ->',
                 'DESIGNATED raw body input retained'),
                ('body-handoff-negative',
                 'if not !handed_off then begin',
                 'if (ignore !handed_off;true) then begin',
                 'DESIGNATED handed-off reply released'),
                ('body-uncertainty-negative',
                 'let guard_body_borrower f = RetainedOwnership.guard ~is_uncertain:body_unresolved f',
                 'let guard_body_borrower f = f ()',
                 'DESIGNATED body uncertainty escaped'),
                ('body-stream-uncertainty-negative',
                 '| e when body_unresolved e -> raise e',
                 '| e when body_unresolved e -> abortStream conn id',
                 'DESIGNATED stream uncertainty converted to abort'),
                ('body-registered-uncertainty-negative',
                 '| _ -> List.exists (fun classify->classify error) !body_ownership_classifiers',
                 '| _ -> false',
                 'DESIGNATED registered body uncertainty escaped')]
            for label,old,replacement,witness in (body_negatives if args.negative_family in ('all','body') else []):
                assert source.count(old)==1
                private=work/label;private.mkdir(mode=0o700)
                (private/'remoteForTest.ml').write_text(controlled(source.replace(old,replacement)))
                (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                bf=['-I',str(private),*flags]
                for argv in [[compiler,*bf,'-c','remoteForTest.ml'],[compiler,*bf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o',label]]:
                    c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(private/label)],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                (private/'test.log').write_text(c.stdout+c.stderr)
                assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                record[label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/label),scope='Single ownership mutation; original tiny pipe inputs; expected assertion failure')
            record['controlled_remote_sha256']=sha(work/'remoteForTest.ml')
            record['controlled_probe_sha256']=sha(work/'remoteTest.ml')
            if args.negative_family in ('all','decoded'):
                # Reintroduce only the second handler decode. Mutable decoded
                # cell identity and conversion count must reject this participant.
                twice=work/'double-decode-negative';twice.mkdir(mode=0o700)
                anchor='      let run () =\n        BorrowedWork.bind (fun () -> serverSide conn args)'
                assert source.count(anchor)==1
                bad=source.replace(anchor,'      let run () =\n        let args = unmarshalArgs conn buf in\n        BorrowedWork.bind (fun () -> serverSide conn args)',1)
                (twice/'remoteForTest.ml').write_text(controlled(bad))
                (twice/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                tf=['-I',str(twice),*flags]
                for argv in [[compiler,*tf,'-c','remoteForTest.ml'],[compiler,*tf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','double-negative']]:
                    c=subprocess.run(argv,cwd=twice,capture_output=True,text=True,timeout=30)
                    record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                c=subprocess.run([str(twice/'double-negative')],cwd=twice,env=dict(os.environ,UNISON=str(twice/'state')),capture_output=True,text=True,timeout=15)
                assert c.returncode==2 and 'DESIGNATED scope and handler received distinct decoded values' in c.stderr,c.stdout+c.stderr
                record['double_decode_negative']=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(twice/'remoteForTest.ml'),binary_sha256=sha(twice/'double-negative'))
                record['decoded_owner_negatives']={}
                for label,needle,replacement,witness in [
                    ('legacy-decoded-bypass','registerSpecialServerCmd ~decodeArgs:(with_decoded_args None mArg tag)','registerSpecialServerCmd','DESIGNATED legacy decoded owner missing'),
                    ('decoded-bypass','| Some decode -> decode conn buf use','| Some _ -> use (unmarshalArgs conn buf)','DESIGNATED decoded arguments released before output'),
                    ('decoded-early-release','    use args in','    let borrowed=use args in release_decoded_input ticket;borrowed in','DESIGNATED decoded arguments released before output'),
                    ('decoded-uncertainty','~is_uncertain:body_unresolved ~on_retained:retain work','~is_uncertain:(fun _->false) ~on_retained:retain work','DESIGNATED decoded uncertainty escaped its owner')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    pf=['-I',str(private),*flags]
                    for argv in [[compiler,*pf,'-c','remoteForTest.ml'],[compiler,*pf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['decoded_owner_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','stream'):
                record['stream_limit_negatives']={}
                for label,needle,replacement in [
                    ('stream-cap-negative','?maxBytes:(Util.StringMap.find_opt cmdName !serverStreamLimits)','?maxBytes:None'),
                    ('fallback-cap-negative','| Some limit -> start_bounded_request conn limit dispatch','| Some limit -> if Util.StringMap.mem cmdName !serverStreamLimits then start_body_request conn dispatch else start_bounded_request conn limit dispatch')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    sf=['-I',str(private),*flags]
                    for argv in [[compiler,*sf,'-c','remoteForTest.ml'],[compiler,*sf,'unix.cmxa','str.cmxa',*[str(build/o)for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o)for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and 'DESIGNATED header payload allocation reached' in c.stderr,c.stdout+c.stderr
                    record['stream_limit_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','pending'):
                record['pending_limit_negatives']={}
                for label,needle,replacement,witness in [
                    ('pending-quota-negative','if MsgIdMap.cardinal !receivers>=slots then','if false && MsgIdMap.cardinal !receivers>=slots then','DESIGNATED pending reply cap ignored'),
                    ('pending-preflight-negative','| None ->\n    check_receiver_capacity ();\n    let maxBytes =','| None ->\n    let maxBytes =','DESIGNATED full registry marshaled new request'),
                    ('pending-duplicate-negative','if MsgIdMap.mem id !receivers then raise(Util.Fatal "RPC reply id already pending");','if false && MsgIdMap.mem id !receivers then raise(Util.Fatal "RPC reply id already pending");','DESIGNATED duplicate pending id replaced')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    pf=['-I',str(private),*flags]
                    for argv in [[compiler,*pf,'-c','remoteForTest.ml'],[compiler,*pf,'unix.cmxa','str.cmxa',*[str(build/o)for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o)for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['pending_limit_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','result'):
                record['result_owner_negatives']={}
                for label,needle,replacement,witness in [
                    ('result-decode-bypass','~decodeResult:(with_decoded_result (Some maxResult) mRet result_tag)','', 'DESIGNATED decoded result missing during consumer'),
                    ('result-early-release','    use result in','    release_result_input ticket;use result in','DESIGNATED decoded result missing during consumer'),
                    ('result-uncertainty','~is_uncertain:body_unresolved ~on_retained:retain_result work','~is_uncertain:(fun _->false) ~on_retained:retain_result work','DESIGNATED uncertain result escaped'),
                    ('result-root-omission','    value:=Some result;','    (* designated result root omitted *)','DESIGNATED uncertain result lost value root'),
                    ('result-bytes-bypass','if !decoded_result_bytes>byte_limit || bytes>byte_limit- !decoded_result_bytes ||','if false ||', 'DESIGNATED result byte quota bypass')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    rf=['-I',str(private),*flags]
                    for argv in [[compiler,*rf,'-c','remoteForTest.ml'],[compiler,*rf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['result_owner_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','errors'):
                record['stream_error_negatives']={}
                for label,needle,replacement,witness in [
                    ('stream-error-preflight','    check_stream_error_capacity ();','    (* designated stream preflight omitted *)','DESIGNATED full error registry ran another handler'),
                    ('stream-error-bytes','bytes>limit- !stream_error_bytes then','false then','DESIGNATED stream diagnostic byte limit ignored'),
                    ('stream-error-early-ping','let work ()=entry.stream_borrowed<-true;use () in','let work ()=entry.stream_borrowed<-true;release_stream_error entry;use () in','DESIGNATED ping released stream error before output'),
                    ('stream-error-reset','if not entry.stream_borrowed then release_stream_error entry','release_stream_error entry','DESIGNATED reset revoked borrowed stream error'),
                    ('stream-error-unknown','| _ -> raise error in','| _ -> 0 in','DESIGNATED unknown exception stored'),
                    ('stream-error-uncertainty','~is_uncertain:body_unresolved ~on_retained:retain_stream work','~is_uncertain:(fun _->false) ~on_retained:retain_stream work','DESIGNATED stream error uncertainty escaped'),
                    ('stream-error-borrow','if entry.stream_borrowed then raise(Util.Fatal "RPC stream error already borrowed");','(* designated duplicate borrower check omitted *)','DESIGNATED duplicate borrower invoked')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1,(label,source.count(needle))
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    ef=['-I',str(private),*flags]
                    for argv in [[compiler,*ef,'-c','remoteForTest.ml'],[compiler,*ef,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['stream_error_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','outbound'):
                record['output_slice_negatives']={}
                for label,needle,replacement,witness in [
                    ('output-count-end','fillBuffer2 conn s pos (pos+len)','fillBuffer2 conn s pos len','DESIGNATED output slice length changed'),
                    ('output-whole-list','  ignore(output_slices_length parts);','  (* designated whole-list preflight omitted *)','DESIGNATED invalid list copied earlier prefix'),
                    ('output-normal-prequeue','perform_owned_output conn.outputQueue Normal l\n    (fun parts->fillBuffer conn.outputBuffer parts)','performOutput conn.outputQueue Normal (fun ()->fillBuffer conn.outputBuffer l)','DESIGNATED invalid output was queued'),
                    ('output-idle-prequeue','perform_owned_output conn.outputQueue Idle l\n    (fun parts->fillBuffer conn.outputBuffer parts)','performOutput conn.outputQueue Idle (fun ()->fillBuffer conn.outputBuffer l)','DESIGNATED invalid output was queued'),
                    ('output-urgent-prequeue','perform_owned_output conn.outputQueue Urgent l\n    (fun parts->BorrowedWork.bind(fun()->fillBuffer conn.outputBuffer parts)\n      (fun()->flushBuffer conn.outputBuffer))','performOutput conn.outputQueue Urgent (fun ()->BorrowedWork.bind(fun()->fillBuffer conn.outputBuffer l)(fun()->flushBuffer conn.outputBuffer))','DESIGNATED invalid output was queued'),
                    ('output-empty-flush','  if pos=endpos then Lwt.return () else','  (* designated empty slice check omitted *)','DESIGNATED empty slice flushed buffer'),
                    ('output-total-overflow','if total<0 || len<0 || len>max_int-total then','if false then','DESIGNATED output length arithmetic wrapped'),
                    ('output-range','if pos<0 || len<0 || pos>available || len>available-pos then','if false then','DESIGNATED invalid output slice accepted')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1,(label,source.count(needle))
                    (private/'remoteForTest.ml').write_text(controlled(source.replace(needle,replacement,1)))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    of=['-I',str(private),*flags]
                    for argv in [[compiler,*of,'-c','remoteForTest.ml'],[compiler,*of,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['output_slice_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            if args.negative_family in ('all','queue'):
                record['output_owner_negatives']={}
                for label,needle,replacement,witness in [
                    ('output-owner-recheck','if !(lane.out_count)>=slots ||\n     !(lane.out_bytes)>budget','if false ||\n     !(lane.out_bytes)>budget','DESIGNATED stale output admission accepted'),
                    ('output-owner-slots','if !(lane.out_count)>=slots || !(lane.out_bytes)>budget || !(lane.out_parts)>part_limit then','if false || !(lane.out_bytes)>budget || !(lane.out_parts)>part_limit then','DESIGNATED output slot quota ignored'),
                    ('output-owner-bytes','if count>=remaining_parts || len>remaining_bytes-bytes then','if count>=remaining_parts then','DESIGNATED output byte quota ignored'),
                    ('output-owner-parts','if count>=remaining_parts || len>remaining_bytes-bytes then','if len>remaining_bytes-bytes then','DESIGNATED output part quota ignored'),
                    ('output-owner-urgent','|Urgent->urgentOutputLane','|Urgent->normalOutputLane','DESIGNATED urgent output not independent'),
                    ('output-owner-early','(fun()->started:=true;consume owner.out_payload)','(fun()->started:=true;let actual=consume owner.out_payload in release_output_owner owner;actual)','DESIGNATED urgent output not independent'),
                    ('output-owner-late','      (fun ()->finish();Lwt.return())\n      (fun error->finish();Lwt.fail error)in','      (fun ()->Lwt.return())\n      (fun error->finish();Lwt.fail error)in','output owner leaked'),
                    ('output-owner-root','  let retain_output _=','  let retain_output _=owner.out_payload<-[];','DESIGNATED uncertain output lost payload root'),
                    ('output-owner-classifier','~is_uncertain:body_unresolved ~on_retained:retain_output','~is_uncertain:(fun _->false) ~on_retained:retain_output','DESIGNATED uncertain output escaped')]:
                    private=work/label;private.mkdir(mode=0o700)
                    assert source.count(needle)==1,(label,source.count(needle))
                    bad=source.replace(needle,replacement,1)
                    # Remove both the early measurement and the authoritative
                    # reservation check for whole-policy omissions. Recheck-only
                    # has its own actual nested-owner counterexample.
                    for second,omit in ({
                        'output-owner-slots': [('if !(lane.out_count)>=slots ||\n     !(lane.out_bytes)>budget', 'if false ||\n     !(lane.out_bytes)>budget')],
                        'output-owner-bytes': [('owner.out_size>budget- !(lane.out_bytes)', 'false')],
                        'output-owner-parts': [('owner.out_elements>part_limit- !(lane.out_parts)', 'false')],
                    }.get(label, [])):
                        assert bad.count(second)==1,(label,second)
                        bad=bad.replace(second,omit,1)
                    (private/'remoteForTest.ml').write_text(controlled(bad))
                    (private/'remoteTest.ml').write_bytes((work/'remoteTest.ml').read_bytes())
                    qf=['-I',str(private),*flags]
                    for argv in [[compiler,*qf,'-c','remoteForTest.ml'],[compiler,*qf,'unix.cmxa','str.cmxa',*[str(build/o) for o in modules],'remoteForTest.cmx','remoteTest.ml',*[str(build/o) for o in objects('COBJS')],'-o','negative']]:
                        c=subprocess.run(argv,cwd=private,capture_output=True,text=True,timeout=30)
                        record['commands'].append(dict(argv=argv,exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==0,c.stderr
                    c=subprocess.run([str(private/'negative')],cwd=private,env=dict(os.environ,UNISON=str(private/'state')),capture_output=True,text=True,timeout=15)
                    assert c.returncode==2 and witness in c.stderr,c.stdout+c.stderr
                    record['output_owner_negatives'][label]=dict(exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr,source_sha256=sha(private/'remoteForTest.ml'),binary_sha256=sha(private/'negative'))
            record['status']='passed'
        finally:
            if args.report:
                args.report.write_text(json.dumps(record, indent=2)+'\n')


if __name__ == "__main__":
    main()
