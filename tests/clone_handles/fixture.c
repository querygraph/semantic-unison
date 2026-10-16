/* Private native fixture. There is no production test API or switch. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#ifdef __APPLE__
#include <sys/clonefile.h>
static int fixture_mode, clone_calls;
static char original_parent[PATH_MAX], moved_parent[PATH_MAX];

static int fixture_clone(int source, int parent, const char *name, int flags)
{
  int call = ++clone_calls;
  if (call == 1 && fixture_mode >= 1 && fixture_mode <= 4) {
    const int errors[] = {0, ENOTSUP, EXDEV, ENOSYS, EIO};
    errno = errors[fixture_mode];
    return -1;
  }
  if (call == 2 && fixture_mode == 5) { errno = EIO; return -1; }
  int result = fclonefileat(source, parent, name, flags);
  if (result == 0 && call == 2 && fixture_mode == 7) {
    /* Rebind the original absolute pathname while the native engine still
       holds its creation parent. All subsequent stage I/O must use that FD. */
    if (rename(original_parent, moved_parent) || mkdir(original_parent, 0700)) abort();
    int replacement = open(original_parent, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (replacement < 0) abort();
    int sentinel = openat(replacement, name, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    const char bytes[] = "replacement sentinel";
    if (sentinel < 0 || write(sentinel, bytes, sizeof(bytes) - 1) != sizeof(bytes) - 1) abort();
    if (close(sentinel) || close(replacement)) abort();
  }
  return result;
}

static int fixture_chmod(int fd, mode_t mode)
{
  if (fixture_mode == 6) { errno = EACCES; return -1; }
  return fchmod(fd, mode);
}
#define fclonefileat fixture_clone
#define fchmod fixture_chmod
#endif
#include "copy_stubs.c"
#ifdef __APPLE__
#undef fclonefileat
#undef fchmod
#endif

CAMLprim value handles_fixture_mode(value mode)
{
#ifdef __APPLE__
  fixture_mode = Int_val(mode);
  clone_calls = 0;
#else
  (void)mode;
#endif
  return Val_unit;
}

CAMLprim value handles_fixture_paths(value original, value moved)
{
  CAMLparam2(original, moved);
#ifdef __APPLE__
  mlsize_t n = caml_string_length(original), m = caml_string_length(moved);
  if (n >= sizeof(original_parent) || m >= sizeof(moved_parent) ||
      memchr(String_val(original), '\0', n) || memchr(String_val(moved), '\0', m))
    caml_unix_error(EINVAL, "fixture_paths", Nothing);
  memcpy(original_parent, String_val(original), n + 1);
  memcpy(moved_parent, String_val(moved), m + 1);
#endif
  CAMLreturn(Val_unit);
}

CAMLprim value handles_fixture_count(value unit)
{
  CAMLparam1(unit);
  DIR *directory = opendir("/dev/fd");
  int count = 0;
  if (!directory) caml_unix_error(errno, "fixture_count", Nothing);
  int own = dirfd(directory);
  struct dirent *entry;
  while ((entry = readdir(directory))) {
    char *end;
    long descriptor = strtol(entry->d_name, &end, 10);
    if (end != entry->d_name && *end == '\0' && descriptor != own) ++count;
  }
  closedir(directory);
  CAMLreturn(Val_int(count));
}

CAMLprim value handles_fixture_flags(value descriptor)
{
  CAMLparam1(descriptor);
  int flags = fcntl(Int_val(descriptor), F_GETFL);
  if (flags == -1) caml_unix_error(errno, "fixture_flags", Nothing);
  int close_exec = fcntl(Int_val(descriptor), F_GETFD);
  if (close_exec == -1) caml_unix_error(errno, "fixture_cloexec", Nothing);
  /* 0=readonly, 2=read/write, bit 4=CLOEXEC, independent of native constants. */
  CAMLreturn(Val_int(((flags & O_ACCMODE) == O_RDWR ? 2 :
                     (flags & O_ACCMODE) == O_RDONLY ? 0 : 1) |
                    ((close_exec & FD_CLOEXEC) ? 4 : 0)));
}

static int fixture_matches(int parent, const char *name, int stage)
{
  struct stat held, named;
  if (fstat(stage, &held)) return -1;
  if (fstatat(parent, name, &named, AT_SYMLINK_NOFOLLOW))
    return errno == ENOENT ? 0 : -1;
  return S_ISREG(named.st_mode) && held.st_dev == named.st_dev && held.st_ino == named.st_ino;
}

CAMLprim value handles_fixture_matches(value parent, value name, value stage)
{
  CAMLparam3(parent, name, stage);
  int result = fixture_matches(Int_val(parent), String_val(name), Int_val(stage));
  if (result < 0) caml_unix_error(errno, "fixture_matches", Nothing);
  CAMLreturn(Val_bool(result));
}

CAMLprim value handles_fixture_unlink(value parent, value name, value stage)
{
  CAMLparam3(parent, name, stage);
  int result = fixture_matches(Int_val(parent), String_val(name), Int_val(stage));
  if (result < 0) caml_unix_error(errno, "fixture_unlink_match", Nothing);
  if (result && unlinkat(Int_val(parent), String_val(name), 0))
    caml_unix_error(errno, "fixture_unlink", Nothing);
  CAMLreturn(Val_bool(result));
}

CAMLprim value handles_fixture_xattrs(value descriptor)
{
  CAMLparam1(descriptor);
#ifdef __APPLE__
  ssize_t result = flistxattr(Int_val(descriptor), NULL, 0, 0);
  if (result < 0) caml_unix_error(errno, "fixture_xattrs", Nothing);
  CAMLreturn(Val_long(result));
#else
  CAMLreturn(Val_int(0));
#endif
}

CAMLprim value handles_fixture_empty_acl(value descriptor)
{
  CAMLparam1(descriptor);
#ifdef __APPLE__
  acl_t acl = acl_get_fd_np(Int_val(descriptor), ACL_TYPE_EXTENDED);
  if (!acl && errno == ENOENT) CAMLreturn(Val_true); /* No extended ACL. */
  if (!acl) caml_unix_error(errno, "fixture_acl", Nothing);
  acl_entry_t entry;
  int result = acl_get_entry(acl, ACL_FIRST_ENTRY, &entry);
  int error = errno;
  acl_free(acl);
  /* For this valid ACL and valid selector, Darwin EINVAL means no entry. */
  if (result != 0 && error != EINVAL)
    caml_unix_error(error, "fixture_acl_entry", Nothing);
  CAMLreturn(Val_bool(result != 0));
#else
  CAMLreturn(Val_true);
#endif
}
