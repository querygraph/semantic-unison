/* Private fixture: wrap the actual source without adding a production switch. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#include <caml/unixsupport.h>
#include <errno.h>
#include <string.h>
#ifdef __APPLE__
#include <sys/attr.h>
#include <sys/stat.h>
#include <unistd.h>
static int fixture_mode;

static size_t fixture_buffer(unsigned char *buffer, size_t capacity, int mode)
{
  uint32_t length = mode == 1 ? 24 : 40;
  attribute_set_t returned;
  unsigned char uuid[16];
  size_t i;
  memset(&returned, 0, sizeof(returned));
  returned.commonattr = ATTR_CMN_RETURNED_ATTRS;
  returned.volattr = ATTR_VOL_INFO | (mode == 1 ? 0 : ATTR_VOL_UUID);
  for (i = 0; i < sizeof(uuid); i++) uuid[i] = mode == 2 ? 0 : (unsigned char)(i + 1);
  if (mode == 4) length = 23;
  if (mode == 5) length = (uint32_t)capacity + 1;
  if (mode == 6) returned.commonattr = 0;
  if (mode == 7) returned.volattr |= ATTR_VOL_SIZE;
  if (mode == 11) returned.dirattr = 1;
  if (mode == 12) returned.fileattr = 1;
  if (mode == 13) returned.forkattr = 1;
  if (mode == 14) returned.commonattr |= ATTR_CMN_NAME;
  memset(buffer, 0, capacity);
  if (capacity >= 4) memcpy(buffer, &length, 4);
  if (capacity >= 24) memcpy(buffer + 4, &returned, sizeof(returned));
  if (capacity >= 40) memcpy(buffer + 24, uuid, sizeof(uuid));
  return mode == 1 ? 24 : 40;
}

static int fixture_getattr(int fd, struct attrlist *request, void *buffer,
                           size_t capacity, unsigned long options)
{
  if (fixture_mode == 0) return fgetattrlist(fd, request, buffer, capacity, options);
  if (request->commonattr != ATTR_CMN_RETURNED_ATTRS ||
      request->volattr != (ATTR_VOL_INFO | ATTR_VOL_UUID) || request->fileattr ||
      request->dirattr || request->forkattr || !(options & FSOPT_REPORT_FULLSIZE)) {
    errno = EINVAL; return -1;
  }
  if (fixture_mode == 8 || fixture_mode == 9) {
    errno = fixture_mode == 8 ? EACCES : EIO; return -1;
  }
  if (fixture_mode == 10) {
    struct stat before;
    if (fstat(fd, &before) || ftruncate(fd, before.st_size + 1)) return -1;
  }
  fixture_buffer(buffer, capacity, fixture_mode);
  return 0;
}
#define fgetattrlist fixture_getattr
#endif
#include "fileObservation_stubs.c"
#ifdef __APPLE__
#undef fgetattrlist
#endif

CAMLprim value file_observation_fixture_mode(value mode)
{
#ifdef __APPLE__
  fixture_mode = Int_val(mode);
#else
  (void)mode;
#endif
  return Val_unit;
}

CAMLprim value file_observation_fixture_buffer(value mode)
{
  CAMLparam1(mode);
  CAMLlocal1(result);
#ifdef __APPLE__
  unsigned char buffer[40];
  size_t length = fixture_buffer(buffer, sizeof(buffer), Int_val(mode));
  result = caml_alloc_string(length);
  memcpy(Bytes_val(result), buffer, length);
  CAMLreturn(result);
#else
  unix_error(ENOSYS, "fixture_buffer", Nothing);
#endif
}

CAMLprim value file_observation_fixture_parse(value buffer)
{
  CAMLparam1(buffer);
  CAMLlocal2(result, bytes);
#ifdef __APPLE__
  unsigned char uuid[16];
  int present = 0;
  int error = unison_parse_volume_uuid((const unsigned char *)Bytes_val(buffer),
                                      caml_string_length(buffer), uuid, &present);
  if (error) unix_error(error, "fixture_parse", Nothing);
  if (!present) CAMLreturn(Val_int(0));
  bytes = caml_alloc_string(sizeof(uuid));
  memcpy(Bytes_val(bytes), uuid, sizeof(uuid));
  result = caml_alloc(1, 0);
  Store_field(result, 0, bytes);
  CAMLreturn(result);
#else
  unix_error(ENOSYS, "fixture_parse", Nothing);
#endif
}

CAMLprim value file_observation_fixture_protocol_errno(value unit)
{
  (void)unit;
#ifdef __APPLE__
  return Val_int(EPROTO);
#else
  return Val_int(0);
#endif
}
