#pragma once
#include <predictive_motion_kinematics/robot_kinematics.hpp>
#include <coal/distance.h>
#include <coal/shape/convex.h>
#include <coal/shape/geometric_shapes.h>
#include <yaml-cpp/yaml.h>
#include <Eigen/Geometry>
#include <array>
#include <cmath>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace predictive_motion::geometry {
using V = Eigen::Vector3d;
using Shape = std::shared_ptr<coal::CollisionGeometry>;
struct Object {
  std::string name, frame, category;
  V center;
  Shape shape;
  int arm_index = -1;
};
struct CoverSphere { std::string primitive; V center; double radius; };
struct Query {
  std::string a, b, type;
  double distance;
  V witness_a, witness_b, normal;
  Eigen::RowVectorXd gradient;
  bool covered_tool_environment=false;
};
struct Snapshot {
  std::vector<Query> queries;
  double minimum_true = std::numeric_limits<double>::infinity();
  double minimum_cover = std::numeric_limits<double>::infinity();
  double minimum_tool_environment_true = std::numeric_limits<double>::infinity();
};
inline V vec(const YAML::Node& n) {
  if (!n.IsSequence() || n.size() != 3) throw std::invalid_argument("3-vector");
  V v(n[0].as<double>(), n[1].as<double>(), n[2].as<double>());
  if (!v.allFinite()) throw std::invalid_argument("nonfinite geometry");
  return v;
}
inline Eigen::MatrixXd pointJacobian(const Pose& pose, const Jacobian& j, const V& p) {
  Eigen::MatrixXd out = j.topRows(3);
  const V lever = p - pose.translation();
  for (int k = 0; k < j.cols(); ++k) out.col(k) += V(j.bottomRows(3).col(k)).cross(lever);
  return out;
}
class Scene {
 public:
  std::vector<Object> objects;
  std::vector<CoverSphere> cover;
  std::string tool_frame;
  int arm_count=0;
  double motion_radius_bound=2.0;
  double cell = 0;
  explicit Scene(const std::string& filename) {
    auto config = YAML::LoadFile(filename);
    tool_frame=config["tool_frame"].as<std::string>();
    motion_radius_bound=config["motion_radius_bound_m"].as<double>();
    cell = config["cover_cell_m"].as<double>();
    if (!std::isfinite(cell) || cell <= 0) throw std::invalid_argument("cover cell");
    int index = 0;
    for (auto arm : config["arm"]) {
      std::ifstream in(arm["file"].as<std::string>());
      int nv, nf; in >> nv >> nf;
      if (!in || nv < 4 || nf < 4) throw std::runtime_error("convex asset");
      auto vertices = std::make_shared<std::vector<coal::Vec3s>>();
      auto faces = std::make_shared<std::vector<coal::Triangle>>();
      for (int i = 0; i < nv; ++i) { V v; in >> v.x() >> v.y() >> v.z(); vertices->push_back(v); }
      for (int i = 0; i < nf; ++i) {
        int a,b,c; in >> a >> b >> c;
        if (a<0 || a>=nv || b<0 || b>=nv || c<0 || c>=nv) throw std::runtime_error("convex index");
        faces->emplace_back(a,b,c);
      }
      if (!in) throw std::runtime_error("truncated convex asset");
      auto shape=std::make_shared<coal::Convex<coal::Triangle>>(vertices,nv,faces,nf);
      shape->computeLocalAABB();
      objects.push_back({arm["frame"].as<std::string>(),arm["frame"].as<std::string>(),
                         "arm",V::Zero(),shape,index++});
    }
    arm_count=index;
    for (auto p : config["primitives"]) {
      const std::string type=p["type"].as<std::string>(), body=p["body"].as<std::string>();
      const std::string name=p["name"].as<std::string>();
      const V center=vec(p["local_position_m"]);
      const auto s=p["size_m"].as<std::vector<double>>();
      Shape shape; V half;
      if(type=="box") { half=V(s.at(0),s.at(1),s.at(2)); shape=std::make_shared<coal::Box>(2*half); }
      else if(type=="cylinder") { half=V(s.at(0),s.at(0),s.at(1)); shape=std::make_shared<coal::Cylinder>(s[0],2*s[1]); }
      else if(type=="sphere") { half=V::Constant(s.at(0)); shape=std::make_shared<coal::Sphere>(s[0]); }
      else throw std::invalid_argument("primitive type");
      const bool tool=body=="inspection_tool";
      objects.push_back({name,tool ? config["tool_frame"].as<std::string>() : "world",
                         tool ? "tool" : "fixture",center,shape,-1});
      if (!tool) continue;
      if(type=="sphere") { cover.push_back({name,center,s[0]}); continue; }
      if(type=="cylinder") {
        const int slices=std::max(1,static_cast<int>(std::ceil(2*s[1]/cell)));
        const double width=2*s[1]/slices,radius=std::hypot(s[0],width/2);
        for(int slice=0;slice<slices;++slice)
          cover.push_back({name,center+V(0,0,-s[1]+(slice+.5)*width),radius});
        continue;
      }
      // Every intersecting axis-aligned cell is enclosed by its circumsphere.
      // Box union is exact before circumspheres; cylinder intersects cells by
      // radial closest point test (z partition already bounded by half-height).
      Eigen::Vector3i count;
      for(int k=0;k<3;++k) count(k)=std::max(1,static_cast<int>(std::ceil(2*half(k)/cell)));
      V width=(2*half).cwiseQuotient(count.cast<double>());
      const double radius=.5*width.norm();
      for(int x=0;x<count.x();++x)for(int y=0;y<count.y();++y)for(int z=0;z<count.z();++z) {
        V local=-half+(V(x+.5,y+.5,z+.5).cwiseProduct(width));
        if(type=="cylinder") {
          V closest=(local.cwiseAbs()-.5*width).cwiseMax(0.0);
          if(closest.head<2>().squaredNorm()>s[0]*s[0]+1e-16)continue;
        }
        cover.push_back({name,center+local,radius});
      }
    }
    objects.push_back({"floor","world","floor",V(0,0,config["floor_z"].as<double>()),
                       std::make_shared<coal::Halfspace>(V::UnitZ(),0),-1});
  }
  bool excluded(const Object& a,const Object& b) const {
    if(a.category==b.category && (a.category=="tool" || a.category=="fixture"))return true;
    if(a.category=="arm" && b.category=="arm" && std::abs(a.arm_index-b.arm_index)<=1)return true;
    if((a.arm_index==0 && b.category=="floor") || (b.arm_index==0 && a.category=="floor"))return true;
    if((a.arm_index==arm_count-1 && b.category=="tool") || (b.arm_index==arm_count-1 && a.category=="tool"))return true;
    return (a.frame=="world" && b.frame=="world");
  }
  Snapshot query(RobotKinematics& robot,const Eigen::VectorXd& q,bool gradients=true,
                 bool cover_queries=true,double keep_cover_below=std::numeric_limits<double>::infinity()) const {
    struct Placement { Pose frame; coal::Transform3s transform; Jacobian jacobian; };
    std::vector<Placement> poses;
    for(const auto& object:objects) {
      Pose pose=object.frame=="world" ? Pose::Identity() : robot.framePose(q,object.frame);
      Jacobian j=object.frame=="world" || !gradients ? Jacobian::Zero(6,q.size()) : robot.frameJacobian(q,object.frame,Reference::LocalWorldAligned);
      poses.push_back({pose,coal::Transform3s(pose.rotation(),pose.act(object.center)),j});
    }
    Snapshot out;
    for(size_t a=0;a<objects.size();++a)for(size_t b=a+1;b<objects.size();++b) {
      if(excluded(objects[a],objects[b]))continue;
      coal::DistanceRequest request;
      request.enable_signed_distance=true;request.gjk_tolerance=1e-10;request.epa_tolerance=1e-10;request.gjk_max_iterations=256;
      coal::DistanceResult result;
      coal::distance(objects[a].shape.get(),poses[a].transform,objects[b].shape.get(),poses[b].transform,request,result);
      if(!std::isfinite(result.min_distance) || !result.normal.allFinite() ||
         !result.nearest_points[0].allFinite() || !result.nearest_points[1].allFinite() ||
         std::abs(result.normal.norm()-1)>1e-6 ||
         (result.nearest_points[1]-result.nearest_points[0]-result.min_distance*result.normal).norm()>1e-6)
        throw std::runtime_error("Invalid Coal distance/witness/normal: "+objects[a].name+"/"+objects[b].name);
      Query r{objects[a].name,objects[b].name,"true",result.min_distance,
              result.nearest_points[0],result.nearest_points[1],result.normal,Eigen::RowVectorXd::Zero(q.size())};
      r.covered_tool_environment=objects[a].category=="tool" && (objects[b].category=="fixture" || objects[b].category=="floor");
      if(r.covered_tool_environment)out.minimum_tool_environment_true=std::min(out.minimum_tool_environment_true,r.distance);
      if(gradients)r.gradient=-r.normal.transpose()*(pointJacobian(poses[a].frame,poses[a].jacobian,r.witness_a)-pointJacobian(poses[b].frame,poses[b].jacobian,r.witness_b));
      if(!r.gradient.allFinite())throw std::runtime_error("nonfinite geometry gradient");
      out.minimum_true=std::min(out.minimum_true,r.distance);out.queries.push_back(std::move(r));
    }
    if(!cover_queries)return out;
    const Pose flange=robot.framePose(q,tool_frame);
    const Jacobian fj=gradients ? robot.frameJacobian(q,tool_frame,Reference::LocalWorldAligned) : Jacobian::Zero(6,q.size());
    for(const auto& sphere:cover) {
      const V center=flange.act(sphere.center);
      for(size_t b=0;b<objects.size();++b) {
        if(objects[b].category!="fixture" && objects[b].category!="floor")continue;
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
        if(distance>=keep_cover_below)continue;
        Query r{sphere.primitive,objects[b].name,"cover",distance,
                center+sphere.radius*normal,closest,normal,Eigen::RowVectorXd::Zero(q.size())};
        if(gradients)r.gradient=-normal.transpose()*pointJacobian(flange,fj,center);
        if(!std::isfinite(distance) || !r.gradient.allFinite())throw std::runtime_error("nonfinite cover query");
        out.queries.push_back(std::move(r));
      }
    }
    return out;
  }
};
}  // namespace predictive_motion::geometry
