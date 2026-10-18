"""Original token/frame controls on production fragments/full Transfer, tiny inputs only."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--compiler',required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];build=a.build.resolve()/'src';work=Path(tempfile.mkdtemp(prefix='unison-transfer-bounds-',dir='/private/tmp'));work.chmod(0o700)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
make=(build/'Makefile.OCaml').read_text()
def objects(name):
 s=re.search('^'+name+r' = (.*?)(?=\n\n)',make,re.M|re.S).group(1)
 return s.replace('\\\n',' ').replace('$(SYSTEM)','generic').replace('$(WINOBJS)','').replace('$(WINCOBJS)','').replace('$(OBJ_EXT)','.o').replace('.cmo','.cmx').split()
modules=objects('OCAMLOBJS');modules=modules[:modules.index('remote.cmx')];native=objects('COBJS')
flags=[x for d in [build,build/'lwt',build/'ubase',build/'system',build/'system/generic',build/'lwt/generic']for x in ['-I',str(d)]]+['-I','+unix','-I','+str']
remote=(root/'src/remote.ml').read_text();start=remote.index('let intSize =');fields=remote[start:remote.index('(*************************************************************************)',start)]
copy=(root/'src/copy.ml').read_text();start=copy.index('let marshalTransferInstruction =');wire='module Remote=RemoteFieldsForTest\n'+copy[start:copy.index('let streamTransferInstruction',start)]
start=copy.index('let transferOutputLimit ')
limit_source='module Transfer=TransferForTest\n'+copy[start:copy.index('let transferFileContents',start)]
assert copy.count('let output_limit=transferOutputLimit fileKind srcFileSize in')==1
assert copy.count('Remote.registerStreamCmd ~maxPayload:(Transfer.maxInstructionBytes+Remote.intSize)')==1
assert copy.count('Transfer.receive ~output_limit fd showProgress ti')==1
assert copy.count('Transfer.Rsync.rsyncDecompress ~output_limit blockSize ifd fd showProgress ti')==1
assert copy.index('let output_limit=transferOutputLimit fileKind srcFileSize in')<copy.index('let outfd = ref None',copy.index('let transferFileContents'))
rsync_copy=copy[copy.index('(* Rsync decompressor *)'):copy.index('(* Simple generic decompressor *)')]
generic_copy=copy[copy.index('(* Simple generic decompressor *)'):copy.index('let file_id = Remote.newMsgId',copy.index('(* Simple generic decompressor *)'))]
assert rsync_copy.index('Transfer.check_output_limit output_limit;')<rsync_copy.index('let ifd = referenceFd')
assert generic_copy.index('Transfer.check_output_limit output_limit;')<generic_copy.index('destinationFd ?producer')
transfer=(root/'src/transfer.ml').read_text()
record=dict(state='failed',workspace=str(work),scope='Actual integer/Copy wire fragments and full Transfer implementation, original <=80KiB fixture files; no transport/SDK/Photo/EXIO/physical sharing/benchmark.',compiler=a.compiler,compiler_sha256=sha(a.compiler),source_pins={str(q.relative_to(root)):sha(q)for q in [root/'src/remote.ml',root/'src/copy.ml',root/'src/transfer.ml',Path(__file__),Path(__file__).with_name('probe.ml')]},linked_objects={str(build/n):sha(build/n)for n in modules+native},calls=[],negative_participants={})
def once(text,old,new):
 assert text.count(old)==1,old
 return text.replace(old,new,1)
def guarded_fields(text):return once(text,'  let b0 = Char.code','  if i<0 || i>Bytearray.length int_buf-intSize then failwith "DESIGNATED integer read reached invalid range";\n  let b0 = Char.code')
def guarded_transfer(text):
 text='let test_forbid_io=ref false\nlet test_write_budget=ref max_int\n'+text
 for anchor in ['let rec reallyWrite outfd buffer pos length =','let rec reallyWriteSubstring outfd buffer pos length =']:
  text=once(text,anchor,anchor+'\n  if !test_forbid_io || length> !test_write_budget then failwith "DESIGNATED transfer IO before validation";\n  test_write_budget:= !test_write_budget-length;')
 text=once(text,'  output outfd buffer pos length','  if pos<0 || length<0 || pos>Bytes.length buffer-length then failwith "DESIGNATED invalid copy buffer write";\n  output outfd buffer pos length')
 return text
def call(argv,cwd,expected=0):
 c=subprocess.run(argv,cwd=cwd,capture_output=True,text=True,timeout=30,env=dict(os.environ,UNISON=str(cwd/'state')))
 record['calls'].append(dict(argv=argv,cwd=str(cwd),exit_code=c.returncode,stdout=c.stdout,stderr=c.stderr));assert c.returncode==expected,(c.returncode,c.stdout,c.stderr)
 return c
try:
 participants=[('current',fields,transfer,None),
  ('integer-negative',once(fields,'  if i<0 || i>Bytearray.length int_buf-intSize then\n    raise(Util.Fatal "Protocol error: incomplete integer field");\n',''),transfer,'DESIGNATED integer read reached invalid range'),
  ('generic-negative',fields,once(transfer,'validate_instruction ~block_size:0 data pos len','(0,false)'),'DESIGNATED transfer IO before validation'),
  ('rsync-negative',fields,once(transfer,'validate_instruction ~block_size:blockSize data pos len','(0,false)'),'DESIGNATED transfer IO before validation'),
  ('short-read-negative',fields,once(transfer,'        if reallyRead infd decomprBuf 0 length<>length then\n          raise(Util.Transient "Rsync basis ended during block copy");','        ignore(reallyRead infd decomprBuf 0 length);'),'DESIGNATED transfer IO before validation'),
  ('buffer-short-read-negative',fields,once(transfer,'        if reallyRead infd decomprBuf 0 decomprBufSize<>decomprBufSize then\n          raise(Util.Transient "Rsync basis ended during block copy");','        ignore(reallyRead infd decomprBuf 0 decomprBufSize);'),'DESIGNATED transfer IO before validation'),
  ('else-group-negative',fields,once(once(transfer,'      end else begin\n        if reallyRead infd decomprBuf 0 length','      end else\n        if reallyRead infd decomprBuf 0 length'),'        reallyWrite outfd decomprBuf 0 length\n      end\n    in\n    let copyBlocks','        reallyWrite outfd decomprBuf 0 length\n    in\n    let copyBlocks'),'DESIGNATED invalid copy buffer write'),
  ('generic-output-negative',fields,once(transfer,'\n  reserve_output output_limit output_bytes eof;','\n  ignore(output_limit,output_bytes,eof);'),'DESIGNATED transfer IO before validation'),
  ('rsync-output-negative',fields,once(transfer,'\n    reserve_output output_limit output_bytes eof;','\n    ignore(output_limit,output_bytes,eof);'),'DESIGNATED output overrun reached copy callback'),
  ('basis-range-negative',fields,once(transfer,'      if offs>basis_length || Int64.of_int length>Int64.sub basis_length offs then\n        raise(Util.Transient "Rsync block range exceeds basis");','      ignore basis_length;'),'DESIGNATED invalid basis range reached copy callback')]
 for label,f,t,witness in participants:
  d=work/label;d.mkdir(mode=0o700)
  for name,text in [('remoteFieldsForTest.ml',guarded_fields(f)),('copyWireForTest.ml',wire),('transferForTest.ml',guarded_transfer(t)),('copyLimitForTest.ml',limit_source)]:(d/name).write_text(text)
  shutil.copyfile(Path(__file__).with_name('probe.ml'),d/'probe.ml')
  for name in ['remoteFieldsForTest.ml','copyWireForTest.ml','transferForTest.ml','copyLimitForTest.ml']:call([a.compiler,*flags,'-c',name],d)
  call([a.compiler,*flags,'unix.cmxa','str.cmxa',*[str(build/n)for n in modules],'remoteFieldsForTest.cmx','copyWireForTest.cmx','transferForTest.cmx','copyLimitForTest.cmx','probe.ml',*[str(build/n)for n in native],'-o','probe'],d)
  c=call([str(d/'probe')],d,expected=2 if witness else 0)
  if witness:
   assert witness in c.stderr,c.stdout+c.stderr
   record['negative_participants'][label]=dict(exit_code=c.returncode,witness=witness,source_sha256=sha(d/('remoteFieldsForTest.ml'if label=='integer-negative'else'transferForTest.ml')),binary_sha256=sha(d/'probe'))
  else:
   print(c.stdout,end='');record['positive']=dict(binary_sha256=sha(d/'probe'),stdout=c.stdout,controlled_fields_sha256=sha(d/'remoteFieldsForTest.ml'),controlled_transfer_sha256=sha(d/'transferForTest.ml'),copy_wire_sha256=sha(d/'copyWireForTest.ml'))
 record['state']='passed'
finally:
 with a.report.open('x')as f:json.dump(record,f,indent=2);f.write('\n')
