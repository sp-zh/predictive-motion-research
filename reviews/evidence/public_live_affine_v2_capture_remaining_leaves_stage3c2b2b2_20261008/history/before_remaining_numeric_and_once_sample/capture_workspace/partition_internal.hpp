#pragma once
#include "capture_workspace.hpp"
namespace phase5_public_live_affine_v2::detail {
struct CostFactory;
class CapturePartitionState final {
 private:
  CapturePartitionState(std::shared_ptr<const void> origin,SharedCaseBudget b,const ResourcePlan& p,const FactorShape& f,
                        const FileIdentity& file,const std::string& semantic)
    :source_origin(std::move(origin)),budget(std::move(b)),plan(p),shape(f),input(file),semantic_sha(semantic){}
  const std::shared_ptr<const void> source_origin;const SharedCaseBudget budget;const ResourcePlan plan;const FactorShape shape;
  const FileIdentity input;const std::string semantic_sha;CaptureWorkspaceObservation status;
  void reject(const char* why) noexcept{if(status.refused)return;status.refused=true;try{status.first_error=why?why:"CAPTURE_PARTITION_REFUSAL";}catch(...){}}
  friend struct CaptureWorkspaceFactory;friend struct CaptureLeafFactory;friend struct CostInputFactory;friend struct CostFactory;
  friend class phase5_public_live_affine_v2::CaptureWorkspaceGrant;
  friend class phase5_public_live_affine_v2::CaptureWorkspaceObserver;
};
}
