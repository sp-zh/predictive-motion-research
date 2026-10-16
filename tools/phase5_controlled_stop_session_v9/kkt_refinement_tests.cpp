#include "current_numeric_guess.hpp"
#include <iostream>
#include <limits>
using namespace phase5_dynamic_numeric_v1;
void check(bool b,const char* m){if(!b)throw std::runtime_error(m);}
template<class F>void refusal(F f){bool bad=false;try{f();}catch(const std::invalid_argument&){bad=true;}check(bad,"original gate must refuse before refinement");}
int main(){try{
 phase5_working_face_basis_v1::Trace trace;trace.refinements.reserve(1536);
 Eigen::MatrixXd K(2,2);K<<2,1,1,0;Eigen::VectorXd rhs(2);rhs<<-1,0;
 auto active=solveKkt(K,rhs,1);check(trace.refinements.empty(),"active solve has no refinement side effect");auto refined=solveKkt(K,rhs,1,&trace,0);check((active.value.array()==refined.value.array()).all()&&refined.residual<=1e-10,"exact original solve unchanged");check(trace.refinements.size()==1&&trace.refinements[0].reason==1&&!trace.refinements[0].accepted&&trace.refinements[0].before_available&&!trace.refinements[0].correction_available,"zero residual explicitly no correction");trace.refinements.clear();
 K<<1,1,1,1;rhs<<1,2;refusal([&]{solveKkt(K,rhs,1,&trace,0);});check(trace.refinements.empty(),"initial original LU residual refusal cannot be rescued");
 K<<-1,0,0,0;rhs<<1,0;refusal([&]{solveKkt(K,rhs,1,&trace,0);});check(trace.refinements.empty(),"original positive Hessian refusal precedes refinement");
 K<<2,0,0,0;rhs<<1,0;auto singular=solveKkt(K,rhs,1,&trace,0);check(singular.rank==1&&singular.dimension==2&&singular.value(0)==.5&&singular.residual==0,"consistent singular original rank/LLT preserved");trace.refinements.clear();
 rhs(0)=std::numeric_limits<double>::quiet_NaN();refusal([&]{solveKkt(K,rhs,1,&trace,0);});check(trace.refinements.empty(),"nonfinite original input refused before refinement");
 std::cout<<"PASS original initial LU/LLT/nonfinite refusals precede refinement; active no refinement, exactzero no correction, original singular rank/Hessian gates retained; longdouble_digits="<<std::numeric_limits<long double>::digits<<"; no Model/native/task\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
