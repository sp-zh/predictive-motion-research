from pathlib import Path
import os,resource,signal,json,hashlib
resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(40);p=Path(__file__).parent;os.environ['MPLCONFIGDIR']='/private/tmp/phase5-foundation-figure-mpl-cache-v2'
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=json.loads((p/'data.json').read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.grid':True,'grid.alpha':.2,'axes.spines.right':False,'axes.spines.top':False});fig,ax=plt.subplots(1,2,figsize=(13,5.5),constrained_layout=True);fig.suptitle('Attempt 42: three fresh proposals refused at boundary 5',fontsize=16)
for k,a in enumerate(z for z in D['trials'] if not z['passed']):
 z=a['points'];ax[0].plot([1000*r['elapsed'] for r in z],[r['affine'] for r in z],label='Trial '+str(k));ax[0].scatter([1000*z[-1]['elapsed']],[z[-1]['affine']])
ax[0].axhline(1e-6,color='#a92222',ls='--',label='Original 1e-6 gate');ax[0].set_yscale('log');ax[0].set(xlabel='Candidate forecast elapsed (ms)',ylabel='Max packed-state affine discrepancy',title='Fixed planning margin did not close the mismatch');ax[0].legend()
W=D['whole'];ax[1].bar([r['cycle'] for r in W],[r['wall'] for r in W],color=['#2374ab' if r['physical_complete'] else '#a92222' for r in W]);ax[1].set(xlabel='Actual boundary index',ylabel='Whole cycle wall time (s)',title='Five physical commits; failed boundary includes all trials');ax[1].annotate('3 trials, no sixth C',(5,W[-1]['wall']),xytext=(-125,5),textcoords='offset points');ax[1].axhline(.004,color='#222222',ls=':',label='4ms diagnostic threshold');ax[1].legend()
fig.text(.5,-.025,'Actual commits: 5 / 10 physical 2ms halves. All cycles missed 4ms. Rejected proposals were not executed. Phase5 NOT_ACCEPTED.',ha='center',fontsize=9);q=p/'scp_fixed_margin_failure42.png';fig.savefig(q,dpi=160,bbox_inches='tight');plt.close(fig);print(json.dumps({'name':q.name,'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'matplotlib_version':matplotlib.__version__}))
