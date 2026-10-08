#include "public_affine_horizon_internal.hpp"
#include <Eigen/LU>
#include <algorithm>
#include <cmath>

namespace phase5_public_affine_horizon {
namespace detail {
void fixed(const Limits& l){
 const Limits d;
 require(l.max_cases==d.max_cases&&l.max_cells==d.max_cells&&l.max_samples==d.max_samples&&
 l.max_nx==d.max_nx&&l.max_nu==d.max_nu&&l.max_terms==d.max_terms&&
 l.max_factor_rows==d.max_factor_rows&&l.max_matrix_elements==d.max_matrix_elements&&
 l.max_document_bytes==d.max_document_bytes&&l.max_problem_numeric_elements==d.max_problem_numeric_elements&&
 l.max_cli_numeric_elements==d.max_cli_numeric_elements&&l.arithmetic_abs==d.arithmetic_abs&&
 l.arithmetic_rel==d.arithmetic_rel,"fixed v1 limits/tolerances altered");
}
void finite(const Matrix& x){require(x.allFinite(),"nonfinite matrix/intermediate");}
void finite(const Vector& x){require(x.allFinite(),"nonfinite vector/intermediate");}
Matrix zeros(std::size_t r,std::size_t c,ProblemBudget& b){
 auto n=mul(r,c);require(n<=b.limits.max_matrix_elements,"single matrix element cap");
 require(r<=std::size_t(std::numeric_limits<Eigen::Index>::max())&&c<=std::size_t(std::numeric_limits<Eigen::Index>::max()),"Eigen index overflow");
 b.reserve(n);return Matrix::Zero(r,c);
}
Vector zeros(std::size_t r,ProblemBudget& b){require(r<=b.limits.max_matrix_elements,"vector element cap");b.reserve(r);return Vector::Zero(r);}
double maximum(const Matrix& x){return x.size()?x.cwiseAbs().maxCoeff():0;}
double maximum(const Vector& x){return x.size()?x.cwiseAbs().maxCoeff():0;}
void bound(long double v){require(std::isfinite(v)&&v<=std::numeric_limits<double>::max(),"arithmetic overflow bound");}
Matrix product(const Matrix& a,const Matrix& c,ProblemBudget& b){
 require(a.cols()==c.rows(),"product shape");finite(a);finite(c);
 bound(static_cast<long double>(maximum(a))*maximum(c)*a.cols());
 auto x=zeros(a.rows(),c.cols(),b);
 // Conservative expression scratch bound; explicit destination avoids aliasing.
 b.reserve(add(a.size(),c.size()));x.noalias()=a*c;finite(x);return x;
}
Vector product(const Matrix& a,const Vector& c,ProblemBudget& b){
 require(a.cols()==c.size(),"vector product shape");finite(a);finite(c);
 bound(static_cast<long double>(maximum(a))*maximum(c)*a.cols());
 auto x=zeros(a.rows(),b);b.reserve(add(a.size(),c.size()));x.noalias()=a*c;finite(x);return x;
}
Matrix plus(const Matrix& a,const Matrix& c,ProblemBudget& b){
 require(a.rows()==c.rows()&&a.cols()==c.cols(),"addition shape");finite(a);finite(c);
 bound(static_cast<long double>(maximum(a))+maximum(c));auto x=zeros(a.rows(),a.cols(),b);x=a+c;finite(x);return x;
}
Vector plus(const Vector& a,const Vector& c,ProblemBudget& b){
 require(a.size()==c.size(),"vector addition shape");finite(a);finite(c);
 bound(static_cast<long double>(maximum(a))+maximum(c));auto x=zeros(a.size(),b);x=a+c;finite(x);return x;
}
double dot(const Vector& a,const Vector& c){
 require(a.size()==c.size(),"dot shape");finite(a);finite(c);
 bound(static_cast<long double>(maximum(a))*maximum(c)*a.size());
 double v=a.dot(c);require(std::isfinite(v),"nonfinite scalar intermediate");return v;
}
bool exact(const Vector& a,const Vector& c){return a.size()==c.size()&&(a.array()==c.array()).all();}
double residual(const Matrix& A,const Matrix& B,const Vector& d,const Vector& o,const Vector& u,const Vector& e,const Limits& l,ProblemBudget& b){
 Vector pred=plus(plus(product(A,o,b),product(B,u,b),b),d,b);
 require(pred.size()==e.size(),"nominal endpoint shape");finite(e);double maxerr=0;
 for(Eigen::Index i=0;i<e.size();++i){
  long double err=std::abs(static_cast<long double>(pred(i))-e(i));
  bound(err);maxerr=std::max(maxerr,static_cast<double>(err));
  require(err<=static_cast<long double>(l.arithmetic_abs)+static_cast<long double>(l.arithmetic_rel)*std::max(std::abs(pred(i)),std::abs(e(i))),"nominal affine defect inconsistent");
 }
 return maxerr;
}
}
using namespace detail;
void ProblemBudget::reserve(std::size_t n){
 fixed(limits);auto p=add(charged_numeric_elements,n),c=add(cli.charged_numeric_elements,n);
 require(planned_numeric_elements<=limits.max_problem_numeric_elements,"planned ceiling exceeds fixed problem cap");
 require(p<=planned_numeric_elements,"allocation would exceed planned case numeric ceiling");
 require(p<=limits.max_problem_numeric_elements,"problem cumulative numeric element cap");
 require(c<=limits.max_cli_numeric_elements,"CLI cumulative numeric element cap");
 charged_numeric_elements=p;cli.charged_numeric_elements=c;
}
Assembly assemble(const Problem& p,const Limits& l,ProblemBudget& b){
 fixed(l);require(&b.limits==&l,"budget limits identity");
 const auto n=p.nx,u=p.nu,N=p.cells.size();
 require(n>0&&n<=l.max_nx&&u>0&&u<=l.max_nu&&N>0&&N<=l.max_cells,"problem dimension caps");
 require(p.samples.size()<=l.max_samples,"sample count cap");
 require(p.actual_initial.size()==Eigen::Index(n),"initial shape");finite(p.actual_initial);
 const auto dx=mul(n,add(N,1)),du=mul(u,N),dy=add(dx,du);
 for(const auto& c:p.cells){require(c.cycles>0&&c.cycles<=int(l.max_samples/2),"cycle cap");
  require(c.A.rows()==Eigen::Index(n)&&c.A.cols()==Eigen::Index(n)&&c.B.rows()==Eigen::Index(n)&&c.B.cols()==Eigen::Index(u)&&c.defect.size()==Eigen::Index(n),"transition shape");finite(c.A);finite(c.B);finite(c.defect);}
 const bool pub=p.source.kind=="public_saved_json"||p.source.kind=="public_saved_native";
 require(pub||p.source.kind=="generic_synthetic","source kind");
 if(pub){require(n==30&&u==8&&p.source.full_nominal_source_certified&&p.nominal_cells.size()==N&&p.nominal_samples.size()==p.samples.size(),"public full nominal descriptor required");}
 else require(p.nominal_cells.empty()&&p.nominal_samples.empty()&&!p.source.full_nominal_source_certified,"synthetic physical certificate forbidden");
 Assembly a;a.recursive_states.reserve(N+1);a.samples.reserve(p.samples.size());a.L=zeros(dx,dx,b);a.L.diagonal().setOnes();a.E=zeros(dx,du,b);a.f=zeros(dx,b);a.f.head(n)=p.actual_initial;
 a.initial_selector=zeros(dx,n,b);a.initial_selector.topRows(n).diagonal().setOnes();
 AffineView first;first.offset=zeros(n,b);first.offset=p.actual_initial;first.control=zeros(n,du,b);first.initial=zeros(n,n,b);first.initial.diagonal().setOnes();a.recursive_states.push_back(std::move(first));
 a.nominal_cell_defect_residual_max=zeros(pub?N:0,b);a.nominal_sample_defect_residual_max=zeros(pub?p.samples.size():0,b);
 for(std::size_t c=0;c<N;++c){const auto& m=p.cells[c];const auto& previous=a.recursive_states[c];
  a.L.block((c+1)*n,c*n,n,n)=-m.A;a.E.block((c+1)*n,c*u,n,u)=m.B;a.f.segment((c+1)*n,n)=m.defect;
  AffineView next;next.offset=plus(product(m.A,previous.offset,b),m.defect,b);
  next.control=product(m.A,previous.control,b);auto selector=zeros(n,du,b);selector.block(0,c*u,n,u)=m.B;next.control=plus(next.control,selector,b);
  next.initial=product(m.A,previous.initial,b);a.recursive_states.push_back(std::move(next));
  if(pub){const auto& v=p.nominal_cells[c];require(v.origin.size()==Eigen::Index(n)&&v.input.size()==Eigen::Index(u)&&v.endpoint.size()==Eigen::Index(n),"nominal cell shape");
   if(c)require(exact(v.origin,p.nominal_cells[c-1].endpoint),"literal nominal cell origin mismatch");
   a.nominal_cell_defect_residual_max(c)=residual(m.A,m.B,m.defect,v.origin,v.input,v.endpoint,l,b);}
 }
 finite(a.L);finite(a.E);finite(a.f);
 // Independent pivoted elimination, never populated from recursive arrays.
 b.reserve(add(mul(8,mul(dx,dx)),mul(6,mul(dx,add(add(du,n),1)))));
 Eigen::FullPivLU<Matrix> lu(a.L);require(lu.isInvertible(),"lifted dynamics singular");
 a.X_control=zeros(dx,du,b);a.X_control=lu.solve(a.E);finite(a.X_control);
 a.X_offset=zeros(dx,b);a.X_offset=lu.solve(a.f);finite(a.X_offset);
 a.X_initial=zeros(dx,n,b);a.X_initial=lu.solve(a.initial_selector);finite(a.X_initial);
 a.T=zeros(dy,du,b);a.T.topRows(dx)=a.X_control;a.T.bottomRows(du).diagonal().setOnes();a.t=zeros(dy,b);a.t.head(dx)=a.X_offset;
 int lastCell=-1,lastCycle=0,lastHalf=0;
 for(std::size_t j=0;j<p.samples.size();++j){const auto& s=p.samples[j];
  require(s.cell<N&&s.cycle>=1&&s.cycle<=p.cells[s.cell].cycles&&(s.half==1||s.half==2),"sample index");
  require(int(s.cell)>lastCell||(int(s.cell)==lastCell&&(s.cycle>lastCycle||(s.cycle==lastCycle&&s.half>lastHalf))),"sample order/duplicate");
  lastCell=s.cell;lastCycle=s.cycle;lastHalf=s.half;
  require(s.A.rows()==Eigen::Index(n)&&s.A.cols()==Eigen::Index(n)&&s.B.rows()==Eigen::Index(n)&&s.B.cols()==Eigen::Index(u)&&s.defect.size()==Eigen::Index(n),"sample shape");finite(s.A);finite(s.B);finite(s.defect);
  SampleView v;v.cell=s.cell;v.cycle=s.cycle;v.half=s.half;const auto& origin=a.recursive_states[s.cell];
  v.recursive.offset=plus(product(s.A,origin.offset,b),s.defect,b);v.recursive.control=product(s.A,origin.control,b);
  auto own=zeros(n,du,b);own.block(0,s.cell*u,n,u)=s.B;v.recursive.control=plus(v.recursive.control,own,b);
  v.recursive.initial=product(s.A,origin.initial,b);
  v.lifted_factor=zeros(n,dy,b);v.lifted_factor.block(0,s.cell*n,n,n)=s.A;v.lifted_factor.block(0,dx+s.cell*u,n,u)=s.B;
  v.lifted_offset=zeros(n,b);v.lifted_offset=s.defect;
  v.eliminated.control=product(v.lifted_factor,a.T,b);v.eliminated.offset=plus(product(v.lifted_factor,a.t,b),s.defect,b);
  Matrix initial_y=zeros(dy,n,b);initial_y.topRows(dx)=a.X_initial;v.eliminated.initial=product(v.lifted_factor,initial_y,b);
  if(pub){const auto& nom=p.nominal_samples[j];require(exact(nom.origin,p.nominal_cells[s.cell].origin)&&exact(nom.input,p.nominal_cells[s.cell].input),"sample literal cell origin/input mismatch");
   a.nominal_sample_defect_residual_max(j)=residual(s.A,s.B,s.defect,nom.origin,nom.input,nom.endpoint,l,b);}
  a.samples.push_back(std::move(v));
 }
 return a;
}
namespace {
Matrix transposed(const Matrix& m,ProblemBudget& b){auto x=detail::zeros(m.cols(),m.rows(),b);x=m.transpose();return x;}
double scalarAdd(double a,double c){detail::bound(std::abs(static_cast<long double>(a))+std::abs(static_cast<long double>(c)));double x=a+c;detail::require(std::isfinite(x),"scalar addition overflow");return x;}
CondensedTerm condense(const Assembly& a,CondensedTerm t,ProblemBudget& b){
 t.factor=detail::product(t.used_F,a.T,b);t.offset=detail::plus(detail::product(t.used_F,a.t,b),t.used_f0,b);
 auto ft=transposed(t.factor,b);t.H=detail::product(ft,t.factor,b);
 auto tt=transposed(a.T,b);t.g=detail::plus(detail::product(ft,t.offset,b),detail::product(tt,t.used_linear,b),b);
 t.constant=scalarAdd(scalarAdd(.5*detail::dot(t.offset,t.offset),detail::dot(t.used_linear,a.t)),t.used_constant);return t;
}
}
Objective substitute(const Assembly& a,const std::vector<FactorTerm>& terms,const Limits& l,ProblemBudget& b){
 fixed(l);require(terms.size()<=l.max_terms,"term count cap");const auto dy=a.T.rows(),du=a.T.cols();Objective o;o.terms.reserve(terms.size());std::size_t totalRows=0;
 for(const auto& in:terms){require(!in.name.empty()&&!in.units.empty(),"term name/units");require(in.F.cols()==dy&&in.F.rows()>=1&&in.F.rows()<=Eigen::Index(l.max_factor_rows)&&in.f0.size()==in.F.rows()&&in.linear.size()==dy,"factor shape");
  finite(in.F);finite(in.f0);finite(in.linear);require(std::isfinite(in.constant),"factor constant finite");
  require(in.sample_additions.size()<=l.max_samples,"sample additions cap");
  CondensedTerm t;t.name=in.name;t.units=in.units;t.used_F=zeros(in.F.rows(),dy,b);t.used_F=in.F;t.used_f0=zeros(in.f0.size(),b);t.used_f0=in.f0;t.used_linear=zeros(dy,b);t.used_linear=in.linear;t.used_constant=in.constant;
  for(const auto& s:in.sample_additions){require(s.sample_index<a.samples.size(),"sample factor index");const auto& view=a.samples[s.sample_index];
   require(s.coefficient.rows()==in.F.rows()&&s.coefficient.cols()==view.lifted_factor.rows(),"sample factor shape");finite(s.coefficient);
   t.used_F=plus(t.used_F,product(s.coefficient,view.lifted_factor,b),b);t.used_f0=plus(t.used_f0,product(s.coefficient,view.lifted_offset,b),b);}
  totalRows=add(totalRows,in.F.rows());o.terms.push_back(condense(a,std::move(t),b));
 }
 auto& s=o.sum;s.name="sum";s.units="declared_terms";s.used_F=zeros(totalRows,dy,b);s.used_f0=zeros(totalRows,b);s.used_linear=zeros(dy,b);s.used_constant=0;
 s.factor=zeros(totalRows,du,b);s.offset=zeros(totalRows,b);s.H=zeros(du,du,b);s.g=zeros(du,b);s.constant=0;std::size_t row=0;
 for(const auto& t:o.terms){const auto r=t.used_F.rows();s.used_F.middleRows(row,r)=t.used_F;s.used_f0.segment(row,r)=t.used_f0;s.factor.middleRows(row,r)=t.factor;s.offset.segment(row,r)=t.offset;
  s.used_linear=plus(s.used_linear,t.used_linear,b);s.used_constant=scalarAdd(s.used_constant,t.used_constant);
  s.H=plus(s.H,t.H,b);s.g=plus(s.g,t.g,b);s.constant=scalarAdd(s.constant,t.constant);row+=r;}
 return o;
}
Evaluation evaluate(const Assembly& a,const CondensedTerm& t,const Vector& U,const Limits& l,ProblemBudget& b){
 fixed(l);require(U.size()==a.T.cols(),"evaluation controls shape");finite(U);Evaluation e;
 auto y=plus(product(a.T,U,b),a.t,b);auto residual=plus(product(t.used_F,y,b),t.used_f0,b);
 e.lifted_value=scalarAdd(scalarAdd(.5*dot(residual,residual),dot(t.used_linear,y)),t.used_constant);
 e.condensed_value=scalarAdd(scalarAdd(.5*dot(U,product(t.H,U,b)),dot(t.g,U)),t.constant);
 auto tt=transposed(a.T,b),ft=transposed(t.used_F,b);
 e.lifted_chain_gradient=product(tt,plus(product(ft,residual,b),t.used_linear,b),b);
 auto ht=transposed(t.H,b);auto hs=zeros(t.H.rows(),t.H.cols(),b);
 // Half first avoids artificial overflow in H+H^T. Stored t.H is untouched.
 for(Eigen::Index i=0;i<hs.rows();++i){for(Eigen::Index j=0;j<hs.cols();++j){hs(i,j)=scalarAdd(.5*t.H(i,j),.5*ht(i,j));}}
 finite(hs);
 e.condensed_gradient=plus(product(hs,U,b),t.g,b);e.condensed_hessian=std::move(hs);
 e.lifted_chain_hessian=product(product(product(tt,ft,b),t.used_F,b),a.T,b);return e;
}
} // namespace phase5_public_affine_horizon
