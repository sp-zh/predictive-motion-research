#include "geometry.hpp"
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
using namespace predictive_motion;
using namespace predictive_motion::geometry;
int main(int argc,char**argv) {
  if(argc!=5)return 2;
  try {
    Scene scene(argv[1]); RobotKinematics robot(loadConfig(argv[2]));
    std::ifstream path(argv[3]);std::string line;std::getline(path,line);
    std::ofstream out(argv[4]);out<<std::setprecision(17);
    out<<"pose,min_true_m,min_tool_environment_true_m,min_cover_m,queries,point_directions_checked,cover_components_checked,point_jacobian_max_error,cover_fd_max_error,true_smooth_components,true_nonsmooth_components,true_interval_failures,true_smooth_error_m_rad\n";
    int row=0; double max_point=0,max_cover=0;
    while(std::getline(path,line)) {
      std::stringstream in(line);std::string cell;std::vector<double> values;
      while(std::getline(in,cell,','))values.push_back(std::stod(cell));
      Eigen::VectorXd q(7);for(int i=0;i<7;++i)q(i)=values.at(values.size()-7+i);
      auto snapshot=scene.query(robot,q);
      if(snapshot.minimum_cover>snapshot.minimum_tool_environment_true+1e-7)throw std::runtime_error("Cover not conservative on common tool/environment set");
      // Independent point position FD at a nontrivial tool lever arm.
      const V local(.0375,.004,.047);
      const Pose p=robot.framePose(q,"fr3_link8");
      auto j=pointJacobian(p,robot.frameJacobian(q,"fr3_link8",Reference::LocalWorldAligned),p.act(local));
      double point_error=0,cover_error=0;
      int point_checks=0,cover_checks=0,true_smooth=0,true_nonsmooth=0,interval_failures=0;
      double true_error=0;
      if(row%10==0)for(int k=0;k<7;++k) {
        Eigen::VectorXd plus=q,minus=q;plus(k)+=1e-6;minus(k)-=1e-6;
        V fd=(robot.framePose(plus,"fr3_link8").act(local)-robot.framePose(minus,"fr3_link8").act(local))/(2e-6);
        point_error=std::max(point_error,(fd-j.col(k)).norm());
        ++point_checks;
        const auto qp=scene.query(robot,plus,false),qm=scene.query(robot,minus,false);
        for(size_t n=0;n<snapshot.queries.size();++n)if(snapshot.queries[n].type=="true") {
          const double left=(snapshot.queries[n].distance-qm.queries[n].distance)/1e-6;
          const double right=(qp.queries[n].distance-snapshot.queries[n].distance)/1e-6;
          const double analytic=snapshot.queries[n].gradient(k);
          if(std::abs(left-right)>1e-4)++true_nonsmooth;
          else {++true_smooth;true_error=std::max(true_error,std::abs(.5*(left+right)-analytic));}
          if(analytic<std::min(left,right)-1e-4 || analytic>std::max(left,right)+1e-4)++interval_failures;
        }
        for(size_t n=0;n<snapshot.queries.size();n+=17)if(snapshot.queries[n].type=="cover") {
          double derivative=(qp.queries[n].distance-qm.queries[n].distance)/(2e-6);
          cover_error=std::max(cover_error,std::abs(derivative-snapshot.queries[n].gradient(k)));
          ++cover_checks;
        }
      }
      max_point=std::max(max_point,point_error);max_cover=std::max(max_cover,cover_error);
      out<<row<<','<<snapshot.minimum_true<<','<<snapshot.minimum_tool_environment_true<<','<<snapshot.minimum_cover<<','<<snapshot.queries.size()<<','<<point_checks<<','<<cover_checks<<',';
      if(point_checks)out<<point_error<<','<<cover_error;else out<<"nan,nan";
      out<<','<<true_smooth<<','<<true_nonsmooth<<','<<interval_failures<<',';
      if(point_checks)out<<true_error;else out<<"nan";
      out<<'\n';
      if(interval_failures || true_error>1e-4)throw std::runtime_error("True primitive/convex derivative audit failed");
      ++row;
    }
    std::cout<<"poses="<<row<<" spheres="<<scene.cover.size()<<" point_error="<<max_point<<" cover_error="<<max_cover<<'\n';
    if(row!=81 || max_point>1e-7 || max_cover>1e-5)return 1;
    return 0;
  }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}
}
