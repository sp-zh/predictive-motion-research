#!/usr/bin/env python3
"""Prepare isolated prospectively frozen v3 fixture; never run plant here."""
from pathlib import Path
import hashlib,yaml
p=Path('/home/codextransfer/predictive_motion');source=p/'tools/phase5_servo_reference/servo_safe_reference_velocity_fixture.cpp';dest=source.with_name('servo_safe_reference_cone_fixture.cpp');assert not dest.exists()
s=source.read_text().replace('#include <Eigen/Cholesky>','#include <Eigen/Cholesky>\n#include "../phase5_command_cone/signed_velocity_cone.hpp"')
helper='''
void addCommandContinuation(QpProblem& q,const CommandLimits& bounds,const CommandHistory& history) {
  for(int j=0;j<history.accepted_velocity.size();++j) {
    phase5_diagnostic::Limits limits{bounds.velocity(j),bounds.acceleration(j),bounds.jerk(j),bounds.dt};
    for(const auto& entry:phase5_diagnostic::candidateVelocityRows(history.accepted_velocity(j),limits)) {
      Eigen::RowVectorXd row=Eigen::RowVectorXd::Zero(history.accepted_velocity.size());
      row(j)=entry.coefficient;appendConstraint(q,row,entry.lower,entry.upper);
    }
  }
}
bool continuableCommand(const QpResult& candidate,const CommandLimits& bounds,const CommandHistory& history) {
  if(candidate.status!=QpStatus::Solved||candidate.velocity.size()!=history.accepted_velocity.size())return false;
  for(int j=0;j<candidate.velocity.size();++j) {
    phase5_diagnostic::Limits limits{bounds.velocity(j),bounds.acceleration(j),bounds.jerk(j),bounds.dt};
    double next_alpha=(candidate.velocity(j)-history.accepted_velocity(j))/bounds.dt;
    if(!phase5_diagnostic::accelerationInterval(candidate.velocity(j),next_alpha,limits).feasible)return false;
  }
  return true;
}
void logQp(std::ostream& rows,std::ostream& solves,int tick,const std::string& kind,const QpProblem& q,const QpResult& r) {
  for(int i=0;i<q.lower.size();++i){rows<<tick<<','<<kind<<','<<i<<','<<q.lower(i)<<','<<q.upper(i);vectorCsv(rows,q.constraints.row(i).transpose());rows<<'\\n';}
  solves<<tick<<','<<kind<<','<<statusName(r.status)<<','<<r.raw_status<<','<<r.api_error<<','<<r.iterations<<','<<r.violation<<','<<r.maximum_violation_row<<','<<r.velocity.size()<<','<<q.state_age_seconds<<','<<r.setup_seconds<<','<<r.solve_seconds;
  for(int j=0;j<7;++j)solves<<','<<(j<r.velocity.size()?r.velocity(j):NAN);
  solves<<'\\n';rows.flush();solves.flush();
}
'''
s=s.replace('void headers(',helper+'\nvoid headers(')
s=s.replace('o.absolute_tolerance=o.relative_tolerance=1e-9;','o.absolute_tolerance=o.relative_tolerance=cfg["qp_stopping_tolerance"].as<double>();')
s=s.replace('std::ofstream raw(dir/"raw.csv"),cycles(dir/"cycles.csv");','''std::ofstream raw(dir/"raw.csv"),cycles(dir/"cycles.csv"),qp_rows(dir/"all_qp_rows.csv"),qp_solves(dir/"all_qp_solves.csv");
    qp_rows<<std::setprecision(17)<<"tick,kind,row,lower,upper,A0,A1,A2,A3,A4,A5,A6\\n";
    qp_solves<<std::setprecision(17)<<"tick,kind,wrapper_status,raw_status,api_error,iterations,SI_violation,maximum_violation_row,candidate_size,state_age_s,setup_s,solve_s,x0,x1,x2,x3,x4,x5,x6\\n";''')
s=s.replace('auto query=geometry.query(robot,measured.q,true,true,.03);','addCommandContinuation(q,bounds,history);\n        auto query=geometry.query(robot,measured.q,true,true,.03);')
s=s.replace('if(candidate.status!=QpStatus::Solved)return false;','if(candidate.status!=QpStatus::Solved||!continuableCommand(candidate,bounds,history))return false;')
s=s.replace('auto result=solveQp(q,o);status=statusName(result.status);','auto result=solveQp(q,o);logQp(qp_rows,qp_solves,tick,"tracking",q,result);status=statusName(result.status);')
s=s.replace('"NONLINEAR_OR_STALE":status','"CONTINUATION_NONLINEAR_OR_STALE":status')
s=s.replace('auto stop=constrainPreviewCommand(stoppingProblem(7),bounds,history);','auto stop=constrainPreviewCommand(stoppingProblem(7),bounds,history);\n          addCommandContinuation(stop,bounds,history);')
s=s.replace('result=solveQp(stop,o);status=statusName(result.status);','result=solveQp(stop,o);logQp(qp_rows,qp_solves,tick,"stop",stop,result);status=statusName(result.status);')
s=s.replace('"Local servo identification/held-out development validation fixture; not a motion research trial"','"Curated seen-input development fixture with prospective tighter solver precision and isolated command velocity continuation; not an untouched holdout or online research trial"')
dest.write_text(s)
cmake=p/'tools/phase5_servo_reference/CMakeLists.txt'
with cmake.open('a') as f:f.write('''
add_executable(servo_safe_reference_cone_fixture servo_safe_reference_cone_fixture.cpp)
target_include_directories(servo_safe_reference_cone_fixture PRIVATE ../phase5_adapter ../phase4_adapters)
target_link_libraries(servo_safe_reference_cone_fixture predictive_motion_kinematics::robot_kinematics predictive_motion_sim::plant predictive_motion_control::predictive_controller coal::coal yaml-cpp)
''')
cfg=yaml.safe_load((p/'config/phase5_development/servo_validation_safe_reference_v2.yaml').read_text());cfg.update({'validation_waveform_id':'curated-reference-velocity-cone-v3-91012','qp_stopping_tolerance':1e-12,'solver_policy':'Native SOLVED-only and original SI1e-7, iterations4000,50ms live age/solve checks unchanged; tighter stopping criterion preselected from independent captured-QP audit, not acceptance relaxation.','command_continuation_scope':'Discrete signed velocity cone on current issued candidate and stop; next accepted history must remain continuable; no future position/geometry or real-plant stop certificate.','root_review_required_before_run':True})
(p/'config/phase5_development/servo_validation_safe_reference_v3.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
print('PREPARED_NOT_RUN',hashlib.sha256(dest.read_bytes()).hexdigest())
