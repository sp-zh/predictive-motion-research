#pragma once
#include "working_face_basis.hpp"
#include <memory>
namespace phase5_latest_numeric_context_v1 {
struct Context {
 std::shared_ptr<phase5_working_face_basis_v1::Trace> trace;
 std::uint64_t cycle=0,trial=0;
 // Called immediately BEFORE entering numeric solve. A refusal/exception before
 // hint creation keeps current IDs with explicit unavailable trace.
 void begin(std::uint64_t current_cycle,std::uint64_t current_trial){trace.reset();cycle=current_cycle;trial=current_trial;}
};
}
