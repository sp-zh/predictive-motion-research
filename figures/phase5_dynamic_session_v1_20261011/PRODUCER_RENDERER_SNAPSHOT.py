from pathlib import Path
import json,hashlib,os,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40)
p=Path(__file__).parent;os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache');os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
names=['ACTUAL_DYNAMIC_SUMMARY.json']+[f'cycle-{k}-{n}.json' for k in range(3) for n in ['validation','value','commit']];before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};summary=json.loads((p/names[0]).read_text());cycles=summary['cycles'];assert len(cycles)==3 and summary['entry']['commits']==3
colors=['#006f89','#d47623','#684e91'];plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
fig,ax=plt.subplots(2,2,figsize=(14,9.5));fig.suptitle('Phase 5 development: three reobserved transactions',fontsize=19,x=.07,ha='left');actual_t=[];actual_v=[];predicted_t=[];predicted_v=[]
for k,color in enumerate(colors):
 a,v,c=[json.loads((p/f'cycle-{k}-{n}.json').read_text()) for n in ['validation','value','commit']];rows=a['points'];assert a['passed'] and len(rows)==400 and all(z['complete'] for z in rows) and c['success'] and len(c['points'])==2
 t=[z['elapsed'] for z in rows];ax[0,0].semilogy(t,[max(z['affine_error'],1e-16) for z in rows],color=color,label=f'Cycle {k+1}, current rebuilt');ax[0,1].plot(t,[z['min_true']*1000 for z in rows],color=color,label=f'Cycle {k+1}: true');ax[0,1].plot(t,[z['min_cover']*1000 for z in rows],color=color,ls='--',label=f'Cycle {k+1}: cover')
 if k==0:actual_t.append(0);actual_v.append(v['actual_initial']['v'][1]*1e6);predicted_t.append(0);predicted_v.append(v['actual_initial']['v'][1]*1e6)
 for j,z in enumerate(c['points']):actual_t.append((4*k+2*(j+1)));actual_v.append(z['v'][1]*1e6);predicted_t.append(4*k+2*(j+1));predicted_v.append(v['substeps'][j]['v'][1]*1e6)
ax[0,0].axhline(1e-6,color='#b23a38',ls='--',label='Original 1e-6 gate');ax[0,0].set_ylim(1e-16,1e-5);ax[0,0].set_ylabel('Mixed state component max error');ax[0,0].set_title('B: 400 genuine predicted samples per cycle',loc='left');ax[0,0].legend(loc='lower right',fontsize=8)
ax[0,1].axhline(5,color='#b23a38',ls=':',label='Original 5 mm floor');ax[0,1].set_ylim(4,25);ax[0,1].set_ylabel('Predicted full-query clearance (mm)');ax[0,1].set_title('B: unchanged true / cover geometry checks',loc='left');ax[0,1].legend(loc='lower right',fontsize=8,ncol=2)
for axis in ax[0]:axis.set_xlabel('Each fresh prediction horizon (s)');axis.set_xlim(0,.8)
ax[1,0].plot(predicted_t,predicted_v,color='#006f89',lw=2,label='Current candidate: first two samples');ax[1,0].scatter(actual_t,actual_v,color='#b23a38',s=34,label='Actual independent observation',zorder=3);ax[1,0].set_title('C: six real 2 ms steps, one retained session',loc='left');ax[1,0].set_xlabel('Actual task time (ms)');ax[1,0].set_ylabel('Joint 2 velocity (microrad/s)');ax[1,0].set_xticks([0,2,4,6,8,10,12]);ax[1,0].set_xlim(-.25,12.25);ax[1,0].legend(loc='lower left',fontsize=8)
for x in [4,8]:ax[1,0].axvline(x,color='#999999',lw=1,ls=':')
segments=['Observe','Nominal + maps','Affine / QP assembly','Hint + solve','Value + B','C + journal'];palette=['#999999','#54878e','#749e62','#dc9b54','#9274a5','#5b7275'];left=np.zeros(3)
for i,label in enumerate(segments):
 vals=np.array([c['timing']['segments'][i]['seconds'] for c in cycles]);ax[1,1].barh([1,2,3],vals,left=left,label=label,color=palette[i]);left+=vals
walls=np.array([c['timing']['complete_cycle_seconds'] for c in cycles]);ax[1,1].barh([1,2,3],walls-left,left=left,color='#dddddd',label='Reobserve / control shift');ax[1,1].axvline(.004,color='#b23a38',ls='--',lw=1.5);ax[1,1].text(.035,.91,'4 ms deadline missed: 3 / 3',transform=ax[1,1].transAxes,color='#b23a38',fontsize=10)
for j,w in enumerate(walls):ax[1,1].text(w+.04,j+1,f'{w:.3f} s',va='center',fontsize=9)
ax[1,1].set_yticks([1,2,3],['Cycle 1','Cycle 2','Cycle 3']);ax[1,1].invert_yaxis();ax[1,1].set_xlabel('Actual offline cycle wall (s), including stage evidence');ax[1,1].set_xlim(0,3.6);ax[1,1].set_title('True wall time: no real-time performance claim',loc='left');ax[1,1].legend(loc='upper left',bbox_to_anchor=(0,-.19),fontsize=7,ncol=3)
fig.text(.07,.064,'Seed 91011 | beta = 0 | alpha optimizer cap 0.000999 rad/s2 | 3 commits / 6 actual task substeps / task progress 0',fontsize=11)
fig.text(.07,.034,'Restricted stabilization diagnostic. Geometric QP rows empty; full nonlinear B/C checked. No full-task, stop, hardware or phase acceptance.',fontsize=10)
fig.subplots_adjust(top=.89,bottom=.22,left=.075,right=.97,hspace=.38,wspace=.28)
for ext in ['png','svg']:fig.savefig(p/('three_reobserved_transactions.'+ext),dpi=160)
plt.close(fig);after={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};assert before==after
outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in ['three_reobserved_transactions.png','three_reobserved_transactions.svg']};(p/'PLOT_PROVENANCE.json').write_text(json.dumps({'schema':'DYNAMIC_THREE_CYCLE_ACTUAL_PLOT_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'All3 currentpredictions400 each, all6 actual tasksteps, all3 offlinewalls. No selected cases/fulltask claims','new_Model_or_MuJoCo_entries':0,'timing_exclusions':'SDKstartup/term; cycle timing serialization/manifest; wallincludes stageevidence andafterobserve/shift'},indent=2)+'\n');print(json.dumps(outputs))
