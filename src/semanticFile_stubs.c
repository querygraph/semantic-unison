/* Bounded positional writes into an already admitted, caller-owned private
 * output. Admission does not duplicate or own the FD. The caller keeps it live,
 * exclusively writable and free of concurrent status-flag changes until the
 * borrowed writer is retired. No pathname operation or OCaml callback occurs. */
#ifndef _WIN32
#ifndef _FILE_OFFSET_BITS
#define _FILE_OFFSET_BITS 64
#endif
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif
#endif

#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/fail.h>
#include <caml/threads.h>
#include <caml/signals.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>

#ifndef _WIN32
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>

enum { UNISON_SEMANTIC_WRITE_MAX = 65536 };

static int unison_semantic_fd(value descriptor, const char *phase)
{
  intnat number = Long_val(descriptor);
  if (number < 0 || number > INT_MAX)
    caml_unix_error(EBADF, phase, Nothing);
  return (int)number;
}
#endif

CAMLprim value unison_semantic_prepare_writer(value descriptor)
{
  CAMLparam1(descriptor);
#ifndef _WIN32
  caml_process_pending_actions();
  int fd = unison_semantic_fd(descriptor, "semantic writer descriptor");
  int error = 0;
  const char *phase = "semantic writer flags";
  struct stat stat;
  caml_enter_blocking_section_no_pending();
  int flags = fcntl(fd, F_GETFL);
  if (flags < 0) error = errno ? errno : EIO;
  else if ((flags & O_ACCMODE) != O_WRONLY &&
           (flags & O_ACCMODE) != O_RDWR) error = EBADF;
  else if (flags & O_APPEND) error = EINVAL;
  if (!error) {
    phase = "semantic writer identity";
    if (fstat(fd, &stat)) error = errno;
    else if (!S_ISREG(stat.st_mode) || stat.st_size < 0) error = EINVAL;
    else if (stat.st_nlink != 1) error = EBUSY;
  }
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, phase, Nothing);
  CAMLreturn(Val_true);
#else
  /* The Windows Unix descriptor has a different representation. Preserve the
   * existing ML seek/write backend without inspecting it as a POSIX integer. */
  CAMLreturn(Val_false);
#endif
}

CAMLprim value unison_semantic_pwrite(value descriptor, value data,
                                     value start, value length, value position)
{
  CAMLparam5(descriptor, data, start, length, position);
#ifndef _WIN32
  /* A raising pending handler runs before interpreting the borrow or copying
   * data. Entry below must not dispatch another handler while using the copy. */
  caml_process_pending_actions();
  intnat first = Long_val(start), count = Long_val(length);
  mlsize_t size = caml_string_length(data);
  if (first < 0 || count < 0 || count > UNISON_SEMANTIC_WRITE_MAX ||
      (uintnat)first > size || (uintnat)count > size - (uintnat)first)
    caml_invalid_argument("SemanticFile.write_at slice");
  int64_t offset = Int64_val(position);
  if (offset < 0 || offset > INT64_MAX - (int64_t)count)
    caml_invalid_argument("SemanticFile.write_at offset");
  off_t native_offset = (off_t)offset;
  off_t native_end = (off_t)(offset + (int64_t)count);
  if ((int64_t)native_offset != offset ||
      (int64_t)native_end != offset + (int64_t)count)
    caml_invalid_argument("SemanticFile.write_at offset");
  int fd = unison_semantic_fd(descriptor, "semantic pwrite descriptor");
  unsigned char buffer[UNISON_SEMANTIC_WRITE_MAX];
  if (count) memcpy(buffer, String_val(data) + first, (size_t)count);

  /* No pointer into the OCaml heap is used while released. One attempt only:
   * short writes/EINTR and cancellation belong to the ML materializer loop. */
  caml_enter_blocking_section_no_pending();
  ssize_t written = pwrite(fd, buffer, (size_t)count, native_offset);
  int error = written == -1 ? errno : 0;
  if (written < -1 || written > count || (written == -1 && !error))
    error = EIO;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "semantic pwrite", Nothing);
  CAMLreturn(Val_long(written));
#else
  caml_unix_error(ENOSYS, "semantic pwrite", Nothing);
#endif
}
