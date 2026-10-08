#!/usr/bin/env python3
"""Actual frozen finite diagnostic outputs; no new model or plant calls."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json,hashlib,collections
from pathlib import Path
ROOT=Path('/home/codextransfer/predictive_motion')
BASE=ROOT/'results/phase5/development/public-coupled-finite-trial-cpp-v1'
ATTEMPT=BASE/'parity-attempt1';FIG=ROOT/'figures/phase5';FIG.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((ATTEMPT/'report.json').read_text());native=json.loads((ATTEMPT/'native.json').read_text())
cases={x['name']:x for x in native['cases']};records={x['name']:x for x in report['records']}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.titlesize':14,'axes.labelsize':12,'figure.facecolor':'white','axes.spines.top':False,'axes.spines.right':False})
scope='Development finite sampled closed-model diagnostics only. GLOBAL nominal cell chain. No connecting segment/ball/admissibility/execution/safety/uniform error bound/main/task/timing or Phase5 acceptance. Earlier independent FD gate FAIL retained.'
def finish(fig,stem,data):
 fig.text(.03,.012,'Recorded predictor outputs only • no new plant • Phase5 NOT_ACCEPTED • earlier independent FD gate remains FAIL',fontsize=10,color='#8b2626')
 path=FIG/('phase5_public_coupled_finite_trial_'+stem+'.png')
 fig.savefig(path,dpi=180,facecolor='white');plt.close(fig)
 provenance=dict(source='actual frozen parity-attempt1/native.json and report.json',script_sha256=sha(Path(__file__)),report_sha256=sha(ATTEMPT/'report.json'),native_sha256=sha(ATTEMPT/'native.json'),inputs_sha256=sha(BASE/'inputs/cases.json'),freeze_sha256=sha(BASE/'frozen_before_predictions.json'),binary_sha256=report['binary_sha256'],figure_sha256=sha(path),figure_bytes=path.stat().st_size,scope=scope,phase5='NOT_ACCEPTED',new_model_or_plant_calls=False,plot_data=data)
 path.with_suffix('.json').write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
 print(path.name,sha(path),flush=True)
# All cases in aggregate; prefix detail uses declared representative categories.
order=['sampled_strict_branches_unchanged','sampled_branch_changed','unsupported','forward_failed','mesh_mismatch']
labels=['Strict sampled branches unchanged','Sampled branch changed','Strict derivative unsupported','Original closed forward failed','Integer mesh mismatch']
colors=['#276f89','#cd7832','#8a709e','#b34848','#6b7884']
counts=collections.Counter(x['outcome'] for x in report['records'])
selected=[
 ('known_w_bound_q1_e0','Known q[1]+1e-6 branch change'),
 ('known_w_bound_C1_e1','Known C[1]−3e-7 diagnostic'),
 ('finite_distinct_nonuniform_global_chain','Distinct controls, mesh [1,3,2,4]'),
 ('same_total_different_integer_mesh','Same duration, different per-cell mesh'),
 ('physical_weak_lower_zero_gradient_trial','Weak physical point'),
 ('initial_C_boundary_trial','Closed C boundary'),
 ('future_trial_original_prefix','Future trial progress failure'),
 ('future_nominal_original_prefix','Future nominal progress failure'),
 ('later_generated_command_domain_prefix','Later command-domain failure'),
 ('later_invalid_alpha_original_global_precheck','Invalid later alpha: global precheck'),
 ('trial_q_dimension_no_outputs','Invalid initial q dimension'),
 ('empty_topology_only','Empty equal topology: failed forward'),
]
fig,axes=plt.subplots(2,1,figsize=(14,11),gridspec_kw={'height_ratios':[1,2.4]})
fig.suptitle('Finite candidate diagnostics preserve branch changes and failed prefixes',fontsize=18,x=.03,ha='left',y=.975)
a=axes[0];x=np.arange(len(order));bars=a.bar(x,[counts[k] for k in order],color=colors,width=.65)
a.set_xticks(x,labels,rotation=12,ha='right');a.set_ylabel('Predeclared pairs');a.set_ylim(0,24)
for bar in bars:a.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.5,str(int(bar.get_height())),ha='center')
a.set_title('All 42 fixed pairs: labels independently checked against frozen original programs',loc='left',pad=15)
a=axes[1];y=np.arange(len(selected));nom=[records[n]['nominal_actual_steps'] for n,_ in selected];trial=[records[n]['trial_actual_steps'] for n,_ in selected]
a.barh(y-.16,nom,height=.3,color='#6b7884',label='Nominal actual 2ms outputs')
a.barh(y+.16,trial,height=.3,color='#276f89',label='Trial actual 2ms outputs')
a.set_yticks(y,[label for _,label in selected]);a.invert_yaxis();a.set_xlabel('Actually produced half steps (zero means no forecast point)')
a.set_xlim(0,24);a.legend(loc='lower right',frameon=False)
a.set_title('Declared representative prefix categories; every failed case remains in full evidence',loc='left',pad=12)
fig.subplots_adjust(left=.36,right=.97,bottom=.09,top=.90,hspace=.50)
finish(fig,'outcomes',dict(outcome_counts={k:counts[k] for k in order},prefix_selected=[dict(name=n,label=l,nominal_steps=records[n]['nominal_actual_steps'],trial_steps=records[n]['trial_actual_steps']) for n,l in selected],selection='All outcomes shown. Prefix detail fixed categories: known changed/unchanged, nonuniform, mismesh, unsupported, future/initial/global-precheck failures. No success curation or ranking.'))
# GLOBAL residuals at every actual matching half of the finite nonuniform trial.
name='finite_distinct_nonuniform_global_chain';case=cases[name]
res=[x for x in case['residuals'] if x['endpoint']=='substep'];time=[p['elapsed_s'] for p in case['nominal']['value']['substeps']]
blocks=[('q','rad'),('v','rad/s'),('C','rad'),('w','rad/s'),('s','dimensionless'),('r','1/s')]
fig,axes=plt.subplots(3,2,figsize=(14,10));fig.suptitle('Self-propagated trial vs GLOBAL nominal cell-chain affine prediction',fontsize=18,x=.03,ha='left',y=.98)
series={}
for a,(key,unit) in zip(axes.flat,blocks):
 values=[x['block_residuals'][key]['max_absolute'] for x in res];series[key]=values
 a.plot(time,values,'o-',markersize=4,color='#276f89')
 for bound in (.004,.016,.024):a.axvline(bound,color='#aeb9bf',ls='--',lw=.8)
 a.set_ylabel('max |residual| ['+unit+']');a.set_xlabel('Actual prediction time [s]');a.set_title(key+' block',loc='left')
 a.ticklabel_format(axis='y',style='sci',scilimits=(0,0));a.grid(axis='y',alpha=.15);a.set_xlim(0,.041)
fig.text(.03,.935,'Mesh [1,3,2,4] • independent state and per-cell input deviations • no actual-trial-origin reset • no residual pass threshold',fontsize=11)
fig.subplots_adjust(left=.10,right=.97,bottom=.09,top=.87,hspace=.67,wspace=.35)
finish(fig,'global_residuals',dict(case=name,time_s=time,max_absolute_residuals_by_block=series,units=dict(blocks),mesh_cycles=[1,3,2,4],command_progress_scale='C/w/s/r are affine; observed rounding-scale residuals are numerical arithmetic, not controller precision claims.',selection='Prospectively declared finite distinct-control case, not chosen by low residual.'))
# Known finite branch counterexamples/diagnostics, old FD gate never relabeled.
chosen=['known_w_bound_q1_e0','known_w_bound_q1_e1','known_w_bound_C1_e0','known_w_bound_C1_e1']
nominal=cases[chosen[0]]['nominal_inspections'][0]
points=[nominal]+[cases[n]['trial_inspections'][0] for n in chosen]
labels=['Nominal','q[1]+1e-6','q[1]+3e-7','C[1]−1e-6','C[1]−3e-7']
eta=1.137;forces=[p['physical_value']['friction']['force'][1] for p in points]
gradients=[p['friction_gradient'][1] for p in points];branches=[p['physical_value']['friction']['branches'][1] for p in points]
force_distance=[(f+eta)*1000 for f in forces]
fig,axes=plt.subplots(2,1,figsize=(13,8));fig.suptitle('Finite sampled diagnostics expose the retained friction-branch counterexamples',fontsize=17,x=.03,ha='left',y=.97)
for a,values,unit,title in zip(axes,[force_distance,gradients],['mN*m','rad/s²'],['Friction force above the lower bound (joint 2)','Original-H KKT gradient at actual first-half inputs']):
 bars=a.bar(np.arange(5),values,color=['#276f89' if b==-1 else '#cd7832' for b in branches],width=.65)
 a.set_xticks(np.arange(5),labels);a.set_ylabel(unit);a.set_title(title,loc='left',pad=14);a.set_ylim(0,max(values)*1.25)
 for i,(bar,b) in enumerate(zip(bars,branches)):a.text(i,bar.get_height()+max(values)*.035,'lower' if b==-1 else 'free',ha='center',fontsize=11)
 a.grid(axis='y',alpha=.15)
fig.text(.03,.89,'Original steps 1e-6 / 3e-7 unchanged • original closed forwards • full per-axis signatures • sampled endpoints only',fontsize=11)
fig.subplots_adjust(left=.12,right=.97,bottom=.10,top=.80,hspace=.60)
finish(fig,'known_branches',dict(labels=labels,cases=chosen,joint_zero_based=1,friction_force_Nm=forces,force_above_lower_mNm=force_distance,original_H_gradient_rad_per_s2=gradients,exact_branches=branches,lower_bound_Nm=-eta,scope='Known retained earlier FD counterexamples/diagnostics; correctly classified finite samples, no repair/replacement of old FD FAIL. No segment/radius certificate.'))
