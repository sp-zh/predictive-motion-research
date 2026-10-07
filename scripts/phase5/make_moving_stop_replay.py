from pathlib import Path
import shutil
p=Path('/home/codextransfer/predictive_motion')
s=(p/'tools/phase5_adapter/phase5_benchmark.cpp').read_text()
needle='    auto cfg = YAML::LoadFile(argv[2]);'
insert='''    // Focused component replay: recorded commands drive the complete plant
    // from the original reset, never q/v-only state injection.
    struct Recorded { std::vector<double> values; };
    std::ifstream replay_input(root / "results/phase5/development/moving-stop-input/raw.csv");
    if (!replay_input) throw std::runtime_error("missing immutable replay input");
    std::string replay_line, replay_cell;
    std::getline(replay_input,replay_line);
    std::map<std::string,int> columns;
    { std::istringstream cells(replay_line); int i=0;
      while(std::getline(cells,replay_cell,',')) columns[replay_cell]=i++; }
    std::map<std::pair<int,int>,Recorded> recorded;
    while(std::getline(replay_input,replay_line)) {
      std::istringstream cells(replay_line); Recorded x;
      while(std::getline(cells,replay_cell,',')) {
        try { x.values.push_back(std::stod(replay_cell)); }
        catch (...) { x.values.push_back(NAN); }
      }
      int tick=int(x.values.at(columns.at("tick"))), sub=int(x.values.at(columns.at("substep")));
      if(tick<695 && sub>0) recorded[{tick,sub}]=std::move(x);
    }
    if(recorded.size()!=1390) throw std::runtime_error("replay roster");
    auto field = [&](const Recorded& x,const std::string& name) {
      return x.values.at(columns.at(name)); };
    auto recordedVector = [&](const Recorded& x,const std::string& name) {
      Eigen::VectorXd v(7); for(int i=0;i<7;++i)v(i)=field(x,name+std::to_string(i));return v; };
    std::ofstream replay_error(dir / "replay_error.csv");
    replay_error << std::setprecision(17) << "tick,substep,q_max_error,dq_max_error\\n";
'''
assert needle in s;s=s.replace(needle,insert+needle)
# Match the original loop start exactly and insert replay after capture/history reset.
needle='      stop_status = "NOT_ATTEMPTED";'
insert='''      if(tick<695) {
        const auto& first=recorded.at({tick,1});
        const auto& last=recorded.at({tick,2});
        history.accepted_position=recordedVector(first,"q_accepted_");
        history.accepted_velocity=recordedVector(first,"dq_accepted_");
        history.accepted_acceleration=recordedVector(first,"command_acc_");
        requested=recordedVector(first,"dq_requested_");
        qrequested=recordedVector(first,"q_requested_");
        modelq=recordedVector(first,"q_model_control_");
        model_requested_a=recordedVector(first,"requested_model_acc_");
        model_applied_a=recordedVector(first,"applied_model_acc_");
        cmdacc=history.accepted_acceleration;
        cmdjerk=recordedVector(first,"command_jerk_");
        plant.command(plant.names(),std::vector<double>(history.accepted_position.data(),
                                                      history.accepted_position.data()+7));
        stamp=Clock::now();
        for(int sub=1;sub<=2;++sub) {
          plant.step(); measured=observe(plant,scratch.get(),robot,geometry);
          const auto& original=recorded.at({tick,sub});
          const double qe=(measured.q-recordedVector(original,"q_post_")).cwiseAbs().maxCoeff();
          const double ve=(measured.dq-recordedVector(original,"dq_post_")).cwiseAbs().maxCoeff();
          replay_error<<tick<<','<<sub<<','<<qe<<','<<ve<<'\\n';
          if(qe>1e-10 || ve>1e-10) throw std::runtime_error("full command replay state mismatch");
          Eigen::VectorXd acc=(measured.dq-prev_dq)/subdt;
          Eigen::VectorXd jerk=(acc-prev_acc)/subdt;
          prev_dq=measured.dq;prev_acc=acc;
          writeRow(tick,sub,"recorded_command_replay",field(original,"command_issued"),
                   field(original,"s"),field(original,"r"),field(original,"b"),0,acc,jerk);
          if(measured.contacts || (tick>=warmup && measured.clearance<safe))
            throw std::runtime_error("replay actual safety violation");
        }
        progress=field(last,"s");progress_speed=field(last,"r");previous_b=field(last,"b");
        cost.issued=field(first,"command_issued");
        cost.plant=seconds(stamp);cost.wall=seconds(cycle_start);cycles.push_back(cost);
        raw.flush();replay_error.flush();
        continue;
      }
      if(tick==695) {
        stopping=true;failure="INJECTED_FAILURE_AFTER_EXACT_COMMAND_REPLAY";
        status="FOCUSED_MOVING_STOP";failed_attempts++;
      }
'''
assert needle in s;s=s.replace(needle,insert+needle)
s=s.replace('#include <random>','#include <random>\n#include <map>')
s=s.replace('"Paused-simulation functional reference; not online/real-time success"',
            '"Exact accepted-command replay then moving-stop component test; not a main research trial"')
(p/'tools/phase5_adapter/moving_stop_replay.cpp').write_text(s)
cm=p/'tools/phase5_adapter/CMakeLists.txt';c=cm.read_text()
if 'add_executable(moving_stop_replay' not in c:
 c+='''
add_executable(moving_stop_replay moving_stop_replay.cpp)
target_include_directories(moving_stop_replay PRIVATE ../phase4_adapters)
target_link_libraries(moving_stop_replay predictive_motion_kinematics::robot_kinematics predictive_motion_sim::plant predictive_motion_control::predictive_controller coal::coal yaml-cpp)
''';cm.write_text(c)
dest=p/'results/phase5/development/moving-stop-input';dest.mkdir(exist_ok=False)
shutil.copyfile(Path('/mnt/d/CodexTransfer/projects/predictive_motion/phase5/raw/reference-v14/predictive_inspection_91011/raw.csv'),dest/'raw.csv')
print('Generated full command replay, retaining the same benchmark stop block.')
