/* Private test helpers; production publication and observations are unmodified. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#if defined(__APPLE__)
#include <sys/attr.h>
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/stdio.h>
#include <stdint.h>
#include <stdio.h>
#include <signal.h>
#endif

#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#endif

CAMLprim value stage_publication_fixture_open_parent(value path, value search)
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

CAMLprim value stage_publication_fixture_fd_state(value fd)
{
  int flags = fcntl(Int_val(fd), F_GETFD);
  if (flags == -1) {
    if (errno == EBADF) return Val_int(-1);
    caml_unix_error(errno, "fixture fd state", Nothing);
  }
  return Val_int((flags & FD_CLOEXEC) ? 1 : 0);
}

CAMLprim value stage_publication_fixture_fd_number(value fd)
{
  return Val_int(Int_val(fd));
}

#if defined(__APPLE__)
static int attribute_fault, attribute_trigger, attribute_calls, rename_fault;
static int stat_fault, filesystem_fault;

static int fixture_fstat(int fd, struct stat *output)
{
  int result = fstat(fd, output);
  if (result == -1) return result;
  if (S_ISDIR(output->st_mode)) {
    if (stat_fault == 1) output->st_ino ^= (ino_t)UINT64_C(0x10000000000);
    if (stat_fault == 2) output->st_dev ^= (dev_t)UINT32_C(0x80000000);
  } else if (S_ISREG(output->st_mode)) {
    if (stat_fault == 3) output->st_ino ^= (ino_t)UINT64_C(0x10000000000);
    if (stat_fault == 4) output->st_dev ^= (dev_t)UINT32_C(0x80000000);
    if (stat_fault == 5) output->st_flags ^= UINT32_C(0x80000000);
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
    return result;
  }
}

#define fgetattrlist fixture_getattrlist
#define renameatx_np fixture_rename
#define fstat fixture_fstat
#define fstatfs fixture_fstatfs
#endif
#include "stagePublication_stubs.c"
#if defined(__APPLE__)
#undef fgetattrlist
#undef renameatx_np
#undef fstat
#undef fstatfs
#endif

CAMLprim value stage_publication_fixture_attribute_fault(value mode, value trigger)
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

CAMLprim value stage_publication_fixture_rename_fault(value mode)
{
#if defined(__APPLE__)
  rename_fault = Int_val(mode);
#else
  (void)mode;
#endif
  return Val_unit;
}

CAMLprim value stage_publication_fixture_errno(value kind)
{
#if defined(__APPLE__)
  return Val_int(Int_val(kind) == 1 ? ENODATA : EPROTO);
#else
  (void)kind;
  return Val_int(0);
#endif
}

CAMLprim value stage_publication_fixture_identity_fault(value kind, value mode)
{
#if defined(__APPLE__)
  if (Int_val(kind) == 1) stat_fault = Int_val(mode);
  else filesystem_fault = Int_val(mode);
#else
  (void)kind; (void)mode;
#endif
  return Val_unit;
}

CAMLprim value stage_publication_fixture_dispatch_pending(value unit)
{
  CAMLparam1(unit);
  caml_process_pending_actions();
  CAMLreturn(Val_unit);
}

CAMLprim value stage_publication_fixture_toggle_directory_flag(value fd)
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
CAMLprim value stage_publication_fixture_fd_count(value unit)
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
