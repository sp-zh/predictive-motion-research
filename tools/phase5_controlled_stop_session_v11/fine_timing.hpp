#pragma once
#include <array>
#include <chrono>
#include <cstdint>
namespace phase5_fine_timing_v1 {
enum class Part {GeometryQuery,FkJacobian,CoalBatch,CoverBatch,GradientSample,Assembly,Hint,NativeWrapper,EvidenceCodecWriteSha,EvidenceFsync,JournalCodecWrite,JournalFsync,Count};
struct Metrics {std::array<double,static_cast<int>(Part::Count)> seconds{};std::array<std::uint64_t,static_cast<int>(Part::Count)> calls{};std::uint64_t gradient_operations=0;};
inline thread_local Metrics* active=nullptr;
class Binding {Metrics* previous_;public:explicit Binding(Metrics& m):previous_(active){active=&m;}~Binding(){active=previous_;}Binding(const Binding&)=delete;};
class Span {using Clock=std::chrono::steady_clock;Metrics* target_;Part part_;Clock::time_point start_;public:explicit Span(Part p,bool enabled=true):target_(enabled?active:nullptr),part_(p){if(target_)start_=Clock::now();}~Span(){if(target_){auto i=static_cast<int>(part_);target_->seconds[i]+=std::chrono::duration<double>(Clock::now()-start_).count();++target_->calls[i];}}Span(const Span&)=delete;};
inline bool sampleGradient(){return active&&((++active->gradient_operations)%256==1);}
}
