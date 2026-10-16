/* Fresh, bounded observations of a caller-owned descriptor. */

#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/threads.h>
#include <caml/unixsupport.h>
#include <caml/version.h>
#include <errno.h>

#if OCAML_VERSION_MAJOR < 5
#define caml_unix_error unix_error
#endif

#if defined(__APPLE__)

#include <sys/stat.h>
#include <sys/mount.h>
#include <sys/attr.h>
#include <unistd.h>
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#define UNISON_VOLUME_UUID_BYTES 16
#define UNISON_VOLUME_REPLY_BYTES \
  (sizeof(uint32_t) + sizeof(attribute_set_t) + UNISON_VOLUME_UUID_BYTES)

/* getattrlist's packed fields have four-byte alignment. Decode with memcpy,
   never by casting a possibly unaligned byte buffer. This helper has no OCaml
   dependencies or side effects; private tests can include this translation
   unit and pass synthetic replies without adding a production test API. */
static int unison_parse_volume_uuid(const unsigned char *buffer, size_t capacity,
                                   unsigned char uuid[UNISON_VOLUME_UUID_BYTES],
                                   int *present)
{
  uint32_t length;
  attribute_set_t returned;
  const size_t header = sizeof(uint32_t) + sizeof(attribute_set_t);
  size_t expected;
  unsigned int i;

  *present = 0;
  memset(uuid, 0, UNISON_VOLUME_UUID_BYTES);
  if (capacity < header) return EPROTO;
  memcpy(&length, buffer, sizeof(length));
  if (length < header || length > capacity) return EPROTO;
  memcpy(&returned, buffer + sizeof(length), sizeof(returned));
  if (returned.commonattr != ATTR_CMN_RETURNED_ATTRS ||
      (returned.volattr & ~(ATTR_VOL_INFO | ATTR_VOL_UUID)) != 0 ||
      returned.dirattr != 0 || returned.fileattr != 0 || returned.forkattr != 0)
    return EPROTO;

  expected = header + ((returned.volattr & ATTR_VOL_UUID)
                       ? UNISON_VOLUME_UUID_BYTES : 0);
  if (length != expected) return EPROTO;
  if (returned.volattr & ATTR_VOL_UUID) {
    memcpy(uuid, buffer + header, UNISON_VOLUME_UUID_BYTES);
    for (i = 0; i < UNISON_VOLUME_UUID_BYTES; ++i)
      if (uuid[i] != 0) *present = 1;
  }
  return 0;
}

static int unison_same_file_observation(const struct stat *a,
                                        const struct stat *b)
{
  return a->st_dev == b->st_dev && a->st_ino == b->st_ino &&
    (a->st_mode & S_IFMT) == (b->st_mode & S_IFMT) &&
    a->st_size == b->st_size && a->st_nlink == b->st_nlink &&
    a->st_flags == b->st_flags &&
    a->st_mtimespec.tv_sec == b->st_mtimespec.tv_sec &&
    a->st_mtimespec.tv_nsec == b->st_mtimespec.tv_nsec &&
    a->st_ctimespec.tv_sec == b->st_ctimespec.tv_sec &&
    a->st_ctimespec.tv_nsec == b->st_ctimespec.tv_nsec;
}

/* Constructor order in Unix.file_kind. No native mode bits cross the ABI. */
static int unison_observed_kind(mode_t mode)
{
  if (S_ISREG(mode)) return 0;
  if (S_ISDIR(mode)) return 1;
  if (S_ISCHR(mode)) return 2;
  if (S_ISBLK(mode)) return 3;
  if (S_ISLNK(mode)) return 4;
  if (S_ISFIFO(mode)) return 5;
  if (S_ISSOCK(mode)) return 6;
  return -1;
}

CAMLprim value unison_file_observation(value descriptor)
{
  CAMLparam1(descriptor);
  CAMLlocal3(result, field, optional_uuid);
  const int fd = Int_val(descriptor);
  struct stat before, after;
  struct statfs filesystem;
  struct attrlist attributes;
  unsigned char buffer[UNISON_VOLUME_REPLY_BYTES];
  unsigned char uuid[UNISON_VOLUME_UUID_BYTES];
  char device_id[9], file_id[17], filesystem_id[17], uuid_text[33];
  const char *phase = "file_observation.fstat";
  int error = 0, present = 0, kind = -1;
  unsigned int i;

  memset(&attributes, 0, sizeof(attributes));
  attributes.bitmapcount = ATTR_BIT_MAP_COUNT;
  attributes.commonattr = ATTR_CMN_RETURNED_ATTRS;
  attributes.volattr = ATTR_VOL_INFO | ATTR_VOL_UUID;
  memset(buffer, 0, sizeof(buffer));

  /* The only descriptor is borrowed. No allocation, descriptor ownership or
     access to the OCaml heap crosses this blocking section. Capture errno
     before reacquiring the runtime. */
  caml_release_runtime_system();
  if (fstat(fd, &before) == -1) { error = errno; goto observed; }
  phase = "file_observation.fstatfs";
  if (fstatfs(fd, &filesystem) == -1) { error = errno; goto observed; }
  phase = "file_observation.fgetattrlist";
  if (fgetattrlist(fd, &attributes, buffer, sizeof(buffer),
                  FSOPT_REPORT_FULLSIZE) == -1) {
    error = errno;
    goto observed;
  }
  phase = "file_observation.volume_attributes";
  error = unison_parse_volume_uuid(buffer, sizeof(buffer), uuid, &present);
  if (error != 0) goto observed;
  phase = "file_observation.fstat_recheck";
  if (fstat(fd, &after) == -1) { error = errno; goto observed; }
  phase = "file_observation.changed";
  if (!unison_same_file_observation(&before, &after)) {
    error = EBUSY;
    goto observed;
  }
  phase = "file_observation.stat_fields";
  if (before.st_size < 0 ||
      before.st_mtimespec.tv_nsec < 0 || before.st_mtimespec.tv_nsec >= 1000000000 ||
      before.st_ctimespec.tv_nsec < 0 || before.st_ctimespec.tv_nsec >= 1000000000) {
    error = EOVERFLOW;
    goto observed;
  }
  kind = unison_observed_kind(before.st_mode);
  if (kind < 0) error = EOPNOTSUPP;

observed:
  caml_acquire_runtime_system();
  if (error != 0) caml_unix_error(error, phase, Nothing);

  snprintf(device_id, sizeof(device_id), "%08" PRIx32, (uint32_t)before.st_dev);
  snprintf(file_id, sizeof(file_id), "%016" PRIx64, (uint64_t)before.st_ino);
  snprintf(filesystem_id, sizeof(filesystem_id), "%08" PRIx32 "%08" PRIx32,
           (uint32_t)filesystem.f_fsid.val[0], (uint32_t)filesystem.f_fsid.val[1]);
  for (i = 0; i < UNISON_VOLUME_UUID_BYTES; ++i)
    snprintf(uuid_text + 2 * i, 3, "%02x", (unsigned int)uuid[i]);

  /* Initialize every field before any further allocation can trigger GC. */
  result = caml_alloc_tuple(13);
  for (i = 0; i < 13; ++i) Store_field(result, i, Val_unit);
  field = caml_copy_string(device_id); Store_field(result, 0, field);
  field = caml_copy_string(file_id); Store_field(result, 1, field);
  Store_field(result, 2, Val_int(kind));
  field = caml_copy_int64((int64_t)before.st_size); Store_field(result, 3, field);
  field = caml_copy_int64((int64_t)before.st_nlink); Store_field(result, 4, field);
  field = caml_copy_int64((int64_t)(uint32_t)before.st_flags);
  Store_field(result, 5, field);
  field = caml_copy_string(filesystem_id); Store_field(result, 6, field);
  field = caml_copy_int64((int64_t)(uint32_t)filesystem.f_flags);
  Store_field(result, 7, field);
  optional_uuid = Val_int(0);
  if (present) {
    field = caml_copy_string(uuid_text);
    optional_uuid = caml_alloc_small(1, 0);
    Field(optional_uuid, 0) = field;
  }
  Store_field(result, 8, optional_uuid);
  field = caml_copy_int64((int64_t)before.st_mtimespec.tv_sec);
  Store_field(result, 9, field);
  Store_field(result, 10, Val_long(before.st_mtimespec.tv_nsec));
  field = caml_copy_int64((int64_t)before.st_ctimespec.tv_sec);
  Store_field(result, 11, field);
  Store_field(result, 12, Val_long(before.st_ctimespec.tv_nsec));
  CAMLreturn(result);
}

#else

CAMLprim value unison_file_observation(value descriptor)
{
  CAMLparam1(descriptor);
  caml_unix_error(ENOSYS, "file_observation.platform", Nothing);
  CAMLreturn(Val_unit);
}

#endif
