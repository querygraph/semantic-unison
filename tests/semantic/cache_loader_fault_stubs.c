/* Original disposable-only wrapper. Production has no mode or fault switch. */
#define _DARWIN_C_SOURCE 1
#include <caml/mlvalues.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdatomic.h>
#include <errno.h>
#include <stdarg.h>
static _Atomic int failed_ordinal, closes, opens, reads, sync_calls;
CAMLprim value unison_cache_control_mode(value ordinal)
{
  atomic_store(&failed_ordinal, Int_val(ordinal));
  atomic_store(&closes, 0); atomic_store(&opens, 0); atomic_store(&reads, 0); atomic_store(&sync_calls, 0); return Val_unit;
}
CAMLprim value unison_cache_control_closes(value unit)
{ (void)unit; return Val_int(atomic_load(&closes)); }
CAMLprim value unison_cache_control_opens(value unit)
{ (void)unit; return Val_int(atomic_load(&opens)); }
int unison_cache_control_openat(int parent, const char *leaf, int flags, ...)
{
  int ordinal=atomic_fetch_add(&opens, 1)+1;
  if (atomic_load(&failed_ordinal)==200+ordinal) { errno=EIO; return -1; }
  if (flags & O_CREAT) {
    va_list args; va_start(args, flags); int mode=va_arg(args, int); va_end(args);
    return openat(parent, leaf, flags, mode);
  }
  return openat(parent, leaf, flags);
}
int unison_cache_control_close(int fd)
{
  int ordinal=atomic_fetch_add(&closes, 1)+1;
  int access=fcntl(fd, F_GETFL), ownership=fcntl(fd, F_GETFD);
  int valid=access!=-1 && ((access & O_ACCMODE)==O_RDONLY || (access & O_ACCMODE)==O_RDWR) &&
    (access & O_NONBLOCK) && ownership!=-1 && (ownership & FD_CLOEXEC);
  int result=close(fd), saved=errno;
  if (!valid && access!=-1) { errno=EINVAL; return -1; }
  if (ordinal==atomic_load(&failed_ordinal)) { errno=EIO; return -1; }
  errno=saved;return result;
}

ssize_t unison_cache_control_pread(int fd, void *bytes, size_t length, off_t offset)
{
  ssize_t result=pread(fd, bytes, length, offset);
  int saved=errno, ordinal=atomic_fetch_add(&reads, 1);
  /* Qualified disposable failure only: lose the descriptor after returned bytes
     so the final stat and first owner close fail. Never retry that stale number. */
  if (atomic_load(&failed_ordinal)==-1 && ordinal==0 && result>0) close(fd);
  errno=saved;return result;
}

CAMLprim value unison_cache_control_syncs(value unit)
{ (void)unit; return Val_int(atomic_load(&sync_calls)); }
int unison_cache_control_fsync(int fd)
{
  int ordinal=atomic_fetch_add(&sync_calls, 1);
  if (atomic_load(&failed_ordinal)==100+ordinal) { errno=EIO; return -1; }
  return fsync(fd);
}
