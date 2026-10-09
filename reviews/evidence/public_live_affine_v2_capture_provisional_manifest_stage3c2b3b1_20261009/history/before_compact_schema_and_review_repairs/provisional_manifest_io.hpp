#pragma once
#include "provisional_manifest.hpp"
namespace phase5_public_live_affine_v2::detail {
struct ManifestEventSource {
  std::function<void(const MetadataConsumer&)> metadata;
  std::function<void(const ReferenceConsumer&)> references;
  std::function<void(const CoverageConsumer&)> coverage;
};
struct ProvisionalManifestIO {
 private:
  static void write(SharedCaseBudget,ProvisionalManifestAttempt&,const ManifestEventSource&);
  static void read(SharedCaseBudget,ProvisionalManifestAttempt&,const ManifestEventSource&);
  friend struct CaptureLeafFactory;
};
}
