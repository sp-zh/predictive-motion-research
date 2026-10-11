from pathlib import Path
import hashlib,shutil,json
D=Path('/private/tmp/phase5_nominal_geometry_provider_active_v2_20261011');S=D/'src';S.mkdir(exist_ok=False)
original=Path('/Users/uot/Documents/ChatGPT/ros/tools/phase4_adapters/geometry.hpp').read_text();(S/'upstream_geometry.hpp').write_text(original);shutil.copy2('/private/tmp/phase5_nominal_geometry_rows_active_v1_20261011/nominal_geometry_selection.hpp',S/'nominal_geometry_selection.hpp')
a=original.index('  Snapshot query(');body=original[a:original.rindex('\n};')];body=body.replace('    struct Placement','    before(counts_.scene_attempts,1400,"Scene eval cumulative1400");\n    struct Placement').replace('robot.framePose(q,object.frame)','pose(robot,q,object.frame)').replace('robot.frameJacobian(q,object.frame,Reference::LocalWorldAligned)','jacobian(robot,q,object.frame)').replace('robot.framePose(q,tool_frame)','pose(robot,q,tool_frame)').replace('robot.frameJacobian(q,tool_frame,Reference::LocalWorldAligned)','jacobian(robot,q,tool_frame)')
body=body.replace('      coal::distance(','      before(counts_.primitive_attempts,20000000,"provider primitive query cumulative20M");++counts_.true_attempts;\n      coal::distance(').replace('request,result);','request,result);++counts_.true_returns;')
body=body.replace('if(!cover_queries)return out;','if(!cover_queries){++counts_.scene_returns;return out;}').replace('        V closest,normal; double signed_center;','        before(counts_.primitive_attempts,20000000,"provider primitive query cumulative20M");++counts_.cover_attempts;\n        V closest,normal; double signed_center;').replace('if(distance>=keep_cover_below)continue;','++counts_.cover_returns;\n        if(distance>=keep_cover_below)continue;').replace('    return out;','    ++counts_.scene_returns;return out;')
header='''#pragma once
#include "geometry.hpp"
namespace phase5_geometry_provider_counted_v2 {
using namespace predictive_motion;using namespace predictive_motion::geometry;
struct Counts {std::uint64_t scene_attempts=0,scene_returns=0,primitive_attempts=0,true_attempts=0,true_returns=0,cover_attempts=0,cover_returns=0,fk_attempts=0,fk_returns=0,jac_attempts=0,jac_returns=0;};
class CountedScene final:public Scene {
 Counts& counts_;static void before(std::uint64_t& count,std::uint64_t cap,const char* why){if(count>=cap)throw std::runtime_error(why);++count;}
 public:CountedScene(const std::string& filename,Counts& counts):Scene(filename),counts_(counts){}
 Pose pose(RobotKinematics& robot,const Eigen::VectorXd& q,const std::string& frame)const {before(counts_.fk_attempts,40000,"provider FK cumulative40000");auto value=robot.framePose(q,frame);++counts_.fk_returns;return value;}
 Jacobian jacobian(RobotKinematics& robot,const Eigen::VectorXd& q,const std::string& frame)const {before(counts_.jac_attempts,20000,"provider analyticJacob cumulative20000");auto value=robot.frameJacobian(q,frame,Reference::LocalWorldAligned);++counts_.jac_returns;return value;}
'''+body+'''\n};
}
''';(S/'counted_geometry.hpp').write_text(header)
(D/'COUNTED_QUERY_SOURCE_BINDING.json').write_text(json.dumps({'upstream_path':'tools/phase4_adapters/geometry.hpp','upstream_sha256':hashlib.sha256(original.encode()).hexdigest(),'upstream_query_source_sha256':hashlib.sha256(original[a:original.rindex('\n};')].encode()).hexdigest(),'counted_query_source_sha256':hashlib.sha256(header.encode()).hexdigest(),'only_changes':'count-before-calls wrappers for FK/Jacobian/Coal/cover/Scene eval and returns; exact original math/options/error thresholds preserved','scope':'finite recorded-nominal geometry diagnostic only; no MuJoCo/ModelF1/controller'},indent=2)+'\n');print('original query preserved; counted copy generated')
