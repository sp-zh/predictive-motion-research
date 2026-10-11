#pragma once
#include "integrated_horizon_qp.hpp"
#include <cmath>
#include <limits>
#include <stdexcept>
#include <cfenv>
#if defined(__x86_64__) || defined(__i386__)
#include <xmmintrin.h>
#endif
namespace phase5_active_session_qp_v1 {
struct BoxScreenedRow {int original_row;long double lower_bound,upper_bound;};
struct BoxScreenResult {
 qp::QpProblem solver_problem;
 std::vector<std::string> labels;
 std::vector<int> retained_rows;
 std::vector<BoxScreenedRow> omitted_rows;
 int rounding_mode=0;unsigned x87_control=0,mxcsr=0;
};
// Omit only inequalities implied by explicitly retained original input boxes.
// Outward rounding bounds exact real products/sums of original double entries.
// All original SI rows remain available and are checked again after solve.
inline BoxScreenResult screenLinearInputBoxes(const Problem& p){
 static_assert(std::numeric_limits<long double>::digits>=std::numeric_limits<double>::digits);
 const auto& q=p.original_si;const int rows=q.constraints.rows();
 if(q.constraints.cols()!=NZ||q.lower.size()!=rows||q.upper.size()!=rows||p.rows.size()!=static_cast<std::size_t>(rows))throw std::invalid_argument("screen original matrix/identity shape");
 std::array<double,NZ> lower{},upper{};std::array<bool,NZ> seen{};std::vector<bool> input(rows,false);
 for(int r=0;r<rows;++r)if(p.rows[r].label.rfind("input/",0)==0){
  int col=-1;for(int j=0;j<NZ;++j)if(q.constraints(r,j)!=0){if(col>=0||q.constraints(r,j)!=1)throw std::invalid_argument("screen exact retained unit input box required");col=j;}
  if(col<0||seen[col]||!std::isfinite(q.lower(r))||!std::isfinite(q.upper(r))||q.lower(r)>q.upper(r))throw std::invalid_argument("screen missing/duplicate/invalid input box");
  seen[col]=true;input[r]=true;lower[col]=q.lower(r);upper[col]=q.upper(r);
 }
 for(bool present:seen)if(!present)throw std::invalid_argument("all160 original input boxes must remain");
 BoxScreenResult out;out.rounding_mode=std::fegetround();
#if defined(__x86_64__) || defined(__i386__)
 unsigned short control=0;asm volatile("fnstcw %0":"=m"(control));out.x87_control=control;out.mxcsr=_mm_getcsr();
 if(out.rounding_mode!=FE_TONEAREST||(control&0x0300)!=0x0300||(control&0x0c00)!=0||(out.mxcsr&0xe040)!=0)throw std::invalid_argument("screen requires nearest/full x87 precision/gradual underflow");
#else
 throw std::invalid_argument("screen floating environment proof currently supports x86 only");
#endif
 out.retained_rows.reserve(rows);
 const long double infinity=std::numeric_limits<long double>::infinity();
 for(int r=0;r<rows;++r){bool remove=false;long double lo=0,hi=0;
  if(!input[r]&&q.lower(r)<q.upper(r)){
   for(int j=0;j<NZ;++j){const double a=q.constraints(r,j);if(!std::isfinite(a))throw std::invalid_argument("nonfinite screen coefficient");if(a==0)continue;
    const long double low=static_cast<long double>(a)*(a>0?lower[j]:upper[j]);
    const long double high=static_cast<long double>(a)*(a>0?upper[j]:lower[j]);
    lo=std::nextafter(lo+std::nextafter(low,-infinity),-infinity);
    hi=std::nextafter(hi+std::nextafter(high,infinity),infinity);
   }
   if(!std::isfinite(lo)||!std::isfinite(hi))throw std::invalid_argument("screen interval overflow");
   remove=lo>=static_cast<long double>(q.lower(r))&&hi<=static_cast<long double>(q.upper(r));
  }
  if(remove)out.omitted_rows.push_back({r,lo,hi});else out.retained_rows.push_back(r);
 }
 const int keep=out.retained_rows.size();auto& s=out.solver_problem;s.hessian=q.hessian;s.gradient=q.gradient;s.state_age_seconds=q.state_age_seconds;s.constraints.resize(keep,NZ);s.lower.resize(keep);s.upper.resize(keep);out.labels.reserve(keep);
 for(int r=0;r<keep;++r){const int old=out.retained_rows[r];s.constraints.row(r)=q.constraints.row(old);s.lower(r)=q.lower(old);s.upper(r)=q.upper(old);out.labels.push_back(p.rows[old].label);}
 return out;
}
}
