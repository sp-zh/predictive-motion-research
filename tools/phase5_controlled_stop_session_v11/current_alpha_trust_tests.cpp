#include "current_alpha_trust.hpp"
#include <iostream>
namespace trust=phase5_current_alpha_trust_v1;namespace core=phase5_active_session_qp_v1;
void check(bool b){if(!b)throw std::runtime_error("derived current trust invariant");}
template<class F>void refuse(F f){bool b=false;try{f();}catch(const std::invalid_argument&){b=true;}check(b);}
int main(){try{core::Problem p;p.seed=Eigen::VectorXd::Zero(160);p.seed(0)=.02;p.original_si.constraints=Eigen::MatrixXd::Zero(2800,160);p.original_si.lower=Eigen::VectorXd::Zero(2800);p.original_si.upper=Eigen::VectorXd::Zero(2800);
 for(int r=0;r<2800;++r){p.rows.push_back({"trust/q/half/"+std::to_string(r),"rad"});p.original_si.constraints(r,0)=r==2799?1.25:.125;p.original_si.constraints(r,9)=-.25;double center=p.original_si.constraints.row(r).dot(p.seed);p.original_si.lower(r)=center-.002;p.original_si.upper(r)=center+.002;}
 auto plan=trust::derive(p,1);check(plan.rows.size()==2800&&plan.center==p.seed&&plan.limiting_original_row==2799&&plan.strict_radius>.00016&&plan.strict_radius<.00017&&plan.solver_radius<plan.strict_radius);
 for(const auto& row:plan.rows){const long double effect=static_cast<long double>(row.coefficient_L1_upper)*plan.strict_radius;check(effect<=.125L*row.margin_lower);check(static_cast<long double>(row.seed_lower)-effect>=p.original_si.lower(row.original_row)&&static_cast<long double>(row.seed_upper)+effect<=p.original_si.upper(row.original_row));}
 check(plan.center(0)>.001); // Centered domain is not old absolute small-alpha box.
 for(double fraction:{.0078125,.00048828125}){auto small=trust::derive(p,1,fraction);check(small.strict_radius<plan.strict_radius&&small.strict_radius<=plan.strict_radius*(fraction/.125)*1.000000000000001);for(const auto& r:small.rows)check(r.coefficient_L1_upper*small.strict_radius<=fraction*r.margin_lower);}for(double fraction:{0.,-.01,.126,std::numeric_limits<double>::quiet_NaN()})refuse([&]{trust::derive(p,1,fraction);});
 auto malformed=p;malformed.original_si.lower.resize(1);refuse([&]{trust::derive(malformed,1);});malformed=p;malformed.original_si.upper.resize(1);refuse([&]{trust::derive(malformed,1);});
 auto limited=trust::derive(p,.0001);check(limited.strict_radius==.0001);p.original_si.constraints(0,7)=1e-20;refuse([&]{trust::derive(p,1);});p.original_si.constraints(0,7)=0;p.original_si.lower(0)=1;refuse([&]{trust::derive(p,1);});p.original_si.lower(0)=-.002;p.rows[0].label="wrong";refuse([&]{trust::derive(p,1);});p.rows[0].label="trust/q/half/0";int original=std::fegetround();check(std::fesetround(FE_UPWARD)==0);refuse([&]{trust::derive(p,1);});check(std::fesetround(original)==0);
 std::cout<<"PASS2800 outward interval/L1/eighthmargin/global box/nominal center/originalcap/missingrow/bcolumn/seedoutside/fenv refusal; synthetic pure planning only no Model/native task\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
