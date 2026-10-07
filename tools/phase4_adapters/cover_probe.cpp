#include "geometry.hpp"
#include <iomanip>
#include <iostream>
#include <random>
using namespace predictive_motion::geometry;
int main(int argc,char**argv) {
  if(argc!=3)return 2;
  try {
    Scene scene(argv[1]);auto cfg=YAML::LoadFile(argv[1]);
    std::mt19937 random(71007);auto unit=[&]{return double(random())/4294967295.;};
    std::ofstream out(argv[2]);out<<std::setprecision(17);
    out<<"primitive,spheres,samples,max_sample_uncovered_m,max_radius_m,analytic_max_inflation_m\n";
    double max_uncovered=-1e9;
    for(auto p:cfg["primitives"]) {
      if(p["body"].as<std::string>()!="inspection_tool")continue;
      const std::string name=p["name"].as<std::string>(),type=p["type"].as<std::string>();
      auto s=p["size_m"].as<std::vector<double>>();const V center=vec(p["local_position_m"]);
      std::vector<const CoverSphere*> spheres;double max_radius=0;
      for(const auto& sphere:scene.cover)if(sphere.primitive==name){spheres.push_back(&sphere);max_radius=std::max(max_radius,sphere.radius);}
      if(spheres.empty())throw std::runtime_error("Missing primitive cover");
      double uncovered=-1e9;int samples=0;
      auto check=[&](const V& point){double gap=1e9;for(auto sphere:spheres)gap=std::min(gap,(point-sphere->center).norm()-sphere->radius);uncovered=std::max(uncovered,gap);++samples;};
      for(int sample=0;sample<10000;++sample) {
        V local;
        if(type=="box") {
          local=V(2*unit()-1,2*unit()-1,2*unit()-1).cwiseProduct(V(s[0],s[1],s[2]));
          if(sample%2==0){int axis=sample%3;local(axis)=(sample%4==0?1:-1)*s[axis];}
        } else if(type=="cylinder") {
          const double angle=2*M_PI*unit(),radius=sample%3==0?s[0]:s[0]*std::sqrt(unit());
          double z=(2*unit()-1)*s[1];if(sample%3==1)z=(sample%2==0?1:-1)*s[1];
          local=V(radius*std::cos(angle),radius*std::sin(angle),z);
        } else {
          const double z=2*unit()-1,angle=2*M_PI*unit();local=s[0]*V(std::sqrt(1-z*z)*std::cos(angle),std::sqrt(1-z*z)*std::sin(angle),z);
        }
        check(center+local);
      }
      if(type=="box")for(int x:{-1,1})for(int y:{-1,1})for(int z:{-1,1})check(center+V(x*s[0],y*s[1],z*s[2]));
      max_uncovered=std::max(max_uncovered,uncovered);
      double inflation=type=="sphere"?0:max_radius;
      if(type=="cylinder")inflation=max_radius-std::min(s[0],s[1]/spheres.size());
      out<<name<<','<<spheres.size()<<','<<samples<<','<<uncovered<<','<<max_radius<<','<<inflation<<'\n';
    }
    std::cout<<"cover_spheres="<<scene.cover.size()<<" maximum_sample_gap="<<max_uncovered<<" motion_radius_bound="<<scene.motion_radius_bound<<'\n';
    return max_uncovered>1e-12?1:0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
