#pragma once
#include "affine_assembly.hpp"
namespace phase5_public_live_affine_v2 {
namespace detail {class CapturePartitionState;struct CaptureWorkspaceFactory;struct CostInputFactory;struct CaptureLeafFactory;}
struct CaptureWorkspaceObservation {
  const char* policy="CAPTURE_WORKSPACE_PARTITION_1";
  Count catalogue_role_upper=0,ancillary_numeric_limit=32,cell_control_split_extra=0;
  Count receipt_limit=0,credit_slots=0,planned_work=0,topology_slots=0,input_cache_slots=16;
  Count required_actual_work=0,remaining_actual_work=0,allocated_work=0;
  Count owned_capture_buffer_slots=0,borrowed_slice_slots=0;
  bool prepared=false,attempted=false,validated=false,cost_consumed=false,applied=false,refused=false;
  std::string first_error;
};
class CaptureWorkspaceObserver final {
 public:
  CaptureWorkspaceObservation observation() const;
 private:
  explicit CaptureWorkspaceObserver(std::shared_ptr<detail::CapturePartitionState> s):state_(std::move(s)){}
  std::shared_ptr<detail::CapturePartitionState> state_;friend class CaptureWorkspaceGrant;
};
class CaptureWorkspaceGrant final {
 public:
  CaptureWorkspaceGrant(const CaptureWorkspaceGrant&)=delete;CaptureWorkspaceGrant& operator=(const CaptureWorkspaceGrant&)=delete;
  CaptureWorkspaceGrant(CaptureWorkspaceGrant&&) noexcept=default;CaptureWorkspaceGrant& operator=(CaptureWorkspaceGrant&&) noexcept=default;
  CaptureWorkspaceObservation observation() const;
  bool readyForOneAdmission() const noexcept;
  CaptureWorkspaceObserver observer() const;
 private:
  explicit CaptureWorkspaceGrant(std::shared_ptr<detail::CapturePartitionState>);
  std::shared_ptr<detail::CapturePartitionState> state_;
  friend struct detail::CaptureWorkspaceFactory;friend struct detail::CostInputFactory;friend struct detail::CaptureLeafFactory;
};
CaptureWorkspaceGrant prepareCaptureWorkspaceV1(const AffineAssemblyOutcome&);
// A private source/case-bound precondition, no idlepool, buffer, slice or READY.
}
