#!/usr/bin/env python3
"""Actual component Jacobians and separately reported fixed-epsilon checks."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
ROOT=Path('/home/codextransfer/predictive_motion');BASE=ROOT/'results/phase5/development/public-coupled-augmented-extension-cpp-v1';DEST=ROOT/'figures/phase5';DEST.mkdir(exist_ok=True,parents=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=json.loads((BASE/'parity-attempt1/report.json').read_text());assert report['status']=='PASS_SELECTED_COMMAND_PROGRESS_EXTENSION_JACOBIANS_ONLY'
analytic=json.loads((BASE/'parity-attempt1/analytic.json').read_text());answer=next(x for x in analytic['cases'] if x['name']=='start_s0_r0_zero');m=answer['cell_maps'][-1];A=np.asarray(m['A']);B=np.asarray(m['B']);positive=[x for x in report['records'] if x['extension_jacobian_success']];threshold=[x for x in report['records'] if x['value_success'] and not x['extension_jacobian_success']];invalid=[x for x in report['records'] if not x['value_success']]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':13,'axes.labelsize':10,'figure.facecolor':'#f7f8fc','axes.facecolor':'white','savefig.facecolor':'#f7f8fc'})
provenance=dict(source='Actual frozen composite extension C++ cell-local output / fixed-epsilon mathematical extension QA',script_sha256=sha(__file__),report_sha256=sha(BASE/'parity-attempt1/report.json'),analytic_sha256=sha(BASE/'parity-attempt1/analytic.json'),inputs_sha256=sha(BASE/'inputs/cases.json'),freeze_sha256=report['freeze_sha256'],binary_sha256=report['binary_sha256'],phase5='NOT_ACCEPTED',new_plant=False,root_review_status='Independent root first fixed-step branch-signature gate failed; diagnosis recorded and failure retained separately.',acceptance='Selected command/progress extension Jacobians, including nominal0/0; no admissible-neighborhood/direction, safety, main/controller/task/timing acceptance.')
def save(fig,stem,data):
 p=DEST/('phase5_public_coupled_augmented_extension_'+stem+'.png');fig.savefig(p,dpi=180);plt.close(fig);meta={**provenance,**data,'figure_sha256':sha(p),'figure_bytes':p.stat().st_size};p.with_suffix('.json').write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n');print(stem,sha(p))
fig=plt.figure(figsize=(14,8.5));gs=fig.add_gridspec(1,2,width_ratios=[3.5,1.45],left=.065,right=.88,bottom=.20,top=.84,wspace=.32);axes=[fig.add_subplot(gs[0,j]) for j in range(2)];norm=SymLogNorm(linthresh=1e-9,linscale=.5,vmin=-max(abs(A).max(),abs(B).max()),vmax=max(abs(A).max(),abs(B).max()),base=10)
for ax,values,title in zip(axes,(A,B),('A: 30 state directions','B: 8 held input directions')):
 im=ax.imshow(values,cmap='RdBu_r',norm=norm,aspect='auto',interpolation='nearest');ax.set_title(title,pad=10);ax.set_yticks([3,10,17,24,28,29],['q⁺ [rad]','v⁺ [rad/s]','C⁺ [rad]','w⁺ [rad/s]','s⁺ [1]','r⁺ [1/s]']);ax.tick_params(length=0)
 for y in [6.5,13.5,20.5,27.5]:ax.axhline(y,color='#5c647a',lw=.6)
axes[0].set_xticks([3,10,17,24,28,29],['q','v','C','w','s','r']);axes[1].set_xticks([3,7],['α [rad/s²]','b [1/s²]'])
for x in [6.5,13.5,20.5,27.5]:axes[0].axvline(x,color='#5c647a',lw=.6)
axes[1].axvline(6.5,color='#5c647a',lw=.6)
cax=fig.add_axes([.915,.24,.016,.56]);fig.colorbar(im,cax=cax,label='Signed coefficient (mixed units, symlog)')
fig.suptitle('Composite extension Jacobian at the declared s = 0, r = 0 nominal start',x=.065,y=.95,ha='left',fontsize=18,fontweight='bold');fig.text(.065,.89,'1 cycle / 4 ms · exact original closed-domain nominal value · full physical map remains nonlinear',fontsize=11)
fig.text(.065,.13,'State order: q₇, v₇, C₇, w₇, s, r. Each A entry has output-unit / input-unit; B uses α or b units.',fontsize=10)
fig.text(.065,.095,'Commands latch for both 2 ms halves; h²Q is retained. Only command/progress polynomials extend outside their bounds.',fontsize=10)
fig.text(.065,.048,'EXTENSION JACOBIAN ONLY · no admissible neighborhood or direction, continuation, safety or main-readiness certificate',fontsize=10,color='#9b3840')
save(fig,'matrix',dict(case=answer['name'],cell=m['cell'],cycles=m['cycle'],A=A.tolist(),B=B.tolist(),state_units=['rad']*7+['rad/s']*7+['rad']*7+['rad/s']*7+['1','1/s'],input_units=['rad/s^2']*7+['1/s^2'],plot_scale='Signed symlog linthresh1e-9; zero remains zero. Mixed coefficient units explicitly labeled.'))
fig=plt.figure(figsize=(14,11));gs=fig.add_gridspec(1,2,width_ratios=[3.2,1.15],left=.14,right=.95,bottom=.20,top=.84,wspace=.36);ax=fig.add_subplot(gs[0,0]);counts=fig.add_subplot(gs[0,1]);ys=np.arange(len(positive));height=.34;floor=1e-7
for ei,e in enumerate(report['epsilons']):
 vals=[x['epsilons'][ei]['max_gate_ratio'] for x in positive];ax.barh(ys+(ei-.5)*height,np.maximum(vals,floor),height,label=f'ε = {e:g}',color=['#2467af','#df9240'][ei])
labels=['Start 0/0 · zero inputs','Start 0/0 · 10 cycles','Terminal 1/0','Initial r upper','Initial s lower','Initial r lower','Initial w upper','Initial w lower','α upper','α lower','w upper · inward α','Generated w upper','Generated s upper','Generated r upper','Start 0/0 · nonuniform','Seen91013 history · 0/0','Old interior reference']
assert len(labels)==len(positive)
ax.set_yticks(ys,labels);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlim(floor/2,2);ax.axvline(1,color='#9b3840',lw=1.5,ls='--');ax.set_xlabel('Worst normalized gate ratio · all endpoints / 38 directions');ax.legend(loc='upper right',framealpha=1);ax.grid(axis='x',alpha=.15)
nums=[len(positive),len(threshold),len(invalid)];counts.barh([2,1,0],nums,color=['#2467af','#df9240','#9b3840']);counts.set_yticks([2,1,0],['Extension J','Value only','Forward failed']);counts.set_xlim(0,max(nums)+3);counts.set_title('Complete nominal roster')
for y,n in zip([2,1,0],nums):counts.text(n+.2,y,str(n),va='center')
fig.suptitle('Producer command/progress extension checks against frozen physical values',x=.055,y=.96,ha='left',fontsize=17,fontweight='bold');fig.text(.055,.875,'Producer fixtures shown. Independent root audit retains a branch-crossing failure; original full gate failed.',fontsize=10,color='#9b3840');fig.text(.055,.91,f'{report["extension_oracle_cases"]} extension value oracles · {report["original_physical_diagnostics"]} strict physical diagnostics · both ε retained',fontsize=11)
fig.text(.055,.14,'Gate: |error| ≤ 5e−7 + 5e−6 |analytic| separately at each ε; unchanged strict physical branches at every probe.',fontsize=10)
fig.text(.055,.10,'Exterior w / α / s / r probes are mathematical extensions only. Nominal values remain the original closed-domain rollout.',fontsize=10)
fig.text(.055,.065,'Zero ratios would display at 1e−7; limit = 1 (dashed). Raw coefficients, errors, units and all attempted cases are retained.',fontsize=10)
fig.text(.055,.03,'EXTENSION COMPONENT ONLY · no admissible-neighborhood / safety / main / task / timing claim · Phase5 unaccepted',fontsize=10,color='#9b3840')
save(fig,'verification',dict(epsilons=report['epsilons'],gate_absolute=report['absolute_per_entry'],gate_relative=report['relative_per_entry'],positive_records=positive,counts=dict(certified_extension=len(positive),value_only=len(threshold),forward_failed=len(invalid),invalid_nominal=6,retained_future_failures=2),exterior_nonphysical_case_count=report['exterior_nonphysical_case_count'],display_floor=floor,display_limits=[floor/2,2],certificate_name=report['certificate_name'],certifies_two_sided_admissible_neighborhood=False))
