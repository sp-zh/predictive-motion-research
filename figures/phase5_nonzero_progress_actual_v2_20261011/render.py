from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path(__file__).resolve().parent;d=json.loads((p/'plot-data.json').read_text());root=p.parents[1]
for n,e in d['source_files'].items():
 q=root/n;b=q.read_bytes();assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],n
assert len(d['actual_tcp'])==6 and len(d['logical_progress'])==3
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#242424','text.color':'#242424','svg.fonttype':'none'})
fig,axs=plt.subplots(2,2,figsize=(13.3,9.1));fig.subplots_adjust(left=.07,right=.98,bottom=.22,top=.87,wspace=.28,hspace=.48)
blue='#236586';orange='#b87728';gray='#c2c6c9';olive='#6d7541';ink='#343a40'
for ax in axs.flat:ax.set_axisbelow(True);ax.grid(axis='y',color='#e4e6e8',linewidth=.7)
ax=axs[0,0];x=[z['elapsed_ms'] for z in d['logical_progress']];y=[z['s']*1e6 for z in d['logical_progress']];ax.bar(x,y,width=1.8,color=blue);ax.set(xticks=x,ylim=(0,2.8),xlabel='Accepted command boundary (ms)',ylabel='Dimensionless progress s (×10⁻⁶)',title='Accepted logical progress: three boundaries')
for xx,yy in zip(x,y):ax.text(xx,yy+.08,f'{yy:.4f}',ha='center',fontsize=11)
ax=axs[0,1];x=np.arange(1,7);pos=np.array([z['translation_m']/.01*100 for z in d['actual_tcp']]);rot=np.array([z['SO3_rad']/.05*100 for z in d['actual_tcp']]);ax.bar(x-.17,pos,.32,color=blue,label='Position / 10 mm');ax.bar(x+.17,rot,.32,color='white',edgecolor=olive,hatch='//',label='SO3 angle / 0.05 rad');ax.axhline(100,color=ink,ls='--',lw=1.2);ax.set(xticks=x,ylim=(0,110),xlabel='Actual 2 ms substep',ylabel='Original error gate used (%)',title='Six actual TCP error checks');ax.legend(loc='upper left',bbox_to_anchor=(0,.83),frameon=False,fontsize=10);ax.text(5.9,101,'Gate',ha='right',va='bottom',fontsize=10)
ax=axs[1,0];x=np.arange(1,4);whole=[z['whole_stage_s']*1000 for z in d['solve_times']];native=[(z['native_setup_s']+z['native_solve_s'])*1000 for z in d['solve_times']];ax.bar(x-.17,whole,.32,color=orange,label='Whole solve stage');ax.bar(x+.17,native,.32,color='white',edgecolor=ink,hatch='//',label='Native setup + solve');ax.set(xticks=x,ylim=(0,2050),xlabel='Control transaction',ylabel='Recorded duration (ms)',title='Solve-stage wall and native timers');ax.legend(frameon=False,loc='upper left',fontsize=10)
for xx,a,b in zip(x,whole,native):ax.text(xx-.17,a+30,f'{a:.0f}',ha='center',fontsize=10);ax.text(xx+.17,b+28,f'{b:.1f}',ha='center',fontsize=10)
ax=axs[1,1];base=np.zeros(3);vals={'Geometry / QP assembly':[],'Solve stage':[],'Value validation':[],'Other cycle work':[]}
for row in d['cycle_times']:
 seg={z['name']:z['seconds']for z in row['segments']};g=seg['geometry_assembly'];s=seg['solve'];v=seg['value_validation'];other=row['complete_cycle_seconds']-g-s-v;assert other>=0
 vals['Geometry / QP assembly'].append(g);vals['Solve stage'].append(s);vals['Value validation'].append(v);vals['Other cycle work'].append(other)
for (label,v),color in zip(vals.items(),[blue,orange,olive,gray]):ax.barh([1,2,3],v,left=base,height=.53,color=color,label=label);base+=np.array(v)
ax.set(yticks=[1,2,3],xlim=(0,7.2),ylim=(.35,3.85),xlabel='Complete offline cycle wall (s)',ylabel='Control transaction',title='Cycle composition; all miss 4 ms');ax.grid(axis='x',color='#e4e6e8',linewidth=.7);ax.legend(loc='lower left',bbox_to_anchor=(0,-.40),ncol=2,frameon=False,fontsize=9)
for yy,v in zip([1,2,3],base):ax.text(v+.08,yy,f'{v:.3f} s',va='center',fontsize=10)
fig.suptitle('Actual36: short nonzero-progress transactions and timing',fontsize=19,x=.07,ha='left',y=.97)
fig.text(.07,.923,'3 accepted transactions · 6 physical substeps · 12 ms of motion · max TCP error 3.216 mm / 5.484 mrad',fontsize=12)
fig.text(.07,.058,'Recorded frozen simulation; native timing is included in the wider solve stage, not a partition of all other work.',fontsize=10)
fig.text(.07,.031,'No complete task, physical stop, realtime or Phase5 acceptance. Startup/termination excluded from cycle timing.',fontsize=10)
for ext in ['png','svg']:fig.savefig(p/f'actual36_short_progress_timing.{ext}',dpi=160,facecolor='white')
plt.close(fig)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
prov={'schema':'ACTUAL36_RESUMED_PRESENTATION_PROVENANCE_V1','renderer_sha256':sha(Path(__file__)),'plot_data_sha256':sha(p/'plot-data.json'),'sources':d['source_files'],'dimensions':[2128,1456],'method':'Matplotlib static source-backed figure, no Model/Scene/FK/solver/plant execution','units':'s dimensionless; elapsedms; positionmetres/0.01; SO3radians/0.05; timer seconds convertedms','scope':d['scope'],'outputs':{q.name:{'bytes':q.stat().st_size,'sha256':sha(q)}for q in p.glob('actual36_short_progress_timing.*')},'phase5':'NOT_ACCEPTED','phase6':'NOT_STARTED'};(p/'PROVENANCE.json').write_text(json.dumps(prov,indent=2)+'\n');print(json.dumps({'outputs':prov['outputs']}))
