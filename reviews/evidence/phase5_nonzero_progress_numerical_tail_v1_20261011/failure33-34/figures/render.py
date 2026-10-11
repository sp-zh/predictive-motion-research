from pathlib import Path
import json,hashlib,os,resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));signal.alarm(40);p=Path(__file__).parent;os.environ['MPLCONFIGDIR']=str(p/'mpl-local-cache');os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
names=['cpp_oracle.stdout','numpy_analysis.json'];before={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};lines=(p/names[0]).read_text().splitlines();U=np.array([float(x) for x in next(s for s in lines if s.startswith('U,')).split(',')[1:]]);assert len(U)==160;beta=U.reshape(20,8)[:,7];jerks=np.diff(np.r_[0.,beta])/.004;lattice=[1,1,2,2,3,3,4,4,5,5,6,6,8,10,12,16,20,24,28,40];s=r=0;elapsed=0;points=[]
for k,count in enumerate(lattice):
 origin_s,origin_r=s,r
 for cycle in range(count):
  for half in [1,2]:
   t=.004*cycle+.002*half;sh=origin_s+t*origin_r+.5*t*t*beta[k];rh=origin_r+t*beta[k];points.append([elapsed+t,sh,rh,k,cycle,half,bool(rh<0)])
  s,r=s+.004*r+.5*.004*.004*beta[k],r+.004*beta[k]
 elapsed+=.004*count
arr=np.asarray(points);assert len(arr)==400 and r<0;npanalysis=json.loads((p/names[1]).read_text());cppterminal=float(next(x for x in lines if x.startswith('terminal,')).split(',')[2]);assert cppterminal==r
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2});fig,ax=plt.subplots(2,2,figsize=(13,8.5));fig.suptitle('Phase 5 pure optimizer diagnostic: nonzero progress, refused tail',x=.075,ha='left',fontsize=18)
ax[0,0].plot(arr[:,0],arr[:,1],color='#006f89');ax[0,0].set(title='400 command progress references',xlabel='Predicted command horizon (s)',ylabel='Logical path progress s')
ax[0,1].plot(arr[:,0],arr[:,2],color='#006f89');ax[0,1].axhline(0,color='#b23a38',ls=':');ax[0,1].set(title='Logical progress speed',xlabel='Predicted command horizon (s)',ylabel='r (1/s)')
x=np.r_[0.,np.cumsum(lattice)[:-1]*.004];ax[1,0].plot(x,jerks,'o-',color='#006f89',markersize=3);ax[1,0].axhline(5,color='#b23a38',ls=':',label='Original +/-5 bound');ax[1,0].axhline(-5,color='#b23a38',ls=':');ax[1,0].set(title='Feedback jerk at cell transitions',xlabel='Predicted command horizon (s)',ylabel='(b - prior b) / 4 ms (1/s3)',ylim=(-5.6,5.6));ax[1,0].legend(loc='upper right',fontsize=8)
vals=[npanalysis['horizon_r']*1e17,cppterminal*1e17];ax[1,1].bar(['NumPy transform','Eigen / C++'],vals,color=['#d47623','#006f89'],width=.55);ax[1,1].axhline(0,color='#b23a38',ls=':');ax[1,1].set(title='Both literal strict progress checks fail',ylabel='Terminal r (x 1e-17 1/s)',ylim=(-2.1,.4));
for i,v in enumerate(vals):ax[1,1].text(i,v-.08,f'{v:.3f}',ha='center',va='top')
fig.text(.075,.057,'Saved attempt 30 initial QP | 144 optimizer dimensions | 160 extra alpha / progress-jerk rows | first s = 1.59968e-7',fontsize=10)
fig.text(.075,.027,'Pure numerical trial only: no new Model, nonlinear candidate, physics, controller, task video or phase acceptance. Failures retained; no clamp.',fontsize=9)
fig.subplots_adjust(top=.88,bottom=.17,left=.075,right=.97,hspace=.43,wspace=.28)
for ext in ['png','svg']:fig.savefig(p/('full144_progress_refused_tail.'+ext),dpi=160)
plt.close(fig);assert before=={n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names};(p/'LOGICAL_HALF_PROGRESS.json').write_text(json.dumps(points)+'\n');outputs={n:{'bytes':(p/n).stat().st_size,'sha256':hashlib.sha256((p/n).read_bytes()).hexdigest()} for n in ['full144_progress_refused_tail.png','full144_progress_refused_tail.svg','LOGICAL_HALF_PROGRESS.json']};(p/'PLOT_PROVENANCE.json').write_text(json.dumps({'schema':'FULL144_PURE_REFUSED_TAIL_PLOT_V1','inputs':before,'outputs':outputs,'matplotlib_version':matplotlib.__version__,'scope':'all400 pure logical references from saved34 numerical U, both strictterminal failures; actual motion not plotted','new_Model_or_MuJoCo_entries':0},indent=2)+'\n');print(json.dumps(outputs))
