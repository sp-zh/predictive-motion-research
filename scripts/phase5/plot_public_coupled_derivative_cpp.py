#!/usr/bin/env python3
"""Actual analytic physical Jacobian and independent FD verification figures."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-derivative-cpp-v1';DEST=ROOT/'figures/phase5';DEST.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=json.loads((BASE/'parity-attempt1/analytic.json').read_text());report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_PHYSICAL_DERIVATIVE_REFERENCE_ONLY'
case=next(x for x in native['cases'] if x['name']=='mixed_strict_lower_upper_free');J=np.array(case['jacobian']);plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':11,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,3,figsize=(14,9));fig.subplots_adjust(bottom=.20,top=.81,hspace=.4,wspace=.42);fig.suptitle('Physical 2 ms transition: analytic 14 × 21 derivative',fontsize=20,x=.06,ha='left');fig.text(.06,.9,'Actual mixed strict lower / upper / free friction fixture • full M, nonlinear forces and implicit damping',fontsize=12)
units=[['dimensionless','seconds','dimensionless'],['1/seconds','dimensionless','1/seconds']]
for row in range(2):
 for col in range(3):
  a=axs[row,col];block=J[row*7:(row+1)*7,col*7:(col+1)*7];lim=max(np.max(abs(block)),1e-12);im=a.imshow(block,cmap='RdBu_r',vmin=-lim,vmax=lim,aspect='equal');fig.colorbar(im,ax=a,fraction=.046,pad=.04);a.set(title=f'∂{("q_next","v_next")[row]} / ∂{("q","v","C")[col]} ({units[row][col]})',xlabel='input joint',ylabel='output joint',xticks=range(7),xticklabels=range(1,8),yticks=range(7),yticklabels=range(1,8))
fig.text(.06,.055,'Each panel uses its own signed color scale and derivative units. Matrices come from the frozen native analytic reference.\nWeak / near thresholds retain the value; the strict-branch API omits a Jacobian without disproving differentiability.\nPhase5 NOT_ACCEPTED; no augmented sensitivity, controller, new plant, task or timing acceptance.',fontsize=10)
paths=[];p=DEST/'phase5_public_coupled_derivative_cpp_matrix.png';fig.savefig(p,dpi=160);plt.close(fig);paths.append(p)
positive=[x for x in report['records'] if x['jacobian_success']];threshold=[x for x in report['records'] if x['value_success'] and not x['jacobian_success']];invalid=[x for x in report['records'] if not x['value_success']]
fig,ax=plt.subplots(1,2,figsize=(14,7));fig.subplots_adjust(bottom=.3,top=.77,wspace=.3);fig.suptitle('Physical derivative: two independent finite-difference steps',fontsize=20,x=.06,ha='left')
for ei,epsilon in enumerate(report['epsilons']):
 for key,linestyle in [('transition','-'),('nq','--'),('nv',':')]:
  ax[0].plot(range(len(positive)),[max(x['epsilons'][ei][key]['max_gate_ratio'],1e-12) for x in positive],label=f'{key}, ε={epsilon:g}',linestyle=linestyle,marker='.')
 ax[0].plot(range(len(positive)),[max(max(m['max_gate_ratio'] for m in x['epsilons'][ei]['mass_q']),1e-12) for x in positive],label=f'∂M, ε={epsilon:g}',linestyle='-.',marker='.')
ax[0].axhline(1,color='black',linewidth=1);ax[0].set(yscale='log',xlabel='predeclared supported case index',ylabel='max |error| / (5e-7 + 5e-6 |analytic|)',title='All 21 columns; zero display floor 1e-12',ylim=(5e-13,2));ax[0].legend(fontsize=7,ncol=2,loc='lower left',bbox_to_anchor=(0,1.14));ax[0].grid(alpha=.2)
labels=['supported\nphysical\nJacobians','threshold\nJacobian\nunsupported','invalid value\ninputs\nrejected','synthetic output\ncorruptions\nrejected'];counts=[len(positive),len(threshold),len(invalid),len(report['synthetic_output_gates']['negative_controls'])];bars=ax[1].bar(labels,counts,color=['#447799','#888888','#bb6644','#8866aa']);ax[1].bar_label(bars);ax[1].set(ylabel='case count',ylim=(0,max(counts)+5),title='Value success and derivative support are distinct');ax[1].tick_params(axis='x',labelsize=8)
fig.text(.06,.09,'Both ε=1e-6 and 3e-7 are reported without selecting the better result. Differences use the original frozen C++ v2 value probe.\nNq / Nv / ∂M are checked from independent base bias/mass outputs as well as the final transition Jacobian.\nAnalytic SDK reference, selected stable branches; no fitting, new plant or runtime / task / Phase5 acceptance.',fontsize=10)
p=DEST/'phase5_public_coupled_derivative_cpp_verification.png';fig.savefig(p,dpi=160);plt.close(fig);paths.append(p)
for p in paths:
 d=dict(figure_sha256=sha(p),script_sha256=sha(__file__),report_sha256=sha(BASE/'parity-attempt1/report.json'),native_output_sha256=sha(BASE/'parity-attempt1/analytic.json'),input_sha256=sha(BASE/'inputs/cases.json'),freeze_sha256=sha(BASE/'frozen_before_predictions.json'),units='Jacobian panel units by block; normalized verification ratio dimensionless; epsilon pertains q(rad),v(rad/s),C(rad).',data_source='Actual frozen analytic native outputs and original-base central finite differences; all21columns at both predeclared epsilon values.',scope='Bounded physical2ms derivative development reference. Phase5 NOT_ACCEPTED; no timing/controller/task ranking.',verification_zero_floor=1e-12 if 'verification' in p.name else None)
 p.with_suffix('.json').write_text(json.dumps(d,indent=2)+'\n');print(str(p),sha(p))
