#include "progress_interior_guard.hpp"
#include <iostream>
#include <limits>
struct Fixture {Eigen::MatrixXd A=Eigen::MatrixXd::Zero(14756,160),Z=Eigen::MatrixXd::Zero(160,144);Eigen::VectorXd lo=Eigen::VectorXd::Constant(14756,-.02),hi=Eigen::VectorXd::Constant(14756,.18),p=Eigen::VectorXd::Zero(160),scale=Eigen::VectorXd::Ones(144);std::vector<std::string> labels=std::vector<std::string>(14756,"unused");Fixture(){Z.topRows(144).setIdentity();for(int i=0;i<400;++i){labels[100+i]="progress/r/half/"+std::to_string(i);A(100+i,7)=.5;}p(7)=.01;}
 auto run(int rows=7101)const{return phase5_progress_interior_guard_v1::prepare(A,lo,hi,labels,Z,p,scale,rows);}
};
template<class F>bool refuses(F f){try{f();return false;}catch(const std::invalid_argument&){return true;}}
int main(){Fixture valid;auto rows=valid.run();if(rows.A.rows()!=264||rows.A.cols()!=144||rows.lower.size()!=264)return 1;for(int i=0;i<264;++i)if(rows.original_row[i]!=100+i||rows.scale(i)!=1||rows.A(i,7)!=.5||rows.lower(i)!=(-.02+1e-9-.005)||rows.upper(i)!=(.18-.005))return 2;
 if(!refuses([&]{valid.run(19737);})||!refuses([&]{valid.run(-1);}))return 3;
 {Fixture f;f.Z.resize(159,144);if(!refuses([&]{f.run();}))return 4;}
 {Fixture f;f.A.resize(14755,160);if(!refuses([&]{f.run();}))return 5;}
 for(double value:{0.,-1.,std::numeric_limits<double>::infinity()}){Fixture f;f.scale(0)=value;if(!refuses([&]{f.run();}))return 6;}
 {Fixture f;f.labels[101]="progress/r/half/0";if(!refuses([&]{f.run();}))return 7;}
 {Fixture f;f.labels[101]="unlisted";if(!refuses([&]{f.run();}))return 8;}
 for(const char* suffix:{"-1","01","400","9999","1x",""}){Fixture f;f.labels[100]=std::string("progress/r/half/")+suffix;if(!refuses([&]{f.run();}))return 9;}
 {Fixture f;f.Z(0,0)=std::numeric_limits<double>::quiet_NaN();if(!refuses([&]{f.run();}))return 10;}
 {Fixture f;f.A(100,0)=std::numeric_limits<double>::infinity();if(!refuses([&]{f.run();}))return 11;}
 {Fixture f;f.A(100,0)=1e308;f.Z(0,0)=1e308;if(!refuses([&]{f.run();}))return 12;}
 {Fixture f;f.A(100,0)=1e308;f.p(0)=1e308;if(!refuses([&]{f.run();}))return 13;}
 {Fixture f;f.A(100,0)=1e308;f.p(0)=-1;f.lo(100)=f.hi(100)=1e308;if(!refuses([&]{f.run();}))return 14;}
 {Fixture f;f.lo(100)=.2;if(!refuses([&]{f.run();}))return 15;}
 {Fixture f;f.A(100,7)=100;auto scaled=f.run();if(scaled.scale(0)!=.01||scaled.A(0,7)!=1)return 16;}
 std::cout<<"PASS fixed264 original400 roster, finite shapes, augmentedmcap, duplicate/missing/negative/leadingzero/range labels, nonfinite/overflow/positive downscale; noModel_OSQP_Task\n";return 0;}
