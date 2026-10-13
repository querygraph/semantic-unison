// Test-only SDK fixture transcoder. Never invoked by the validation option.
#include "dng_exceptions.h"
#include "dng_file_stream.h"
#include "dng_globals.h"
#include "dng_host.h"
#include "dng_image_writer.h"
#include "dng_info.h"
#include "dng_negative.h"
#include "dng_tag_values.h"
#include "dng_xmp_sdk.h"
#include <cstdio>
#include <cstring>
void UnisonSdkReportError(const char *, const char *);
void UnisonSdkReportWarning(const char *, const char *);
static unsigned errors = 0;
void ReportError(const char *s, const char *d) { ++errors; UnisonSdkReportError(s, d); }
void ReportWarning(const char *s, const char *d) { UnisonSdkReportWarning(s, d); }
int main(int argc, char **argv) {
  if (argc != 4 || (strcmp(argv[1], "jpeg") && strcmp(argv[1], "jxl") &&
                    strcmp(argv[1], "uncompressed"))) return 64;
  try {
    gVerbose = false;
    dng_xmp_sdk::InitializeSDK();
    dng_host host;
    host.SetSaveDNGVersion(dngVersion_1_7_1_0);
    host.SetIgnoreEnhanced(true);
    dng_file_stream source(argv[2]);
    dng_info info;
    info.Parse(host, source);
    info.PostParse(host);
    if (!info.IsValidDNG()) return 65;
    AutoPtr<dng_negative> negative(host.Make_dng_negative());
    negative->Parse(host, source, info);
    negative->PostParse(host, source, info);
    negative->ReadStage1Image(host, source, info);
    negative->ValidateRawImageDigest(host);
    negative->FindRawImageDigest(host);
    negative->FindNewRawImageDigest(host);
    dng_image_writer writer;
    if (!strcmp(argv[1], "jxl")) negative->LosslessCompressJXL(host, writer);
    dng_file_stream target(argv[3], true);
    writer.WriteDNG(host, target, *negative.Get(), nullptr,
                    dngVersion_SaveDefault, !strcmp(argv[1], "uncompressed"));
    return errors ? 65 : 0;
  } catch (const dng_exception &e) {
    fprintf(stderr, "SDK fixture writer failed %d\n", static_cast<int>(e.ErrorCode()));
    return 65;
  }
}
