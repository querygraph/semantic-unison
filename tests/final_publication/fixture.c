/* Private test helpers; production publication and observations are unmodified. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <errno.h>
#include <time.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#if defined(__APPLE__)
#include <sys/attr.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/xattr.h>
#include <sys/stdio.h>
#include <stdint.h>
#include <stdio.h>
#include <signal.h>
#endif

#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#endif

CAMLprim value final_publication_fixture_open_parent(value path, value search)
{
  CAMLparam2(path, search);
  const size_t length = caml_string_length(path);
  char *copy;
  int fd, flags = O_RDONLY, error;
  if (memchr(String_val(path), '\0', length))
    caml_invalid_argument("fixture parent contains NUL");
  copy = malloc(length + 1);
  if (!copy) caml_raise_out_of_memory();
  memcpy(copy, String_val(path), length);
  copy[length] = '\0';
#if defined(O_SEARCH)
  if (Bool_val(search)) flags = O_SEARCH;
#else
  if (Bool_val(search)) {
    free(copy);
    caml_unix_error(ENOSYS, "fixture O_SEARCH", Nothing);
  }
#endif
#if defined(O_DIRECTORY)
  flags |= O_DIRECTORY;
#endif
#if defined(O_CLOEXEC)
  flags |= O_CLOEXEC;
#endif
  /* Keep this small test-only open under the runtime: no C-owned descriptor
     crosses a pending asynchronous-exception delivery point before adoption. */
  fd = open(copy, flags);
  error = errno;
  free(copy);
  if (fd == -1) caml_unix_error(error, "fixture open parent", path);
  if (fcntl(fd, F_SETFD, FD_CLOEXEC) == -1) {
    error = errno;
    close(fd);
    caml_unix_error(error, "fixture parent CLOEXEC", Nothing);
  }
  CAMLreturn(Val_int(fd));
}

CAMLprim value final_publication_fixture_fd_state(value fd)
{
  int flags = fcntl(Int_val(fd), F_GETFD);
  if (flags == -1) {
    if (errno == EBADF) return Val_int(-1);
    caml_unix_error(errno, "fixture fd state", Nothing);
  }
  return Val_int((flags & FD_CLOEXEC) ? 1 : 0);
}

CAMLprim value final_publication_fixture_fd_number(value fd)
{
  return Val_int(Int_val(fd));
}

#if defined(__APPLE__)
static int attribute_fault, attribute_trigger, attribute_calls, rename_fault;
static int stat_fault, filesystem_fault, postrename_failure, auxiliary_lookup_fault, unlink_fault;
static int duplicate_fault;
static int regular_signal_trigger, regular_stat_calls;

static int fixture_fstat(int fd, struct stat *output)
{
  if (postrename_failure) { errno = EIO; return -1; }
  int result = fstat(fd, output);
  if (result == -1) return result;
  if (S_ISDIR(output->st_mode)) {
    if (stat_fault == 1) output->st_ino ^= (ino_t)UINT64_C(0x10000000000);
    if (stat_fault == 2) output->st_dev ^= (dev_t)UINT32_C(0x80000000);
  } else if (S_ISREG(output->st_mode)) {
    regular_stat_calls++;
    if (regular_signal_trigger == regular_stat_calls && raise(SIGUSR1) != 0) abort();
    if (stat_fault == 3) output->st_ino ^= (ino_t)UINT64_C(0x10000000000);
    if (stat_fault == 4) output->st_dev ^= (dev_t)UINT32_C(0x80000000);
    if (stat_fault == 5) output->st_flags ^= UINT32_C(0x80000000);
    if (stat_fault == 6) output->st_mode ^= 0100;
    if (stat_fault == 7) output->st_uid ^= UINT32_C(0x80000000);
    if (stat_fault == 8) output->st_gid ^= UINT32_C(0x80000000);
    if (stat_fault == 9) output->st_mtimespec.tv_nsec ^= 1;
    if (stat_fault == 10) output->st_ctimespec.tv_nsec ^= 1;
    if (stat_fault == 11) output->st_size ^= INT64_C(0x10000000000);
    if (stat_fault == 12) output->st_nlink ^= UINT16_C(0x8000);
  }
  return result;
}

static int fixture_fstatfs(int fd, struct statfs *output)
{
  int result = fstatfs(fd, output);
  if (result == -1) return result;
  if (filesystem_fault == 1) output->f_fsid.val[0] ^= UINT32_C(0x80000000);
  if (filesystem_fault == 2) output->f_fsid.val[1] ^= UINT32_C(0x80000000);
  if (filesystem_fault == 3) output->f_flags ^= UINT32_C(0x80000000);
  return result;
}

static int fixture_getattrlist(int fd, struct attrlist *request, void *output,
                               size_t capacity, unsigned long options)
{
  int mode, result;
  uint32_t length;
  attribute_set_t returned;
  unsigned char *buffer = output;
  const size_t header = sizeof(length) + sizeof(returned);
  attribute_calls++;
  mode = attribute_trigger == 0 || attribute_trigger == attribute_calls
    ? attribute_fault : 0;
  if (mode == 6 || mode == 7 || mode == 12 || mode == 13 || mode == 14) {
    if (mode == 6) errno = EIO;
    else if (mode == 7) errno = EACCES;
    else if (mode == 12) errno = ENOTSUP;
    else if (mode == 13) errno = ENOSYS;
    else errno = EOPNOTSUPP;
    return -1;
  }
  result = fgetattrlist(fd, request, output, capacity, options);
  if (result == -1 || mode == 0) return result;
  if (request->bitmapcount != ATTR_BIT_MAP_COUNT ||
      request->commonattr != ATTR_CMN_RETURNED_ATTRS ||
      request->volattr != (ATTR_VOL_INFO | ATTR_VOL_UUID) ||
      request->dirattr || request->fileattr || request->forkattr ||
      !(options & FSOPT_REPORT_FULLSIZE) || capacity < header + 16) {
    errno = EINVAL;
    return -1;
  }
  memcpy(&length, buffer, sizeof(length));
  memcpy(&returned, buffer + sizeof(length), sizeof(returned));
  switch (mode) {
    case 1: /* Valid returned-mask reply without a UUID. */
      returned.volattr &= ~ATTR_VOL_UUID;
      length = (uint32_t)header;
      break;
    case 2: memset(buffer + header, 0, 16); break;
    case 3: length = (uint32_t)header - 1; break;
    case 4: length = (uint32_t)capacity + 1; break;
    case 5: returned.dirattr = ATTR_DIR_ENTRYCOUNT; break;
    case 8: returned.volattr |= ATTR_VOL_SIZE; break;
    case 9: buffer[header] ^= 1; break;
    case 11: buffer[header + 15] ^= 0x80; break;
    case 10: /* Real flag mutation during a native observation. */
    {
      struct stat before;
      if (fstat(fd, &before) == -1 || fchflags(fd, before.st_flags ^ UF_NODUMP) == -1)
        return -1;
      break;
    }
    default: errno = EINVAL; return -1;
  }
  memcpy(buffer, &length, sizeof(length));
  memcpy(buffer + sizeof(length), &returned, sizeof(returned));
  return 0;
}

static int fixture_rename(int from_parent, const char *from, int to_parent,
                          const char *to, unsigned int flags)
{
  if (rename_fault == 1) {errno = EIO; return -1;}
  if (rename_fault == 2) {
    const char race[] = "exclusive native race sentinel";
    int fd = openat(to_parent, to, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    int saved;
    ssize_t written;
    if (fd == -1) return -1;
    written = write(fd, race, sizeof(race) - 1);
    saved = errno;
    if (close(fd) == -1 && written == (ssize_t)(sizeof(race) - 1)) return -1;
    if (written != (ssize_t)(sizeof(race) - 1)) {
      errno = written < 0 ? saved : EIO;
      return -1;
    }
  }
  {
    int result = renameatx_np(from_parent, from, to_parent, to, flags);
    if (result == 0 && rename_fault == 3 && raise(SIGUSR1) != 0) abort();
    if (result == 0 && rename_fault == 4) postrename_failure = 1;
    return result;
  }
}

static int fixture_replace(int from_parent, const char *from, int to_parent, const char *to)
{
  if (rename_fault == 1) { errno = EIO; return -1; }
  int result = renameat(from_parent, from, to_parent, to);
  if (result == 0 && rename_fault == 3 && raise(SIGUSR1) != 0) abort();
  if (result == 0 && rename_fault == 4) postrename_failure = 1;
  return result;
}
static int fixture_lookup(int parent, const char *name, struct stat *output, int flags)
{
  if (auxiliary_lookup_fault && strncmp(name, "._", 2) == 0) {
    errno = auxiliary_lookup_fault == 1 ? EACCES : EIO;
    return -1;
  }
  return fstatat(parent, name, output, flags);
}
static int fixture_unlink(int parent, const char *name, int flags)
{
  if (unlink_fault) { errno = unlink_fault == 1 ? EPERM : EIO; return -1; }
  return unlinkat(parent, name, flags);
}
static int fixture_duplicate(int descriptor, int command, int argument)
{
  if (command == F_DUPFD_CLOEXEC && duplicate_fault == 1) { errno = EMFILE; return -1; }
  int result = fcntl(descriptor, command, argument);
  if (result >= 0 && command == F_DUPFD_CLOEXEC && duplicate_fault == 2 && raise(SIGUSR1) != 0) abort();
  return result;
}
#define fcntl fixture_duplicate
#define unlinkat fixture_unlink
#define fstatat fixture_lookup
/* Original deterministic diagnostic faults; production has no test switch. */
static int timing_clock_fault, timing_clock_calls, timing_allocation_fault;
static int fixture_clock_gettime(clockid_t clock, struct timespec *now)
{
  timing_clock_calls++;
  if (timing_clock_fault == 1) { errno = ERANGE; return -1; }
  if (timing_clock_fault == 2) {
    now->tv_sec = (timing_clock_calls & 1) ? 2 : 1;
    now->tv_nsec = 0;
    return 0;
  }
  return clock_gettime(clock, now);
}
static value fixture_copy_double(double number)
{
  if (timing_allocation_fault) caml_raise_out_of_memory();
  return caml_copy_double(number);
}
CAMLprim value final_publication_fixture_timing_fault(value clock, value allocation)
{
  timing_clock_fault = Int_val(clock); timing_clock_calls = 0;
  timing_allocation_fault = Bool_val(allocation);
  return Val_unit;
}
CAMLprim value final_publication_fixture_timing_calls(value unit)
{
  (void)unit;
  return Val_int(timing_clock_calls);
}
#define clock_gettime fixture_clock_gettime
#define caml_copy_double fixture_copy_double
#define renameat fixture_replace
#define fgetattrlist fixture_getattrlist
#define renameatx_np fixture_rename
#define fstat fixture_fstat
#define fstatfs fixture_fstatfs
#endif
#include "finalPublication_stubs.c"
#if defined(__APPLE__)
#undef fgetattrlist
#undef fcntl
#undef unlinkat
#undef fstatat
#undef clock_gettime
#undef caml_copy_double
#undef renameat
#undef renameatx_np
#undef fstat
#undef fstatfs
#endif

CAMLprim value final_publication_fixture_attribute_fault(value mode, value trigger)
{
#if defined(__APPLE__)
  attribute_fault = Int_val(mode);
  attribute_trigger = Int_val(trigger);
  attribute_calls = 0;
#else
  (void)mode; (void)trigger;
#endif
  return Val_unit;
}

CAMLprim value final_publication_fixture_rename_fault(value mode)
{
#if defined(__APPLE__)
  rename_fault = Int_val(mode);
  postrename_failure = 0;
#else
  (void)mode;
#endif
  return Val_unit;
}

CAMLprim value final_publication_fixture_auxiliary_fault(value mode)
{
#if defined(__APPLE__)
  auxiliary_lookup_fault = Int_val(mode);
#else
  (void)mode;
#endif
  return Val_unit;
}
CAMLprim value final_publication_fixture_unlink_fault(value mode)
{
#if defined(__APPLE__)
  unlink_fault = Int_val(mode);
#else
  (void)mode;
#endif
  return Val_unit;
}
CAMLprim value final_publication_fixture_duplicate_fault(value mode)
{
#if defined(__APPLE__)
  duplicate_fault = Int_val(mode);
#else
  (void)mode;
#endif
  return Val_unit;
}
CAMLprim value final_publication_fixture_regular_signal(value trigger)
{
#if defined(__APPLE__)
  regular_signal_trigger = Int_val(trigger);
  regular_stat_calls = 0;
#else
  (void)trigger;
#endif
  return Val_unit;
}
CAMLprim value final_publication_fixture_immutable(value path, value enable)
{
  CAMLparam2(path, enable);
#if defined(__APPLE__)
  if (chflags(String_val(path), Bool_val(enable) ? UF_IMMUTABLE : 0) == -1)
    caml_unix_error(errno, "fixture immutable flag", path);
#else
  caml_unix_error(ENOSYS, "fixture immutable flag", Nothing);
#endif
  CAMLreturn(Val_unit);
}

CAMLprim value final_publication_fixture_attribute_write(value path, value bytes, value resource)
{
  CAMLparam3(path, bytes, resource);
#if defined(__APPLE__)
  const char *name = Bool_val(resource) ? "com.apple.ResourceFork" : "org.unison.final-publication-test";
  if (setxattr(String_val(path), name, String_val(bytes), caml_string_length(bytes), 0, 0) == -1)
    caml_unix_error(errno, "fixture attribute write", path);
#else
  caml_unix_error(ENOSYS, "fixture attribute write", Nothing);
#endif
  CAMLreturn(Val_unit);
}
CAMLprim value final_publication_fixture_attribute_read(value path, value resource)
{
  CAMLparam2(path, resource);
#if defined(__APPLE__)
  char bytes[2048];
  const char *name = Bool_val(resource) ? "com.apple.ResourceFork" : "org.unison.final-publication-test";
  ssize_t size = getxattr(String_val(path), name, bytes, sizeof(bytes), 0, 0);
  if (size == -1) caml_unix_error(errno, "fixture attribute read", path);
  CAMLreturn(caml_alloc_initialized_string(size, bytes));
#else
  caml_unix_error(ENOSYS, "fixture attribute read", Nothing);
  CAMLreturn(Val_unit);
#endif
}

CAMLprim value final_publication_fixture_errno(value kind)
{
#if defined(__APPLE__)
  return Val_int(Int_val(kind) == 1 ? ENODATA : EPROTO);
#else
  (void)kind;
  return Val_int(0);
#endif
}

CAMLprim value final_publication_fixture_identity_fault(value kind, value mode)
{
#if defined(__APPLE__)
  if (Int_val(kind) == 1) stat_fault = Int_val(mode);
  else filesystem_fault = Int_val(mode);
#else
  (void)kind; (void)mode;
#endif
  return Val_unit;
}

CAMLprim value final_publication_fixture_dispatch_pending(value unit)
{
  CAMLparam1(unit);
  caml_process_pending_actions();
  CAMLreturn(Val_unit);
}

CAMLprim value final_publication_fixture_toggle_directory_flag(value fd)
{
#if defined(__APPLE__)
  struct stat before;
  if (fstat(Int_val(fd), &before) == -1 ||
      fchflags(Int_val(fd), before.st_flags ^ UF_NODUMP) == -1)
    caml_unix_error(errno, "fixture toggle directory flag", Nothing);
#else
  (void)fd;
  caml_unix_error(ENOSYS, "fixture toggle directory flag", Nothing);
#endif
  return Val_unit;
}

/* No OCaml allocation or pending-action boundary: a failing call's FD count
   is sampled in its exception handler before GC can run custom finalizers. */
CAMLprim value final_publication_fixture_fd_count(value unit)
{
  DIR *directory;
  struct dirent *entry;
  int count = 0, own;
  (void)unit;
  directory = opendir("/dev/fd");
  if (directory == NULL) return Val_int(-1);
  own = dirfd(directory);
  while ((entry = readdir(directory)) != NULL) {
    char *end;
    long descriptor = strtol(entry->d_name, &end, 10);
    if (end != entry->d_name && *end == '\0' && descriptor != own)
      count++;
  }
  if (closedir(directory) == -1) return Val_int(-1);
  return Val_int(count);
}
