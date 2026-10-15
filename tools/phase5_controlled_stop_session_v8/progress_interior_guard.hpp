#pragma once
#include <Eigen/Core>
#include <array>
#include <vector>
#include <string>
#include <stdexcept>
#include <cmath>
#include <algorithm>
namespace phase5_progress_interior_guard_v1 {
inline constexpr int halves=264,original_rows=14756,controls=160,free_controls=144;
inline constexpr double floor_rate=1e-9;
struct Rows {Eigen::MatrixXd A;Eigen::VectorXd lower,upper,scale;std::array<int,halves> original_row{};};
inline Rows prepare(const Eigen::MatrixXd& originalA,const Eigen::VectorXd& originalLower,const Eigen::VectorXd& originalUpper,const std::vector<std::string>& labels,const Eigen::MatrixXd& Z,const Eigen::VectorXd& p,const Eigen::VectorXd& variableScale,int existing_solver_rows){
 auto need=[](bool ok,const char* message){if(!ok)throw std::invalid_argument(message);};
 need(existing_solver_rows>=0&&existing_solver_rows<=20000-halves,"guard augmented row cap before allocation");
 need(originalA.rows()==original_rows&&originalA.cols()==controls&&originalLower.size()==original_rows&&originalUpper.size()==original_rows&&labels.size()==original_rows&&Z.rows()==controls&&Z.cols()==free_controls&&p.size()==controls&&variableScale.size()==free_controls,"guard fixed original and reduced shapes before calculation");
 need(Z.allFinite()&&p.allFinite()&&variableScale.allFinite()&&(variableScale.array()>0).all(),"guard finite affine map and positive variable scale");
 std::array<int,400> roster;roster.fill(-1);const std::string prefix="progress/r/half/";
 for(int row=0;row<original_rows;++row){const auto& label=labels[row];if(label.compare(0,prefix.size(),prefix)!=0)continue;const auto suffix=label.substr(prefix.size());need(!suffix.empty()&&suffix.size()<=3&&(suffix.size()==1||suffix[0]!='0'),"guard canonical half index");int index=0;for(char c:suffix){need(c>='0'&&c<='9',"guard decimal half index");index=10*index+c-'0';}need(index>=0&&index<400&&roster[index]<0,"guard unique half index range");roster[index]=row;}
 for(int row:roster)need(row>=0,"guard complete unique original400 half-r roster");
 // Select every first264 original half-r row even if the original box screen
 // omitted it. Existing original constraints remain mandatory and unchanged.
 for(int sample=0;sample<halves;++sample){const int row=roster[sample];need(originalA.row(row).allFinite()&&std::isfinite(originalLower(row))&&std::isfinite(originalUpper(row))&&originalLower(row)<=originalUpper(row),"guard finite selected original rows and ordered bounds");}
 Rows out;out.A.resize(halves,free_controls);out.lower.resize(halves);out.upper.resize(halves);out.scale.resize(halves);
 for(int sample=0;sample<halves;++sample){const int row=roster[sample];const Eigen::RowVectorXd unscaled=originalA.row(row)*Z;const double shift=originalA.row(row).dot(p);need(unscaled.allFinite()&&std::isfinite(shift),"guard finite original affine transformation");const Eigen::RowVectorXd values=unscaled*variableScale.asDiagonal();need(values.allFinite(),"guard finite scaled row before norm");const double norm=values.cwiseAbs().maxCoeff();need(std::isfinite(norm),"guard finite scaled infinity norm");const double multiplier=1/std::max(1.,norm);need(std::isfinite(multiplier)&&multiplier>0&&multiplier<=1,"guard strictly positive downward row scale");const double lower=originalLower(row)+floor_rate-shift,upper=originalUpper(row)-shift;need(std::isfinite(lower)&&std::isfinite(upper)&&lower<=upper,"guard finite tightened planning bounds");const Eigen::RowVectorXd scaled=multiplier*values;const double scaledLower=multiplier*lower,scaledUpper=multiplier*upper;need(scaled.allFinite()&&std::isfinite(scaledLower)&&std::isfinite(scaledUpper)&&scaledLower<=scaledUpper,"guard finite encoded planning row");out.A.row(sample)=scaled;out.lower(sample)=scaledLower;out.upper(sample)=scaledUpper;out.scale(sample)=multiplier;out.original_row[sample]=row;}
 return out;
}
// This intersects the existing biased-p planning domain, not original E0.
// It is not a candidate/token/stop certificate. All original native/fullSI,
// rounded200/half400, genuine B400 and private actual C gates still apply.
}
