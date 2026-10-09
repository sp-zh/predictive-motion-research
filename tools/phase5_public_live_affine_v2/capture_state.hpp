#pragma once
#include "foundation.hpp"
#include <array>
#include <functional>
#include <stdexcept>
#include <string_view>
namespace phase5_public_live_affine_v2 {
// Initialized memory is separate from successfully evaluated mathematics.
// Stable field IDs/traversals and stage cursor semantics are in CAPTURE_CONTRACT.
struct MathCaptureTrace {
  const char* stage="NOT_ALLOCATED";
  Count item=0,row=0,column=0,addition=0,memory_item=0;
  const char* memory_stage="DEFINED_PLACEHOLDERS";
  std::array<Count,32> written{};
  bool complete=false,construction_completed=false;
};
class RetainedNumericRegionView final {
 public:
  RetainedNumericRegionView(const RetainedNumericRegionView&)=delete;
  RetainedNumericRegionView& operator=(const RetainedNumericRegionView&)=delete;
  std::string_view role() const noexcept{return role_;}
  Count definedCount() const noexcept{return count_;}
  const MathCaptureTrace& trace() const noexcept{return *trace_;}
  // Failure regions may contain nonfinite IEEE bits; never promote to success.
  double value(Count i) const {if(!*active_||i>=count_)throw std::invalid_argument("retained region outside callback/defined range");return data_[i];}
  RetainedNumericRegionView(std::string_view role,const double* data,Count count,
                            const MathCaptureTrace& trace,const bool& active)
    :role_(role),data_(data),count_(count),trace_(&trace),active_(&active){}
 private:
  std::string_view role_;const double* data_;Count count_;
  const MathCaptureTrace* trace_;const bool* active_;
};
using RetainedRegionConsumer=std::function<void(const RetainedNumericRegionView&)>;
// Merely a bounded borrowed forensic view. No file serializer/publisher exists.
}
