#include "linear_box_screen.hpp"
#include <iostream>
#include <stdexcept>
namespace c=phase5_active_session_qp_v1;
void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
int main(){try{
 c::Problem p;auto& q=p.original_si;q.hessian=Eigen::MatrixXd::Identity(c::NZ,c::NZ);q.gradient=Eigen::VectorXd::Zero(c::NZ);q.constraints=Eigen::MatrixXd::Zero(c::NZ+4,c::NZ);q.lower.resize(c::NZ+4);q.upper.resize(c::NZ+4);
 for(int j=0;j<c::NZ;++j){q.constraints(j,j)=1;double cap=j%8==7?.5:1;q.lower(j)=-cap;q.upper(j)=cap;p.rows.push_back({"input/"+std::to_string(j/8)+"/"+std::to_string(j%8),"SI"});}
 q.constraints(c::NZ,0)=.3;q.constraints(c::NZ,7)=-.25;q.lower(c::NZ)=-.6;q.upper(c::NZ)=.6;p.rows.push_back({"provably_inactive","SI"});
 q.constraints(c::NZ+1,0)=2;q.lower(c::NZ+1)=-1;q.upper(c::NZ+1)=1;p.rows.push_back({"active_inequality","SI"});
 q.constraints(c::NZ+2,0)=.05;q.lower(c::NZ+2)=0;q.upper(c::NZ+2)=0;p.rows.push_back({"must_retain_equality","SI"});
 q.constraints(c::NZ+3,0)=1;q.lower(c::NZ+3)=-1;q.upper(c::NZ+3)=1;p.rows.push_back({"outward_boundary_kept","SI"});
 const auto s=c::screenLinearInputBoxes(p);need(s.omitted_rows.size()==1&&s.omitted_rows[0].original_row==c::NZ,"screen selection differs from independent box corner oracle");
 // Enumerate all relevant two-dimensional corners independently; other
 // coordinates have zero coefficients in every non-input test row.
 for(double a:{-1.,1.})for(double b:{-.5,.5}){const double value=.3*a-.25*b;need(value>=-.6&&value<=.6,"omitted row invalid at input-box corner");}
 need(s.retained_rows.size()==c::NZ+3&&s.solver_problem.constraints.rows()==c::NZ+3,"retained matrix shape");
 for(int j=0;j<c::NZ;++j)need(s.retained_rows[j]==j,"input box dropped using itself as proof");
 need(s.solver_problem.hessian==q.hessian&&s.solver_problem.gradient==q.gradient,"objective altered by screen");
 for(std::size_t i=0;i<s.retained_rows.size();++i){int old=s.retained_rows[i];need(s.solver_problem.constraints.row(i)==q.constraints.row(old)&&s.solver_problem.lower(i)==q.lower(old)&&s.solver_problem.upper(i)==q.upper(old)&&s.labels[i]==p.rows[old].label,"original row/label mapping altered");}
 auto bad=p;bad.rows[0].label="not_an_input_box";bool denied=false;try{c::screenLinearInputBoxes(bad);}catch(const std::invalid_argument&){denied=true;}need(denied,"unproved input box accepted");
 const int saved=std::fegetround();need(std::fesetround(FE_DOWNWARD)==0,"cannot set directed rounding regression");denied=false;try{c::screenLinearInputBoxes(p);}catch(const std::invalid_argument&){denied=true;}need(std::fesetround(saved)==0,"cannot restore rounding");need(denied,"unsupported floating rounding accepted");
 std::cout<<"PASS independent corner implication, retained exact boxes/equality/active boundary, unchanged objective/original row labels, missing-box refusal; Model/solver/plant=0\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
