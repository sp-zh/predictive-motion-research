#pragma once
#include "bounded_row_progress_seed_v5.hpp"
#include <cstring>
namespace phase5_bounded_global_interval_seed_v6 {
using Legacy=phase5_bounded_row_progress_seed_v5::Result;
using Correction=phase5_bounded_row_progress_seed_v5::Correction;
struct Scan {
 int iteration=0,limiting_upper_row=-1,selected_row=-1;
 bool bound_available=false,limiter_available=false,selected_available=false;
 double upper_high=0,upper_residual=0,epsilon_high=0,epsilon_residual=0;
 double limiter_value=0,limiter_travel=0,limiter_lower=0,limiter_upper=0;
};
struct Result:Legacy {
 bool legacy_summary_available=false,legacy_complete=false,legacy_retry_available=false,legacy_seed_available=false,global_scope_eligible=false,global_scope_entered=false;
 std::size_t legacy_corrections_count=0,legacy_rows_written=0,global_scan_attempts=0;
 double legacy_initial_violation=0,legacy_interval_lower=0,legacy_interval_upper=0;
 std::string legacy_error;
 std::vector<Scan> global_scans;
};
constexpr std::uint64_t conservative_inventory58=phase5_bounded_row_progress_seed_v5::conservative_initializer_inventory56+8*24+512;
static_assert(sizeof(Scan)<=24*sizeof(double),"bounded exact-upper metadata per scan");
static_assert(conservative_inventory58==246770&&conservative_inventory58<250000,"old V5 peak plus bounded8 scan records/working144 vector and scalars fits unchanged250K; AS4GiB still mandatory");
inline void exactSplit(long double value,double& high,double& residual){
 if(!std::isfinite(value))throw std::invalid_argument("finite fullray bound before serialization");
 high=static_cast<double>(value);
 if(!std::isfinite(high))throw std::invalid_argument("serializable fullray bound high");
 residual=static_cast<double>(value-static_cast<long double>(high));
 if(!std::isfinite(residual)||static_cast<long double>(high)+static_cast<long double>(residual)!=value)
  throw std::invalid_argument("fullray bound not exactly representable by two saved binary64 values; retained refusal");
}
inline Scan originalUniformUpper(const Eigen::VectorXd&value,const Eigen::VectorXd&travel,const Eigen::VectorXd&lo,const Eigen::VectorXd&hi,int iteration){
 auto need=[](bool ok,const char*why){if(!ok)throw std::invalid_argument(why);};
 need(value.size()>0&&value.size()<=20000&&travel.size()==value.size()&&lo.size()==value.size()&&hi.size()==value.size()&&value.allFinite()&&travel.allFinite()&&lo.allFinite()&&hi.allFinite()&&(lo.array()<=hi.array()).all(),"finite fullray upper arrays");
   long double upper=1e-6L;int limiter=-1;
   for(int r=0;r<value.size();++r){const long double t=travel(r),v=value(r);if(t!=0){
    const long double bound=t>0?(static_cast<long double>(hi(r))+1e-12L-v)/t:(static_cast<long double>(lo(r))-1e-12L-v)/t;
    need(std::isfinite(bound),"finite original row uniform upper bound");if(bound<upper){upper=bound;limiter=r;}
   }}
   Scan scan;scan.iteration=iteration;scan.limiting_upper_row=limiter;
   exactSplit(upper,scan.upper_high,scan.upper_residual);
   const long double epsilon=std::max(0.L,upper);exactSplit(epsilon,scan.epsilon_high,scan.epsilon_residual);scan.bound_available=true;
   if(limiter>=0){scan.limiter_available=true;scan.limiter_value=value(limiter);scan.limiter_travel=travel(limiter);scan.limiter_lower=lo(limiter);scan.limiter_upper=hi(limiter);}
 return scan;
}
inline Result prepare(const Eigen::MatrixXd&A,const Eigen::VectorXd&lo,const Eigen::VectorXd&hi,const Eigen::VectorXd&nominal,const Eigen::VectorXd&scale){
 Result out;static_cast<Legacy&>(out)=phase5_bounded_row_progress_seed_v5::prepare(A,lo,hi,nominal,scale);
 out.legacy_summary_available=true;out.legacy_complete=out.complete;out.legacy_retry_available=out.retry_available;out.legacy_seed_available=out.retry.seed.size()==144&&out.retry.seed.allFinite();out.legacy_error=out.error;
 out.legacy_corrections_count=out.corrections.size();out.legacy_rows_written=out.retry.row_bounds_written;
 out.legacy_initial_violation=out.retry.initial_violation;out.legacy_interval_lower=out.retry.interval_lower;out.legacy_interval_upper=out.retry.interval_upper;
 const std::string nointerior="bounded initializer ray has no interior; wholepolytope unknown";
 out.global_scope_eligible=!out.complete&&out.error==nointerior&&out.retry_available;
 // All previously successful V5 results, all other failures and the exhausted
 // original shared8 correction budget return byte-identical legacy math.
 if(!out.global_scope_eligible||out.corrections.size()>=8)return out;
 auto need=[](bool ok,const char*why){if(!ok)throw std::invalid_argument(why);};
 try{
  need(A.rows()>0&&A.rows()<=20000&&A.cols()==144&&lo.size()==A.rows()&&hi.size()==A.rows()&&nominal.size()==144&&scale.size()==144&&A.allFinite()&&lo.allFinite()&&hi.allFinite()&&nominal.allFinite()&&scale.allFinite()&&(scale.array()>0).all()&&(lo.array()<=hi.array()).all(),"validated fullray fallback shapes and arrays before allocation");
  need(out.retry.seed.size()==144&&out.retry.seed.allFinite()&&out.retry.row_bounds_written==static_cast<std::size_t>(A.rows()),"legacy nointerior full measured row table and seed available");
  for(const auto&c:out.corrections)need(c.applied&&c.error.empty(),"legacy nointerior prefix consists of applied corrections");
  Eigen::VectorXd working=std::move(out.retry.seed);
  for(int j=0;j<144;++j)if(j%8!=7)need(std::memcmp(&working(j),&nominal(j),sizeof(double))==0,"legacy nonbeta bits preserved before fullray fallback");
  // Free the old table before the new helper/table allocations. Retain its
  // actual scalar refusal and correction prefix; old evidence is immutable.
  out.retry=phase5_bounded_progress_seed_v1::Result{};out.retry_available=false;
  out.global_scope_entered=true;out.global_scans.reserve(8);
  Eigen::VectorXd ray=Eigen::VectorXd::Zero(144);for(int k=0;k<18;++k)ray(8*k+7)=1/scale(8*k+7);
  const Eigen::VectorXd travel=A*ray;need(ray.allFinite()&&travel.allFinite(),"finite unchanged free18beta uniform direction");
  for(int iteration=static_cast<int>(out.legacy_corrections_count);iteration<8;++iteration){
   ++out.global_scan_attempts;const Eigen::VectorXd value=A*working;need(value.allFinite(),"finite fullray current row values");
   Scan scan=originalUniformUpper(value,travel,lo,hi,iteration);const long double epsilon=static_cast<long double>(scan.epsilon_high)+static_cast<long double>(scan.epsilon_residual);
   int bad=-1;double gap=1e-12;
   for(int r=0;r<A.rows();++r){const double v=std::max({0.,lo(r)-value(r),value(r)-hi(r)});
    const long double useful=static_cast<long double>(value(r)<lo(r)?std::max(0.,travel(r)):std::max(0.,-travel(r)))*epsilon;
    const long double required=static_cast<long double>(v)-1e-12L;
    if(v>gap&&required>useful&&std::isfinite(required)&&std::isfinite(useful)&&static_cast<double>(required)>static_cast<double>(useful)){bad=r;gap=v;}
   }
   need(out.global_scans.size()<8,"bounded fullray scans before append");
   if(bad>=0){scan.selected_available=true;scan.selected_row=bad;}
   out.global_scans.push_back(scan);if(bad<0)break;
   Correction metadata;metadata.iteration=iteration;metadata.row=bad;metadata.before=value(bad);metadata.lower=lo(bad);metadata.upper=hi(bad);metadata.uniform_travel=travel(bad);
   metadata.required_domain_improvement=static_cast<double>(static_cast<long double>(gap)-1e-12L);
   metadata.useful_uniform_change=static_cast<double>(static_cast<long double>(value(bad)<lo(bad)?std::max(0.,travel(bad)):std::max(0.,-travel(bad)))*epsilon);
   metadata.eligibility_reason=travel(bad)==0?1:2;metadata.eligibility_available=true;
   need(out.corrections.size()<8,"original shared8 correction budget before append");out.corrections.push_back(std::move(metadata));auto&c=out.corrections.back();
   try{
    need(std::isfinite(c.required_domain_improvement)&&std::isfinite(c.useful_uniform_change)&&c.required_domain_improvement>c.useful_uniform_change,"saved strict fullray reach deficit");
    need(gap<=1e-10,"row seed deficit beyond original rounding repair scope; wholepolytope unknown");
    Eigen::VectorXd physical=Eigen::VectorXd::Zero(144);double norm2=0;
    for(int k=0;k<18;++k){const int j=8*k+7;physical(j)=A(bad,j)/scale(j);norm2+=physical(j)*physical(j);}
    need(physical.allFinite()&&std::isfinite(norm2)&&norm2>0,"row has no finite freeprogress corrective direction; wholepolytope unknown");
    const double target=value(bad)<lo(bad)?lo(bad):hi(bad),amount=(target-value(bad))/norm2;need(std::isfinite(amount),"finite row corrective amount");
    Eigen::VectorXd delta=Eigen::VectorXd::Zero(144);for(int k=0;k<18;++k){const int j=8*k+7;delta(j)=amount*physical(j)/scale(j);}
    need(delta.allFinite(),"finite proposed differential delta");c.delta=std::move(delta);c.delta_available=true;
    const Eigen::VectorXd step=scale.array()*c.delta.array();if(step.allFinite()){c.physical_delta_inf=step.cwiseAbs().maxCoeff();c.step_norm_available=true;}
    need(c.step_norm_available&&c.physical_delta_inf<=1e-6,"original differential seed displacement cap; no clipping");
    Eigen::VectorXd proposed=working;for(int k=0;k<18;++k){const int j=8*k+7;proposed(j)+=c.delta(j);}need(proposed.allFinite(),"finite proposed row seed");
    const Eigen::VectorXd total=scale.array()*(proposed-nominal).array();if(total.allFinite()){c.total_physical_delta_inf=total.cwiseAbs().maxCoeff();c.total_norm_available=true;}
    need(c.total_norm_available&&c.total_physical_delta_inf<=1e-6,"original combined legacy plus fullray displacement cap");
    const Eigen::VectorXd after=A*proposed;need(after.allFinite(),"finite proposed allrow values");c.after=after(bad);c.full_violation=std::max({0.,(lo-after).maxCoeff(),(after-hi).maxCoeff()});c.after_available=true;
    working=std::move(proposed);c.applied=true;out.row_changed=true;
   }catch(const std::exception&e){c.error=e.what();throw;}
  }
  out.retry=phase5_bounded_progress_seed_v1::prepare(A,lo,hi,working,scale);out.retry_available=true;
  need(out.retry.complete&&out.retry.error.empty(),out.retry.error.c_str());
  for(int j=0;j<144;++j)if(j%8!=7)out.retry.seed(j)=nominal(j);
  need((scale.array()*(out.retry.seed-nominal).array()).abs().maxCoeff()<=1e-6,"original total initializer displacement after fullray and uniform");
  const Eigen::VectorXd final=A*out.retry.seed;need(final.allFinite()&&std::max({0.,(lo-final).maxCoeff(),(final-hi).maxCoeff()})<=1e-12,"original final allrow seed allowance unchanged");
  out.complete=true;out.error.clear();
 }catch(const std::exception&e){out.complete=false;out.error=e.what();}
 return out;
}
// This guard uses a computed necessary upper on one original uniform ray;
// its binary80 value is saved exactly as two binary64 values. It proves no
// wholepolytope/physical property. All original native/SI/B/C/stop gates remain.
}
