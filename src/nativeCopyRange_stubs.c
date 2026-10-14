/* Strict, endpoint-local range-copy receipts.  The upstream compatibility
 * primitive remains in copy_stubs.c.  Successful copying here does not attest
 * block sharing, even when the kernel chooses to share storage internally. */

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
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#endif

#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/signals.h>
#include <caml/threads.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <stdint.h>
#include <limits.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <winioctl.h>
#endif

/* Keep these scalar codes in agreement with NativeCopyRange's decoder. */
enum unsn_range_status { RANGE_PROGRESS, RANGE_DECLINED, RANGE_FAILED };
enum unsn_range_mutation { RANGE_NO_EFFECT, RANGE_KNOWN_PREFIX,
                           RANGE_INDETERMINATE };
enum unsn_range_backend { RANGE_PLATFORM, RANGE_LINUX_COPY_FILE_RANGE,
                          RANGE_LINUX_SENDFILE, RANGE_FREEBSD, RANGE_SOLARIS,
                          RANGE_WINDOWS };
enum unsn_range_phase { RANGE_UNAVAILABLE, RANGE_ARGUMENTS, RANGE_DESCRIPTORS,
                        RANGE_COPY_FILE_RANGE, RANGE_SENDFILE,
                        RANGE_VOLUME_QUERY, RANGE_GEOMETRY, RANGE_SPARSE,
                        RANGE_EXTEND_EOF, RANGE_DUPLICATE_EXTENTS,
                        RANGE_ADVANCE_POSITION, RANGE_VERIFY_POSITION };
enum unsn_range_decline { RANGE_NOT_DECLINED, RANGE_PLATFORM_ABSENT,
                          RANGE_KERNEL_ABSENT, RANGE_FILESYSTEM_ABSENT,
                          RANGE_CROSS_DEVICE, RANGE_ALIGNMENT };

struct unsn_range_result {
  int status, backend, phase, mutation, decline;
  intnat completed;
  int unix_error;
  int64_t native_code;
};

static void unsn_range_fail(struct unsn_range_result *result, int phase,
                            int error, int mutation, int64_t native_code)
{
  result->status = RANGE_FAILED;
  result->phase = phase;
  result->unix_error = error ? error : EIO;
  result->native_code = native_code;
  result->mutation = mutation;
  result->decline = RANGE_NOT_DECLINED;
}

static void unsn_range_decline(struct unsn_range_result *result, int phase,
                               int reason, int error, int64_t native_code)
{
  result->status = RANGE_DECLINED;
  result->phase = phase;
  result->unix_error = error;
  result->native_code = native_code;
  result->mutation = RANGE_NO_EFFECT;
  result->decline = reason;
}

#ifndef _WIN32

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#if defined(__linux__) || defined(__linux)
#include <sys/syscall.h>
#include <sys/sendfile.h>
#elif defined(__FreeBSD__)
#include <sys/param.h>
#elif defined(__sun) || defined(sun)
#include <sys/sendfile.h>
#endif

/* No EINVAL, EBADF, ESPIPE or historical unknown-error convention is promoted
 * to a capability result.  Expected unsupported native errors still require
 * an unchanged destination position before they can permit suffix copying. */
#if defined(__linux__) || defined(__linux) || \
    (defined(__FreeBSD__) && __FreeBSD_version >= 1300037) || \
    defined(__sun) || defined(sun)
static int unsn_range_unsupported(int error)
{
  if (error == ENOSYS) return RANGE_KERNEL_ABSENT;
  if (error == EXDEV) return RANGE_CROSS_DEVICE;
  if (error == EOPNOTSUPP) return RANGE_FILESYSTEM_ABSENT;
  return RANGE_NOT_DECLINED;
}

static int unsn_range_position(int output, off_t expected,
                               struct unsn_range_result *result)
{
  off_t actual = lseek(output, (off_t)0, SEEK_CUR);
  if (actual == (off_t)-1) {
    int error = errno;
    unsn_range_fail(result, RANGE_VERIFY_POSITION, error,
                    RANGE_INDETERMINATE, error);
    return 0;
  }
  if (actual != expected) {
    unsn_range_fail(result, RANGE_VERIFY_POSITION, EIO,
                    RANGE_INDETERMINATE, 0);
    return 0;
  }
  return 1;
}
#endif

static void unsn_range_posix(int input, int output, int64_t offset,
                             intnat length, struct unsn_range_result *result)
{
  struct stat source, destination;
  int flags, error;
  off_t source_offset, source_end, destination_offset, destination_end;

  if (offset < 0 || length < 0 || offset > INT64_MAX - (int64_t)length ||
      (uintmax_t)length > (uintmax_t)SIZE_MAX ||
      (uintmax_t)length > (uintmax_t)SSIZE_MAX) {
    unsn_range_fail(result, RANGE_ARGUMENTS, EINVAL, RANGE_NO_EFFECT, EINVAL);
    return;
  }
  source_offset = (off_t)offset;
  source_end = (off_t)(offset + (int64_t)length);
  if ((int64_t)source_offset != offset ||
      (int64_t)source_end != offset + (int64_t)length) {
    unsn_range_fail(result, RANGE_ARGUMENTS, EOVERFLOW,
                    RANGE_NO_EFFECT, EOVERFLOW);
    return;
  }
  if (input < 0 || output < 0) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
    return;
  }
  if (fstat(input, &source) == -1 || fstat(output, &destination) == -1) {
    error = errno;
    unsn_range_fail(result, RANGE_DESCRIPTORS, error, RANGE_NO_EFFECT, error);
    return;
  }
  if (!S_ISREG(source.st_mode) || !S_ISREG(destination.st_mode) ||
      (source.st_dev == destination.st_dev &&
       source.st_ino == destination.st_ino)) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EINVAL, RANGE_NO_EFFECT, EINVAL);
    return;
  }
  flags = fcntl(input, F_GETFL);
  if (flags == -1) {
    error = errno;
    unsn_range_fail(result, RANGE_DESCRIPTORS, error, RANGE_NO_EFFECT, error);
    return;
  }
  if ((flags & O_ACCMODE) != O_RDONLY && (flags & O_ACCMODE) != O_RDWR) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
    return;
  }
#ifdef O_PATH
  if (flags & O_PATH) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
    return;
  }
#endif
#ifdef O_EVTONLY
  if (flags & O_EVTONLY) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
    return;
  }
#endif
  flags = fcntl(output, F_GETFL);
  if (flags == -1) {
    error = errno;
    unsn_range_fail(result, RANGE_DESCRIPTORS, error, RANGE_NO_EFFECT, error);
    return;
  }
  if ((flags & O_ACCMODE) != O_WRONLY && (flags & O_ACCMODE) != O_RDWR) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
    return;
  }
  if (flags & O_APPEND) {
    unsn_range_fail(result, RANGE_DESCRIPTORS, EINVAL, RANGE_NO_EFFECT, EINVAL);
    return;
  }
  if (source.st_size < 0 || offset > (int64_t)source.st_size ||
      (int64_t)length > (int64_t)source.st_size - offset) {
    unsn_range_fail(result, RANGE_ARGUMENTS, EINVAL, RANGE_NO_EFFECT, EINVAL);
    return;
  }
  destination_offset = lseek(output, (off_t)0, SEEK_CUR);
  if (destination_offset == (off_t)-1) {
    error = errno;
    unsn_range_fail(result, RANGE_DESCRIPTORS, error, RANGE_NO_EFFECT, error);
    return;
  }
  if (destination_offset < 0 ||
      (uintmax_t)destination_offset > (uintmax_t)INT64_MAX ||
      (int64_t)destination_offset > INT64_MAX - (int64_t)length) {
    unsn_range_fail(result, RANGE_ARGUMENTS, EOVERFLOW,
                    RANGE_NO_EFFECT, EOVERFLOW);
    return;
  }
  destination_end = (off_t)((int64_t)destination_offset + (int64_t)length);
  if ((int64_t)destination_end !=
      (int64_t)destination_offset + (int64_t)length) {
    unsn_range_fail(result, RANGE_ARGUMENTS, EOVERFLOW,
                    RANGE_NO_EFFECT, EOVERFLOW);
    return;
  }
  if (length == 0) {
    result->status = RANGE_PROGRESS;
    result->phase = RANGE_ARGUMENTS;
    return;
  }

#if defined(__linux__) || defined(__linux) || \
    (defined(__FreeBSD__) && __FreeBSD_version >= 1300037) || \
    defined(__sun) || defined(sun)
  {
    ssize_t copied;
    off_t native_source_offset = source_offset;
    int decline;
#if defined(__linux__) || defined(__linux)
#ifdef __NR_copy_file_range
    result->backend = RANGE_LINUX_COPY_FILE_RANGE;
    result->phase = RANGE_COPY_FILE_RANGE;
    copied = syscall(__NR_copy_file_range, input, &native_source_offset,
                      output, NULL, (size_t)length, 0);
    error = copied == -1 ? errno : 0;
    decline = unsn_range_unsupported(error);
    if (copied == -1 && decline != RANGE_NOT_DECLINED) {
      if (native_source_offset != source_offset) {
        unsn_range_fail(result, RANGE_COPY_FILE_RANGE, error,
                        RANGE_INDETERMINATE, error);
        return;
      }
      if (!unsn_range_position(output, destination_offset, result)) return;
      /* Reuse upstream's second acceleration only after a known no-effect
       * decline. Descriptor/argument/operational errors never trigger it. */
      result->backend = RANGE_LINUX_SENDFILE;
      result->phase = RANGE_SENDFILE;
      copied = sendfile(output, input, &native_source_offset, (size_t)length);
      error = copied == -1 ? errno : 0;
    }
#else
    result->backend = RANGE_LINUX_SENDFILE;
    result->phase = RANGE_SENDFILE;
    copied = sendfile(output, input, &native_source_offset, (size_t)length);
    error = copied == -1 ? errno : 0;
#endif
#elif defined(__FreeBSD__)
    result->backend = RANGE_FREEBSD;
    result->phase = RANGE_COPY_FILE_RANGE;
    copied = copy_file_range(input, &native_source_offset, output, NULL,
                             (size_t)length, 0);
    error = copied == -1 ? errno : 0;
#else
    result->backend = RANGE_SOLARIS;
    result->phase = RANGE_SENDFILE;
    copied = sendfile(output, input, &native_source_offset, (size_t)length);
    error = copied == -1 ? errno : 0;
#endif
    /* Capture native errno above, before lseek or runtime reacquisition. */
    if (copied == -1) {
#if defined(__sun) || defined(sun)
      if (native_source_offset > source_offset &&
          native_source_offset <= source_end) {
        result->completed = (intnat)(native_source_offset - source_offset);
        unsn_range_fail(result, result->phase, error,
                        RANGE_INDETERMINATE, error);
        if (unsn_range_position(output,
              (off_t)(destination_offset + result->completed), result))
          result->mutation = RANGE_KNOWN_PREFIX;
        return;
      }
#endif
      decline = unsn_range_unsupported(error);
      if (decline != RANGE_NOT_DECLINED &&
          native_source_offset == source_offset) {
        int phase = result->phase;
        if (!unsn_range_position(output, destination_offset, result)) return;
        unsn_range_decline(result, phase, decline, error, error);
      } else {
        unsn_range_fail(result, result->phase, error,
                        RANGE_INDETERMINATE, error);
      }
      return;
    }
    if (copied < 0 || (uintmax_t)copied > (uintmax_t)length ||
        native_source_offset != source_offset + copied) {
      unsn_range_fail(result, result->phase, EIO, RANGE_INDETERMINATE, 0);
      return;
    }
    result->completed = (intnat)copied;
    result->mutation = copied ? RANGE_KNOWN_PREFIX : RANGE_NO_EFFECT;
    if (!unsn_range_position(output,
          (off_t)(destination_offset + copied), result)) return;
    result->status = RANGE_PROGRESS;
    return;
  }
#else
  /* This path still executes all argument/descriptor preflight. Unavailable
   * acceleration must never disguise an invalid borrow as permission to copy. */
  unsn_range_decline(result, RANGE_UNAVAILABLE, RANGE_PLATFORM_ABSENT, 0, 0);
#endif
}

#else /* _WIN32 */

/* Match the guarded compatibility declarations in copy_stubs.c without
 * exporting duplicate symbols or depending on an external NT import library. */
#ifndef FILE_SUPPORTS_BLOCK_REFCOUNTING
#define FILE_SUPPORTS_BLOCK_REFCOUNTING 0x08000000
#endif
#ifndef FSCTL_GET_INTEGRITY_INFORMATION
#define FSCTL_GET_INTEGRITY_INFORMATION 0x9027c
#endif
#ifndef FSCTL_DUPLICATE_EXTENTS_TO_FILE
#define FSCTL_DUPLICATE_EXTENTS_TO_FILE 0x98344
#endif
#if defined(__MINGW32__)
typedef struct _FSCTL_GET_INTEGRITY_INFORMATION_BUFFER {
  WORD ChecksumAlgorithm;
  WORD Reserved;
  DWORD Flags;
  DWORD ChecksumChunkSizeInBytes;
  DWORD ClusterSizeInBytes;
} FSCTL_GET_INTEGRITY_INFORMATION_BUFFER;
#if !defined(__MINGW64_VERSION_MAJOR) || __MINGW64_VERSION_MAJOR < 13
typedef struct _DUPLICATE_EXTENTS_DATA {
  HANDLE FileHandle;
  LARGE_INTEGER SourceFileOffset;
  LARGE_INTEGER TargetFileOffset;
  LARGE_INTEGER ByteCount;
} DUPLICATE_EXTENTS_DATA;
#endif
#endif

/* PUBLIC_OBJECT_BASIC_INFORMATION's documented fixed layout:
 * https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntqueryobject
 * ObjectBasicInformation is a synchronous object query, not queued file I/O.
 * Reserved fields are opaque; no NtQueryInformationFile stack reply can remain
 * outstanding after this primitive returns. */
struct unsn_range_object_basic {
  ULONG attributes;
  ACCESS_MASK granted_access;
  ULONG handle_count;
  ULONG pointer_count;
  ULONG reserved[10];
};
typedef LONG (NTAPI *unsn_range_query_object)
  (HANDLE, ULONG, PVOID, ULONG, PULONG);
typedef ULONG (NTAPI *unsn_range_status_to_error)(LONG);

/* Win32 errors retain DWORD; the descriptor access query retains its original
 * unsigned NTSTATUS and supplies the separately mapped DOS/Unix error. */
static void unsn_range_win_fail(struct unsn_range_result *result, int phase,
                               DWORD error, int mutation)
{
  unsn_range_fail(result, phase, 0, mutation, (int64_t)(uint32_t)error);
  /* Preserve even an inconsistent zero native code; provide EIO separately.
   * Nonzero Win32 codes are mapped only with the OCaml runtime held. */
  result->unix_error = error ? 0 : EIO;
}

static DWORD unsn_range_win_error(void)
{
  return GetLastError();
}

/* DeviceIoControl's device-specific contract requires an event for overlapped
 * handles. Own at most one private manual-reset event at a time, entirely in
 * the released-runtime section. Borrowed file handles stay valid/exclusive
 * until this operation settles; neither the OVERLAPPED nor its stack buffers
 * may escape while pending. There is no OS wait deadline here.
 * https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-deviceiocontrol
 * https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult
 * completed distinguishes successful device mutation from a subsequent event
 * close failure. Preserve the primary error, otherwise report close failure.
 * A failed OS CloseHandle is terminal; reliable cleanup after such an OS
 * failure is not claimed, and this event handle is never retried/reused. */
static int unsn_range_win_control(HANDLE file, DWORD code,
                                  void *input, DWORD input_size,
                                  void *output, DWORD output_size,
                                  DWORD *returned, DWORD *error, int *completed)
{
  OVERLAPPED overlap;
  HANDLE event;
  BOOL succeeded, closed;
  DWORD close_error;

  *returned = 0;
  *error = 0;
  *completed = 0;
  event = CreateEventW(NULL, TRUE, FALSE, NULL);
  if (!event) {
    *error = unsn_range_win_error();
    return 0;
  }
  memset(&overlap, 0, sizeof(overlap));
  overlap.hEvent = event;
  succeeded = DeviceIoControl(file, code, input, input_size, output, output_size,
                              returned, &overlap);
  if (!succeeded) {
    *error = unsn_range_win_error();
    if (*error == ERROR_IO_PENDING) {
      /* Synchronous handles can ignore OVERLAPPED, so the immediate TRUE path
       * keeps DeviceIoControl's returned bytes. Await only a reported pending
       * operation, using this operation's private event and reply structure. */
      do {
        succeeded = GetOverlappedResult(file, &overlap, returned, TRUE);
        *error = succeeded ? 0 : unsn_range_win_error();
      } while (!succeeded &&
               (*error == ERROR_IO_PENDING || *error == ERROR_IO_INCOMPLETE));
    }
  }
  *completed = succeeded != FALSE;
  /* No runtime callback or allocation can interrupt native cleanup. Copy the
   * primary error before CloseHandle can overwrite thread-local error state. */
  closed = CloseHandle(event);
  close_error = closed ? 0 : unsn_range_win_error();
  if (!closed) {
    if (succeeded) *error = close_error;
    return 0;
  }
  return succeeded != FALSE;
}

static int unsn_range_win_position(HANDLE output, LONGLONG expected,
                                   struct unsn_range_result *result,
                                   DWORD *map_error)
{
  LARGE_INTEGER zero, actual;
  zero.QuadPart = 0;
  if (!SetFilePointerEx(output, zero, &actual, FILE_CURRENT)) {
    *map_error = unsn_range_win_error();
    unsn_range_win_fail(result, RANGE_VERIFY_POSITION, *map_error,
                        RANGE_INDETERMINATE);
    return 0;
  }
  if (actual.QuadPart != expected) {
    *map_error = ERROR_GEN_FAILURE;
    unsn_range_win_fail(result, RANGE_VERIFY_POSITION, *map_error,
                        RANGE_INDETERMINATE);
    return 0;
  }
  return 1;
}

static void unsn_range_windows(HANDLE input, HANDLE output,
                               int64_t offset, intnat length,
                               struct unsn_range_result *result,
                               DWORD *map_error)
{
  BY_HANDLE_FILE_INFORMATION source, destination;
  struct unsn_range_object_basic source_access, destination_access;
  HMODULE ntdll;
  unsn_range_query_object query;
  unsn_range_status_to_error map_status;
  LONG status;
  DWORD source_flags, destination_flags, returned, kind;
  FSCTL_GET_INTEGRITY_INFORMATION_BUFFER source_integrity,
                                        destination_integrity;
  DUPLICATE_EXTENTS_DATA duplicate;
  LARGE_INTEGER zero, cursor, ending;
  FILE_END_OF_FILE_INFO eof;
  FILE_SET_SPARSE_BUFFER sparse;
  uint64_t source_size, destination_size;
  int source_sparse, destination_sparse, control_completed;

  result->backend = RANGE_WINDOWS;
  if (offset < 0 || length < 0 || offset > INT64_MAX - (int64_t)length) {
    *map_error = ERROR_INVALID_PARAMETER;
    unsn_range_win_fail(result, RANGE_ARGUMENTS, *map_error, RANGE_NO_EFFECT);
    return;
  }
#define WIN_FAIL(phase, mutation) do { \
  *map_error = unsn_range_win_error(); \
  unsn_range_win_fail(result, phase, *map_error, mutation); return; \
} while (0)
  kind = GetFileType(input);
  if (kind == FILE_TYPE_UNKNOWN) WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  if (kind != FILE_TYPE_DISK) {
    *map_error = ERROR_INVALID_PARAMETER;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  kind = GetFileType(output);
  if (kind == FILE_TYPE_UNKNOWN) WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  if (kind != FILE_TYPE_DISK) {
    *map_error = ERROR_INVALID_PARAMETER;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  if (!GetFileInformationByHandle(input, &source))
    WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  if (!GetFileInformationByHandle(output, &destination))
    WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  if ((source.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
      (destination.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ||
      (source.dwVolumeSerialNumber == destination.dwVolumeSerialNumber &&
       source.nFileIndexHigh == destination.nFileIndexHigh &&
       source.nFileIndexLow == destination.nFileIndexLow)) {
    *map_error = ERROR_INVALID_PARAMETER;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  /* These pointers and NT reply structures are per-call stack values. There
   * is no global lazy initialization, allocation or newly owned module handle. */
  ntdll = GetModuleHandleW(L"ntdll.dll");
  if (!ntdll) WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  query = (unsn_range_query_object)GetProcAddress(ntdll, "NtQueryObject");
  if (!query) WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  map_status = (unsn_range_status_to_error)GetProcAddress(ntdll,
                                                        "RtlNtStatusToDosError");
  if (!map_status) WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  memset(&source_access, 0, sizeof(source_access));
  returned = 0;
  status = query(input, 0, &source_access, sizeof(source_access), &returned);
  if (status != 0) {
    *map_error = map_status(status);
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    result->native_code = (int64_t)(uint32_t)status;
    return;
  }
  if (returned != sizeof(source_access)) {
    *map_error = ERROR_INVALID_DATA;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  memset(&destination_access, 0, sizeof(destination_access));
  returned = 0;
  status = query(output, 0, &destination_access,
                  sizeof(destination_access), &returned);
  if (status != 0) {
    *map_error = map_status(status);
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    result->native_code = (int64_t)(uint32_t)status;
    return;
  }
  if (returned != sizeof(destination_access)) {
    *map_error = ERROR_INVALID_DATA;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  /* Generic writers can have both WRITE_DATA and APPEND_DATA. Require the
   * former, rejecting append-only handles; the caller must additionally avoid
   * append-mode wrappers, whose userspace semantics these access bits do not
   * establish. Windows runtime/mode qualification remains separate. */
  if (!(source_access.granted_access & FILE_READ_DATA) ||
      !(destination_access.granted_access & FILE_WRITE_DATA)) {
    *map_error = ERROR_ACCESS_DENIED;
    unsn_range_win_fail(result, RANGE_DESCRIPTORS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  source_size = ((uint64_t)source.nFileSizeHigh << 32) | source.nFileSizeLow;
  destination_size = ((uint64_t)destination.nFileSizeHigh << 32) |
                      destination.nFileSizeLow;
  if (source_size > INT64_MAX || destination_size > INT64_MAX ||
      (uint64_t)offset > source_size ||
      (uint64_t)length > source_size - (uint64_t)offset) {
    *map_error = ERROR_INVALID_PARAMETER;
    unsn_range_win_fail(result, RANGE_ARGUMENTS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  zero.QuadPart = 0;
  if (!SetFilePointerEx(output, zero, &cursor, FILE_CURRENT))
    WIN_FAIL(RANGE_DESCRIPTORS, RANGE_NO_EFFECT);
  if (cursor.QuadPart < 0 || cursor.QuadPart > INT64_MAX - (int64_t)length) {
    *map_error = ERROR_ARITHMETIC_OVERFLOW;
    unsn_range_win_fail(result, RANGE_ARGUMENTS, *map_error, RANGE_NO_EFFECT);
    return;
  }
  ending.QuadPart = cursor.QuadPart + (int64_t)length;
  if (length == 0) {
    result->status = RANGE_PROGRESS;
    result->phase = RANGE_ARGUMENTS;
    return;
  }
  if (!GetVolumeInformationByHandleW(input, NULL, 0, NULL, NULL,
                                     &source_flags, NULL, 0))
    WIN_FAIL(RANGE_VOLUME_QUERY, RANGE_NO_EFFECT);
  if (!GetVolumeInformationByHandleW(output, NULL, 0, NULL, NULL,
                                     &destination_flags, NULL, 0))
    WIN_FAIL(RANGE_VOLUME_QUERY, RANGE_NO_EFFECT);
  if (!(source_flags & FILE_SUPPORTS_BLOCK_REFCOUNTING) ||
      !(destination_flags & FILE_SUPPORTS_BLOCK_REFCOUNTING)) {
    unsn_range_decline(result, RANGE_VOLUME_QUERY, RANGE_FILESYSTEM_ABSENT, 0, 0);
    return;
  }
  if (source.dwVolumeSerialNumber != destination.dwVolumeSerialNumber) {
    unsn_range_decline(result, RANGE_VOLUME_QUERY, RANGE_CROSS_DEVICE, 0, 0);
    return;
  }
  memset(&source_integrity, 0, sizeof(source_integrity));
  memset(&destination_integrity, 0, sizeof(destination_integrity));
  returned = 0;
  if (!unsn_range_win_control(input, FSCTL_GET_INTEGRITY_INFORMATION, NULL, 0,
                               &source_integrity, sizeof(source_integrity),
                               &returned, map_error, &control_completed)) {
    unsn_range_win_fail(result, RANGE_GEOMETRY, *map_error, RANGE_NO_EFFECT);
    return;
  }
  if (returned != sizeof(source_integrity) ||
      source_integrity.ClusterSizeInBytes == 0) {
    *map_error = ERROR_INVALID_DATA;
    unsn_range_win_fail(result, RANGE_GEOMETRY, *map_error, RANGE_NO_EFFECT);
    return;
  }
  returned = 0;
  if (!unsn_range_win_control(output, FSCTL_GET_INTEGRITY_INFORMATION, NULL, 0,
                               &destination_integrity,
                               sizeof(destination_integrity),
                               &returned, map_error, &control_completed)) {
    unsn_range_win_fail(result, RANGE_GEOMETRY, *map_error, RANGE_NO_EFFECT);
    return;
  }
  if (returned != sizeof(destination_integrity) ||
      destination_integrity.ClusterSizeInBytes == 0 ||
      destination_integrity.ClusterSizeInBytes !=
        source_integrity.ClusterSizeInBytes) {
    *map_error = ERROR_INVALID_DATA;
    unsn_range_win_fail(result, RANGE_GEOMETRY, *map_error, RANGE_NO_EFFECT);
    return;
  }
  if (offset % source_integrity.ClusterSizeInBytes != 0 ||
      cursor.QuadPart % source_integrity.ClusterSizeInBytes != 0 ||
      length % source_integrity.ClusterSizeInBytes != 0) {
    unsn_range_decline(result, RANGE_GEOMETRY, RANGE_ALIGNMENT, 0, 0);
    return;
  }
  memset(&duplicate, 0, sizeof(duplicate));
  duplicate.FileHandle = input;
  duplicate.SourceFileOffset.QuadPart = offset;
  duplicate.TargetFileOffset = cursor;
  duplicate.ByteCount.QuadPart = (int64_t)length; /* Exact: never round up. */
  source_sparse = (source.dwFileAttributes & FILE_ATTRIBUTE_SPARSE_FILE) != 0;
  destination_sparse =
    (destination.dwFileAttributes & FILE_ATTRIBUTE_SPARSE_FILE) != 0;
  if (source_sparse && !destination_sparse) {
    sparse.SetSparse = TRUE;
    if (!unsn_range_win_control(output, FSCTL_SET_SPARSE, &sparse, sizeof(sparse),
                                 NULL, 0, &returned, map_error,
                                 &control_completed)) {
      unsn_range_win_fail(result, RANGE_SPARSE, *map_error, RANGE_INDETERMINATE);
      return;
    }
  }
  if (destination_size < (uint64_t)ending.QuadPart) {
    if (!source_sparse && !destination_sparse) {
      sparse.SetSparse = TRUE;
      if (!unsn_range_win_control(output, FSCTL_SET_SPARSE, &sparse, sizeof(sparse),
                                   NULL, 0, &returned, map_error,
                                   &control_completed)) {
        unsn_range_win_fail(result, RANGE_SPARSE, *map_error, RANGE_INDETERMINATE);
        return;
      }
    }
    eof.EndOfFile = ending;
    if (!SetFileInformationByHandle(output, FileEndOfFileInfo, &eof,
                                     sizeof(eof)))
      WIN_FAIL(RANGE_EXTEND_EOF, RANGE_INDETERMINATE);
    if (!source_sparse && !destination_sparse) {
      sparse.SetSparse = FALSE;
      if (!unsn_range_win_control(output, FSCTL_SET_SPARSE, &sparse, sizeof(sparse),
                                   NULL, 0, &returned, map_error,
                                   &control_completed)) {
        unsn_range_win_fail(result, RANGE_SPARSE, *map_error, RANGE_INDETERMINATE);
        return;
      }
    }
  }
  /* Every failed duplication is conservatively indeterminate, including after
   * successful sparse/EOF preparation; it never authorizes ordinary fallback. */
  if (!unsn_range_win_control(output, FSCTL_DUPLICATE_EXTENTS_TO_FILE,
                               &duplicate, sizeof(duplicate), NULL, 0,
                               &returned, map_error, &control_completed)) {
    if (control_completed) result->completed = length;
    unsn_range_win_fail(result, RANGE_DUPLICATE_EXTENTS,
                        *map_error, RANGE_INDETERMINATE);
    return;
  }
  result->completed = length;
  result->mutation = RANGE_KNOWN_PREFIX;
  if (!unsn_range_win_position(output, cursor.QuadPart, result, map_error)) return;
  if (!SetFilePointerEx(output, ending, NULL, FILE_BEGIN))
    WIN_FAIL(RANGE_ADVANCE_POSITION, RANGE_INDETERMINATE);
  if (!unsn_range_win_position(output, ending.QuadPart, result, map_error)) return;
  result->status = RANGE_PROGRESS;
  result->phase = RANGE_DUPLICATE_EXTENTS;
#undef WIN_FAIL
}

#endif /* _WIN32 */

CAMLprim value unison_copy_file_status(value source, value destination,
                                      value source_offset, value length)
{
  CAMLparam4(source, destination, source_offset, length);
  CAMLlocal4(result, optional_error, mapped_error, raw_error);
  struct unsn_range_result native = {
    RANGE_FAILED, RANGE_PLATFORM, RANGE_ARGUMENTS, RANGE_NO_EFFECT,
    RANGE_NOT_DECLINED, 0, 0, 0
  };
  int64_t offset;
  intnat count;
#ifdef _WIN32
  HANDLE input, output;
  DWORD map_error = 0;
  int kinds_valid;
#else
  intnat input_number, output_number;
#endif
  /* A pending handler can raise before the borrow starts. After copying the
   * scalars/handles, entry must not run another pending handler. No OCaml heap
   * pointer, native allocation or descriptor ownership crosses the release. */
  caml_process_pending_actions();
  offset = Int64_val(source_offset);
  count = Long_val(length);
#ifdef _WIN32
  kinds_valid = Descr_kind_val(source) == KIND_HANDLE &&
                Descr_kind_val(destination) == KIND_HANDLE;
  input = Handle_val(source);
  output = Handle_val(destination);
#else
  input_number = Long_val(source);
  output_number = Long_val(destination);
#endif
  caml_enter_blocking_section_no_pending();
#ifdef _WIN32
  if (!kinds_valid) {
    map_error = ERROR_INVALID_HANDLE;
    native.backend = RANGE_WINDOWS;
    unsn_range_win_fail(&native, RANGE_DESCRIPTORS, map_error, RANGE_NO_EFFECT);
  } else {
    unsn_range_windows(input, output, offset, count, &native, &map_error);
  }
#else
  if (input_number < 0 || input_number > INT_MAX ||
      output_number < 0 || output_number > INT_MAX) {
    unsn_range_fail(&native, RANGE_DESCRIPTORS, EBADF, RANGE_NO_EFFECT, EBADF);
  } else {
    unsn_range_posix((int)input_number, (int)output_number, offset, count, &native);
  }
#endif
  caml_acquire_runtime_system();
#ifdef _WIN32
  if (map_error != 0) {
    caml_win32_maperr(map_error);
    native.unix_error = errno ? errno : EIO;
  }
#endif
  optional_error = Val_int(0);
  if (native.unix_error != 0) {
    mapped_error = caml_unix_error_of_code(native.unix_error);
    optional_error = caml_alloc_small(1, 0);
    Store_field(optional_error, 0, mapped_error);
  }
  raw_error = caml_copy_int64(native.native_code);
  result = caml_alloc_tuple(8);
  Store_field(result, 0, Val_int(native.status));
  Store_field(result, 1, Val_long(native.completed));
  Store_field(result, 2, Val_int(native.backend));
  Store_field(result, 3, Val_int(native.phase));
  Store_field(result, 4, optional_error);
  Store_field(result, 5, Val_int(native.mutation));
  Store_field(result, 6, Val_int(native.decline));
  Store_field(result, 7, raw_error);
  CAMLreturn(result);
}
