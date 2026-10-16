#pragma once
#include <array>
#include <vector>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <stdexcept>
namespace phase5_actual_stop_monitor_v1 {
using Seven=std::array<double,7>;
struct Spec {double velocity=.0001,acceleration=.001,command_velocity=.000001,command_acceleration=.0001,progress_rate=.000001,progress_acceleration=.0001,command_drift=.000001,progress_drift=.000001;std::uint64_t required_halves=50,maximum_halves=178;};
struct Point {std::uint64_t actual_global_half=0;double simulation_time=0;Seven actual_velocity{},actual_acceleration{},command_C{},accepted_w{},accepted_alpha{};double s=0,r=0,b=0;bool complete_actual_guards=false;};
struct Record {Point point;bool below_thresholds=false,hold_drift_pass=false;std::uint64_t consecutive=0;double C_drift=0,s_drift=0;};
class Monitor {Spec s_;std::uint64_t next_,consecutive_=0;double first_time_=0,last_time_=0,anchor_s_=0;Seven anchor_C_{};bool anchor_=false,failed_=false;std::vector<Record> records_;static void need(bool b,const char* m){if(!b)throw std::invalid_argument(m);}static double maxabs(const Seven& a){double v=0;for(double x:a){need(std::isfinite(x),"finite actual stop vectors");v=std::max(v,std::abs(x));}return v;}public:
 Monitor(const Spec& s,std::uint64_t first_actual_half):s_(s),next_(first_actual_half){need(s.velocity==.0001&&s.acceleration==.001&&s.command_velocity==.000001&&s.command_acceleration==.0001&&s.progress_rate==.000001&&s.progress_acceleration==.0001&&s.command_drift==.000001&&s.progress_drift==.000001&&s.required_halves==50&&s.maximum_halves==178&&first_actual_half>1000,"fixed prospective component stop criteria and finite scope");records_.reserve(s.maximum_halves);}
 const Spec& spec()const{return s_;}const std::vector<Record>& records()const{return records_;}std::uint64_t consecutive()const{return consecutive_;}bool failed()const{return failed_;}bool passed()const{return !failed_&&consecutive_>=s_.required_halves;}
 void actualHalf(const Point& p){try{need(!failed_,"stop monitor structural failure is terminal");need(records_.size()<s_.maximum_halves&&p.actual_global_half==next_&&p.complete_actual_guards&&std::isfinite(p.simulation_time)&&std::isfinite(p.s)&&std::isfinite(p.r)&&std::isfinite(p.b),"unique complete actual guarded physical stop observation");need(p.s>=0&&p.s<=1&&p.r>=0,"original progress domain in stop observation");if(!records_.empty())need(std::abs((p.simulation_time-last_time_)-.002)<=1e-10,"actual stop fixed2ms order");maxabs(p.command_C);const double actual_v=maxabs(p.actual_velocity),actual_a=maxabs(p.actual_acceleration),command_w=maxabs(p.accepted_w),command_alpha=maxabs(p.accepted_alpha);Record r;r.point=p;r.below_thresholds=actual_v<=s_.velocity&&actual_a<=s_.acceleration&&command_w<=s_.command_velocity&&command_alpha<=s_.command_acceleration&&p.r<=s_.progress_rate&&std::abs(p.b)<=s_.progress_acceleration;
  if(r.below_thresholds){if(!anchor_){anchor_=true;anchor_C_=p.command_C;anchor_s_=p.s;first_time_=p.simulation_time;}for(int j=0;j<7;++j)r.C_drift=std::max(r.C_drift,std::abs(p.command_C[j]-anchor_C_[j]));r.s_drift=std::abs(p.s-anchor_s_);r.hold_drift_pass=r.C_drift<=s_.command_drift&&r.s_drift<=s_.progress_drift;if(r.hold_drift_pass)++consecutive_;else{anchor_=false;consecutive_=0;}}
  else{anchor_=false;consecutive_=0;}r.consecutive=consecutive_;records_.push_back(r);last_time_=p.simulation_time;++next_;if(passed())need(std::abs((last_time_-first_time_+.002)-.002*consecutive_)<=1e-9,"actual dwell duration from consecutive2ms samples");
 }catch(...){failed_=true;throw;}
 }
};
}
