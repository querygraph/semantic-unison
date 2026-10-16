/* Private native fixture. No production hook and no OCaml callback while the
 * runtime is released. Every actual write receives a checked native copy. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/threads.h>
#include <caml/signals.h>
#include <caml/unixsupport.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

enum {
  REAL, SHORT, EINTR_ONCE, EINTR_TWICE, EIO_ALWAYS, SHORT_THEN_EIO,
  ZERO, OVERCOUNT, DUP_PERTURB, EINTR_ALWAYS, SHORT_THEN_ZERO,
  SHORT_THEN_OVERCOUNT, FLAGS_EIO, FLAGS_EINTR_ONCE, STAT_EIO,
  FLAGS_NO_ERRNO, PWRITE_NO_ERRNO, INVALID_NEGATIVE, SIGNAL_COPY,
  FLAGS_EINTR_ALWAYS, STAT_EINTR_ONCE
};
enum { MAX_CALLS = 10000 };
static int mode, calls, flags_calls, stat_calls, seek_calls, write_calls;
static int copies, release_calls, released_writes, bad_copy, signal_injected;
static int kernel_calls;
static int is_released, shared_dup = -1;
static const void *copied_destination;
static const void *copy_source;
static size_t copied_length;
struct attempt { int64_t offset, requested, returned, before, after, actual; int error; };
static struct attempt attempts[MAX_CALLS];

static void require(int yes) { if (!yes) abort(); }
static void *fixture_memcpy(void *destination, const void *source, size_t length)
{
  require(!is_released);
  ++copies;
  copied_destination = destination; copy_source = source; copied_length = length;
  void *result = memcpy(destination, source, length);
  if (mode == SIGNAL_COPY && !signal_injected) {
    signal_injected = 1; require(raise(SIGUSR1) == 0);
  }
  return result;
}
static void fixture_release(void)
{
  ++release_calls; is_released = 1;
  caml_enter_blocking_section_no_pending();
}
static void fixture_acquire(void)
{
  caml_acquire_runtime_system();
  is_released = 0;
}
static int fixture_fcntl(int fd, int command, ...)
{
  require(command == F_GETFL && is_released);
  ++flags_calls;
  if (mode == FLAGS_EIO) { errno = EIO; return -1; }
  if (mode == FLAGS_NO_ERRNO) { errno = 0; return -1; }
  if ((mode == FLAGS_EINTR_ONCE && flags_calls == 1) || mode == FLAGS_EINTR_ALWAYS) { errno = EINTR; return -1; }
  return fcntl(fd, command);
}
static int fixture_fstat(int fd, struct stat *stat)
{
  require(is_released); ++stat_calls;
  if (mode == STAT_EIO) { errno = EIO; return -1; }
  if (mode == STAT_EINTR_ONCE && stat_calls == 1) { errno = EINTR; return -1; }
  return fstat(fd, stat);
}
static ssize_t fixture_pwrite(int fd, const void *buffer, size_t length, off_t offset)
{
  require(is_released && calls < MAX_CALLS);
  ++calls; ++released_writes;
  struct attempt *a = &attempts[calls - 1];
  a->offset = offset; a->requested = length;
  if (mode == DUP_PERTURB) {
    require(shared_dup >= 0 && lseek(shared_dup, 101 + calls, SEEK_SET) == 101 + calls);
  }
  a->before = lseek(fd, 0, SEEK_CUR);
  if (length && (buffer != copied_destination || buffer == copy_source || length != copied_length)) {
    /* The pointer-only negative never dereferences a borrowed heap pointer. */
    ++bad_copy; a->returned = -1; a->error = EFAULT;
    a->after = lseek(fd, 0, SEEK_CUR); errno = EFAULT; return -1;
  }
  ssize_t result;
  if ((mode == EINTR_ONCE && calls == 1) || (mode == EINTR_TWICE && calls <= 2) || mode == EINTR_ALWAYS) { errno = EINTR; result = -1; }
  else if (mode == EIO_ALWAYS || (mode == SHORT_THEN_EIO && calls > 1)) { errno = EIO; result = -1; }
  else if (mode == ZERO || (mode == SHORT_THEN_ZERO && calls > 1)) result = 0;
  else if (mode == OVERCOUNT || (mode == SHORT_THEN_OVERCOUNT && calls > 1)) result = (ssize_t)length + 1;
  else if (mode == PWRITE_NO_ERRNO) { errno = 0; result = -1; }
  else if (mode == INVALID_NEGATIVE) { errno = 0; result = -2; }
  else {
    size_t count = length;
    if (mode == SHORT || ((mode == SHORT_THEN_EIO || mode == SHORT_THEN_ZERO || mode == SHORT_THEN_OVERCOUNT) && calls == 1))
      count = length < 997 ? length : 997;
    ++kernel_calls;
    result = pwrite(fd, buffer, count, offset);
    if (result > 0) a->actual = result;
  }
  int error = result < 0 ? errno : 0;
  a->returned = result; a->error = error; a->after = lseek(fd, 0, SEEK_CUR);
  errno = error; return result;
}
/* Only the seek/write source negative calls these production wrappers. */
static off_t __attribute__((unused)) fixture_lseek(int fd, off_t offset, int whence)
{ ++seek_calls; return lseek(fd, offset, whence); }
static ssize_t __attribute__((unused)) fixture_write(int fd, const void *data, size_t length)
{ ++write_calls; return write(fd, data, length); }

#undef memcpy
#define memcpy fixture_memcpy
#define fcntl fixture_fcntl
#define fstat fixture_fstat
#define pwrite fixture_pwrite
#define lseek fixture_lseek
#define write fixture_write
#define caml_enter_blocking_section_no_pending fixture_release
#undef caml_acquire_runtime_system
#define caml_acquire_runtime_system fixture_acquire
#include "semanticFile_stubs.c"
#undef memcpy
#undef fcntl
#undef fstat
#undef pwrite
#undef lseek
#undef write
#undef caml_enter_blocking_section_no_pending
#undef caml_acquire_runtime_system

CAMLprim value positional_fixture_setup(value fault)
{
  mode = Int_val(fault);
  calls = flags_calls = stat_calls = seek_calls = write_calls = 0;
  copies = release_calls = released_writes = bad_copy = signal_injected = kernel_calls = 0;
  is_released = 0; shared_dup = -1;
  copied_destination = copy_source = NULL; copied_length = 0;
  memset(attempts, 0, sizeof(attempts));
  return Val_unit;
}
CAMLprim value positional_fixture_dup(value descriptor)
{ shared_dup = Int_val(descriptor); return Val_unit; }
CAMLprim value positional_fixture_stats(value unit)
{
  CAMLparam1(unit); CAMLlocal1(result);
  const int values[] = {calls, flags_calls, stat_calls, seek_calls, write_calls,
    copies, release_calls, released_writes, bad_copy, signal_injected, kernel_calls};
  result = caml_alloc_tuple(sizeof(values)/sizeof(values[0]));
  for (size_t i = 0; i < sizeof(values)/sizeof(values[0]); ++i) Store_field(result, i, Val_int(values[i]));
  CAMLreturn(result);
}
CAMLprim value positional_fixture_attempt(value number)
{
  CAMLparam1(number); CAMLlocal2(result, scalar);
  int index = Int_val(number); require(index >= 0 && index < calls);
  const struct attempt *a = &attempts[index];
  const int64_t values[] = {a->offset,a->requested,a->returned,a->before,a->after,a->error,a->actual};
  result = caml_alloc_tuple(sizeof(values)/sizeof(values[0]));
  for (size_t i = 0; i < sizeof(values)/sizeof(values[0]); ++i) {
    scalar = caml_copy_int64(values[i]); Store_field(result, i, scalar);
  }
  CAMLreturn(result);
}
CAMLprim value positional_fixture_fdcount(value unit)
{
  CAMLparam1(unit);
  DIR *directory = opendir("/dev/fd"); require(directory != NULL);
  int count = 0, own = dirfd(directory); struct dirent *entry;
  while ((entry = readdir(directory))) {
    char *end; long fd = strtol(entry->d_name, &end, 10);
    if (end != entry->d_name && !*end && fd != own) ++count;
  }
  require(closedir(directory) == 0); CAMLreturn(Val_int(count));
}
CAMLprim value positional_fixture_dispatch(value unit)
{ CAMLparam1(unit); caml_process_pending_actions(); CAMLreturn(Val_unit); }
