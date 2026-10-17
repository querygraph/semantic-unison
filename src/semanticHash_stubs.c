/* Each context belongs to one worker. No global state or OCaml callbacks.
 * CommonCrypto supplies the platform SHA-256 implementation on macOS; other
 * systems retain the separately tested portable reference implementation.
 * UNISON_SEMANTIC_HASH_OPENSSL explicitly selects the owned OpenSSL3 adapter. */
#include <caml/mlvalues.h>
#include <caml/memory.h>
#include <caml/alloc.h>
#include <caml/fail.h>
#if defined(UNISON_SEMANTIC_HASH_OPENSSL)
#include "semanticHash_evp.h"

CAMLprim value unison_semantic_sha256_init(value unit)
{
  CAMLparam1(unit); CAMLlocal2(context, result);
  context = UNISON_EVP_API(create)(unit);
  result = caml_alloc(1, 0);
  Store_field(result, 0, context);
  CAMLreturn(result);
}
CAMLprim value unison_semantic_sha256_feed(value context, value input,
                                         value offset, value length)
{
  return UNISON_EVP_API(feed)(context, input, offset, length);
}
CAMLprim value unison_semantic_sha256_finish(value context)
{
  return UNISON_EVP_API(finish)(context);
}
#else
#ifdef __APPLE__
#include <CommonCrypto/CommonDigest.h>
#include <string.h>
#endif

CAMLprim value unison_semantic_sha256_init(value unit)
{
  CAMLparam1(unit);
  CAMLlocal2(context, result);
#ifdef __APPLE__
  context = caml_alloc_string(sizeof(CC_SHA256_CTX));
  CC_SHA256_CTX native;
  if (!CC_SHA256_Init(&native)) caml_failwith("SHA-256 initialization");
  memcpy(Bytes_val(context), &native, sizeof native);
  result = caml_alloc(1, 0);
  Store_field(result, 0, context);
  CAMLreturn(result);
#else
  CAMLreturn(Val_int(0));
#endif
}

CAMLprim value unison_semantic_sha256_feed(value context, value input,
                                         value offset, value length)
{
  CAMLparam4(context, input, offset, length);
#ifdef __APPLE__
  intnat off = Long_val(offset), len = Long_val(length);
  if (caml_string_length(context) != sizeof(CC_SHA256_CTX) ||
      off < 0 || len < 0 || len > 65536 ||
      (uintnat)off > caml_string_length(input) ||
      (uintnat)len > caml_string_length(input) - (uintnat)off)
    caml_invalid_argument("SHA-256 chunk bounds");
  CC_SHA256_CTX native;
  memcpy(&native, Bytes_val(context), sizeof native);
  if (!CC_SHA256_Update(&native, Bytes_val(input) + off, (CC_LONG)len))
    caml_failwith("SHA-256 update");
  memcpy(Bytes_val(context), &native, sizeof native);
  CAMLreturn(Val_unit);
#else
  caml_failwith("native SHA-256 unavailable");
#endif
}

CAMLprim value unison_semantic_sha256_finish(value context)
{
  CAMLparam1(context);
  CAMLlocal1(result);
#ifdef __APPLE__
  if (caml_string_length(context) != sizeof(CC_SHA256_CTX))
    caml_invalid_argument("SHA-256 context");
  CC_SHA256_CTX native;
  unsigned char digest[CC_SHA256_DIGEST_LENGTH];
  memcpy(&native, Bytes_val(context), sizeof native);
  if (!CC_SHA256_Final(digest, &native)) caml_failwith("SHA-256 finalization");
  memset(Bytes_val(context), 0, sizeof native);
  result = caml_alloc_string(CC_SHA256_DIGEST_LENGTH);
  memcpy(Bytes_val(result), digest, CC_SHA256_DIGEST_LENGTH);
  CAMLreturn(result);
#else
  caml_failwith("native SHA-256 unavailable");
#endif
}

#endif /* explicit OpenSSL selection vs unchanged platform backend */
