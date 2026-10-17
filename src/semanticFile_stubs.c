/* Bounded positional writes into an already admitted, caller-owned private
 * output. Admission does not duplicate or own the FD. The caller keeps it live,
 * exclusively writable and free of concurrent status-flag changes until the
 * borrowed writer is retired. No pathname operation or OCaml callback occurs. */
#if defined(__APPLE__) && !defined(_DARWIN_C_SOURCE)
#define _DARWIN_C_SOURCE 1
#endif
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
#include <caml/alloc.h>
#include <caml/custom.h>
#include <stdlib.h>
#include <stdio.h>
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

/* Borrowed positional input: no descriptor acquisition or close anywhere. */
CAMLprim value unison_semantic_prepare_reader(value descriptor)
{
  CAMLparam1(descriptor);
#ifndef _WIN32
  caml_process_pending_actions();
  int fd = unison_semantic_fd(descriptor, "semantic reader descriptor");
  int error = 0;
  struct stat stat;
  caml_enter_blocking_section_no_pending();
  int flags = fcntl(fd, F_GETFL);
  if (flags < 0) error = errno ? errno : EIO;
  else if ((flags & O_ACCMODE) != O_RDONLY &&
           (flags & O_ACCMODE) != O_RDWR) error = EBADF;
  if (!error && fstat(fd, &stat)) error = errno ? errno : EIO;
  if (!error && (!S_ISREG(stat.st_mode) || stat.st_size < 0)) error = EINVAL;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "semantic reader admission", Nothing);
  CAMLreturn(Val_true);
#else
  CAMLreturn(Val_false);
#endif
}

CAMLprim value unison_semantic_pread(value descriptor, value length, value position)
{
  CAMLparam3(descriptor, length, position);
  CAMLlocal1(result);
#ifndef _WIN32
  caml_process_pending_actions();
  intnat count = Long_val(length);
  int64_t offset = Int64_val(position);
  if (count < 0 || count > UNISON_SEMANTIC_WRITE_MAX || offset < 0 ||
      offset > INT64_MAX - (int64_t)count)
    caml_invalid_argument("SemanticFile.borrowed_read bounds");
  off_t native_offset = (off_t)offset;
  off_t native_end = (off_t)(offset + (int64_t)count);
  if ((int64_t)native_offset != offset ||
      (int64_t)native_end != offset + (int64_t)count)
    caml_invalid_argument("SemanticFile.borrowed_read offset");
  int fd = unison_semantic_fd(descriptor, "semantic pread descriptor");
  unsigned char buffer[UNISON_SEMANTIC_WRITE_MAX];
  caml_enter_blocking_section_no_pending();
  ssize_t received = pread(fd, buffer, (size_t)count, native_offset);
  int error = received == -1 ? errno : 0;
  if (received < -1 || received > count || (received == -1 && !error)) error = EIO;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "semantic pread", Nothing);
  result = caml_alloc_initialized_string((mlsize_t)received, (const char *)buffer);
  CAMLreturn(result);
#else
  caml_unix_error(ENOSYS, "semantic pread", Nothing);
#endif
}

/* Immutable checkpoint record publication. No descriptor is opened, duplicated,
 * closed or retained: the caller borrows both FDs through settlement. */
#ifdef __APPLE__
struct component_record_publication {
  struct stat directory, stage;
  char temporary[256], target[256];
  int ready, published;
};
#define RECORD_PUBLICATION(v) (*(struct component_record_publication **)Data_custom_val(v))
static void record_publication_finalize(value v)
{
  free(RECORD_PUBLICATION(v));
  RECORD_PUBLICATION(v) = NULL;
}
static struct custom_operations record_publication_ops = {
  .identifier = "unison.component-record-publication/0",
  .finalize = record_publication_finalize,
  .compare = custom_compare_default,
  .hash = custom_hash_default,
  .serialize = custom_serialize_default,
  .deserialize = custom_deserialize_default,
  .compare_ext = custom_compare_ext_default,
  .fixed_length = custom_fixed_length_default
};
static int record_directory_same(const struct stat *a, const struct stat *b)
{
  return S_ISDIR(b->st_mode) && a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_uid == b->st_uid && a->st_gid == b->st_gid && a->st_mode == b->st_mode &&
    a->st_flags == b->st_flags && b->st_uid == getuid() && (b->st_mode & 07777) == 0700;
}
static int record_stage_same(const struct stat *a, const struct stat *b, int check_ctime)
{
  return S_ISREG(b->st_mode) && a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_uid == b->st_uid && a->st_gid == b->st_gid && a->st_mode == b->st_mode &&
    a->st_flags == b->st_flags && a->st_size == b->st_size && b->st_nlink == 1 &&
    b->st_uid == getuid() && (b->st_mode & 07777) == 0600 &&
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    (!check_ctime || (a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
                     a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec));
}
static void record_leaf(value text, char output[256])
{
  mlsize_t length = caml_string_length(text);
  if (!length || length > 255 || memchr(String_val(text), 0, length) ||
      memchr(String_val(text), '/', length) ||
      (length == 1 && String_val(text)[0] == '.') ||
      (length == 2 && !memcmp(String_val(text), "..", 2)))
    caml_invalid_argument("component record leaf");
  memcpy(output, String_val(text), length); output[length] = 0;
}
#endif

CAMLprim value unison_component_record_publication_available(value unit)
{
  CAMLparam1(unit);
#ifdef __APPLE__
  CAMLreturn(Val_true);
#else
  CAMLreturn(Val_false);
#endif
}

CAMLprim value unison_component_record_publication_prepare(value directory, value stage,
                                                           value temporary, value target)
{
  CAMLparam4(directory, stage, temporary, target);
  CAMLlocal1(ticket);
#ifdef __APPLE__
  caml_process_pending_actions();
  ticket = caml_alloc_custom(&record_publication_ops, sizeof(void *), 0, 1);
  RECORD_PUBLICATION(ticket) = NULL;
  struct component_record_publication *context = calloc(1, sizeof(*context));
  if (!context) caml_raise_out_of_memory();
  RECORD_PUBLICATION(ticket) = context;
  record_leaf(temporary, context->temporary); record_leaf(target, context->target);
  if (!strcmp(context->temporary, context->target)) caml_invalid_argument("component record same leaf");
  int parent = unison_semantic_fd(directory, "component record directory FD");
  int fd = unison_semantic_fd(stage, "component record stage FD");
  struct stat named;
  if (fstat(parent, &context->directory) == -1 || fstat(fd, &context->stage) == -1)
    caml_unix_error(errno, "component record prepare stat", Nothing);
  if (!record_directory_same(&context->directory, &context->directory) ||
      !record_stage_same(&context->stage, &context->stage, 1) ||
      context->stage.st_size < 80 || context->stage.st_size > 1048656)
    caml_unix_error(EINVAL, "component record private stage", Nothing);
  if (fstatat(parent, context->temporary, &named, AT_SYMLINK_NOFOLLOW) == -1)
    caml_unix_error(errno, "component record stage name", Nothing);
  if (!record_stage_same(&context->stage, &named, 1))
    caml_unix_error(EBUSY, "component record stage binding", Nothing);
  if (fstatat(parent, context->target, &named, AT_SYMLINK_NOFOLLOW) == 0)
    caml_unix_error(EEXIST, "component record target exists", Nothing);
  if (errno != ENOENT) caml_unix_error(errno, "component record target lookup", Nothing);
  context->ready = 1;
  CAMLreturn(ticket);
#else
  caml_unix_error(ENOSYS, "component record publication", Nothing);
#endif
}

CAMLprim value unison_component_record_publication_publish(value ticket, value directory, value stage)
{
  CAMLparam3(ticket, directory, stage);
#ifdef __APPLE__
  caml_process_pending_actions();
  struct component_record_publication *context = RECORD_PUBLICATION(ticket);
  if (!context || !context->ready || context->published)
    caml_invalid_argument("component record publication state");
  int parent = unison_semantic_fd(directory, "component record directory FD");
  int fd = unison_semantic_fd(stage, "component record stage FD");
  int error = 0;
  const char *phase = "component record binding";
  struct stat observed, named;
  caml_enter_blocking_section_no_pending();
  if (fstat(parent, &observed) == -1) error = errno;
  else if (!record_directory_same(&context->directory, &observed)) error = EBUSY;
  else if (fstat(fd, &observed) == -1) error = errno;
  else if (!record_stage_same(&context->stage, &observed, 1)) error = EBUSY;
  else if (fstatat(parent, context->temporary, &named, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
  else if (!record_stage_same(&context->stage, &named, 1)) error = EBUSY;
  if (!error && fsync(fd) == -1) { error = errno; phase = "component record stage sync"; }
  if (!error && renameatx_np(parent, context->temporary, parent, context->target, RENAME_EXCL) == -1) {
    error = errno; phase = "component record exclusive rename";
  } else if (!error) {
    /* Persist the observed namespace effect before runtime reacquisition or
     * any post-rename error. Never infer it merely from a pathname later. */
    context->published = 1;
    phase = "component record published verification";
    if (fstat(fd, &observed) == -1 ||
        fstatat(parent, context->target, &named, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
    else if (!record_stage_same(&context->stage, &observed, 0) ||
             !record_stage_same(&observed, &named, 1)) error = EBUSY;
    if (!error && fsync(parent) == -1) { error = errno; phase = "component record directory sync"; }
  }
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, phase, Nothing);
  CAMLreturn(Val_unit);
#else
  caml_unix_error(ENOSYS, "component record publication", Nothing);
#endif
}

CAMLprim value unison_component_record_publication_published(value ticket)
{
  CAMLparam1(ticket);
#ifdef __APPLE__
  struct component_record_publication *context = RECORD_PUBLICATION(ticket);
  CAMLreturn(Val_bool(context && context->published));
#else
  caml_unix_error(ENOSYS, "component record publication", Nothing);
#endif
}

/* Monotonic cache-payload reservations. Empty private directory slots survive
 * failures; no FD is opened or closed and no slot/config is ever removed here. */
#ifdef __APPLE__
enum { COMPONENT_QUOTA_SLOTS = 4096, COMPONENT_QUOTA_CHARGE = 2097152 };
struct component_metadata_quota {
  struct stat directory, slot_identity, record_stage, entry_stage;
  char config[160], slot[64];
  int limit, attempted, reserved, ready_payload, stage_phase;
};
#define METADATA_QUOTA(v) (*(struct component_metadata_quota **)Data_custom_val(v))
static void metadata_quota_finalize(value v) { free(METADATA_QUOTA(v)); METADATA_QUOTA(v) = NULL; }
static struct custom_operations metadata_quota_ops = {
  .identifier = "unison.component-metadata-quota/0", .finalize = metadata_quota_finalize,
  .compare = custom_compare_default, .hash = custom_hash_default,
  .serialize = custom_serialize_default, .deserialize = custom_deserialize_default,
  .compare_ext = custom_compare_ext_default, .fixed_length = custom_fixed_length_default
};
static void metadata_slot_name(int index, char output[64])
{
  snprintf(output, 64, ".component-reservation-%04d", index);
}
static int metadata_config(struct component_metadata_quota *context, int directory, int create)
{
  const char *name = ".component-quota-v0";
  struct stat before, after;
  if (fstatat(directory, name, &before, AT_SYMLINK_NOFOLLOW) == -1) {
    if (errno != ENOENT || !create) return errno;
    /* A missing configuration never resets capacity over retained slots.
     * Cooperating managed owners never delete those slots. */
    for (int i = 0; i < COMPONENT_QUOTA_SLOTS; ++i) {
      char slot[64]; metadata_slot_name(i, slot);
      if (fstatat(directory, slot, &after, AT_SYMLINK_NOFOLLOW) == 0) return EBUSY;
      if (errno != ENOENT) return errno;
    }
    if (symlinkat(context->config, directory, name) == -1 && errno != EEXIST) return errno;
    if (fstatat(directory, name, &before, AT_SYMLINK_NOFOLLOW) == -1) return errno;
    if (fsync(directory) == -1) return errno;
  }
  if (!S_ISLNK(before.st_mode) || before.st_uid != getuid() || before.st_nlink != 1) return EINVAL;
  char contents[160];
  ssize_t count = readlinkat(directory, name, contents, sizeof(contents));
  if (count == -1) return errno;
  if ((size_t)count != strlen(context->config) || memcmp(contents, context->config, (size_t)count)) return EINVAL;
  if (fstatat(directory, name, &after, AT_SYMLINK_NOFOLLOW) == -1) return errno;
  if (before.st_dev != after.st_dev || before.st_ino != after.st_ino || before.st_mode != after.st_mode ||
      before.st_uid != after.st_uid || before.st_nlink != after.st_nlink ||
      before.st_ctimespec.tv_sec != after.st_ctimespec.tv_sec ||
      before.st_ctimespec.tv_nsec != after.st_ctimespec.tv_nsec) return EBUSY;
  return 0;
}
#endif

CAMLprim value unison_component_metadata_quota_prepare(value directory, value byte_limit, value entry_limit)
{
  CAMLparam3(directory, byte_limit, entry_limit); CAMLlocal1(ticket);
#ifdef __APPLE__
  caml_process_pending_actions();
  int64_t bytes = Int64_val(byte_limit); intnat entries = Long_val(entry_limit);
  if (bytes < COMPONENT_QUOTA_CHARGE || bytes > INT64_C(8589934592) ||
      entries < 1 || entries > COMPONENT_QUOTA_SLOTS) caml_invalid_argument("component metadata quota bounds");
  ticket = caml_alloc_custom(&metadata_quota_ops, sizeof(void *), 0, 1); METADATA_QUOTA(ticket) = NULL;
  struct component_metadata_quota *context = calloc(1, sizeof(*context));
  if (!context) caml_raise_out_of_memory(); METADATA_QUOTA(ticket) = context;
  context->limit = (int)(bytes / COMPONENT_QUOTA_CHARGE);
  if (context->limit > entries) context->limit = (int)entries;
  snprintf(context->config, sizeof(context->config), "unison-component-quota/0:bytes=%lld:entries=%ld:charge=2097152",
           (long long)bytes, (long)entries);
  int parent = unison_semantic_fd(directory, "component quota directory FD");
  if (fstat(parent, &context->directory) == -1) caml_unix_error(errno, "component quota directory", Nothing);
  if (!record_directory_same(&context->directory, &context->directory))
    caml_unix_error(EINVAL, "component quota private directory", Nothing);
  caml_enter_blocking_section_no_pending();
  int error = metadata_config(context, parent, 1);
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "component quota configuration", Nothing);
  CAMLreturn(ticket);
#else
  caml_unix_error(ENOSYS, "component metadata quota", Nothing);
#endif
}

CAMLprim value unison_component_metadata_quota_reserve(value ticket, value directory)
{
  CAMLparam2(ticket, directory);
#ifdef __APPLE__
  caml_process_pending_actions();
  struct component_metadata_quota *context = METADATA_QUOTA(ticket);
  if (!context || context->attempted) caml_invalid_argument("component quota attempt already consumed");
  int parent = unison_semantic_fd(directory, "component quota directory FD");
  context->attempted = 1;
  int error = 0; struct stat observed;
  caml_enter_blocking_section_no_pending();
  if (fstat(parent, &observed) == -1) error = errno;
  else if (!record_directory_same(&context->directory, &observed)) error = EBUSY;
  if (!error) error = metadata_config(context, parent, 0);
  for (int i = 0; !error && i < context->limit; ++i) {
    char name[64]; metadata_slot_name(i, name);
    if (mkdirat(parent, name, 0700) == 0) {
      strcpy(context->slot, name); context->reserved = 1;
      if (fstatat(parent, name, &observed, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
      else if (!S_ISDIR(observed.st_mode) || observed.st_uid != getuid() ||
               (observed.st_mode & 07777) != 0700) error = EBUSY;
      else context->slot_identity = observed;
      if (!error && fsync(parent) == -1) error = errno;
      if (!error) context->ready_payload = 1;
      break;
    }
    if (errno != EEXIST) { error = errno; break; }
    if (fstatat(parent, name, &observed, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
    else if (!S_ISDIR(observed.st_mode) || observed.st_uid != getuid() ||
             (observed.st_mode & 07777) != 0700) error = EINVAL;
  }
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "component quota reservation", Nothing);
  CAMLreturn(Val_bool(context->reserved));
#else
  caml_unix_error(ENOSYS, "component metadata quota", Nothing);
#endif
}

CAMLprim value unison_component_metadata_quota_reserved(value ticket)
{
  CAMLparam1(ticket);
#ifdef __APPLE__
  struct component_metadata_quota *context = METADATA_QUOTA(ticket);
  CAMLreturn(Val_bool(context && context->reserved));
#else
  caml_unix_error(ENOSYS, "component metadata quota", Nothing);
#endif
}

CAMLprim value unison_component_metadata_quota_slot(value ticket)
{
  CAMLparam1(ticket);
#ifdef __APPLE__
  struct component_metadata_quota *context = METADATA_QUOTA(ticket);
  if (!context || !context->reserved) caml_invalid_argument("component quota has no reserved slot");
  CAMLreturn(caml_copy_string(context->slot));
#else
  caml_unix_error(ENOSYS, "component metadata quota", Nothing);
#endif
}

CAMLprim value unison_component_metadata_stages(value ticket, value directory, value stages, value seal)
{
  CAMLparam4(ticket, directory, stages, seal);
#ifdef __APPLE__
  caml_process_pending_actions();
  struct component_metadata_quota *context = METADATA_QUOTA(ticket);
  int sealing = Bool_val(seal);
  if (!context || !context->ready_payload || context->stage_phase != (sealing ? 1 : 0))
    caml_invalid_argument("component quota staging state");
  int parent = unison_semantic_fd(directory, "component quota directory FD");
  int record_fd = unison_semantic_fd(Field(stages, 0), "component record stage FD");
  int entry_fd = unison_semantic_fd(Field(stages, 1), "component entry stage FD");
  char record_name[128], entry_name[128];
  snprintf(record_name, sizeof(record_name), "%s-record.tmp", context->slot);
  snprintf(entry_name, sizeof(entry_name), "%s-entry.tmp", context->slot);
  struct stat observed, record, entry, named;
  int error = 0;
  caml_enter_blocking_section_no_pending();
  if (fstat(parent, &observed) == -1) error = errno;
  else if (!record_directory_same(&context->directory, &observed)) error = EBUSY;
  if (!error) error = metadata_config(context, parent, 0);
  if (!error && fstatat(parent, context->slot, &observed, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
  if (!error && !record_directory_same(&context->slot_identity, &observed)) error = EBUSY;
  if (!error && (fstat(record_fd, &record) == -1 || fstat(entry_fd, &entry) == -1)) error = errno;
  if (!error && (!record_stage_same(&record, &record, 1) || !record_stage_same(&entry, &entry, 1) ||
      (record.st_dev == entry.st_dev && record.st_ino == entry.st_ino))) error = EINVAL;
  if (!error && !sealing && (record.st_size != 0 || entry.st_size != 0)) error = EINVAL;
  if (!error && sealing) {
    const struct stat *old_record = &context->record_stage, *old_entry = &context->entry_stage;
    if (record.st_dev != old_record->st_dev || record.st_ino != old_record->st_ino ||
        entry.st_dev != old_entry->st_dev || entry.st_ino != old_entry->st_ino ||
        record.st_mode != old_record->st_mode || entry.st_mode != old_entry->st_mode ||
        record.st_gid != old_record->st_gid || entry.st_gid != old_entry->st_gid ||
        record.st_flags != old_record->st_flags || entry.st_flags != old_entry->st_flags ||
        record.st_size < 80 || entry.st_size < 80 ||
        record.st_size > 1048656 || entry.st_size > 131072 ||
        record.st_size + entry.st_size > COMPONENT_QUOTA_CHARGE) error = EBUSY;
  }
  if (!error && fstatat(parent, record_name, &named, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
  if (!error && !record_stage_same(&record, &named, 1)) error = EBUSY;
  if (!error && fstatat(parent, entry_name, &named, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
  if (!error && !record_stage_same(&entry, &named, 1)) error = EBUSY;
  if (!error) {
    if (!sealing) { context->record_stage = record; context->entry_stage = entry; }
    context->stage_phase = sealing ? 2 : 1;
  }
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "component quota stage binding", Nothing);
  CAMLreturn(Val_unit);
#else
  caml_unix_error(ENOSYS, "component metadata stages", Nothing);
#endif
}

#ifdef __APPLE__
static void metadata_digest_leaf(value name, char output[256])
{
  record_leaf(name, output);
  if (strlen(output) != 64) caml_invalid_argument("component metadata digest leaf");
  for (int i = 0; i < 64; ++i)
    if (!((output[i] >= '0' && output[i] <= '9') || (output[i] >= 'a' && output[i] <= 'f')))
      caml_invalid_argument("component metadata digest leaf");
}
#endif

CAMLprim value unison_component_metadata_leaf_present(value directory, value name)
{
  CAMLparam2(directory, name);
#ifdef __APPLE__
  caml_process_pending_actions();
  char leaf[256]; metadata_digest_leaf(name, leaf);
  int parent = unison_semantic_fd(directory, "component metadata directory FD");
  struct stat before, after, named; int error = 0, present = 0;
  caml_enter_blocking_section_no_pending();
  if (fstat(parent, &before) == -1) error = errno;
  else if (!record_directory_same(&before, &before)) error = EINVAL;
  if (!error) {
    if (fstatat(parent, leaf, &named, AT_SYMLINK_NOFOLLOW) == 0) present = 1;
    else if (errno != ENOENT) error = errno;
  }
  if (!error && fstat(parent, &after) == -1) error = errno;
  if (!error && !record_directory_same(&before, &after)) error = EBUSY;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "component metadata leaf presence", Nothing);
  CAMLreturn(Val_bool(present));
#else
  caml_unix_error(ENOSYS, "component metadata lookup", Nothing);
#endif
}

CAMLprim value unison_component_metadata_leaf_check(value directory, value name, value limit, value descriptor)
{
  CAMLparam4(directory, name, limit, descriptor);
#ifdef __APPLE__
  caml_process_pending_actions();
  char leaf[256]; metadata_digest_leaf(name, leaf);
  intnat maximum = Long_val(limit);
  if (maximum < 80 || maximum > 1048656) caml_invalid_argument("component metadata leaf limit");
  int parent = unison_semantic_fd(directory, "component metadata directory FD");
  int fd = unison_semantic_fd(descriptor, "component metadata leaf FD");
  struct stat before, after, first, last, named; int error = 0;
  caml_enter_blocking_section_no_pending();
  if (fstat(parent, &before) == -1) error = errno;
  else if (!record_directory_same(&before, &before)) error = EINVAL;
  if (!error && fstat(fd, &first) == -1) error = errno;
  if (!error && (!record_stage_same(&first, &first, 1) || first.st_size < 80 || first.st_size > maximum)) error = EINVAL;
  if (!error && fstatat(parent, leaf, &named, AT_SYMLINK_NOFOLLOW) == -1) error = errno;
  if (!error && fstat(fd, &last) == -1) error = errno;
  if (!error && (!record_stage_same(&first, &last, 1) || !record_stage_same(&last, &named, 1))) error = EBUSY;
  if (!error && fstat(parent, &after) == -1) error = errno;
  if (!error && !record_directory_same(&before, &after)) error = EBUSY;
  caml_acquire_runtime_system();
  if (error) caml_unix_error(error, "component metadata leaf binding", Nothing);
  CAMLreturn(Val_unit);
#else
  caml_unix_error(ENOSYS, "component metadata lookup", Nothing);
#endif
}
