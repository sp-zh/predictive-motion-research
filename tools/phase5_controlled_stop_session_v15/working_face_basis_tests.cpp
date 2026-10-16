#include "working_face_basis.hpp"
#include <iostream>
#include <limits>
int main(){using namespace phase5_working_face_basis_v1;
 Eigen::MatrixXd A(4,3);A<<1,0,0,0,1,0,2,0,0,0,0,1;std::vector<Face> faces={{0,1},{1,-1},{2,1}};auto r=reduce(A,faces,10,3,1);if(!r.complete||r.rank!=2||!r.rank_measured||!r.span_measured||r.span_error>1e-12||r.kept_positions.size()!=2||r.old_encoded.size()!=3)return 1;
 auto full=faces;full[2]={3,1};auto independent=reduce(A,full,11,2,1);if(independent.complete||independent.rank!=3||!independent.rank_measured||independent.span_measured)return 2;
 auto duplicate=faces;duplicate[2]={0,-1};if(reduce(A,duplicate,0,3,1).complete)return 3;
 auto bad=faces;bad[1].side=0;if(reduce(A,bad,0,3,1).complete)return 4;bad=faces;bad[0].row=-1;if(reduce(A,bad,0,3,1).complete)return 5;
 auto nan=A;nan(0,0)=std::numeric_limits<double>::quiet_NaN();if(reduce(nan,faces,0,3,1).complete)return 6;
 if(reduce(A,faces,0,0,1).complete||reduce(A,faces,0,3,0).complete||reduce(A,{{0,1}},0,3,1).complete)return 7;
 Eigen::MatrixXd near=A;near(2,2)=1e-17;auto tiny=reduce(near,faces,0,3,1);if(!tiny.complete||tiny.span_error>1e-12)return 8;
 // A real extra direction must not be discarded by rank selection.
 near(2,2)=1e-8;auto real=reduce(near,faces,0,3,1);if(real.complete||real.rank!=3)return 9;
 const double lo=-.024101261134803324;const double rounded=std::nextafter(lo,-std::numeric_limits<double>::infinity());if(!endpointWithinExistingNumericDomain(rounded,lo,.2)||endpointWithinExistingNumericDomain(lo-2e-12,lo,.2))return 10;
 for(double x:{std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){bool refused=false;try{endpointWithinExistingNumericDomain(x,lo,.2);}catch(const std::invalid_argument&){refused=true;}if(!refused)return 11;}
 bool refused=false;try{endpointWithinExistingNumericDomain(0,1,-1);}catch(const std::invalid_argument&){refused=true;}if(!refused)return 12;
 std::cout<<"PASS numerical fullface redundancy/basis reconstruction/fullrank cap refusal/near-dependent vsreal direction/malformed/nonfinite/newblocker/unchanged1e-12 endpoint domain true-boundary refusal; no Model/native/task\n";return 0;}
