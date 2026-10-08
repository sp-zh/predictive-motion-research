#!/usr/bin/env python3
"""Actual component Jacobians and separately reported fixed-epsilon checks."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-sensitivity-cpp-v1';DEST=ROOT/'figures/phase5';DEST.mkdir(exist_ok=True,parents=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_BOUNDED_AUGMENTED_CYCLE_CELL_SENSITIVITIES_ONLY'
analytic=json.loads((BASE/'parity-attempt1/analytic.json').read_text());answer=next(x for x in analytic['cases'] if x['name']=='nonuniform_mixed');m=answer['cell_maps'][-1];A=np.asarray(m['A']);B=np.asarray(m['B']);positive=[x for x in report['records'] if x['sensitivity_success']];threshold=[x for x in report['records'] if x['value_success'] and not x['sensitivity_success']];invalid=[x for x in report['records'] if not x['value_success']]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'#f7f8fc','axes.facecolor':'white','savefig.facecolor':'#f7f8fc'})
provenance=dict(source='Actual frozen C++ cell-local output / fixed-epsilon QA report',script_sha256=sha(__file__),report_sha256=sha(BASE/'parity-attempt1/report.json'),analytic_sha256=sha(BASE/'parity-attempt1/analytic.json'),inputs_sha256=sha(BASE/'inputs/cases.json'),freeze_sha256=report['freeze_sha256'],binary_sha256=report['binary_sha256'],phase5='NOT_ACCEPTED',new_plant=False,acceptance='Selected numerical components only; common task start s=0/r=0 unsupported; no controller/task/timing acceptance.')
def save(fig,stem,data):
 p=DEST/('phase5_public_coupled_augmented_sensitivity_'+stem+'.png');fig.savefig(p,dpi=180);plt.close(fig);meta={**provenance,**data,'figure_sha256':sha(p),'figure_bytes':p.stat().st_size};p.with_suffix('.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n');print(stem,sha(p))
fig=plt.figure(figsize=(14,8.5));gs=fig.add_gridspec(1,2,width_ratios=[3.5,1.45],left=.065,right=.88,bottom=.20,top=.84,wspace=.32);axes=[fig.add_subplot(gs[0,j]) for j in range(2)];norm=SymLogNorm(linthresh=1e-7,linscale=.5,vmin=-max(abs(A).max(),abs(B).max()),vmax=max(abs(A).max(),abs(B).max()),base=10)
for ax,values,title in zip(axes,(A,B),('A: 30 state directions','B: 8 held input directions')):
 im=ax.imshow(values,cmap='RdBu_r',norm=norm,aspect='auto',interpolation='nearest');ax.set_title(title,pad=10);ax.set_yticks([3,10,17,24,28,29],['q⁺ [rad]','v⁺ [rad/s]','C⁺ [rad]','w⁺ [rad/s]','s⁺ [1]','r⁺ [1/s]']);ax.tick_params(length=0)
 for y in [6.5,13.5,20.5,27.5]:ax.axhline(y,color='#5c647a',lw=.6)
axes[0].set_xticks([3,10,17,24,28,29],['q','v','C','w','s','r']);axes[1].set_xticks([3,7],['α [rad/s²]','b [1/s²]'])
for x in [6.5,13.5,20.5,27.5]:axes[0].axvline(x,color='#5c647a',lw=.6)
axes[1].axvline(6.5,color='#5c647a',lw=.6)
cax=fig.add_axes([.915,.24,.016,.56]);fig.colorbar(im,cax=cax,label='Signed coefficient (mixed units, symlog)')
fig.suptitle('Augmented cell sensitivity from actual recorded numerical output',x=.065,y=.95,ha='left',fontsize=18,fontweight='bold');fig.text(.065,.89,'Nonuniform mesh [1, 3, 2, 4] · last cell = 4 cycles / 16 ms · matched nonlinear cell origin',fontsize=11)
fig.text(.065,.13,'State order: q₇, v₇, C₇, w₇, s, r. Each A entry has output-unit / input-unit; B uses α or b units.',fontsize=10)
fig.text(.065,.095,'Commands are latched for both 2 ms halves. Tiny α → physical terms retain h²Q; progress follows exact polynomials.',fontsize=10)
fig.text(.065,.048,'DEVELOPMENT COMPONENT ONLY · Phase5 unaccepted · s=0 / r=0 task starts outside this central-domain API',fontsize=10,color='#9b3840')
save(fig,'matrix',dict(case=answer['name'],cell=m['cell'],cycles=m['cycle'],A=A.tolist(),B=B.tolist(),state_units=['rad']*7+['rad/s']*7+['rad']*7+['rad/s']*7+['1','1/s'],input_units=['rad/s^2']*7+['1/s^2'],plot_scale='Signed symlog linthresh1e-7; zero remains zero. Mixed coefficient units explicitly labeled.'))
fig=plt.figure(figsize=(14,8));gs=fig.add_gridspec(1,2,width_ratios=[3.2,1.2],left=.075,right=.95,bottom=.27,top=.81,wspace=.30);ax=fig.add_subplot(gs[0,0]);counts=fig.add_subplot(gs[0,1]);xs=np.arange(len(positive));width=.34;floor=1e-7
for ei,e in enumerate(report['epsilons']):
 vals=[x['epsilons'][ei]['max_gate_ratio'] for x in positive];ax.bar(xs+(ei-.5)*width,np.maximum(vals,floor),width,label=f'ε = {e:g}',color=['#2467af','#df9240'][ei])
ax.set_yscale('log');ax.set_ylim(floor/2,2);ax.axhline(1,color='#9b3840',lw=1.5,ls='--');ax.text(-.5,1.2,'declared per-entry limit = 1',color='#9b3840');ax.set_ylabel('Worst normalized gate ratio across all endpoints / 38 directions');ax.set_xticks(xs,['All-free\n1 cycle','Held\n10 cycles','Split\n4 cells','Nonuniform\n4 cells','Force\nsaturation','Seen91013\nhistory']);ax.legend(loc='upper right');ax.grid(axis='y',alpha=.15)
nums=[len(positive),len(threshold),len(invalid)];counts.barh([2,1,0],nums,color=['#2467af','#df9240','#9b3840']);counts.set_yticks([2,1,0],['Certified','Value only','Forward failed']);counts.set_xlim(0,max(nums)+3);counts.set_title('Full predeclared roster')
for y,n in zip([2,1,0],nums):counts.text(n+.2,y,str(n),va='center')
fig.suptitle('Independent finite differences against frozen original forward values',x=.075,y=.95,ha='left',fontsize=18,fontweight='bold');fig.text(.075,.88,f'{report["fd_augmented_cases"]} original augmented calls · {report["fd_original_physical_diagnostics"]} original physical diagnostics · both ε retained',fontsize=11)
fig.text(.075,.17,'Gate: |error| ≤ 5e−7 + 5e−6 |analytic| per entry, separately for each ε; same strict branches at every perturbation.',fontsize=10)
fig.text(.075,.125,'Command/progress rational coefficients, independent J₁/J₂, h²Q and every halfstep semiimplicit q identity also pass.',fontsize=10)
fig.text(.075,.078,'Zero ratios would be displayed at 1e−7; actual values and units are retained in provenance. No favorable-step selection.',fontsize=10)
fig.text(.075,.03,'DEVELOPMENT COMPONENT ONLY · Phase5 unaccepted · no main controller, plant rerun, task or real-time claim',fontsize=10,color='#9b3840')
save(fig,'verification',dict(epsilons=report['epsilons'],gate_absolute=report['absolute_per_entry'],gate_relative=report['relative_per_entry'],positive_records=positive,counts=dict(certified=len(positive),value_only=len(threshold),forward_failed=len(invalid),invalid_initial_parser=10,retained_future_failure=1),display_floor=floor,display_limits=[floor/2,2]))
