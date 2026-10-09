#pragma once
#include "provisional_manifest.hpp"
namespace phase5_public_live_affine_v2::detail {
class ManifestAttemptRowView final {
 public:
  ManifestAttemptRowView(const ManifestAttemptRowView&)=delete;ManifestAttemptRowView& operator=(const ManifestAttemptRowView&)=delete;
 private:
  ManifestAttemptRowView(const BoundLeafAttempt* a,Count index,std::string_view root,bool source,bool cost,bool partition):actual_(a),index_(index),first_root_(root),source_matches_(source),cost_matches_(cost),partition_matches_(partition){}
  const BoundLeafAttempt* actual_;Count index_;std::string_view first_root_;bool source_matches_,cost_matches_,partition_matches_;
  friend struct CaptureLeafFactory;friend struct ManifestWriter;friend struct ManifestReader;
};
using ManifestAttemptConsumer=std::function<void(const ManifestAttemptRowView&)>;
struct ManifestEventSource {
  Count attempt_count=0;std::function<void(const ManifestAttemptConsumer&)> attempts;
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
