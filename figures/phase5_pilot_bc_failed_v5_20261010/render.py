from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parents[2]/"reviews/evidence/phase5_pilot_bc_failed_v5_20261010"
out=Path(__file__).resolve().parent
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
names=['ACTUAL_CANDIDATE_VALIDATION.json','FAILURE_BRANCH_NEIGHBORHOOD.json'];before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}
assert before=={'ACTUAL_CANDIDATE_VALIDATION.json':'143b0adcef2fc9fd01f7221b3f0e85402a86e491b73de1ee544e6a02c0593452','FAILURE_BRANCH_NEIGHBORHOOD.json':'8d3476d80d831dadc42d31d32932f94b050bdd99371ed22cbde3831834d478ba'}
a=json.loads((p/names[0]).read_text());b=json.loads((p/names[1]).read_text());rows=a['points'];done=[r for r in rows if r['complete']];assert len(rows)==53 and len(done)==52 and not a['passed'];fail=rows[-1]
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
fig,ax=plt.subplots(3,1,figsize=(12,9));fig.suptitle('Phase 5 development: retained candidate validation refusal',fontsize=18,x=.07,ha='left')
ax[0].semilogy([r['elapsed'] for r in rows],[max(r['affine_error'],1e-16) for r in rows],color='#006f89',label='Genuine value vs original affine map, max |error|');ax[0].axhline(1e-6,color='#b23a38',ls='--',label='Unchanged 1e-6 gate');ax[0].scatter([fail['elapsed']],[fail['affine_error']],color='#b23a38',s=55,zorder=4);ax[0].set_ylabel('Mixed state component error');ax[0].legend(loc='upper left');ax[0].set_xlim(0,.115)
ax[1].plot([r['elapsed'] for r in done],[r['min_true']*1000 for r in done],label='Full true geometry',color='#006f89');ax[1].plot([r['elapsed'] for r in done],[r['min_cover']*1000 for r in done],label='Full cover geometry',color='#568d39');ax[1].axhline(5,color='#b23a38',ls='--',label='5 mm floor');ax[1].set_ylabel('Predicted clearance (mm)');ax[1].set_xlim(0,.115);ax[1].legend(loc='lower left');ax[1].text(.012,.86,'52 checked points; failed point geometry not queried',transform=ax[1].transAxes,fontsize=10)
near=b['rows'];ax[2].step([r['elapsed'] for r in near],[r['nominal_friction_branches'][5] for r in near],where='mid',color='#999999',label='Zero-input nominal, joint 6');ax[2].step([r['elapsed'] for r in near],[r['candidate_friction_branches'][5] for r in near],where='mid',color='#b23a38',label='Candidate value, joint 6');ax[2].set_ylim(-1.3,.3);ax[2].set_yticks([-1,0],['Lower bound','Interior']);ax[2].set_ylabel('Friction branch');ax[2].set_xlabel('Prediction horizon time (s), fixed 2 ms samples');ax[2].set_xlim(.094,.115);ax[2].legend(loc='lower left',fontsize=10)
for aaxis in ax:aaxis.axvline(.106,color='#b23a38',ls=':',alpha=.7)
fig.text(.07,.055,'Seed 91011 | all progress inputs zero | Model value: 400 substeps returned | validation refused at 0.106 s',fontsize=11)
fig.text(.07,.031,'Control commits: 0. Plots show development predictions and retained refusal; no accepted task or physical performance claim.',fontsize=10)
fig.subplots_adjust(top=.91,bottom=.13,left=.11,right=.97,hspace=.32)
for ext in ['png','svg']:fig.savefig(out/('candidate_validation_refusal_root.'+ext),dpi=160)
plt.close(fig)
after={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};assert before==after
outputs={n:{'bytes':(out/n).stat().st_size,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in ['candidate_validation_refusal_root.png','candidate_validation_refusal_root.svg']};(out/'ROOT_REPRODUCTION_PROVENANCE.json').write_text(json.dumps({'schema':'PILOT_BC_FAILURE_PREDICTION_PLOT_V5','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'actual_scope':'B predicted values, first failure retained; 0 taskstep/commit; phase5 NOT_ACCEPTED','Model_or_MuJoCo_native_entries':0},indent=2)+'\n')
print(json.dumps(outputs))
