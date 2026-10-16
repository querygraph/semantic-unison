/* Strict, endpoint-local whole-file cloning.  The upstream boolean symbols in
 * copy_stubs.c remain compatibility APIs.  A receipt here describes one held
 * object operation, not measured physical allocation or an immutable digest.
 *
 * Native Linux and Windows paths are source implementations, not runtime
 * qualification on a macOS host.  Named creation uses a preallocated owner;
 * its finalizer closes descriptors only and NEVER removes saved names. */

#if (defined(__linux__) || defined(__linux)) && !defined(_GNU_SOURCE)
#define _GNU_SOURCE
#endif
#ifdef _WIN32
#ifndef WINVER
#define WINVER 0x0603
#endif
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0603
#endif
#endif

#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/custom.h>
#include <caml/fail.h>
#include <caml/signals.h>
#include <caml/threads.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <errno.h>
#include <stdint.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error_of_code unix_error_of_code
#define caml_unix_error unix_error
#define caml_win32_maperr win32_maperr
#endif

/* These IDs belong to WholeFileClone, not to the range-copy protocol. */
enum wf_status { WF_SHARED, WF_DECLINED, WF_FAILED, WF_NO_WORK };
enum wf_backend { WF_PLATFORM, WF_LINUX_FICLONE, WF_MACOS_FCLONEFILEAT };
enum wf_mutation { WF_NO_EFFECT, WF_KNOWN_PREFIX, WF_INDETERMINATE };
enum wf_decline { WF_NOT_DECLINED, WF_PLATFORM_ABSENT, WF_KERNEL_ABSENT,
                  WF_FILESYSTEM_ABSENT, WF_CROSS_DEVICE, WF_SOURCE_CONSTRAINTS,
                  WF_EMPTY_SOURCE };
enum wf_phase { WF_UNAVAILABLE, WF_ARGUMENTS, WF_SOURCE_DESCRIPTOR,
                WF_DESTINATION_DESCRIPTOR, WF_SOURCE_EOF, WF_DESTINATION_EOF,
                WF_SOURCE_POSITION, WF_DESTINATION_POSITION,
                WF_DESTINATION_PARENT, WF_NATIVE_CLONE, WF_VERIFY_SOURCE,
                WF_VERIFY_DESTINATION, WF_VERIFY_CURSOR, WF_PROPERTY_PROFILE,
                WF_CLEANUP };
struct wf_result {
  int status, backend, phase, error, mutation, decline;
  int64_t completed, native_code;
};

static struct wf_result wf_initial(void)
{
  struct wf_result r = { WF_FAILED, WF_PLATFORM, WF_ARGUMENTS, EIO,
                         WF_NO_EFFECT, WF_NOT_DECLINED, 0, 0 };
  return r;
}
static void wf_fail(struct wf_result *r, int phase, int error,
                    int mutation, int64_t native_code)
{
  r->status = WF_FAILED; r->phase = phase; r->error = error ? error : EIO;
  r->mutation = mutation; r->decline = WF_NOT_DECLINED;
  r->native_code = native_code;
}
static void wf_declined(struct wf_result *r, int phase, int decline,
                        int error, int64_t native_code)
{
  r->status = WF_DECLINED; r->phase = phase; r->error = error;
  r->mutation = WF_NO_EFFECT; r->decline = decline;
  r->completed = 0; r->native_code = native_code;
}
static void wf_success(struct wf_result *r, int64_t length)
{
  r->status = length ? WF_SHARED : WF_NO_WORK;
  r->error = 0; r->native_code = 0; r->decline = WF_NOT_DECLINED;
  r->completed = length; r->mutation = length ? WF_KNOWN_PREFIX : WF_NO_EFFECT;
}

static value wf_raw(struct wf_result r)
{
  CAMLparam0();
  CAMLlocal5(result, optional_error, mapped_error, completed, raw_error);
  optional_error = Val_int(0);
  if (r.error) {
    mapped_error = caml_unix_error_of_code(r.error);
    optional_error = caml_alloc_small(1, 0);
    Store_field(optional_error, 0, mapped_error);
  }
  completed = caml_copy_int64(r.completed);
  raw_error = caml_copy_int64(r.native_code);
  result = caml_alloc_tuple(8);
  Store_field(result, 0, Val_int(r.status));
  Store_field(result, 1, completed);
  Store_field(result, 2, Val_int(r.backend));
  Store_field(result, 3, Val_int(r.phase));
  Store_field(result, 4, optional_error);
  Store_field(result, 5, Val_int(r.mutation));
  Store_field(result, 6, Val_int(r.decline));
  Store_field(result, 7, raw_error);
  CAMLreturn(result);
}

#ifndef _WIN32
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#if defined(__linux__) || defined(__linux)
#include <sys/ioctl.h>
#ifndef FICLONE
#ifdef _IOW
#define FICLONE _IOW(0x94, 9, int)
#endif
#endif
#endif
#ifdef __APPLE__
#include <AvailabilityMacros.h>
#if defined(MAC_OS_X_VERSION_10_12)
#include <sys/clonefile.h>
#endif
#endif

static int wf_same_identity(const struct stat *a, const struct stat *b)
{
  return a->st_dev == b->st_dev && a->st_ino == b->st_ino;
}
static int wf_same_constraints(const struct stat *a, const struct stat *b)
{
  return wf_same_identity(a, b) && a->st_mode == b->st_mode &&
    a->st_nlink == b->st_nlink && a->st_uid == b->st_uid && a->st_gid == b->st_gid
#if defined(__APPLE__) || defined(__FreeBSD__) || defined(__NetBSD__) || defined(__OpenBSD__)
    && a->st_flags == b->st_flags
#endif
    ;
}
static int wf_same_source(const struct stat *a, const struct stat *b)
{
  return wf_same_constraints(a, b) && a->st_size == b->st_size &&
#ifdef __APPLE__
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
    a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec;
#elif (defined(__NetBSD__) && ((_POSIX_C_SOURCE - 0) < 200809L) && \
       ((_XOPEN_SOURCE - 0) < 700) && !defined(_NETBSD_SOURCE)) || \
      (defined(__OpenBSD__) && __POSIX_VISIBLE < 200809 && !__BSD_VISIBLE)
    /* BSD headers retain separate second/nanosecond fields when the selected
     * feature namespace predates POSIX2008; do not require a hidden st_mtim. */
    a->st_mtime == b->st_mtime && a->st_mtimensec == b->st_mtimensec &&
    a->st_ctime == b->st_ctime && a->st_ctimensec == b->st_ctimensec;
#else
    a->st_mtim.tv_sec == b->st_mtim.tv_sec &&
    a->st_mtim.tv_nsec == b->st_mtim.tv_nsec &&
    a->st_ctim.tv_sec == b->st_ctim.tv_sec &&
    a->st_ctim.tv_nsec == b->st_ctim.tv_nsec;
#endif
}
static int wf_flags(int fd, int output, struct wf_result *r)
{
  int flags = fcntl(fd, F_GETFL), phase = output ? WF_DESTINATION_DESCRIPTOR :
                                                 WF_SOURCE_DESCRIPTOR;
  if (flags == -1) {
    int error = errno; wf_fail(r, phase, error, WF_NO_EFFECT, error); return 0;
  }
  if ((output && (flags & O_ACCMODE) != O_WRONLY &&
                  (flags & O_ACCMODE) != O_RDWR) ||
      (!output && (flags & O_ACCMODE) != O_RDONLY &&
                   (flags & O_ACCMODE) != O_RDWR)) {
    wf_fail(r, phase, EBADF, WF_NO_EFFECT, EBADF); return 0;
  }
#ifdef O_PATH
  if (flags & O_PATH) {
    wf_fail(r, phase, EBADF, WF_NO_EFFECT, EBADF); return 0;
  }
#endif
#ifdef O_EVTONLY
  if (flags & O_EVTONLY) {
    wf_fail(r, phase, EBADF, WF_NO_EFFECT, EBADF); return 0;
  }
#endif
  if (output && (flags & O_APPEND)) {
    wf_fail(r, phase, EINVAL, WF_NO_EFFECT, EINVAL); return 0;
  }
  return 1;
}
static int wf_length(int64_t length, struct wf_result *r)
{
  if (length < 0) {
    wf_fail(r, WF_ARGUMENTS, EINVAL, WF_NO_EFFECT, EINVAL); return 0;
  }
  if ((int64_t)(off_t)length != length) {
    wf_fail(r, WF_ARGUMENTS, EOVERFLOW, WF_NO_EFFECT, EOVERFLOW); return 0;
  }
  return 1;
}
static int wf_source_preflight(int source, int64_t length, struct stat *before,
                               off_t *position, struct wf_result *r)
{
  if (!wf_length(length, r)) return 0;
  if (source < 0) {
    wf_fail(r, WF_SOURCE_DESCRIPTOR, EBADF, WF_NO_EFFECT, EBADF); return 0;
  }
  if (fstat(source, before)) {
    int error = errno;
    wf_fail(r, WF_SOURCE_DESCRIPTOR, error, WF_NO_EFFECT, error); return 0;
  }
  if (!S_ISREG(before->st_mode)) {
    wf_fail(r, WF_SOURCE_DESCRIPTOR, EINVAL, WF_NO_EFFECT, EINVAL); return 0;
  }
  if (!wf_flags(source, 0, r)) return 0;
  if (before->st_size < 0 || (int64_t)before->st_size != length) {
    wf_fail(r, WF_SOURCE_EOF, EBUSY, WF_NO_EFFECT, 0); return 0;
  }
  *position = lseek(source, 0, SEEK_CUR);
  if (*position == (off_t)-1) {
    int error = errno;
    wf_fail(r, WF_SOURCE_POSITION, error, WF_NO_EFFECT, error); return 0;
  }
  return 1;
}
static int wf_cursor(int fd, off_t before, struct wf_result *r, int mutation)
{
  off_t after = lseek(fd, 0, SEEK_CUR);
  if (after == (off_t)-1) {
    int error = errno;
    wf_fail(r, WF_VERIFY_CURSOR, error, mutation, error); return 0;
  }
  if (after != before) {
    wf_fail(r, WF_VERIFY_CURSOR, EBUSY, mutation, 0); return 0;
  }
  return 1;
}
static int wf_post_flags(int fd, int output, struct wf_result *r)
{
  if (wf_flags(fd, output, r)) return 1;
  r->mutation = WF_INDETERMINATE;
  r->phase = output ? WF_VERIFY_DESTINATION : WF_VERIFY_SOURCE;
  return 0;
}

static void wf_fd_posix(int source, int destination, int64_t length,
                        struct wf_result *r)
{
  struct stat src, dst, src_after, dst_after;
  off_t source_position, destination_position;
  int error;
  if (!wf_source_preflight(source, length, &src, &source_position, r)) return;
  if (destination < 0 || fstat(destination, &dst)) {
    error = destination < 0 ? EBADF : errno;
    wf_fail(r, WF_DESTINATION_DESCRIPTOR, error, WF_NO_EFFECT, error); return;
  }
  if (!S_ISREG(dst.st_mode) || dst.st_nlink != 1 || wf_same_identity(&src, &dst)) {
    wf_fail(r, WF_DESTINATION_DESCRIPTOR, EINVAL, WF_NO_EFFECT, EINVAL); return;
  }
  if (!wf_flags(destination, 1, r)) return;
  /* On macOS/BSD this FD backend is absent. Ordinary regular DATA can still be
   * readable/writable with native flags (for example nodump); do not turn the
   * named API's Source_constraints eligibility decline into a terminal error
   * here. Access/append/identity/EOF/position checks remain authoritative. */
  if (dst.st_size != 0) {
    wf_fail(r, WF_DESTINATION_EOF, EINVAL, WF_NO_EFFECT, EINVAL); return;
  }
  destination_position = lseek(destination, 0, SEEK_CUR);
  if (destination_position == (off_t)-1) {
    error = errno;
    wf_fail(r, WF_DESTINATION_POSITION, error, WF_NO_EFFECT, error); return;
  }
  if (destination_position != 0) {
    wf_fail(r, WF_DESTINATION_POSITION, EINVAL, WF_NO_EFFECT, EINVAL); return;
  }
  if (!length) { r->phase = WF_VERIFY_CURSOR; wf_success(r, 0); return; }
#if (defined(__linux__) || defined(__linux)) && defined(FICLONE)
  r->backend = WF_LINUX_FICLONE; r->phase = WF_NATIVE_CLONE;
  int native_status = ioctl(destination, FICLONE, source);
  if (native_status != 0) {
    error = native_status == -1 ? errno : EIO;
    int64_t raw_code = native_status == -1 ? error : 0;
    /* The whole ioctl has no authoritative partial-byte count. Only these
     * backend-specific unsupported outcomes may be considered no-effect, and
     * only after unchanged source, destination and cursor fences. EINVAL and
     * EBADF are operational failures, never a retry convention. */
    int decline = native_status != -1 ? WF_NOT_DECLINED :
                  error == ENOSYS || error == ENOTTY ? WF_KERNEL_ABSENT :
                  error == EOPNOTSUPP ? WF_FILESYSTEM_ABSENT :
                  error == EXDEV ? WF_CROSS_DEVICE : WF_NOT_DECLINED;
    wf_fail(r, WF_NATIVE_CLONE, error, WF_INDETERMINATE, raw_code);
    if (!decline) return;
    if (fstat(source, &src_after)) {
      error = errno; wf_fail(r, WF_VERIFY_SOURCE, error, WF_INDETERMINATE, error); return;
    }
    if (!wf_same_source(&src, &src_after)) {
      wf_fail(r, WF_VERIFY_SOURCE, EBUSY, WF_INDETERMINATE, 0); return;
    }
    if (fstat(destination, &dst_after)) {
      error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
    }
    if (!wf_same_source(&dst, &dst_after)) {
      wf_fail(r, WF_VERIFY_DESTINATION, EBUSY, WF_INDETERMINATE, 0); return;
    }
    if (!wf_cursor(source, source_position, r, WF_INDETERMINATE) ||
        !wf_cursor(destination, destination_position, r, WF_INDETERMINATE)) return;
    if (!wf_post_flags(source, 0, r) || !wf_post_flags(destination, 1, r)) return;
    wf_declined(r, WF_NATIVE_CLONE, decline, error, error); return;
  }
  if (fstat(source, &src_after)) {
    error = errno; wf_fail(r, WF_VERIFY_SOURCE, error, WF_INDETERMINATE, error); return;
  }
  if (!wf_same_source(&src, &src_after)) {
    wf_fail(r, WF_VERIFY_SOURCE, EBUSY, WF_INDETERMINATE, 0); return;
  }
  if (fstat(destination, &dst_after)) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  if (!wf_same_constraints(&dst, &dst_after) || dst_after.st_size != (off_t)length) {
    wf_fail(r, WF_VERIFY_DESTINATION, EBUSY, WF_INDETERMINATE, 0); return;
  }
  r->completed = length;
  if (!wf_cursor(source, source_position, r, WF_INDETERMINATE) ||
      !wf_cursor(destination, destination_position, r, WF_INDETERMINATE)) return;
  if (!wf_post_flags(source, 0, r) || !wf_post_flags(destination, 1, r)) return;
  r->phase = WF_VERIFY_CURSOR; wf_success(r, length);
#else
  /* Unsupported platforms still perform real descriptor/EOF/access preflight.
   * This result is scoped absence, not a filesystem capability cache entry. */
  wf_declined(r, WF_UNAVAILABLE, WF_PLATFORM_ABSENT, 0, 0);
#endif
}

#else /* _WIN32 */
#include <windows.h>

/* Synchronous NtQueryObject ObjectBasicInformation avoids pending stack I/O.
 * Raw NTSTATUS bits remain opaque; mapped Unix errors are separate. No global
 * mutable lazy initialization or acquired module ownership is introduced. */
struct wf_object_basic {
  ULONG attributes; ACCESS_MASK granted_access;
  ULONG handle_count, pointer_count, reserved[10];
};
typedef LONG (NTAPI *wf_query_object)(HANDLE, ULONG, PVOID, ULONG, PULONG);
typedef ULONG (NTAPI *wf_status_to_error)(LONG);
static void wf_win_fail(struct wf_result *r, int phase, DWORD code,
                        DWORD *map_error)
{
  *map_error = code;
  wf_fail(r, phase, code ? 0 : EIO, WF_NO_EFFECT, (int64_t)(uint32_t)code);
  if (code) r->error = 0;
}
static int wf_win_observe(HANDLE file, int output,
                          BY_HANDLE_FILE_INFORMATION *info,
                          LARGE_INTEGER *position, struct wf_result *r,
                          DWORD *map_error)
{
  int phase = output ? WF_DESTINATION_DESCRIPTOR : WF_SOURCE_DESCRIPTOR;
  DWORD kind = GetFileType(file), returned = 0;
  HMODULE module;
  wf_query_object query;
  wf_status_to_error map_status;
  struct wf_object_basic access;
  LARGE_INTEGER zero;
  LONG status;
  if (kind == FILE_TYPE_UNKNOWN) {
    wf_win_fail(r, phase, GetLastError(), map_error); return 0;
  }
  if (kind != FILE_TYPE_DISK) {
    wf_win_fail(r, phase, ERROR_INVALID_PARAMETER, map_error); return 0;
  }
  if (!GetFileInformationByHandle(file, info)) {
    wf_win_fail(r, phase, GetLastError(), map_error); return 0;
  }
  if (info->dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) {
    wf_win_fail(r, phase, ERROR_INVALID_PARAMETER, map_error); return 0;
  }
  module = GetModuleHandleW(L"ntdll.dll");
  if (!module) { wf_win_fail(r, phase, GetLastError(), map_error); return 0; }
  query = (wf_query_object)GetProcAddress(module, "NtQueryObject");
  if (!query) { wf_win_fail(r, phase, GetLastError(), map_error); return 0; }
  map_status = (wf_status_to_error)GetProcAddress(module, "RtlNtStatusToDosError");
  if (!map_status) { wf_win_fail(r, phase, GetLastError(), map_error); return 0; }
  memset(&access, 0, sizeof(access));
  status = query(file, 0, &access, sizeof(access), &returned);
  if (status != 0) {
    wf_win_fail(r, phase, map_status(status), map_error);
    r->native_code = (int64_t)(uint32_t)status; return 0;
  }
  if (returned != sizeof(access)) {
    wf_win_fail(r, phase, ERROR_INVALID_DATA, map_error); return 0;
  }
  /* FILE_WRITE_DATA rejects append-only rights. The FILE_APPEND_DATA bit on a
   * generic writable handle does not prove an append mode; exclusive nonappend
   * runtime use remains the caller contract on this absent backend. */
  if (!(access.granted_access & (output ? FILE_WRITE_DATA : FILE_READ_DATA))) {
    wf_win_fail(r, phase, ERROR_ACCESS_DENIED, map_error); return 0;
  }
  zero.QuadPart = 0;
  if (!SetFilePointerEx(file, zero, position, FILE_CURRENT)) {
    wf_win_fail(r, output ? WF_DESTINATION_POSITION : WF_SOURCE_POSITION,
                 GetLastError(), map_error); return 0;
  }
  return 1;
}
static void wf_fd_windows(HANDLE source, HANDLE destination, int64_t length,
                          struct wf_result *r, DWORD *map_error)
{
  BY_HANDLE_FILE_INFORMATION src, dst;
  LARGE_INTEGER source_position, destination_position;
  uint64_t source_size, destination_size;
  if (length < 0) {
    wf_win_fail(r, WF_ARGUMENTS, ERROR_INVALID_PARAMETER, map_error); return;
  }
  if (!wf_win_observe(source, 0, &src, &source_position, r, map_error) ||
      !wf_win_observe(destination, 1, &dst, &destination_position, r, map_error)) return;
  if (dst.nNumberOfLinks != 1 ||
      (src.dwVolumeSerialNumber == dst.dwVolumeSerialNumber &&
       src.nFileIndexHigh == dst.nFileIndexHigh &&
       src.nFileIndexLow == dst.nFileIndexLow)) {
    wf_win_fail(r, WF_DESTINATION_DESCRIPTOR, ERROR_INVALID_PARAMETER, map_error); return;
  }
  source_size = ((uint64_t)src.nFileSizeHigh << 32) | src.nFileSizeLow;
  destination_size = ((uint64_t)dst.nFileSizeHigh << 32) | dst.nFileSizeLow;
  if (source_size != (uint64_t)length) {
    wf_fail(r, WF_SOURCE_EOF, EBUSY, WF_NO_EFFECT, 0); return;
  }
  if (destination_size) {
    wf_win_fail(r, WF_DESTINATION_EOF, ERROR_INVALID_PARAMETER, map_error); return;
  }
  if (source_position.QuadPart < 0) {
    wf_win_fail(r, WF_SOURCE_POSITION, ERROR_INVALID_PARAMETER, map_error); return;
  }
  if (destination_position.QuadPart != 0) {
    wf_win_fail(r, WF_DESTINATION_POSITION, ERROR_INVALID_PARAMETER, map_error); return;
  }
  if (!length) { r->phase = WF_VERIFY_CURSOR; wf_success(r, 0); return; }
  /* ReFS range duplication is a distinct future composed whole operation;
   * CopyFile's opportunistic sharing is not a strict native whole clone. */
  wf_declined(r, WF_UNAVAILABLE, WF_PLATFORM_ABSENT, 0, 0);
}
#endif

CAMLprim value unison_clone_file_status(value source, value destination,
                                       value expected_length)
{
  CAMLparam3(source, destination, expected_length);
  struct wf_result r = wf_initial();
  int64_t length;
#ifdef _WIN32
  HANDLE input, output;
  int valid;
  DWORD map_error = 0;
#else
  intnat input, output;
#endif
  caml_process_pending_actions();
  length = Int64_val(expected_length);
#ifdef _WIN32
  valid = Descr_kind_val(source) == KIND_HANDLE &&
          Descr_kind_val(destination) == KIND_HANDLE;
  input = Handle_val(source); output = Handle_val(destination);
#else
  input = Long_val(source); output = Long_val(destination);
#endif
  caml_enter_blocking_section_no_pending();
#ifdef _WIN32
  if (!valid) wf_win_fail(&r, WF_SOURCE_DESCRIPTOR, ERROR_INVALID_HANDLE, &map_error);
  else wf_fd_windows(input, output, length, &r, &map_error);
#else
  if (input < 0 || input > INT_MAX)
    wf_fail(&r, WF_SOURCE_DESCRIPTOR, EBADF, WF_NO_EFFECT, EBADF);
  else if (output < 0 || output > INT_MAX)
    wf_fail(&r, WF_DESTINATION_DESCRIPTOR, EBADF, WF_NO_EFFECT, EBADF);
  else wf_fd_posix((int)input, (int)output, length, &r);
#endif
  caml_acquire_runtime_system();
#ifdef _WIN32
  if (map_error) {
    caml_win32_maperr(map_error); r.error = errno ? errno : EIO;
  }
#endif
  CAMLreturn(wf_raw(r));
}

/* Named owner state is deliberately separate from the raw scalar receipt.
 * run stores all ownership/result facts before reacquiring the runtime.  The
 * installed stock5.5.1 and inspected Ox runtimes mark pending actions during
 * reacquisition; later allocations/polls/adoption may raise.  The rooted custom
 * owner remains discoverable by the facade on every such path. */
enum wf_owner_state { WF_PREPARED, WF_ATTEMPTED, WF_ADMITTED,
                       WF_TRANSFERRED, WF_ABORTED };
struct wf_named_owner {
#ifndef _WIN32
  pthread_mutex_t mutex;
  int mutex_ready;
  struct stat parent_identity, output_identity;
#else
  SRWLOCK mutex;
#endif
  char *leaf;
  int output, backup, owns_output, created, admitted, parent_observed;
  int state, cleanup_error, residual, finish_done, finish_error;
  struct wf_result result;
};

static int wf_close_owned(int *slot)
{
  int fd = *slot;
  *slot = -1;
#ifndef _WIN32
  if (fd >= 0 && close(fd)) return errno;
#else
  (void)fd; /* No named Windows backend owns an output descriptor. */
#endif
  return 0;
}
static void wf_named_finalize(value owner)
{
  struct wf_named_owner *ctx = *(struct wf_named_owner **)Data_custom_val(owner);
  if (!ctx) return;
  *(struct wf_named_owner **)Data_custom_val(owner) = NULL;
  /* Every active call roots its owner, so finalization cannot race that call.
   * Transferred output is only borrowed: never close it from this finalizer.
   * Saved names confer NO finalizer unlink authority. */
  if (ctx->owns_output) wf_close_owned(&ctx->output);
  wf_close_owned(&ctx->backup);
#ifndef _WIN32
  if (ctx->mutex_ready) pthread_mutex_destroy(&ctx->mutex);
#endif
  free(ctx->leaf); free(ctx);
}
static struct custom_operations wf_named_operations = {
  .identifier = "unison.whole_clone.named_owner.v0",
  .finalize = wf_named_finalize,
  .compare = custom_compare_default,
  .hash = custom_hash_default,
  .serialize = custom_serialize_default,
  .deserialize = custom_deserialize_default,
  .compare_ext = custom_compare_ext_default,
  .fixed_length = custom_fixed_length_default
};
static struct wf_named_owner *wf_named_context(value owner)
{
  if (!Is_block(owner) || Tag_val(owner) != Custom_tag ||
      Custom_ops_val(owner) != &wf_named_operations)
    caml_invalid_argument("whole_clone: invalid owner");
  struct wf_named_owner *ctx = *(struct wf_named_owner **)Data_custom_val(owner);
  if (!ctx) caml_invalid_argument("whole_clone: finalized owner");
  return ctx;
}
static int wf_named_lock(struct wf_named_owner *ctx)
{
#ifndef _WIN32
  return pthread_mutex_lock(&ctx->mutex);
#else
  AcquireSRWLockExclusive(&ctx->mutex); return 0;
#endif
}
static void wf_named_unlock(struct wf_named_owner *ctx)
{
#ifndef _WIN32
  pthread_mutex_unlock(&ctx->mutex);
#else
  ReleaseSRWLockExclusive(&ctx->mutex);
#endif
}

CAMLprim value unison_whole_clone_named_available(value unit)
{
  (void)unit;
#if defined(__APPLE__) && defined(MAC_OS_X_VERSION_10_12)
  if (__builtin_available(macOS 10.12, *)) return Val_true;
#endif
  return Val_false;
}

CAMLprim value unison_whole_clone_prepare_named(value leaf)
{
  CAMLparam1(leaf);
  CAMLlocal1(owner);
  mlsize_t length = caml_string_length(leaf);
  int error = 0;
  if (!length || memchr(String_val(leaf), '\0', length) ||
      memchr(String_val(leaf), '/', length) ||
      memchr(String_val(leaf), '\\', length) ||
      (length == 1 && String_val(leaf)[0] == '.') ||
      (length == 2 && String_val(leaf)[0] == '.' && String_val(leaf)[1] == '.'))
    caml_invalid_argument("whole_clone: private leaf required");
  caml_process_pending_actions();
  owner = caml_alloc_custom(&wf_named_operations, sizeof(struct wf_named_owner *),
                            sizeof(struct wf_named_owner) + length + 1, 1);
  *(struct wf_named_owner **)Data_custom_val(owner) = NULL;
  struct wf_named_owner *ctx = calloc(1, sizeof(*ctx));
  if (!ctx) caml_raise_out_of_memory();
  *(struct wf_named_owner **)Data_custom_val(owner) = ctx;
  ctx->output = ctx->backup = -1;
  ctx->result = wf_initial();
  ctx->leaf = malloc(length + 1);
  if (!ctx->leaf) caml_raise_out_of_memory();
  memcpy(ctx->leaf, String_val(leaf), length); ctx->leaf[length] = '\0';
#ifndef _WIN32
  error = pthread_mutex_init(&ctx->mutex, NULL);
  if (error) caml_unix_error(error, "whole_clone.prepare.mutex", Nothing);
  ctx->mutex_ready = 1;
#else
  InitializeSRWLock(&ctx->mutex);
#endif
  CAMLreturn(owner);
}

#ifndef _WIN32
/* Parent observations deliberately exclude directory entry timestamps: sibling
 * operations can change them. Identity/constraints are cooperative witnesses,
 * not a proof of mount lifetime or atomic compare-and-unlink. */
static int wf_same_parent(const struct stat *a, const struct stat *b)
{
  return S_ISDIR(a->st_mode) && S_ISDIR(b->st_mode) &&
    wf_same_identity(a, b) && a->st_mode == b->st_mode &&
    a->st_uid == b->st_uid && a->st_gid == b->st_gid
#if defined(__APPLE__) || defined(__FreeBSD__) || defined(__NetBSD__) || defined(__OpenBSD__)
    && a->st_flags == b->st_flags
#endif
    ;
}
#if defined(__APPLE__) && defined(MAC_OS_X_VERSION_10_12)
static int wf_named_absent(int parent, const char *leaf, struct wf_result *r,
                           int mutation)
{
  struct stat named;
  int phase = mutation == WF_NO_EFFECT ? WF_DESTINATION_PARENT :
                                         WF_VERIFY_DESTINATION;
  if (!fstatat(parent, leaf, &named, AT_SYMLINK_NOFOLLOW)) {
    wf_fail(r, phase, EEXIST, mutation, EEXIST); return 0;
  }
  int error = errno;
  if (error != ENOENT) {
    wf_fail(r, phase, error, mutation, error); return 0;
  }
  return 1;
}
static int wf_named_match(struct wf_named_owner *ctx, int parent, int witness,
                          int missing_ok)
{
  struct stat directory, held, named, after;
  if (fstat(parent, &directory)) return -1;
  if (!ctx->parent_observed || !wf_same_parent(&ctx->parent_identity, &directory)) {
    errno = EBUSY; return -1;
  }
  if (fstat(witness, &held)) return -1;
  if (!S_ISREG(held.st_mode) || held.st_nlink != 1 ||
      !wf_same_identity(&ctx->output_identity, &held)) {
    errno = EBUSY; return -1;
  }
  if (fstatat(parent, ctx->leaf, &named, AT_SYMLINK_NOFOLLOW)) {
    if (missing_ok && errno == ENOENT) return 1;
    return -1;
  }
  if (fstat(witness, &after)) return -1;
  if (!S_ISREG(named.st_mode) || named.st_nlink != 1 ||
      !wf_same_identity(&held, &named) || !wf_same_identity(&held, &after)) {
    errno = EBUSY; return -1;
  }
  return 0;
}
#endif

static void wf_named_posix(int source, int parent, int64_t length,
                           struct wf_named_owner *ctx)
{
  struct wf_result *r = &ctx->result;
  struct stat src, src_after, directory, output;
  off_t source_position;
  int error;
  if (!wf_source_preflight(source, length, &src, &source_position, r)) return;
  if (parent < 0 || fstat(parent, &directory)) {
    error = parent < 0 ? EBADF : errno;
    wf_fail(r, WF_DESTINATION_PARENT, error, WF_NO_EFFECT, error); return;
  }
  if (!S_ISDIR(directory.st_mode)) {
    wf_fail(r, WF_DESTINATION_PARENT, ENOTDIR, WF_NO_EFFECT, ENOTDIR); return;
  }
  ctx->parent_identity = directory; ctx->parent_observed = 1;
#if defined(__APPLE__) && defined(MAC_OS_X_VERSION_10_12)
  if (!wf_named_absent(parent, ctx->leaf, r, WF_NO_EFFECT)) return;
  if (__builtin_available(macOS 10.12, *)) {} else {
    wf_declined(r, WF_UNAVAILABLE, WF_PLATFORM_ABSENT, 0, 0); return;
  }
  r->backend = WF_MACOS_FCLONEFILEAT;
  if (src.st_flags) {
    wf_declined(r, WF_SOURCE_DESCRIPTOR, WF_SOURCE_CONSTRAINTS, 0, 0); return;
  }
  if (!length) {
    wf_declined(r, WF_SOURCE_EOF, WF_EMPTY_SOURCE, 0, 0); return;
  }
  r->phase = WF_NATIVE_CLONE;
  int native_status = fclonefileat(source, parent, ctx->leaf, CLONE_NOOWNERCOPY);
  if (native_status != 0) {
    error = native_status == -1 ? errno : EIO;
    int64_t raw_code = native_status == -1 ? error : 0;
    /* clonefile documents atomic creation/failure. Verify absence, the actual
     * parent and source/cursor before admitting its scoped support declines.
     * EEXIST or changed/unknown name ownership is terminal and never removed. */
    int decline = native_status != -1 ? WF_NOT_DECLINED :
                  error == ENOSYS ? WF_KERNEL_ABSENT :
                  error == ENOTSUP ? WF_FILESYSTEM_ABSENT :
                  error == EXDEV ? WF_CROSS_DEVICE : WF_NOT_DECLINED;
    wf_fail(r, WF_NATIVE_CLONE, error, WF_INDETERMINATE, raw_code);
    if (!decline) return;
    if (!wf_named_absent(parent, ctx->leaf, r, WF_INDETERMINATE)) return;
    if (fstat(parent, &directory)) {
      error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
    }
    if (!wf_same_parent(&ctx->parent_identity, &directory)) {
      wf_fail(r, WF_VERIFY_DESTINATION, EBUSY, WF_INDETERMINATE, 0); return;
    }
    if (fstat(source, &src_after)) {
      error = errno; wf_fail(r, WF_VERIFY_SOURCE, error, WF_INDETERMINATE, error); return;
    }
    if (!wf_same_source(&src, &src_after)) {
      wf_fail(r, WF_VERIFY_SOURCE, EBUSY, WF_INDETERMINATE, 0); return;
    }
    if (!wf_cursor(source, source_position, r, WF_INDETERMINATE)) return;
    if (!wf_post_flags(source, 0, r)) return;
    wf_declined(r, WF_NATIVE_CLONE, decline, error, error); return;
  }
  ctx->created = 1; /* Publish residue before any subsequent fallible action. */
  /* Opening after creation has a cooperative first-admission assumption; a
   * clonefile syscall does not return an atomic created-inode receipt. */
  ctx->output = openat(parent, ctx->leaf,
                       O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
  if (ctx->output < 0) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  ctx->owns_output = 1;
  if (fstat(ctx->output, &output)) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  if (!S_ISREG(output.st_mode) || output.st_nlink != 1 ||
      output.st_dev != ctx->parent_identity.st_dev ||
      wf_same_identity(&src, &output) || output.st_size != (off_t)length) {
    wf_fail(r, WF_VERIFY_DESTINATION, EBUSY, WF_INDETERMINATE, 0); return;
  }
  ctx->output_identity = output;
  if (wf_named_match(ctx, parent, ctx->output, 0)) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  ctx->admitted = 1;
  if (fstat(source, &src_after)) {
    error = errno; wf_fail(r, WF_VERIFY_SOURCE, error, WF_INDETERMINATE, error); return;
  }
  if (!wf_same_source(&src, &src_after)) {
    wf_fail(r, WF_VERIFY_SOURCE, EBUSY, WF_INDETERMINATE, 0); return;
  }
  if (!wf_cursor(source, source_position, r, WF_INDETERMINATE) ||
      !wf_cursor(ctx->output, 0, r, WF_INDETERMINATE)) return;
  if (!wf_post_flags(source, 0, r)) return;
  if (fstat(ctx->output, &output)) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  if (!wf_same_constraints(&ctx->output_identity, &output) ||
      output.st_size != (off_t)length) {
    wf_fail(r, WF_VERIFY_DESTINATION, EBUSY, WF_INDETERMINATE, 0); return;
  }
  if (wf_named_match(ctx, parent, ctx->output, 0)) {
    error = errno; wf_fail(r, WF_VERIFY_DESTINATION, error, WF_INDETERMINATE, error); return;
  }
  r->completed = length;
  /* Retain a second, independently owned witness through the facade's result
   * construction/source close. finish closes it before the last transfer. */
  ctx->backup = fcntl(ctx->output, F_DUPFD_CLOEXEC, 0);
  if (ctx->backup < 0) {
    error = errno; wf_fail(r, WF_CLEANUP, error, WF_INDETERMINATE, error); return;
  }
  ctx->state = WF_ADMITTED; r->phase = WF_VERIFY_CURSOR; wf_success(r, length);
#else
  wf_declined(r, WF_UNAVAILABLE, WF_PLATFORM_ABSENT, 0, 0);
#endif
}
#endif

CAMLprim value unison_whole_clone_run_named(value source, value parent,
                                           value expected_length, value owner)
{
  CAMLparam4(source, parent, expected_length, owner);
  struct wf_named_owner *ctx = wf_named_context(owner);
  struct wf_result receipt;
  int64_t length;
  int lock_error;
#ifndef _WIN32
  intnat input, directory;
#endif
  caml_process_pending_actions();
  length = Int64_val(expected_length);
#ifndef _WIN32
  input = Long_val(source); directory = Long_val(parent);
#endif
  caml_enter_blocking_section_no_pending();
  lock_error = wf_named_lock(ctx);
  if (!lock_error) {
    if (ctx->state != WF_PREPARED) {
      receipt = wf_initial();
      wf_fail(&receipt, WF_ARGUMENTS, EBUSY, WF_NO_EFFECT, 0);
    } else {
      ctx->state = WF_ATTEMPTED;
#ifndef _WIN32
      if (input < 0 || input > INT_MAX)
        wf_fail(&ctx->result, WF_SOURCE_DESCRIPTOR, EBADF, WF_NO_EFFECT, EBADF);
      else if (directory < 0 || directory > INT_MAX)
        wf_fail(&ctx->result, WF_DESTINATION_PARENT, EBADF, WF_NO_EFFECT, EBADF);
      else wf_named_posix((int)input, (int)directory, length, ctx);
#else
      /* The facade uses named_available before opening unsupported directory
       * handles. No Windows named creation or descriptor ownership is added. */
      wf_declined(&ctx->result, WF_UNAVAILABLE, WF_PLATFORM_ABSENT, 0, 0);
#endif
      receipt = ctx->result;
    }
    wf_named_unlock(ctx);
  } else {
    receipt = wf_initial();
    wf_fail(&receipt, WF_ARGUMENTS, lock_error, WF_NO_EFFECT, lock_error);
  }
  caml_acquire_runtime_system();
  CAMLreturn(wf_raw(receipt));
}

CAMLprim value unison_whole_clone_peek_named_output(value owner)
{
  CAMLparam1(owner);
  struct wf_named_owner *ctx = wf_named_context(owner);
  int error = wf_named_lock(ctx), fd;
  if (error) caml_unix_error(error, "whole_clone.peek.lock", Nothing);
  fd = ctx->state == WF_ADMITTED && ctx->owns_output ? ctx->output : -1;
  wf_named_unlock(ctx);
  if (fd < 0) caml_invalid_argument("whole_clone: no admitted output");
  CAMLreturn(Val_int(fd));
}

CAMLprim value unison_whole_clone_transfer_named_output(value owner,
                                                       value fd_ref,
                                                       value transferred_ref)
{
  CAMLparam3(owner, fd_ref, transferred_ref);
  struct wf_named_owner *ctx = wf_named_context(owner);
  int error;
  /* These facade-owned one-field boxes are allocated before native mutation.
   * Valid transfer has no allocation, runtime release, pending dispatch or
   * raising action after the ownership stores. */
  if (!Is_block(fd_ref) || Tag_val(fd_ref) != 0 || Wosize_val(fd_ref) != 1 ||
      !Is_block(transferred_ref) || Tag_val(transferred_ref) != 0 ||
      Wosize_val(transferred_ref) != 1 || Field(transferred_ref, 0) != Val_false)
    caml_invalid_argument("whole_clone: invalid handoff boxes");
  error = wf_named_lock(ctx);
  if (error) caml_unix_error(error, "whole_clone.transfer.lock", Nothing);
  if (ctx->state != WF_ADMITTED || !ctx->owns_output || ctx->output < 0 ||
      ctx->backup >= 0 || !ctx->finish_done || ctx->finish_error) {
    wf_named_unlock(ctx); caml_invalid_argument("whole_clone: invalid transfer state");
  }
  Store_field(fd_ref, 0, Val_int(ctx->output));
  Store_field(transferred_ref, 0, Val_true);
  ctx->owns_output = 0; ctx->state = WF_TRANSFERRED;
  /* Keep only BORROWED cleanup witness identity/number. Fs aborts before
   * closing its slot; finalization never closes this transferred descriptor. */
  wf_named_unlock(ctx);
  CAMLreturn(Val_unit);
}

/* Unix.close enters a pending-dispatching blocking section before its OS close
 * on the inspected runtimes. A facade cannot disarm its slot and then call that
 * primitive: an early callback could leave a live FD without an owner. This
 * private named-facade close performs the ownership store and its single close
 * with no intervening allocation or pending dispatch. Later errors/polls see a
 * settled slot; a failed OS close never authorizes retrying a recycled number. */
CAMLprim value unison_whole_clone_close_slot(value fd_ref, value owned_ref)
{
  CAMLparam2(fd_ref, owned_ref);
#ifndef _WIN32
  intnat number;
  int error;
#endif
  if (!Is_block(fd_ref) || Tag_val(fd_ref) != 0 || Wosize_val(fd_ref) != 1 ||
      !Is_block(owned_ref) || Tag_val(owned_ref) != 0 || Wosize_val(owned_ref) != 1 ||
      (Field(owned_ref, 0) != Val_false && Field(owned_ref, 0) != Val_true))
    caml_invalid_argument("whole_clone: invalid close owner boxes");
  if (Field(owned_ref, 0) == Val_false) CAMLreturn(Val_unit);
#ifndef _WIN32
  if (!Is_long(Field(fd_ref, 0)))
    caml_unix_error(EBADF, "whole_clone.close_slot", Nothing);
  number = Long_val(Field(fd_ref, 0));
  if (number < 0 || number > INT_MAX)
    caml_unix_error(EBADF, "whole_clone.close_slot", Nothing);
  Store_field(owned_ref, 0, Val_false);
  caml_enter_blocking_section_no_pending();
  error = close((int)number) ? errno : 0;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "whole_clone.close_slot", Nothing);
  CAMLreturn(Val_unit);
#else
  /* Named availability is false, so the Windows facade acquires no such slots.
   * Do not close a CRT/socket/HANDLE with an invented ownership convention. */
  caml_unix_error(ENOSYS, "whole_clone.close_slot.platform", Nothing);
  CAMLreturn(Val_unit);
#endif
}

static value wf_cleanup_raw(int error, int residual)
{
  CAMLparam0();
  CAMLlocal4(result, optional_error, mapped, raw_error);
  optional_error = Val_int(0);
  if (error) {
    mapped = caml_unix_error_of_code(error);
    optional_error = caml_alloc_small(1, 0); Store_field(optional_error, 0, mapped);
  }
  raw_error = caml_copy_int64(error);
  result = caml_alloc_tuple(3);
  Store_field(result, 0, optional_error); Store_field(result, 1, raw_error);
  Store_field(result, 2, Val_int(residual));
  CAMLreturn(result);
}

CAMLprim value unison_whole_clone_abort_named(value owner, value parent)
{
  CAMLparam2(owner, parent);
  struct wf_named_owner *ctx = wf_named_context(owner);
  int error = 0, residual = 0, lock_error;
#ifndef _WIN32
  intnat directory = Long_val(parent);
#endif
  /* Abort intentionally does not dispatch pending actions before cleanup. */
  caml_enter_blocking_section_no_pending();
  lock_error = wf_named_lock(ctx);
  if (lock_error) error = lock_error;
  else {
    if (ctx->state == WF_ABORTED) {
      error = ctx->cleanup_error; residual = ctx->residual;
    } else {
      if (ctx->created) {
        residual = 2; /* No missing-name/ownership assertion without a witness. */
#if defined(__APPLE__) && defined(MAC_OS_X_VERSION_10_12)
        int witness = ctx->backup >= 0 ? ctx->backup : ctx->output;
        if (directory < 0 || directory > INT_MAX) error = EBADF;
        else if (ctx->admitted && witness >= 0) {
          int matched = wf_named_match(ctx, (int)directory, witness, 1);
          if (matched < 0) error = errno;
          else if (matched > 0) residual = 0;
          else if (unlinkat((int)directory, ctx->leaf, 0)) {
            error = errno;
            if (error == ENOENT) { error = 0; residual = 0; }
          } else residual = 1;
        }
#endif
      }
      if (ctx->owns_output) {
        int close_error = wf_close_owned(&ctx->output);
        ctx->owns_output = 0;
        if (!error) error = close_error;
      }
      int close_error = wf_close_owned(&ctx->backup);
      if (!error) error = close_error;
      /* A transferred output number is now invalid for this context. Its
       * facade owner closes it after this cleanup, before closing parent. */
      ctx->output = -1; ctx->state = WF_ABORTED;
      ctx->cleanup_error = error; ctx->residual = residual;
    }
    wf_named_unlock(ctx);
  }
  caml_acquire_runtime_system();
  CAMLreturn(wf_cleanup_raw(error, residual));
}

CAMLprim value unison_whole_clone_finish_named(value owner)
{
  CAMLparam1(owner);
  struct wf_named_owner *ctx = wf_named_context(owner);
  int error, lock_error, residual;
  /* Close the backup before the facade's final no-allocation transfer. Main
   * ownership and cleanup authority are retained until that transfer. */
  caml_enter_blocking_section_no_pending();
  lock_error = wf_named_lock(ctx);
  if (lock_error) { error = lock_error; residual = 2; }
  else {
    residual = ctx->created ? 2 : 0;
    if (ctx->state != WF_ADMITTED || !ctx->owns_output) error = EBUSY;
    else if (ctx->finish_done) error = ctx->finish_error;
    else {
      error = wf_close_owned(&ctx->backup);
      ctx->finish_done = 1; ctx->finish_error = error;
    }
    wf_named_unlock(ctx);
  }
  caml_acquire_runtime_system();
  CAMLreturn(wf_cleanup_raw(error, residual));
}
