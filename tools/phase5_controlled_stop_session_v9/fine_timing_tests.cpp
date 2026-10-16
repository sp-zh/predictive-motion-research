#include "fine_timing.hpp"
#include <stdexcept>
#include <iostream>
namespace t=phase5_fine_timing_v1;
void need(bool b){if(!b)throw std::runtime_error("timing invariant");}
int main(){
 t::Metrics outer,inner;need(t::active==nullptr);
 {t::Binding bound(outer);{t::Span a(t::Part::GeometryQuery);{t::Span b(t::Part::FkJacobian);}}
 need(outer.calls[0]==1&&outer.calls[1]==1&&outer.seconds[0]>=outer.seconds[1]);
 try{t::Span a(t::Part::Assembly);throw std::runtime_error("retained failure");}catch(const std::runtime_error&){}
 need(outer.calls[static_cast<int>(t::Part::Assembly)]==1);
 {t::Binding nested(inner);{t::Span a(t::Part::Hint);}need(t::active==&inner);}
 need(t::active==&outer&&inner.calls[static_cast<int>(t::Part::Hint)]==1&&outer.calls[static_cast<int>(t::Part::Hint)]==0);
 for(int i=0;i<512;++i){t::Span sampled(t::Part::GradientSample,t::sampleGradient());}
 need(outer.gradient_operations==512&&outer.calls[static_cast<int>(t::Part::GradientSample)]==2);
 }need(t::active==nullptr);{t::Span disabled(t::Part::Hint);}need(inner.calls[static_cast<int>(t::Part::Hint)]==1);
 std::cout<<"PASS timing nesting, exception retention, binding lifetime, unavailable meter and exact1of256 gradient sampling; no Model/native execution\n";
}
