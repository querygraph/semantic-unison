/* Isolated OpenSSL3 adapter candidate; not selected by production builds yet.
 * One OCaml owner/domain per context. No OCaml pointers in native storage. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/custom.h>
#include <caml/fail.h>
#include <openssl/evp.h>
#include <openssl/crypto.h>
#include <openssl/opensslv.h>
#include <stdint.h>
#include <string.h>
#if OPENSSL_VERSION_MAJOR < 3
#error "OpenSSL3 EVP API required"
#endif
#ifdef EVPHASH_TEST_COUNTERS
#include <stdatomic.h>
static atomic_long live_contexts;
static atomic_long owned_methods;
static atomic_int injected_failure;
static int take_failure(int stage)
{
  int expected = stage;
  return atomic_compare_exchange_strong(&injected_failure, &expected, 0);
}
#endif

struct hash_context { EVP_MD_CTX *ctx; EVP_MD *md; uint64_t length; };
static void release(struct hash_context *h)
{
  if (h->ctx != NULL) {
    EVP_MD_CTX_free(h->ctx); h->ctx = NULL;
#ifdef EVPHASH_TEST_COUNTERS
    atomic_fetch_sub(&live_contexts, 1);
#endif
  }
  if (h->md != NULL) {
    EVP_MD_free(h->md); h->md = NULL;
#ifdef EVPHASH_TEST_COUNTERS
    atomic_fetch_sub(&owned_methods, 1);
#endif
  }
}
static void finalize(value v) { release((struct hash_context *)Data_custom_val(v)); }
static struct custom_operations operations = {
  "org.firstpair.semantic-hash.openssl3/1", finalize,
  custom_compare_default, custom_hash_default, custom_serialize_default,
  custom_deserialize_default, custom_compare_ext_default, custom_fixed_length_default
};
static struct hash_context *context(value v)
{
  if (!Is_block(v) || Tag_val(v) != Custom_tag || Custom_ops_val(v) != &operations)
    caml_invalid_argument("EVP hash context");
  struct hash_context *h = (struct hash_context *)Data_custom_val(v);
  if (h->ctx == NULL) caml_invalid_argument("EVP hash context finalized");
  return h;
}
CAMLprim value unison_evp_hash_create(value unit)
{
  CAMLparam1(unit); CAMLlocal1(v);
  /* 4096 is a GC pressure hint, not measured allocator coverage or a cap. */
  v = caml_alloc_custom_mem(&operations, sizeof(struct hash_context), 4096);
  struct hash_context *h = (struct hash_context *)Data_custom_val(v);
  h->ctx = NULL; h->md = NULL; h->length = 0;
  h->ctx = EVP_MD_CTX_new();
  if (h->ctx == NULL) caml_raise_out_of_memory();
#ifdef EVPHASH_TEST_COUNTERS
  atomic_fetch_add(&live_contexts, 1);
#endif
  const char *algorithm = "SHA256";
#ifdef EVPHASH_TEST_COUNTERS
  if (take_failure(1)) algorithm = "UNISON_TEST_MISSING_DIGEST";
#endif
  h->md = EVP_MD_fetch(NULL, algorithm, NULL);
#ifdef EVPHASH_TEST_COUNTERS
  if (h->md != NULL) atomic_fetch_add(&owned_methods, 1);
#endif
  if (h->md == NULL || EVP_MD_get_size(h->md) != 32 ||
      EVP_DigestInit_ex2(h->ctx, h->md, NULL) != 1) {
    release(h); caml_failwith("EVP SHA256 initialization");
  }
  CAMLreturn(v);
}
CAMLprim value unison_evp_hash_feed(value v, value input, value offset, value length)
{
  CAMLparam4(v, input, offset, length);
  struct hash_context *h = context(v);
  intnat off = Long_val(offset), len = Long_val(length);
  if (off < 0 || len < 0 || len > 65536 ||
      (uintnat)off > caml_string_length(input) ||
      (uintnat)len > caml_string_length(input) - (uintnat)off ||
      h->length > UINT64_C(0x1fffffffffffffff) - (uint64_t)len)
    caml_invalid_argument("EVP SHA256 chunk bounds");
  int success;
#ifdef EVPHASH_TEST_COUNTERS
  success = take_failure(2) ? 0 : EVP_DigestUpdate(h->ctx, Bytes_val(input) + off, (size_t)len);
#else
  success = EVP_DigestUpdate(h->ctx, Bytes_val(input) + off, (size_t)len);
#endif
  if (success != 1) {
    release(h); caml_failwith("EVP SHA256 update");
  }
  h->length += (uint64_t)len;
  CAMLreturn(Val_unit);
}
CAMLprim value unison_evp_hash_finish(value v)
{
  CAMLparam1(v); CAMLlocal1(result);
  struct hash_context *h = context(v);
  unsigned char digest[EVP_MAX_MD_SIZE]; unsigned int size = 0;
  int success;
#ifdef EVPHASH_TEST_COUNTERS
  success = take_failure(3) ? 0 : EVP_DigestFinal_ex(h->ctx, digest, &size);
#else
  success = EVP_DigestFinal_ex(h->ctx, digest, &size);
#endif
  release(h); /* No native ownership survives a subsequent OCaml allocation. */
  if (success != 1 || size != 32) caml_failwith("EVP SHA256 finalization");
  result = caml_alloc_string(32); memcpy(Bytes_val(result), digest, 32);
  CAMLreturn(result);
}
CAMLprim value unison_evp_hash_version(value unit)
{
  CAMLparam1(unit); CAMLreturn(caml_copy_string(OpenSSL_version(OPENSSL_VERSION)));
}
#ifdef EVPHASH_TEST_COUNTERS
CAMLprim value unison_evp_hash_test_live(value unit)
{
  CAMLparam1(unit); CAMLreturn(Val_long(atomic_load(&live_contexts)));
}
CAMLprim value unison_evp_hash_test_methods(value unit)
{
  CAMLparam1(unit); CAMLreturn(Val_long(atomic_load(&owned_methods)));
}
CAMLprim value unison_evp_hash_test_failure(value stage)
{
  CAMLparam1(stage);
  intnat stage_id = Long_val(stage);
  if (stage_id < 1 || stage_id > 3) caml_invalid_argument("EVP test failure stage");
  atomic_store(&injected_failure, (int)stage_id);
  CAMLreturn(Val_unit);
}
#endif
