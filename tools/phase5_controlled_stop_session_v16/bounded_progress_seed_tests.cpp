#include "bounded_progress_seed.hpp"
#include <iostream>
#include <limits>
int main(){Eigen::MatrixXd A=Eigen::MatrixXd::Zero(2,144);A(0,7)=1;A(1,0)=1;Eigen::VectorXd lo(2),hi(2);lo<<1e-9,-1;hi<<.1,1;Eigen::VectorXd nominal=Eigen::VectorXd::Zero(144),scale=Eigen::VectorXd::Ones(144);auto r=phase5_bounded_progress_seed_v1::prepare(A,lo,hi,nominal,scale);if(!r.complete||!r.changed||r.epsilon<=0||r.epsilon>1e-6||r.attempts.empty()||r.attempts.back().worst_violation>1e-12)return 1;for(int j=0;j<144;++j)if(j%8!=7&&r.seed(j)!=nominal(j))return 2;
 auto same=phase5_bounded_progress_seed_v1::prepare(A,lo,hi,r.seed,scale);if(!same.complete||same.changed||same.epsilon!=0||(same.seed-r.seed).norm()!=0)return 3;
 auto flatlo=lo;flatlo(1)=.01;auto flat=phase5_bounded_progress_seed_v1::prepare(A,flatlo,hi,nominal,scale);if(flat.complete||flat.error.find("wholepolytope unknown")==std::string::npos)return 4;if(flat.row_bounds_written!=1||flat.row_direction_bounds.rows()!=2||!flat.row_direction_bounds.allFinite()||!flat.row_direction_bounds.row(1).isZero(0))return 13;
 auto distant=lo;distant(0)=.01;auto capped=phase5_bounded_progress_seed_v1::prepare(A,distant,hi,nominal,scale);if(capped.complete||capped.error.find("wholepolytope unknown")==std::string::npos)return 5;
 auto backwards=A;backwards(0,7)=-1;auto negative=phase5_bounded_progress_seed_v1::prepare(backwards,lo,hi,nominal,scale);if(negative.complete)return 6;
 auto inverted=lo;inverted(0)=1;auto order=phase5_bounded_progress_seed_v1::prepare(A,inverted,hi,nominal,scale);if(order.complete)return 7;
 for(double x:{0.,-1.,std::numeric_limits<double>::infinity()}){auto badscale=scale;badscale(7)=x;if(phase5_bounded_progress_seed_v1::prepare(A,lo,hi,nominal,badscale).complete)return 8;}
 auto nan=nominal;nan(0)=std::numeric_limits<double>::quiet_NaN();if(phase5_bounded_progress_seed_v1::prepare(A,lo,hi,nan,scale).complete)return 9;
 auto tiny=scale;tiny(7)=std::numeric_limits<double>::denorm_min();if(phase5_bounded_progress_seed_v1::prepare(A,lo,hi,nominal,tiny).complete)return 10;
 Eigen::MatrixXd wrong=Eigen::MatrixXd::Zero(2,143);if(phase5_bounded_progress_seed_v1::prepare(wrong,lo,hi,nominal,scale).complete)return 11;
 Eigen::MatrixXd excess=Eigen::MatrixXd::Zero(20001,144);auto el=Eigen::VectorXd::Zero(20001),eh=Eigen::VectorXd::Ones(20001);if(phase5_bounded_progress_seed_v1::prepare(excess,el,eh,nominal,scale).complete)return 12;
 std::cout<<"PASS bounded optimizer seed direction/all-row recheck/unchanged feasible seed/flat-infeasible/empty capped ray/negative direction/inverted/shape/nonfinite/overflow; no actualstate/candidate/Model/nativeOSQP/task modifications\n";return 0;}
