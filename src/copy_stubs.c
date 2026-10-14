/* Unison file synchronizer: src/copy_stubs.c */
/* Copyright 2021-2025, Tõivo Leedjärv

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifdef _WIN32

/* Minimum Windows API needed for getting the definition of
 * struct DUPLICATE_EXTENTS_DATA with MinGW headers under MSYS2.
 * As of 2025-11, MSYS2 by default targets Windows 7, which is
 * not sufficient in this case. */
#define WINVER 0x0603
#define _WIN32_WINNT 0x0603  /* Windows 8.1 */

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#endif /* _WIN32 */


#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/threads.h>
#include <caml/signals.h>
#include <caml/unixsupport.h>
#include <caml/version.h>

#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#define caml_uerror uerror
#define caml_win32_maperr win32_maperr
#endif


#include <errno.h>
#include <stdint.h>


/* ----------------------------------------------- */
/* Clone a file given source and destination paths */
/* It must fully complete or fully fail.

   The function must not raise any exceptions.

   Return true for success and false for failure
   or if the operation is not supported.           */

#if defined(__APPLE__)


#include <AvailabilityMacros.h>

#if defined(MAC_OS_X_VERSION_10_12)
#include <string.h>
#include <sys/attr.h>
#include <sys/clonefile.h>

CAMLprim value unison_clone_path(value src, value dst)
{
  CAMLparam2(src, dst);
  char *srcn, *dstn;
  int status;

  srcn = strdup(String_val(src));
  dstn = strdup(String_val(dst));
  caml_release_runtime_system();
  status = clonefile(srcn, dstn, CLONE_NOFOLLOW | CLONE_NOOWNERCOPY);
  free(srcn);
  free(dstn);
  caml_acquire_runtime_system();

  /* Don't raise an exception, just return false in case of errors */
  CAMLreturn(Val_bool(status == 0));
}
#else /* MAC_OS_X_VERSION_10_12 */
CAMLprim value unison_clone_path(value src, value dst)
{
  CAMLparam2(src, dst);
  CAMLreturn(Val_false);
}
#endif /* MAC_OS_X_VERSION_10_12 */


#else /* defined(__APPLE__) */


CAMLprim value unison_clone_path(value src, value dst)
{
  CAMLparam2(src, dst);
  CAMLreturn(Val_false);
}

/* Regarding Windows API: The CopyFile function in Windows API can do file
 * clones under right conditions. Nevertheless, we can't use that function
 * since it is not possible to explicitly request cloning (it is possible to
 * check whether block cloning is supported (see [unison_copy_file]) but it is
 * not a guarantee that the CopyFile function will actually result in a
 * cloning operation) and the function will fall back to a normal copy, which
 * we do not want in this case (even though performance-wise it would be more
 * like sendfile). */

#endif /* defined(__APPLE__) */


/* ----------------------------------------------- */
/* Clone a file given input and output fd          */
/* It must fully complete or fully fail.

   The function must not raise any exceptions.

   Return true for success and false for failure
   or if the operation is not supported.           */

#if defined(__linux__) || defined(__linux)


#include <sys/ioctl.h>

#if !defined(FICLONE) && defined(_IOW)
#define FICLONE _IOW(0x94, 9, int)
#endif

CAMLprim value unison_clone_file(value vin_fd, value vout_fd)
{
  CAMLparam2(vin_fd, vout_fd);
  int in_fd = Int_val(vin_fd);
  int out_fd = Int_val(vout_fd);

#ifdef FICLONE
  caml_release_runtime_system();
  int status = ioctl(out_fd, FICLONE, in_fd);
  caml_acquire_runtime_system();

  /* Don't raise an exception, just return false in case of errors */
  CAMLreturn(Val_bool(status == 0));
#else /* defined(FICLONE) */
  CAMLreturn(Val_false);
#endif
}


#else /* defined(__linux__) */


CAMLprim value unison_clone_file(value in_fd, value out_fd)
{
  CAMLparam2(in_fd, out_fd);
  CAMLreturn(Val_false);
}


#endif /* defined(__linux__) */


/* --------------------------------------------------------- */
/* Copy, or possibly clone, a file given input and output fd */
/* If operation is not supported by the OS or the filesystem
   then file offsets must not have been changed at failure.
   Output file offset must be changed on success.

   The function must return the number of bytes copied.

   On any error, raise a Unix exception based on errno.
   Raise ENOSYS if the operation is not supported.           */

#if defined(__linux__) || defined(__linux)


#include <unistd.h>
#include <sys/syscall.h>
#include <sys/sendfile.h>

CAMLprim value unison_copy_file(value vin_fd, value vout_fd, value vin_offs, value vlen)
{
  CAMLparam4(vin_fd, vout_fd, vin_offs, vlen);
  int in_fd = Int_val(vin_fd);
  int out_fd = Int_val(vout_fd);
  off_t off_i = Int64_val(vin_offs);
  size_t len = Long_val(vlen);
  ssize_t ret;

  caml_release_runtime_system();
#ifdef __NR_copy_file_range
  /* First, try copy_file_range() */
  /* Using off_i prevents changing in_fd file offset */
  ret = syscall(__NR_copy_file_range, in_fd, &off_i, out_fd, NULL, len, 0);
  if (ret == -1 && (errno == ENOSYS || errno == EBADF || errno == EXDEV))
#endif /* defined(__NR_copy_file_range) */
  {
    /* Second, try sendfile(); this one changes out_fd file offset */
    ret = sendfile(out_fd, in_fd, &off_i, len);
  }
  caml_acquire_runtime_system();
  if (ret == -1) caml_uerror("copy_file", Nothing);

  CAMLreturn(Val_long(ret));
}


#elif defined(__FreeBSD__)

#include <sys/param.h>
#include <sys/types.h>
#include <unistd.h>

CAMLprim value unison_copy_file(value vin_fd, value vout_fd, value vin_offs, value vlen)
{
  CAMLparam4(vin_fd, vout_fd, vin_offs, vlen);
#if __FreeBSD_version >= 1300037
  int in_fd = Int_val(vin_fd);
  int out_fd = Int_val(vout_fd);
  off_t off_i = Int64_val(vin_offs);
  size_t len = Long_val(vlen);
  ssize_t ret;

  caml_release_runtime_system();
  /* Using off_i prevents changing in_fd file offset */
  ret = copy_file_range(in_fd, &off_i, out_fd, NULL, len, 0);
  caml_acquire_runtime_system();
  if (ret == -1) caml_uerror("copy_file", Nothing);

  CAMLreturn(Val_long(ret));
#else /* __FreeBSD_version >= 1300037 */
  caml_unix_error(ENOSYS, "copy_file", Nothing);
  CAMLreturn(Val_long(0));
#endif /* __FreeBSD_version >= 1300037 */
}


#elif defined(__sun) || defined(sun)


#include <sys/sendfile.h>

CAMLprim value unison_copy_file(value vin_fd, value vout_fd, value vin_offs, value vlen)
{
  CAMLparam4(vin_fd, vout_fd, vin_offs, vlen);
  int in_fd = Int_val(vin_fd);
  int out_fd = Int_val(vout_fd);
  off_t off_orig;
  off_t off = off_orig = Int64_val(vin_offs);
  size_t len = Long_val(vlen);
  ssize_t ret;

  caml_release_runtime_system();
  /* This one changes out_fd file offset */
  ret = sendfile(out_fd, in_fd, &off, len);
  caml_acquire_runtime_system();
  if (ret == -1) {
    if (off > off_orig) {
      ret = off - off_orig;
    } else {
      caml_uerror("copy_file", Nothing);
    }
  }

  CAMLreturn(Val_long(ret));
}


#elif defined(_WIN32)


#include <windows.h>
#include <winioctl.h>

#if defined(__MINGW32__)

/* FIXME: As of January 2025, mingw has does not include type definitions for
 * FSCTL_GET_INTEGRITY_INFORMATION_BUFFER and DUPLICATE_EXTENTS_DATA (but does
 * include the definitions of FSCTL constants). If you get a compilation error
 * about "type redefinition" or similar, just remove the typedefs below. */

#ifndef FILE_SUPPORTS_BLOCK_REFCOUNTING
#define FILE_SUPPORTS_BLOCK_REFCOUNTING 0x08000000
#endif

#ifndef FSCTL_GET_INTEGRITY_INFORMATION
#define FSCTL_GET_INTEGRITY_INFORMATION 0x9027c
#endif

typedef struct _FSCTL_GET_INTEGRITY_INFORMATION_BUFFER {
  WORD  ChecksumAlgorithm;
  WORD  Reserved;
  DWORD Flags;
  DWORD ChecksumChunkSizeInBytes;
  DWORD ClusterSizeInBytes;
} FSCTL_GET_INTEGRITY_INFORMATION_BUFFER;

#ifndef FSCTL_DUPLICATE_EXTENTS_TO_FILE
#define FSCTL_DUPLICATE_EXTENTS_TO_FILE 0x98344
#endif

#if !defined(__MINGW64_VERSION_MAJOR) || __MINGW64_VERSION_MAJOR < 13

/* This typedef is included in mingw since version 13.0.0 */
typedef struct _DUPLICATE_EXTENTS_DATA {
  HANDLE        FileHandle;
  LARGE_INTEGER SourceFileOffset;
  LARGE_INTEGER TargetFileOffset;
  LARGE_INTEGER ByteCount;
} DUPLICATE_EXTENTS_DATA;

#endif /* __MINGW64_VERSION_MAJOR < 13 */

#endif /* defined(__MINGW32__) */

void unsn_copy_file_error(void)
{
  caml_win32_maperr(GetLastError());
  caml_uerror("copy_file", Nothing);
}

BOOL unsn_copy_file_supports_cloning(HANDLE h)
{
  DWORD flags = 0;
  return
    (GetVolumeInformationByHandleW(h, NULL, 0, NULL, NULL, &flags, NULL, 0)
      && (flags & FILE_SUPPORTS_BLOCK_REFCOUNTING));
 }

void unsn_copy_file_set_sparse(HANDLE h, BOOL sparse)
{
  FILE_SET_SPARSE_BUFFER sp;
  sp.SetSparse = sparse;
  if (!DeviceIoControl(h, FSCTL_SET_SPARSE, &sp, sizeof(sp),
        NULL, 0, NULL, NULL)) {
    unsn_copy_file_error();
  }
}

BOOL unsn_copy_file_get_sparse(HANDLE h)
{
  FILE_BASIC_INFO info;
  if (!GetFileInformationByHandleEx(h, FileBasicInfo, &info, sizeof(info))) {
    unsn_copy_file_error();
  }
  return (info.FileAttributes & FILE_ATTRIBUTE_SPARSE_FILE) != 0;
}

CAMLprim value unison_copy_file(value in_fd, value out_fd, value in_offs, value len)
{
  CAMLparam4(in_fd, out_fd, in_offs, len);

  HANDLE hin = Handle_val(in_fd);
  HANDLE hout = Handle_val(out_fd);

  if (!unsn_copy_file_supports_cloning(hout)
      || !unsn_copy_file_supports_cloning(hin)) {
    caml_unix_error(ENOSYS, "copy_file", Nothing);
  }

  /* INTEGRITY_INFORMATION contains information about fs cluster size. We make
   * the assumption that both the source and destination have the same cluster
   * size (From MSDN: The source and destination files must be on the same ReFS
   * volume.). */
  FSCTL_GET_INTEGRITY_INFORMATION_BUFFER intgrty;
  if (!DeviceIoControl(hin, FSCTL_GET_INTEGRITY_INFORMATION,
        NULL, 0, &intgrty, sizeof(intgrty), NULL, NULL)) {
    unsn_copy_file_error();
  }

  DUPLICATE_EXTENTS_DATA dupl;
  dupl.FileHandle = hin;
  dupl.SourceFileOffset.QuadPart = Int64_val(in_offs);
  if (!SetFilePointerEx(hout, (LARGE_INTEGER){0}, &dupl.TargetFileOffset,
        FILE_CURRENT)) {
    unsn_copy_file_error();
  }

  /* From MSDN: The source and destination regions must begin and end at
   * a cluster boundary. */
  if ((dupl.SourceFileOffset.QuadPart % intgrty.ClusterSizeInBytes != 0)
      || (dupl.TargetFileOffset.QuadPart % intgrty.ClusterSizeInBytes != 0)) {
    /* FSCTL_DUPLICATE_EXTENTS_TO_FILE would fail anyway if this didn't hold,
     * but this way we can bail out earlier. */
    caml_unix_error(EINVAL, "copy_file", Nothing);
  }
  dupl.ByteCount.QuadPart = Long_val(len) +
    intgrty.ClusterSizeInBytes - (Long_val(len) % intgrty.ClusterSizeInBytes);

  /* From MSDN: If the source file is sparse, the destination file must also be
   * sparse. */
  BOOL in_is_sparse = unsn_copy_file_get_sparse(hin);
  BOOL out_is_sparse = unsn_copy_file_get_sparse(hout);
  /* Based on the wording in MSDN, it is ok if the destination file is sparse
   * and the source is not, the opposite is not. */
  if (in_is_sparse && !out_is_sparse) {
    unsn_copy_file_set_sparse(hout, TRUE);
  }

  /* From MSDN: The destination region must not extend past the end of file. */
  LARGE_INTEGER newTargetLen;
  newTargetLen.QuadPart = dupl.TargetFileOffset.QuadPart + Long_val(len);
  FILE_STANDARD_INFO fi;
  if (!GetFileInformationByHandleEx(hout, FileStandardInfo, &fi, sizeof(fi))) {
    unsn_copy_file_error();
  }
  if (fi.EndOfFile.QuadPart < newTargetLen.QuadPart) {
    /* We want to avoid allocating on disk when extending the file. Make the
     * destination file temporarily sparse, if it's not already. */
    if (!out_is_sparse && !in_is_sparse) {
      unsn_copy_file_set_sparse(hout, TRUE);
    }
    FILE_END_OF_FILE_INFO eofi;
    eofi.EndOfFile = newTargetLen;
    if (!SetFileInformationByHandle(hout, FileEndOfFileInfo, &eofi, sizeof(eofi))) {
      unsn_copy_file_error();
    }
    /* The destination file was set to sparse when extending it; revert the
     * sparse status. */
    if (!out_is_sparse && !in_is_sparse) {
      unsn_copy_file_set_sparse(hout, FALSE);
    }
  }

  caml_release_runtime_system();
  BOOL res = DeviceIoControl(hout, FSCTL_DUPLICATE_EXTENTS_TO_FILE,
                             &dupl, sizeof(dupl), NULL, 0, NULL, NULL);
  caml_acquire_runtime_system();
  if (!res) {
    unsn_copy_file_error();
  } else {
    /* FSCTL_DUPLICATE_EXTENTS_TO_FILE does not advance the destination file
     * offset. */
    LARGE_INTEGER copied;
    copied.QuadPart = Long_val(len);
    if (!SetFilePointerEx(hout, copied, NULL, FILE_CURRENT)) {
      unsn_copy_file_error();
    }
  }

  CAMLreturn(len);
}

#else /* defined(__linux__) || defined(__FreeBSD__) || defined(__sun) || defined(_WIN32) */


CAMLprim value unison_copy_file(value in_fd, value out_fd, value in_offs, value len)
{
  CAMLparam4(in_fd, out_fd, in_offs, len);
  caml_unix_error(ENOSYS, "copy_file", Nothing);
  CAMLreturn(Val_long(0));
}


#endif /* defined(__linux__) || defined(__FreeBSD__) || defined (__sun) || defined(_WIN32) */

/* Receiver-local, data-only cloned staging. Keep the basis separate from the
 * evolving output, so shifted rsync references never read overwritten bytes.
 * The private basis is unlinked before returning and lives only through its fd.
 * Unlike clone_path, operational errors are not silently treated as unsupported.
 */
#if defined(__APPLE__) && defined(MAC_OS_X_VERSION_10_12)
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <sys/acl.h>
#include <unistd.h>

static int unsn_same_basis(const struct stat *a, const struct stat *b)
{
  return a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_size == b->st_size &&
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
    a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec;
}

/* Keep these immediate constructors in sync with Fs.clone_stage_decline. */
enum unsn_stage_decline {
  UNSN_STAGE_PLATFORM = 0, UNSN_STAGE_NONREGULAR, UNSN_STAGE_FLAGS,
  UNSN_STAGE_CROSS_DEVICE, UNSN_STAGE_UNSUPPORTED
};

enum {
  UNSN_STAGE_RANDOM_BYTES = 16,
  UNSN_STAGE_RESERVATION_ATTEMPTS = 128,
  UNSN_STAGE_SCRATCH_SIZE = sizeof(".unison.basis-") - 1 +
    2 * UNSN_STAGE_RANDOM_BYTES + sizeof(".unison.tmp")
};

/* A held descriptor is the cleanup witness. Missing cleanup names are harmless;
 * descriptor failures and different current objects are never hidden. This is
 * a cooperative namespace fence, not an atomic compare-and-unlink primitive. */
static int unsn_stage_match_owned(int parent, const char *name, int witness,
                                int missing_ok, int single_link)
{
  struct stat before, named, after;
  if (fstat(witness, &before)) return -1;
  if (!S_ISREG(before.st_mode) || (single_link && before.st_nlink != 1)) {
    errno = EBUSY; return -1;
  }
  if (fstatat(parent, name, &named, AT_SYMLINK_NOFOLLOW)) {
    if (missing_ok && errno == ENOENT) return 1;
    return -1;
  }
  if (fstat(witness, &after)) return -1;
  if (!S_ISREG(named.st_mode) || !S_ISREG(after.st_mode) ||
      before.st_dev != after.st_dev || before.st_ino != after.st_ino ||
      named.st_dev != before.st_dev || named.st_ino != before.st_ino ||
      (single_link && (named.st_nlink != 1 || after.st_nlink != 1))) {
    errno = EBUSY; return -1;
  }
  return 0;
}

static int unsn_stage_remove_owned(int parent, const char *name, int witness,
                                 int missing_ok)
{
  int matched = unsn_stage_match_owned(parent, name, witness, missing_ok, 0);
  if (matched < 0) return -1;
  if (matched > 0) return 0;
  if (unlinkat(parent, name, 0)) {
    if (missing_ok && errno == ENOENT) return 0;
    return -1;
  }
  return 0;
}

/* Clear before one close attempt. A failed close must never authorize retrying
 * a number that another operation may have reused. Return the native errno. */
static int unsn_stage_close(int *slot)
{
  int fd = *slot;
  *slot = -1;
  if (fd >= 0 && close(fd)) return errno;
  return 0;
}

static int unsn_stage_reserve(int parent, char *name)
{
  static const char prefix[] = ".unison.basis-", suffix[] = ".unison.tmp";
  static const char hex[] = "0123456789abcdef";
  unsigned char random[UNSN_STAGE_RANDOM_BYTES];
  for (int attempt = 0; attempt < UNSN_STAGE_RESERVATION_ATTEMPTS; attempt++) {
    arc4random_buf(random, sizeof(random));
    memcpy(name, prefix, sizeof(prefix) - 1);
    for (int i = 0; i < UNSN_STAGE_RANDOM_BYTES; i++) {
      name[sizeof(prefix) - 1 + 2 * i] = hex[random[i] >> 4];
      name[sizeof(prefix) + 2 * i] = hex[random[i] & 15];
    }
    memcpy(name + sizeof(prefix) - 1 + 2 * UNSN_STAGE_RANDOM_BYTES,
           suffix, sizeof(suffix));
    int fd = openat(parent, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW |
                    O_CLOEXEC | O_NONBLOCK, 0600);
    if (fd >= 0) return fd;
    if (errno != EEXIST) return -1;
  }
  errno = EEXIST; return -1;
}

static value unsn_clone_stage_impl(value source, value destination, int strict,
                                  int keep_parent, int sized, int64_t expected)
{
  CAMLparam2(source, destination);
  CAMLlocal3(pair, result, declined);
  /* The additive sized API admits the captured source EOF before creating
   * either stage. Existing unsized/boolean APIs keep their original contract. */
  if (sized && (expected < 0 || (int64_t)(off_t)expected != expected))
    caml_unix_error(expected < 0 ? EINVAL : EOVERFLOW,
                    "clone_stage: expected length", destination);
  if (__builtin_available(macOS 10.12, *)) {} else {
    if (!strict) CAMLreturn(Val_int(0));
    declined = caml_alloc(1, 1);
    Store_field(declined, 0, Val_int(UNSN_STAGE_PLATFORM));
    CAMLreturn(declined);
  }
  /* Allocate every result block before acquiring native resources. An OCaml
   * allocation failure must not abandon a stage or descriptors on success. */
  pair = caml_alloc_tuple(keep_parent ? 3 : 2);
  Store_field(pair, 0, Val_int(-1)); Store_field(pair, 1, Val_int(-1));
  if (keep_parent) Store_field(pair, 2, Val_int(-1));
  result = caml_alloc(1, 0); Store_field(result, 0, pair);
  if (strict) {
    declined = caml_alloc(1, 1);
    Store_field(declined, 0, Val_int(UNSN_STAGE_PLATFORM));
  }
  /* Pending handlers may raise. Dispatch before owning native resources,
   * then defer newly arriving handlers until the blocking section is over. */
  caml_process_pending_actions();
  char *src = strdup(String_val(source)), *dst = strdup(String_val(destination));
  char *scratch = NULL, *attrs = NULL;
  int input = -1, basis = -1, output = -1, parent = -1, reserve = -1, stage_read = -1;
  int error = 0, unsupported = 0, decline_reason = UNSN_STAGE_UNSUPPORTED;
  int reservation_owned = 0, basis_owned = 0, output_owned = 0, output_admitted = 0;
  const char *phase = "clone_stage: path allocation";
  struct stat before, after, named, basis_identity, stage_identity, output_identity;
  acl_t acl = NULL;
  if (src == NULL || dst == NULL) { error = ENOMEM; goto done; }
  char *slash = strrchr(dst, '/');
  const char *name = slash ? slash + 1 : dst;
  phase = "clone_stage: destination name";
  if (*name == '\0') { error = EINVAL; goto done; }
  phase = "clone_stage: scratch allocation";
  scratch = malloc(UNSN_STAGE_SCRATCH_SIZE);
  if (!scratch) { error = ENOMEM; goto done; }

  caml_enter_blocking_section_no_pending();
  /* A replaced FIFO must not block before the regular-file check. O_NONBLOCK
   * has no data-I/O effect on the regular files accepted by this operation. */
  phase = "clone_stage: source open";
  input = open(src, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
  if (input < 0) { error = errno; goto unlocked_done; }
  phase = "clone_stage: source stat";
  if (fstat(input, &before)) { error = errno; goto unlocked_done; }
  /* Compressed data relies on platform xattrs. Flagged files may also make
   * private clones undeletable. Keep the ordinary copy path for these cases. */
  if (!S_ISREG(before.st_mode)) {
    decline_reason = UNSN_STAGE_NONREGULAR;
    unsupported = 1; goto unlocked_done;
  }
  if (sized && before.st_size != (off_t)expected) {
    error = EBUSY; phase = "clone_stage: expected source EOF";
    goto unlocked_done;
  }
  if (before.st_flags != 0) {
    decline_reason = UNSN_STAGE_FLAGS;
    unsupported = 1; goto unlocked_done;
  }
  if (slash) *slash = '\0';
  phase = "clone_stage: destination parent";
  parent = open(slash ? (*dst ? dst : "/") : ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  if (slash) *slash = '/';
  if (parent < 0) { error = errno; goto unlocked_done; }
  phase = "clone_stage: basis reservation";
  reserve = unsn_stage_reserve(parent, scratch);
  if (reserve < 0) { error = errno; goto unlocked_done; }
  reservation_owned = 1;
  phase = "clone_stage: reservation removal";
  if (unsn_stage_remove_owned(parent, scratch, reserve, 0)) {
    error = errno; goto unlocked_done;
  }
  reservation_owned = 0;
  phase = "clone_stage: reservation close";
  error = unsn_stage_close(&reserve);
  if (error) goto unlocked_done;
  phase = "clone_stage: basis clone";
  if (fclonefileat(input, parent, scratch, CLONE_NOOWNERCOPY)) {
    error = errno;
    if (error == ENOTSUP || error == EXDEV || error == ENOSYS) {
      decline_reason = error == EXDEV ? UNSN_STAGE_CROSS_DEVICE :
        error == ENOSYS ? UNSN_STAGE_PLATFORM : UNSN_STAGE_UNSUPPORTED;
      unsupported = 1; error = 0;
    }
    goto unlocked_done;
  }
  phase = "clone_stage: basis open";
  basis = openat(parent, scratch, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
  if (basis < 0) { error = errno; goto unlocked_done; }
  phase = "clone_stage: basis identity";
  if (fstat(basis, &basis_identity)) { error = errno; goto unlocked_done; }
  if (!S_ISREG(basis_identity.st_mode) || basis_identity.st_nlink != 1 ||
      basis_identity.st_dev != before.st_dev || basis_identity.st_ino == before.st_ino) {
    error = EBUSY; goto unlocked_done;
  }
  if (unsn_stage_match_owned(parent, scratch, basis, 0, 1)) {
    error = errno; goto unlocked_done;
  }
  basis_owned = 1;
  if (sized && basis_identity.st_size != (off_t)expected) {
    error = EBUSY; phase = "clone_stage: expected basis EOF";
    goto unlocked_done;
  }
  phase = "clone_stage: source stability";
  if (fstat(input, &after) || lstat(src, &named)) {
    error = errno; goto unlocked_done;
  }
  if (!unsn_same_basis(&before, &after) || !unsn_same_basis(&before, &named)) {
    error = EBUSY; goto unlocked_done;
  }
  phase = "clone_stage: output clone";
  if (fclonefileat(basis, parent, name, CLONE_NOOWNERCOPY)) {
    error = errno; goto unlocked_done;
  }
  /* Change permissions only on the inode we actually opened. A pathname
   * chmod could follow a replaced staging name to a live unrelated file. */
  phase = "clone_stage: output read open";
  stage_read = openat(parent, name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
  if (stage_read < 0) { error = errno; goto unlocked_done; }
  phase = "clone_stage: output identity";
  if (fstat(stage_read, &stage_identity)) { error = errno; goto unlocked_done; }
  if (!S_ISREG(stage_identity.st_mode) || stage_identity.st_nlink != 1 ||
      stage_identity.st_dev != basis_identity.st_dev ||
      stage_identity.st_ino == basis_identity.st_ino ||
      stage_identity.st_ino == before.st_ino) {
    error = EBUSY; goto unlocked_done;
  }
  if (unsn_stage_match_owned(parent, name, stage_read, 0, 1)) {
    error = errno; goto unlocked_done;
  }
  output_owned = 1;
  phase = "clone_stage: ACL allocation";
  acl = acl_init(0);
  if (!acl) { error = errno; goto unlocked_done; }
  phase = "clone_stage: ACL clearing";
  if (acl_set_fd_np(stage_read, acl, ACL_TYPE_EXTENDED)) { error = errno; goto unlocked_done; }
  phase = "clone_stage: writable mode";
  if (fchmod(stage_read, 0600)) { error = errno; goto unlocked_done; }
  phase = "clone_stage: output write open";
  output = openat(parent, name, O_RDWR | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
  if (output < 0) { error = errno; goto unlocked_done; }
  phase = "clone_stage: output reopen identity";
  if (fstat(output, &output_identity)) { error = errno; goto unlocked_done; }
  if (stage_identity.st_dev != output_identity.st_dev ||
      stage_identity.st_ino != output_identity.st_ino || output_identity.st_nlink != 1) {
    error = EBUSY; goto unlocked_done;
  }
  if (sized && output_identity.st_size != (off_t)expected) {
    error = EBUSY; phase = "clone_stage: expected output EOF";
    goto unlocked_done;
  }
  if (unsn_stage_match_owned(parent, name, output, 0, 1)) {
    error = errno; goto unlocked_done;
  }
  output_admitted = 1;
  phase = "clone_stage: output read close";
  error = unsn_stage_close(&stage_read);
  if (error) goto unlocked_done;
  /* Match a fresh data-fork temporary file: old resource forks, Finder info,
   * arbitrary xattrs and inherited ACLs must not leak into the result when
   * their synchronization preferences are disabled or the source lacks them. */
  phase = "clone_stage: attribute listing";
  ssize_t count = flistxattr(output, NULL, 0, 0);
  if (count < 0) { error = errno; goto unlocked_done; }
  if (count > 0) {
    phase = "clone_stage: attribute allocation";
    attrs = malloc((size_t)count);
    if (!attrs) { error = ENOMEM; goto unlocked_done; }
    phase = "clone_stage: attribute read";
    ssize_t actual = flistxattr(output, attrs, (size_t)count, 0);
    if (actual < 0) { error = errno; goto unlocked_done; }
    phase = "clone_stage: attribute clearing";
    for (ssize_t pos = 0; pos < actual; pos += strlen(attrs + pos) + 1)
      if (fremovexattr(output, attrs + pos, 0)) { error = errno; goto unlocked_done; }
  }
  if (sized) {
    struct stat source_final, source_named, basis_final, output_final;
    phase = "clone_stage: final source EOF/stability";
    if (fstat(input, &source_final) || lstat(src, &source_named)) {
      error = errno; goto unlocked_done;
    }
    if (!unsn_same_basis(&before, &source_final) ||
        !unsn_same_basis(&before, &source_named) ||
        source_final.st_size != (off_t)expected) {
      error = EBUSY; goto unlocked_done;
    }
    phase = "clone_stage: final basis EOF/stability";
    if (fstat(basis, &basis_final)) { error = errno; goto unlocked_done; }
    if (!unsn_same_basis(&basis_identity, &basis_final) ||
        basis_final.st_size != (off_t)expected) {
      error = EBUSY; goto unlocked_done;
    }
    phase = "clone_stage: final output EOF/identity";
    if (fstat(output, &output_final)) { error = errno; goto unlocked_done; }
    if (!S_ISREG(output_final.st_mode) || output_final.st_nlink != 1 ||
        output_final.st_dev != output_identity.st_dev ||
        output_final.st_ino != output_identity.st_ino ||
        output_final.st_size != (off_t)expected) {
      error = EBUSY; goto unlocked_done;
    }
    if (unsn_stage_match_owned(parent, name, output, 0, 1)) {
      error = errno; goto unlocked_done;
    }
  }
  phase = "clone_stage: basis unlink";
  if (unsn_stage_remove_owned(parent, scratch, basis, 0)) {
    error = errno; goto unlocked_done;
  }
  basis_owned = 0;

unlocked_done:
  /* Settle non-witness resources first, then remove only admitted names before
   * closing their witnesses. Pure declines cannot hide cleanup failures. */
  {
    int close_error = unsn_stage_close(&input);
    if (close_error && !error) {
      error = close_error; phase = "clone_stage: source close";
    }
  }
  if (acl) {
    if (acl_free(acl) && !error) {
      error = errno; phase = "clone_stage: ACL cleanup";
    }
    acl = NULL;
  }
  if (error || unsupported) {
    if (output_owned) {
      int witness = output_admitted ? output : stage_read;
      if (unsn_stage_remove_owned(parent, name, witness, 1)) {
        if (!error) { error = errno; phase = "clone_stage: output cleanup"; }
      } else output_owned = 0;
    }
  }
  if (reservation_owned) {
    if (unsn_stage_remove_owned(parent, scratch, reserve, 1)) {
      if (!error) { error = errno; phase = "clone_stage: reservation cleanup"; }
    } else reservation_owned = 0;
  }
  if (basis_owned) {
    if (unsn_stage_remove_owned(parent, scratch, basis, 1)) {
      if (!error) { error = errno; phase = "clone_stage: basis cleanup"; }
    } else basis_owned = 0;
  }
  {
    int close_error = unsn_stage_close(&stage_read);
    if (close_error && !error) {
      error = close_error; phase = "clone_stage: output read close";
    }
    close_error = unsn_stage_close(&reserve);
    if (close_error && !error) {
      error = close_error; phase = "clone_stage: reservation close";
    }
  }
  if (error || unsupported) {
    unsn_stage_close(&basis);
    unsn_stage_close(&output);
  }
  /* Only the additive handles ABI transfers the actual creation directory.
   * Legacy success, every decline and every error still close it here. */
  if (parent >= 0 && (!keep_parent || error || unsupported)) {
    int close_error = unsn_stage_close(&parent);
    if (close_error && !error) {
      error = close_error; phase = "clone_stage: destination parent close";
      /* The last directory close has lost name authority. Preserve a linked
       * output rather than attempting an absolute-path cleanup. */
      unsn_stage_close(&basis); unsn_stage_close(&output);
    }
  }
  free(attrs); free(scratch); free(src); free(dst);
  caml_acquire_runtime_system();
  goto report;
done:
  free(attrs); free(scratch); free(src); free(dst);
report:
  if (error) caml_unix_error(error, strict ? phase : "clone_stage", destination);
  if (unsupported) {
    if (!strict) CAMLreturn(Val_int(0));
    Store_field(declined, 0, Val_int(decline_reason));
    CAMLreturn(declined);
  }
  Store_field(pair, 0, Val_int(basis)); Store_field(pair, 1, Val_int(output));
  if (keep_parent) Store_field(pair, 2, Val_int(parent));
  CAMLreturn(result);
}

CAMLprim value unison_clone_stage(value source, value destination)
{
  return unsn_clone_stage_impl(source, destination, 0, 0, 0, 0);
}

CAMLprim value unison_clone_stage_status(value source, value destination)
{
  return unsn_clone_stage_impl(source, destination, 1, 0, 0, 0);
}

CAMLprim value unison_clone_stage_handles(value source, value destination)
{
  return unsn_clone_stage_impl(source, destination, 1, 1, 0, 0);
}

CAMLprim value unison_clone_stage_sized_handles(value source, value destination,
                                               value expected_length)
{
  CAMLparam3(source, destination, expected_length);
  int64_t expected = Int64_val(expected_length);
  CAMLreturn(unsn_clone_stage_impl(source, destination, 1, 1, 1, expected));
}
#else
CAMLprim value unison_clone_stage(value source, value destination)
{
  CAMLparam2(source, destination);
  CAMLreturn(Val_int(0));
}

CAMLprim value unison_clone_stage_status(value source, value destination)
{
  CAMLparam2(source, destination);
  CAMLlocal1(result);
  result = caml_alloc(1, 1);
  Store_field(result, 0, Val_int(0)); /* Fs.Platform_unavailable */
  CAMLreturn(result);
}

CAMLprim value unison_clone_stage_handles(value source, value destination)
{
  /* The strict decline constructors have identical layouts in both ABIs. */
  return unison_clone_stage_status(source, destination);
}

CAMLprim value unison_clone_stage_sized_handles(value source, value destination,
                                               value expected_length)
{
  CAMLparam3(source, destination, expected_length);
  if (Int64_val(expected_length) < 0)
    caml_unix_error(EINVAL, "clone_stage: expected length", destination);
  CAMLreturn(unison_clone_stage_status(source, destination));
}
#endif
