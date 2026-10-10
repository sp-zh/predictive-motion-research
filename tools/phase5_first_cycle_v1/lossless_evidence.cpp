#include "lossless_evidence.hpp"
#include <algorithm>
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <limits>
#include <stdexcept>
#include <sys/stat.h>
#include <unistd.h>
#include <yaml-cpp/yaml.h>
namespace phase5_first_cycle_v1 {
namespace {
constexpr std::uint64_t byte_cap=128ULL*1024*1024;
void need(bool x,const char* s){if(!x)throw std::runtime_error(s);}
std::string digest(EVP_MD_CTX* ctx){std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> copy(EVP_MD_CTX_new(),EVP_MD_CTX_free);
 need(copy&&EVP_MD_CTX_copy_ex(copy.get(),ctx)==1,"actual output prefix hash clone failed");unsigned char b[32]{};unsigned n=0;
 need(EVP_DigestFinal_ex(copy.get(),b,&n)==1&&n==32,"actual output prefix hash final failed");const char* hex="0123456789abcdef";std::string out;
 for(unsigned j=0;j<n;++j){out.push_back(hex[b[j]>>4]);out.push_back(hex[b[j]&15]);}return out;}
void metadata(BinaryFile& f,const live::NativeMetadata& m){
 f.text(m.pinocchio_version);f.u64(m.nq);f.u64(m.nv);
 for(const auto* v:{&m.joint_names,&m.frame_names}){f.u64(v->size());for(const auto& s:*v)f.text(s);}
 for(const auto* v:{&m.idx_q,&m.idx_v,&m.joint_nq,&m.joint_nv}){f.u64(v->size());for(int x:*v)f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(x)));}
 for(const auto* v:{&m.masses,&m.armature,&m.gravity,&m.R,&m.B,&m.damping})f.vector(*v);
}
void identity(BinaryFile& f,const live::FileIdentity& id){f.text(id.path);f.text(id.sha256);f.u64(id.bytes);}
}
BinaryFile::BinaryFile(int fd,EVP_MD_CTX* hash,FileReceipt& r,std::uint64_t& total,std::uint64_t limit):fd_(fd),hash_(hash),receipt_(r),total_(total),limit_(limit){}
void BinaryFile::bytes(const void* ptr,std::size_t n){need(total_<=limit_&&n<=limit_-total_,"independent evidence output cap before write");const auto* p=static_cast<const unsigned char*>(ptr);
 while(n){const auto got=::write(fd_,p,n);if(got<0&&errno==EINTR)continue;need(got>0,"actual evidence write failed; prefix retained");
  receipt_.bytes+=static_cast<std::uint64_t>(got);total_+=static_cast<std::uint64_t>(got);
  receipt_.hash_valid=false;need(EVP_DigestUpdate(hash_,p,static_cast<std::size_t>(got))==1,"actual output prefix SHA update failed");receipt_.hash_valid=true;p+=got;n-=static_cast<std::size_t>(got);}
}
void BinaryFile::u64(std::uint64_t x){unsigned char b[8];for(int j=0;j<8;++j)b[j]=static_cast<unsigned char>((x>>(8*j))&255);bytes(b,8);}
void BinaryFile::number(double d){static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"IEEE double evidence required");std::uint64_t x;std::memcpy(&x,&d,8);u64(x);}
void BinaryFile::text(const std::string& s){need(s.size()<=1024*1024,"bounded output text");u64(s.size());bytes(s.data(),s.size());}
void BinaryFile::matrix(const Eigen::MatrixXd& m){u64(m.rows());u64(m.cols());for(Eigen::Index r=0;r<m.rows();++r)for(Eigen::Index c=0;c<m.cols();++c)number(m(r,c));}
void BinaryFile::vector(const Eigen::VectorXd& v){u64(v.size());for(double x:v)number(x);}
void BinaryFile::state(const phase5_public_coupled_augmented::State& s){vector(s.q);vector(s.v);vector(s.C);vector(s.w);number(s.s);number(s.r);}
void BinaryFile::state(const live::State30& s){for(const auto* v:{&s.q,&s.v,&s.C,&s.w})for(double x:*v)number(x);number(s.s);number(s.r);}
Evidence::Evidence(const std::string& dir):dir_(dir){need(dir_.is_absolute()&&!std::filesystem::exists(dir_),"fresh absolute output directory required");
 need(std::filesystem::create_directory(dir_),"FIRST output directory creation failed");::chmod(dir_.c_str(),0700);receipts_.reserve(12);}
void Evidence::write(const std::string& name,const std::string& role,const std::function<void(BinaryFile&)>& emit){
 need(!name.empty()&&name.find('/')==std::string::npos&&name.find("..") ==std::string::npos&&receipts_.size()<12,"bounded fixed artifact names");
 receipts_.push_back({name,role,{},{},0,false});auto& r=receipts_.back();int fd=-1;
 std::unique_ptr<EVP_MD_CTX,decltype(&EVP_MD_CTX_free)> hash(EVP_MD_CTX_new(),EVP_MD_CTX_free);
 try{need(hash&&EVP_DigestInit_ex(hash.get(),EVP_sha256(),nullptr)==1,"output SHA init");r.hash_valid=true;
  fd=::open((dir_/name).c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);need(fd>=0,"FIRST evidence file refused");r.created=true;
  const bool final_role=role=="ACTUAL_NATIVE_BOOTSTRAP_SNAPSHOT"||role=="ACTUAL_DIRECT_BOOTSTRAP_API_ENTRIES";
  BinaryFile out(fd,hash.get(),r,total_,final_role?byte_cap:byte_cap-4ULL*1024*1024);out.text("P5_FIRST_CYCLE_LOSSLESS_V1");out.text(role);emit(out);
  need(::fsync(fd)==0,"evidence fsync failed");r.sha256=digest(hash.get());const int owned=fd;fd=-1;need(::close(owned)==0,"evidence close failed; no close retry");r.complete=true;
 }catch(const std::exception& e){r.error=e.what();if(hash&&r.hash_valid)try{r.sha256=digest(hash.get());}catch(...){}if(fd>=0)::close(fd);throw;}
}
void Evidence::snapshot(const std::string& name,const Snapshot& s){write(name,"ACTUAL_NATIVE_BOOTSTRAP_SNAPSHOT",[&](BinaryFile& f){
 f.text(s.epoch);f.text(s.source);f.text(s.stage);f.text(s.first_error);f.u64(s.complete);f.u64(s.joints_read);f.u64(s.contacts);f.number(s.simulation_time);f.state(s.actual);
 f.u64(s.integration_before_written);f.u64(s.integration_before.size());for(double x:s.integration_before)f.number(x);
 f.u64(s.integration_after_written);f.u64(s.integration_after.size());for(double x:s.integration_after)f.number(x);
 });}
void Evidence::modelOpen(const live::ModelOpenOutcome& o){write("model_open.bin","ORIGINAL_MODEL_OPEN_RESULT",[&](BinaryFile& f){
 f.u64(o.hasModel());f.u64(o.constructorAttempted());f.u64(o.metadataAttempted());f.text(o.refusal());const auto* m=o.observedMetadata();f.u64(m!=nullptr);if(m)metadata(f,*m);
 });}
void Evidence::rawForecast(const live::OwnedPublicForecast& source){write("original_nominal.bin","ORIGINAL_GENUINE_NOMINAL_BEFORE_ADAPTER",[&](BinaryFile& f){
 f.text(source.transportFailure());f.text(source.structuralRefusal());f.text(source.invocationSha256());f.text(std::string(source.verifiedUnits()));f.text(std::string(source.verifiedCertificateName()));
 identity(f,source.currentProducerIdentity());identity(f,source.reviewRecordIdentity());identity(f,source.protocolIdentity());
 f.u64(source.verifiedFiles().size());for(const auto& id:source.verifiedFiles())identity(f,id);
 f.u64(source.verifiedLoadedLibraries().size());for(const auto& id:source.verifiedLoadedLibraries())identity(f,id);
 metadata(f,source.verifiedMetadata());f.state(source.actualContext().actualInitial());
 for(double x:source.actualContext().previousAlpha())f.number(x);f.number(source.actualContext().previousB());
 const auto attempts=source.releaseAttemptFacts();for(auto x:{attempts.prepare,attempts.open,attempts.forecast,attempts.constructor,attempts.metadata,attempts.rollout})f.u64(x);
 f.u64(source.mesh().cycles().size());for(auto n:source.mesh().cycles())f.u64(n);
 f.u64(source.nativeCells().size());for(const auto& c:source.nativeCells()){f.u64(c.cycles);f.vector(c.alpha);f.number(c.b);}
 const auto* raw=source.originalResult();f.u64(raw!=nullptr);if(!raw)return;
 f.u64(raw->value.success);f.u64(raw->value.has_final_state);f.text(raw->value.error);f.state(raw->value.final_state);
 f.u64(raw->extension_jacobian_success);f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(raw->first_uncertified_substep)));f.text(raw->error);
 f.u64(raw->value.substeps.size());for(const auto& s:raw->value.substeps){f.u64(s.cell);f.u64(s.cycle);f.u64(s.half);f.number(s.elapsed_s);f.number(s.s_reference);f.number(s.r_reference);
  for(const auto* v:{&s.q,&s.v,&s.C,&s.w,&s.friction.force})f.vector(*v);f.u64(s.friction.branches.size());for(int x:s.friction.branches)f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(x)));
  f.u64(s.friction.iterations);f.number(s.friction.original_kkt);f.u64(s.control_clips);f.u64(s.force_clips);}
 for(const auto* v:{&raw->value.cycle_end_states,&raw->value.cell_end_states}){f.u64(v->size());for(const auto& s:*v)f.state(s);}
 for(const auto* v:{&raw->substep_maps,&raw->cycle_maps,&raw->cell_maps}){f.u64(v->size());for(const auto& m:*v){f.u64(m.cell);f.u64(m.cycle);f.u64(m.half);f.state(m.origin);f.state(m.state);f.state(m.cell_origin);f.vector(m.input);
  f.matrix(m.A);f.matrix(m.B);f.matrix(m.cell_A);f.matrix(m.cell_B);f.vector(m.defect);f.vector(m.cell_defect);}}
 });}
void Evidence::integration(const bridge::Outcome& source){write("inline_qp.bin","INLINE_QP_COMPLETE_OR_RETAINED_PREFIX",[&](BinaryFile& f){
 const auto& t=source.trace();f.text(t.stage);f.text(t.first_error);f.u64(t.complete);f.u64(t.refused);f.u64(t.factor_rows_written);f.u64(t.constraint_rows_written);f.u64(t.task_nodes_returned);f.u64(t.planned_numeric_slots);f.u64(t.snapshot_age_bound);f.text(t.observation_source);
 f.u64(static_cast<unsigned>(t.timing_mode));f.number(t.original_observer_age);f.number(t.known_upstream_elapsed);f.number(t.connection_elapsed);f.u64(t.linear_geometry_present);
 const auto& p=source.retainedProblem();f.matrix(p.original_si.hessian);f.vector(p.original_si.gradient);f.matrix(p.original_si.constraints);f.vector(p.original_si.lower);f.vector(p.original_si.upper);f.number(p.original_si.state_age_seconds);
 f.matrix(p.F);f.vector(p.f);f.vector(p.seed);f.number(p.constant);f.u64(p.rows.size());for(const auto& r:p.rows){f.text(r.label);f.text(r.units);}
 f.u64(p.terms.size());for(const auto& r:p.terms){f.text(r.name);f.u64(r.first_factor_row);f.u64(r.rows);}
 f.u64(p.retained_task_prefix.size());for(const auto& t:p.retained_task_prefix){f.text(t.source_id);f.vector(t.residual);f.vector(t.Js);f.matrix(t.Jq);}
 // Sparse certificate's exact scalar contents and ordered row/column indices.
 f.u64(p.psd_factor.rows());f.u64(p.psd_factor.cols());f.u64(p.psd_factor.nonZeros());for(int c=0;c<p.psd_factor.outerSize();++c)for(Eigen::SparseMatrix<double>::InnerIterator x(p.psd_factor,c);x;++x){f.u64(x.row());f.u64(x.col());f.number(x.value());}
 });}
void Evidence::candidate(const bridge::CandidateOutcome& c){write("candidate.bin","SOLVER_RESULT_AND_DATA_ONLY_PREVIEW",[&](BinaryFile& f){
 f.text(c.stopReason());f.u64(c.executionPermission());f.u64(c.solveAttempts());f.u64(c.solverWrapperEntries());const auto& r=c.solverResult();f.u64(static_cast<unsigned>(r.status));f.u64(r.raw_status);f.u64(r.api_error);f.u64(r.iterations);f.u64(static_cast<std::uint64_t>(static_cast<std::int64_t>(r.maximum_violation_row)));f.vector(r.velocity);
 for(double x:{r.violation,r.primal_residual,r.dual_residual,r.setup_seconds,r.solve_seconds,r.minimum_row_scale,r.maximum_row_scale,r.minimum_variable_scale,r.maximum_variable_scale,r.solver_absolute_tolerance,r.solver_relative_tolerance,r.initial_rho,r.rho_estimate,r.update_seconds})f.number(x);
 for(auto x:{r.workspace_reused,r.matrix_updated,r.dual_reused})f.u64(x);f.u64(r.dual_mapped_rows);f.text(r.reset_reason);f.u64(r.hessian_nonzeros);f.u64(r.constraint_nonzeros);f.u64(r.rho_updates);f.u64(r.polish_status);
 f.u64(c.originalRowViolations().size());for(double x:c.originalRowViolations())f.number(x);
 const auto& timing=c.timing();f.u64(static_cast<unsigned>(timing.mode));for(double x:{timing.original_observer_age,timing.known_upstream_elapsed,timing.connection_and_solver_elapsed,timing.known_wall_age})f.number(x);f.u64(timing.known_current_age_within_policy);f.u64(timing.complete_online_observation_timing_proved);
 const auto& p=c.forensicFirstPreview();f.u64(p.has_value());if(p){for(const auto* v:{&p->C_next,&p->w_next,&p->alpha,&p->implied_alpha,&p->command_jerk_if_accepted})for(double x:*v)f.number(x);
  for(double x:{p->s_next,p->r_next,p->b,p->progress_jerk})f.number(x);for(double x:p->half_s_reference)f.number(x);for(double x:p->half_r_reference)f.number(x);f.u64(p->from.completed_tick);f.u64(p->from.completed_command_sequence);}
 const auto& tail=c.terminalTail();f.u64(tail.has_value());if(tail){for(double x:tail->final_w)f.number(x);for(double x:tail->last_alpha)f.number(x);f.number(tail->final_r);f.number(tail->last_b);f.u64(tail->exact_zero_command_progress_tail);}
 const auto& request=c.forwardRequest();f.u64(request.has_value());if(request){f.state(request->actual_initial_at_completed_boundary);f.u64(request->boundary.completed_tick);f.u64(request->boundary.completed_command_sequence);f.text(request->observation_id);f.text(request->transaction_id);f.text(request->nominal_invocation_sha256);for(auto n:request->cycles)f.u64(n);f.u64(request->candidate_controls.size());for(const auto& u:request->candidate_controls){for(double x:u.alpha)f.number(x);f.number(u.b);}}
 });}
void Evidence::bootstrap(const BootstrapFacts& b){write("bootstrap.bin","ACTUAL_DIRECT_BOOTSTRAP_API_ENTRIES",[&](BinaryFile& f){for(auto n:{b.load_xml,b.make_data,b.reset_keyframe,b.forward,b.copy_data,b.state_size,b.get_state,b.joint_name_queries,b.key_name_queries})f.u64(n);f.u64(b.initialized);f.text(b.first_error);});}
void Evidence::finish(const std::string& stage,const std::string& error,bool same){
 YAML::Emitter o;o<<YAML::BeginMap<<YAML::Key<<"schema"<<YAML::Value<<"FIRST_CYCLE_EVIDENCE_MANIFEST_V1"<<YAML::Key<<"stage"<<YAML::Value<<stage<<YAML::Key<<"error"<<YAML::Value<<error<<YAML::Key<<"actual_boundary_unchanged"<<YAML::Value<<same<<YAML::Key<<"output_bytes"<<YAML::Value<<total_<<YAML::Key<<"execution_permission"<<YAML::Value<<false<<YAML::Key<<"phase5"<<YAML::Value<<"NOT_ACCEPTED"<<YAML::Key<<"phase6"<<YAML::Value<<"NOT_STARTED"<<YAML::Key<<"files"<<YAML::Value<<YAML::BeginSeq;
 for(const auto& r:receipts_)o<<YAML::BeginMap<<YAML::Key<<"file"<<YAML::Value<<r.file<<YAML::Key<<"role"<<YAML::Value<<r.role<<YAML::Key<<"bytes"<<YAML::Value<<r.bytes<<YAML::Key<<"sha256"<<YAML::Value<<r.sha256<<YAML::Key<<"created"<<YAML::Value<<r.created<<YAML::Key<<"hash_valid"<<YAML::Value<<r.hash_valid<<YAML::Key<<"complete"<<YAML::Value<<r.complete<<YAML::Key<<"error"<<YAML::Value<<r.error<<YAML::EndMap;o<<YAML::EndSeq<<YAML::EndMap;
 const std::string text=o.c_str();const int fd=::open((dir_/"MANIFEST.yaml").c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);need(fd>=0,"FIRST manifest creation failed");std::size_t at=0;while(at<text.size()){const auto n=::write(fd,text.data()+at,text.size()-at);if(n<0&&errno==EINTR)continue;if(n<=0){::close(fd);throw std::runtime_error("manifest prefix write failed");}at+=static_cast<std::size_t>(n);}const int sync=::fsync(fd),close=::close(fd);need(sync==0&&close==0,"manifest flush/close failed");
}
}
