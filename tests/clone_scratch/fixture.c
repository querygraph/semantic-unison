/* Private native fault fixture; no production API, environment seam or callback.
 * Wrappers execute solely C/POSIX work while the OCaml runtime is released. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/unixsupport.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/acl.h>
#include <sys/clonefile.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/xattr.h>
#include <unistd.h>

enum {
  NORMAL, REBIND, COLLISIONS, EXHAUST, RESERVE_REPLACED, RESERVE_REMOVED,
  RESERVE_EIO, RESERVE_ENOSPC, RESERVE_EACCES, RESERVE_EMFILE,
  RESERVE_STAT_ONCE, RESERVE_STAT_ALWAYS, REMOVE_ONCE, REMOVE_ALWAYS,
  BASIS_UNSUPPORTED, BASIS_EXDEV, BASIS_ENOSYS, BASIS_EIO,
  BASIS_OPEN_FAIL, BASIS_STAT_FAIL, BASIS_REPLACED, BASIS_REMOVED,
  OUTPUT_CLONE_FAIL, OUTPUT_OPEN_FAIL, OUTPUT_STAT_FAIL,
  OUTPUT_REPLACED, OUTPUT_REMOVED, MODE_FAIL, RECYCLED_CLOSE,
  OUTPUT_WRITE_FAIL, OUTPUT_REOPEN_FAIL, BASIS_REMOVE_ONCE,
  BASIS_REMOVE_ALWAYS, SOURCE_STAT_FAIL, SOURCE_NAME_FAIL,
  RESERVE_HARDLINK, BASIS_HARDLINK, OUTPUT_HARDLINK, SOURCE_REPLACED,
  RECYCLED_SOURCE_CLOSE, RECYCLED_READ_CLOSE, RECYCLED_PARENT_CLOSE,
  RESERVE_SYMLINK, RESERVE_DIRECTORY, BASIS_SYMLINK, BASIS_DIRECTORY,
  OUTPUT_SYMLINK, OUTPUT_DIRECTORY, RESERVE_MUTABLE, BASIS_MUTABLE,
  OUTPUT_MUTABLE, RESERVE_MISSING_BAD_WITNESS, BASIS_OPEN_REPLACED,
  OUTPUT_OPEN_REPLACED, LONG_LEAF, UNICODE_LEAF, RELATIVE_LEAF,
  RECYCLED_PARENT_WITH_PRIMARY, RECYCLED_SOURCE_WITH_DECLINE,
  RECYCLED_READ_WITH_PRIMARY, LONG_LEAF_254
};
static int mode, attempts, random_calls, clones, unlink_calls, statat_calls;
static int reserve_fd = -1, basis_fd = -1, read_fd = -1, input_fd = -1;
static int parent_fd = -1, reserve_stat_calls, basis_stat_calls, output_stat_calls;
static int source_stat_calls, source_name_calls, injected, recycled_fd = -1;
static int recycled_closes, basis_remove_calls;
static int reservation_wrong_parent, absolute_reservations;
static struct stat held_parent_stat, replacement_stat;
static char original[4096], moved[4096], source_path[4096];
static char scratch_name[256], output_name[256];

static void require(int yes) { if (!yes) abort(); }
static int scratch(const char *name) { return strstr(name, ".unison.tmp") != NULL; }
static void copy_name(char *destination, size_t size, const char *name)
{ require(strlen(name) < size); strcpy(destination, name); }
static void sentinel_at(int parent, const char *name)
{
  int fd = openat(parent, name, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
  static const char bytes[] = "foreign sentinel";
  require(fd >= 0 && write(fd, bytes, sizeof(bytes)-1) == sizeof(bytes)-1);
  require(close(fd) == 0);
}
static void replace_at(int parent, const char *name)
{
  require(renameat(parent, name, parent, "displaced-owned") == 0);
  sentinel_at(parent, name);
}
static void link_at(int parent, const char *name)
{ require(linkat(parent, name, parent, "owned-alias", 0) == 0); }
static void replace_kind_at(int parent, const char *name, int directory)
{
  require(renameat(parent, name, parent, "displaced-owned") == 0);
  if (directory) require(mkdirat(parent, name, 0700) == 0);
  else require(symlinkat("absent-target", parent, name) == 0);
}
static void mutate_owned(int fd)
{
  const struct timeval times[2] = {{1700000000,0},{1700000001,0}};
  require(fchmod(fd, 0440) == 0 && futimes(fd, times) == 0);
}

static int fixture_open(const char *path, int flags, ...)
{
  mode_t permissions = 0;
  if (flags & O_CREAT) { va_list args; va_start(args, flags); permissions = va_arg(args, int); va_end(args); }
  int fd = open(path, flags, permissions);
  if (fd >= 0 && (flags & O_DIRECTORY)) {
    parent_fd = fd;
    if (mode == REBIND) {
      require(rename(original, moved) == 0 && mkdir(original, 0700) == 0);
      int replacement = open(original, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
      require(replacement >= 0); sentinel_at(replacement, "parent-sentinel");
      require(fstat(replacement, &replacement_stat) == 0);
      require(close(replacement) == 0);
    }
    require(fstat(fd, &held_parent_stat) == 0);
  } else if (fd >= 0 && strcmp(path, source_path) == 0) input_fd = fd;
  return fd;
}

static void fixture_random(void *bytes, size_t size)
{
  ++random_calls;
  memset(bytes, 0, size);
  require(size == 16);
  ((unsigned char *)bytes)[15] = (unsigned char)random_calls;
}

static int fixture_openat(int parent, const char *name, int flags, ...)
{
  mode_t permissions = 0;
  if (flags & O_CREAT) { va_list args; va_start(args, flags); permissions = va_arg(args, int); va_end(args); }
  if ((flags & O_CREAT) && scratch(name)) {
    ++attempts; copy_name(scratch_name, sizeof(scratch_name), name);
    struct stat observed;
    require(fstat(parent, &observed) == 0);
    if (observed.st_dev != held_parent_stat.st_dev || observed.st_ino != held_parent_stat.st_ino) ++reservation_wrong_parent;
    if ((mode == COLLISIONS && attempts <= 3) || mode == EXHAUST) {
      if (mode == COLLISIONS && attempts == 2) require(symlinkat("absent-target", parent, name) == 0);
      else if (mode == COLLISIONS && attempts == 3) require(mkdirat(parent, name, 0700) == 0);
      else sentinel_at(parent, name);
    }
    if (mode >= RESERVE_EIO && mode <= RESERVE_EMFILE) {
      const int errors[] = {EIO, ENOSPC, EACCES, EMFILE}; errno = errors[mode - RESERVE_EIO]; return -1;
    }
    int fd = openat(parent, name, flags, permissions);
    if (fd >= 0) reserve_fd = fd;
    return fd;
  }
  if (scratch(name)) {
    copy_name(scratch_name, sizeof(scratch_name), name);
    if (mode == BASIS_OPEN_REPLACED) { replace_at(parent, name); errno = EIO; return -1; }
    if (mode == BASIS_OPEN_FAIL) { errno = EIO; return -1; }
    int fd = openat(parent, name, flags, permissions);
    if (fd >= 0) basis_fd = fd;
    return fd;
  }
  copy_name(output_name, sizeof(output_name), name);
  if ((flags & O_ACCMODE) == O_RDONLY) {
    if (mode == OUTPUT_OPEN_REPLACED) { replace_at(parent, name); errno = EIO; return -1; }
    if (mode == OUTPUT_OPEN_FAIL) { errno = EIO; return -1; }
    int fd = openat(parent, name, flags, permissions);
    if (fd >= 0) read_fd = fd;
    return fd;
  }
  if (mode == OUTPUT_WRITE_FAIL) { errno = EIO; return -1; }
  return openat(parent, name, flags, permissions);
}

/* Only the restored absolute-path private negative calls this wrapper. */
static int __attribute__((unused)) fixture_mkstemps(char *path, int suffix)
{
  ++absolute_reservations;
  int fd = mkstemps(path, suffix);
  if (fd >= 0) {
    reserve_fd = fd;
    char directory[4096]; copy_name(directory, sizeof(directory), path);
    char *slash = strrchr(directory, '/'); require(slash != NULL); *slash = '\0';
    int parent = open(directory, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    struct stat observed; require(parent >= 0 && fstat(parent, &observed) == 0 && close(parent) == 0);
    if (observed.st_dev != held_parent_stat.st_dev || observed.st_ino != held_parent_stat.st_ino) ++reservation_wrong_parent;
    copy_name(scratch_name, sizeof(scratch_name), strrchr(path, '/') + 1);
  }
  return fd;
}

static int fixture_fstat(int fd, struct stat *info)
{
  if (fd == reserve_fd && reserve_fd >= 0) {
    ++reserve_stat_calls;
    if (mode == RESERVE_MISSING_BAD_WITNESS && reserve_stat_calls > 1) { errno = EBADF; return -1; }
    if ((mode == RESERVE_STAT_ONCE && reserve_stat_calls == 1) || mode == RESERVE_STAT_ALWAYS) { errno = EIO; return -1; }
  } else if (fd == basis_fd && basis_fd >= 0) {
    ++basis_stat_calls;
    if (mode == BASIS_STAT_FAIL && basis_stat_calls == 1) { errno = EIO; return -1; }
  } else if (fd == read_fd && read_fd >= 0) {
    ++output_stat_calls;
    if (mode == OUTPUT_STAT_FAIL && output_stat_calls == 1) { errno = EIO; return -1; }
  } else if (fd == input_fd && input_fd >= 0) {
    ++source_stat_calls;
    if (mode == SOURCE_STAT_FAIL && source_stat_calls == 2) { errno = EIO; return -1; }
  }
  int result = fstat(fd, info);
  if (result == 0 && mode == OUTPUT_REOPEN_FAIL && fd != read_fd && fd != basis_fd &&
      fd != reserve_fd && fd != input_fd && fd != parent_fd) info->st_ino ^= 1;
  return result;
}

static int fixture_lstat(const char *name, struct stat *info)
{
  if (strcmp(name, source_path) == 0) {
    ++source_name_calls;
    if (mode == SOURCE_NAME_FAIL) { errno = EACCES; return -1; }
    if (mode == SOURCE_REPLACED && !injected) {
      injected = 1;
      char target[4096]; require(strlen(name) + sizeof("-displaced") < sizeof(target));
      snprintf(target, sizeof(target), "%s-displaced", name);
      require(rename(name, target) == 0);
      int fd = open(name, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
      const char text[] = "replacement source";
      require(fd >= 0 && write(fd, text, sizeof(text)-1) == sizeof(text)-1 && close(fd) == 0);
    }
  }
  return lstat(name, info);
}

static int fixture_fstatat(int parent, const char *name, struct stat *info, int flags)
{
  ++statat_calls;
  if (scratch(name) && !injected) {
    if (reserve_fd >= 0 && (mode == RESERVE_REPLACED || mode == RESERVE_REMOVED || mode == RESERVE_HARDLINK ||
                           mode == RESERVE_SYMLINK || mode == RESERVE_DIRECTORY ||
                           mode == RESERVE_MUTABLE || mode == RESERVE_MISSING_BAD_WITNESS)) {
      injected = 1;
      if (mode == RESERVE_REPLACED) replace_at(parent, name);
      else if (mode == RESERVE_REMOVED || mode == RESERVE_MISSING_BAD_WITNESS) require(unlinkat(parent, name, 0) == 0);
      else if (mode == RESERVE_HARDLINK) link_at(parent, name);
      else if (mode == RESERVE_MUTABLE) mutate_owned(reserve_fd);
      else replace_kind_at(parent, name, mode == RESERVE_DIRECTORY);
    } else if (basis_fd >= 0 && clones >= 2 && (mode == BASIS_REPLACED || mode == BASIS_REMOVED || mode == BASIS_HARDLINK ||
                                             mode == BASIS_SYMLINK || mode == BASIS_DIRECTORY || mode == BASIS_MUTABLE)) {
      injected = 1;
      if (mode == BASIS_REPLACED) replace_at(parent, name);
      else if (mode == BASIS_REMOVED) require(unlinkat(parent, name, 0) == 0);
      else if (mode == BASIS_HARDLINK) link_at(parent, name);
      else if (mode == BASIS_MUTABLE) mutate_owned(basis_fd);
      else replace_kind_at(parent, name, mode == BASIS_DIRECTORY);
    }
  }
  return fstatat(parent, name, info, flags);
}

static int fixture_unlinkat(int parent, const char *name, int flags)
{
  ++unlink_calls;
  if (scratch(name) && clones == 0 && (mode == REMOVE_ALWAYS || (mode == REMOVE_ONCE && unlink_calls == 1))) { errno = EACCES; return -1; }
  if (scratch(name) && clones >= 2) {
    ++basis_remove_calls;
    if (mode == BASIS_REMOVE_ALWAYS || (mode == BASIS_REMOVE_ONCE && basis_remove_calls == 1)) { errno = EIO; return -1; }
  }
  return unlinkat(parent, name, flags);
}

static int fixture_clone(int source, int parent, const char *name, int flags)
{
  ++clones;
  if (clones == 1 && mode >= BASIS_UNSUPPORTED && mode <= BASIS_EIO) {
    const int errors[] = {ENOTSUP, EXDEV, ENOSYS, EIO}; errno = errors[mode - BASIS_UNSUPPORTED]; return -1;
  }
  if (clones == 1 && mode == RECYCLED_SOURCE_WITH_DECLINE) { errno = ENOTSUP; return -1; }
  if (clones == 2 && mode == OUTPUT_CLONE_FAIL) { errno = EIO; return -1; }
  int result = fclonefileat(source, parent, name, flags);
  if (result == 0 && clones == 1) copy_name(scratch_name, sizeof(scratch_name), name);
  if (result == 0 && clones == 2) copy_name(output_name, sizeof(output_name), name);
  return result;
}

static int fixture_chmod(int fd, mode_t permissions)
{
  if (mode == OUTPUT_REPLACED || mode == OUTPUT_REMOVED || mode == OUTPUT_HARDLINK ||
      mode == OUTPUT_SYMLINK || mode == OUTPUT_DIRECTORY || mode == OUTPUT_MUTABLE) {
    if (!injected) {
      injected = 1;
      if (mode == OUTPUT_REPLACED) replace_at(parent_fd, output_name);
      else if (mode == OUTPUT_REMOVED) require(unlinkat(parent_fd, output_name, 0) == 0);
      else if (mode == OUTPUT_HARDLINK) link_at(parent_fd, output_name);
      else if (mode == OUTPUT_MUTABLE) mutate_owned(fd);
      else replace_kind_at(parent_fd, output_name, mode == OUTPUT_DIRECTORY);
    }
    errno = EACCES; return -1;
  }
  if (mode == MODE_FAIL || mode == RECYCLED_PARENT_WITH_PRIMARY || mode == RECYCLED_READ_WITH_PRIMARY) { errno = EACCES; return -1; }
  return fchmod(fd, permissions);
}

static int fixture_close(int fd)
{
  if (fd == recycled_fd && recycled_fd >= 0) ++recycled_closes;
  int was_reserve = fd == reserve_fd && reserve_fd >= 0;
  int recycle = (was_reserve && mode == RECYCLED_CLOSE) ||
    (fd == input_fd && input_fd >= 0 && (mode == RECYCLED_SOURCE_CLOSE || mode == RECYCLED_SOURCE_WITH_DECLINE)) ||
    (fd == read_fd && read_fd >= 0 && (mode == RECYCLED_READ_CLOSE || mode == RECYCLED_READ_WITH_PRIMARY)) ||
    (fd == parent_fd && parent_fd >= 0 && (mode == RECYCLED_PARENT_CLOSE || mode == RECYCLED_PARENT_WITH_PRIMARY));
  if (fd == reserve_fd) reserve_fd = -1;
  if (fd == basis_fd) basis_fd = -1;
  if (fd == read_fd) read_fd = -1;
  if (fd == input_fd) input_fd = -1;
  if (fd == parent_fd) parent_fd = -1;
  int result = close(fd);
  if (recycle) {
    require(result == 0);
    int temporary = open("/dev/null", O_RDONLY | O_CLOEXEC);
    require(temporary >= 0);
    if (temporary != fd) { require(dup2(temporary, fd) == fd && close(temporary) == 0); }
    recycled_fd = fd; errno = EIO; return -1;
  }
  return result;
}

#define open fixture_open
#define openat fixture_openat
#define arc4random_buf fixture_random
#define fstat fixture_fstat
#define lstat fixture_lstat
#define fstatat fixture_fstatat
#define unlinkat fixture_unlinkat
#define fclonefileat fixture_clone
#define fchmod fixture_chmod
#define close fixture_close
#define mkstemps fixture_mkstemps
#include "copy_stubs.c"
#undef open
#undef openat
#undef arc4random_buf
#undef fstat
#undef lstat
#undef fstatat
#undef unlinkat
#undef fclonefileat
#undef fchmod
#undef close
#undef mkstemps

CAMLprim value scratch_fixture_setup(value fault, value directory, value renamed, value source)
{
  CAMLparam4(fault, directory, renamed, source);
  mode = Int_val(fault);
  attempts = random_calls = clones = unlink_calls = statat_calls = 0;
  reserve_stat_calls = basis_stat_calls = output_stat_calls = source_stat_calls = source_name_calls = 0;
  reserve_fd = basis_fd = read_fd = input_fd = parent_fd = -1;
  injected = recycled_closes = basis_remove_calls = 0; recycled_fd = -1;
  reservation_wrong_parent = absolute_reservations = 0;
  scratch_name[0] = output_name[0] = '\0';
  copy_name(original, sizeof(original), String_val(directory));
  copy_name(moved, sizeof(moved), String_val(renamed));
  copy_name(source_path, sizeof(source_path), String_val(source));
  CAMLreturn(Val_unit);
}
CAMLprim value scratch_fixture_stats(value unit)
{
  CAMLparam1(unit); CAMLlocal1(result);
  const int values[] = {attempts, random_calls, clones, unlink_calls, statat_calls,
    reserve_stat_calls, basis_stat_calls, output_stat_calls, source_stat_calls,
    source_name_calls, injected, recycled_closes, basis_remove_calls,
    reservation_wrong_parent, absolute_reservations};
  result = caml_alloc_tuple(sizeof(values)/sizeof(values[0]));
  for (size_t i = 0; i < sizeof(values)/sizeof(values[0]); ++i) Store_field(result, i, Val_int(values[i]));
  CAMLreturn(result);
}
CAMLprim value scratch_fixture_name(value unit)
{ CAMLparam1(unit); CAMLreturn(caml_copy_string(scratch_name)); }
CAMLprim value scratch_fixture_recycled(value unit)
{
  CAMLparam1(unit);
  int valid = recycled_fd >= 0 && fcntl(recycled_fd, F_GETFD) >= 0;
  if (valid) require(close(recycled_fd) == 0);
  recycled_fd = -1;
  CAMLreturn(Val_bool(valid && recycled_closes == 0));
}
CAMLprim value scratch_fixture_fdcount(value unit)
{
  CAMLparam1(unit);
  DIR *directory = opendir("/dev/fd"); require(directory != NULL);
  int count = 0, own = dirfd(directory); struct dirent *entry;
  while ((entry = readdir(directory))) {
    char *end; long fd = strtol(entry->d_name, &end, 10);
    if (end != entry->d_name && !*end && fd != own) ++count;
  }
  require(closedir(directory) == 0);
  CAMLreturn(Val_int(count));
}
CAMLprim value scratch_fixture_flags(value descriptor)
{
  CAMLparam1(descriptor);
  int fd = Int_val(descriptor), flags = fcntl(fd, F_GETFL), exec = fcntl(fd, F_GETFD);
  if (flags < 0 || exec < 0) caml_unix_error(errno, "fixture_flags", Nothing);
  CAMLreturn(Val_int(((flags & O_ACCMODE) == O_RDWR ? 2 : (flags & O_ACCMODE) == O_RDONLY ? 0 : 1) | ((exec & FD_CLOEXEC) ? 4 : 0)));
}
CAMLprim value scratch_fixture_parent_unchanged(value unit)
{
  CAMLparam1(unit);
  struct stat observed;
  if (lstat(original, &observed)) caml_unix_error(errno, "fixture_parent_stat", Nothing);
  CAMLreturn(Val_bool(observed.st_dev == replacement_stat.st_dev &&
    observed.st_ino == replacement_stat.st_ino &&
    observed.st_mtimespec.tv_sec == replacement_stat.st_mtimespec.tv_sec &&
    observed.st_mtimespec.tv_nsec == replacement_stat.st_mtimespec.tv_nsec &&
    observed.st_ctimespec.tv_sec == replacement_stat.st_ctimespec.tv_sec &&
    observed.st_ctimespec.tv_nsec == replacement_stat.st_ctimespec.tv_nsec));
}
CAMLprim value scratch_fixture_filesystem(value path)
{
  CAMLparam1(path);
  struct statfs observed;
  if (statfs(String_val(path), &observed)) caml_unix_error(errno, "fixture_statfs", Nothing);
  CAMLreturn(caml_copy_string(observed.f_fstypename));
}
