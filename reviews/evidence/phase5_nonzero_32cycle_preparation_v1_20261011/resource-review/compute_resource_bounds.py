"""Source/saved36 fixed-shape arithmetic only; no runtime or optimizer calls."""
from pathlib import Path
from fractions import Fraction as Q
import json,hashlib
OUT=Path(__file__).resolve().parent
ROOT=Path('/Users/uot/Documents/ChatGPT/ros')
files=['tools/phase5_nonzero_progress_session_v1/'+n for n in ['cycle_support.hpp','counted_geometry.hpp','runtime_observer.cpp','runtime_observer.hpp','active_first_cycle.cpp','lossless_evidence.cpp','integrated_horizon_qp.cpp','model_boundary.cpp','normalization.cpp','affine_assembly.cpp']]+['tools/phase5_public_live_affine_v2/foundation.hpp','tools/phase5_public_live_affine_v2/foundation_resources.cpp','config/phase5.yaml','tools/phase5_adapter/phase5_benchmark.cpp','docs/phase5_development_status.md']
pins={}
for n in files:
 b=(ROOT/n).read_bytes();pins[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};p=OUT/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
C,N,T,S,nx,nu=32,20,200,400,30,8
raw=(S+T+N)*2441+S*52+(T+N+1)*30+N*9
sdk=3*raw+1000000
normalized=N*1241+S*1243
boundary=(N+1)*(30+30*160+900);embedding=790*160+790
scratch=640;work=4*30*160+4*900+60
per_source=279+raw+normalized+scratch+(S+T)*scratch+boundary+embedding+(work-scratch)+240+raw
inline=14756*(160+2)+741*(160+1)+4*160*160+20*30*160+64*160
per_numeric=inline+200000+4000000+2000000
assert raw==1541030 and sdk==5623090 and per_source==4258979 and per_numeric==8918413
# Maximum original retained rows before/after fixed reduction storage gates.
first_fixed=741*144+160*144+144*144+16*160+160+5*144+16
scaled_fixed=144*144+7*144+741*144
extra=160*(2*144+9)
maxr_first=(2000000-first_fixed)//(144+2)
maxr_final=(4000000-first_fixed-scaled_fixed-extra)//((144+2)+(144+3)+1)
assert maxr_first==12644 and maxr_final==12483
summary=json.loads(Path('/private/tmp/root_independent_nonzero_progress_actual_review_20261011/STAGE1_RESULT.json').read_text());walls=[x['timing']['wall'] for x in summary['cycles']]
h=Q(.004);s=r=Q(0);jb=Q(4.9995);b=Q(0)
for k in range(C):
 b=min(Q(.5),b+jb*h);s,r=s+h*r+Q(1,2)*h*h*b,r+h*b
result={'schema':'ROOT_PROSPECTIVE_32CYCLE_SOURCE36_RESOURCE_ARITHMETIC_V1','basis':'Fixed unchanged N20/T200/S400/full14756/741F/full144 path, not runtime success extrapolation','cycles':C,'forecast_attempts_max':2*C,'task_step_attempts_max':2*C,'task_virtual_seconds':float(C*h),'provider_only':{'scenes':C*S,'primitives':C*S*9035,'FK':C*S*14,'Jacobian':C*S*14,'requested_caps':{'scenes':13200,'primitives':120000000,'FK':200000,'Jacobian':200000}},'full_geometry_work_roster_if_all_B_C_complete':{'scenes':1000+C*(400+401+3),'primitives':(1000+C*(400+401+3))*9035,'scope':'warmup and B/C calls use other Scene paths, outside provider counters; includes initial B/C queries'},'logical_numeric':{'inline_per_cycle':inline,'geometry_per_cycle':200000,'reduction_per_cycle_reservation':4000000,'hint_per_cycle_reservation':2000000,'per_cycle':per_numeric,'all32':C*per_numeric,'requested_cap':400000000},'original_batch':{'raw_result_slots':raw,'two_resident_allowances':2*sdk,'fixed_path_charge_per_complete_cycle':per_source,'32_fixed_path_total':2*sdk+C*per_source,'hard_cumulative_cap':1024000000,'simultaneous_live_cap':64000000,'no_reset':True,'scope':'exact declared fixed source-call schedule; failures stop prefix; added capture/sample callbacks need their own charges, not caller history reset'},'binary_output':{'per_Evidence_cap':128*1024**2,'root_plus32_per_Evidence_cap_sum':33*128*1024**2,'requested_global_cap':2*1024**3,'aggregate_cap_does_not_guarantee32':True,'max_base_reduced_rows_per_current_storage_caps':maxr_final,'max_solver_rows_including160guards':maxr_final+160},'journal':{'maximum_declared_line_bytes':4096,'warm_events':3000,'C_events_if32complete':8*C,'max_all_lines_bytes':(3000+8*C)*4096,'requested_global_cap':64*1024**2,'existing_each_file_cap':12582912},'timing':{'observed36_cycle_seconds':walls,'observed36_min_max_repeat32_not_guarantee':[min(walls)*C,max(walls)*C],'hint_per_call_wall_cap_s':10,'native_per_call_solve_cap_s':20,'sum_32_hints_native_caps_before_other_work_s':C*30,'requested_CPU_s':420,'requested_wall_s':600,'requested_AS_bytes':4*1024**3,'bounded_refusal_not_all32_guarantee':True},'progress_from_initial_zero':{'max_s_using_only_b_le_half':.5*.5*float(C*h)**2,'max_r_using_only_b_le_half':.5*float(C*h),'tight_discrete_Jb_internal_guard_upper_s':float(s),'tight_discrete_Jb_internal_guard_upper_r':float(r),'scope':'algebraic upper bound, not a future control proposal or actual prediction; cannot reach normalized fullpath1 in32ticks'},'inputs':pins,'no_native_model_compiler_SSH_optimizer_calls':True}
for n,i in pins.items():b0=(ROOT/n).read_bytes();assert len(b0)==i['bytes'] and hashlib.sha256(b0).hexdigest()==i['sha256']
(OUT/'BOUNDS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['provider_only','logical_numeric','original_batch','journal','progress_from_initial_zero']}))
