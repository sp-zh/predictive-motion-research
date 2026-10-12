#pragma once
#include "geometry.hpp"
#include "fine_timing.hpp"
#include "cycle_support.hpp"
namespace phase5_geometry_provider_counted_v2 {
using namespace predictive_motion;using namespace predictive_motion::geometry;
struct Counts {std::uint64_t scene_attempts=0,scene_returns=0,primitive_attempts=0,true_attempts=0,true_returns=0,cover_attempts=0,cover_returns=0,fk_attempts=0,fk_returns=0,jac_attempts=0,jac_returns=0;};
class CountedScene final:public Scene {
 Counts& counts_;const phase5_dynamic_cycle_support_v1::Envelope scope_;static void before(std::uint64_t& count,std::uint64_t cap,const char* why){if(count>=cap)throw std::runtime_error(why);++count;}
 public:CountedScene(const std::string& filename,Counts& counts,const phase5_dynamic_cycle_support_v1::Envelope& scope):Scene(filename),counts_(counts),scope_(scope){}
 Pose pose(RobotKinematics& robot,const Eigen::VectorXd& q,const std::string& frame)const {phase5_fine_timing_v1::Span timing(phase5_fine_timing_v1::Part::FkJacobian);before(counts_.fk_attempts,scope_.provider_fk,"provider FK declared cumulative cap");auto value=robot.framePose(q,frame);if(!value.rotation().allFinite()||!value.translation().allFinite())throw std::runtime_error("finite actual FK pose");++counts_.fk_returns;return value;}
 Jacobian jacobian(RobotKinematics& robot,const Eigen::VectorXd& q,const std::string& frame)const {phase5_fine_timing_v1::Span timing(phase5_fine_timing_v1::Part::FkJacobian);before(counts_.jac_attempts,scope_.provider_jac,"provider analyticJacob declared cumulative cap");auto value=robot.frameJacobian(q,frame,Reference::LocalWorldAligned);if(!value.allFinite())throw std::runtime_error("finite actual analytic Jacobian");++counts_.jac_returns;return value;}
  Snapshot query(RobotKinematics& robot,const Eigen::VectorXd& q,bool gradients=true,
                 bool cover_queries=true,double keep_cover_below=std::numeric_limits<double>::infinity()) const {
    phase5_fine_timing_v1::Span query_timing(phase5_fine_timing_v1::Part::GeometryQuery);
    before(counts_.scene_attempts,scope_.provider_scene,"Scene eval declared cumulative cap");
    struct Placement { Pose frame; coal::Transform3s transform; Jacobian jacobian; };
    std::vector<Placement> poses;
    for(const auto& object:objects) {
      Pose pose=object.frame=="world" ? Pose::Identity() : this->pose(robot,q,object.frame);
      Jacobian j=object.frame=="world" || !gradients ? Jacobian::Zero(6,q.size()) : jacobian(robot,q,object.frame);
      poses.push_back({pose,coal::Transform3s(pose.rotation(),pose.act(object.center)),j});
    }
    Snapshot out;
    {phase5_fine_timing_v1::Span batch_timing(phase5_fine_timing_v1::Part::CoalBatch);
    for(size_t a=0;a<objects.size();++a)for(size_t b=a+1;b<objects.size();++b) {
      if(excluded(objects[a],objects[b]))continue;
      coal::DistanceRequest request;
      request.enable_signed_distance=true;request.gjk_tolerance=1e-10;request.epa_tolerance=1e-10;request.gjk_max_iterations=256;
      coal::DistanceResult result;
      before(counts_.primitive_attempts,scope_.provider_primitives,"provider primitive query declared cumulative cap");++counts_.true_attempts;
      coal::distance(objects[a].shape.get(),poses[a].transform,objects[b].shape.get(),poses[b].transform,request,result);++counts_.true_returns;
      if(!std::isfinite(result.min_distance) || !result.normal.allFinite() ||
         !result.nearest_points[0].allFinite() || !result.nearest_points[1].allFinite() ||
         std::abs(result.normal.norm()-1)>1e-6 ||
         (result.nearest_points[1]-result.nearest_points[0]-result.min_distance*result.normal).norm()>1e-6)
        throw std::runtime_error("Invalid Coal distance/witness/normal: "+objects[a].name+"/"+objects[b].name);
      Query r{objects[a].name,objects[b].name,"true",result.min_distance,
              result.nearest_points[0],result.nearest_points[1],result.normal,Eigen::RowVectorXd::Zero(q.size())};
      r.covered_tool_environment=objects[a].category=="tool" && (objects[b].category=="fixture" || objects[b].category=="floor");
      if(r.covered_tool_environment)out.minimum_tool_environment_true=std::min(out.minimum_tool_environment_true,r.distance);
      if(gradients){phase5_fine_timing_v1::Span gradient_timing(phase5_fine_timing_v1::Part::GradientSample,phase5_fine_timing_v1::sampleGradient());r.gradient=-r.normal.transpose()*(pointJacobian(poses[a].frame,poses[a].jacobian,r.witness_a)-pointJacobian(poses[b].frame,poses[b].jacobian,r.witness_b));}
      if(!r.gradient.allFinite())throw std::runtime_error("nonfinite geometry gradient");
      out.minimum_true=std::min(out.minimum_true,r.distance);out.queries.push_back(std::move(r));
    }
    }
    if(!cover_queries){++counts_.scene_returns;return out;}
    const Pose flange=pose(robot,q,tool_frame);
    const Jacobian fj=gradients ? jacobian(robot,q,tool_frame) : Jacobian::Zero(6,q.size());
    {phase5_fine_timing_v1::Span batch_timing(phase5_fine_timing_v1::Part::CoverBatch);
    int cover_index=0;for(const auto& sphere:cover) {
      const int current_index=cover_index++;
      const V center=flange.act(sphere.center);
      for(size_t b=0;b<objects.size();++b) {
        if(objects[b].category!="fixture" && objects[b].category!="floor")continue;
        before(counts_.primitive_attempts,scope_.provider_primitives,"provider primitive query declared cumulative cap");++counts_.cover_attempts;
        V closest,normal; double signed_center;
        if(objects[b].category=="floor") {
          signed_center=center.z()-objects[b].center.z();normal=V(0,0,-1);
          closest=center-V(0,0,signed_center);
        } else {
          const auto box=std::dynamic_pointer_cast<coal::Box>(objects[b].shape);
          V local=center-objects[b].center;
          V delta=local.cwiseAbs()-box->halfSide;
          if(delta.maxCoeff()<=0) {
            if(gradients)throw std::runtime_error("Sphere center inside fixture; safe gradient unavailable");
            Eigen::Index axis; signed_center=delta.maxCoeff(&axis);
            const double sign=local(axis)<0?-1.0:1.0;
            normal=V::Zero();normal(axis)=-sign;
            closest=center;closest(axis)-=signed_center*sign;
          }else {
            closest=objects[b].center+local.cwiseMax(-box->halfSide).cwiseMin(box->halfSide);
            signed_center=(closest-center).norm();normal=(closest-center)/signed_center;
          }
        }
        const double distance=signed_center-sphere.radius;
        if(!std::isfinite(distance))throw std::runtime_error("nonfinite cover query");
        out.minimum_cover=std::min(out.minimum_cover,distance);
        ++counts_.cover_returns;
        if(distance>=keep_cover_below)continue;
        Query r{sphere.primitive,objects[b].name,"cover",distance,
                center+sphere.radius*normal,closest,normal,Eigen::RowVectorXd::Zero(q.size())};
        r.cover_index=current_index;
        if(gradients){phase5_fine_timing_v1::Span gradient_timing(phase5_fine_timing_v1::Part::GradientSample,phase5_fine_timing_v1::sampleGradient());r.gradient=-normal.transpose()*pointJacobian(flange,fj,center);}
        if(!std::isfinite(distance) || !r.gradient.allFinite())throw std::runtime_error("nonfinite cover query");
        out.queries.push_back(std::move(r));
      }
    }
    }
    ++counts_.scene_returns;return out;
  }
};
}
