from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path(__file__).resolve().parent
data=p.parents[1]/'reviews/evidence/phase5_geometry_qp_actual_v2_20261011/plot-inputs'
expected={'cycle-0-commit.json': 'cfd8f423b491ab93638ac11cb24bd23a37de954c8ab0c950d9401fb69e48ebdf', 'cycle-2-value.json': '45192222a76f00deeda55bb9bed67eed793b260b7ead891470dfb3cf717dedbf', 'cycle-0-value.json': '40057fe962651c18a3efe016a4098e5143bc9706c31263035fd5a1a8484b6c54', 'cycle-2-validation.json': 'b4cc6b5580b16bb91350b6df48e37240cb01dafd831e5ff2932157e54e8db8ea', 'ACTUAL_DYNAMIC_SUMMARY.json': '180a266b8d99a50f129ff8417d1de774476f5e8c77819efbe21b287620030902', 'cycle-0-validation.json': '8c26b93d5acb56585fee8c0ef02236c6a62f5560c091af5a86d2296de7e9f066', 'cycle-1-commit.json': '6327b9e86c10cf12bf53550b8e1d87935744d12d948860e3b4a5dd2a6fda9588', 'cycle-1-value.json': '734bbf0155d9bda8acc90222c07ff34fca09db92dd0a8fa2504dd47dec6579ce', 'cycle-2-commit.json': '4d4d6bbe82c8b2516cf47a5e94ff83065b9fc6046d1556931736575a6c0d6264', 'cycle-1-validation.json': '36921c9a067d0c9d7e927029695a80599d3fd7280d02084b781213fbe68c89dc'}
names=list(expected)
before={n:hashlib.sha256((data/n).read_bytes()).hexdigest() for n in names}
assert before==expected
summary=json.loads((data/'ACTUAL_DYNAMIC_SUMMARY.json').read_text());cycles=summary['cycles'];assert len(cycles)==3 and summary['entry']['commits']==3
colors=['#006f89','#d47623','#684e91'];plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
fig,ax=plt.subplots(2,2,figsize=(14,9.5));fig.suptitle('Phase 5 development: three current geometry-QP transactions',fontsize=19,x=.07,ha='left');actual_t=[];actual_v=[];predicted_t=[];predicted_v=[]
for k,color in enumerate(colors):
 a,v,c=[json.loads((data/f'cycle-{k}-{n}.json').read_text()) for n in ['validation','value','commit']];rows=a['points'];assert a['passed'] and len(rows)==400 and all(z['complete'] for z in rows) and c['success'] and len(c['points'])==2
 t=[z['elapsed'] for z in rows];ax[0,0].semilogy(t,[max(z['affine_error'],1e-16) for z in rows],color=color,label=f'Cycle {k+1}, current rebuilt');ax[0,1].plot(t,[z['min_true']*1000 for z in rows],color=color,label=f'Cycle {k+1}: true');ax[0,1].plot(t,[z['min_cover']*1000 for z in rows],color=color,ls='--',label=f'Cycle {k+1}: cover')
 if k==0:actual_t.append(0);actual_v.append(v['actual_initial']['v'][1]*1e6);predicted_t.append(0);predicted_v.append(v['actual_initial']['v'][1]*1e6)
 for j,z in enumerate(c['points']):actual_t.append((4*k+2*(j+1)));actual_v.append(z['v'][1]*1e6);predicted_t.append(4*k+2*(j+1));predicted_v.append(v['substeps'][j]['v'][1]*1e6)
ax[0,0].axhline(1e-6,color='#b23a38',ls='--',label='Original 1e-6 gate');ax[0,0].set_ylim(1e-16,1e-5);ax[0,0].set_ylabel('Mixed state component max error');ax[0,0].set_title('B: 400 genuine predicted samples per cycle',loc='left');ax[0,0].legend(loc='lower right',fontsize=8)
ax[0,1].axhline(5,color='#b23a38',ls=':',label='Original 5 mm floor');ax[0,1].set_ylim(4,25);ax[0,1].set_ylabel('Predicted full-query clearance (mm)');ax[0,1].set_title('B: unchanged true / cover geometry checks',loc='left');ax[0,1].legend(loc='lower right',fontsize=8,ncol=2)
for axis in ax[0]:axis.set_xlabel('Each fresh prediction horizon (s)');axis.set_xlim(0,.8)
ax[1,0].plot(predicted_t,predicted_v,color='#006f89',lw=2,label='Current candidate: first two samples');ax[1,0].scatter(actual_t,actual_v,color='#b23a38',s=34,label='Actual independent observation',zorder=3);ax[1,0].set_title('C: six real 2 ms steps, one retained session',loc='left');ax[1,0].set_xlabel('Actual task time (ms)');ax[1,0].set_ylabel('Joint 2 velocity (microrad/s)');ax[1,0].set_xticks([0,2,4,6,8,10,12]);ax[1,0].set_xlim(-.25,12.25);ax[1,0].legend(loc='lower left',fontsize=8)
for x in [4,8]:ax[1,0].axvline(x,color='#999999',lw=1,ls=':')
segments=['Observe','Nominal + maps','Geometry / QP assembly','Hint + solve','Value + B','C + journal'];palette=['#999999','#54878e','#749e62','#dc9b54','#9274a5','#5b7275'];left=np.zeros(3)
for i,label in enumerate(segments):
 vals=np.array([c['timing']['segments'][i]['seconds'] for c in cycles]);ax[1,1].barh([1,2,3],vals,left=left,label=label,color=palette[i]);left+=vals
walls=np.array([c['timing']['complete_cycle_seconds'] for c in cycles]);ax[1,1].barh([1,2,3],walls-left,left=left,color='#dddddd',label='Reobserve / control shift');ax[1,1].axvline(.004,color='#b23a38',ls='--',lw=1.5);ax[1,1].text(.035,.91,'4 ms deadline missed: 3 / 3',transform=ax[1,1].transAxes,color='#b23a38',fontsize=10)
for j,w in enumerate(walls):ax[1,1].text(w+.04,j+1,f'{w:.3f} s',va='center',fontsize=9)
ax[1,1].set_yticks([1,2,3],['Cycle 1','Cycle 2','Cycle 3']);ax[1,1].invert_yaxis();ax[1,1].set_xlabel('Actual offline cycle wall (s), including stage evidence');ax[1,1].set_xlim(0,6.2);ax[1,1].set_title('True wall time: no real-time performance claim',loc='left');ax[1,1].legend(loc='upper left',bbox_to_anchor=(0,-.19),fontsize=7,ncol=3)
fig.text(.07,.064,'Seed 91011 | beta = 0 | alpha optimizer cap 0.000999 rad/s2 | 3 commits / 6 actual task substeps / task progress 0',fontsize=11)
fig.text(.07,.034,'Restricted stabilization diagnostic. 1600 geometric QP rows per cycle; full nonlinear B/C checked. No full-task, stop, hardware or phase acceptance.',fontsize=10)
fig.subplots_adjust(top=.89,bottom=.22,left=.075,right=.97,hspace=.38,wspace=.28)
for ext in ['png','svg']:fig.savefig(p/('three_current_geometry_qp_transactions_root.'+ext),dpi=160)
plt.close(fig);after={n:hashlib.sha256((data/n).read_bytes()).hexdigest() for n in names};assert before==after
outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in ['three_current_geometry_qp_transactions_root.png','three_current_geometry_qp_transactions_root.svg']}
(p/'ROOT_REPRODUCTION_PROVENANCE.json').write_text(json.dumps({'schema':'ROOT_ACTUAL_GEOMETRY_QP_PLOT_REPRODUCTION_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'Pinned complete3cycles/all1200predictedpoints/all6actualsteps/all3walls; plotting only, no Model/Scene/native call; not taskprogress/stop/phase acceptance.'},indent=2)+'\n')
print(json.dumps(outputs))
