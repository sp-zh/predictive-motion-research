#!/usr/bin/env python3
"""Read-only root branch-crossing counterexample; no model calls."""
import json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-extension-cpp-v1';SRC=BASE/'independent_root_diagnosis/BRANCH_GATE_FAILURE_DIAGNOSIS.json';CONST=ROOT/'results/phase5/development/public-coupled-servo-v1-training/public_constants.json';DEST=ROOT/'figures/phase5'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
d=json.loads(SRC.read_text());assert d['decision']=='FAIL_DECLARED_SAME_BRANCH_FD_GATE' and d['new_model_calls'] is False and d['source_inputs_gates_unchanged'] is True and d['changed_probe_count']==2 and len(d['issues'])==2
items=d['issues'];nominal=items[0]['diagnostics'][0];assert items[1]['diagnostics'][0]==nominal;points=[nominal]+[x['diagnostics'][1] for x in items];eta=json.loads(CONST.read_text())['friction_bounds'][1]
assert points[0]['force'][1]==-eta and points[0]['branches'][1]==-1 and all(x['branches'][1]==0 for x in points[1:]);assert all(x['case']=='root_boundary_initial_w_plusV' and x['substep']==0 for x in items)
forces=[(x['force'][1]+eta)*1000 for x in points];gradients=[x['gradient'][1] for x in points];labels=['Nominal','q₂ + ε','C₂ − ε'];colors=['#2467af','#c66d38','#9b3840']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'figure.facecolor':'#f7f8fc','axes.facecolor':'white','savefig.facecolor':'#f7f8fc'})
fig=plt.figure(figsize=(13,7.5));gs=fig.add_gridspec(1,2,left=.085,right=.96,bottom=.24,top=.77,wspace=.32);axes=[fig.add_subplot(gs[0,j]) for j in range(2)]
for ax,values,title,ylabel in zip(axes,(forces,gradients),('Friction force leaves the lower bound','Individual strict conditions still pass'),('f₂ − (−η₂) [mN·m]','Original-H KKT gradient₂ [rad/s²]')):
 ax.scatter(range(3),values,c=colors,s=120,zorder=4);ax.set_xticks(range(3),labels);ax.set_xlim(-.4,2.4);ax.set_ylabel(ylabel);ax.set_title(title,fontsize=14,pad=12);ax.grid(axis='y',alpha=.18)
axes[0].axhline(0,color='#536178',ls='--',lw=1);axes[0].set_ylim(-.18,1.95)
for i,v in enumerate(forces):axes[0].annotate(f'{v:.6f}',(i,v),xytext=(0,13),textcoords='offset points',ha='center')
axes[1].set_yscale('symlog',linthresh=1e-10);axes[1].set_ylim(-2e-10,.1);axes[1].axhline(1e-7,color='#9b3840',ls='--',lw=1);axes[1].text(-.32,1.6e-7,'active margin gate 1e−7',color='#9b3840',fontsize=9);axes[1].annotate(f'{gradients[0]:.9f}',(0,gradients[0]),xytext=(0,13),textcoords='offset points',ha='center')
for i in (1,2):axes[1].annotate('free\n|gradient| ≤ 1e−10',(i,gradients[i]),xytext=(0,17+18*(i-1)),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('Independent root counterexample: fixed ε crosses a friction branch',x=.06,y=.94,ha='left',fontsize=18,fontweight='bold');fig.text(.06,.875,'root_boundary_initial_w_plusV · first 2 ms half · ε = 1e−6 · joint₂ (array index 1)',fontsize=11)
fig.text(.06,.16,'Nominal branch −1 (lower bound); both changed probes branch 0 (free). Other physical clamp signatures are unchanged.',fontsize=10)
fig.text(.06,.115,'A strict pointwise margin does not guarantee the declared finite probe radius. The original two-ε branch gate remains FAILED.',fontsize=10,color='#9b3840')
fig.text(.06,.068,'Saved diagnostics only: no new model call, parameter, case, gate or ε change; all original root cases and failures retained.',fontsize=10)
fig.text(.06,.024,'DEVELOPMENT FAILURE EVIDENCE · extension Jacobian alone is no admissibility / safety / main certificate · Phase5 unaccepted',fontsize=10,color='#9b3840')
p=DEST/'phase5_public_coupled_augmented_extension_failure.png';fig.savefig(p,dpi=180);plt.close(fig);meta=dict(source='Original saved independent root branch-gate diagnosis; no new model calls',source_sha256=sha(SRC),source_original_Mac='results/phase5-reference/root-augmented-boundary-predeclaration-20261007/BRANCH_GATE_FAILURE_DIAGNOSIS.json',script_sha256=sha(Path(__file__)),constants_sha256=sha(CONST),figure_sha256=sha(p),figure_bytes=p.stat().st_size,case=items[0]['case'],substep=0,epsilon=1e-6,joint_array_index=1,joint_label='joint2',eta_Nm=eta,points=points,force_above_lower_mNm=forces,gradient_rad_s2=gradients,root_decision=d['decision'],phase5='NOT_ACCEPTED',new_model_calls=False,display='Gradient uses symlog linthresh1e-10 so near-zero free gradients remain visible; force offset only for display.',scope='Strict nominal physical policy is unchanged; finite-step same-branch gate failure retained. No epsilon selection, new plant or main/task/timing/Phase5 acceptance.');p.with_suffix('.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n');print('failure',sha(p))
