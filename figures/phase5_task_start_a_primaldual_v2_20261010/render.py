"""Plot retained native solved-but-refused data, without running any model."""
from pathlib import Path
import collections,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REVIEW=ROOT/'reviews/evidence/phase5_task_start_a_primaldual_v2_20261010/independent'
sha=lambda b:hashlib.sha256(b).hexdigest()
b=(REVIEW/'READY.json').read_bytes()
assert sha(b)=='fb182a1c80ff780898f11214ed78b41f39a5f5fb2d2070dbb3ee389b63ac6f6a'
r=json.loads(b);db=(REVIEW/'results.json').read_bytes();pin=r['files']['results.json']
assert len(db)==pin['bytes'] and sha(db)==pin['sha256']
d=json.loads(db);n=d['native_result'];si=d['full_original_SI'];h=d['strict_history']
assert n['raw_status']==1 and n['iterations']==1 and si['gate1e_7_pass']
assert not n['request_authorized'] and n['request']==0 and d['task_commits']==0
counts=collections.Counter(x['kind'] for x in h['all_failures'])
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(1,3,figsize=(15,5),layout='constrained')
vals=[n['setup']*1000,n['solve']*1000]
ax[0].bar(['Native setup','Native solve'],vals,color=['#306989','#348975'])
for i,v in enumerate(vals):ax[0].annotate(f'{v:.3f} ms',(i,v),xytext=(0,6),textcoords='offset points',ha='center')
ax[0].set(title='SOLVED · one iteration · polished',ylabel='Recorded native subset time (ms)',ylim=(0,max(vals)*1.2))
ax[1].bar(['Recorded scan','Independent scan'],[si['recorded_max'],si['independent_max']],color='#348975')
ax[1].set_yscale('log');ax[1].set_ylim(1e-16,1e-6)
ax[1].axhline(1e-7,color='#555',ls='--',label='Original SI gate: 1e-7')
ax[1].legend(fontsize=9)
ax[1].set(title='All 13,156 original rows pass',ylabel='Maximum original-unit violation\n(worst row: feedback jerk, 1/s³)')
ax[1].text(.5,.58,f"Maximum {si['independent_max']:.3g}",transform=ax[1].transAxes,ha='center')
labels=[k.replace('_',' ') for k in counts];values=list(counts.values())
ax[2].barh(labels,values,color='#ae5146')
for i,v in enumerate(values):ax[2].text(v+.6,i,str(v),va='center')
ax[2].set(title='Strict history refuses candidate',xlabel='Failing checks in 200-cycle forensic replay',xlim=(0,max(values)*1.22))
for a in ax:a.grid(axis='y',alpha=.15)
fig.suptitle('Actual task-start QP: numerical solve closed; executable candidate still refused',fontsize=15)
fig.supxlabel('First progress jerk = 5.000000000000001 > strict cap 5. No tolerance change or clamp.\nForensic preview only; no nonlinear B, forward request, task commit or online 4 ms claim. Phase 5 NOT_ACCEPTED.',fontsize=10)
for suffix in ['png','svg']:fig.savefig(OUT/('diagnostics.'+suffix),dpi=170,bbox_inches='tight')
p={'schema':'A5_SOLVED_STRICT_REFUSED_DIAGNOSTIC_FIGURE_V1','review_ready_sha256':sha(b),'review_results_sha256':sha(db),'renderer_sha256':sha(Path(__file__).read_bytes()),'scope':'Actual saved-file native/SI/strict-history diagnostics. No executed trajectory, full task, matched method ranking or complete-cycle latency.','data':{'native_ms':vals,'full_original_SI':si,'first_strict_failure':h['first_failure'],'strict_failure_counts':dict(counts)},'files':{x.name:{'bytes':x.stat().st_size,'sha256':sha(x.read_bytes())} for x in sorted(OUT.iterdir()) if x.suffix in ['.png','.svg']},'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'}
(OUT/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
