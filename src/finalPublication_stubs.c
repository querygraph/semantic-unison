/* Endpoint-local cooperative finalized-candidate publication. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/custom.h>
#include <caml/fail.h>
#include <caml/threads.h>
#include <caml/signals.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <errno.h>
#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#define caml_unix_code_of_unix_error code_of_unix_error
#endif

CAMLprim value unison_final_publication_errno_unavailable(value error)
{
  CAMLparam1(error);
#if defined(__APPLE__)
  int native_error = caml_unix_code_of_unix_error(error);
  CAMLreturn(Val_bool(native_error == ENODATA || native_error == ENOTSUP ||
                     native_error == EOPNOTSUPP || native_error == ENOSYS));
#else
  CAMLreturn(Val_false);
#endif
}

#if defined(__APPLE__)
#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/attr.h>
#include <sys/fcntl.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum final_phase { PREPARED, PRODUCING, ATTACHED, PUBLISHED, CLOSED };
struct directory_identity {
  dev_t device;
  ino_t inode;
  uint32_t flags;
  fsid_t filesystem;
  uint32_t mount_flags;
  unsigned char uuid[16];
};
struct publication_error { int number; const char *phase; };
struct final_context {
  pthread_mutex_t mutex;
  int mutex_ready;
  int root_fd, working_fd, candidate_parent_fd, target_parent_fd, witness_fd;
  char *logical_root, *working_dir, *candidate_path, *target_path;
  char *candidate_auxiliary, *target_auxiliary;
  char *quarantine_name;
  const char *candidate_parent, *candidate_name, *target_parent, *target_name;
  struct directory_identity root_identity, working_identity;
  struct directory_identity candidate_parent_identity, target_parent_identity;
  struct stat candidate_stat, target_stat, published_stat, producer_stat;
  int target_observed, target_exists, was_published, published_proven, check_apple_double;
  int producer_frozen;
  int producer_origin;
  enum final_phase phase;
};

static void record_error(struct publication_error *error, int number, const char *phase)
{
  if (error->number == 0) { error->number = number; error->phase = phase; }
}
static void close_slot(int *slot, struct publication_error *error, const char *phase)
{
  int fd = *slot;
  *slot = -1;
  if (fd >= 0 && close(fd) == -1 && error != NULL) record_error(error, errno, phase);
}
static void close_context(struct final_context *context, struct publication_error *error)
{
  context->phase = CLOSED;
  close_slot(&context->witness_fd, error, "final_publication.close.candidate");
  close_slot(&context->candidate_parent_fd, error, "final_publication.close.candidate_parent");
  close_slot(&context->target_parent_fd, error, "final_publication.close.target_parent");
  close_slot(&context->working_fd, error, "final_publication.close.working_directory");
  close_slot(&context->root_fd, error, "final_publication.close.logical_root");
  free(context->logical_root); context->logical_root = NULL;
  free(context->working_dir); context->working_dir = NULL;
  free(context->candidate_path); context->candidate_path = NULL;
  free(context->target_path); context->target_path = NULL;
  free(context->candidate_auxiliary); context->candidate_auxiliary = NULL;
  free(context->target_auxiliary); context->target_auxiliary = NULL;
  free(context->quarantine_name); context->quarantine_name = NULL;
  context->candidate_parent = context->candidate_name = NULL;
  context->target_parent = context->target_name = NULL;
}
static void finalize_publication(value handle)
{
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  if (context == NULL) return;
  /* Rooted calls retain this block; finalization cannot race a native call.
     Finalization closes only and never changes any filesystem name. */
  *(struct final_context **)Data_custom_val(handle) = NULL;
  close_context(context, NULL);
  if (context->mutex_ready) pthread_mutex_destroy(&context->mutex);
  free(context);
}
static struct custom_operations publication_operations = {
  .identifier = "unison.final_publication.local.v0",
  .finalize = finalize_publication,
  .compare = custom_compare_default,
  .hash = custom_hash_default,
  .serialize = custom_serialize_default,
  .deserialize = custom_deserialize_default,
  .compare_ext = custom_compare_ext_default,
  .fixed_length = custom_fixed_length_default
};
static int directory_open_flags(void)
{
#ifdef O_SEARCH
  return O_SEARCH | O_DIRECTORY | O_CLOEXEC;
#else
  return O_RDONLY | O_DIRECTORY | O_CLOEXEC;
#endif
}

/* Only native identity/constraints are fixed for a directory. Sibling entry
   operations may change size, nlink, mtime and ctime throughout the transfer. */
static int same_directory_stat(const struct stat *before, const struct stat *after)
{
  return S_ISDIR(before->st_mode) && S_ISDIR(after->st_mode) &&
    before->st_dev == after->st_dev && before->st_ino == after->st_ino &&
    before->st_flags == after->st_flags;
}
static int same_directory(const struct directory_identity *a, const struct directory_identity *b)
{
  return a->device == b->device && a->inode == b->inode && a->flags == b->flags &&
    a->filesystem.val[0] == b->filesystem.val[0] &&
    a->filesystem.val[1] == b->filesystem.val[1] &&
    a->mount_flags == b->mount_flags && memcmp(a->uuid, b->uuid, 16) == 0;
}

static int same_producer_stat(const struct stat *a, const struct stat *b)
{
  return S_ISREG(a->st_mode) && S_ISREG(b->st_mode) &&
    a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_nlink == 1 && b->st_nlink == 1;
}
static int identity_observe(int fd, int directory, struct directory_identity *identity)
{
  struct stat before, after;
  struct statfs filesystem;
  struct attrlist attributes;
  attribute_set_t returned;
  const size_t header = sizeof(uint32_t) + sizeof(attribute_set_t);
  unsigned char buffer[sizeof(uint32_t) + sizeof(attribute_set_t) + 16];
  uint32_t length;
  unsigned int i;
  int nonzero = 0;

  if (fstat(fd, &before) == -1) return errno;
  if (directory && !S_ISDIR(before.st_mode)) return ENOTDIR;
  if (!directory && (!S_ISREG(before.st_mode) || before.st_nlink != 1)) return EBUSY;
  if (fstatfs(fd, &filesystem) == -1) return errno;
  memset(&attributes, 0, sizeof(attributes));
  attributes.bitmapcount = ATTR_BIT_MAP_COUNT;
  attributes.commonattr = ATTR_CMN_RETURNED_ATTRS;
  attributes.volattr = ATTR_VOL_INFO | ATTR_VOL_UUID;
  memset(buffer, 0, sizeof(buffer));
  if (fgetattrlist(fd, &attributes, buffer, sizeof(buffer), FSOPT_REPORT_FULLSIZE) == -1)
    return errno;
  memcpy(&length, buffer, sizeof(length));
  if (length < header || length > sizeof(buffer)) return EPROTO;
  memcpy(&returned, buffer + sizeof(length), sizeof(returned));
  if (returned.commonattr != ATTR_CMN_RETURNED_ATTRS ||
      (returned.volattr & ~(ATTR_VOL_INFO | ATTR_VOL_UUID)) != 0 ||
      returned.dirattr != 0 || returned.fileattr != 0 || returned.forkattr != 0)
    return EPROTO;
  if (length != header + ((returned.volattr & ATTR_VOL_UUID) ? 16 : 0)) return EPROTO;
  if (!(returned.volattr & ATTR_VOL_UUID)) return ENODATA;
  memcpy(identity->uuid, buffer + header, 16);
  for (i = 0; i < 16; ++i) if (identity->uuid[i] != 0) nonzero = 1;
  if (!nonzero) return ENODATA;
  if (fstat(fd, &after) == -1) return errno;
  if (!(directory ? same_directory_stat(&before, &after) : same_producer_stat(&before, &after)))
    return EBUSY;
  identity->device = before.st_dev;
  identity->inode = before.st_ino;
  identity->flags = (uint32_t)before.st_flags;
  identity->filesystem = filesystem.f_fsid;
  identity->mount_flags = (uint32_t)filesystem.f_flags;
  return 0;
}
static int directory_observe(int fd, struct directory_identity *identity)
{
  return identity_observe(fd, 1, identity);
}
static int same_volume(const struct directory_identity *a, const struct directory_identity *b)
{
  return a->device == b->device &&
    a->filesystem.val[0] == b->filesystem.val[0] &&
    a->filesystem.val[1] == b->filesystem.val[1] &&
    a->mount_flags == b->mount_flags && memcmp(a->uuid, b->uuid, 16) == 0;
}


/* All stable Darwin stat facts are compared explicitly, avoiding padding and
   narrow OCaml integer/float conversions. Reads may legitimately change atime. */
static int same_file(const struct stat *a, const struct stat *b)
{
  return a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_mode == b->st_mode && a->st_nlink == b->st_nlink &&
    a->st_uid == b->st_uid && a->st_gid == b->st_gid && a->st_rdev == b->st_rdev &&
    a->st_size == b->st_size && a->st_blocks == b->st_blocks &&
    a->st_blksize == b->st_blksize && a->st_flags == b->st_flags && a->st_gen == b->st_gen &&
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
    a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec &&
    a->st_birthtimespec.tv_sec == b->st_birthtimespec.tv_sec &&
    a->st_birthtimespec.tv_nsec == b->st_birthtimespec.tv_nsec;
}
static int observe_expected_directory(int fd, const struct directory_identity *expected)
{
  struct directory_identity observed;
  int error = directory_observe(fd, &observed);
  return error != 0 ? error : same_directory(expected, &observed) ? 0 : EBUSY;
}
static int probe_path(int parent, const char *path, const struct directory_identity *expected)
{
  int fd = openat(parent, path, directory_open_flags());
  int error;
  if (fd < 0) return errno;
  error = observe_expected_directory(fd, expected);
  if (close(fd) == -1 && error == 0) error = errno;
  return error;
}
static void check_bindings(struct final_context *context, struct publication_error *error)
{
  int number;
#define BINDING(expression, phase) do { number = (expression); \
  if (number != 0) { record_error(error, number, phase); return; } } while (0)
  BINDING(probe_path(AT_FDCWD, context->logical_root, &context->root_identity),
          "final_publication.binding.logical_root");
  BINDING(observe_expected_directory(context->root_fd, &context->root_identity),
          "final_publication.binding.held_logical_root");
  BINDING(probe_path(AT_FDCWD, context->working_dir, &context->working_identity),
          "final_publication.binding.working_directory");
  BINDING(observe_expected_directory(context->working_fd, &context->working_identity),
          "final_publication.binding.held_working_directory");
  BINDING(probe_path(context->working_fd, context->candidate_parent, &context->candidate_parent_identity),
          "final_publication.binding.candidate_parent");
  BINDING(observe_expected_directory(context->candidate_parent_fd, &context->candidate_parent_identity),
          "final_publication.binding.held_candidate_parent");
  BINDING(probe_path(context->working_fd, context->target_parent, &context->target_parent_identity),
          "final_publication.binding.target_parent");
  BINDING(observe_expected_directory(context->target_parent_fd, &context->target_parent_identity),
          "final_publication.binding.held_target_parent");
#undef BINDING
}
static int candidate_matches(struct final_context *context, int require_baseline)
{
  struct stat before, named, after;
  if (fstat(context->witness_fd, &before) == -1) return errno;
  if (!S_ISREG(before.st_mode) || before.st_nlink != 1) return EBUSY;
  if (fstatat(context->candidate_parent_fd, context->candidate_name, &named, AT_SYMLINK_NOFOLLOW) == -1)
    return errno;
  if (fstat(context->witness_fd, &after) == -1) return errno;
  if (!same_file(&before, &named) || !same_file(&before, &after)) return EBUSY;
  if (require_baseline && !same_file(&context->candidate_stat, &before)) return EBUSY;
  return 0;
}
static int producer_matches(struct final_context *context)
{
  struct stat before, named, after;
  struct directory_identity volume;
  int number;
  if (fstat(context->witness_fd, &before) == -1) return errno;
  if (!same_producer_stat(&context->producer_stat, &before)) return EBUSY;
  if (fstatat(context->candidate_parent_fd, context->candidate_name, &named, AT_SYMLINK_NOFOLLOW) == -1)
    return errno;
  if (fstat(context->witness_fd, &after) == -1) return errno;
  if (!same_producer_stat(&before, &named) || !same_producer_stat(&before, &after)) return EBUSY;
  number = identity_observe(context->witness_fd, 0, &volume);
  if (number != 0) return number;
  return same_volume(&volume, &context->candidate_parent_identity) ? 0 : EBUSY;
}
static int auxiliary_absent(struct final_context *context, struct publication_error *error)
{
  struct stat observed;
  if (!context->check_apple_double) return 1;
  if (fstatat(context->candidate_parent_fd, context->candidate_auxiliary, &observed,
              AT_SYMLINK_NOFOLLOW) == 0) return 0;
  if (errno != ENOENT) {
    record_error(error, errno, "final_publication.auxiliary.candidate_lookup"); return 0;
  }
  if (fstatat(context->target_parent_fd, context->target_auxiliary, &observed,
              AT_SYMLINK_NOFOLLOW) == 0) return 0;
  if (errno != ENOENT) {
    record_error(error, errno, "final_publication.auxiliary.target_lookup"); return 0;
  }
  return 1;
}
static void check_auxiliary(struct final_context *context, struct publication_error *error)
{
  if (!auxiliary_absent(context, error) && error->number == 0)
    record_error(error, EOPNOTSUPP, "final_publication.auxiliary.present");
}
static void check_candidate(struct final_context *context, struct publication_error *error)
{
  int number;
  if (context->phase != ATTACHED) {
    record_error(error, EINVAL, "final_publication.check.candidate_state"); return;
  }
  check_bindings(context, error);
  if (error->number != 0) return;
  check_auxiliary(context, error);
  if (error->number != 0) return;
  number = candidate_matches(context, 1);
  if (number != 0) record_error(error, number, "final_publication.check.candidate");
}
static void check_producer(struct final_context *context, struct publication_error *error)
{
  int number;
  if (context->phase != PRODUCING) {
    record_error(error, EINVAL, "final_publication.check.producer_state"); return;
  }
  check_bindings(context, error);
  if (error->number != 0) return;
  number = producer_matches(context);
  if (number != 0) record_error(error, number, "final_publication.check.producer");
}
static void check_target(struct final_context *context, struct publication_error *error)
{
  struct stat observed;
  if (!context->target_observed) {
    record_error(error, EINVAL, "final_publication.check.target_state"); return;
  }
  if (fstatat(context->target_parent_fd, context->target_name, &observed, AT_SYMLINK_NOFOLLOW) == -1) {
    if (errno == ENOENT) {
      if (context->target_exists) record_error(error, EBUSY, "final_publication.check.target_disappeared");
    } else record_error(error, errno, "final_publication.check.target_lookup");
    return;
  }
  if (!context->target_exists || !same_file(&context->target_stat, &observed))
    record_error(error, EBUSY, "final_publication.check.target");
}
static int current_candidate_matches(struct final_context *context)
{
  struct stat before, named, after;
  /* Cleanup uses current witness identity, allowing a failed late property or
     data mutation and preserving any foreign replacement/hardlink. */
  if (fstat(context->witness_fd, &before) == -1) return errno;
  if (!S_ISREG(before.st_mode)) return EBUSY;
  if (fstatat(context->candidate_parent_fd, context->candidate_name, &named, AT_SYMLINK_NOFOLLOW) == -1)
    return errno;
  if (fstat(context->witness_fd, &after) == -1) return errno;
  return same_file(&before, &named) && same_file(&before, &after) ? 0 : EBUSY;
}
static void cleanup_owned(struct final_context *context, struct publication_error *error)
{
  int number;
  if ((context->phase != PRODUCING && context->phase != ATTACHED) || context->was_published) return;
  number = current_candidate_matches(context);
  if (number == ENOENT) return;
  if (number == 0 && unlinkat(context->candidate_parent_fd, context->candidate_name, 0) == -1)
    number = errno;
  if (number != 0) record_error(error, number, "final_publication.cleanup.candidate");
}
static void split_relative(char *path, const char **parent, const char **name)
{
  char *slash = strrchr(path, '/');
  if (slash == NULL) { *parent = "."; *name = path; }
  else { *slash = '\0'; *parent = path; *name = slash + 1; }
}
static void raise_error(struct publication_error error)
{
  if (error.number != 0) caml_unix_error(error.number, error.phase, Nothing);
}
static int enter_context(struct final_context *context, struct publication_error *error, const char *phase)
{
  int number = pthread_mutex_lock(&context->mutex);
  if (number != 0) { record_error(error, number, phase); return 0; }
  return 1;
}

CAMLprim value unison_final_publication_available(value unit)
{
  CAMLparam1(unit);
  if (__builtin_available(macOS 10.12, *)) CAMLreturn(Val_true);
  CAMLreturn(Val_false);
}
CAMLprim value unison_final_publication_prepare(value root, value working, value candidate, value target, value auxiliary)
{
  CAMLparam5(root, working, candidate, target, auxiliary);
  CAMLlocal1(handle);
  struct final_context *context;
  struct publication_error error = { 0, NULL };
  int number;
  if (__builtin_available(macOS 10.12, *)) {} else
    caml_unix_error(ENOSYS, "final_publication.platform", Nothing);
  handle = caml_alloc_custom(&publication_operations, sizeof(context), sizeof(*context) +
    caml_string_length(root) + caml_string_length(working) + caml_string_length(candidate) +
    caml_string_length(target) + caml_string_length(candidate) + caml_string_length(target) + 10, 1024 * 1024);
  *(struct final_context **)Data_custom_val(handle) = NULL;
  context = calloc(1, sizeof(*context));
  if (context == NULL) caml_raise_out_of_memory();
  context->root_fd = context->working_fd = context->candidate_parent_fd = -1;
  context->target_parent_fd = context->witness_fd = -1;
  context->phase = PREPARED;
  context->check_apple_double = Bool_val(auxiliary);
  *(struct final_context **)Data_custom_val(handle) = context;
  number = pthread_mutex_init(&context->mutex, NULL);
  if (number != 0) caml_unix_error(number, "final_publication.prepare.mutex", Nothing);
  context->mutex_ready = 1;
  context->logical_root = strdup(String_val(root));
  context->working_dir = strdup(String_val(working));
  context->candidate_path = strdup(String_val(candidate));
  context->target_path = strdup(String_val(target));
  if (!context->logical_root || !context->working_dir || !context->candidate_path || !context->target_path) {
    close_context(context, NULL);
    caml_unix_error(ENOMEM, "final_publication.prepare.paths", Nothing);
  }
  split_relative(context->candidate_path, &context->candidate_parent, &context->candidate_name);
  split_relative(context->target_path, &context->target_parent, &context->target_name);
  context->candidate_auxiliary = malloc(strlen(context->candidate_name) + 3);
  context->target_auxiliary = malloc(strlen(context->target_name) + 3);
  if (!context->candidate_auxiliary || !context->target_auxiliary) {
    close_context(context, NULL);
    caml_unix_error(ENOMEM, "final_publication.prepare.auxiliary_names", Nothing);
  }
  strcpy(context->candidate_auxiliary, "._"); strcat(context->candidate_auxiliary, context->candidate_name);
  strcpy(context->target_auxiliary, "._"); strcat(context->target_auxiliary, context->target_name);
  caml_enter_blocking_section_no_pending();
#define PREPARE_OPEN(slot, expression, phase) do { context->slot = (expression); \
  if (context->slot < 0) { record_error(&error, errno, phase); goto prepared; } } while (0)
#define PREPARE_ID(slot, id, phase) do { number = directory_observe(context->slot, &context->id); \
  if (number != 0) { record_error(&error, number, phase); goto prepared; } } while (0)
  PREPARE_OPEN(root_fd, open(context->logical_root, directory_open_flags()), "final_publication.prepare.logical_root");
  PREPARE_ID(root_fd, root_identity, "final_publication.prepare.root_identity");
  PREPARE_OPEN(working_fd, open(context->working_dir, directory_open_flags()), "final_publication.prepare.working_directory");
  PREPARE_ID(working_fd, working_identity, "final_publication.prepare.working_identity");
  PREPARE_OPEN(candidate_parent_fd, openat(context->working_fd, context->candidate_parent, directory_open_flags()),
               "final_publication.prepare.candidate_parent");
  PREPARE_ID(candidate_parent_fd, candidate_parent_identity, "final_publication.prepare.candidate_identity");
  PREPARE_OPEN(target_parent_fd, openat(context->working_fd, context->target_parent, directory_open_flags()),
               "final_publication.prepare.target_parent");
  PREPARE_ID(target_parent_fd, target_parent_identity, "final_publication.prepare.target_identity");
  if (same_directory(&context->candidate_parent_identity, &context->target_parent_identity) &&
      strcmp(context->candidate_name, context->target_name) == 0)
    record_error(&error, EINVAL, "final_publication.prepare.aliased_names");
prepared:
  if (error.number != 0) close_context(context, &error);
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(handle);
#undef PREPARE_OPEN
#undef PREPARE_ID
}
CAMLprim value unison_final_publication_auxiliary_absent(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int absent = 0;
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.auxiliary.lock")) {
    if (context->phase == CLOSED)
      record_error(&error, EINVAL, "final_publication.auxiliary.state");
    else {
      check_bindings(context, &error);
      if (error.number == 0) absent = auxiliary_absent(context, &error);
    }
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_bool(absent));
}
CAMLprim value unison_final_publication_resolution(value handle, value working, value target)
{
  CAMLparam3(handle, working, target);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  char *working_copy = strdup(String_val(working)), *target_copy = strdup(String_val(target));
  const char *parent, *name;
  int number, fresh = -1;
  if (!working_copy || !target_copy) {
    free(working_copy); free(target_copy);
    caml_raise_out_of_memory();
  }
  split_relative(target_copy, &parent, &name);
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.resolution.lock")) goto resolution_unlocked;
  if (context->phase == CLOSED) {
    record_error(&error, EINVAL, "final_publication.resolution.state"); goto resolution;
  }
  check_bindings(context, &error);
  if (error.number != 0) goto resolution;
  if (strcmp(name, context->target_name) != 0) {
    record_error(&error, EBUSY, "final_publication.resolution.target_name"); goto resolution;
  }
  fresh = open(working_copy, directory_open_flags());
  if (fresh < 0) { record_error(&error, errno, "final_publication.resolution.working_directory"); goto resolution; }
  number = observe_expected_directory(fresh, &context->working_identity);
  if (number != 0) { record_error(&error, number, "final_publication.resolution.working_identity"); goto resolution; }
  number = probe_path(fresh, parent, &context->target_parent_identity);
  if (number != 0) record_error(&error, number, "final_publication.resolution.target_parent");
resolution:
  close_slot(&fresh, &error, "final_publication.resolution.close_working");
  pthread_mutex_unlock(&context->mutex);
resolution_unlocked:
  free(working_copy); free(target_copy);
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
static void adopt_producer(struct final_context *context, int borrowed, int resume,
                           struct publication_error *error)
{
  int number;
  if (context->phase != PREPARED) {
    record_error(error, EINVAL, resume ? "final_publication.adopt_resume.state" :
      "final_publication.adopt_mutable.state"); return;
  }
  check_bindings(context, error);
  if (error->number != 0) goto adoption_failed;
  check_auxiliary(context, error);
  if (error->number != 0) goto adoption_failed;
  if (resume)
    context->witness_fd = openat(context->candidate_parent_fd, context->candidate_name,
                                O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
  else
    context->witness_fd = fcntl(borrowed, F_DUPFD_CLOEXEC, 0);
  if (context->witness_fd < 0) {
    record_error(error, errno, resume ? "final_publication.adopt_resume.open" :
      "final_publication.adopt_mutable.duplicate"); goto adoption_failed;
  }
  if (fstat(context->witness_fd, &context->producer_stat) == -1) {
    record_error(error, errno, resume ? "final_publication.adopt_resume.producer_stat" :
      "final_publication.adopt_mutable.producer_stat"); goto adoption_failed;
  }
  number = producer_matches(context);
  if (number != 0) {
    record_error(error, number, resume ? "final_publication.adopt_resume.producer" :
      "final_publication.adopt_mutable.producer"); goto adoption_failed;
  }
  check_bindings(context, error);
  if (error->number != 0) goto adoption_failed;
  /* The already rooted native owner retains the actual output before the
     caller can close its original channel or disarm its stage owner. */
  context->producer_origin = resume ? 2 : 1;
  context->phase = PRODUCING;
  return;
adoption_failed:
  /* No candidate name was admitted. In particular, a same-byte replacement
     is never unlinked or retried by opening its saved normal pathname. */
  close_context(context, error);
}
CAMLprim value unison_final_publication_adopt_mutable(value handle, value candidate)
{
  CAMLparam2(handle, candidate);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int borrowed = Int_val(candidate);
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.adopt_mutable.lock")) {
    adopt_producer(context, borrowed, 0, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_adopt_resume(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.adopt_resume.lock")) {
    adopt_producer(context, -1, 1, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_producer_origin(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int origin = 0;
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.producer_origin.lock")) {
    origin = context->producer_origin;
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_int(origin));
}
CAMLprim value unison_final_publication_check_producer(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.check_producer.lock")) {
    check_producer(context, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_check_handoff(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.check_handoff.lock")) {
    switch (context->phase) {
    case PREPARED: check_bindings(context, &error); break;
    case PRODUCING: check_producer(context, &error); break;
    case ATTACHED: check_candidate(context, &error); break;
    case PUBLISHED:
    case CLOSED: record_error(&error, EINVAL, "final_publication.check_handoff.state"); break;
    }
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_check_producer_fd(value handle, value candidate)
{
  CAMLparam2(handle, candidate);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  struct stat before, named, after;
  struct directory_identity volume;
  int borrowed = Int_val(candidate), number;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.check_producer_fd.lock")) goto writer_unlocked;
  check_producer(context, &error);
  if (error.number != 0) goto writer;
  if (fstat(borrowed, &before) == -1) {
    record_error(&error, errno, "final_publication.check_producer_fd.writer"); goto writer;
  }
  if (!same_producer_stat(&context->producer_stat, &before)) {
    record_error(&error, EBUSY, "final_publication.check_producer_fd.identity"); goto writer;
  }
  if (fstatat(context->candidate_parent_fd, context->candidate_name, &named, AT_SYMLINK_NOFOLLOW) == -1) {
    record_error(&error, errno, "final_publication.check_producer_fd.name"); goto writer;
  }
  if (fstat(borrowed, &after) == -1) {
    record_error(&error, errno, "final_publication.check_producer_fd.recheck"); goto writer;
  }
  if (!same_producer_stat(&before, &named) || !same_producer_stat(&before, &after)) {
    record_error(&error, EBUSY, "final_publication.check_producer_fd.changed"); goto writer;
  }
  number = identity_observe(borrowed, 0, &volume);
  if (number != 0) { record_error(&error, number, "final_publication.check_producer_fd.volume"); goto writer; }
  if (!same_volume(&volume, &context->candidate_parent_identity)) {
    record_error(&error, EBUSY, "final_publication.check_producer_fd.volume_identity"); goto writer;
  }
  check_producer(context, &error);
writer:
  pthread_mutex_unlock(&context->mutex);
writer_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_freeze_producer(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int number;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.freeze_producer.lock")) goto frozen_unlocked;
  check_producer(context, &error);
  if (error.number != 0) goto frozen;
  check_auxiliary(context, &error);
  if (error.number != 0) goto frozen;
  if (fstat(context->witness_fd, &context->candidate_stat) == -1) {
    record_error(&error, errno, "final_publication.freeze_producer.baseline"); goto frozen;
  }
  number = candidate_matches(context, 1);
  if (number != 0) { record_error(&error, number, "final_publication.freeze_producer.candidate"); goto frozen; }
  check_bindings(context, &error);
  if (error.number != 0) goto frozen;
  check_auxiliary(context, &error);
  if (error.number != 0) goto frozen;
  context->producer_frozen = 1;
  context->phase = ATTACHED;
frozen:
  pthread_mutex_unlock(&context->mutex);
frozen_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_producer_finalized(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int result = 0;
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.producer_finalized.lock")) {
    result = context->producer_frozen;
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_bool(result));
}
CAMLprim value unison_final_publication_attach(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int number;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.attach.lock")) goto attached_unlocked;
  if (context->phase != PREPARED) { record_error(&error, EINVAL, "final_publication.attach.state"); goto attached; }
  check_bindings(context, &error);
  if (error.number != 0) goto attached;
  check_auxiliary(context, &error);
  if (error.number != 0) goto attached;
  context->witness_fd = openat(context->candidate_parent_fd, context->candidate_name,
                              O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
  if (context->witness_fd < 0) { record_error(&error, errno, "final_publication.attach.open_candidate"); goto attached; }
  number = candidate_matches(context, 0);
  if (number != 0) { record_error(&error, number, "final_publication.attach.candidate"); goto attach_failed; }
  if (fstat(context->witness_fd, &context->candidate_stat) == -1) {
    record_error(&error, errno, "final_publication.attach.candidate_stat"); goto attach_failed;
  }
  number = candidate_matches(context, 1);
  if (number != 0) { record_error(&error, number, "final_publication.attach.candidate_baseline"); goto attach_failed; }
  check_bindings(context, &error);
  if (error.number != 0) goto attach_failed;
  context->phase = ATTACHED;
  goto attached;
attach_failed:
  /* Candidate ownership begins only after every proof above succeeds. */
  close_slot(&context->witness_fd, &error, "final_publication.attach.close_candidate");
attached:
  pthread_mutex_unlock(&context->mutex);
attached_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_check_candidate(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.check_candidate.lock")) {
    check_candidate(context, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_observe_target(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  struct stat after;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.observe_target.lock")) goto observed_unlocked;
  if (context->target_observed) { record_error(&error, EINVAL, "final_publication.observe_target.state"); goto observed; }
  check_candidate(context, &error);
  if (error.number != 0) goto observed;
  if (fstatat(context->target_parent_fd, context->target_name, &context->target_stat, AT_SYMLINK_NOFOLLOW) == -1) {
    if (errno != ENOENT) { record_error(&error, errno, "final_publication.observe_target.lookup"); goto observed; }
    context->target_exists = 0;
  } else {
    if (!S_ISREG(context->target_stat.st_mode) && !S_ISLNK(context->target_stat.st_mode)) {
      record_error(&error, EOPNOTSUPP, "final_publication.observe_target.kind"); goto observed;
    }
    if (fstatat(context->target_parent_fd, context->target_name, &after, AT_SYMLINK_NOFOLLOW) == -1) {
      record_error(&error, errno, "final_publication.observe_target.recheck"); goto observed;
    }
    if (!same_file(&context->target_stat, &after)) {
      record_error(&error, EBUSY, "final_publication.observe_target.changed"); goto observed;
    }
    context->target_exists = 1;
  }
  context->target_observed = 1;
observed:
  pthread_mutex_unlock(&context->mutex);
observed_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_check(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.check.lock")) {
    check_candidate(context, &error);
    if (error.number == 0) check_target(context, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_publish(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int result;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.publish.lock")) goto published_unlocked;
  check_candidate(context, &error);
  if (error.number != 0) goto published;
  check_target(context, &error);
  if (error.number != 0) goto published;
  check_auxiliary(context, &error);
  if (error.number != 0) goto published;
  if (context->target_exists)
    result = renameat(context->candidate_parent_fd, context->candidate_name,
                      context->target_parent_fd, context->target_name);
  else
    result = renameatx_np(context->candidate_parent_fd, context->candidate_name,
                         context->target_parent_fd, context->target_name, RENAME_EXCL);
  if (result == -1) record_error(&error, errno, "final_publication.publish.rename");
  else {
    context->phase = PUBLISHED;
    context->was_published = 1;
    /* Rename succeeded before any following observation or error. A missing
       post-rename proof must never make abort unlink the live target. */
    if (fstat(context->witness_fd, &context->published_stat) == -1)
      record_error(&error, errno, "final_publication.publish.result_stat");
    else {
      struct stat before = context->candidate_stat;
      before.st_ctimespec = context->published_stat.st_ctimespec;
      if (!same_file(&before, &context->published_stat))
        record_error(&error, EBUSY, "final_publication.publish.result_changed");
      else context->published_proven = 1;
    }
  }
published:
  pthread_mutex_unlock(&context->mutex);
published_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_check_published(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  struct stat before, named, after;
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.check_published.lock")) goto checked_unlocked;
  if (context->phase != PUBLISHED || !context->published_proven) {
    record_error(&error, EBUSY, "final_publication.check_published.state"); goto checked;
  }
  check_bindings(context, &error);
  if (error.number != 0) goto checked;
  check_auxiliary(context, &error);
  if (error.number != 0) goto checked;
  if (fstat(context->witness_fd, &before) == -1) {
    record_error(&error, errno, "final_publication.check_published.witness"); goto checked;
  }
  if (fstatat(context->target_parent_fd, context->target_name, &named, AT_SYMLINK_NOFOLLOW) == -1) {
    record_error(&error, errno, "final_publication.check_published.target"); goto checked;
  }
  if (fstat(context->witness_fd, &after) == -1) {
    record_error(&error, errno, "final_publication.check_published.recheck"); goto checked;
  }
  if (!same_file(&context->published_stat, &before) || !same_file(&before, &named) ||
      !same_file(&before, &after))
    record_error(&error, EBUSY, "final_publication.check_published.changed");
checked:
  pthread_mutex_unlock(&context->mutex);
checked_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_published(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int result = 0;
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.published.lock")) {
    result = context->was_published;
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_bool(result));
}
CAMLprim value unison_final_publication_release(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.release.lock")) {
    close_context(context, NULL);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_abort(value handle)
{
  CAMLparam1(handle);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  caml_enter_blocking_section_no_pending();
  if (enter_context(context, &error, "final_publication.abort.lock")) {
    cleanup_owned(context, &error);
    close_context(context, &error);
    pthread_mutex_unlock(&context->mutex);
  }
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
CAMLprim value unison_final_publication_quarantine(value handle, value name)
{
  CAMLparam2(handle, name);
  struct final_context *context = *(struct final_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  char *incoming_name = strdup(String_val(name));
  int number;
  if (incoming_name == NULL) caml_raise_out_of_memory();
  caml_enter_blocking_section_no_pending();
  if (!enter_context(context, &error, "final_publication.quarantine.lock")) goto quarantined_unlocked;
  if ((context->phase == PRODUCING || context->phase == ATTACHED) && !context->was_published) {
    if (strcmp(incoming_name, context->candidate_name) == 0 || strcmp(incoming_name, context->target_name) == 0)
      record_error(&error, EINVAL, "final_publication.quarantine.name");
    else {
      number = current_candidate_matches(context);
      if (number != 0 && number != ENOENT)
        record_error(&error, number, "final_publication.quarantine.candidate");
      else if (number == 0) {
        if (renameatx_np(context->candidate_parent_fd, context->candidate_name,
                        context->candidate_parent_fd, incoming_name, RENAME_EXCL) == -1)
          record_error(&error, errno, "final_publication.quarantine.rename");
        else {
          /* The quarantine is owned before any post-rename probe or pending
             exception can fail. Cleanup follows the captured parent/name. */
          context->quarantine_name = incoming_name;
          incoming_name = NULL;
          context->candidate_name = context->quarantine_name;
          cleanup_owned(context, &error);
        }
      }
    }
  }
  /* No original-name unlink if quarantine itself failed, and no published
     live-name changes under any failure or repeated cleanup call. */
  close_context(context, &error);
  pthread_mutex_unlock(&context->mutex);
quarantined_unlocked:
  free(incoming_name);
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}
#else
CAMLprim value unison_final_publication_available(value unit)
{
  CAMLparam1(unit);
  CAMLreturn(Val_false);
}
#define UNISON_FINAL_UNAVAILABLE(name, params, roots) \
  CAMLprim value name params { roots; \
    caml_unix_error(ENOSYS, "final_publication.platform", Nothing); \
    CAMLreturn(Val_unit); }
UNISON_FINAL_UNAVAILABLE(unison_final_publication_prepare,
  (value root, value work, value candidate, value target, value auxiliary), CAMLparam5(root, work, candidate, target, auxiliary))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_auxiliary_absent, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_resolution,
  (value handle, value work, value target), CAMLparam3(handle, work, target))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_attach, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_adopt_mutable, (value handle, value candidate), CAMLparam2(handle, candidate))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_adopt_resume, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_producer_origin, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check_handoff, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check_producer, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check_producer_fd, (value handle, value candidate), CAMLparam2(handle, candidate))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_freeze_producer, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_producer_finalized, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check_candidate, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_observe_target, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_publish, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_check_published, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_published, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_release, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_abort, (value handle), CAMLparam1(handle))
UNISON_FINAL_UNAVAILABLE(unison_final_publication_quarantine, (value handle, value name), CAMLparam2(handle, name))
#endif
