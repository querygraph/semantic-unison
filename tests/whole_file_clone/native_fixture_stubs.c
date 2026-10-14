/* Independent fixture I/O: all requests are synthetic own temporary objects.
 * pread/pwrite never advance caller cursors and do not claim block sharing. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/unixsupport.h>
#include <caml/signals.h>
#include <caml/fail.h>
#include <caml/callback.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <signal.h>
#include <fcntl.h>
#ifdef __APPLE__
#include <sys/mount.h>
#endif
#if defined(__APPLE__) || defined(__linux__)
#include <sys/xattr.h>
#endif
int whole_fixture_mode = 0;
CAMLprim value whole_fixture_native_mode(value mode)
{
  whole_fixture_mode=Int_val(mode);
  return Val_unit;
}

/* Queue a real OCaml signal without allocating or asking the runtime to
 * dispatch it. The next production blocking/pending boundary decides timing. */
CAMLprim value whole_fixture_queue_signal(value unit)
{
  if(kill(getpid(),SIGUSR1)) caml_uerror("fixture signal",Nothing);
  return Val_unit;
}
CAMLprim value whole_fixture_pending_dispatch(value unit)
{
  CAMLparam1(unit);
  caml_process_pending_actions();
  CAMLreturn(Val_unit);
}
CAMLprim value whole_fixture_fd_is_open(value descriptor)
{
  return Val_bool(fcntl(Int_val(descriptor),F_GETFD)!=-1);
}
extern value unison_whole_clone_close_slot(value,value);
extern value caml_unix_close(value);
void whole_fixture_raise_primary(void)
{
  const value *primary=caml_named_value("unison-whole-fixture-primary");
  if(!primary) caml_failwith("private primary exception registration missing");
  caml_raise(*primary);
}
/* No intervening ML return/poll exists between real signal queue and actual
 * production native close. Dispatch after close is a private observation seam.
 * The legacy control uses the actual linked Unix.close implementation. */
CAMLprim value whole_fixture_probe_close_slot(value descriptor,value owned)
{
  CAMLparam2(descriptor,owned);
  if(kill(getpid(),SIGUSR1)) caml_uerror("fixture close signal",Nothing);
  unison_whole_clone_close_slot(descriptor,owned);
  caml_process_pending_actions();
  whole_fixture_raise_primary();
  CAMLreturn(Val_unit);
}
CAMLprim value whole_fixture_legacy_probe_close_slot(value descriptor,value owned)
{
  CAMLparam2(descriptor,owned);
  if(Bool_val(Field(owned,0))) {
    Store_field(owned,0,Val_false);
    if(kill(getpid(),SIGUSR1)) caml_uerror("fixture legacy close signal",Nothing);
    caml_unix_close(Field(descriptor,0));
    caml_process_pending_actions();
    whole_fixture_raise_primary();
  }
  CAMLreturn(Val_unit);
}
CAMLprim value whole_fixture_nodump(value descriptor,value enabled)
{
  CAMLparam2(descriptor,enabled);
#ifdef __APPLE__
  if(fchflags(Int_val(descriptor),Bool_val(enabled)?UF_NODUMP:0))
    caml_uerror("fixture nodump",Nothing);
#else
  caml_unix_error(ENOSYS,"fixture nodump",Nothing);
#endif
  CAMLreturn(Val_unit);
}
CAMLprim value whole_fixture_filesystem_type(value path)
{
  CAMLparam1(path);
#ifdef __APPLE__
  struct statfs status;
  if(statfs(String_val(path),&status)) caml_uerror("fixture statfs",path);
  CAMLreturn(caml_copy_string(status.f_fstypename));
#else
  caml_unix_error(ENOSYS,"fixture statfs",path);
  CAMLreturn(Val_unit);
#endif
}

CAMLprim value whole_fixture_exact_copy(value source, value destination, value length)
{
  CAMLparam3(source, destination, length);
  int s=Int_val(source), d=Int_val(destination);
  off_t wanted=(off_t)Int64_val(length), offset=0;
  char data[4096];
  if (wanted<0) caml_unix_error(EINVAL,"fixture length",Nothing);
  while (offset<wanted) {
    size_t n=(size_t)(wanted-offset);
    if(n>sizeof(data)) n=sizeof(data);
    ssize_t got=pread(s,data,n,offset);
    if(got<0 && errno==EINTR) continue;
    if(got<=0) caml_unix_error(got<0?errno:EIO,"fixture pread",Nothing);
    ssize_t written=0;
    while(written<got) {
      ssize_t count=pwrite(d,data+written,(size_t)(got-written),offset+written);
      if(count<0 && errno==EINTR) continue;
      if(count<=0) caml_unix_error(count<0?errno:EIO,"fixture pwrite",Nothing);
      written+=count;
    }
    offset+=got;
  }
  if(ftruncate(d,wanted)) caml_uerror("fixture ftruncate",Nothing);
  CAMLreturn(Val_unit);
}

CAMLprim value whole_fixture_write_at(value destination, value offset, value bytes)
{
  CAMLparam3(destination,offset,bytes);
  size_t done=0, total=caml_string_length(bytes);
  off_t position=(off_t)Int64_val(offset);
  while(done<total) {
    ssize_t count=pwrite(Int_val(destination),String_val(bytes)+done,total-done,position+done);
    if(count<0 && errno==EINTR) continue;
    if(count<=0) caml_unix_error(count<0?errno:EIO,"fixture write-at",Nothing);
    done+=(size_t)count;
  }
  CAMLreturn(Val_unit);
}

CAMLprim value whole_fixture_set_xattr(value path,value name,value bytes)
{
  CAMLparam3(path,name,bytes);
  int result;
#if defined(__APPLE__)
  result=setxattr(String_val(path),String_val(name),String_val(bytes),caml_string_length(bytes),0,0);
#elif defined(__linux__)
  result=setxattr(String_val(path),String_val(name),String_val(bytes),caml_string_length(bytes),0);
#else
  errno=ENOSYS;result=-1;
#endif
  if(result) caml_uerror("fixture setxattr",path);
  CAMLreturn(Val_unit);
}

CAMLprim value whole_fixture_get_xattr(value path,value name)
{
  CAMLparam2(path,name);
  CAMLlocal1(result);
  char bytes[65536];
  ssize_t n;
#if defined(__APPLE__)
  n=getxattr(String_val(path),String_val(name),bytes,sizeof(bytes),0,0);
#elif defined(__linux__)
  n=getxattr(String_val(path),String_val(name),bytes,sizeof(bytes));
#else
  errno=ENOSYS;n=-1;
#endif
  if(n<0) caml_uerror("fixture getxattr",path);
  result=caml_alloc_string((mlsize_t)n);
  memcpy(Bytes_val(result),bytes,(size_t)n);
  CAMLreturn(result);
}
