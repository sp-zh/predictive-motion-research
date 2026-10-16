#pragma once
#include "integrated_horizon_qp.hpp"
#include <cfenv>
#include <limits>
#include <cmath>
#if defined(__x86_64__) || defined(__i386__)
#include <xmmintrin.h>
#endif
namespace phase5_current_alpha_trust_v1 {
namespace core=phase5_active_session_qp_v1;
struct RowProof {int original_row=0;double coefficient_L1_upper=0,seed_lower=0,seed_upper=0,margin_lower=0;};
struct Plan {Eigen::VectorXd center;std::vector<RowProof> rows;double strict_radius=0,solver_radius=0;int limiting_original_row=-1;};
inline double downward(long double x){double d=static_cast<double>(x);if(static_cast<long double>(d)>x)d=std::nextafter(d,-std::numeric_limits<double>::infinity());return d;}
inline double upward(long double x){double d=static_cast<double>(x);if(static_cast<long double>(d)<x)d=std::nextafter(d,std::numeric_limits<double>::infinity());return d;}
inline Plan derive(const core::Problem& p,double original_alpha_cap,double margin_fraction=.125){
 static_assert(std::numeric_limits<long double>::digits>=std::numeric_limits<double>::digits);
 if(std::fegetround()!=FE_TONEAREST||p.original_si.constraints.cols()!=core::NZ||p.original_si.lower.size()!=p.original_si.constraints.rows()||p.original_si.upper.size()!=p.original_si.constraints.rows()||p.seed.size()!=core::NZ||!p.seed.allFinite()||p.rows.size()!=static_cast<std::size_t>(p.original_si.constraints.rows())||!std::isfinite(original_alpha_cap)||original_alpha_cap<=0||!std::isfinite(margin_fraction)||margin_fraction<=0||margin_fraction>.125)throw std::invalid_argument("current alpha trust exact finite shape/nearest/original cap");
#if defined(__x86_64__) || defined(__i386__)
 unsigned short control=0;asm volatile("fnstcw %0":"=m"(control));const auto mxcsr=_mm_getcsr();if((control&0x0300)!=0x0300||(control&0x0c00)!=0||(mxcsr&0xe040)!=0)throw std::invalid_argument("current trust nearest/full x87 precision/gradual underflow required");
#else
 throw std::invalid_argument("current outward trust proof supports x86 only");
#endif
 const long double inf=std::numeric_limits<long double>::infinity();Plan out;out.center=p.seed;out.rows.reserve(2800);double radius=original_alpha_cap;
 for(int r=0;r<p.original_si.constraints.rows();++r){if(p.rows[r].label.rfind("trust/q/half/",0)!=0)continue;long double lo=0,hi=0,l1=0;
  for(int j=0;j<core::NZ;++j){const double a=p.original_si.constraints(r,j);if(!std::isfinite(a))throw std::invalid_argument("finite current joint-trust coefficients");if(j%core::NU==7&&a!=0)throw std::invalid_argument("original joint trust must have exact-zero progress input columns");if(a==0)continue;
   const long double product=static_cast<long double>(a)*p.seed(j);lo=std::nextafter(lo+std::nextafter(product,-inf),-inf);hi=std::nextafter(hi+std::nextafter(product,inf),inf);l1=std::nextafter(l1+std::abs(static_cast<long double>(a)),inf);
  }
  const double lower=p.original_si.lower(r),upper=p.original_si.upper(r);if(!std::isfinite(lower)||!std::isfinite(upper)||lower>=upper)throw std::invalid_argument("finite original joint trust interval");
  const long double margin=std::min(std::nextafter(lo-static_cast<long double>(lower),-inf),std::nextafter(static_cast<long double>(upper)-hi,-inf));const double m=downward(margin),sum=upward(l1);
  if(!std::isfinite(m)||m<=0||!std::isfinite(sum)||sum<0)throw std::invalid_argument("original nominal seed not rigorously interior to current q trust");
  out.rows.push_back({r,sum,downward(lo),upward(hi),m});if(sum>0){const double bound=downward(std::nextafter(static_cast<long double>(margin_fraction)*static_cast<long double>(m)/static_cast<long double>(sum),-inf));if(bound<radius){radius=bound;out.limiting_original_row=r;}}
 }
 if(out.rows.size()!=2800||!std::isfinite(radius)||radius<=0||radius>original_alpha_cap)throw std::invalid_argument("complete current2800 bounded-margin q trust derivation");
 out.strict_radius=radius;out.solver_radius=std::nextafter(radius*.999,0.);if(!(out.solver_radius>0&&out.solver_radius<out.strict_radius))throw std::invalid_argument("strict inward current alpha trust planning margin");return out;
}
}
