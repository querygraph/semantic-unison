// Unison's original adapter code. Adobe SDK is obtained and built separately.
// This is SDK validation, not a claim about Lightroom's proprietary UI.
#include "dng_exceptions.h"
#include "dng_file_stream.h"
#include "dng_globals.h"
#include "dng_host.h"
#include "dng_ifd.h"
#include "dng_info.h"
#include "dng_negative.h"
#include "dng_shared.h"
#include "dng_tag_codes.h"
#include "dng_tag_values.h"
#include "dng_xmp_sdk.h"
#if defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
#include "area_task_host.h"
#endif
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
#include "memory_allocator.h"
#endif
#include <CommonCrypto/CommonDigest.h>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <memory>
#include <limits>
#include <stdexcept>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
#define TXMP_STRING_TYPE std::string
#define XMP_INCLUDE_XMPFILES 0
#include "XMP.hpp"
#include "XMP.incl_cpp"

static std::atomic<unsigned> errors{0}, warnings{0};
void UnisonSdkReportError(const char *, const char *);
void UnisonSdkReportWarning(const char *, const char *);
void ReportError(const char *message, const char *detail) {
  ++errors;
  UnisonSdkReportError(message, detail);
}
void ReportWarning(const char *message, const char *detail) {
  ++warnings;
  UnisonSdkReportWarning(message, detail);
}
static bool xmp_error(void *, XMP_ErrorSeverity, XMP_Int32 cause, XMP_StringPtr message) {
  ++errors;
  fprintf(stderr, "XMP error %d: %s\n", static_cast<int>(cause), message);
  // The toolkit silently recovers from some XML errors with its default
  // callback. Qualification requires recording and rejecting those errors.
  return false;
}

class TrackingShared final : public dng_shared {
public:
  bool old_digest_present = false, new_digest_present = false;
  bool ParseTag(dng_stream &stream, dng_exif &exif, uint32 parent, bool main,
                uint32 tag, uint32 type, uint32 count, uint64 offset, int64 delta) override {
    const bool parsed = dng_shared::ParseTag(stream, exif, parent, main, tag, type,
                                            count, offset, delta);
    if (parsed && tag == tcRawImageDigest) old_digest_present = true;
    if (parsed && tag == tcNewRawImageDigest) new_digest_present = true;
    return parsed;
  }
};
#if defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
using ValidationHostBase = UnisonAreaTaskHost;
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
static constexpr const char *driver_build = "unison-sdk171-2724-v3-area-memory-unqualified";
#else
static constexpr const char *driver_build = "unison-sdk171-2724-v2-area-unqualified";
#endif
#else
using ValidationHostBase = dng_host;
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
static constexpr const char *driver_build = "unison-sdk171-2724-v3-memory-unqualified";
#else
static constexpr const char *driver_build = "unison-sdk171-2724-v1-single";
#endif
#endif
class ValidationHost final : public ValidationHostBase {
public:
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
  ValidationHost(uint32 threads,dng_memory_allocator *allocator)
#if defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
    : ValidationHostBase(threads,allocator) {}
#else
    : ValidationHostBase(allocator) { (void) threads; }
#endif
#elif defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
  explicit ValidationHost(uint32 threads) : ValidationHostBase(threads) {}
#else
  explicit ValidationHost(uint32) {}
#endif
  dng_shared *Make_dng_shared() override { return new TrackingShared; }
};

static uint32 requested_threads(const char *value) {
  uint32 result = 0;
  if (!value[0] || value[0] == '0') return 0;
  for (const char *p = value; *p; ++p) {
    if (*p < '0' || *p > '9') return 0;
    result = result * 10 + uint32(*p - '0');
    if (result > 128) return 0;
  }
  return result;
}

struct FileHash { std::string hex; uint64_t size; };
static FileHash hash_file(const char *path) {
  std::unique_ptr<FILE, decltype(&fclose)> file(fopen(path, "rb"), fclose);
  if (!file) throw std::runtime_error("cannot open candidate");
  struct stat before{}, after{};
  if (fstat(fileno(file.get()), &before) || !S_ISREG(before.st_mode))
    throw std::runtime_error("candidate must be a regular file");
  CC_SHA256_CTX context;
  CC_SHA256_Init(&context);
  std::vector<unsigned char> buffer(1024 * 1024);
  uint64_t size = 0;
  for (;;) {
    size_t n = fread(buffer.data(), 1, buffer.size(), file.get());
    if (n) { CC_SHA256_Update(&context, buffer.data(), static_cast<CC_LONG>(n)); size += n; }
    if (n < buffer.size()) {
      if (ferror(file.get())) throw std::runtime_error("candidate read failed");
      break;
    }
  }
  if (fstat(fileno(file.get()), &after) || before.st_size != after.st_size ||
      before.st_mtimespec.tv_sec != after.st_mtimespec.tv_sec ||
      before.st_mtimespec.tv_nsec != after.st_mtimespec.tv_nsec ||
      before.st_ctimespec.tv_sec != after.st_ctimespec.tv_sec ||
      before.st_ctimespec.tv_nsec != after.st_ctimespec.tv_nsec ||
      size != static_cast<uint64_t>(after.st_size))
    throw std::runtime_error("candidate changed while hashing");
  unsigned char bytes[CC_SHA256_DIGEST_LENGTH];
  CC_SHA256_Final(bytes, &context);
  std::string hex;
  for (unsigned char b : bytes) {
    hex += "0123456789abcdef"[b >> 4]; hex += "0123456789abcdef"[b & 15];
  }
  return {hex, size};
}

#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
static size_t requested_memory(const char *text) {
  size_t value=0;
  if(!*text || *text=='0')return 0;
  for(const char *p=text;*p;p++) {
    if(*p<'0'||*p>'9' || value>(std::numeric_limits<size_t>::max()-size_t(*p-'0'))/10)return 0;
    value=value*10+size_t(*p-'0');
  }
  return value;
}
#endif
int main(int argc, char **argv) {
  // Fixed protocol argv, no output/render/write options and no shell.
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
  constexpr int argument_count=12,path_index=11;
  const size_t memory_limit=argc==argument_count?requested_memory(argv[9]):0;
#else
  constexpr int argument_count=10,path_index=9;
#endif
  uint32 threads = argc == argument_count ? requested_threads(argv[7]) : 0;
#if defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
  // This separate protocol is intentionally unavailable to the production
  // v1 caller. Compilation and synthetic scheduler tests are not SDK runtime
  // qualification, even if a user installs and pins this executable.
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
  const char *protocol = "--unison-dng-validation-area-memory-source-v0";
#else
  const char *protocol = "--unison-dng-validation-area-source-v0";
#endif
#else
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
  const char *protocol = "--unison-dng-validation-memory-source-v0";
#else
  const char *protocol = "--unison-dng-validation-v1";
#endif
  if (threads != 1) threads = 0;
#endif
  if (argc != argument_count || strcmp(argv[1], protocol) ||
      strcmp(argv[2], "--expected-sha256") || strcmp(argv[4], "--expected-size") ||
      strcmp(argv[6], "--threads") || !threads ||
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
      strcmp(argv[8], "--host-memory-bytes") || !memory_limit ||
#endif
      strcmp(argv[path_index-1], "--") || argv[path_index][0] != '/') {
    fprintf(stderr, "Expected %s arguments and the build's explicit thread allowance.\n", protocol);
    return 64;
  }
  const char *path = argv[path_index];
  FileHash file{"", 0};
  const char *structure = "invalid", *decode = "not_checked", *raw = "not_checked";
  int receipt_fd = dup(STDOUT_FILENO);
  if (receipt_fd < 0 || dup2(STDERR_FILENO, STDOUT_FILENO) < 0) return 70;
  // SDK diagnostics occasionally use stdout; reserve original stdout for the
  // sole structured receipt and route all SDK output to bounded stderr.
  FILE *receipt = fdopen(receipt_fd, "w");
  if (!receipt) return 70;
  try {
    file = hash_file(path);
    if (file.hex != argv[3] || std::to_string(file.size) != argv[5])
      throw std::runtime_error("candidate does not match expected full-file identity");
    gVerbose = false;
    dng_xmp_sdk::InitializeSDK();
    SXMPMeta::SetDefaultErrorCallback(xmp_error, nullptr, 10000);
#if defined(UNISON_EXPERIMENTAL_MEMORY_BUDGET)
    // Allocator is declared before the host/negative and outlives all joined
    // area/codec calls and returned SDK buffers within this synchronous scope.
    UnisonMemoryAllocator allocator(memory_limit);
    // Declared before host: report after host and all SDK buffers are destroyed,
    // while the allocator's shared accounting state remains available.
    struct MemoryReport {
      const UnisonMemoryAllocator &allocator;
      ~MemoryReport() {
        try {
          const auto u = allocator.usage();
          fprintf(stderr, "UNISON-HOST-MEMORY 1 limit=%zu used=%zu peak=%zu live=%zu denied=%zu\n",
                  u.limit, u.used, u.peak, u.live, u.denied);
        } catch (...) {
          // Observational diagnostics must not terminate exception unwinding.
          fprintf(stderr, "UNISON-HOST-MEMORY unavailable\n");
        }
      }
    } memory_report{allocator};
    ValidationHost host(threads,&allocator);
#else
    ValidationHost host(threads);
#endif
#if defined(UNISON_EXPERIMENTAL_AREA_TASK_HOST)
    // Declared after host: report joined scheduler state before host teardown.
    struct AreaReport {
      const ValidationHost &host;
      ~AreaReport() {
        const auto a = host.Activity();
        fprintf(stderr, "UNISON-HOST-AREA 1 tasks=%llu started=%llu finish=%llu calls=%llu active=%llu peak=%llu max-partition=%llu reference=%llu\n",
                (unsigned long long)a.tasks, (unsigned long long)a.start_successes,
                (unsigned long long)a.finish_calls, (unsigned long long)a.process_calls,
                (unsigned long long)a.active_callbacks, (unsigned long long)a.peak_callbacks,
                (unsigned long long)a.max_partition, (unsigned long long)host.ReferenceTasks());
      }
    } area_report{host};
#endif
    host.SetIgnoreEnhanced(true); // Validate original raw, never an enhanced substitute.
    dng_file_stream stream(path);
    dng_info info;
    info.Parse(host, stream);
    info.PostParse(host);
    if (!info.IsValidDNG()) throw std::runtime_error("SDK rejected DNG structure");
    auto &shared = static_cast<TrackingShared &>(*info.fShared.Get());
    AutoPtr<dng_negative> negative(host.Make_dng_negative());
    negative->Parse(host, stream, info);
    negative->PostParse(host, stream, info);
    structure = errors.load() ? "invalid" : "valid";
    negative->ReadStage1Image(host, stream, info);
    if (!negative->Stage1Image() || negative->IsPreview())
      throw std::runtime_error("SDK did not decode complete stage-1 raw image");
    if (info.fMaskIndex != -1) negative->ReadTransparencyMask(host, stream, info);
    if (info.fDepthIndex != -1) negative->ReadDepthMap(host, stream, info);
    if (!info.fSemanticMaskIndices.empty()) negative->ReadSemanticMasks(host, stream, info);
    decode = "success";
    const dng_fingerprint old_digest = negative->RawImageDigest();
    const dng_fingerprint new_digest = negative->NewRawImageDigest();
    if (!shared.old_digest_present && !shared.new_digest_present) raw = "missing";
    else if (info.fMaskIndex != -1 &&
             info.fIFD[info.fMaskIndex]->fCompression != ccUncompressed &&
             info.fIFD[info.fMaskIndex]->fCompression != ccJPEG) {
      // SDK can skip digest checking for lossy transparency. Do not label a
      // skipped verification valid. Conservative until those masks qualify.
      raw = "unsupported";
    } else {
      raw = "valid";
      // SDK prefers NewRawImageDigest when both exist; validate each present
      // tag separately, including rejecting present all-zero fingerprints.
      for (int which = 0; which != 2; ++which) {
        const bool present = which ? shared.new_digest_present : shared.old_digest_present;
        const dng_fingerprint stored = which ? new_digest : old_digest;
        if (!present) continue;
        if (!stored.IsValid()) { ++errors; raw = "mismatch"; continue; }
        negative->ClearRawImageDigest();
        if (which) negative->SetNewRawImageDigest(stored);
        else negative->SetRawImageDigest(stored);
        const unsigned prior = errors.load();
        negative->ValidateRawImageDigest(host);
        if (errors.load() != prior || negative->IsDamaged()) raw = "mismatch";
      }
    }
    const auto final_hash = hash_file(path);
    if (final_hash.hex != file.hex || final_hash.size != file.size)
      throw std::runtime_error("candidate changed during SDK validation");
  } catch (const dng_exception &e) {
    ++errors; decode = "failure";
    fprintf(stderr, "SDK exception %d\n", static_cast<int>(e.ErrorCode()));
  } catch (const std::exception &e) {
    ++errors;
    fprintf(stderr, "Validation driver: %s\n", e.what());
  } catch (...) {
    ++errors; fprintf(stderr, "Unknown SDK validation exception\n");
  }
  if (file.hex.empty()) { fclose(receipt); return 65; }
  fprintf(receipt, "UNISON-DNG-VALIDATION 1\ncandidate-sha256 %s\ncandidate-size %llu\n"
    "driver-build %s\nstructure %s\ndecode %s\nraw-digest %s\n"
    "errors %u\nwarnings %u\nEND\n", file.hex.c_str(),
    static_cast<unsigned long long>(file.size), driver_build, structure, decode, raw,
    errors.load(), warnings.load());
  const bool write_failed = fclose(receipt) != 0;
  // Findings are deliberately reported in the protocol even with exit zero.
  // This exercises the consumer's requirement to examine SDK error counts.
  return write_failed ? 74 : 0;
}
