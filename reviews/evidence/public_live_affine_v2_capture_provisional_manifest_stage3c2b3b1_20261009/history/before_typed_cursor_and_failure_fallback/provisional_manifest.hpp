#pragma once
#include "capture_metadata.hpp"
namespace phase5_public_live_affine_v2 {
enum class ProvisionalManifestMode {LiveUnacceptedDiagnostics,RetainedFailureDiagnostics};
struct ProvisionalManifestSnapshot {
  Count live=0,charges=0,metadata_bytes=0,output_bytes=0,live_ceiling=0,charge_ceiling=0,output_ceiling=0,metadata_ceiling=0;
  bool references_available=false,coverage_available=false;
};
struct ProvisionalManifestObservation {
  const char* stage="NOT_ATTEMPTED";Count physical_bytes=0,consumed_bytes=0,pending_bytes=0,event=0,field=0,last_bits=0;
  bool refused=false,hash_valid=false,last_bits_valid=false;std::string first_error,prefix_sha256;
};
namespace detail {struct ProvisionalManifestIO;struct ManifestWriter;struct ManifestReader;}
class ProvisionalManifestAttempt final {
 public:
  ProvisionalManifestAttempt(const ProvisionalManifestAttempt&)=delete;ProvisionalManifestAttempt& operator=(const ProvisionalManifestAttempt&)=delete;
  ProvisionalManifestAttempt(ProvisionalManifestAttempt&&) noexcept=default;ProvisionalManifestAttempt& operator=(ProvisionalManifestAttempt&&) noexcept=default;
  const ProvisionalManifestObservation& writeObservation() const noexcept{return writer_;}
  const ProvisionalManifestObservation& readObservation() const noexcept{return reader_;}
  bool closedProvisional() const noexcept{return closed_;}bool exactProvisionalReadback() const noexcept{return exact_;}
  bool fullCaptureComplete() const noexcept{return false;}bool fullFlowAccepted() const noexcept{return false;}
 private:
  ProvisionalManifestAttempt()=default;
  std::shared_ptr<OwnedReservation> snapshot_ticket_; // Owns16 slots through snapshot lifetime.
  std::shared_ptr<const void> source_origin_,cost_origin_;std::shared_ptr<detail::CapturePartitionState> partition_;
  ProvisionalManifestSnapshot snapshot_;ProvisionalManifestMode mode_=ProvisionalManifestMode::LiveUnacceptedDiagnostics;
  std::string root_,name_,sha256_;Count bytes_=0,device_=0,inode_=0,directory_device_=0,directory_inode_=0,metadata_events_=0,reference_events_=0,coverage_events_=0;
  ProvisionalManifestObservation writer_,reader_;bool closed_=false,exact_=false;
  friend struct detail::CaptureLeafFactory;friend struct detail::ProvisionalManifestIO;friend struct detail::ManifestWriter;friend struct detail::ManifestReader;
};
}
