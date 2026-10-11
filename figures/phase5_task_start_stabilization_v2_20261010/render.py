"""Render actual saved A7 planned command history; no Model or execution."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
REVIEW=ROOT/'reviews/evidence/phase5_task_start_stabilization_v2_20261010'
sha=lambda b:hashlib.sha256(b).hexdigest()
rb=(REVIEW/'PRODUCER_READY.json').read_bytes();assert sha(rb)=='5146ccede2eef1edeac17d1b7c3674675a2c3065633cafa0ca349497b7667294'
r=json.loads(rb);b=(REVIEW/'ACTUAL_SOLVER_SUMMARY.json').read_bytes();pin=r['files']['ACTUAL_SOLVER_SUMMARY.json'];assert len(b)==pin['bytes'] and sha(b)==pin['sha256']
d=json.loads(b);req=d['forward_request'];u=np.array(req['controls']);initial=np.array(req['state30']);cycles=req['cycles']
assert u.shape==(20,8) and np.array_equal(u.reshape(160),d['control_vector'])
assert np.all(u[:,7]==0) and np.all(initial[21:30]==0) and sum(cycles)==200
assert d['raw_status']==1 and d['forward_request_exists']==1 and d['execution_permission']==0
assert len(d['original_row_violations'])==13156 and max(d['original_row_violations'])<=1e-7
w=[0.]*7;C=initial[14:21].tolist();s=0.;progress_rate=0.;history=[];command_alpha=[];times=[0.];vel=[w.copy()]
for k in range(20):
 for tick in range(cycles[k]):
  for j in range(7):
   w[j]+=.004*float(u[k,j]);C[j]+=.004*w[j]
  progress_rate+=.004*float(u[k,7]);s+=.004*progress_rate
  history.append([s,progress_rate,float(u[k,7])]);times.append(.004*len(history));vel.append(w.copy());command_alpha.append(u[k,:7])
assert all(x==0 for row in history for x in row)
t=np.array(times);vel=np.array(vel);alpha=np.array(command_alpha)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(1,3,figsize=(15,5),layout='constrained')
colors=plt.cm.tab10(np.arange(7))
for j in range(7):
 ax[0].step(t[:-1],alpha[:,j],where='post',color=colors[j],label=f'Joint {j+1}')
 ax[1].plot(t,vel[:,j],color=colors[j])
ax[0].set(title='Planned command acceleration α',xlabel='Future plan time (s)',ylabel='rad/s²')
ax[0].legend(ncol=2,fontsize=8)
ax[1].set(title='Reconstructed command speed w',xlabel='Future plan time (s)',ylabel='rad/s')
ax[2].plot(t,np.zeros_like(t),color='#348975',lw=2)
ax[2].set(title='All progress inputs fixed to zero',xlabel='Future plan time (s)',ylabel='s, r and b (all zero)',ylim=(-.01,.01))
ax[2].text(.5,.7,'SOLVED · one iteration\n13,156 original SI rows pass\nStrict command/progress history passes',transform=ax[2].transAxes,ha='center',fontsize=10)
ax[2].text(.5,.18,'Data-only forward request\nNo nonlinear B or physical C commit',transform=ax[2].transAxes,ha='center',color='#a4493f',fontsize=10)
for a in ax:a.grid(alpha=.18)
fig.suptitle('Actual A7 stabilization component: candidate passes linear/history gates; zero progress',fontsize=15)
fig.supxlabel('Saved QP controls and exact 4 ms command recurrence; these curves are plans, not measured robot motion.\nCommand terminal speed is near zero, not certified physical rest. No full-task success or online timing claim; Phase 5 NOT_ACCEPTED.',fontsize=10)
for suffix in ['png','svg']:fig.savefig(OUT/('planned_commands.'+suffix),dpi=170,bbox_inches='tight')
p={'schema':'A7_STABILIZATION_PLANNED_COMMAND_DIAGNOSTIC_V1','producer_ready_sha256':sha(rb),'actual_summary_sha256':sha(b),'renderer_sha256':sha(Path(__file__).read_bytes()),'scope':'Actual saved QP candidate planned command recurrence. Not physical motion/value validation/replay/full task/online performance. Restricted beta0 subspace does not prove unrestricted optimality.','data':{'cycles':cycles,'command_law':'w_next=w+.004*alpha; C_next=C+.004*w_next; held for two2ms steps only if subsequently validated','total_plan_seconds':t[-1],'max_absolute_planned_alpha':float(abs(alpha).max()),'max_absolute_planned_w':float(abs(vel).max()),'terminal_planned_w':vel[-1].tolist(),'progress_all_exact_zero':True,'native_setup_seconds':d['setup_seconds'],'native_solve_seconds':d['solve_seconds'],'original_rows':13156,'maximum_original_SI_violation':max(d['original_row_violations']),'physical_commits':0},'files':{x.name:{'bytes':x.stat().st_size,'sha256':sha(x.read_bytes())} for x in sorted(OUT.iterdir()) if x.suffix in ['.png','.svg']},'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'}
(OUT/'provenance.json').write_text(json.dumps(p,indent=2)+'\n')
