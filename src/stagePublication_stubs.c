/* Endpoint-owned, cooperative private-stage publication. */
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

CAMLprim value unison_stage_publication_errno_unavailable(value error)
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

enum publication_phase { PREPARED, STAGE_OWNED, TEMP_OWNED, DISARMED, CLOSED };
struct directory_identity {
  dev_t device;
  ino_t inode;
  uint32_t flags;
  fsid_t filesystem;
  uint32_t mount_flags;
  unsigned char uuid[16];
};
struct publication_error { int number; const char *phase; };
struct publication_context {
  pthread_mutex_t mutex;
  int mutex_ready;
  int root_fd, expected_stage_parent_fd, temporary_parent_fd;
  int actual_stage_parent_fd, witness_fd;
  char *working_dir, *stage_path, *temporary_path;
  const char *stage_parent, *stage_name, *temporary_parent, *temporary_name;
  struct directory_identity root_identity, stage_parent_identity, temporary_parent_identity;
  enum publication_phase phase;
};

static void record_error(struct publication_error *error, int number, const char *phase)
{
  if (error->number == 0) { error->number = number; error->phase = phase; }
}

/* Clear ownership before close; an error never causes a reused integer to be
   closed again. Always attempt the remaining descriptors. */
static void close_slot(int *slot, struct publication_error *error, const char *phase)
{
  int fd = *slot;
  *slot = -1;
  if (fd >= 0 && close(fd) == -1 && error != NULL) record_error(error, errno, phase);
}
static void close_context(struct publication_context *context, struct publication_error *error)
{
  context->phase = CLOSED;
  close_slot(&context->witness_fd, error, "stage_publication.close.witness");
  close_slot(&context->actual_stage_parent_fd, error, "stage_publication.close.actual_parent");
  close_slot(&context->expected_stage_parent_fd, error, "stage_publication.close.expected_parent");
  close_slot(&context->temporary_parent_fd, error, "stage_publication.close.temporary_parent");
  close_slot(&context->root_fd, error, "stage_publication.close.working_directory");
  free(context->working_dir); context->working_dir = NULL;
  free(context->stage_path); context->stage_path = NULL;
  free(context->temporary_path); context->temporary_path = NULL;
  context->stage_parent = context->stage_name = NULL;
  context->temporary_parent = context->temporary_name = NULL;
}

static void finalize_publication(value handle)
{
  struct publication_context *context = *(struct publication_context **)Data_custom_val(handle);
  if (context == NULL) return;
  /* Rooted calls retain the custom block, so finalization cannot race them.
     Finalizers close handles only: no unlink using any saved name. */
  *(struct publication_context **)Data_custom_val(handle) = NULL;
  close_context(context, NULL);
  if (context->mutex_ready) pthread_mutex_destroy(&context->mutex);
  free(context);
}

static struct custom_operations publication_operations = {
  .identifier = "unison.stage_publication.local.v0",
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

static int directory_observe(int fd, struct directory_identity *identity)
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
  if (!S_ISDIR(before.st_mode)) return ENOTDIR;
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
  if (!same_directory_stat(&before, &after)) return EBUSY;
  identity->device = before.st_dev;
  identity->inode = before.st_ino;
  identity->flags = (uint32_t)before.st_flags;
  identity->filesystem = filesystem.f_fsid;
  identity->mount_flags = (uint32_t)filesystem.f_flags;
  return 0;
}

static int same_file(const struct stat *a, const struct stat *b)
{
  return S_ISREG(a->st_mode) && S_ISREG(b->st_mode) &&
    a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    a->st_size == b->st_size && a->st_nlink == b->st_nlink && a->st_flags == b->st_flags &&
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
    a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec;
}

static int name_matches_witness(int parent, const char *name, int witness, int require_single_link)
{
  struct stat before, named, after;
  if (fstat(witness, &before) == -1) return errno;
  if (!S_ISREG(before.st_mode)) return EINVAL;
  if (fstatat(parent, name, &named, AT_SYMLINK_NOFOLLOW) == -1) return errno;
  if (fstat(witness, &after) == -1) return errno;
  if (!same_file(&before, &named) || !same_file(&before, &after)) return EBUSY;
  return require_single_link && before.st_nlink != 1 ? EBUSY : 0;
}

static int remove_owned_name(int parent, const char *name, int witness)
{
  /* A later foreign hardlink prevents private-stage admission, but removing
     this identity-bound owned leaf leaves that foreign link untouched. */
  int error = name_matches_witness(parent, name, witness, 0);
  if (error == ENOENT) return 0;
  if (error != 0) return error;
  if (unlinkat(parent, name, 0) == -1) return errno;
  return 0;
}

static void cleanup_owned(struct publication_context *context, struct publication_error *error)
{
  int number = 0;
  if (context->phase == STAGE_OWNED)
    number = remove_owned_name(context->actual_stage_parent_fd, context->stage_name, context->witness_fd);
  else if (context->phase == TEMP_OWNED)
    number = remove_owned_name(context->temporary_parent_fd, context->temporary_name, context->witness_fd);
  if (number != 0) record_error(error, number, "stage_publication.cleanup.owned_name");
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

static void check_bindings(struct publication_context *context, struct publication_error *error)
{
  int number = probe_path(AT_FDCWD, context->working_dir, &context->root_identity);
  if (number != 0) { record_error(error, number, "stage_publication.binding.working_directory"); return; }
  number = observe_expected_directory(context->root_fd, &context->root_identity);
  if (number != 0) { record_error(error, number, "stage_publication.binding.held_working_directory"); return; }
  number = probe_path(context->root_fd, context->stage_parent, &context->stage_parent_identity);
  if (number != 0) { record_error(error, number, "stage_publication.binding.stage_parent"); return; }
  number = probe_path(context->root_fd, context->temporary_parent, &context->temporary_parent_identity);
  if (number != 0) { record_error(error, number, "stage_publication.binding.temporary_parent"); return; }
  number = observe_expected_directory(context->temporary_parent_fd, &context->temporary_parent_identity);
  if (number != 0) record_error(error, number, "stage_publication.binding.held_temporary_parent");
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

CAMLprim value unison_stage_publication_available(value unit)
{
  CAMLparam1(unit);
  if (__builtin_available(macOS 10.12, *)) CAMLreturn(Val_true);
  CAMLreturn(Val_false);
}

CAMLprim value unison_stage_publication_prepare(value working_dir, value stage, value temporary)
{
  CAMLparam3(working_dir, stage, temporary);
  CAMLlocal1(handle);
  struct publication_context *context;
  struct publication_error error = { 0, NULL };
  int number;
  if (__builtin_available(macOS 10.12, *)) {} else
    caml_unix_error(ENOSYS, "stage_publication.platform", Nothing);
  /* Root the finalizable owner before native allocations or descriptor opens. */
  handle = caml_alloc_custom(&publication_operations, sizeof(context),
    sizeof(*context) + caml_string_length(working_dir) +
    caml_string_length(stage) + caml_string_length(temporary) + 3, 1024 * 1024);
  *(struct publication_context **)Data_custom_val(handle) = NULL;
  context = calloc(1, sizeof(*context));
  if (context == NULL) caml_raise_out_of_memory();
  context->root_fd = context->expected_stage_parent_fd = context->temporary_parent_fd = -1;
  context->actual_stage_parent_fd = context->witness_fd = -1;
  context->phase = PREPARED;
  *(struct publication_context **)Data_custom_val(handle) = context;
  number = pthread_mutex_init(&context->mutex, NULL);
  if (number != 0) caml_unix_error(number, "stage_publication.prepare.mutex", Nothing);
  context->mutex_ready = 1;
  context->working_dir = strdup(String_val(working_dir));
  context->stage_path = strdup(String_val(stage));
  context->temporary_path = strdup(String_val(temporary));
  if (context->working_dir == NULL || context->stage_path == NULL || context->temporary_path == NULL) {
    close_context(context, NULL);
    caml_unix_error(ENOMEM, "stage_publication.prepare.paths", Nothing);
  }
  split_relative(context->stage_path, &context->stage_parent, &context->stage_name);
  split_relative(context->temporary_path, &context->temporary_parent, &context->temporary_name);

  caml_enter_blocking_section_no_pending();
  context->root_fd = open(context->working_dir, directory_open_flags());
  if (context->root_fd < 0) { record_error(&error, errno, "stage_publication.prepare.working_directory"); goto prepared; }
  number = directory_observe(context->root_fd, &context->root_identity);
  if (number != 0) { record_error(&error, number, "stage_publication.prepare.working_identity"); goto prepared; }
  context->expected_stage_parent_fd = openat(context->root_fd, context->stage_parent, directory_open_flags());
  if (context->expected_stage_parent_fd < 0) { record_error(&error, errno, "stage_publication.prepare.stage_parent"); goto prepared; }
  number = directory_observe(context->expected_stage_parent_fd, &context->stage_parent_identity);
  if (number != 0) { record_error(&error, number, "stage_publication.prepare.stage_identity"); goto prepared; }
  context->temporary_parent_fd = openat(context->root_fd, context->temporary_parent, directory_open_flags());
  if (context->temporary_parent_fd < 0) { record_error(&error, errno, "stage_publication.prepare.temporary_parent"); goto prepared; }
  number = directory_observe(context->temporary_parent_fd, &context->temporary_parent_identity);
  if (number != 0) { record_error(&error, number, "stage_publication.prepare.temporary_identity"); goto prepared; }
  if (same_directory(&context->stage_parent_identity, &context->temporary_parent_identity) &&
      strcmp(context->stage_name, context->temporary_name) == 0)
    record_error(&error, EINVAL, "stage_publication.prepare.aliased_names");
prepared:
  if (error.number != 0) close_context(context, &error);
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(handle);
}

CAMLprim value unison_stage_publication_adopt(value handle, value parent, value stage)
{
  CAMLparam3(handle, parent, stage);
  struct publication_context *context = *(struct publication_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int incoming_parent = Int_val(parent), borrowed_stage = Int_val(stage), number;
  /* No pending-action dispatch while the consumed parent is a local integer.
     Lock only with the runtime released; unlock before reacquisition. */
  caml_enter_blocking_section_no_pending();
  number = pthread_mutex_lock(&context->mutex);
  if (number != 0) {
    record_error(&error, number, "stage_publication.adopt.lock");
    close_slot(&incoming_parent, &error, "stage_publication.adopt.close_parent");
    goto adopted_unlocked;
  }
  if (context->phase != PREPARED) {
    record_error(&error, EINVAL, "stage_publication.adopt.state");
    close_slot(&incoming_parent, &error, "stage_publication.adopt.close_parent");
    cleanup_owned(context, &error);
    close_context(context, &error);
    goto adopted;
  }
  context->actual_stage_parent_fd = incoming_parent;
  incoming_parent = -1;
  number = observe_expected_directory(context->actual_stage_parent_fd, &context->stage_parent_identity);
  if (number != 0) record_error(&error, number, "stage_publication.adopt.actual_parent");
  if (error.number == 0) check_bindings(context, &error);
  if (error.number == 0) {
    number = name_matches_witness(context->actual_stage_parent_fd, context->stage_name, borrowed_stage, 1);
    if (number != 0) record_error(&error, number, "stage_publication.adopt.stage_name");
  }
  if (error.number == 0) {
    context->witness_fd = fcntl(borrowed_stage, F_DUPFD_CLOEXEC, 0);
    if (context->witness_fd < 0) record_error(&error, errno, "stage_publication.adopt.witness");
  }
  if (error.number != 0) {
    number = remove_owned_name(context->actual_stage_parent_fd, context->stage_name, borrowed_stage);
    if (number != 0) record_error(&error, number, "stage_publication.adopt.cleanup");
    close_context(context, &error);
  } else {
    context->phase = STAGE_OWNED;
    close_slot(&context->expected_stage_parent_fd, NULL, NULL);
  }
adopted:
  pthread_mutex_unlock(&context->mutex);
adopted_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}

CAMLprim value unison_stage_publication_publish(value handle)
{
  CAMLparam1(handle);
  struct publication_context *context = *(struct publication_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  struct stat existing;
  int number;
  caml_enter_blocking_section_no_pending();
  number = pthread_mutex_lock(&context->mutex);
  if (number != 0) { record_error(&error, number, "stage_publication.publish.lock"); goto published_unlocked; }
  if (context->phase != STAGE_OWNED) { record_error(&error, EINVAL, "stage_publication.publish.state"); goto published; }
  check_bindings(context, &error);
  if (error.number != 0) goto published;
  number = observe_expected_directory(context->actual_stage_parent_fd, &context->stage_parent_identity);
  if (number != 0) { record_error(&error, number, "stage_publication.publish.held_stage_parent"); goto published; }
  number = name_matches_witness(context->actual_stage_parent_fd, context->stage_name, context->witness_fd, 1);
  if (number != 0) { record_error(&error, number, "stage_publication.publish.stage_name"); goto published; }
  if (fstatat(context->temporary_parent_fd, context->temporary_name, &existing, AT_SYMLINK_NOFOLLOW) == 0) {
    record_error(&error, EEXIST, "stage_publication.publish.temporary_exists"); goto published;
  }
  if (errno != ENOENT) { record_error(&error, errno, "stage_publication.publish.temporary_lookup"); goto published; }
  if (renameatx_np(context->actual_stage_parent_fd, context->stage_name,
                  context->temporary_parent_fd, context->temporary_name, RENAME_EXCL) == -1)
    record_error(&error, errno, "stage_publication.publish.rename");
  else context->phase = TEMP_OWNED;
published:
  pthread_mutex_unlock(&context->mutex);
published_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}

CAMLprim value unison_stage_publication_disarm(value handle)
{
  CAMLparam1(handle);
  struct publication_context *context = *(struct publication_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int number;
  caml_enter_blocking_section_no_pending();
  number = pthread_mutex_lock(&context->mutex);
  if (number != 0) { record_error(&error, number, "stage_publication.disarm.lock"); goto disarmed_unlocked; }
  if (context->phase != TEMP_OWNED) record_error(&error, EINVAL, "stage_publication.disarm.state");
  else {
    close_context(context, NULL);
    context->phase = DISARMED;
  }
  pthread_mutex_unlock(&context->mutex);
disarmed_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}

CAMLprim value unison_stage_publication_abort(value handle)
{
  CAMLparam1(handle);
  struct publication_context *context = *(struct publication_context **)Data_custom_val(handle);
  struct publication_error error = { 0, NULL };
  int number;
  caml_enter_blocking_section_no_pending();
  number = pthread_mutex_lock(&context->mutex);
  if (number != 0) { record_error(&error, number, "stage_publication.abort.lock"); goto aborted_unlocked; }
  cleanup_owned(context, &error);
  close_context(context, &error);
  pthread_mutex_unlock(&context->mutex);
aborted_unlocked:
  caml_acquire_runtime_system();
  raise_error(error);
  CAMLreturn(Val_unit);
}

#else

CAMLprim value unison_stage_publication_available(value unit)
{
  CAMLparam1(unit);
  CAMLreturn(Val_false);
}
#define UNISON_PUBLICATION_UNAVAILABLE(name, params, roots) \
  CAMLprim value name params { roots; \
    caml_unix_error(ENOSYS, "stage_publication.platform", Nothing); \
    CAMLreturn(Val_unit); }
UNISON_PUBLICATION_UNAVAILABLE(unison_stage_publication_prepare,
  (value root, value stage, value temporary), CAMLparam3(root, stage, temporary))
UNISON_PUBLICATION_UNAVAILABLE(unison_stage_publication_adopt,
  (value handle, value parent, value stage), CAMLparam3(handle, parent, stage))
UNISON_PUBLICATION_UNAVAILABLE(unison_stage_publication_publish, (value handle), CAMLparam1(handle))
UNISON_PUBLICATION_UNAVAILABLE(unison_stage_publication_disarm, (value handle), CAMLparam1(handle))
UNISON_PUBLICATION_UNAVAILABLE(unison_stage_publication_abort, (value handle), CAMLparam1(handle))

#endif
